"""
Checklist Engine: Maps Application Category -> Dynamic Checklist -> Missing/Expired/Inconsistent Validation.
AICTE EoA (Extension of Approval) and associated category validator.
"""
from datetime import datetime, timezone
from typing import Dict, List, Any

CATEGORY_CHECKLISTS: Dict[str, List[Dict[str, Any]]] = {
    "Extension of Approval (EoA)": [
        {
            "code": "DOC_FIRE_NOC",
            "name": "Fire Safety Certificate / NOC",
            "required": True,
            "issuing_authority": "State Fire & Emergency Services",
            "max_age_months": 12,
            "criticality": "HIGH",
            "description": "Valid Fire Safety NOC covering the upcoming academic session."
        },
        {
            "code": "DOC_LAND_TITLE",
            "name": "Land Title Deed / 30-Year Lease Deed",
            "required": True,
            "issuing_authority": "Sub-Registrar / Revenue Authority",
            "max_age_months": 360,
            "criticality": "HIGH",
            "description": "Continuous unbroken ownership or registered lease agreement of minimum 30 years."
        },
        {
            "code": "DOC_BUILDING_PLAN",
            "name": "Approved Building Plan & Occupancy Certificate",
            "required": True,
            "issuing_authority": "Municipal Corporation / Town Planning Authority",
            "max_age_months": None,
            "criticality": "HIGH",
            "description": "Architectural drawings with carpet area statement certified by registered architect."
        },
        {
            "code": "DOC_FACULTY_ROSTER",
            "name": "Faculty Roster & Form 16 Salary Proof",
            "required": True,
            "issuing_authority": "Institution Governing Body & Bank Records",
            "max_age_months": 6,
            "criticality": "HIGH",
            "description": "Full roster of teaching faculty with Cadre, PAN, Aadhaar hash, and UGC 7th CPC scale compliance."
        },
        {
            "code": "DOC_AFFILIATION_ORDER",
            "name": "University Affiliation Order",
            "required": True,
            "issuing_authority": "State / Central Affiliating University",
            "max_age_months": 12,
            "criticality": "HIGH",
            "description": "Affiliation order for the ongoing and upcoming academic year."
        },
        {
            "code": "DOC_AUDITED_ACCOUNTS",
            "name": "Audited Financial Statements (Last 3 Years)",
            "required": True,
            "issuing_authority": "Chartered Accountant (UDIN verified)",
            "max_age_months": 12,
            "criticality": "MEDIUM",
            "description": "Balance Sheet, Income/Expenditure account with verified UDIN."
        },
        {
            "code": "DOC_CAMPUS_PHOTOS",
            "name": "Geo-tagged Infrastructure & Laboratory Photos",
            "required": True,
            "issuing_authority": "Institution AICTE Portal Upload",
            "max_age_months": 3,
            "criticality": "MEDIUM",
            "description": "Timestamped and geo-tagged photos of computer center, library, labs, and barrier-free ramps."
        }
    ],
    "Increase in Intake": [
        {
            "code": "DOC_FIRE_NOC",
            "name": "Fire Safety Certificate / NOC",
            "required": True,
            "issuing_authority": "State Fire & Emergency Services",
            "max_age_months": 12,
            "criticality": "HIGH",
            "description": "Valid Fire Safety NOC covering increased occupant load."
        },
        {
            "code": "DOC_ADDITIONAL_AREA_PROOF",
            "name": "Additional Built-up Area Occupancy Certificate",
            "required": True,
            "issuing_authority": "Municipal Corporation / Town Planning Authority",
            "max_age_months": 12,
            "criticality": "HIGH",
            "description": "Proof of incremental classroom and laboratory space satisfying 10.5 sqm/student."
        },
        {
            "code": "DOC_NBA_ACCREDITATION",
            "name": "NBA Accreditation Certificate",
            "required": True,
            "issuing_authority": "National Board of Accreditation",
            "max_age_months": 24,
            "criticality": "HIGH",
            "description": "Eligible courses must have minimum 675/1000 NBA score for intake expansion."
        },
        {
            "code": "DOC_FACULTY_ROSTER",
            "name": "Augmented Faculty Roster",
            "required": True,
            "issuing_authority": "Institution Governing Body",
            "max_age_months": 3,
            "criticality": "HIGH",
            "description": "Additional teaching appointments committed for the increased intake."
        }
    ]
}

