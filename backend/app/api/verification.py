from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import VerificationCheck, Application
from backend.app.schemas.schemas import VerificationCheckOut
from backend.app.services.issuer_apis import issuer_gateway
from backend.app.services.audit_chain import AuditChainService

router = APIRouter(prefix="/verification", tags=["External Mock Issuer APIs"])

class VerificationQueryRequest(BaseModel):
    application_id: int
    document_id: Optional[int] = None
    issuer_type: str  # fire_department, land_registry, university_affiliation, cbdt_income_tax
    parameters: Dict[str, Any]

@router.post("/query", response_model=VerificationCheckOut)
def query_external_issuer(
    request: VerificationQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Simulates external statutory issuer gateway query.
    Returns authoritative issuer response with standardized status:
    verified, mismatch_detected, expired, verification_pending, source_unavailable, manual_review_required.
    Appends an immutable audit receipt.
    """
    app = db.query(Application).filter(Application.id == request.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    issuer_res = {}
    if request.issuer_type == "fire_department":
        issuer_res = issuer_gateway.verify_fire_noc(request.parameters)
    elif request.issuer_type == "land_registry":
        issuer_res = issuer_gateway.verify_land_deed(request.parameters)
    elif request.issuer_type == "university_affiliation":
        issuer_res = issuer_gateway.verify_university_affiliation(request.parameters)
    elif request.issuer_type == "cbdt_income_tax":
        issuer_res = issuer_gateway.verify_faculty_tax_record(request.parameters)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported issuer type: {request.issuer_type}")

    check = VerificationCheck(
        application_id=app.id,
        document_id=request.document_id,
        issuer_type=request.issuer_type,
        issuer_name=issuer_res.get("issuer_name", "Authoritative Portal"),
        status=issuer_res.get("status", "verification_pending"),
        query_parameters=request.parameters,
        issuer_response_data=issuer_res.get("authoritative_record") or {},
        discrepancy_details=issuer_res.get("discrepancies", []),
        latency_ms=issuer_res.get("latency_ms", 100)
    )

    db.add(check)
    db.commit()
    db.refresh(check)

    # Append to cryptographic audit chain
    AuditChainService.append_receipt(
        db=db,
        event_type="EXTERNAL_ISSUER_VERIFICATION",
        payload={
            "check_id": check.id,
            "issuer_type": check.issuer_type,
            "issuer_name": check.issuer_name,
            "status": check.status,
            "discrepancies_count": len(check.discrepancy_details)
        },
        actor_email="system@aicte-india.org",
        actor_role="SYSTEM",
        application_id=app.id
    )

    return check
