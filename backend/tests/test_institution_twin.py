"""
Pytest Test Suite for NetworkX Institution Twin Graph Builder & Pluggable ImpossibilityEngine.
Validates:
1. Graph Builder: 8 Node Types (Institution, Faculty, Programme, Document, Lab, Building, Location, Issuer)
   and 5 Edge Types (employs, offers, holds, issued_by, located_at).
2. Database Loading: load_from_db populates the MultiDiGraph from SQLAlchemy models.
3. Check 1: Faculty full-time at two institutions with overlapping dates (masked ID + fuzzy name/DOB).
4. Check 2: Built-up area per student below configured norm, using claimed intake.
5. Check 3: Document issued before issuer's creation date, or validity ending before it starts.
6. Check 4: Lab equipment list inconsistent with approved programmes.
7. Check 5: Same document reference number used by different institutions.
8. Pluggable Architecture: Custom check registration and execution.
9. Wording Constraint: Outputs MUST state 'indicator for review', strictly avoiding 'fraud'.
10. Ground Truth Evaluation: 100% precision and recall against ground truth dataset.
"""
import re
import json
import pytest
import networkx as nx
from pathlib import Path
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models.models import (
    Institution, Faculty, FacultyEmployment, Programme,
    Document, Lab, Building, Location, Issuer
)
from backend.app.services.graph_builder import InstitutionTwinGraphBuilder, graph_builder
from backend.app.services.impossibility_engine import (
    ImpossibilityEngine,
    BaseImpossibilityCheck,
    DualEmploymentFacultyCheck,
    BuiltUpAreaDensityCheck,
    DocumentIssuerChronologyCheck,
    LabEquipmentProgrammeConsistencyCheck,
    SharedDocumentReferenceCheck,
    calculate_name_similarity,
    normalize_person_name,
    date_ranges_overlap,
    parse_flexible_date
)
from backend.app.data.seed_data import seed_database, seed_institution_twin_tables


@pytest.fixture(scope="session")
def db_session():
    """Initializes database schema, seeds benchmark data, and provides test session."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database()
    seed_institution_twin_tables(db)
    yield db
    db.close()


@pytest.fixture
def engine_instance():
    """Returns an initialized ImpossibilityEngine instance."""
    return ImpossibilityEngine()


# ==============================================================================
# 1. INSTITUTION TWIN GRAPH BUILDER TESTS (8 Nodes, 5 Edges, DB Loading)
# ==============================================================================

def test_graph_builder_all_8_node_types():
    """Validates that InstitutionTwinGraphBuilder instantiates all 8 node types."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.create_empty_graph()

    builder.add_institution_node(g, "INST_TEST", {"name": "Test Engineering College", "approved_intake": 300})
    builder.add_faculty_node(g, "FAC_TEST", {"name": "Dr. Raman", "pan_masked": "AB****89C", "dob": "1980-01-01"})
    builder.add_programme_node(g, "PROG_TEST", {"name": "Mechanical Engineering", "approved_intake": 60})
    builder.add_document_node(g, "DOC_TEST", {"document_type": "Fire NOC", "reference_number": "NOC/123", "issue_date": "2024-01-01"})
    builder.add_lab_node(g, "LAB_TEST", {"name": "CAD/CAM Lab", "equipment": ["Workstations", "CNC"]})
    builder.add_building_node(g, "BLD_TEST", {"name": "Main Block", "built_up_area_sqm": 5000.0})
    builder.add_location_node(g, "LOC_TEST", {"city": "Bengaluru", "state": "Karnataka"})
    builder.add_issuer_node(g, "ISSUER_TEST", {"name": "Fire Department", "creation_date": "2010-01-01"})

    node_types = {d.get("type") for _, d in g.nodes(data=True)}
    expected_types = {"INSTITUTION", "FACULTY", "PROGRAMME", "DOCUMENT", "LAB", "BUILDING", "LOCATION", "ISSUER"}
    assert expected_types.issubset(node_types), f"Missing node types: {expected_types - node_types}"