def generate_checklist_status(category: str, submitted_documents: List[Any]) -> Dict[str, Any]:
    """
    Evaluates submitted documents against required checklist items.
    Detects:
    - Missing mandatory documents
    - Expired documents (based on structured fields like 'valid_till')
    - Inconsistent metadata (e.g. date discrepancies)
    """
    checklist_template = CATEGORY_CHECKLISTS.get(category, CATEGORY_CHECKLISTS["Extension of Approval (EoA)"])
    items_status = []
    
    missing_count = 0
    expired_count = 0
    inconsistent_count = 0
    
    doc_map = {doc.document_type: doc for doc in submitted_documents}
    
    now = datetime.now(timezone.utc)
    
    for item in checklist_template:
        doc_match = None
        it_name = (item.get("name") or "").lower()
        it_code = (item.get("code") or "").lower()
        for doc_type, doc in doc_map.items():
            dt_lower = (doc_type or "").lower()
            if dt_lower and (dt_lower in it_name or it_name in dt_lower or it_code in dt_lower or dt_lower in it_code):
                doc_match = doc
                break
                
        if not doc_match:
            missing_count += 1
            items_status.append({
                "code": item["code"],
                "name": item["name"],
                "status": "MISSING",
                "criticality": item["criticality"],
                "issuing_authority": item["issuing_authority"],
                "details": f"Mandatory document '{item['name']}' not yet uploaded."
            })
        else:
            # Check for expiration
            fields = doc_match.structured_fields or {}
            valid_till_str = fields.get("valid_till") or fields.get("expiry_date")
            is_expired = False
            expiry_msg = "Document valid"
            
            if valid_till_str:
                try:
                    expiry_date = datetime.strptime(valid_till_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if expiry_date < now:
                        is_expired = True
                        expired_count += 1
                        expiry_msg = f"Expired on {valid_till_str}"
                    else:
                        expiry_msg = f"Valid until {valid_till_str}"
                except ValueError:
                    pass
            
            # Check for metadata inconsistency (e.g., modified after issue)
            is_inconsistent = False
            inconsistency_msg = ""
            forensics = doc_match.metadata_forensics or {}
            if forensics.get("software_anomalies") or doc_match.is_flagged_for_review:
                is_inconsistent = True
                inconsistent_count += 1
                inconsistency_msg = doc_match.review_reason or "Digital forensics anomaly detected in document header"

            status = "EXPIRED" if is_expired else ("INCONSISTENT" if is_inconsistent else "VERIFIED")
            
            items_status.append({
                "code": item["code"],
                "name": item["name"],
                "status": status,
                "criticality": item["criticality"],
                "issuing_authority": item["issuing_authority"],
                "document_id": doc_match.id,
                "filename": doc_match.filename,
                "expiry_info": expiry_msg,
                "is_expired": is_expired,
                "is_inconsistent": is_inconsistent,
                "details": inconsistency_msg if is_inconsistent else expiry_msg
            })
            
    total_required = len(checklist_template)
    completed_items = len([i for i in items_status if i["status"] == "VERIFIED"])
    completion_rate = round((completed_items / total_required) * 100, 1) if total_required > 0 else 100.0

    return {
        "category": category,
        "total_items": total_required,
        "completed_items": completed_items,
        "missing_items": missing_count,
        "expired_items": expired_count,
        "inconsistent_items": inconsistent_count,
        "completion_rate_pct": completion_rate,
        "items": items_status
    }
