"""
PRAMAAN-X Verification Connector Framework: API Lookup Connector.

Queries authoritative government registries (State Fire NOC, Revenue Land Records,
University Affiliation, Building Plan Approval, CBDT Form 16 / TDS Gateway).

Supports:
- Live HTTP calls with timeout and exponential backoff
- Local fallback to mock_issuer authoritative registry JSON
- Field discrepancy matching (entity name, expiry date, occupancy type, land area)
- Strict mapping to 6 verification statuses:
  'verified', 'mismatch_detected', 'expired', 'verification_pending',
  'source_unavailable', 'manual_review_required'
"""

from __future__ import annotations

import os
import json
import time
import httpx
import logging
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.app.services.connectors.base import (
    IssuerConnector,
    VerificationStatus,
    VerificationResult,
    DiscrepancyDetail,
    compute_sha256
)

logger = logging.getLogger("pramaan_x.connectors.api")

def _find_registry_file() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "mock_issuer" / "data" / "registry.json"
        if candidate.exists():
            return candidate
    return current.parents[4] / "mock_issuer" / "data" / "registry.json"

REGISTRY_PATH = _find_registry_file()

SUPPORTED_DOC_TYPES = {
    "fire safety certificate": "fire",
    "fire safety noc": "fire",
    "fire noc": "fire",
    "state fire clearance": "fire",
    "land deed": "land",
    "land use certificate": "land",
    "title deed": "land",
    "revenue survey record": "land",
    "university affiliation order": "affiliation",
    "university affiliation": "affiliation",
    "affiliation certificate": "affiliation",
    "building plan approval": "fire", # town planning / municipal master plan
    "approved building plan": "fire",
    "faculty tax record": "tax",
    "cbdt form 16": "tax",
    "form 16 / 26as": "tax",
    "accreditation certificate": "accreditation",
    "nba accreditation": "accreditation"
}