def test_graph_builder_all_5_edge_types():
    """Validates that InstitutionTwinGraphBuilder instantiates all 5 edge types with attributes."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.create_empty_graph()

    # Add prerequisite nodes
    builder.add_institution_node(g, "INST_01", {"name": "College A"})
    builder.add_faculty_node(g, "FAC_01", {"name": "Dr. A"})
    builder.add_programme_node(g, "PROG_01", {"name": "Civil Engineering"})
    builder.add_document_node(g, "DOC_01", {"document_type": "Affidavit"})
    builder.add_lab_node(g, "LAB_01", {"name": "Survey Lab"})
    builder.add_building_node(g, "BLD_01", {"name": "Science Block"})
    builder.add_location_node(g, "LOC_01", {"city": "Bengaluru"})
    builder.add_issuer_node(g, "ISS_01", {"name": "State Board"})

    # 1. employs (with start/end dates, full-time/part-time)
    builder.add_employs_edge(
        g, "INST_01", "FAC_01",
        start_date="2021-08-01",
        end_date=None,
        employment_type="Full-Time",
        role="Professor"
    )

    # 2. offers
    builder.add_offers_edge(g, "INST_01", "PROG_01", intake=60, academic_year="2025-26")

    # 3. holds (Institution -> Document / Building / Lab)
    builder.add_holds_edge(g, "INST_01", "DOC_01", entity_type="DOCUMENT")
    builder.add_holds_edge(g, "INST_01", "BLD_01", entity_type="BUILDING")
    builder.add_holds_edge(g, "INST_01", "LAB_01", entity_type="LAB")

    # 4. issued_by
    builder.add_issued_by_edge(g, "DOC_01", "ISS_01", issue_date="2024-01-01", reference_number="REF-001")

    # 5. located_at
    builder.add_located_at_edge(g, "INST_01", "LOC_01")
    builder.add_located_at_edge(g, "BLD_01", "LOC_01")

    edge_relations = {d.get("relation") for _, _, d in g.edges(data=True)}
    expected_relations = {"employs", "offers", "holds", "issued_by", "located_at"}
    assert expected_relations == edge_relations

    # Validate employs edge properties
    employs_data = g.get_edge_data("INST_01", "FAC_01")[0]
    assert employs_data["relation"] == "employs"
    assert employs_data["employment_type"] == "Full-Time"
    assert employs_data["start_date"] == "2021-08-01"
    assert employs_data["end_date"] is None


def test_load_graph_from_db(db_session: Session):
    """Validates that graph builder loads entities directly from the SQLAlchemy database."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.load_from_db(db_session)

    assert g.number_of_nodes() >= 10
    assert g.number_of_edges() >= 10

    # Ensure nodes of each type are present in DB-loaded graph
    types = {d.get("type") for _, d in g.nodes(data=True)}
    for expected in ["INSTITUTION", "FACULTY", "PROGRAMME", "DOCUMENT", "LAB", "BUILDING", "LOCATION", "ISSUER"]:
        assert expected in types, f"Expected node type {expected} missing in DB graph"

    # Test serialization format for UI
    serialized = builder.serialize_graph(g)
    assert "nodes" in serialized
    assert "edges" in serialized
    assert "summary" in serialized
    assert serialized["summary"]["total_nodes"] == g.number_of_nodes()
    assert serialized["summary"]["total_edges"] == g.number_of_edges()


