"""
PRAMAAN-X Verification Connector Framework Package.
"""

from backend.app.services.connectors.base import (
    VerificationStatus,
    VerificationResult,
    DiscrepancyDetail,
    IssuerConnector,
    compute_sha256
)
from backend.app.services.connectors.manual_review_queue import (
    ManualReviewStatus,
    ManualReviewPriority,
    ManualReviewItem,
    ManualReviewQueue,
    default_manual_review_queue
)
from backend.app.services.connectors.api_lookup_connector import ApiLookupConnector
from backend.app.services.connectors.qr_decode_connector import QrDecodeConnector
from backend.app.services.connectors.digital_signature_connector import DigitalSignatureConnector
from backend.app.services.connectors.registry import ConnectorRegistry, connector_registry

__all__ = [
    "VerificationStatus",
    "VerificationResult",
    "DiscrepancyDetail",
    "IssuerConnector",
    "compute_sha256",
    "ManualReviewStatus",
    "ManualReviewPriority",
    "ManualReviewItem",
    "ManualReviewQueue",
    "default_manual_review_queue",
    "ApiLookupConnector",
    "QrDecodeConnector",
    "DigitalSignatureConnector",
    "ConnectorRegistry",
    "connector_registry"
]
