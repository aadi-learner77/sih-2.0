"""
PRAMAAN-X Verification Connector Framework: Core Abstractions & Data Contracts.

Defines:
1. VerificationStatus Enum: Exactly 6 standard outcomes.
2. VerificationResult & DiscrepancyDetail: Full audit and cryptographic metadata models.
3. IssuerConnector (ABC): Abstract base connector implementing retries with exponential
   backoff, timeouts, SHA-256 request/response hashing, timestamping, and automatic
   routing of inconclusive cases to a manual review queue.
"""

from __future__ import annotations

import time
import json
import random
import hashlib
import logging
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from backend.app.services.connectors.manual_review_queue import ManualReviewQueue

logger = logging.getLogger("pramaan_x.connectors")


# ============================================================================
# 1. STANDARDIZED VERIFICATION STATUS ENUM (EXACTLY 6 STATUSES)
# ============================================================================

class VerificationStatus(str, Enum):
    """
    Mandatory standard verification statuses per AICTE PRAMAAN-X specification.
    Every issuer connector outcome must map to exactly one of these values.
    """
    VERIFIED = "verified"
    MISMATCH_DETECTED = "mismatch_detected"
    EXPIRED = "expired"
    VERIFICATION_PENDING = "verification_pending"
    SOURCE_UNAVAILABLE = "source_unavailable"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


# ============================================================================
# 2. AUDIT & DISCREPANCY DATA MODELS
# ============================================================================

class DiscrepancyDetail(BaseModel):
    """Represents a specific field-level discrepancy detected during verification."""
    field: str = Field(..., description="Field name where discrepancy was identified")
    claimed_value: Any = Field(None, description="Value declared by applicant in document")
    issuer_value: Any = Field(None, description="Authoritative value from issuer registry")
    discrepancy_type: str = Field("FIELD_MISMATCH", description="Classification of mismatch")
    summary: str = Field("", description="Human-readable decision-support summary")


class VerificationResult(BaseModel):
    """
    Standardized result contract returned by all IssuerConnectors.
    Contains complete cryptographic provenance (request/response hashes, timestamp, source).
    """
    status: VerificationStatus = Field(..., description="Standardized outcome status")
    source: str = Field(..., description="Authoritative source or connector name")
    timestamp: str = Field(..., description="UTC ISO-8601 execution timestamp")
    request_hash: str = Field(..., description="SHA-256 hex digest of query parameters")
    response_hash: str = Field(..., description="SHA-256 hex digest of raw issuer response")
    document_type: str = Field(..., description="Document category verified")
    reference_number: Optional[str] = Field(None, description="Document/certificate reference identifier")
    issuer_name: str = Field(..., description="Statutory issuing authority name")
    authoritative_data: Dict[str, Any] = Field(default_factory=dict, description="Registry record fields")
    discrepancies: List[DiscrepancyDetail] = Field(default_factory=list, description="List of detected mismatches")
    advisory: str = Field(..., description="Non-punitive decision-support advisory text")
    latency_ms: int = Field(0, description="Total execution latency in milliseconds")
    attempts: int = Field(1, description="Number of retry attempts executed")
    routed_to_manual_review: bool = Field(False, description="True if routed to scrutiny officer queue")
    manual_review_id: Optional[str] = Field(None, description="Queue reference identifier if routed")
    manual_review_reason: Optional[str] = Field(None, description="Reason for human scrutiny routing")
    raw_response: Dict[str, Any] = Field(default_factory=dict, description="Complete unprocessed issuer payload")

    def to_dict(self) -> Dict[str, Any]:
        """Returns JSON-serializable dictionary representation."""
        return self.model_dump()


# ============================================================================
# 3. CRYPTOGRAPHIC PROVENANCE HELPERS
# ============================================================================

def compute_sha256(data: Any) -> str:
    """
    Computes a deterministic SHA-256 hex digest for any data structure,
    bytes, or string for immutable audit logging.
    """
    if isinstance(data, (bytes, bytearray)):
        return hashlib.sha256(data).hexdigest()
    if isinstance(data, str):
        return hashlib.sha256(data.encode("utf-8")).hexdigest()
    try:
        canonical_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
    except Exception:
        return hashlib.sha256(str(data).encode("utf-8")).hexdigest()


# ============================================================================
# 4. ABSTRACT ISSUER CONNECTOR BASE CLASS
# ============================================================================