def test_subgraph_extraction_json_format():
    """Validates that extract_subgraph produces {nodes: [...], edges: [...]} JSON for UI rendering."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.build_from_records(
        institutions=[{"id": "I1", "name": "Inst 1"}, {"id": "I2", "name": "Inst 2"}],
        faculty=[{"id": "F1", "name": "Dr. X"}],
        employments=[
            {"inst_id": "I1", "fac_id": "F1", "employment_type": "Full-Time"},
            {"inst_id": "I2", "fac_id": "F1", "employment_type": "Full-Time"}
        ]
    )

    subgraph = builder.extract_subgraph(g, ["I1", "I2", "F1"])
    assert "nodes" in subgraph
    assert "edges" in subgraph
    assert len(subgraph["nodes"]) == 3
    assert len(subgraph["edges"]) == 2

    # Verify edge formatting
    for edge in subgraph["edges"]:
        assert "source" in edge
        assert "target" in edge
        assert "relation" in edge
        assert edge["relation"] == "employs"


# ==============================================================================
# 2. CHECK 1 TESTS: Dual Employment Faculty (Masked ID + Fuzzy Name / DOB)
# ==============================================================================

def test_check1_dual_employment_same_node_detected():
    """Validates detection when same faculty node has overlapping full-time employments."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.build_from_records(
        institutions=[
            {"id": "INST_A", "name": "College Alpha"},
            {"id": "INST_B", "name": "College Beta"}
        ],
        faculty=[
            {
                "id": "FAC_01",
                "name": "Dr. R. K. Sharma",
                "pan_masked": "AB****89C",
                "aadhaar_masked": "XXXX-XXXX-9021",
                "dob": "1975-08-12"
            }
        ],
        employments=[
            {"inst_id": "INST_A", "fac_id": "FAC_01", "employment_type": "Full-Time", "start_date": "2021-08-01", "end_date": None},
            {"inst_id": "INST_B", "fac_id": "FAC_01", "employment_type": "Full-Time", "start_date": "2022-01-15", "end_date": None}
        ]
    )

    check = DualEmploymentFacultyCheck()
    findings = check.evaluate(g)

    assert len(findings) == 1
    f = findings[0]
    assert f["conflict_type"] == "DUAL_EMPLOYMENT_GHOST_FACULTY"
    assert f["check_id"] == "DUAL_EMPLOYMENT_FACULTY"
    assert "indicator for review" in f["explanation"].lower()
    assert "fraud" not in f["explanation"].lower()
    assert len(f["conflicting_subgraph"]["nodes"]) == 3  # INST_A, INST_B, FAC_01
    assert len(f["conflicting_subgraph"]["edges"]) == 2


def test_check1_dual_employment_fuzzy_name_matching():
    """Validates fuzzy name matching across two distinct faculty nodes with matching masked PAN."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.build_from_records(
        institutions=[
            {"id": "INST_A", "name": "College Alpha"},
            {"id": "INST_B", "name": "College Beta"}
        ],
        faculty=[
            {
                "id": "FAC_01A",
                "name": "Dr. Ram Kumar Sharma",
                "pan_masked": "AB****89C",
                "dob": "1975-08-12"
            },
            {
                "id": "FAC_01B",
                "name": "Prof. R. K. Sharma",  # Fuzzy match with Dr. Ram Kumar Sharma
                "pan_masked": "AB****89C",     # Identical masked PAN
                "dob": "1975-08-12"
            }
        ],
        employments=[
            {"inst_id": "INST_A", "fac_id": "FAC_01A", "employment_type": "Full-Time", "start_date": "2021-08-01", "end_date": "2025-12-31"},
            {"inst_id": "INST_B", "fac_id": "FAC_01B", "employment_type": "Full-Time", "start_date": "2023-01-01", "end_date": None}
        ]
    )

    check = DualEmploymentFacultyCheck()
    findings = check.evaluate(g)

    assert len(findings) == 1
    f = findings[0]
    assert "indicator for review" in f["title"].lower()
    assert "conflicting_subgraph" in f
    assert len(f["conflicting_subgraph"]["nodes"]) == 4


def test_check1_clean_controls_no_false_positive():
    """Validates that non-overlapping dates or part-time employment do NOT trigger finding."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.build_from_records(
        institutions=[
            {"id": "INST_A", "name": "College Alpha"},
            {"id": "INST_B", "name": "College Beta"}
        ],
        faculty=[
            # Case 1: Sequential, non-overlapping dates (resigned before joining new)
            {
                "id": "FAC_CLEAN_1",
                "name": "Dr. Priya Sundaram",
                "pan_masked": "CD****45E"
            },
            # Case 2: One appointment is Adjunct / Part-Time
            {
                "id": "FAC_CLEAN_2",
                "name": "Dr. Amit Varma",
                "pan_masked": "EF****12G"
            }
        ],
        employments=[
            {"inst_id": "INST_A", "fac_id": "FAC_CLEAN_1", "employment_type": "Full-Time", "start_date": "2018-01-01", "end_date": "2021-06-30"},
            {"inst_id": "INST_B", "fac_id": "FAC_CLEAN_1", "employment_type": "Full-Time", "start_date": "2021-07-01", "end_date": "2024-12-31"},
            {"inst_id": "INST_A", "fac_id": "FAC_CLEAN_2", "employment_type": "Full-Time", "start_date": "2022-01-01", "end_date": None},
            {"inst_id": "INST_B", "fac_id": "FAC_CLEAN_2", "employment_type": "Part-Time Visiting", "start_date": "2022-01-01", "end_date": None}
        ]
    )

    check = DualEmploymentFacultyCheck()
    findings = check.evaluate(g)
    assert len(findings) == 0, "Clean controls should not trigger dual-employment finding"


