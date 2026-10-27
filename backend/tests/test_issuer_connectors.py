"""
PyTest Test Suite for PRAMAAN-X Verification Connector Framework.

Tests:
1. Abstract IssuerConnector base class enforcement and contract compliance.
2. Exact 6-status enumeration mapping ('verified', 'mismatch_detected', 'expired',
   'verification_pending', 'source_unavailable', 'manual_review_required').
3. Deterministic SHA-256 request and response hashing.
4. Timestamping and source metadata recording.
5. Exponential backoff retries with jitter and timeout handling.
6. Automatic routing of inconclusive cases to the ManualReviewQueue.
7. ApiLookupConnector across verified, mismatch, expired, pending, and timeout scenarios.
8. QrDecodeConnector (pyzbar + OpenCV) across matching, conflicting, expired, and missing QR.
9. DigitalSignatureConnector across authentic, tampered byte-range, expired cert, and unsigned cases.
10. ConnectorRegistry dispatching and composite multi-channel verification.
11. ManualReviewQueue ticket lifecycle (enqueue, filter, officer resolution).
12. FastAPI REST endpoints under /api/v1/verification/connector/*.
"""

import pytest
import qrcode
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.verification import router as verification_router
from backend.app.services.connectors import (
    VerificationStatus,
    VerificationResult,
    DiscrepancyDetail,
    IssuerConnector,
    compute_sha256,
    ManualReviewStatus,
    ManualReviewPriority,
    ManualReviewQueue,
    default_manual_review_queue,
    ApiLookupConnector,
    QrDecodeConnector,
    DigitalSignatureConnector,
    ConnectorRegistry,
    connector_registry
)

# Test FastAPI application
test_app = FastAPI()
test_app.include_router(verification_router, prefix="/api/v1")


@pytest.fixture(scope="module")
def client():
    return TestClient(test_app)


@pytest.fixture(autouse=True)
def clean_manual_review_queue():
    """Clears review queue before each test."""
    default_manual_review_queue.clear()
    yield
    default_manual_review_queue.clear()


# ============================================================================
# 1. ABSTRACT CONTRACT & EXACT STATUS ENUMERATION TESTS
# ============================================================================

def test_exact_six_verification_statuses():
    """Verifies that the framework defines and enforces EXACTLY the 6 required statuses."""
    expected_statuses = {
        "verified",
        "mismatch_detected",
        "expired",
        "verification_pending",
        "source_unavailable",
        "manual_review_required"
    }
    actual_statuses = {s.value for s in VerificationStatus}
    assert actual_statuses == expected_statuses, f"Statuses mismatch: {actual_statuses} != {expected_statuses}"
    assert len(VerificationStatus) == 6


def test_abstract_connector_cannot_be_instantiated_directly():
    """Verifies that IssuerConnector is an ABC and requires concrete implementation."""
    with pytest.raises(TypeError):
        IssuerConnector(name="AbstractTest")  # type: ignore


def test_deterministic_sha256_hashing():
    """Verifies deterministic SHA-256 computation regardless of key ordering."""
    payload1 = {"b": 2, "a": 1, "nested": {"y": 20, "x": 10}}
    payload2 = {"nested": {"x": 10, "y": 20}, "a": 1, "b": 2}

    h1 = compute_sha256(payload1)
    h2 = compute_sha256(payload2)
    assert h1 == h2
    assert len(h1) == 64
    assert all(c in "0123456789abcdef" for c in h1)


# ============================================================================
# 2. RETRIES, BACKOFF & INCONCLUSIVE ROUTING TESTS
# ============================================================================

class FlakyTestConnector(IssuerConnector):
    """Mock connector to verify retry count and backoff timing."""

    def __init__(self, failures_before_success=2):
        super().__init__(
            name="FlakyTestConnector",
            max_retries=3,
            base_backoff_seconds=0.02,
            max_backoff_seconds=0.1
        )
        self.attempts_executed = 0
        self.failures_before_success = failures_before_success

    def supports_document_type(self, document_type: str) -> bool:
        return True

    def _execute_verification(self, doc_fields: Dict[str, Any], attempt: int = 1) -> VerificationResult:
        self.attempts_executed += 1
        if self.attempts_executed <= self.failures_before_success:
            raise TimeoutError(f"Transient timeout on attempt {attempt}")

        return VerificationResult(
            status=VerificationStatus.VERIFIED,
            source=self.name,
            timestamp="2026-10-27T10:00:00Z",
            request_hash=compute_sha256(doc_fields),
            response_hash=compute_sha256({"ok": True}),
            document_type="Test Document",
            issuer_name=self.name,
            advisory="Success after retry."
        )


