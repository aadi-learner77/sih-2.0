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


# ============================================================================
# ISSUER CONNECTOR FRAMEWORK ENDPOINTS
# ============================================================================

from backend.app.services.connectors import (
    connector_registry,
    default_manual_review_queue,
    VerificationResult,
    ManualReviewStatus
)


class ConnectorVerifyRequest(BaseModel):
    document_type: str
    doc_fields: Dict[str, Any]
    preferred_connector: Optional[str] = None  # 'api', 'qr', 'signature'
    application_id: Optional[int] = None
    document_id: Optional[int] = None


class ManualReviewResolutionRequest(BaseModel):
    officer_email: str
    resolution_status: str = "RESOLVED"
    notes: str = ""


@router.post("/connector/verify", response_model=VerificationResult)
def verify_via_connector(
    request: ConnectorVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Executes verification via the abstract IssuerConnector framework:
    Supports API lookup, QR decode + lookup, and digital-signature validation.
    Enforces retries with backoff, timeouts, SHA-256 request/response hashing,
    and automatic routing of inconclusive cases to the manual review queue.
    """
    fields = dict(request.doc_fields)
    fields["document_type"] = request.document_type
    if request.application_id:
        fields["application_id"] = str(request.application_id)

    result = connector_registry.verify(
        doc_fields=fields,
        preferred_connector=request.preferred_connector
    )

    # If application exists, persist verification audit check
    if request.application_id:
        app = db.query(Application).filter(Application.id == request.application_id).first()
        if app:
            check = VerificationCheck(
                application_id=app.id,
                document_id=request.document_id,
                issuer_type=request.preferred_connector or "connector_framework",
                issuer_name=result.issuer_name,
                status=result.status.value,
                query_parameters=fields,
                issuer_response_data={
                    "authoritative_data": result.authoritative_data,
                    "request_hash": result.request_hash,
                    "response_hash": result.response_hash,
                    "source": result.source,
                    "manual_review_id": result.manual_review_id
                },
                discrepancy_details=[d.model_dump() for d in result.discrepancies],
                latency_ms=result.latency_ms
            )
            db.add(check)
            db.commit()
            db.refresh(check)

            AuditChainService.append_receipt(
                db=db,
                event_type="CONNECTOR_FRAMEWORK_VERIFICATION",
                payload={
                    "check_id": check.id,
                    "source": result.source,
                    "status": result.status.value,
                    "request_hash": result.request_hash,
                    "response_hash": result.response_hash,
                    "routed_to_manual_review": result.routed_to_manual_review
                },
                actor_email="system@aicte-india.org",
                actor_role="SYSTEM",
                application_id=app.id
            )

    return result


@router.post("/connector/composite-verify")
def composite_verify_via_connectors(request: ConnectorVerifyRequest):
    """Executes multi-channel verification across all applicable connectors."""
    fields = dict(request.doc_fields)
    fields["document_type"] = request.document_type
    return connector_registry.verify_composite(fields)


@router.get("/connector/list")
def list_registered_connectors():
    """Returns all active IssuerConnectors in the framework."""
    return connector_registry.list_connectors()


@router.get("/connector/manual-review-queue")
def list_manual_review_queue(
    status: Optional[str] = None,
    priority: Optional[str] = None
):
    """Returns inconclusive cases currently routed to the scrutiny officer queue."""
    status_filter = ManualReviewStatus(status) if status else None
    return default_manual_review_queue.list(status=status_filter)


@router.post("/connector/manual-review-queue/{queue_id}/resolve")
def resolve_manual_review_item(
    queue_id: str,
    request: ManualReviewResolutionRequest
):
    """Scrutiny officer resolution sign-off on a manual review queue ticket."""
    resolution = ManualReviewStatus(request.resolution_status)
    item = default_manual_review_queue.resolve(
        queue_id=queue_id,
        officer_email=request.officer_email,
        resolution_status=resolution,
        notes=request.notes
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"Manual review item '{queue_id}' not found.")
    return item

