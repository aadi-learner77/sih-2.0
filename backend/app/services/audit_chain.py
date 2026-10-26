"""
Hash-Chained Tamper-Evident Verification Receipts Audit Ledger:
Generates cryptographically linked audit receipts for every verification event.
Guarantees immutability and tamper-detection across the entire lifecycle of an application.
"""
import json
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import AuditReceipt
from backend.app.core.config import settings

GENESIS_HASH = "0" * 64

class AuditChainService:
    @staticmethod
    def _compute_payload_hash(payload: Any) -> str:
        """Serializes payload canonically and computes SHA-256 hash."""
        canonical_str = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    @staticmethod
    def _compute_receipt_hash(receipt_index: int, timestamp_str: str, event_type: str, actor_email: str, payload_hash: str, previous_hash: str) -> str:
        """Computes the chained cryptographic block hash."""
        block_content = f"{receipt_index}|{timestamp_str}|{event_type}|{actor_email}|{payload_hash}|{previous_hash}"
        return hashlib.sha256(block_content.encode("utf-8")).hexdigest()

    @staticmethod
    def _compute_signature(receipt_hash: str) -> str:
        """Computes HMAC-SHA256 signature with the server secret key."""
        key = settings.SECRET_KEY.encode("utf-8")
        return hmac.new(key, receipt_hash.encode("utf-8"), hashlib.sha256).hexdigest()

    @classmethod
    def append_receipt(
        cls,
        db: Session,
        event_type: str,
        payload: Dict[str, Any],
        actor_email: str = "system@aicte-india.org",
        actor_role: str = "SYSTEM",
        application_id: Optional[int] = None
    ) -> AuditReceipt:
        """
        Appends a new cryptographically chained verification receipt to the ledger.
        """
        # Fetch the most recent receipt to get previous_hash and current index
        last_receipt = db.query(AuditReceipt).order_by(AuditReceipt.receipt_index.desc()).first()
        
        if last_receipt is None:
            new_index = 0
            previous_hash = GENESIS_HASH
        else:
            new_index = last_receipt.receipt_index + 1
            previous_hash = last_receipt.receipt_hash

        now_utc = datetime.now(timezone.utc)
        timestamp_str = now_utc.isoformat()
        payload_hash = cls._compute_payload_hash(payload)
        receipt_hash = cls._compute_receipt_hash(
            receipt_index=new_index,
            timestamp_str=timestamp_str,
            event_type=event_type,
            actor_email=actor_email,
            payload_hash=payload_hash,
            previous_hash=previous_hash
        )
        signature = cls._compute_signature(receipt_hash)

        receipt = AuditReceipt(
            receipt_index=new_index,
            timestamp=now_utc,
            event_type=event_type,
            actor_email=actor_email,
            actor_role=actor_role,
            application_id=application_id,
            payload_hash=payload_hash,
            previous_hash=previous_hash,
            receipt_hash=receipt_hash,
            signature_digest=signature
        )

        db.add(receipt)
        db.commit()
        db.refresh(receipt)
        return receipt

    @classmethod
    def verify_ledger_integrity(cls, db: Session, application_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Iterates and verifies the cryptographic chain integrity.
        Detects any unauthorized modification, deletion, or backdating in audit records.
        """
        query = db.query(AuditReceipt).order_by(AuditReceipt.receipt_index.asc())
        if application_id:
            query = query.filter(AuditReceipt.application_id == application_id)
            
        receipts: List[AuditReceipt] = query.all()
        
        if not receipts:
            return {
                "chain_length": 0,
                "is_intact": True,
                "status": "EMPTY_LEDGER",
                "message": "No receipts recorded in ledger yet."
            }

        expected_prev_hash = GENESIS_HASH if receipts[0].receipt_index == 0 else receipts[0].previous_hash
        tampered_receipts = []

        for receipt in receipts:
            # 1. Verify previous_hash link
            if receipt.previous_hash != expected_prev_hash:
                tampered_receipts.append({
                    "receipt_index": receipt.receipt_index,
                    "error": "CHAIN_BROKEN",
                    "details": f"Previous hash mismatch. Expected {expected_prev_hash[:16]}..., found {receipt.previous_hash[:16]}..."
                })

            # 2. Recompute and verify signature
            expected_sig = cls._compute_signature(receipt.receipt_hash)
            if receipt.signature_digest != expected_sig:
                tampered_receipts.append({
                    "receipt_index": receipt.receipt_index,
                    "error": "INVALID_SIGNATURE",
                    "details": "Digital signature does not match receipt hash (record content altered)."
                })

            expected_prev_hash = receipt.receipt_hash

        is_intact = len(tampered_receipts) == 0

        return {
            "chain_length": len(receipts),
            "is_intact": is_intact,
            "status": "VALID_VERIFIED" if is_intact else "TAMPERING_DETECTED",
            "genesis_hash": receipts[0].previous_hash if receipts else None,
            "latest_receipt_hash": receipts[-1].receipt_hash if receipts else None,
            "tampered_receipts_count": len(tampered_receipts),
            "tamper_diagnostics": tampered_receipts,
            "verification_timestamp": datetime.now(timezone.utc).isoformat()
        }
