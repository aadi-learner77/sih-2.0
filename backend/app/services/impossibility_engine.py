"""
Impossibility Engine using NetworkX Knowledge Graph.
Models complex inter-institutional relationships across:
- Institutions, Faculty, Programmes, Documents, Labs, Buildings, Locations, Issuers.

Pluggable checks architecture:
1. Faculty full-time at two institutions with overlapping dates (match on masked ID + fuzzy name/DOB)
2. Built-up area per student below the configured norm, using the claimed intake
3. Document issued before the issuing body's creation date, or validity ending before it starts
4. Lab equipment list inconsistent with the approved programmes
5. Same document reference number used by different institutions

CRITICAL REGULATORY CONSTRAINT:
All findings and messages strictly state "indicator for review", adhering to non-punitive review guidelines.
"""
import re
import difflib
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Set, Tuple
import networkx as nx
from sqlalchemy.orm import Session

from backend.app.services.graph_builder import graph_builder, InstitutionTwinGraphBuilder


def normalize_person_name(name: str) -> str:
    """Normalizes person names for fuzzy matching by stripping honorifics and non-alphanumerics."""
    if not name:
        return ""
    cleaned = re.sub(r"^(dr\.|prof\.|mr\.|mrs\.|ms\.|shri|smt\.|dr|prof)\s+", "", name.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", cleaned)
    return " ".join(cleaned.lower().split())


def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculates fuzzy similarity ratio between two person names."""
    n1 = normalize_person_name(name1)
    n2 = normalize_person_name(name2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0

    # Token set containment (e.g. "ram kumar sharma" and "r k sharma")
    tokens1 = set(n1.split())
    tokens2 = set(n2.split())
    if tokens1 == tokens2:
        return 1.0

    seq_ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
    return seq_ratio


def parse_flexible_date(date_str: Any) -> Optional[date]:
    """Safely parses date strings into datetime.date objects."""
    if not date_str:
        return None
    if isinstance(date_str, (datetime, date)):
        return date_str if isinstance(date_str, date) else date_str.date()

    date_str = str(date_str).strip()
    if not date_str or date_str.lower() in ("none", "null", "present", "current", "ongoing", "n/a"):
        return None

    # Common formats: YYYY-MM-DD, DD-MM-YYYY, YYYY/MM/DD, DD/MM/YYYY
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(date_str[:10], fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def date_ranges_overlap(
    start1: Optional[date],
    end1: Optional[date],
    start2: Optional[date],
    end2: Optional[date]
) -> bool:
    """Checks whether two employment date intervals overlap."""
    eff_start1 = start1 or date(1970, 1, 1)
    eff_end1 = end1 or date(9999, 12, 31)
    eff_start2 = start2 or date(1970, 1, 1)
    eff_end2 = end2 or date(9999, 12, 31)
    return (eff_start1 <= eff_end2) and (eff_start2 <= eff_end1)


# ============================================================================
# BASE PLUGGABLE CHECK
# ============================================================================
class BaseImpossibilityCheck(ABC):
    """Abstract base class for all pluggable impossibility review checks."""

    check_id: str
    name: str
    description: str
    severity: str = "CRITICAL"
    indicator_type: str = "INDICATOR_FOR_REVIEW"

    @abstractmethod
    def evaluate(
        self,
        graph: nx.MultiDiGraph,
        target_inst_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes check against the graph.
        Returns a list of finding dicts containing:
        - conflicting_subgraph: {"nodes": [...], "edges": [...]} (JSON format for UI)
        - explanation: Wording stating 'indicator for review'
        """
        pass


# ============================================================================
# CHECK 1: Dual Employment (Ghost Faculty)
# Faculty full-time at two institutions with overlapping dates (masked ID + fuzzy name/DOB)
# ============================================================================
class DualEmploymentFacultyCheck(BaseImpossibilityCheck):
    check_id = "DUAL_EMPLOYMENT_FACULTY"
    name = "Dual Employment Faculty Check"
    description = (
        "Detects faculty full-time at two institutions with overlapping dates, "
        "matching on masked ID + fuzzy name/DOB."
    )
    severity = "CRITICAL"
    indicator_type = "INDICATOR_FOR_REVIEW"

    def evaluate(
        self,
        graph: nx.MultiDiGraph,
        target_inst_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        findings = []

        # Collect all employs edges
        employments: List[Dict[str, Any]] = []
        for u, v, k, d in graph.edges(keys=True, data=True):
            if d.get("relation") == "employs":
                u_type = graph.nodes[u].get("type")
                v_type = graph.nodes[v].get("type")
                inst_id = u if u_type == "INSTITUTION" else (v if v_type == "INSTITUTION" else None)
                fac_id = v if v_type == "FACULTY" else (u if u_type == "FACULTY" else None)

                if inst_id and fac_id:
                    emp_type = str(d.get("employment_type", "Full-Time")).lower()
                    if "full-time" in emp_type or "regular" in emp_type:
                        employments.append({
                            "edge": (u, v, k),
                            "inst_id": str(inst_id),
                            "fac_id": str(fac_id),
                            "start_date": parse_flexible_date(d.get("start_date")),
                            "end_date": parse_flexible_date(d.get("end_date")),
                            "raw_start": d.get("start_date"),
                            "raw_end": d.get("end_date"),
                            "role": d.get("role", "Faculty"),
                            "fac_data": dict(graph.nodes[fac_id])
                        })

        processed_pairs: Set[Tuple[str, str, str, str]] = set()

        for i in range(len(employments)):
            for j in range(i + 1, len(employments)):
                e1 = employments[i]
                e2 = employments[j]

                # Must be distinct institutions
                if e1["inst_id"] == e2["inst_id"]:
                    continue

                if target_inst_id:
                    if target_inst_id not in (e1["inst_id"], e2["inst_id"]):
                        continue

                # Check date overlap
                if not date_ranges_overlap(e1["start_date"], e1["end_date"], e2["start_date"], e2["end_date"]):
                    continue

                # Check identity match
                f1 = e1["fac_data"]
                f2 = e2["fac_data"]

                is_match = False
                match_reason = ""

                # Same faculty node
                if e1["fac_id"] == e2["fac_id"]:
                    is_match = True
                    match_reason = "Identical Faculty Entity Node"
                else:
                    # Masked ID match
                    pan1 = str(f1.get("pan_masked") or "").strip().upper()
                    pan2 = str(f2.get("pan_masked") or "").strip().upper()
                    aadhaar1 = str(f1.get("aadhaar_masked") or "").strip().upper()
                    aadhaar2 = str(f2.get("aadhaar_masked") or "").strip().upper()

                    masked_id_match = False
                    if pan1 and pan2 and pan1 == pan2 and len(pan1) >= 5 and "X" not in pan1[2:4]:
                        masked_id_match = True
                        match_reason = f"Masked PAN Match ({pan1})"
                    elif aadhaar1 and aadhaar2 and aadhaar1 == aadhaar2 and len(aadhaar1) >= 8:
                        masked_id_match = True
                        match_reason = f"Masked Aadhaar Match ({aadhaar1})"

                    if masked_id_match:
                        # Fuzzy Name or DOB match
                        dob1 = str(f1.get("dob") or "").strip()
                        dob2 = str(f2.get("dob") or "").strip()
                        name_sim = calculate_name_similarity(f1.get("name", ""), f2.get("name", ""))

                        if dob1 and dob2 and dob1 == dob2:
                            is_match = True
                            match_reason += f" + Identical DOB ({dob1})"
                        elif name_sim >= 0.70:
                            is_match = True
                            match_reason += f" + Fuzzy Name Similarity ({name_sim:.0%})"

                if is_match:
                    pair_key = tuple(sorted([e1["inst_id"], e2["inst_id"]]) + sorted([e1["fac_id"], e2["fac_id"]]))
                    if pair_key in processed_pairs:
                        continue
                    processed_pairs.add(pair_key)

                    inst1_name = graph.nodes[e1["inst_id"]].get("label", e1["inst_id"])
                    inst2_name = graph.nodes[e2["inst_id"]].get("label", e2["inst_id"])
                    fac_name = f1.get("name") or f2.get("name")

                    subgraph_nodes = list({e1["inst_id"], e2["inst_id"], e1["fac_id"], e2["fac_id"]})
                    subgraph = InstitutionTwinGraphBuilder.extract_subgraph(graph, subgraph_nodes)

                    date_desc1 = f"{e1['raw_start'] or 'Beginning'} to {e1['raw_end'] or 'Present'}"
                    date_desc2 = f"{e2['raw_start'] or 'Beginning'} to {e2['raw_end'] or 'Present'}"

                    findings.append({
                        "engine_module": "IMPOSSIBILITY_ENGINE",
                        "check_id": self.check_id,
                        "conflict_type": "DUAL_EMPLOYMENT_GHOST_FACULTY",
                        "indicator_type": self.indicator_type,
                        "severity": self.severity,
                        "entity_ids": subgraph_nodes,
                        "title": f"Indicator for Review: Concurrent Full-Time Appointment ({fac_name})",
                        "explanation": (
                            f"Indicator for review: Faculty member {fac_name} ({match_reason}) is recorded as a "
                            f"Full-Time regular employee across multiple distinct institutions: "
                            f"{inst1_name} ({date_desc1}) and {inst2_name} ({date_desc2}) with overlapping tenure. "
                            f"Statutory regulations mandate single-institution exclusivity for full-time faculty, "
                            f"serving as an indicator for review."
                        ),
                        "evidence_chain": {
                            "faculty_name": fac_name,
                            "match_reason": match_reason,
                            "pan_masked": f1.get("pan_masked") or f2.get("pan_masked"),
                            "aadhaar_masked": f1.get("aadhaar_masked") or f2.get("aadhaar_masked"),
                            "appointments": [
                                {"institution": inst1_name, "role": e1["role"], "dates": date_desc1},
                                {"institution": inst2_name, "role": e2["role"], "dates": date_desc2}
                            ]
                        },
                        "conflicting_subgraph": subgraph,
                        "recommended_action": (
                            "Indicator for review: Issue formal regulatory inquiry to both institutions requesting "
                            "Form 16 statements, monthly salary disbursement logs, and physical biometric attendance."
                        )
                    })

        return findings


# ============================================================================
# CHECK 2: Built-Up Area Density Deficit
# Built-up area per student below the configured norm, using claimed intake
# ============================================================================
class BuiltUpAreaDensityCheck(BaseImpossibilityCheck):
    check_id = "BUILT_UP_AREA_DENSITY_DEFICIT"
    name = "Built-Up Area Density Norm Check"
    description = (
        "Verifies that the institutional total built-up area per student is not "
        "below the configured norm using claimed intake."
    )
    severity = "CRITICAL"
    indicator_type = "INDICATOR_FOR_REVIEW"

    def __init__(self, min_sqm_per_student: float = 10.5, duration_years: int = 4):
        self.min_sqm_per_student = min_sqm_per_student
        self.duration_years = duration_years

    def evaluate(
        self,
        graph: nx.MultiDiGraph,
        target_inst_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        findings = []

        inst_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "INSTITUTION"]
        for inst_id in inst_nodes:
            if target_inst_id and inst_id != target_inst_id:
                continue

            inst_data = graph.nodes[inst_id]

            # 1. Claimed intake: Check offered programmes or fall back to institution approved_intake
            offered_prog_nodes = []
            prog_intake_sum = 0
            for _, v, d in graph.out_edges(inst_id, data=True):
                if d.get("relation") == "offers" and graph.nodes[v].get("type") == "PROGRAMME":
                    offered_prog_nodes.append(v)
                    prog_intake = graph.nodes[v].get("approved_intake") or d.get("approved_intake") or 0
                    prog_intake_sum += int(prog_intake)

            claimed_intake = prog_intake_sum if prog_intake_sum > 0 else int(inst_data.get("approved_intake") or 0)
            if claimed_intake <= 0:
                continue

            total_students = claimed_intake * self.duration_years

            # 2. Total built-up area: Check held buildings or fall back to institution total_built_up_area_sqm
            held_bld_nodes = []
            bld_area_sum = 0.0
            for _, v, d in graph.out_edges(inst_id, data=True):
                if d.get("relation") == "holds" and graph.nodes[v].get("type") == "BUILDING":
                    held_bld_nodes.append(v)
                    bld_area = graph.nodes[v].get("built_up_area_sqm") or 0.0
                    bld_area_sum += float(bld_area)

            total_area = bld_area_sum if bld_area_sum > 0 else float(inst_data.get("total_built_up_area_sqm") or 0.0)

            actual_sqm_per_student = total_area / total_students if total_students > 0 else 0.0

            if actual_sqm_per_student < self.min_sqm_per_student:
                deficit_sqm = (total_students * self.min_sqm_per_student) - total_area
                subgraph_nodes = [inst_id] + held_bld_nodes + offered_prog_nodes
                subgraph = InstitutionTwinGraphBuilder.extract_subgraph(graph, subgraph_nodes)

                findings.append({
                    "engine_module": "IMPOSSIBILITY_ENGINE",
                    "check_id": self.check_id,
                    "conflict_type": self.check_id,
                    "indicator_type": self.indicator_type,
                    "severity": "CRITICAL" if actual_sqm_per_student < (self.min_sqm_per_student * 0.7) else "WARNING",
                    "entity_ids": [inst_id],
                    "title": f"Indicator for Review: Built-Up Area Density Deficit ({inst_data.get('label')})",
                    "explanation": (
                        f"Indicator for review: Total declared built-up area ({total_area:,.1f} sq.m) is below the configured "
                        f"norm of {self.min_sqm_per_student} sq.m/student for a claimed annual intake of {claimed_intake} "
                        f"(estimated campus population: {total_students} students across {self.duration_years} cohorts). "
                        f"The campus provides only {actual_sqm_per_student:.2f} sq.m/student, leaving a regulatory shortfall "
                        f"of {deficit_sqm:,.1f} sq.m, which serves as an indicator for review."
                    ),
                    "evidence_chain": {
                        "institution_id": inst_id,
                        "institution_name": inst_data.get("label"),
                        "claimed_intake": claimed_intake,
                        "student_population": total_students,
                        "total_built_up_area_sqm": total_area,
                        "actual_sqm_per_student": round(actual_sqm_per_student, 2),
                        "norm_sqm_per_student": self.min_sqm_per_student,
                        "shortfall_sqm": round(deficit_sqm, 1)
                    },
                    "conflicting_subgraph": subgraph,
                    "recommended_action": (
                        "Indicator for review: Require submission of certified architect CAD drawings, local municipal "
                        "occupancy certificate, and conduct physical inspection of instructional spaces."
                    )
                })

        return findings


# ============================================================================
# CHECK 3: Document Issuer Chronology
# Document issued before the issuing body's creation date, or validity ending before it starts
# ============================================================================
class DocumentIssuerChronologyCheck(BaseImpossibilityCheck):
    check_id = "DOCUMENT_ISSUER_CHRONOLOGY"
    name = "Document Issuer Chronology Check"
    description = (
        "Flags documents issued before the issuing authority's establishment date, "
        "or documents whose validity period expires before their issue date."
    )
    severity = "CRITICAL"
    indicator_type = "INDICATOR_FOR_REVIEW"

    def evaluate(
        self,
        graph: nx.MultiDiGraph,
        target_inst_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        findings = []

        doc_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "DOCUMENT"]
        for doc_id in doc_nodes:
            doc_data = graph.nodes[doc_id]

            # Find holding institution(s)
            holding_insts = []
            for u, _, d in graph.in_edges(doc_id, data=True):
                if d.get("relation") == "holds" and graph.nodes[u].get("type") == "INSTITUTION":
                    holding_insts.append(u)

            if target_inst_id and holding_insts and target_inst_id not in holding_insts:
                continue

            issue_dt = parse_flexible_date(doc_data.get("issue_date"))
            valid_dt = parse_flexible_date(doc_data.get("valid_till"))

            # Find connected Issuer(s) via issued_by edges
            issuer_edges = [
                (v, d) for _, v, d in graph.out_edges(doc_id, data=True)
                if d.get("relation") == "issued_by" and graph.nodes[v].get("type") == "ISSUER"
            ]

            # 3A: Document issued before issuer's creation date
            for issuer_id, edge_data in issuer_edges:
                issuer_data = graph.nodes[issuer_id]
                issuer_created_dt = parse_flexible_date(issuer_data.get("creation_date"))

                if issue_dt and issuer_created_dt and (issue_dt < issuer_created_dt):
                    subgraph_nodes = list(set([doc_id, issuer_id] + holding_insts))
                    subgraph = InstitutionTwinGraphBuilder.extract_subgraph(graph, subgraph_nodes)

                    findings.append({
                        "engine_module": "IMPOSSIBILITY_ENGINE",
                        "check_id": f"{self.check_id}_PREDATES_ISSUER",
                        "conflict_type": "DOCUMENT_PREDATES_ISSUER_CREATION",
                        "indicator_type": self.indicator_type,
                        "severity": self.severity,
                        "entity_ids": subgraph_nodes,
                        "title": f"Indicator for Review: Document Issue Predates Issuing Authority ({doc_data.get('label')})",
                        "explanation": (
                            f"Indicator for review: Document '{doc_data.get('document_type')}' (Ref: {doc_data.get('reference_number', 'N/A')}) "
                            f"bears an issue date of {issue_dt.isoformat()}, which precedes the official establishment date "
                            f"({issuer_created_dt.isoformat()}) of the issuing body '{issuer_data.get('label')}'. "
                            f"This chronological discrepancy serves as an indicator for review."
                        ),
                        "evidence_chain": {
                            "document_id": doc_id,
                            "document_type": doc_data.get("document_type"),
                            "reference_number": doc_data.get("reference_number"),
                            "reported_issue_date": issue_dt.isoformat(),
                            "issuer_name": issuer_data.get("label"),
                            "issuer_establishment_date": issuer_created_dt.isoformat()
                        },
                        "conflicting_subgraph": subgraph,
                        "recommended_action": (
                            "Indicator for review: Cross-verify certificate issuance records directly with the "
                            "designated issuing portal or state gazette registry."
                        )
                    })

            # 3B: Validity ending before it starts (inverted interval)
            if issue_dt and valid_dt and (valid_dt < issue_dt):
                subgraph_nodes = list(set([doc_id] + [v for v, _ in issuer_edges] + holding_insts))
                subgraph = InstitutionTwinGraphBuilder.extract_subgraph(graph, subgraph_nodes)

                findings.append({
                    "engine_module": "IMPOSSIBILITY_ENGINE",
                    "check_id": f"{self.check_id}_INVERTED_VALIDITY",
                    "conflict_type": "DOCUMENT_INVERTED_VALIDITY_INTERVAL",
                    "indicator_type": self.indicator_type,
                    "severity": self.severity,
                    "entity_ids": subgraph_nodes,
                    "title": f"Indicator for Review: Inverted Validity Interval ({doc_data.get('label')})",
                    "explanation": (
                        f"Indicator for review: Document '{doc_data.get('document_type')}' (Ref: {doc_data.get('reference_number', 'N/A')}) "
                        f"states a validity expiration date ({valid_dt.isoformat()}) prior to its issue date "
                        f"({issue_dt.isoformat()}). This inverted chronological validity interval serves as an indicator for review."
                    ),
                    "evidence_chain": {
                        "document_id": doc_id,
                        "document_type": doc_data.get("document_type"),
                        "reference_number": doc_data.get("reference_number"),
                        "issue_date": issue_dt.isoformat(),
                        "validity_expiry_date": valid_dt.isoformat()
                    },
                    "conflicting_subgraph": subgraph,
                    "recommended_action": (
                        "Indicator for review: Request re-issuance or clarification from applicant institution "
                        "regarding clerical date inversion or document invalidity."
                    )
                })

        return findings


# ============================================================================
# CHECK 4: Lab Equipment Programme Consistency
# Lab equipment list inconsistent with approved programmes
# ============================================================================
class LabEquipmentProgrammeConsistencyCheck(BaseImpossibilityCheck):
    check_id = "LAB_EQUIPMENT_PROGRAMME_INCONSISTENCY"
    name = "Lab Equipment Programme Consistency Check"
    description = (
        "Verifies that laboratory equipment inventories are consistent with "
        "the academic requirements of approved technical programmes."
    )
    severity = "CRITICAL"
    indicator_type = "INDICATOR_FOR_REVIEW"

    # Mandatory equipment keywords per discipline
    PROGRAMME_DOMAIN_EQUIPMENT = {
        "mechanical": {
            "keywords": ["mechanical", "automobile", "production", "mechatronics", "manufacturing", "thermal"],
            "required_sample": ["Lathe Machine", "Milling Machine", "Universal Testing Machine (UTM)", "CNC Trainer"],
            "patterns": ["lathe", "milling", "universal testing", "utm", "cnc", "heat transfer", "shaper", "fluid mechanics", "pelton", "refrigeration"]
        },
        "civil": {
            "keywords": ["civil", "structural", "environmental", "construction", "transportation"],
            "required_sample": ["Total Station", "Compression Testing Machine (CTM)", "Theodolite", "Concrete Mixer"],
            "patterns": ["total station", "theodolite", "compression testing", "ctm", "concrete mixer", "triaxial", "direct shear", "soil mechanics", "universal testing"]
        },
        "electrical": {
            "keywords": ["electrical", "eee", "power system", "electrical and electronics", "high voltage"],
            "required_sample": ["Digital Storage Oscilloscope", "Transformer Test Bench", "DC Motor-Generator Set", "Power Electronics Trainer"],
            "patterns": ["oscilloscope", "transformer", "motor-generator", "dc motor", "power electronics", "network analyzer", "synchronous machine", "ac drive"]
        },
        "chemical": {
            "keywords": ["chemical", "petrochemical", "polymer", "process engineering"],
            "required_sample": ["Fractional Distillation Column", "Tubular Flow Reactor", "Gas Chromatograph", "Heat Exchanger"],
            "patterns": ["distillation", "reactor", "heat exchanger", "gas chromatograph", "absorption", "mass transfer", "fluidization"]
        },
        "computer": {
            "keywords": ["computer", "cse", "information technology", "software", "artificial intelligence", "data science"],
            "required_sample": ["High-Performance Computing Workstations", "Managed Network Switch", "Rack Server Cluster"],
            "patterns": ["workstation", "server", "switch", "router", "cluster", "gpu", "computing", "network lab"]
        },
        "electronics": {
            "keywords": ["electronics and communication", "ece", "telecommunication", "vlsi"],
            "required_sample": ["Spectrum Analyzer", "Digital Storage Oscilloscope", "Microwave Test Bench", "DSP Starter Kit"],
            "patterns": ["spectrum analyzer", "oscilloscope", "microwave", "dsp", "antenna", "vlsi", "function generator"]
        }
    }

    def evaluate(
        self,
        graph: nx.MultiDiGraph,
        target_inst_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        findings = []

        inst_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "INSTITUTION"]
        for inst_id in inst_nodes:
            if target_inst_id and inst_id != target_inst_id:
                continue

            inst_data = graph.nodes[inst_id]

            # 1. Collect offered programmes
            programmes = []
            for _, v, d in graph.out_edges(inst_id, data=True):
                if d.get("relation") == "offers" and graph.nodes[v].get("type") == "PROGRAMME":
                    programmes.append((v, graph.nodes[v]))

            if not programmes:
                continue

            # 2. Collect all lab equipment items held by this institution
            held_labs = []
            all_equipment_items: List[str] = []
            for _, v, d in graph.out_edges(inst_id, data=True):
                if d.get("relation") == "holds" and graph.nodes[v].get("type") == "LAB":
                    held_labs.append(v)
                    lab_data = graph.nodes[v]
                    eq_list = lab_data.get("equipment") or []
                    for eq in eq_list:
                        all_equipment_items.append(str(eq).lower())

            # 3. For each programme, check curricular equipment presence
            for prog_id, prog_data in programmes:
                prog_name = str(prog_data.get("name") or prog_data.get("discipline") or "").lower()

                # Determine discipline
                matched_domain = None
                for domain_key, domain_info in self.PROGRAMME_DOMAIN_EQUIPMENT.items():
                    if any(kw in prog_name for kw in domain_info["keywords"]):
                        matched_domain = domain_info
                        break

                if not matched_domain:
                    continue

                # Check if any required patterns match the declared lab equipment
                matches_found = []
                for pattern in matched_domain["patterns"]:
                    if any(pattern in eq for eq in all_equipment_items):
                        matches_found.append(pattern)

                if len(matches_found) == 0:
                    subgraph_nodes = [inst_id, prog_id] + held_labs
                    subgraph = InstitutionTwinGraphBuilder.extract_subgraph(graph, subgraph_nodes)

                    sample_needed = ", ".join(matched_domain["required_sample"][:3])
                    findings.append({
                        "engine_module": "IMPOSSIBILITY_ENGINE",
                        "check_id": self.check_id,
                        "conflict_type": self.check_id,
                        "indicator_type": self.indicator_type,
                        "severity": self.severity,
                        "entity_ids": [inst_id, prog_id],
                        "title": f"Indicator for Review: Lab Equipment Inconsistent with Programme ({prog_data.get('label')})",
                        "explanation": (
                            f"Indicator for review: Institution offers approved programme '{prog_data.get('name')}' "
                            f"but declared laboratory equipment inventory lacks mandatory core curricular apparatus. "
                            f"None of the required domain equipment (e.g., {sample_needed}) was detected across the "
                            f"{len(held_labs)} declared laboratories. This curriculum inconsistency serves as an indicator for review."
                        ),
                        "evidence_chain": {
                            "institution_name": inst_data.get("label"),
                            "programme_name": prog_data.get("name"),
                            "declared_labs_count": len(held_labs),
                            "declared_equipment_sample": all_equipment_items[:5],
                            "expected_equipment_sample": matched_domain["required_sample"]
                        },
                        "conflicting_subgraph": subgraph,
                        "recommended_action": (
                            "Indicator for review: Issue directive requiring submission of laboratory purchase vouchers, "
                            "geo-tagged lab photos, and dispatch physical inspection team."
                        )
                    })

        return findings


# ============================================================================
# CHECK 5: Shared Document Reference Number Collision
# Same document reference number used by different institutions
# ============================================================================
class SharedDocumentReferenceCheck(BaseImpossibilityCheck):
    check_id = "SHARED_DOCUMENT_REFERENCE_COLLISION"
    name = "Shared Document Reference Collision Check"
    description = (
        "Detects identical document registration or reference numbers claimed "
        "concurrently by multiple distinct educational institutions."
    )
    severity = "CRITICAL"
    indicator_type = "INDICATOR_FOR_REVIEW"

    def evaluate(
        self,
        graph: nx.MultiDiGraph,
        target_inst_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        findings = []

        # Map reference numbers to (doc_id, inst_id)
        ref_map: Dict[str, List[Tuple[str, str]]] = {}

        doc_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "DOCUMENT"]
        for doc_id in doc_nodes:
            doc_data = graph.nodes[doc_id]
            ref_no = str(doc_data.get("reference_number") or "").strip().upper()

            if not ref_no or ref_no in ("N/A", "NONE", "NULL", "PENDING", "-", "0", "UNKNOWN"):
                continue

            # Find all holding institutions
            holding_insts = set()
            for u, _, d in graph.in_edges(doc_id, data=True):
                if d.get("relation") == "holds" and graph.nodes[u].get("type") == "INSTITUTION":
                    holding_insts.add(u)

            if not holding_insts and doc_data.get("institution_id"):
                inst_id = str(doc_data["institution_id"])
                if graph.has_node(inst_id) and graph.nodes[inst_id].get("type") == "INSTITUTION":
                    holding_insts.add(inst_id)

            for inst_id in holding_insts:
                if ref_no not in ref_map:
                    ref_map[ref_no] = []
                ref_map[ref_no].append((doc_id, inst_id))

        # Identify reference collisions across distinct institutions
        for ref_no, items in ref_map.items():
            distinct_insts = list({inst_id for doc_id, inst_id in items})
            if len(distinct_insts) > 1:
                if target_inst_id and target_inst_id not in distinct_insts:
                    continue

                doc_ids = list({doc_id for doc_id, inst_id in items})
                inst_names = [graph.nodes[iid].get("label", iid) for iid in distinct_insts]
                doc_types = list({graph.nodes[did].get("document_type", "Document") for did in doc_ids})

                subgraph_nodes = distinct_insts + doc_ids
                subgraph = InstitutionTwinGraphBuilder.extract_subgraph(graph, subgraph_nodes)

                findings.append({
                    "engine_module": "IMPOSSIBILITY_ENGINE",
                    "check_id": self.check_id,
                    "conflict_type": self.check_id,
                    "indicator_type": self.indicator_type,
                    "severity": self.severity,
                    "entity_ids": subgraph_nodes,
                    "title": f"Indicator for Review: Cross-Institutional Reference Number Reuse ({ref_no})",
                    "explanation": (
                        f"Indicator for review: The identical document reference number '{ref_no}' "
                        f"({', '.join(doc_types)}) is simultaneously claimed by {len(distinct_insts)} "
                        f"distinct institutions: {', '.join(inst_names)}. Official regulatory instruments are "
                        f"strictly single-entity certificates, which serves as an indicator for review."
                    ),
                    "evidence_chain": {
                        "reference_number": ref_no,
                        "document_types": doc_types,
                        "claimant_institutions": [
                            {"id": iid, "name": graph.nodes[iid].get("label", iid)}
                            for iid in distinct_insts
                        ],
                        "document_ids": doc_ids
                    },
                    "conflicting_subgraph": subgraph,
                    "recommended_action": (
                        "Indicator for review: Cross-reference reference number against state repository records "
                        "and issue clarification notices to both claimant institutions."
                    )
                })

        return findings


# ============================================================================
# CHECK 6: Shared Land Parcel Collision
# Same land deed / survey number claimed by distinct institutions
# ============================================================================
class SharedLandParcelCheck(BaseImpossibilityCheck):
    check_id = "SHARED_LAND_PARCEL_COLLISION"
    name = "Shared Land Parcel Collision Check"
    description = "Detects identical revenue survey numbers claimed by distinct colleges."
    severity = "CRITICAL"
    indicator_type = "INDICATOR_FOR_REVIEW"

    def evaluate(
        self,
        graph: nx.MultiDiGraph,
        target_inst_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        findings = []
        survey_map: Dict[str, List[str]] = {}

        for n, d in graph.nodes(data=True):
            if d.get("type") == "INSTITUTION":
                survey_no = str(d.get("survey_numbers") or "").strip()
                if survey_no and survey_no not in ("-", "N/A", "NONE"):
                    parts = [p.strip() for p in re.split(r"[,&]", survey_no) if p.strip()]
                    for p in parts:
                        clean_p = p.upper()
                        if clean_p not in survey_map:
                            survey_map[clean_p] = []
                        survey_map[clean_p].append(str(n))

        for s_num, inst_ids in survey_map.items():
            distinct_insts = list(set(inst_ids))
            if len(distinct_insts) > 1:
                if target_inst_id and target_inst_id not in distinct_insts:
                    continue

                inst_names = [graph.nodes[iid].get("label", iid) for iid in distinct_insts]
                subgraph = InstitutionTwinGraphBuilder.extract_subgraph(graph, distinct_insts)

                findings.append({
                    "engine_module": "IMPOSSIBILITY_ENGINE",
                    "check_id": self.check_id,
                    "conflict_type": self.check_id,
                    "indicator_type": self.indicator_type,
                    "severity": self.severity,
                    "entity_ids": distinct_insts,
                    "title": f"Indicator for Review: Conflicting Land Survey Claim ({s_num})",
                    "explanation": (
                        f"Indicator for review: The identical land revenue survey number '{s_num}' is claimed by "
                        f"{len(distinct_insts)} distinct institutions: {', '.join(inst_names)}. "
                        f"This conflicting campus title claim serves as an indicator for review."
                    ),
                    "evidence_chain": {
                        "survey_no": s_num,
                        "claimants": inst_names
                    },
                    "conflicting_subgraph": subgraph,
                    "recommended_action": (
                        "Indicator for review: Dispatch Revenue Inspector to cross-verify Khasra geo-coordinates with State Land Records."
                    )
                })

        return findings


# ============================================================================
# MAIN IMPOSSIBILITY ENGINE ORCHESTRATOR
# ============================================================================
class ImpossibilityEngine:
    """
    Pluggable Impossibility Engine running on the Institution Twin Knowledge Graph.
    Coordinates registered regulatory consistency checks and outputs indicator for review findings.
    """

    def __init__(self, checks: Optional[List[BaseImpossibilityCheck]] = None):
        self.graph = nx.MultiDiGraph()
        self.checks: List[BaseImpossibilityCheck] = []

        if checks is not None:
            for check in checks:
                self.register_check(check)
        else:
            # Register the 5 standard pluggable checks + land parcel collision
            self.register_check(DualEmploymentFacultyCheck())
            self.register_check(BuiltUpAreaDensityCheck(min_sqm_per_student=10.5, duration_years=4))
            self.register_check(DocumentIssuerChronologyCheck())
            self.register_check(LabEquipmentProgrammeConsistencyCheck())
            self.register_check(SharedDocumentReferenceCheck())
            self.register_check(SharedLandParcelCheck())

        self._build_seed_knowledge_graph()

    def register_check(self, check: BaseImpossibilityCheck):
        """Registers a new pluggable check."""
        # Replace if check_id already registered
        self.checks = [c for c in self.checks if c.check_id != check.check_id]
        self.checks.append(check)

    def unregister_check(self, check_id: str):
        """Unregisters an impossibility check by ID."""
        self.checks = [c for c in self.checks if c.check_id != check_id]

    def get_check(self, check_id: str) -> Optional[BaseImpossibilityCheck]:
        """Returns registered check by ID."""
        for c in self.checks:
            if c.check_id == check_id:
                return c
        return None

    def list_checks(self) -> List[Dict[str, Any]]:
        """Lists metadata of all registered pluggable checks."""
        return [
            {
                "check_id": c.check_id,
                "name": c.name,
                "description": c.description,
                "severity": c.severity,
                "indicator_type": c.indicator_type
            }
            for c in self.checks
        ]

    def load_graph_from_db(self, db: Session, target_inst_id: Optional[str] = None) -> nx.MultiDiGraph:
        """Loads the Institution Twin knowledge graph from the relational database."""
        self.graph = graph_builder.load_from_db(db, target_institution_id=target_inst_id)
        return self.graph

    def set_graph(self, graph: nx.MultiDiGraph):
        """Directly sets the active graph."""
        self.graph = graph

    def run_checks(
        self,
        graph: Optional[nx.MultiDiGraph] = None,
        target_inst_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Runs all registered checks against the active graph and returns
        findings with conflicting subgraphs and review indicators.
        """
        active_graph = graph if graph is not None else self.graph
        all_findings: List[Dict[str, Any]] = []

        for check in self.checks:
            check_findings = check.evaluate(active_graph, target_inst_id=target_inst_id)
            all_findings.extend(check_findings)

        return all_findings

    # Backwards-compatible alias
    def detect_all_impossibilities(self, target_inst_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Backwards-compatible API endpoint alias."""
        return self.run_checks(target_inst_id=target_inst_id)

    def get_full_graph_serialized(self) -> Dict[str, Any]:
        """Serializes current graph for UI visualization."""
        return InstitutionTwinGraphBuilder.serialize_graph(self.graph)

    def _build_seed_knowledge_graph(self):
        """Populates seed knowledge graph with synthetic baseline data and review indicator scenarios."""
        institutions = [
            {
                "id": "INST_001",
                "aicte_id": "1-109283711",
                "name": "Apex Institute of Technology & Science",
                "city": "Bengaluru",
                "state": "Karnataka",
                "approved_intake": 480,
                "built_up_area_sqm": 8500.0, # Insufficient for 480 * 4 students
                "trust_name": "Apex Vidya Foundation",
                "survey_numbers": "SY-102/4"
            },
            {
                "id": "INST_002",
                "aicte_id": "1-209384722",
                "name": "Royal College of Engineering",
                "city": "Mysuru",
                "state": "Karnataka",
                "approved_intake": 360,
                "built_up_area_sqm": 18200.0,
                "trust_name": "Royal Educational Trust",
                "survey_numbers": "SY-88/1"
            },
            {
                "id": "INST_003",
                "aicte_id": "1-309485733",
                "name": "National Academy of Technical Studies",
                "city": "Bengaluru",
                "state": "Karnataka",
                "approved_intake": 420,
                "built_up_area_sqm": 19000.0,
                "trust_name": "Apex Vidya Foundation",
                "survey_numbers": "SY-102/4"
            }
        ]

        faculty = [
            {
                "id": "FAC_101",
                "name": "Dr. R. K. Sharma",
                "pan_masked": "AB****89C",
                "aadhaar_masked": "XXXX-XXXX-9021",
                "dob": "1975-08-12",
                "designation": "Professor & Head",
                "highest_degree": "Ph.D. IIT Bombay"
            },
            {
                "id": "FAC_102",
                "name": "Dr. Priya Sundaram",
                "pan_masked": "CD****45E",
                "aadhaar_masked": "XXXX-XXXX-4412",
                "dob": "1982-11-20",
                "designation": "Associate Professor",
                "highest_degree": "Ph.D. IISc"
            }
        ]

        employments = [
            # Dual employment across INST_001 and INST_002
            {"inst_id": "INST_001", "fac_id": "FAC_101", "employment_type": "Full-Time", "role": "Professor", "start_date": "2021-08-01", "end_date": None},
            {"inst_id": "INST_002", "fac_id": "FAC_101", "employment_type": "Full-Time", "role": "Professor", "start_date": "2022-01-15", "end_date": None},
            # Single employment
            {"inst_id": "INST_001", "fac_id": "FAC_102", "employment_type": "Full-Time", "role": "Associate Professor", "start_date": "2020-07-10", "end_date": None}
        ]

        programmes = [
            {"id": "PROG_001", "name": "Mechanical Engineering", "approved_intake": 120, "academic_year": "2025-26"},
            {"id": "PROG_002", "name": "Computer Science & Engineering", "approved_intake": 180, "academic_year": "2025-26"}
        ]

        offers = [
            {"inst_id": "INST_001", "prog_id": "PROG_001", "intake": 120},
            {"inst_id": "INST_001", "prog_id": "PROG_002", "intake": 180},
            {"inst_id": "INST_002", "prog_id": "PROG_001", "intake": 120}
        ]

        labs = [
            # INST_001 only has Computer Lab (Mechanical Engineering lab equipment is missing!)
            {"id": "LAB_001", "name": "Computing & Simulation Lab", "department": "CSE", "equipment": ["Workstations", "Servers", "Gigabit Switch"]},
            # INST_002 has Mechanical Workshop
            {"id": "LAB_002", "name": "Mechanical Workshop", "department": "Mechanical", "equipment": ["Lathe Machine", "Milling Machine", "Universal Testing Machine", "CNC Trainer"]}
        ]

        issuers = [
            {"id": "ISSUER_FIRE_KA", "name": "Karnataka State Fire & Emergency Services", "issuer_type": "fire_department", "creation_date": "2020-01-01"},
            {"id": "ISSUER_BHOOMI", "name": "Karnataka Revenue Department (Bhoomi)", "issuer_type": "land_registry", "creation_date": "2000-01-01"}
        ]

        documents = [
            # Issue date 2015-06-15 predates ISSUER_FIRE_KA creation date (2020-01-01)
            {
                "id": "DOC_FIRE_001",
                "document_type": "Fire Safety Certificate",
                "reference_number": "FIR/KA/2024/99102",
                "issue_date": "2015-06-15",
                "valid_till": "2026-06-30"
            },
            # Document with inverted validity interval (validity ends before it starts)
            {
                "id": "DOC_LAND_002",
                "document_type": "Land Title Deed",
                "reference_number": "LAN/KA/2024/33011",
                "issue_date": "2023-01-01",
                "valid_till": "2021-12-31"
            },
            # Shared reference document: same ref FIR/KA/2024/99102 used by both INST_001 and INST_003
            {
                "id": "DOC_FIRE_003",
                "document_type": "Fire Safety Certificate",
                "reference_number": "FIR/KA/2024/99102",
                "issue_date": "2024-01-10",
                "valid_till": "2027-01-10"
            }
        ]

        holds = [
            {"inst_id": "INST_001", "target_id": "LAB_001", "entity_type": "LAB"},
            {"inst_id": "INST_002", "target_id": "LAB_002", "entity_type": "LAB"},
            {"inst_id": "INST_001", "target_id": "DOC_FIRE_001", "entity_type": "DOCUMENT"},
            {"inst_id": "INST_002", "target_id": "DOC_LAND_002", "entity_type": "DOCUMENT"},
            {"inst_id": "INST_003", "target_id": "DOC_FIRE_003", "entity_type": "DOCUMENT"}
        ]

        issued_by = [
            {"doc_id": "DOC_FIRE_001", "issuer_id": "ISSUER_FIRE_KA", "issue_date": "2015-06-15", "valid_till": "2026-06-30"},
            {"doc_id": "DOC_LAND_002", "issuer_id": "ISSUER_BHOOMI", "issue_date": "2023-01-01", "valid_till": "2021-12-31"},
            {"doc_id": "DOC_FIRE_003", "issuer_id": "ISSUER_FIRE_KA", "issue_date": "2024-01-10", "valid_till": "2027-01-10"}
        ]

        buildings = [
            {"id": "BLD_001", "name": "Main Academic Block", "built_up_area_sqm": 8500.0, "floors": 4},
            {"id": "BLD_002", "name": "Engineering Complex", "built_up_area_sqm": 18200.0, "floors": 6}
        ]

        holds.extend([
            {"inst_id": "INST_001", "target_id": "BLD_001", "entity_type": "BUILDING"},
            {"inst_id": "INST_002", "target_id": "BLD_002", "entity_type": "BUILDING"}
        ])

        locations = [
            {"id": "LOC_001", "city": "Bengaluru", "state": "Karnataka", "address": "Devanahalli Tech Zone"},
            {"id": "LOC_002", "city": "Mysuru", "state": "Karnataka", "address": "Hootagalli Industrial Area"}
        ]

        located_at = [
            {"source_id": "INST_001", "location_id": "LOC_001"},
            {"source_id": "INST_002", "location_id": "LOC_002"},
            {"source_id": "BLD_001", "location_id": "LOC_001"},
            {"source_id": "BLD_002", "location_id": "LOC_002"}
        ]

        self.graph = graph_builder.build_from_records(
            institutions=institutions,
            faculty=faculty,
            programmes=programmes,
            documents=documents,
            labs=labs,
            buildings=buildings,
            locations=locations,
            issuers=issuers,
            employments=employments,
            holds=holds,
            offers=offers,
            issued_by=issued_by,
            located_at=located_at
        )


# Global singleton
impossibility_engine = ImpossibilityEngine()