def test_retry_with_backoff_success_after_transient_failures():
    """Verifies that transient errors trigger retries with backoff and succeed."""
    connector = FlakyTestConnector(failures_before_success=2)
    res = connector.verify({"document_type": "Test Doc", "ref": "REF-123"})

    assert res.status == VerificationStatus.VERIFIED
    assert connector.attempts_executed == 3
    assert res.attempts == 3


def test_retry_exhaustion_routes_to_manual_review_queue():
    """Verifies that exhausting retries yields source_unavailable and auto-enqueues."""
    connector = FlakyTestConnector(failures_before_success=5)  # Will fail all 3 retries
    res = connector.verify({"document_type": "Critical Certificate", "reference_number": "REF-FAIL"})

    assert res.status == VerificationStatus.SOURCE_UNAVAILABLE
    assert connector.attempts_executed == 3
    assert res.routed_to_manual_review is True
    assert res.manual_review_id is not None
    assert "MRQ-" in res.manual_review_id

    # Check queue
    queue_item = default_manual_review_queue.get(res.manual_review_id)
    assert queue_item is not None
    assert queue_item.priority == ManualReviewPriority.HIGH
    assert queue_item.status == ManualReviewStatus.PENDING_REVIEW


# ============================================================================
# 3. API LOOKUP CONNECTOR TESTS
# ============================================================================

def test_api_lookup_verified_outcome():
    """Verifies active matching COEP Fire NOC yields 'verified'."""
    connector = ApiLookupConnector()
    res = connector.verify({
        "document_type": "Fire Safety Certificate",
        "reference_number": "FIR/2025/98354",
        "institution_name": "College of Engineering Pune (COEP Technological University)"
    })

    assert res.status == VerificationStatus.VERIFIED
    assert len(res.discrepancies) == 0
    assert "verified successfully" in res.advisory.lower()
    assert res.source == "Statutory Registry API Gateway"
    assert len(res.request_hash) == 64
    assert len(res.response_hash) == 64


def test_api_lookup_mismatch_detected_outcome():
    """Verifies entity & occupancy mismatch yields 'mismatch_detected'."""
    connector = ApiLookupConnector()
    res = connector.verify({
        "document_type": "Fire Safety Certificate",
        "reference_number": "FIR/2025/89612",  # Registered to Phusro Mall
        "institution_name": "VJTI Engineering Institute",
        "occupancy_type": "Educational (Group B)"
    })

    assert res.status == VerificationStatus.MISMATCH_DETECTED
    assert len(res.discrepancies) >= 1
    disc_types = [d.discrepancy_type for d in res.discrepancies]
    assert "ENTITY_MISMATCH" in disc_types or "OCCUPANCY_CLASSIFICATION_MISMATCH" in disc_types


def test_api_lookup_expired_outcome():
    """Verifies lapsed certificate yields 'expired'."""
    connector = ApiLookupConnector()
    res = connector.verify({
        "document_type": "Fire Safety Certificate",
        "reference_number": "FS/2023/8812",  # Expired 2024-01-09
        "institution_name": "Apex Institute of Technology & Science"
    })

    assert res.status == VerificationStatus.EXPIRED
    assert len(res.discrepancies) == 1
    assert res.discrepancies[0].discrepancy_type == "CERTIFICATE_EXPIRED"


def test_api_lookup_unregistered_reference_routes_to_manual_review():
    """Verifies non-existent reference number yields 'manual_review_required'."""
    connector = ApiLookupConnector()
    res = connector.verify({
        "document_type": "Fire Safety Certificate",
        "reference_number": "FIR/NONEXISTENT/000",
        "institution_name": "Unknown Trust"
    })

    assert res.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    assert res.routed_to_manual_review is True
    assert res.manual_review_id is not None
    assert "not located in the digital" in res.advisory.lower()


# ============================================================================
# 4. QR DECODE CONNECTOR TESTS (PYZBAR & OPENCV)
# ============================================================================

def test_qr_decode_verified_matching_code():
    """Verifies QR code with matching reference and active validity yields 'verified'."""
    connector = QrDecodeConnector()
    qr_img = qrcode.make("https://fire.karnataka.gov.in/verify?ref=FIR/2025/98354&name=College+of+Engineering+Pune&valid_till=2027-06-30")

    res = connector.verify({
        "document_type": "Fire Safety Certificate",
        "reference_number": "FIR/2025/98354",
        "institution_name": "College of Engineering Pune",
        "image": qr_img
    })

    assert res.status == VerificationStatus.VERIFIED
    assert len(res.discrepancies) == 0
    assert "QR verification successful" in res.advisory


