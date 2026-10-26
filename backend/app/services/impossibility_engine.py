"""
Impossibility Engine using NetworkX Knowledge Graph.
Models complex inter-institutional relationships:
- Institutions, Faculty, Land Parcels, Educational Trusts.
Detects mathematically or physically impossible claims:
1. Dual Employment / Ghost Faculty (Same faculty full-time at multiple colleges)
2. Land Sharing / Survey Number collision (Same land deed claimed by distinct institutions)
3. Physical Density Impossibility (Built-up area physically incapable of holding intake)
4. Trust Overlap / Cadre Discrepancies
"""
import networkx as nx
from typing import Dict, List, Any, Optional

class ImpossibilityEngine:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self._build_seed_knowledge_graph()

    def _build_seed_knowledge_graph(self):
        """Constructs synthetic baseline graph across multiple regional institutions."""
        self.graph.clear()
        
        # 1. Institutions
        institutions = [
            {
                "id": "INST_001",
                "aicte_id": "1-109283711",
                "name": "Apex Institute of Technology & Science",
                "city": "Bengaluru",
                "state": "Karnataka",
                "approved_intake": 480,
                "built_up_area_sqm": 8500.0,  # Insufficient area for 480 intake
                "trust": "Apex Vidya Foundation"
            },
            {
                "id": "INST_002",
                "aicte_id": "1-209384722",
                "name": "Royal College of Engineering",
                "city": "Mysuru",
                "state": "Karnataka",
                "approved_intake": 360,
                "built_up_area_sqm": 14200.0,
                "trust": "Royal Educational Trust"
            },
            {
                "id": "INST_003",
                "aicte_id": "1-309485733",
                "name": "National Academy of Technical Studies",
                "city": "Bengaluru",
                "state": "Karnataka",
                "approved_intake": 420,
                "built_up_area_sqm": 16000.0,
                "trust": "Apex Vidya Foundation"
            },
            {
                "id": "INST_004",
                "aicte_id": "1-409586744",
                "name": "Zenith Institute of Engineering",
                "city": "Mangaluru",
                "state": "Karnataka",
                "approved_intake": 300,
                "built_up_area_sqm": 12500.0,
                "trust": "Zenith Charitable Trust"
            }
        ]
        
        for inst in institutions:
            self.graph.add_node(
                inst["id"],
                type="INSTITUTION",
                label=inst["name"],
                aicte_id=inst["aicte_id"],
                city=inst["city"],
                state=inst["state"],
                intake=inst["approved_intake"],
                area_sqm=inst["built_up_area_sqm"],
                trust=inst["trust"]
            )

        # 2. Faculty (Including intentional dual-employment ghost faculty)
        faculty_roster = [
            {
                "id": "FAC_101",
                "name": "Dr. R. K. Sharma",
                "designation": "Professor & Head (CSE)",
                "pan_masked": "AB****89C",
                "aadhaar_masked": "XXXX-XXXX-9021",
                "highest_degree": "Ph.D. IIT Bombay",
                # This professor is claimed as full-time by BOTH INST_001 and INST_002!
                "appointments": [
                    {"inst_id": "INST_001", "role": "Professor (Full-Time)", "doj": "2021-08-01"},
                    {"inst_id": "INST_002", "role": "Professor (Full-Time)", "doj": "2022-01-15"}
                ]
            },
            {
                "id": "FAC_102",
                "name": "Dr. Priya Sundaram",
                "designation": "Associate Professor",
                "pan_masked": "CD****45E",
                "aadhaar_masked": "XXXX-XXXX-4412",
                "highest_degree": "Ph.D. IISc",
                "appointments": [
                    {"inst_id": "INST_001", "role": "Associate Professor", "doj": "2020-07-10"}
                ]
            },
            {
                "id": "FAC_103",
                "name": "Prof. Amit Varma",
                "designation": "Assistant Professor",
                "pan_masked": "EF****12G",
                "aadhaar_masked": "XXXX-XXXX-7729",
                "highest_degree": "M.Tech NITK",
                "appointments": [
                    {"inst_id": "INST_002", "role": "Assistant Professor", "doj": "2023-06-01"}
                ]
            },
            {
                "id": "FAC_104",
                "name": "Dr. Suresh N.",
                "designation": "Professor & Dean",
                "pan_masked": "GH****78K",
                "aadhaar_masked": "XXXX-XXXX-3388",
                "highest_degree": "Ph.D. Anna Univ",
                # Dual claimed across INST_003 and INST_004 (140 km apart!)
                "appointments": [
                    {"inst_id": "INST_003", "role": "Dean & Professor (Full-Time)", "doj": "2019-09-01"},
                    {"inst_id": "INST_004", "role": "Professor (Full-Time)", "doj": "2023-11-01"}
                ]
            }
        ]

        for fac in faculty_roster:
            self.graph.add_node(
                fac["id"],
                type="FACULTY",
                label=fac["name"],
                pan_masked=fac["pan_masked"],
                aadhaar_masked=fac["aadhaar_masked"],
                designation=fac["designation"],
                degree=fac["highest_degree"]
            )
            for appt in fac["appointments"]:
                self.graph.add_edge(
                    fac["id"],
                    appt["inst_id"],
                    relation="EMPLOYED_AS_FULL_TIME",
                    role=appt["role"],
                    doj=appt["doj"]
                )

        # 3. Land Parcels (Including parcel sharing collision)
        land_parcels = [
            {
                "id": "LAND_PARCEL_A",
                "survey_no": "Sy. No. 42/1 & 42/2",
                "revenue_village": "Devanahalli",
                "acres": 6.2,
                "owners": ["INST_001", "INST_003"] # SAME LAND CLAIMED BY TWO COLLEGES!
            },
            {
                "id": "LAND_PARCEL_B",
                "survey_no": "Sy. No. 108/3",
                "revenue_village": "Hootagalli",
                "acres": 7.5,
                "owners": ["INST_002"]
            },
            {
                "id": "LAND_PARCEL_C",
                "survey_no": "Sy. No. 71/B",
                "revenue_village": "Surathkal",
                "acres": 5.8,
                "owners": ["INST_004"]
            }
        ]

        for land in land_parcels:
            self.graph.add_node(
                land["id"],
                type="LAND_PARCEL",
                label=land["survey_no"],
                village=land["revenue_village"],
                acres=land["acres"]
            )
            for inst_id in land["owners"]:
                self.graph.add_edge(
                    inst_id,
                    land["id"],
                    relation="CLAIMS_CAMPUS_LAND",
                    acres=land["acres"]
                )

    def detect_all_impossibilities(self, target_inst_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Runs comprehensive conflict detection queries on the knowledge graph:
        1. Ghost Faculty (Dual full-time employment)
        2. Land parcel survey number collisions
        3. Built-up area physical density violation (< 10.5 sqm/student)
        """
        anomalies = []

        # 1. Check Ghost Faculty (Dual Employment)
        faculty_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "FACULTY"]
        for fac_id in faculty_nodes:
            fac_data = self.graph.nodes[fac_id]
            # Find all institutions this faculty is connected to via EMPLOYED_AS_FULL_TIME
            edges = self.graph.out_edges(fac_id, data=True)
            full_time_edges = [
                (u, v, d) for u, v, d in edges 
                if d.get("relation") == "EMPLOYED_AS_FULL_TIME"
            ]
            
            if len(full_time_edges) > 1:
                inst_ids = [v for u, v, d in full_time_edges]
                inst_names = [self.graph.nodes[iid].get("label", iid) for iid in inst_ids]
                
                # Check if target_inst_id is involved
                if target_inst_id and (target_inst_id not in inst_ids):
                    continue
                
                anomalies.append({
                    "engine_module": "IMPOSSIBILITY_ENGINE",
                    "conflict_type": "DUAL_EMPLOYMENT_GHOST_FACULTY",
                    "severity": "CRITICAL",
                    "entity_id": fac_id,
                    "entity_name": fac_data.get("label"),
                    "pan_masked": fac_data.get("pan_masked"),
                    "aadhaar_masked": fac_data.get("aadhaar_masked"),
                    "involved_institutions": [
                        {"id": iid, "name": self.graph.nodes[iid].get("label"), "city": self.graph.nodes[iid].get("city")}
                        for iid in inst_ids
                    ],
                    "title": f"Impossible Multi-Campus Appointment: {fac_data.get('label')}",
                    "explanation": (
                        f"Faculty member {fac_data.get('label')} (PAN: {fac_data.get('pan_masked')}) is simultaneously "
                        f"reported as a Full-Time regular faculty member across {len(inst_ids)} separate institutions: "
                        f"{', '.join(inst_names)}. Statutory regulations mandate single-institution full-time exclusivity."
                    ),
                    "evidence_chain": {
                        "faculty_id": fac_id,
                        "degrees": fac_data.get("degree"),
                        "employers": [
                            {"inst_name": self.graph.nodes[v].get("label"), "role": d.get("role"), "doj": d.get("doj")}
                            for u, v, d in full_time_edges
                        ]
                    },
                    "recommended_action": "Issue formal Show-Cause Notice to both institutions and request biometric/Form 16 verification."
                })

        # 2. Check Land Parcel Collision (Shared Revenue Survey Number)
        land_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "LAND_PARCEL"]
        for land_id in land_nodes:
            land_data = self.graph.nodes[land_id]
            # Inbound edges from institutions claiming this land
            in_edges = self.graph.in_edges(land_id, data=True)
            claiming_insts = [
                u for u, v, d in in_edges 
                if d.get("relation") == "CLAIMS_CAMPUS_LAND"
            ]
            
            if len(claiming_insts) > 1:
                inst_names = [self.graph.nodes[iid].get("label", iid) for iid in claiming_insts]
                
                if target_inst_id and (target_inst_id not in claiming_insts):
                    continue
                    
                anomalies.append({
                    "engine_module": "IMPOSSIBILITY_ENGINE",
                    "conflict_type": "SHARED_LAND_PARCEL_COLLISION",
                    "severity": "CRITICAL",
                    "entity_id": land_id,
                    "entity_name": land_data.get("label"),
                    "involved_institutions": [
                        {"id": iid, "name": self.graph.nodes[iid].get("label")} 
                        for iid in claiming_insts
                    ],
                    "title": f"Conflicting Land Title Claim: {land_data.get('label')}",
                    "explanation": (
                        f"The identical land survey number ({land_data.get('label')}, {land_data.get('acres')} acres in "
                        f"{land_data.get('village')}) is claimed by {len(claiming_insts)} distinct institutions: "
                        f"{', '.join(inst_names)} without joint-campus regulatory approval."
                    ),
                    "evidence_chain": {
                        "survey_no": land_data.get("label"),
                        "acres": land_data.get("acres"),
                        "claimants": inst_names
                    },
                    "recommended_action": "Dispatch Revenue Inspector to cross-verify Khasra geo-coordinates with State Land Records."
                })

        # 3. Check Physical Built-Up Area Density Impossibility
        inst_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "INSTITUTION"]
        for iid in inst_nodes:
            if target_inst_id and iid != target_inst_id:
                continue
                
            inst_data = self.graph.nodes[iid]
            intake = inst_data.get("intake", 0)
            area = inst_data.get("area_sqm", 0.0)
            
            if intake > 0:
                sqm_per_student = area / (intake * 4) # 4 batches of undergraduate intake
                min_norm = 10.5 # AICTE standard sqm/student for total campus
                
                # If area is below 50% of regulatory requirement, physical impossibility flagged
                if area < (intake * 20.0): # Approx threshold
                    anomalies.append({
                        "engine_module": "IMPOSSIBILITY_ENGINE",
                        "conflict_type": "PHYSICAL_DENSITY_IMPOSSIBILITY",
                        "severity": "WARNING",
                        "entity_id": iid,
                        "entity_name": inst_data.get("label"),
                        "title": f"Physical Capacity Density Anomaly: {inst_data.get('label')}",
                        "explanation": (
                            f"Reported total built-up area ({area:,.0f} sq.m) is inadequate for the sanctioned student "
                            f"capacity ({intake} intake/year = ~{intake*4} total campus students). "
                            f"Mandated instructional space per student cannot physically fit in the declared blueprint."
                        ),
                        "evidence_chain": {
                            "reported_area_sqm": area,
                            "sanctioned_intake": intake,
                            "estimated_student_population": intake * 4,
                            "carpet_area_shortfall_sqm": round((intake * 4 * min_norm) - area, 1)
                        },
                        "recommended_action": "Require submitted municipal occupancy certificate and registered architect CAD drawing audit."
                    })

        return anomalies

    def get_full_graph_serialized(self) -> Dict[str, Any]:
        """Serializes graph to JSON-compatible node/edge format for frontend visualization."""
        nodes = []
        for n, d in self.graph.nodes(data=True):
            node_copy = dict(d)
            node_copy["id"] = n
            nodes.append(node_copy)

        edges = []
        for u, v, k, d in self.graph.edges(keys=True, data=True):
            edge_copy = dict(d)
            edge_copy["source"] = u
            edge_copy["target"] = v
            edge_copy["key"] = k
            edges.append(edge_copy)

        return {
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "total_institutions": len([n for n in nodes if n.get("type") == "INSTITUTION"]),
                "total_faculty": len([n for n in nodes if n.get("type") == "FACULTY"]),
                "total_parcels": len([n for n in nodes if n.get("type") == "LAND_PARCEL"]),
                "total_edges": len(edges)
            }
        }

# Global singleton
impossibility_engine = ImpossibilityEngine()