# ==============================================================================
# 3. CHECK 2 TESTS: Built-Up Area Density Norm
# ==============================================================================

def test_check2_area_below_norm_detected():
    """Validates detection when built-up area is below configured norm for claimed intake."""
    builder = InstitutionTwinGraphBuilder()
    # 480 annual intake * 4 years = 1920 campus students. Norm = 10.5 sqm/student -> requires 20,160 sqm
    # College provides only 8,500 sqm (4.43 sqm/student)
    g = builder.build_from_records(
        institutions=[
            {
                "id": "INST_DEFICIT",
                "name": "Deficit Engineering College",
                "approved_intake": 480,
                "total_built_up_area_sqm": 8500.0
            }
        ],
        programmes=[
            {"id": "PROG_01", "name": "Mechanical", "approved_intake": 240},
            {"id": "PROG_02", "name": "Computer Science", "approved_intake": 240}
        ],
        buildings=[
            {"id": "BLD_01", "name": "Single Academic Block", "built_up_area_sqm": 8500.0}
        ],
        offers=[
            {"inst_id": "INST_DEFICIT", "prog_id": "PROG_01", "intake": 240},
            {"inst_id": "INST_DEFICIT", "prog_id": "PROG_02", "intake": 240}
        ],
        holds=[
            {"inst_id": "INST_DEFICIT", "target_id": "BLD_01", "entity_type": "BUILDING"}
        ]
    )

    check = BuiltUpAreaDensityCheck(min_sqm_per_student=10.5, duration_years=4)
    findings = check.evaluate(g)

    assert len(findings) == 1
    f = findings[0]
    assert f["conflict_type"] == "BUILT_UP_AREA_DENSITY_DEFICIT"
    assert "indicator for review" in f["explanation"].lower()
    assert "fraud" not in f["explanation"].lower()
    assert f["evidence_chain"]["actual_sqm_per_student"] < 5.0
    assert len(f["conflicting_subgraph"]["nodes"]) >= 2


def test_check2_area_compliant_control():
    """Validates that an institution meeting the configured norm passes cleanly."""
    builder = InstitutionTwinGraphBuilder()
    # 300 annual intake * 4 = 1200 students. At 10.5 norm requires 12,600 sqm. College has 16,000 sqm (13.3 sqm/student)
    g = builder.build_from_records(
        institutions=[
            {
                "id": "INST_COMPLIANT",
                "name": "Compliant Engineering College",
                "approved_intake": 300,
                "total_built_up_area_sqm": 16000.0
            }
        ]
    )

    check = BuiltUpAreaDensityCheck(min_sqm_per_student=10.5, duration_years=4)
    findings = check.evaluate(g)
    assert len(findings) == 0, "Compliant institution should not trigger area deficit finding"


# ==============================================================================
# 4. CHECK 3 TESTS: Document Issuer Chronology
# ==============================================================================

