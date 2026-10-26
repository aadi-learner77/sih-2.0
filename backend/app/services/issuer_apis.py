"""
Mock External Issuer APIs Gateway:
Simulates authoritative government and statutory verification portals:
- State Fire & Emergency Services NOC Portal
- State Revenue & Land Records Registry (e.g. Bhoomi/Mahabhulekh)
- State Examining University Affiliation Portal
- Central Board of Direct Taxes (CBDT) Form 16 / TDS Gateway

Standardized response statuses:
'verified', 'mismatch_detected', 'expired', 'verification_pending', 'source_unavailable', 'manual_review_required'
"""
import os
import time
import httpx
from typing import Dict, Any, List

MOCK_ISSUER_URL = os.getenv("MOCK_ISSUER_URL")

class MockIssuerGateway:
    def __init__(self, base_url: str = MOCK_ISSUER_URL):
        self.base_url = base_url.rstrip("/") if base_url else None

    def _query_remote_service(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any] | None:
        """Attempts HTTP query to the standalone mock-issuer container if reachable."""
        if not self.base_url:
            return None
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.post(f"{self.base_url}{endpoint}", json=payload)
                if res.status_code == 200:
                    return res.json()
        except Exception:
            pass
        return None

    def verify_fire_noc(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Queries State Fire Department Database.
        Matches NOC Number, issuing district, and expiry date.
        """
        noc_no = str(query.get("noc_number", "")).strip().upper()
        inst_name = query.get("institution_name", "")
        claimed_expiry = query.get("expiry_date", "")
        
        # Test Case Scenarios based on NOC input
        if "EXPIRED" in noc_no or noc_no == "FS/2023/8812":
            return {
                "issuer_name": "Karnataka Fire & Emergency Services",
                "issuer_code": "KFES_PORTAL",
                "status": "expired",
                "latency_ms": 140,
                "authoritative_record": {
                    "noc_number": noc_no,
                    "registered_entity": inst_name,
                    "issue_date": "2023-01-10",
                    "expiry_date": "2024-01-09",
                    "status": "LAPSED",
                    "renewal_applied": False
                },
                "discrepancies": [
                    {
                        "field": "expiry_date",
                        "claimed_value": claimed_expiry,
                        "issuer_value": "2024-01-09",
                        "discrepancy_type": "CERTIFICATE_LAPSED",
                        "summary": "NOC lapsed on 2024-01-09; no active renewal registered on state fire portal."
                    }
                ],
                "advisory": "Indicator for review: Mandatory fire clearance is currently lapsed on government records."
            }

        elif "MISMATCH" in noc_no or noc_no == "FS/2024/991":
            return {
                "issuer_name": "Karnataka Fire & Emergency Services",
                "issuer_code": "KFES_PORTAL",
                "status": "mismatch_detected",
                "latency_ms": 115,
                "authoritative_record": {
                    "noc_number": noc_no,
                    "registered_entity": "Apex Commercial Shopping Mall (Not Educational)",
                    "occupancy_type": "Commercial - Mercantile",
                    "registered_height_meters": 15.0,
                    "expiry_date": "2026-12-31"
                },
                "discrepancies": [
                    {
                        "field": "registered_entity",
                        "claimed_value": inst_name,
                        "issuer_value": "Apex Commercial Shopping Mall",
                        "discrepancy_type": "ENTITY_NAME_MISMATCH",
                        "summary": "State portal registers this NOC number to a commercial mall, not an educational institution."
                    },
                    {
                        "field": "occupancy_type",
                        "claimed_value": "Educational Institution (Group B)",
                        "issuer_value": "Commercial - Mercantile",
                        "discrepancy_type": "OCCUPANCY_CLASSIFICATION_MISMATCH",
                        "summary": "Building occupancy category differs in statutory registry."
                    }
                ],
                "advisory": "Critical Indicator for review: NOC number belongs to a commercial property on official portal."
            }

        elif "UNAVAILABLE" in noc_no:
            return {
                "issuer_name": "State Fire Services Portal",
                "issuer_code": "SFES_GATEWAY",
                "status": "source_unavailable",
                "latency_ms": 480,
                "authoritative_record": None,
                "discrepancies": [],
                "advisory": "Statutory database gateway temporarily unreachable (HTTP 503). Retrying via async webhook."
            }

        else:
            # Clean Verified Case
            return {
                "issuer_name": "State Fire & Emergency Services",
                "issuer_code": "KFES_PORTAL",
                "status": "verified",
                "latency_ms": 95,
                "authoritative_record": {
                    "noc_number": noc_no or "FS/2024/7741",
                    "registered_entity": inst_name,
                    "occupancy_type": "Educational (Group B)",
                    "issue_date": "2024-05-15",
                    "expiry_date": "2027-05-14",
                    "sanctioned_floors": "G+3",
                    "fire_officer_id": "CFO-BLR-041",
                    "status": "VALID_ACTIVE"
                },
                "discrepancies": [],
                "advisory": "All parameters match authoritative state portal records."
            }

    def verify_land_deed(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Queries State Revenue Department (Bhoomi / Mahabhulekh / AnyRoR).
        Cross-checks Survey Number, Area, and Land Conversion status (Agricultural vs Non-Ag Educational).
        """
        survey_no = query.get("survey_no", "")
        claimed_acres = float(query.get("claimed_acres", 5.0))
        village = query.get("village", "Devanahalli")

        if "42/1" in survey_no:
            # Overlap scenario
            return {
                "issuer_name": "State Revenue Department Land Registry (Bhoomi)",
                "issuer_code": "REV_BHOOMI_API",
                "status": "manual_review_required",
                "latency_ms": 180,
                "authoritative_record": {
                    "survey_no": survey_no,
                    "village": village,
                    "total_recorded_extent_acres": 6.2,
                    "land_classification": "Non-Agricultural (Educational)",
                    "encumbrance_status": "LITIGATION_PENDING",
                    "registered_title_holder": "Apex Vidya Foundation & Joint Claimants"
                },
                "discrepancies": [
                    {
                        "field": "encumbrance_status",
                        "claimed_value": "CLEAR_TITLE_FREE_OF_ENCUMBRANCE",
                        "issuer_value": "LITIGATION_PENDING / MULTIPLE_CLAIMANTS",
                        "discrepancy_type": "TITLE_DISPUTE_INDICATOR",
                        "summary": "Revenue records reflect active caveat and joint claimant petition on Survey 42/1."
                    }
                ],
                "advisory": "Indicator for review: Legal title notice on revenue records requires scrutiny officer inspection."
            }
        else:
            return {
                "issuer_name": "State Revenue Department Land Registry (Bhoomi)",
                "issuer_code": "REV_BHOOMI_API",
                "status": "verified",
                "latency_ms": 110,
                "authoritative_record": {
                    "survey_no": survey_no or "Sy. No. 108/3",
                    "village": village,
                    "total_recorded_extent_acres": claimed_acres,
                    "land_classification": "Non-Agricultural (Educational)",
                    "encumbrance_status": "CLEAR_TITLE_NIL_ENCUMBRANCE",
                    "registered_title_holder": query.get("trust_name", "Educational Trust")
                },
                "discrepancies": [],
                "advisory": "Title, village classification, and educational conversion verified against state revenue database."
            }

    def verify_university_affiliation(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Queries State Technical University Affiliation Portal (e.g. VTU / AKTU / Anna Univ).
        Checks if the institution has an unrevoked annual affiliation order.
        """
        aicte_id = query.get("aicte_id", "")
        inst_name = query.get("institution_name", "")

        return {
            "issuer_name": "State Examining University Affiliation Cell",
            "issuer_code": "UNIV_AFFILIATION_PORTAL",
            "status": "verified",
            "latency_ms": 85,
            "authoritative_record": {
                "aicte_id": aicte_id,
                "institution_name": inst_name,
                "affiliation_period": "2025-2026",
                "affiliation_type": "Permanent Affiliation (UG Engineering)",
                "approved_branches": ["Computer Science", "Electronics & Comm.", "Mechanical", "Civil"],
                "sanctioned_university_intake": 480,
                "order_number": "UNIV/AFFIL/2025/1049"
            },
            "discrepancies": [],
            "advisory": "University affiliation order authenticated for academic session 2025-26."
        }

    def verify_faculty_tax_record(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Queries CBDT TRACES / Income Tax Portal for Form 16 / TDS deduction.
        Detects dual salary draws under the same PAN.
        """
        pan_masked = query.get("pan_masked", "AB****89C")
        faculty_name = query.get("faculty_name", "Dr. R. K. Sharma")

        if "89C" in pan_masked:
            # Dual salary draw detected
            return {
                "issuer_name": "Central Board of Direct Taxes (CBDT) TRACES Gateway",
                "issuer_code": "CBDT_TRACES_MOCK",
                "status": "mismatch_detected",
                "latency_ms": 160,
                "authoritative_record": {
                    "pan_masked": pan_masked,
                    "assessment_year": "2025-26",
                    "active_tds_deductors": [
                        {"deductor_name": "Apex Institute of Technology", "deductor_tan": "BLRA99182A", "section": "192 (Salary)"},
                        {"deductor_name": "Royal College of Engineering", "deductor_tan": "MYSR28191B", "section": "192 (Salary)"}
                    ]
                },
                "discrepancies": [
                    {
                        "field": "salary_deductions_q3_q4",
                        "claimed_value": "Sole Employment at Apex Institute",
                        "issuer_value": "Simultaneous Section 192 (Regular Salary) TDS by 2 distinct educational institutions",
                        "discrepancy_type": "DUAL_SALARY_DRAW_EVIDENCE",
                        "summary": "Form 26AS/TDS demonstrates concurrent regular monthly salary disbursed by two colleges."
                    }
                ],
                "advisory": "Critical Indicator for review: Financial records indicate concurrent full-time employment."
            }
        else:
            return {
                "issuer_name": "Central Board of Direct Taxes (CBDT) TRACES Gateway",
                "issuer_code": "CBDT_TRACES_MOCK",
                "status": "verified",
                "latency_ms": 105,
                "authoritative_record": {
                    "pan_masked": pan_masked,
                    "assessment_year": "2025-26",
                    "active_tds_deductors": [
                        {"deductor_name": query.get("institution_name", "Technical Institute"), "section": "192 (Salary)"}
                    ]
                },
                "discrepancies": [],
                "advisory": "Single employer TDS verification corroborated on tax registry."
            }

# Global singleton
issuer_gateway = MockIssuerGateway()