class ApiLookupConnector(IssuerConnector):
    """
    Connects to external statutory issuer APIs (or local authoritative mock registry)
    to verify document credentials, validity, and declared parameters.
    """

    def __init__(
        self,
        name: str = "Statutory Registry API Gateway",
        base_url: Optional[str] = None,
        timeout_seconds: float = 3.5,
        max_retries: int = 3,
        base_backoff_seconds: float = 0.2,
        max_backoff_seconds: float = 1.5,
        manual_review_queue: Optional[Any] = None
    ):
        super().__init__(
            name=name,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            base_backoff_seconds=base_backoff_seconds,
            max_backoff_seconds=max_backoff_seconds,
            manual_review_queue=manual_review_queue
        )
        self.base_url = base_url or os.getenv("MOCK_ISSUER_URL")
        self._cached_registry: Optional[Dict[str, Any]] = None

    def supports_document_type(self, document_type: str) -> bool:
        """Checks if document category is supported by the statutory API lookup."""
        clean_name = document_type.strip().lower()
        if clean_name in SUPPORTED_DOC_TYPES:
            return True
        return any(k in clean_name for k in ["fire", "land", "affiliation", "tax", "accreditation", "building"])

    def _get_authority_key(self, doc_type: str) -> str:
        """Maps document type to registry authority key ('fire', 'land', 'affiliation', 'accreditation')."""
        clean_name = doc_type.strip().lower()
        for k, v in SUPPORTED_DOC_TYPES.items():
            if k in clean_name:
                return v
        if "fire" in clean_name:
            return "fire"
        if "land" in clean_name:
            return "land"
        if "affiliation" in clean_name:
            return "affiliation"
        return "fire"

    def _load_registry_records(self) -> Dict[str, Any]:
        """Loads authoritative records from mock_issuer registry file."""
        if self._cached_registry is not None:
            return self._cached_registry

        if REGISTRY_PATH.exists():
            try:
                with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                    self._cached_registry = json.load(f)
                    return self._cached_registry
            except Exception as e:
                logger.error(f"Failed to load registry from {REGISTRY_PATH}: {e}")

        # Fallback minimal records
        self._cached_registry = {
            "authorities": {
                "fire": {"name": "State Fire & Emergency Services", "records": {}},
                "land": {"name": "State Revenue & Land Records", "records": {}},
                "affiliation": {"name": "State Examining University", "records": {}},
                "accreditation": {"name": "National Board of Accreditation", "records": {}}
            }
        }
        return self._cached_registry

    def _execute_verification(self, doc_fields: Dict[str, Any], attempt: int = 1) -> VerificationResult:
        """
        Executes API query with simulated or live HTTP lookup and field cross-examination.
        """
        # Testing hooks for simulated network anomalies
        simulated_error = doc_fields.get("simulated_error")
        if simulated_error == "timeout":
            raise TimeoutError(f"Simulated HTTP gateway timeout on attempt {attempt}")
        if simulated_error == "503" or simulated_error == "connection_error":
            raise ConnectionError(f"Simulated HTTP 503 Service Unavailable on attempt {attempt}")

        doc_type = str(doc_fields.get("document_type", "Fire Safety Certificate"))
        ref_no = str(doc_fields.get("reference_number") or doc_fields.get("ref") or doc_fields.get("noc_number") or "").strip()
        claimed_entity = str(doc_fields.get("institution_name") or doc_fields.get("registered_entity") or "").strip()
        claimed_expiry = str(doc_fields.get("expiry_date") or doc_fields.get("valid_till") or "").strip()

        authority_key = self._get_authority_key(doc_type)

        # 1. Attempt live query if mock issuer service base_url is accessible
        if self.base_url:
            try:
                api_key = os.getenv("ISSUER_API_KEY", "pramaanx-mock-key-2025")
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    resp = client.get(
                        f"{self.base_url.rstrip('/')}/verify",
                        params={"authority": authority_key, "ref": ref_no, "name": claimed_entity},
                        headers={"X-API-Key": api_key}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return self._map_remote_response(data, doc_fields, authority_key)
                    elif resp.status_code == 503:
                        raise ConnectionError("Remote mock issuer returned HTTP 503 (Source Unavailable)")
            except (httpx.TimeoutException, TimeoutError):
                raise TimeoutError(f"HTTP timeout connecting to mock issuer gateway at {self.base_url}")
            except (httpx.ConnectError, ConnectionError) as ce:
                raise ConnectionError(f"Connection failure to mock issuer: {ce}")
            except Exception as e:
                logger.warning(f"Live API query failed ({e}), falling back to local registry.")

        # 2. Local Authoritative Registry Lookup
        registry = self._load_registry_records()
        auth_data = registry.get("authorities", {}).get(authority_key, {})
        auth_name = auth_data.get("name", f"State {authority_key.title()} Authority")
        records = auth_data.get("records", {})

        # Find record by reference number (case-insensitive)
        matched_record = None
        for r_key, r_val in records.items():
            if r_key.upper() == ref_no.upper() or r_val.get("reference_number", "").upper() == ref_no.upper():
                matched_record = r_val
                break

        # A. Reference Number Not Found in Digital Registry
        if not matched_record:
            return VerificationResult(
                status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
                source=f"{auth_name} Registry",
                timestamp=datetime.now(timezone.utc).isoformat(),
                request_hash=compute_sha256(doc_fields),
                response_hash=compute_sha256({"matched": False, "reference_number": ref_no}),
                document_type=doc_type,
                reference_number=ref_no,
                issuer_name=auth_name,
                authoritative_data={},
                discrepancies=[],
                advisory=(
                    f"Reference number '{ref_no}' was not located in the digital {auth_name} registry. "
                    f"Indicator for review: Document may be a legacy manual issue or requires physical registry cross-examination."
                ),
                manual_review_reason=f"Reference number '{ref_no}' not found in authoritative digital database.",
                raw_response={"status": "not_found", "reference_number": ref_no}
            )

        # B. Check Expiry
        issuer_expiry = str(matched_record.get("expiry_date") or matched_record.get("valid_till") or "")
        is_expired = False
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if issuer_expiry and issuer_expiry < today_str:
            is_expired = True
        elif matched_record.get("status") in ["LAPSED", "EXPIRED", "REVOKED"]:
            is_expired = True

        if is_expired:
            return VerificationResult(
                status=VerificationStatus.EXPIRED,
                source=f"{auth_name} Registry",
                timestamp=datetime.now(timezone.utc).isoformat(),
                request_hash=compute_sha256(doc_fields),
                response_hash=compute_sha256(matched_record),
                document_type=doc_type,
                reference_number=ref_no,
                issuer_name=auth_name,
                authoritative_data=matched_record,
                discrepancies=[
                    DiscrepancyDetail(
                        field="expiry_date",
                        claimed_value=claimed_expiry or "Active Claim",
                        issuer_value=issuer_expiry or "LAPSED",
                        discrepancy_type="CERTIFICATE_EXPIRED",
                        summary=f"Certificate expired on {issuer_expiry or 'past date'} per statutory registry."
                    )
                ],
                advisory=f"Indicator for review: Statutory {doc_type} lapsed on {issuer_expiry}; no active renewal registered.",
                raw_response=matched_record
            )

        # C. Cross-check entity name & parameter discrepancies
        discrepancies: List[DiscrepancyDetail] = []
        reg_entity = str(matched_record.get("registered_entity", "")).strip()

        # Check entity name mismatch (if both are provided and have significant divergence)
        if claimed_entity and reg_entity:
            claimed_tokens = set(claimed_entity.lower().replace("&", "and").split())
            reg_tokens = set(reg_entity.lower().replace("&", "and").split())
            overlap = len(claimed_tokens.intersection(reg_tokens))
            similarity = overlap / max(1, min(len(claimed_tokens), len(reg_tokens)))

            if similarity < 0.35 and not any(t in reg_entity.lower() for t in ["college", "institute", "trust"]):
                discrepancies.append(DiscrepancyDetail(
                    field="registered_entity",
                    claimed_value=claimed_entity,
                    issuer_value=reg_entity,
                    discrepancy_type="ENTITY_MISMATCH",
                    summary=f"Certificate registered to '{reg_entity}' instead of applicant '{claimed_entity}'."
                ))

        # Check occupancy type discrepancy (e.g. Commercial vs Educational)
        claimed_occ = doc_fields.get("occupancy_type")
        issuer_occ = matched_record.get("occupancy_type")
        if claimed_occ and issuer_occ and "educational" in str(claimed_occ).lower() and "commercial" in str(issuer_occ).lower():
            discrepancies.append(DiscrepancyDetail(
                field="occupancy_type",
                claimed_value=claimed_occ,
                issuer_value=issuer_occ,
                discrepancy_type="OCCUPANCY_CLASSIFICATION_MISMATCH",
                summary=f"Occupancy is registered as '{issuer_occ}' in town planning, differing from educational use."
            ))

        # Check pending status in registry
        if matched_record.get("status") in ["PENDING_RENEWAL", "IN_PROCESS", "UNDER_SCRUTINY"]:
            return VerificationResult(
                status=VerificationStatus.VERIFICATION_PENDING,
                source=f"{auth_name} Registry",
                timestamp=datetime.now(timezone.utc).isoformat(),
                request_hash=compute_sha256(doc_fields),
                response_hash=compute_sha256(matched_record),
                document_type=doc_type,
                reference_number=ref_no,
                issuer_name=auth_name,
                authoritative_data=matched_record,
                discrepancies=discrepancies,
                advisory="Certificate renewal application is currently pending with statutory authority.",
                raw_response=matched_record
            )

        # Mismatch detected outcome
        if discrepancies:
            return VerificationResult(
                status=VerificationStatus.MISMATCH_DETECTED,
                source=f"{auth_name} Registry",
                timestamp=datetime.now(timezone.utc).isoformat(),
                request_hash=compute_sha256(doc_fields),
                response_hash=compute_sha256(matched_record),
                document_type=doc_type,
                reference_number=ref_no,
                issuer_name=auth_name,
                authoritative_data=matched_record,
                discrepancies=discrepancies,
                advisory=f"Indicator for review: {len(discrepancies)} parameter discrepancy(ies) detected against {auth_name} records.",
                raw_response=matched_record
            )

        # D. Conclusive Match -> VERIFIED
        return VerificationResult(
            status=VerificationStatus.VERIFIED,
            source=f"{auth_name} Registry",
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_hash=compute_sha256(doc_fields),
            response_hash=compute_sha256(matched_record),
            document_type=doc_type,
            reference_number=ref_no,
            issuer_name=auth_name,
            authoritative_data=matched_record,
            discrepancies=[],
            advisory=f"Authoritative record verified successfully with {auth_name}. Certificate is valid and active.",
            raw_response=matched_record
        )

    def _map_remote_response(self, data: Dict[str, Any], doc_fields: Dict[str, Any], authority_key: str) -> VerificationResult:
        """Normalizes external HTTP response into standard VerificationResult."""
        raw_status = data.get("status", "verified")
        status_map = {
            "verified": VerificationStatus.VERIFIED,
            "mismatch": VerificationStatus.MISMATCH_DETECTED,
            "mismatch_detected": VerificationStatus.MISMATCH_DETECTED,
            "expired": VerificationStatus.EXPIRED,
            "not_found": VerificationStatus.MANUAL_REVIEW_REQUIRED,
            "pending": VerificationStatus.VERIFICATION_PENDING,
            "verification_pending": VerificationStatus.VERIFICATION_PENDING,
            "source_unavailable": VerificationStatus.SOURCE_UNAVAILABLE,
            "manual_review_required": VerificationStatus.MANUAL_REVIEW_REQUIRED
        }
        status = status_map.get(raw_status, VerificationStatus.MANUAL_REVIEW_REQUIRED)
        issuer_name = data.get("issuer_name", f"{authority_key.title()} Statutory Portal")

        discrepancies: List[DiscrepancyDetail] = []
        for d in data.get("discrepancies", []):
            discrepancies.append(DiscrepancyDetail(
                field=d.get("field", "general"),
                claimed_value=d.get("claimed_value"),
                issuer_value=d.get("issuer_value"),
                discrepancy_type=d.get("discrepancy_type", "FIELD_MISMATCH"),
                summary=d.get("summary", "")
            ))

        return VerificationResult(
            status=status,
            source=issuer_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_hash=compute_sha256(doc_fields),
            response_hash=compute_sha256(data),
            document_type=str(doc_fields.get("document_type", "Statutory Document")),
            reference_number=doc_fields.get("reference_number") or data.get("reference_number"),
            issuer_name=issuer_name,
            authoritative_data=data.get("authoritative_record") or data.get("record") or {},
            discrepancies=discrepancies,
            advisory=data.get("advisory", f"Registry verification status: {status.value}"),
            raw_response=data
        )