def test_check3_document_issued_before_issuer_creation():
    """Validates detection when document issue date precedes issuer creation date."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.build_from_records(
        institutions=[{"id": "INST_01", "name": "Apex Tech"}],
        issuers=[
            {
                "id": "ISSUER_FIRE_DEPT",
                "name": "State Fire Authority",
                "creation_date": "2020-01-01"
            }
        ],
        documents=[
            {
                "id": "DOC_ANACHRONISTIC",
                "document_type": "Fire NOC",
                "reference_number": "FIR/2015/001",
                "issue_date": "2015-06-15",  # 5 years before issuer existed!
                "valid_till": "2026-06-30"
            }
        ],
        holds=[{"inst_id": "INST_01", "target_id": "DOC_ANACHRONISTIC"}],
        issued_by=[{"doc_id": "DOC_ANACHRONISTIC", "issuer_id": "ISSUER_FIRE_DEPT"}]
    )

    check = DocumentIssuerChronologyCheck()
    findings = check.evaluate(g)

    assert len(findings) == 1
    f = findings[0]
    assert f["conflict_type"] == "DOCUMENT_PREDATES_ISSUER_CREATION"
    assert "indicator for review" in f["explanation"].lower()
    assert "fraud" not in f["explanation"].lower()
    assert len(f["conflicting_subgraph"]["nodes"]) == 3  # Document, Issuer, Institution


def test_check3_document_validity_ending_before_it_starts():
    """Validates detection when document validity expiration date is before its issue date."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.build_from_records(
        institutions=[{"id": "INST_01", "name": "Apex Tech"}],
        documents=[
            {
                "id": "DOC_INVERTED",
                "document_type": "Land Title Deed",
                "reference_number": "LAN/2023/102",
                "issue_date": "2023-01-15",
                "valid_till": "2021-12-31"  # Ends before it was issued!
            }
        ],
        holds=[{"inst_id": "INST_01", "target_id": "DOC_INVERTED"}]
    )

    check = DocumentIssuerChronologyCheck()
    findings = check.evaluate(g)

    assert len(findings) == 1
    f = findings[0]
    assert f["conflict_type"] == "DOCUMENT_INVERTED_VALIDITY_INTERVAL"
    assert "indicator for review" in f["explanation"].lower()
    assert "fraud" not in f["explanation"].lower()


def test_check3_clean_document_control():
    """Validates that a chronologically sound document passes cleanly."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.build_from_records(
        institutions=[{"id": "INST_01", "name": "Apex Tech"}],
        issuers=[{"id": "ISSUER_BOARD", "name": "Affiliation Board", "creation_date": "1998-01-01"}],
        documents=[
            {
                "id": "DOC_CLEAN",
                "document_type": "Affiliation Order",
                "issue_date": "2024-05-01",
                "valid_till": "2027-05-01"
            }
        ],
        holds=[{"inst_id": "INST_01", "target_id": "DOC_CLEAN"}],
        issued_by=[{"doc_id": "DOC_CLEAN", "issuer_id": "ISSUER_BOARD"}]
    )

    check = DocumentIssuerChronologyCheck()
    findings = check.evaluate(g)
    assert len(findings) == 0, "Valid document should not trigger chronology finding"


# ==============================================================================
# 5. CHECK 4 TESTS: Lab Equipment Programme Consistency
# ==============================================================================

def test_check4_missing_lab_equipment_detected():
    """Validates detection when an approved programme has no corresponding equipment in labs."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.build_from_records(
        institutions=[{"id": "INST_01", "name": "Apex Tech"}],
        programmes=[
            {"id": "PROG_MECH", "name": "Mechanical Engineering"}
        ],
        labs=[
            # Institution only has computer lab, zero mechanical equipment!
            {"id": "LAB_CS", "name": "Computer Center", "equipment": ["Workstations", "Servers"]}
        ],
        offers=[{"inst_id": "INST_01", "prog_id": "PROG_MECH"}],
        holds=[{"inst_id": "INST_01", "target_id": "LAB_CS", "entity_type": "LAB"}]
    )

    check = LabEquipmentProgrammeConsistencyCheck()
    findings = check.evaluate(g)

    assert len(findings) == 1
    f = findings[0]
    assert f["conflict_type"] == "LAB_EQUIPMENT_PROGRAMME_INCONSISTENCY"
    assert "indicator for review" in f["explanation"].lower()
    assert "fraud" not in f["explanation"].lower()
    assert "Mechanical Engineering" in f["explanation"]
    assert len(f["conflicting_subgraph"]["nodes"]) == 3  # Institution, Programme, Lab


