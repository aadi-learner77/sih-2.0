"""
PRAMAAN-X Verification Connector Framework: Manual Review Queue.

Manages routing of inconclusive verification outcomes (manual_review_required,
source_unavailable) to a prioritized scrutiny officer queue.
Tracks resolution state, officer assignment, and audit trail.
"""

from __future__ import annotations

import uuid
import threading
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ManualReviewStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class ManualReviewPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ManualReviewItem(BaseModel):
    """A single verification case routed to the scrutiny officer review queue."""
    queue_id: str = Field(..., description="Unique queue ticket identifier")
    document_type: str = Field(..., description="Type of document under review")
    reference_number: Optional[str] = Field(None, description="Claimed reference number")
    institution_id: Optional[str] = Field(None, description="Applicant institution ID")
    institution_name: Optional[str] = Field(None, description="Applicant institution name")
    status: ManualReviewStatus = Field(ManualReviewStatus.PENDING_REVIEW, description="Queue lifecycle status")
    priority: ManualReviewPriority = Field(ManualReviewPriority.MEDIUM, description="Review urgency")
    reason: str = Field(..., description="Why automated verification was inconclusive")
    source: str = Field(..., description="Connector or registry source")
    request_hash: str = Field(..., description="SHA-256 hash of query parameters")
    response_hash: str = Field(..., description="SHA-256 hash of raw issuer response")
    routed_at: str = Field(..., description="UTC ISO-8601 routing timestamp")
    assigned_officer: Optional[str] = Field(None, description="Scrutiny officer email")
    resolution_notes: Optional[str] = Field(None, description="Officer scrutiny findings")
    resolved_at: Optional[str] = Field(None, description="UTC ISO-8601 resolution timestamp")
    verification_result: Dict[str, Any] = Field(default_factory=dict, description="Snapshot of verification result")
    doc_fields: Dict[str, Any] = Field(default_factory=dict, description="Input document fields")


class ManualReviewQueue:
    """Thread-safe in-memory review queue for scrutiny officers."""

    def __init__(self):
        self._lock = threading.Lock()
        self._items: Dict[str, ManualReviewItem] = {}

    def enqueue(
        self,
        result: Any,
        doc_fields: Dict[str, Any],
        reason: str,
        priority: str = "MEDIUM"
    ) -> ManualReviewItem:
        """Enqueues an inconclusive verification case."""
        with self._lock:
            queue_id = f"MRQ-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            routed_at = datetime.now(timezone.utc).isoformat()

            prio = ManualReviewPriority.HIGH if priority == "HIGH" else ManualReviewPriority.MEDIUM

            # Handle result object or dict
            res_dict = result.to_dict() if hasattr(result, "to_dict") else dict(result)

            item = ManualReviewItem(
                queue_id=queue_id,
                document_type=str(doc_fields.get("document_type") or res_dict.get("document_type") or "Document"),
                reference_number=doc_fields.get("reference_number") or res_dict.get("reference_number"),
                institution_id=doc_fields.get("institution_id"),
                institution_name=doc_fields.get("institution_name") or doc_fields.get("name"),
                status=ManualReviewStatus.PENDING_REVIEW,
                priority=prio,
                reason=reason,
                source=str(res_dict.get("source", "Connector Framework")),
                request_hash=str(res_dict.get("request_hash", "")),
                response_hash=str(res_dict.get("response_hash", "")),
                routed_at=routed_at,
                verification_result=res_dict,
                doc_fields=doc_fields
            )
            self._items[queue_id] = item
            return item

    def get(self, queue_id: str) -> Optional[ManualReviewItem]:
        """Retrieves a specific review item by ID."""
        with self._lock:
            return self._items.get(queue_id)

    def list(
        self,
        status: Optional[ManualReviewStatus] = None,
        priority: Optional[ManualReviewPriority] = None
    ) -> List[ManualReviewItem]:
        """Lists items in the queue with optional filtering."""
        with self._lock:
            items = list(self._items.values())

        if status:
            items = [i for i in items if i.status == status]
        if priority:
            items = [i for i in items if i.priority == priority]

        # Sort: HIGH priority first, then most recently routed
        items.sort(key=lambda x: (0 if x.priority == ManualReviewPriority.HIGH else 1, x.routed_at), reverse=False)
        return items

    def resolve(
        self,
        queue_id: str,
        officer_email: str,
        resolution_status: ManualReviewStatus = ManualReviewStatus.RESOLVED,
        notes: str = ""
    ) -> Optional[ManualReviewItem]:
        """Marks an item as resolved with scrutiny officer sign-off."""
        with self._lock:
            item = self._items.get(queue_id)
            if not item:
                return None
            item.status = resolution_status
            item.assigned_officer = officer_email
            item.resolution_notes = notes
            item.resolved_at = datetime.now(timezone.utc).isoformat()
            return item

    def clear(self) -> None:
        """Clears queue items (useful for testing)."""
        with self._lock:
            self._items.clear()


# Singleton default manual review queue instance
default_manual_review_queue = ManualReviewQueue()
