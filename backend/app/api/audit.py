from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import AuditReceipt
from backend.app.schemas.schemas import AuditReceiptOut
from backend.app.services.audit_chain import AuditChainService

router = APIRouter(prefix="/audit", tags=["Tamper-Evident Audit Ledger"])

@router.get("/receipts", response_model=List[AuditReceiptOut])
def get_audit_receipts(
    application_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Returns chronological cryptographically linked receipts from the immutable audit ledger."""
    query = db.query(AuditReceipt).order_by(AuditReceipt.receipt_index.asc())
    if application_id:
        query = query.filter(AuditReceipt.application_id == application_id)
    return query.all()

@router.get("/verify-chain")
def verify_audit_ledger_integrity(
    application_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Mathematical Chain Integrity Verification:
    Iterates through all hash-chained blocks, verifying SHA-256 parent links and digital signatures.
    Returns status: 'VALID_VERIFIED' or 'TAMPERING_DETECTED' with pinpoint diagnostics.
    """
    return AuditChainService.verify_ledger_integrity(db, application_id=application_id)

@router.post("/simulate-tamper-demo")
def simulate_tampering_for_evaluation(
    receipt_index: int = Query(2, description="Receipt block index to subtly modify"),
    db: Session = Depends(get_db)
):
    """
    Hackathon Demo Utility:
    Subtly modifies a historical receipt's payload hash directly in the database
    to demonstrably prove that the cryptographic audit chain detects tampering immediately.
    """
    target = db.query(AuditReceipt).filter(AuditReceipt.receipt_index == receipt_index).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"Receipt index {receipt_index} not found")

    # Invert last characters of payload hash to simulate manual record tampering
    original_hash = target.payload_hash
    target.payload_hash = target.payload_hash[:-4] + "dead"
    db.commit()

    return {
        "status": "TAMPERING_SIMULATED",
        "receipt_index": receipt_index,
        "original_payload_hash": original_hash,
        "tampered_payload_hash": target.payload_hash,
        "instruction": "Now run GET /api/v1/audit/verify-chain to observe automated cryptographic breach detection!"
    }