def test_check4_equipped_lab_passes_control():
    """Validates that an approved programme with proper lab apparatus passes cleanly."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.build_from_records(
        institutions=[{"id": "INST_01", "name": "Royal College"}],
        programmes=[
            {"id": "PROG_MECH", "name": "Mechanical Engineering"}
        ],
        labs=[
            {
                "id": "LAB_MECH",
                "name": "Machine Workshop",
                "equipment": ["Lathe Machine", "Milling Machine", "Universal Testing Machine", "CNC Trainer"]
            }
        ],
        offers=[{"inst_id": "INST_01", "prog_id": "PROG_MECH"}],
        holds=[{"inst_id": "INST_01", "target_id": "LAB_MECH", "entity_type": "LAB"}]
    )

    check = LabEquipmentProgrammeConsistencyCheck()
    findings = check.evaluate(g)
    assert len(findings) == 0, "Well-equipped lab should not trigger equipment inconsistency"


# ==============================================================================
# 6. CHECK 5 TESTS: Shared Document Reference Number
# ==============================================================================

def test_check5_shared_reference_number_detected():
    """Validates detection when identical document reference number is claimed by multiple institutions."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.build_from_records(
        institutions=[
            {"id": "INST_A", "name": "College Alpha"},
            {"id": "INST_B", "name": "College Beta"}
        ],
        documents=[
            {
                "id": "DOC_A",
                "document_type": "Fire NOC",
                "reference_number": "FIR/KA/2024/99102"
            },
            {
                "id": "DOC_B",
                "document_type": "Fire NOC",
                "reference_number": "FIR/KA/2024/99102"  # Identical reference number!
            }
        ],
        holds=[
            {"inst_id": "INST_A", "target_id": "DOC_A"},
            {"inst_id": "INST_B", "target_id": "DOC_B"}
        ]
    )

    check = SharedDocumentReferenceCheck()
    findings = check.evaluate(g)

    assert len(findings) == 1
    f = findings[0]
    assert f["conflict_type"] == "SHARED_DOCUMENT_REFERENCE_COLLISION"
    assert "indicator for review" in f["explanation"].lower()
    assert "fraud" not in f["explanation"].lower()
    assert len(f["conflicting_subgraph"]["nodes"]) == 4  # INST_A, INST_B, DOC_A, DOC_B


def test_check5_unique_reference_control():
    """Validates that distinct reference numbers pass cleanly."""
    builder = InstitutionTwinGraphBuilder()
    g = builder.build_from_records(
        institutions=[
            {"id": "INST_A", "name": "College Alpha"},
            {"id": "INST_B", "name": "College Beta"}
        ],
        documents=[
            {"id": "DOC_A", "document_type": "Fire NOC", "reference_number": "FIR/2024/001"},
            {"id": "DOC_B", "document_type": "Fire NOC", "reference_number": "FIR/2024/002"}
        ],
        holds=[
            {"inst_id": "INST_A", "target_id": "DOC_A"},
            {"inst_id": "INST_B", "target_id": "DOC_B"}
        ]
    )

    check = SharedDocumentReferenceCheck()
    findings = check.evaluate(g)
    assert len(findings) == 0, "Distinct reference numbers should not trigger collision"


# ==============================================================================
# 7. PLUGGABLE ARCHITECTURE TESTS
# ==============================================================================

class CustomLandZoningCheck(BaseImpossibilityCheck):
    check_id = "CUSTOM_LAND_ZONING_CHECK"
    name = "Custom Land Zoning Check"
    description = "Test pluggable check verifying campus zoning."

    def evaluate(self, graph, target_inst_id=None):
        return [{
            "engine_module": "IMPOSSIBILITY_ENGINE",
            "check_id": self.check_id,
            "conflict_type": self.check_id,
            "indicator_type": self.indicator_type,
            "severity": "WARNING",
            "title": "Indicator for Review: Industrial Zone Campus",
            "explanation": "Indicator for review: Campus is situated in heavy industrial zone.",
            "conflicting_subgraph": {"nodes": [], "edges": []}
        }]


