from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import (
    get_current_user,
    enforce_institution_isolation,
    normalize_role,
    ROLE_INSTITUTION_USER
)
from backend.app.core.logging_service import log_sensitive_access
from backend.app.models.models import AuditReceipt, Application, User, AuditLog
from backend.app.schemas.schemas import AuditReceiptOut
from backend.app.services.audit_chain import AuditChainService
from backend.app.services.verification_receipts import verify_chain

router = APIRouter(prefix="/audit", tags=["Tamper-Evident Audit Ledger"])


@router.get("/receipts", response_model=List[AuditReceiptOut])
def get_audit_receipts(
    application_id: Optional[int] = Query(None),
    req: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns chronological cryptographically linked receipts from the immutable audit ledger.
    Enforces tenant isolation for institution users.
    """
    if application_id:
        app = db.query(Application).filter(Application.id == application_id).first()
        if app:
            enforce_institution_isolation(current_user, app.institution_id)

    query = db.query(AuditReceipt).order_by(AuditReceipt.receipt_index.asc())
    if application_id:
        query = query.filter(AuditReceipt.application_id == application_id)

    receipts = query.all()

    log_sensitive_access(
        db=db,
        user=current_user,
        action="GET_AUDIT_RECEIPTS",
        resource="/api/v1/audit/receipts",
        details={"application_id": application_id, "count": len(receipts)},
        request=req
    )

    return receipts


@router.get("/verify-chain")
def verify_audit_ledger_integrity(
    application_id: Optional[int] = Query(None),
    req: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Mathematical Chain Integrity Verification:
    Iterates through all hash-chained blocks, verifying SHA-256 parent links and Ed25519 digital signatures.
    Returns status: 'CHAIN_INTACT' or 'TAMPERING_DETECTED' with first broken link diagnostics.
    """
    if application_id:
        app = db.query(Application).filter(Application.id == application_id).first()
        if app:
            enforce_institution_isolation(current_user, app.institution_id)

    # First check verification_receipts chain
    result = verify_chain(db, application_id=application_id)
    if result.get("total_receipts", 0) == 0:
        # Fall back to legacy audit receipts
        result = AuditChainService.verify_ledger_integrity(db, application_id=application_id)

    log_sensitive_access(
        db=db,
        user=current_user,
        action="VERIFY_AUDIT_CHAIN",
        resource="/api/v1/audit/verify-chain",
        details={"application_id": application_id, "is_valid": result.get("is_valid")},
        request=req
    )

    return result


@router.post("/simulate-tamper-demo")
def simulate_tampering_for_evaluation(
    receipt_index: int = Query(2, description="Receipt block index to subtly modify"),
    req: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Demo Utility:
    Subtly modifies a historical receipt's payload hash directly in the database
    to demonstrably prove that the cryptographic audit chain detects tampering immediately.
    """
    target = db.query(AuditReceipt).filter(AuditReceipt.receipt_index == receipt_index).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"Receipt index {receipt_index} not found")

    original_hash = target.payload_hash
    target.payload_hash = target.payload_hash[:-4] + "dead"
    db.commit()

    log_sensitive_access(
        db=db,
        user=current_user,
        action="SIMULATE_TAMPER_DEMO",
        resource="/api/v1/audit/simulate-tamper-demo",
        details={"receipt_index": receipt_index},
        request=req
    )

    return {
        "status": "TAMPERING_SIMULATED",
        "receipt_index": receipt_index,
        "original_payload_hash": original_hash,
        "tampered_payload_hash": target.payload_hash,
        "instruction": "Now run GET /api/v1/audit/verify-chain to observe automated cryptographic breach detection!"
    }


@router.get("/logs")
def get_audit_logs(
    limit: int = Query(50, description="Max logs to return"),
    action: Optional[str] = Query(None, description="Filter by action"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns recent immutable access and determination logs for audit review.
    """
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "actor_email": log.actor_email,
            "actor_role": log.actor_role,
            "action": log.action,
            "resource": log.resource,
            "ip_address": log.ip_address,
            "status_code": log.status_code,
            "details": log.details
        }
        for log in logs
    ]

