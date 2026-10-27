"""
Institution Twin Graph Builder using NetworkX.
Constructs a comprehensive knowledge graph representing institutional digital twins:
- Nodes: Institution, Faculty, Programme, Document, Lab, Building, Location, Issuer
- Edges:
  - employs (start_date, end_date, employment_type: Full-Time / Part-Time, role)
  - offers (intake, academic_year)
  - holds (Institution -> Document, Institution -> Building, Institution -> Lab)
  - issued_by (Document -> Issuer)
  - located_at (Institution / Building / Lab -> Location)
Loads directly from SQLAlchemy database models and supports dictionary-based records.
"""
from typing import Dict, List, Any, Optional, Set, Iterable
import networkx as nx
from sqlalchemy.orm import Session

from backend.app.models.models import (
    Institution, Faculty, FacultyEmployment, Programme,
    Document, Lab, Building, Location, Issuer
)


class InstitutionTwinGraphBuilder:
    """
    Constructs and serializes the NetworkX 'Institution Twin' Knowledge Graph
    from relational database models or structured data dictionaries.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def create_empty_graph(self) -> nx.MultiDiGraph:
        """Initializes a new empty MultiDiGraph."""
        self.graph = nx.MultiDiGraph()
        return self.graph

    # -------------------------------------------------------------------------
    # Node Addition Helpers
    # -------------------------------------------------------------------------

    def add_institution_node(self, graph: nx.MultiDiGraph, inst_id: str, data: Dict[str, Any]):
        """Adds an Institution node."""
        graph.add_node(
            str(inst_id),
            type="INSTITUTION",
            label=data.get("name") or str(inst_id),
            name=data.get("name", ""),
            aicte_id=data.get("aicte_id", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            category=data.get("category", "Engineering & Technology"),
            approved_intake=int(data.get("approved_intake") or 0),
            total_built_up_area_sqm=float(data.get("total_built_up_area_sqm") or data.get("built_up_area_sqm") or 0.0),
            land_area_acres=float(data.get("land_area_acres") or 0.0),
            trust_name=data.get("trust_name", ""),
            survey_numbers=data.get("survey_numbers", ""),
            status=data.get("status", "ACTIVE")
        )

    def add_faculty_node(self, graph: nx.MultiDiGraph, faculty_id: str, data: Dict[str, Any]):
        """Adds a Faculty node."""
        graph.add_node(
            str(faculty_id),
            type="FACULTY",
            label=data.get("name") or str(faculty_id),
            name=data.get("name", ""),
            faculty_code=data.get("faculty_code", str(faculty_id)),
            pan_masked=data.get("pan_masked", ""),
            aadhaar_masked=data.get("aadhaar_masked", ""),
            dob=data.get("dob", ""),
            designation=data.get("designation", ""),
            highest_degree=data.get("highest_degree") or data.get("qualification", "")
        )

    def add_programme_node(self, graph: nx.MultiDiGraph, prog_id: str, data: Dict[str, Any]):
        """Adds a Programme node."""
        graph.add_node(
            str(prog_id),
            type="PROGRAMME",
            label=data.get("name") or str(prog_id),
            name=data.get("name", ""),
            programme_code=data.get("programme_code", str(prog_id)),
            degree_level=data.get("degree_level", "UG"),
            approved_intake=int(data.get("approved_intake") or 60),
            academic_year=data.get("academic_year", "2025-26"),
            discipline=data.get("discipline") or data.get("name", "")
        )

    def add_document_node(self, graph: nx.MultiDiGraph, doc_id: str, data: Dict[str, Any]):
        """Adds a Document node."""
        ref_no = data.get("reference_number")
        if not ref_no and isinstance(data.get("structured_fields"), dict):
            ref_no = data["structured_fields"].get("reference_number") or data["structured_fields"].get("noc_number")

        issue_d = data.get("issue_date")
        if not issue_d and isinstance(data.get("structured_fields"), dict):
            issue_d = data["structured_fields"].get("issue_date")

        valid_d = data.get("valid_till") or data.get("validity_date")
        if not valid_d and isinstance(data.get("structured_fields"), dict):
            valid_d = data["structured_fields"].get("valid_till") or data["structured_fields"].get("validity_date")

        graph.add_node(
            str(doc_id),
            type="DOCUMENT",
            label=data.get("document_type") or str(doc_id),
            document_type=data.get("document_type", "Document"),
            reference_number=str(ref_no or "").strip(),
            issue_date=str(issue_d or "").strip(),
            valid_till=str(valid_d or "").strip(),
            filename=data.get("filename", ""),
            file_hash=data.get("file_hash", ""),
            institution_id=str(data.get("institution_id") or "")
        )

    def add_lab_node(self, graph: nx.MultiDiGraph, lab_id: str, data: Dict[str, Any]):
        """Adds a Lab node."""
        equipment = data.get("equipment") or []
        if isinstance(equipment, str):
            equipment = [item.strip() for item in equipment.split(",") if item.strip()]

        graph.add_node(
            str(lab_id),
            type="LAB",
            label=data.get("name") or str(lab_id),
            name=data.get("name", ""),
            department=data.get("department", ""),
            equipment=list(equipment),
            capacity=int(data.get("capacity") or 30),
            area_sqm=float(data.get("area_sqm") or 75.0)
        )

    def add_building_node(self, graph: nx.MultiDiGraph, bld_id: str, data: Dict[str, Any]):
        """Adds a Building node."""
        graph.add_node(
            str(bld_id),
            type="BUILDING",
            label=data.get("name") or str(bld_id),
            name=data.get("name", ""),
            building_code=data.get("building_code", str(bld_id)),
            building_type=data.get("building_type", "Instructional"),
            built_up_area_sqm=float(data.get("built_up_area_sqm") or 0.0),
            floors=int(data.get("floors") or 1)
        )

    def add_location_node(self, graph: nx.MultiDiGraph, loc_id: str, data: Dict[str, Any]):
        """Adds a Location node."""
        label_text = data.get("city", "")
        if data.get("state"):
            label_text = f"{label_text}, {data['state']}" if label_text else data["state"]

        graph.add_node(
            str(loc_id),
            type="LOCATION",
            label=label_text or str(loc_id),
            city=data.get("city", ""),
            state=data.get("state", ""),
            district=data.get("district", ""),
            address=data.get("address", ""),
            latitude=float(data["latitude"]) if data.get("latitude") is not None else None,
            longitude=float(data["longitude"]) if data.get("longitude") is not None else None,
            survey_numbers=data.get("survey_numbers", "")
        )

    def add_issuer_node(self, graph: nx.MultiDiGraph, issuer_id: str, data: Dict[str, Any]):
        """Adds an Issuer node."""
        graph.add_node(
            str(issuer_id),
            type="ISSUER",
            label=data.get("name") or str(issuer_id),
            name=data.get("name", ""),
            issuer_type=data.get("issuer_type", ""),
            creation_date=str(data.get("creation_date") or "").strip(),
            state=data.get("state", ""),
            authority_level=data.get("authority_level", "STATE")
        )

    # -------------------------------------------------------------------------
    # Edge Addition Helpers
    # -------------------------------------------------------------------------

    def add_employs_edge(
        self,
        graph: nx.MultiDiGraph,
        inst_id: str,
        faculty_id: str,
        start_date: str,
        end_date: Optional[str] = None,
        employment_type: str = "Full-Time",
        role: str = "Faculty",
        department: Optional[str] = None
    ):
        """Adds an employs edge connecting Institution and Faculty."""
        graph.add_edge(
            str(inst_id),
            str(faculty_id),
            relation="employs",
            start_date=str(start_date or "").strip(),
            end_date=str(end_date).strip() if end_date else None,
            employment_type=str(employment_type or "Full-Time"),
            role=str(role or "Faculty"),
            department=str(department or "")
        )

    def add_offers_edge(
        self,
        graph: nx.MultiDiGraph,
        inst_id: str,
        prog_id: str,
        intake: Optional[int] = None,
        academic_year: str = "2025-26"
    ):
        """Adds an offers edge connecting Institution and Programme."""
        graph.add_edge(
            str(inst_id),
            str(prog_id),
            relation="offers",
            approved_intake=intake,
            academic_year=str(academic_year)
        )

    def add_holds_edge(
        self,
        graph: nx.MultiDiGraph,
        inst_id: str,
        target_id: str,
        entity_type: Optional[str] = None
    ):
        """Adds a holds edge (Institution -> Document / Building / Lab)."""
        graph.add_edge(
            str(inst_id),
            str(target_id),
            relation="holds",
            entity_type=entity_type
        )

    def add_issued_by_edge(
        self,
        graph: nx.MultiDiGraph,
        doc_id: str,
        issuer_id: str,
        issue_date: Optional[str] = None,
        valid_till: Optional[str] = None,
        reference_number: Optional[str] = None
    ):
        """Adds an issued_by edge connecting Document and Issuer."""
        graph.add_edge(
            str(doc_id),
            str(issuer_id),
            relation="issued_by",
            issue_date=issue_date,
            valid_till=valid_till,
            reference_number=reference_number
        )

    def add_located_at_edge(
        self,
        graph: nx.MultiDiGraph,
        source_id: str,
        location_id: str
    ):
        """Adds a located_at edge connecting Institution/Building/Lab to Location."""
        graph.add_edge(
            str(source_id),
            str(location_id),
            relation="located_at"
        )

    # -------------------------------------------------------------------------
    # Database Loader
    # -------------------------------------------------------------------------

    def load_from_db(
        self,
        db: Session,
        target_institution_id: Optional[str] = None
    ) -> nx.MultiDiGraph:
        """
        Queries database models and builds the full Institution Twin MultiDiGraph.
        """
        graph = self.create_empty_graph()

        # 1. Institutions
        inst_query = db.query(Institution)
        if target_institution_id:
            # Match either integer ID or string aicte_id
            if str(target_institution_id).isdigit():
                inst_query = inst_query.filter(
                    (Institution.id == int(target_institution_id)) | 
                    (Institution.aicte_id == target_institution_id)
                )
            else:
                inst_query = inst_query.filter(Institution.aicte_id == target_institution_id)

        institutions = inst_query.all()
        inst_id_set = {str(inst.id) for inst in institutions}
        inst_node_map = {}

        for inst in institutions:
            node_key = f"INST_{inst.id}"
            inst_node_map[inst.id] = node_key
            self.add_institution_node(
                graph,
                node_key,
                {
                    "name": inst.name,
                    "aicte_id": inst.aicte_id,
                    "city": inst.city,
                    "state": inst.state,
                    "category": inst.category,
                    "approved_intake": inst.approved_intake,
                    "total_built_up_area_sqm": inst.total_built_up_area_sqm,
                    "land_area_acres": inst.land_area_acres,
                    "trust_name": inst.trust_name,
                    "survey_numbers": inst.survey_numbers,
                    "status": inst.status
                }
            )

        # 2. Locations
        loc_query = db.query(Location)
        locations = loc_query.all()
        loc_node_map = {}
        for loc in locations:
            node_key = f"LOC_{loc.id}"
            loc_node_map[loc.id] = node_key
            self.add_location_node(
                graph,
                node_key,
                {
                    "city": loc.city,
                    "state": loc.state,
                    "district": loc.district,
                    "address": loc.address,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "survey_numbers": loc.survey_numbers
                }
            )
            # Edge: Institution -> Location
            if loc.institution_id and loc.institution_id in inst_node_map:
                self.add_located_at_edge(graph, inst_node_map[loc.institution_id], node_key)

        # Also create implicit Location nodes for institutions with city/state if no explicit Location model
        for inst in institutions:
            inst_key = inst_node_map[inst.id]
            # Check if inst has a location edge
            has_loc_edge = any(
                d.get("relation") == "located_at" for _, _, d in graph.out_edges(inst_key, data=True)
            )
            if not has_loc_edge and (inst.city or inst.state):
                loc_key = f"LOC_INST_{inst.id}"
                self.add_location_node(
                    graph,
                    loc_key,
                    {
                        "city": inst.city,
                        "state": inst.state,
                        "address": inst.address or f"{inst.city}, {inst.state}",
                        "survey_numbers": inst.survey_numbers
                    }
                )
                self.add_located_at_edge(graph, inst_key, loc_key)

        # 3. Buildings
        buildings = db.query(Building).all()
        bld_node_map = {}
        for bld in buildings:
            if bld.institution_id not in inst_node_map:
                continue
            inst_key = inst_node_map[bld.institution_id]
            bld_key = f"BLD_{bld.id}"
            bld_node_map[bld.id] = bld_key
            self.add_building_node(
                graph,
                bld_key,
                {
                    "name": bld.name,
                    "building_code": bld.building_code,
                    "building_type": bld.building_type,
                    "built_up_area_sqm": bld.built_up_area_sqm,
                    "floors": bld.floors
                }
            )
            # Edge: Institution holds Building
            self.add_holds_edge(graph, inst_key, bld_key, entity_type="BUILDING")

            # Edge: Building located_at Location
            if bld.location_id and bld.location_id in loc_node_map:
                self.add_located_at_edge(graph, bld_key, loc_node_map[bld.location_id])

        # 4. Labs
        labs = db.query(Lab).all()
        for lab in labs:
            if lab.institution_id not in inst_node_map:
                continue
            inst_key = inst_node_map[lab.institution_id]
            lab_key = f"LAB_{lab.id}"
            self.add_lab_node(
                graph,
                lab_key,
                {
                    "name": lab.name,
                    "department": lab.department,
                    "equipment": lab.equipment,
                    "capacity": lab.capacity,
                    "area_sqm": lab.area_sqm
                }
            )
            # Edge: Institution holds Lab
            self.add_holds_edge(graph, inst_key, lab_key, entity_type="LAB")

        # 5. Programmes
        programmes = db.query(Programme).all()
        for prog in programmes:
            if prog.institution_id not in inst_node_map:
                continue
            inst_key = inst_node_map[prog.institution_id]
            prog_key = f"PROG_{prog.id}"
            self.add_programme_node(
                graph,
                prog_key,
                {
                    "name": prog.name,
                    "programme_code": prog.programme_code,
                    "degree_level": prog.degree_level,
                    "approved_intake": prog.approved_intake,
                    "academic_year": prog.academic_year
                }
            )
            # Edge: Institution offers Programme
            self.add_offers_edge(
                graph,
                inst_key,
                prog_key,
                intake=prog.approved_intake,
                academic_year=prog.academic_year
            )

        # 6. Issuers
        issuers = db.query(Issuer).all()
        issuer_node_map = {}
        for iss in issuers:
            iss_key = f"ISSUER_{iss.id}"
            issuer_node_map[iss.id] = iss_key
            self.add_issuer_node(
                graph,
                iss_key,
                {
                    "name": iss.name,
                    "issuer_type": iss.issuer_type,
                    "creation_date": iss.creation_date,
                    "state": iss.state,
                    "authority_level": iss.authority_level
                }
            )

        # 7. Documents
        documents = db.query(Document).all()
        for doc in documents:
            inst_id = doc.institution_id
            if not inst_id and doc.application:
                inst_id = doc.application.institution_id

            if not inst_id or inst_id not in inst_node_map:
                continue

            inst_key = inst_node_map[inst_id]
            doc_key = f"DOC_{doc.id}"

            self.add_document_node(
                graph,
                doc_key,
                {
                    "document_type": doc.document_type,
                    "reference_number": doc.reference_number,
                    "issue_date": doc.issue_date,
                    "valid_till": doc.valid_till,
                    "filename": doc.filename,
                    "file_hash": doc.file_hash,
                    "structured_fields": doc.structured_fields,
                    "institution_id": inst_key
                }
            )

            # Edge: Institution holds Document
            self.add_holds_edge(graph, inst_key, doc_key, entity_type="DOCUMENT")

            # Edge: Document issued_by Issuer
            if doc.issuer_id and doc.issuer_id in issuer_node_map:
                iss_key = issuer_node_map[doc.issuer_id]
                self.add_issued_by_edge(
                    graph,
                    doc_key,
                    iss_key,
                    issue_date=doc.issue_date,
                    valid_till=doc.valid_till,
                    reference_number=doc.reference_number
                )
            elif isinstance(doc.structured_fields, dict) and doc.structured_fields.get("issuer_id"):
                raw_iss_id = doc.structured_fields.get("issuer_id")
                # Find matching issuer
                for iss_id_int, node_id_str in issuer_node_map.items():
                    if str(iss_id_int) == str(raw_iss_id) or node_id_str == str(raw_iss_id):
                        self.add_issued_by_edge(
                            graph,
                            doc_key,
                            node_id_str,
                            issue_date=doc.issue_date,
                            valid_till=doc.valid_till,
                            reference_number=doc.reference_number
                        )
                        break

        # 8. Faculty & Employments
        faculty_members = db.query(Faculty).all()
        fac_node_map = {}
        for fac in faculty_members:
            fac_key = f"FAC_{fac.id}"
            fac_node_map[fac.id] = fac_key
            self.add_faculty_node(
                graph,
                fac_key,
                {
                    "name": fac.name,
                    "faculty_code": fac.faculty_code,
                    "pan_masked": fac.pan_masked,
                    "aadhaar_masked": fac.aadhaar_masked,
                    "dob": fac.dob,
                    "designation": fac.designation,
                    "highest_degree": fac.highest_degree
                }
            )

        employments = db.query(FacultyEmployment).all()
        for emp in employments:
            if emp.institution_id not in inst_node_map or emp.faculty_id not in fac_node_map:
                continue
            inst_key = inst_node_map[emp.institution_id]
            fac_key = fac_node_map[emp.faculty_id]

            self.add_employs_edge(
                graph,
                inst_key,
                fac_key,
                start_date=emp.start_date,
                end_date=emp.end_date,
                employment_type=emp.employment_type,
                role=emp.role,
                department=emp.department
            )

        self.graph = graph
        return self.graph

    # -------------------------------------------------------------------------
    # Record-Based Loader (Testing / Standalone)
    # -------------------------------------------------------------------------

    def build_from_records(
        self,
        institutions: Optional[List[Dict[str, Any]]] = None,
        faculty: Optional[List[Dict[str, Any]]] = None,
        programmes: Optional[List[Dict[str, Any]]] = None,
        documents: Optional[List[Dict[str, Any]]] = None,
        labs: Optional[List[Dict[str, Any]]] = None,
        buildings: Optional[List[Dict[str, Any]]] = None,
        locations: Optional[List[Dict[str, Any]]] = None,
        issuers: Optional[List[Dict[str, Any]]] = None,
        employments: Optional[List[Dict[str, Any]]] = None,
        holds: Optional[List[Dict[str, Any]]] = None,
        offers: Optional[List[Dict[str, Any]]] = None,
        issued_by: Optional[List[Dict[str, Any]]] = None,
        located_at: Optional[List[Dict[str, Any]]] = None
    ) -> nx.MultiDiGraph:
        """
        Builds the Institution Twin MultiDiGraph directly from dictionary records.
        """
        graph = self.create_empty_graph()

        # Add Nodes
        for inst in (institutions or []):
            i_id = inst.get("id") or inst.get("institution_id")
            self.add_institution_node(graph, i_id, inst)

        for fac in (faculty or []):
            f_id = fac.get("id") or fac.get("faculty_id")
            self.add_faculty_node(graph, f_id, fac)

        for prog in (programmes or []):
            p_id = prog.get("id") or prog.get("programme_id")
            self.add_programme_node(graph, p_id, prog)

        for doc in (documents or []):
            d_id = doc.get("id") or doc.get("document_id")
            self.add_document_node(graph, d_id, doc)

        for lab in (labs or []):
            l_id = lab.get("id") or lab.get("lab_id")
            self.add_lab_node(graph, l_id, lab)

        for bld in (buildings or []):
            b_id = bld.get("id") or bld.get("building_id")
            self.add_building_node(graph, b_id, bld)

        for loc in (locations or []):
            loc_id = loc.get("id") or loc.get("location_id")
            self.add_location_node(graph, loc_id, loc)

        for iss in (issuers or []):
            iss_id = iss.get("id") or iss.get("issuer_id")
            self.add_issuer_node(graph, iss_id, iss)

        # Add Edges: employs
        for emp in (employments or []):
            inst_id = emp.get("institution_id") or emp.get("inst_id")
            fac_id = emp.get("faculty_id") or emp.get("fac_id")
            self.add_employs_edge(
                graph,
                inst_id,
                fac_id,
                start_date=emp.get("start_date") or emp.get("doj", "2020-01-01"),
                end_date=emp.get("end_date"),
                employment_type=emp.get("employment_type") or emp.get("role", "Full-Time"),
                role=emp.get("role", "Professor"),
                department=emp.get("department")
            )

        # Add Edges: holds
        for h in (holds or []):
            inst_id = h.get("institution_id") or h.get("inst_id")
            target_id = h.get("target_id") or h.get("entity_id") or h.get("document_id") or h.get("building_id") or h.get("lab_id")
            self.add_holds_edge(graph, inst_id, target_id, entity_type=h.get("entity_type"))

        # Add Edges: offers
        for o in (offers or []):
            inst_id = o.get("institution_id") or o.get("inst_id")
            prog_id = o.get("programme_id") or o.get("prog_id")
            self.add_offers_edge(
                graph,
                inst_id,
                prog_id,
                intake=o.get("intake"),
                academic_year=o.get("academic_year", "2025-26")
            )

        # Add Edges: issued_by
        for ib in (issued_by or []):
            doc_id = ib.get("document_id") or ib.get("doc_id")
            issuer_id = ib.get("issuer_id")
            self.add_issued_by_edge(
                graph,
                doc_id,
                issuer_id,
                issue_date=ib.get("issue_date"),
                valid_till=ib.get("valid_till"),
                reference_number=ib.get("reference_number")
            )

        # Add Edges: located_at
        for loc_e in (located_at or []):
            src_id = loc_e.get("source_id") or loc_e.get("institution_id") or loc_e.get("building_id")
            loc_id = loc_e.get("location_id")
            self.add_located_at_edge(graph, src_id, loc_id)

        self.graph = graph
        return self.graph

    # -------------------------------------------------------------------------
    # Graph Serialization & Subgraph Extraction
    # -------------------------------------------------------------------------

    @staticmethod
    def serialize_graph(graph: nx.MultiDiGraph) -> Dict[str, Any]:
        """Serializes NetworkX graph to JSON-compatible node/edge structure."""
        nodes = []
        for n, d in graph.nodes(data=True):
            node_item = dict(d)
            node_item["id"] = str(n)
            nodes.append(node_item)

        edges = []
        for u, v, k, d in graph.edges(keys=True, data=True):
            edge_item = dict(d)
            edge_item["source"] = str(u)
            edge_item["target"] = str(v)
            edge_item["key"] = k
            edges.append(edge_item)

        # Summary statistics
        summary = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "total_institutions": len([n for n in nodes if n.get("type") == "INSTITUTION"]),
            "total_faculty": len([n for n in nodes if n.get("type") == "FACULTY"]),
            "total_programmes": len([n for n in nodes if n.get("type") == "PROGRAMME"]),
            "total_documents": len([n for n in nodes if n.get("type") == "DOCUMENT"]),
            "total_labs": len([n for n in nodes if n.get("type") == "LAB"]),
            "total_buildings": len([n for n in nodes if n.get("type") == "BUILDING"]),
            "total_locations": len([n for n in nodes if n.get("type") == "LOCATION"]),
            "total_issuers": len([n for n in nodes if n.get("type") == "ISSUER"])
        }

        return {
            "nodes": nodes,
            "edges": edges,
            "summary": summary
        }

    @staticmethod
    def extract_subgraph(
        graph: nx.MultiDiGraph,
        node_ids: Iterable[str],
        include_connecting_edges: bool = True
    ) -> Dict[str, Any]:
        """
        Extracts a conflicting subgraph (nodes + edges as JSON for UI rendering)
        based on a set of entity node IDs.
        """
        node_set = {str(n) for n in node_ids if graph.has_node(str(n))}
        
        nodes = []
        for n in node_set:
            d = graph.nodes[n]
            node_item = dict(d)
            node_item["id"] = str(n)
            nodes.append(node_item)

        edges = []
        if include_connecting_edges:
            for u in node_set:
                for v in node_set:
                    if graph.has_edge(u, v):
                        edge_dict = graph.get_edge_data(u, v)
                        for k, d in edge_dict.items():
                            edge_item = dict(d)
                            edge_item["source"] = str(u)
                            edge_item["target"] = str(v)
                            edge_item["key"] = k
                            edges.append(edge_item)

        return {
            "nodes": nodes,
            "edges": edges
        }


# Global singleton instance
graph_builder = InstitutionTwinGraphBuilder()