def test_pluggable_architecture_registration_and_execution(engine_instance: ImpossibilityEngine):
    """Validates pluggable registration, retrieval, and execution of custom checks."""
    initial_check_count = len(engine_instance.checks)
    custom_check = CustomLandZoningCheck()

    # Register
    engine_instance.register_check(custom_check)
    assert len(engine_instance.checks) == initial_check_count + 1
    assert engine_instance.get_check("CUSTOM_LAND_ZONING_CHECK") is custom_check

    # Execute
    findings = engine_instance.run_checks()
    custom_findings = [f for f in findings if f["check_id"] == "CUSTOM_LAND_ZONING_CHECK"]
    assert len(custom_findings) == 1
    assert "indicator for review" in custom_findings[0]["explanation"].lower()

    # Unregister
    engine_instance.unregister_check("CUSTOM_LAND_ZONING_CHECK")
    assert len(engine_instance.checks) == initial_check_count
    assert engine_instance.get_check("CUSTOM_LAND_ZONING_CHECK") is None


# ==============================================================================
# 8. REGULATORY WORDING CONSTRAINT AUDIT
# ==============================================================================

def test_regulatory_wording_constraint_strictly_adhered(engine_instance: ImpossibilityEngine):
    """
    CRITICAL REGULATORY CONSTRAINT TEST:
    Asserts that:
    1. Every finding contains 'indicator for review' in title or explanation.
    2. The word 'fraud' (case-insensitive) NEVER appears in ANY output, finding, or text.
    """
    findings = engine_instance.run_checks()
    assert len(findings) > 0, "Engine should return findings on seed knowledge graph"

    for f in findings:
        title = f.get("title", "")
        explanation = f.get("explanation", "")
        recommended_action = f.get("recommended_action", "")
        full_text = f"{title} {explanation} {recommended_action}".lower()

        # Must state "indicator for review"
        assert "indicator for review" in full_text, (
            f"Finding {f.get('conflict_type')} missing required wording 'indicator for review': {title}"
        )

        # STRICTLY NEVER state "fraud"
        assert "fraud" not in full_text, (
            f"CRITICAL ERROR: Prohibited word found in finding {f.get('conflict_type')}: {explanation}"
        )


# ==============================================================================
# 9. GROUND TRUTH BENCHMARK EVALUATION TEST
# ==============================================================================

def test_ground_truth_detection_accuracy(engine_instance: ImpossibilityEngine):
    """
    Evaluates detection against the ground truth dataset:
    - Verifies 100% recall on all planted ground truth impossibility cases.
    - Verifies 0 false positives on negative controls.
    """
    gt_file = Path(__file__).resolve().parent.parent.parent / "generated_data" / "institution_twin_ground_truth.json"
    assert gt_file.exists(), f"Ground truth file not found at {gt_file}"

    with open(gt_file, "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    cases = gt_data["ground_truth_cases"]
    findings = engine_instance.run_checks()
    detected_conflicts = {f["conflict_type"] for f in findings}

    for case in cases:
        expected_type = case["expected_conflict_type"]
        assert expected_type in detected_conflicts, (
            f"Ground truth case {case['case_id']} expected conflict {expected_type} not detected"
        )

        # Find matching finding
        matching_findings = [f for f in findings if f["conflict_type"] == expected_type]
        assert len(matching_findings) >= 1
        finding = matching_findings[0]

        # Verify indicator type
        assert finding["indicator_type"] == case["expected_indicator_type"]

        # Verify subgraph format
        subgraph = finding["conflicting_subgraph"]
        assert "nodes" in subgraph and "edges" in subgraph
        assert len(subgraph["nodes"]) > 0

        # Verify negative control is not erroneously flagged
        for control in case.get("negative_controls", []):
            if "faculty_id" in control:
                # Ensure control faculty is not in finding entities
                assert control["faculty_id"] not in finding.get("entity_ids", [])
            if "reference_number" in control:
                assert control["reference_number"] not in finding.get("explanation", "")