def test_qr_decode_reference_mismatch():
    """Verifies QR code pointing to a different reference number yields 'mismatch_detected'."""
    connector = QrDecodeConnector()
    qr_img = qrcode.make("https://fire.karnataka.gov.in/verify?ref=FIR/2021/11094&name=College+of+Engineering+Pune")

    res = connector.verify({
        "document_type": "Fire Safety Certificate",
        "reference_number": "FIR/2025/98354",  # Printed differs from QR
        "institution_name": "College of Engineering Pune",
        "image": qr_img
    })

    assert res.status == VerificationStatus.MISMATCH_DETECTED
    assert len(res.discrepancies) >= 1
    assert any(d.discrepancy_type == "QR_REFERENCE_MISMATCH" for d in res.discrepancies)


def test_qr_decode_expired_certificate():
    """Verifies QR payload with lapsed expiry date yields 'expired'."""
    connector = QrDecodeConnector()
    qr_img = qrcode.make("https://fire.karnataka.gov.in/verify?ref=FS/2023/8812&valid_till=2024-01-09")

    res = connector.verify({
        "document_type": "Fire Safety Certificate",
        "reference_number": "FS/2023/8812",
        "image": qr_img
    })

    assert res.status == VerificationStatus.EXPIRED
    assert len(res.discrepancies) == 1
    assert res.discrepancies[0].discrepancy_type == "CERTIFICATE_EXPIRED"


def test_qr_decode_missing_qr_code_routes_to_manual_review():
    """Verifies document lacking a detectable QR code yields 'manual_review_required'."""
    connector = QrDecodeConnector()
    res = connector.verify({
        "document_type": "Fire Safety Certificate",
        "reference_number": "FIR/2025/98354",
        "image": None
    })

    assert res.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    assert res.routed_to_manual_review is True
    assert "missing, cropped, or degraded" in res.advisory.lower()


# ============================================================================
# 5. DIGITAL SIGNATURE CONNECTOR TESTS (PKCS#7 / PAdES)
# ============================================================================

def test_digital_signature_verified_trusted_ca():
    """Verifies valid PKCS#7 signature from recognized CA yields 'verified'."""
    connector = DigitalSignatureConnector()
    res = connector.verify({
        "document_type": "Building Plan Approval",
        "reference_number": "BPA/2025/104",
        "is_digitally_signed": True,
        "signer_name": "Chief Town Planner, BMRDA",
        "cert_authority": "NIC Certifying Authority",
        "cert_valid_till": "2027-12-31"
    })

    assert res.status == VerificationStatus.VERIFIED
    assert len(res.discrepancies) == 0
    assert "Digital signature verified successfully" in res.advisory


def test_digital_signature_byte_tamper_mismatch():
    """Verifies document content modification post-signing yields 'mismatch_detected'."""
    connector = DigitalSignatureConnector()
    res = connector.verify({
        "document_type": "Building Plan Approval",
        "reference_number": "BPA/2025/104",
        "is_digitally_signed": True,
        "tamper_detected": True,
        "signer_name": "Chief Town Planner"
    })

    assert res.status == VerificationStatus.MISMATCH_DETECTED
    assert len(res.discrepancies) == 1
    assert res.discrepancies[0].discrepancy_type == "DIGITAL_SIGNATURE_TAMPER_DETECTED"


def test_digital_signature_expired_certificate():
    """Verifies signing certificate past its expiration yields 'expired'."""
    connector = DigitalSignatureConnector()
    res = connector.verify({
        "document_type": "Building Plan Approval",
        "reference_number": "BPA/2025/104",
        "is_digitally_signed": True,
        "cert_valid_till": "2023-05-15",  # Past date
        "cert_authority": "e-Mudhra"
    })

    assert res.status == VerificationStatus.EXPIRED
    assert len(res.discrepancies) == 1
    assert res.discrepancies[0].discrepancy_type == "SIGNING_CERTIFICATE_EXPIRED"


def test_digital_signature_unsigned_document_routes_to_manual_review():
    """Verifies unsigned document yields 'manual_review_required'."""
    connector = DigitalSignatureConnector()
    res = connector.verify({
        "document_type": "Building Plan Approval",
        "reference_number": "BPA/2025/104",
        "is_digitally_signed": False
    })

    assert res.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    assert res.routed_to_manual_review is True
    assert "lacks cryptographic digital signature" in res.manual_review_reason.lower()


def test_digital_signature_untrusted_ca_routes_to_manual_review():
    """Verifies self-signed or unrecognized CA yields 'manual_review_required'."""
    connector = DigitalSignatureConnector()
    res = connector.verify({
        "document_type": "Building Plan Approval",
        "reference_number": "BPA/2025/104",
        "is_digitally_signed": True,
        "is_self_signed": True,
        "cert_authority": "Rogue Untrusted CA"
    })

    assert res.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    assert res.routed_to_manual_review is True
    assert res.discrepancies[0].discrepancy_type == "UNTRUSTED_ROOT_CERTIFICATE"