class IssuerConnector(ABC):
    """
    Abstract base class for statutory and mock issuer verification connectors.
    Provides built-in:
    - Retries with exponential backoff & jitter
    - Configurable timeouts
    - Deterministic request/response SHA-256 hashing
    - Precise ISO-8601 UTC timestamping
    - Automatic routing of inconclusive cases to a manual review queue
    """

    def __init__(
        self,
        name: str,
        timeout_seconds: float = 4.0,
        max_retries: int = 3,
        base_backoff_seconds: float = 0.2,
        max_backoff_seconds: float = 2.0,
        manual_review_queue: Optional[Any] = None
    ):
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(1, max_retries)
        self.base_backoff_seconds = base_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self._manual_review_queue = manual_review_queue

    @property
    def manual_review_queue(self) -> Any:
        if self._manual_review_queue is None:
            from backend.app.services.connectors.manual_review_queue import default_manual_review_queue
            self._manual_review_queue = default_manual_review_queue
        return self._manual_review_queue

    @abstractmethod
    def supports_document_type(self, document_type: str) -> bool:
        """
        Determines whether this connector handles the specified document type.
        
        Args:
            document_type: Canonical or alias document name.
            
        Returns:
            bool: True if supported, False otherwise.
        """
        pass

    @abstractmethod
    def _execute_verification(self, doc_fields: Dict[str, Any], attempt: int = 1) -> VerificationResult:
        """
        Connector-specific verification implementation.
        Must raise TimeoutError or ConnectionError on transient failures to trigger retries.
        
        Args:
            doc_fields: Dictionary of extracted document fields.
            attempt: Current retry attempt number (1-indexed).
            
        Returns:
            VerificationResult: The verification outcome.
        """
        pass

    def verify(self, doc_fields: Dict[str, Any]) -> VerificationResult:
        """
        Public template method:
        Executes document verification with:
        1. Exponential backoff retries for transient errors.
        2. Strict timeout handling.
        3. Deterministic SHA-256 request and response hashing.
        4. Inconclusive case detection and automatic routing to manual review queue.
        
        Args:
            doc_fields: Dictionary of document fields (e.g. reference_number, entity_name).
            
        Returns:
            VerificationResult: Complete audit result mapped to standard status.
        """
        start_time = time.time()
        timestamp = datetime.now(timezone.utc).isoformat()
        request_hash = compute_sha256(doc_fields)
        doc_type = str(doc_fields.get("document_type", "Unknown Document"))
        ref_no = doc_fields.get("reference_number") or doc_fields.get("ref") or doc_fields.get("noc_number")

        last_exception: Optional[Exception] = None
        result: Optional[VerificationResult] = None

        executed_attempts = 1
        for attempt in range(1, self.max_retries + 1):
            executed_attempts = attempt
            try:
                logger.info(f"[{self.name}] Verifying '{doc_type}' (attempt {attempt}/{self.max_retries})...")
                result = self._execute_verification(doc_fields, attempt=attempt)

                # If connector explicitly signaled source_unavailable and we have retries left, treat as transient
                if result.status == VerificationStatus.SOURCE_UNAVAILABLE and attempt < self.max_retries:
                    raise ConnectionError(f"Source unavailable on attempt {attempt}")

                # Conclusive or non-retryable result obtained
                break

            except (TimeoutError, ConnectionError, OSError) as exc:
                last_exception = exc
                logger.warning(f"[{self.name}] Transient error on attempt {attempt}: {str(exc)}")

                if attempt < self.max_retries:
                    # Exponential backoff with random jitter
                    backoff = min(self.max_backoff_seconds, self.base_backoff_seconds * (2 ** (attempt - 1)))
                    jitter = random.uniform(0.01, 0.08)
                    time.sleep(backoff + jitter)
                else:
                    logger.error(f"[{self.name}] All {self.max_retries} attempts exhausted for '{doc_type}'.")

            except Exception as unhandled_exc:
                logger.exception(f"[{self.name}] Unhandled connector failure: {str(unhandled_exc)}")
                last_exception = unhandled_exc
                break

        total_latency_ms = int((time.time() - start_time) * 1000)

        # If retries were exhausted without result, synthesize SOURCE_UNAVAILABLE
        if result is None:
            raw_err = {"error": str(last_exception), "retries_exhausted": self.max_retries}
            result = VerificationResult(
                status=VerificationStatus.SOURCE_UNAVAILABLE,
                source=self.name,
                timestamp=timestamp,
                request_hash=request_hash,
                response_hash=compute_sha256(raw_err),
                document_type=doc_type,
                reference_number=ref_no,
                issuer_name=self.name,
                authoritative_data={},
                discrepancies=[],
                advisory=(
                    f"Statutory authority portal '{self.name}' was unreachable after {self.max_retries} "
                    f"retries (timeout: {self.timeout_seconds}s). Case routed to manual review queue."
                ),
                latency_ms=total_latency_ms,
                attempts=self.max_retries,
                raw_response=raw_err
            )

        # Ensure metadata is accurately populated
        result.source = self.name
        result.timestamp = timestamp
        result.request_hash = request_hash
        result.attempts = executed_attempts
        if not result.response_hash:
            result.response_hash = compute_sha256(result.raw_response or result.authoritative_data)
        result.latency_ms = total_latency_ms


        # Inconclusive routing: if MANUAL_REVIEW_REQUIRED or SOURCE_UNAVAILABLE, enqueue
        if result.status in (VerificationStatus.MANUAL_REVIEW_REQUIRED, VerificationStatus.SOURCE_UNAVAILABLE):
            self._route_to_manual_review(result, doc_fields)

        return result

    def _route_to_manual_review(self, result: VerificationResult, doc_fields: Dict[str, Any]) -> None:
        """Enqueues inconclusive verification cases for scrutiny officer evaluation."""
        reason = result.manual_review_reason or result.advisory
        priority = "HIGH" if result.status == VerificationStatus.SOURCE_UNAVAILABLE else "MEDIUM"
        
        queue_item = self.manual_review_queue.enqueue(
            result=result,
            doc_fields=doc_fields,
            reason=reason,
            priority=priority
        )
        result.routed_to_manual_review = True
        result.manual_review_id = queue_item.queue_id
        result.manual_review_reason = reason
        logger.info(f"[{self.name}] Inconclusive verification routed to manual review queue as {queue_item.queue_id}")
