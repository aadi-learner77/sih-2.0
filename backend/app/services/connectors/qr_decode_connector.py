"""
PRAMAAN-X Verification Connector Framework: QR Decode + Lookup Connector.

Decodes cryptographic and verification QR codes from document images, PDF pages,
or buffers using pyzbar with OpenCV fallback and CLAHE contrast enhancement.
Cross-verifies decoded payload (URL, JSON, key-value) against claimed document fields
and optionally conducts secondary lookup against authoritative issuer registries.

Strictly maps outcomes to 6 standard verification statuses:
'verified', 'mismatch_detected', 'expired', 'verification_pending',
'source_unavailable', 'manual_review_required'
"""

from __future__ import annotations

import re
import io
import json
import urllib.parse
import logging
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from PIL import Image

import cv2
try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False

try:
    import pymupdf # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from backend.app.services.connectors.base import (
    IssuerConnector,
    VerificationStatus,
    VerificationResult,
    DiscrepancyDetail,
    compute_sha256
)
from backend.app.services.connectors.api_lookup_connector import ApiLookupConnector

logger = logging.getLogger("pramaan_x.connectors.qr")


class QrDecodeConnector(IssuerConnector):
    """
    Decodes verification QR codes using pyzbar / OpenCV and performs cross-field
    integrity matching and optional authoritative registry lookup.
    """

    def __init__(
        self,
        name: str = "Document QR Security Gateway",
        timeout_seconds: float = 4.0,
        max_retries: int = 3,
        base_backoff_seconds: float = 0.2,
        max_backoff_seconds: float = 1.5,
        manual_review_queue: Optional[Any] = None,
        secondary_api_connector: Optional[ApiLookupConnector] = None
    ):
        super().__init__(
            name=name,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            base_backoff_seconds=base_backoff_seconds,
            max_backoff_seconds=max_backoff_seconds,
            manual_review_queue=manual_review_queue
        )
        self.secondary_api_connector = secondary_api_connector or ApiLookupConnector(
            name="Secondary Statutory Lookup (QR Linked)"
        )

    def supports_document_type(self, document_type: str) -> bool:
        """QR verification is applicable across any statutory or technical document."""
        clean = document_type.strip().lower()
        supported_keywords = [
            "fire", "land", "affiliation", "building", "plan",
            "tax", "accreditation", "certificate", "noc", "order", "qr"
        ]
        return any(k in clean for k in supported_keywords)

    def decode_qr_payload(self, doc_input: Any) -> Tuple[Optional[str], Optional[str]]:
        """
        Extracts QR code text from image path, PDF file, bytes, or numpy array.
        Returns: (decoded_payload, decoder_used)
        """
        # Case 1: Pre-extracted string already provided
        if isinstance(doc_input, str) and (doc_input.startswith("http") or "ref=" in doc_input or "{" in doc_input):
            return doc_input.strip(), "pre_extracted_string"

        # Case 2: File path or raw bytes/image
        img_bgr: Optional[np.ndarray] = None

        if isinstance(doc_input, (str, Path)):
            p = Path(doc_input)
            if not p.exists():
                return None, None
            if p.suffix.lower() == ".pdf" and PYMUPDF_AVAILABLE:
                # Render first page of PDF to image pixmap
                doc = pymupdf.open(str(p))
                if len(doc) > 0:
                    page = doc[0]
                    pix = page.get_pixmap(dpi=150)
                    img_data = pix.tobytes("png")
                    nparr = np.frombuffer(img_data, np.uint8)
                    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                img_bgr = cv2.imread(str(p))

        elif isinstance(doc_input, (bytes, bytearray)):
            nparr = np.frombuffer(doc_input, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        elif isinstance(doc_input, Image.Image) or hasattr(doc_input, "convert"):
            arr = np.array(doc_input.convert("RGB"))
            img_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

        elif isinstance(doc_input, np.ndarray):
            img_bgr = doc_input

        if img_bgr is None:
            return None, None

        # 1. Primary Attempt with PyZbar
        if PYZBAR_AVAILABLE:
            try:
                decoded_objs = pyzbar_decode(img_bgr)
                if decoded_objs:
                    data = decoded_objs[0].data.decode("utf-8", errors="ignore").strip()
                    if data:
                        return data, "pyzbar"
            except Exception as e:
                logger.debug(f"PyZbar decode failed: {e}")

        # 2. Secondary Attempt with OpenCV QRCodeDetector
        try:
            detector = cv2.QRCodeDetector()
            val, points, _ = detector.detectAndDecode(img_bgr)
            if val and len(str(val).strip()) > 0:
                return str(val).strip(), "opencv"

            # 3. Enhanced CLAHE Attempt with OpenCV for noisy/low-contrast scans
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            val, points, _ = detector.detectAndDecode(enhanced)
            if val and len(str(val).strip()) > 0:
                return str(val).strip(), "opencv_clahe"

            # Also try pyzbar on enhanced image if available
            if PYZBAR_AVAILABLE:
                decoded_objs = pyzbar_decode(enhanced)
                if decoded_objs:
                    data = decoded_objs[0].data.decode("utf-8", errors="ignore").strip()
                    if data:
                        return data, "pyzbar_clahe"
        except Exception as e:
            logger.debug(f"OpenCV QR decode error: {e}")

        return None, None

    def parse_qr_payload(self, raw_payload: str) -> Dict[str, Any]:
        """
        Parses QR string into structured dictionary of reference numbers, entity names, and dates.
        Supports URL query strings, JSON structures, and key-value pairs.
        """
        parsed: Dict[str, Any] = {"raw_payload": raw_payload}

        # 1. JSON Payload
        if raw_payload.startswith("{") and raw_payload.endswith("}"):
            try:
                data = json.loads(raw_payload)
                if isinstance(data, dict):
                    parsed.update(data)
                    return parsed
            except Exception:
                pass

        # 2. URL Payload (e.g. https://portal.gov.in/verify?ref=FIR/2025/98354&name=COEP)
        if "://" in raw_payload or "?" in raw_payload:
            try:
                parsed_url = urllib.parse.urlparse(raw_payload)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                for k, v in query_params.items():
                    parsed[k.lower()] = v[0] if v else ""
                if "ref" in parsed and "reference_number" not in parsed:
                    parsed["reference_number"] = parsed["ref"]
                if "name" in parsed and "institution_name" not in parsed:
                    parsed["institution_name"] = parsed["name"]
                if "expiry" in parsed and "expiry_date" not in parsed:
                    parsed["expiry_date"] = parsed["expiry"]
                return parsed
            except Exception:
                pass

        # 3. Regex Pattern Fallbacks
        ref_match = re.search(r"(?:ref|certificate|noc|order)[=_: ]+([A-Za-z0-9/\-_]+)", raw_payload, re.IGNORECASE)
        if not ref_match:
            ref_match = re.search(r"([A-Z]{2,4}/\d{4}/\d{3,6})", raw_payload)
        if ref_match:
            parsed["reference_number"] = ref_match.group(1).strip()

        date_match = re.search(r"(?:valid_till|expiry|validity)[=_: ]+(\d{4}-\d{2}-\d{2})", raw_payload, re.IGNORECASE)
        if date_match:
            parsed["expiry_date"] = date_match.group(1).strip()

        return parsed

    def _execute_verification(self, doc_fields: Dict[str, Any], attempt: int = 1) -> VerificationResult:
        """
        Executes QR decoding, compares decoded values with claimed document fields,
        and optionally triggers secondary lookup.
        """
        # Testing hooks for simulated network/transient anomalies
        if doc_fields.get("simulated_error") == "timeout":
            raise TimeoutError(f"Simulated QR lookup timeout on attempt {attempt}")
        if doc_fields.get("simulated_error") == "source_unavailable":
            raise ConnectionError(f"Simulated QR secondary gateway unavailable on attempt {attempt}")

        doc_type = str(doc_fields.get("document_type", "Statutory Certificate"))
        claimed_ref = str(doc_fields.get("reference_number") or doc_fields.get("ref") or "").strip()
        claimed_entity = str(doc_fields.get("institution_name") or doc_fields.get("registered_entity") or "").strip()
        claimed_expiry = str(doc_fields.get("expiry_date") or doc_fields.get("valid_till") or "").strip()

        # Check for image input in doc_fields
        doc_input = (
            doc_fields.get("qr_payload") or
            doc_fields.get("file_path") or
            doc_fields.get("file_bytes") or
            doc_fields.get("image") or
            doc_fields.get("qr_image")
        )

        # 1. Decode QR Code
        decoded_text, decoder_engine = self.decode_qr_payload(doc_input)

        if not decoded_text:
            return VerificationResult(
                status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
                source=f"{self.name} (Scanner)",
                timestamp=datetime.now(timezone.utc).isoformat(),
                request_hash=compute_sha256(doc_fields),
                response_hash=compute_sha256({"qr_detected": False}),
                document_type=doc_type,
                reference_number=claimed_ref,
                issuer_name="Document QR Verification Engine",
                authoritative_data={},
                discrepancies=[],
                advisory=(
                    f"No legible verification QR code was detected on the submitted '{doc_type}'. "
                    f"Indicator for review: Mandatory statutory QR watermark is missing, cropped, or degraded."
                ),
                manual_review_reason="Verification QR code could not be decoded by pyzbar or OpenCV.",
                raw_response={"qr_detected": False, "claimed_reference": claimed_ref}
            )

        # 2. Parse Structured QR Payload
        qr_data = self.parse_qr_payload(decoded_text)
        qr_ref = str(qr_data.get("reference_number") or qr_data.get("ref") or "").strip()
        qr_entity = str(qr_data.get("institution_name") or qr_data.get("name") or qr_data.get("registered_entity") or "").strip()
        qr_expiry = str(qr_data.get("expiry_date") or qr_data.get("valid_till") or "").strip()

        discrepancies: List[DiscrepancyDetail] = []

        # 3. Check QR vs Claimed Reference Number Mismatch
        if claimed_ref and qr_ref and claimed_ref.upper() != qr_ref.upper():
            discrepancies.append(DiscrepancyDetail(
                field="reference_number",
                claimed_value=claimed_ref,
                issuer_value=qr_ref,
                discrepancy_type="QR_REFERENCE_MISMATCH",
                summary=(
                    f"QR code encodes reference '{qr_ref}' which conflicts with claimed "
                    f"printed reference '{claimed_ref}'."
                )
            ))

        # 4. Check QR vs Claimed Entity Name Mismatch
        if claimed_entity and qr_entity:
            t_claimed = set(claimed_entity.lower().replace("&", "and").split())
            t_qr = set(qr_entity.lower().replace("&", "and").split())
            overlap = len(t_claimed.intersection(t_qr))
            similarity = overlap / max(1, min(len(t_claimed), len(t_qr)))
            if similarity < 0.35 and not any(k in qr_entity.lower() for k in ["college", "institute", "trust"]):
                discrepancies.append(DiscrepancyDetail(
                    field="registered_entity",
                    claimed_value=claimed_entity,
                    issuer_value=qr_entity,
                    discrepancy_type="QR_ENTITY_MISMATCH",
                    summary=f"QR payload assigns certificate to '{qr_entity}' instead of applicant '{claimed_entity}'."
                ))

        # 5. Check QR Expiry Date
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if qr_expiry and qr_expiry < today_str:
            return VerificationResult(
                status=VerificationStatus.EXPIRED,
                source=f"{self.name} ({decoder_engine})",
                timestamp=datetime.now(timezone.utc).isoformat(),
                request_hash=compute_sha256(doc_fields),
                response_hash=compute_sha256(qr_data),
                document_type=doc_type,
                reference_number=qr_ref or claimed_ref,
                issuer_name="Document QR Verification Engine",
                authoritative_data=qr_data,
                discrepancies=[
                    DiscrepancyDetail(
                        field="expiry_date",
                        claimed_value=claimed_expiry or "Active",
                        issuer_value=qr_expiry,
                        discrepancy_type="CERTIFICATE_EXPIRED",
                        summary=f"QR code payload confirms validity expired on {qr_expiry}."
                    )
                ],
                advisory=f"Indicator for review: Document QR code indicates certificate lapsed on {qr_expiry}.",
                raw_response=qr_data
            )

        # If discrepancies detected between QR payload and claimed document
        if discrepancies:
            return VerificationResult(
                status=VerificationStatus.MISMATCH_DETECTED,
                source=f"{self.name} ({decoder_engine})",
                timestamp=datetime.now(timezone.utc).isoformat(),
                request_hash=compute_sha256(doc_fields),
                response_hash=compute_sha256(qr_data),
                document_type=doc_type,
                reference_number=qr_ref or claimed_ref,
                issuer_name="Document QR Verification Engine",
                authoritative_data=qr_data,
                discrepancies=discrepancies,
                advisory=(
                    f"Indicator for review: Critical mismatch between QR code metadata and declared "
                    f"document text ({len(discrepancies)} discrepancy items)."
                ),
                raw_response=qr_data
            )

        # 6. Secondary Authoritative Lookup (if reference number is extracted)
        effective_ref = qr_ref or claimed_ref
        if effective_ref and doc_fields.get("perform_secondary_lookup", True):
            lookup_query = {
                "document_type": doc_type,
                "reference_number": effective_ref,
                "institution_name": qr_entity or claimed_entity,
                "expiry_date": qr_expiry or claimed_expiry
            }
            sec_res = self.secondary_api_connector.verify(lookup_query)
            
            # Propagate secondary status if not verified
            if sec_res.status != VerificationStatus.VERIFIED:
                sec_res.source = f"{self.name} -> {sec_res.source}"
                sec_res.advisory = f"QR verified, but secondary registry check returned: {sec_res.status.value}. {sec_res.advisory}"
                return sec_res

        # 7. Fully Verified Outcome
        return VerificationResult(
            status=VerificationStatus.VERIFIED,
            source=f"{self.name} ({decoder_engine})",
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_hash=compute_sha256(doc_fields),
            response_hash=compute_sha256(qr_data),
            document_type=doc_type,
            reference_number=effective_ref,
            issuer_name="Document QR Verification Engine",
            authoritative_data=qr_data,
            discrepancies=[],
            advisory=f"QR verification successful via {decoder_engine}. Encoded metadata aligns with claimed document fields.",
            raw_response=qr_data
        )