# ============================================================================
# 6. CONNECTOR REGISTRY & COMPOSITE VERIFICATION TESTS
# ============================================================================

def test_registry_smart_dispatch():
    """Verifies registry dispatches to appropriate connector based on fields."""
    # QR field present -> dispatches to QR connector
    qr_img = qrcode.make("https://portal.gov.in/verify?ref=FIR/2025/98354&name=COEP")
    res_qr = connector_registry.verify({
        "document_type": "Fire NOC",
        "reference_number": "FIR/2025/98354",
        "institution_name": "College of Engineering Pune",
        "qr_image": qr_img
    })
    assert "QR" in res_qr.source

    # Signature field present -> dispatches to Signature connector
    res_sig = connector_registry.verify({
        "document_type": "Building Plan",
        "reference_number": "BPA/2025/104",
        "is_digitally_signed": True,
        "cert_authority": "NIC CA"
    })
    assert "Signature" in res_sig.source


def test_registry_composite_verification():
    """Verifies multi-channel composite verification across all applicable connectors."""
    composite_report = connector_registry.verify_composite({
        "document_type": "Fire Safety Certificate",
        "reference_number": "FIR/2025/98354",
        "institution_name": "College of Engineering Pune (COEP Technological University)"
    })

    assert "overall_status" in composite_report
    assert "connector_results" in composite_report
    assert len(composite_report["connector_results"]) >= 2


# ============================================================================
# 7. MANUAL REVIEW QUEUE LIFECYCLE TESTS
# ============================================================================

def test_manual_review_queue_resolution():
    """Verifies queue ticket creation, listing, and scrutiny officer sign-off."""
    connector = ApiLookupConnector()
    res = connector.verify({
        "document_type": "Land Deed",
        "reference_number": "LAND/UNKNOWN/999",
        "institution_name": "Rural Academy"
    })

    assert res.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    queue_id = res.manual_review_id

    # Check listing
    pending_items = default_manual_review_queue.list(status=ManualReviewStatus.PENDING_REVIEW)
    assert any(i.queue_id == queue_id for i in pending_items)

    # Scrutiny officer sign-off
    resolved = default_manual_review_queue.resolve(
        queue_id=queue_id,
        officer_email="officer.verma@aicte-india.org",
        resolution_status=ManualReviewStatus.RESOLVED,
        notes="Physically verified with District Registrar; manual entry validated."
    )

    assert resolved is not None
    assert resolved.status == ManualReviewStatus.RESOLVED
    assert resolved.assigned_officer == "officer.verma@aicte-india.org"
    assert resolved.resolved_at is not None


# ============================================================================
# 8. FASTAPI REST API ENDPOINTS TESTS
# ============================================================================

def test_fastapi_connector_verify_endpoint(client):
    """Verifies POST /api/v1/verification/connector/verify."""
    response = client.post(
        "/api/v1/verification/connector/verify",
        json={
            "document_type": "Fire Safety Certificate",
            "preferred_connector": "api",
            "doc_fields": {
                "reference_number": "FIR/2025/98354",
                "institution_name": "College of Engineering Pune (COEP Technological University)"
            }
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "verified"
    assert "request_hash" in data
    assert "response_hash" in data
    assert "source" in data
    assert "timestamp" in data


def test_fastapi_manual_review_queue_endpoints(client):
    """Verifies GET and POST resolution endpoints for manual review queue."""
    # 1. Trigger an item into the queue
    client.post(
        "/api/v1/verification/connector/verify",
        json={
            "document_type": "Fire Safety Certificate",
            "preferred_connector": "api",
            "doc_fields": {
                "reference_number": "UNKNOWN/REF/999",
                "institution_name": "Mystery Institute"
            }
        }
    )

    # 2. List queue
    get_res = client.get("/api/v1/verification/connector/manual-review-queue")
    assert get_res.status_code == 200
    queue = get_res.json()
    assert len(queue) >= 1
    ticket_id = queue[0]["queue_id"]

    # 3. Resolve ticket
    res_post = client.post(
        f"/api/v1/verification/connector/manual-review-queue/{ticket_id}/resolve",
        json={
            "officer_email": "scrutiny.lead@aicte-india.org",
            "resolution_status": "RESOLVED",
            "notes": "Verified against physical district archives."
        }
    )
    assert res_post.status_code == 200
    resolved_item = res_post.json()
    assert resolved_item["status"] == "RESOLVED"
    assert resolved_item["assigned_officer"] == "scrutiny.lead@aicte-india.org"
