"""
PRAMAAN-X Verification Connector Framework: Connector Registry & Dispatcher.

Central registry that maintains all active IssuerConnectors, dynamically routes
verification requests based on document type or preferred connector, and supports
multi-channel composite verification (e.g. API lookup + QR decode + Digital signature).
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Union

from backend.app.services.connectors.base import (
    IssuerConnector,
    VerificationStatus,
    VerificationResult
)
from backend.app.services.connectors.api_lookup_connector import ApiLookupConnector
from backend.app.services.connectors.qr_decode_connector import QrDecodeConnector
from backend.app.services.connectors.digital_signature_connector import DigitalSignatureConnector

logger = logging.getLogger("pramaan_x.connectors.registry")


class ConnectorRegistry:
    """Central registry and dispatcher for IssuerConnectors."""

    def __init__(self):
        self._connectors: Dict[str, IssuerConnector] = {}
        self._initialize_default_connectors()

    def _initialize_default_connectors(self):
        """Registers default statutory API, QR, and Digital Signature connectors."""
        api_conn = ApiLookupConnector()
        qr_conn = QrDecodeConnector(secondary_api_connector=api_conn)
        sig_conn = DigitalSignatureConnector()

        self.register(api_conn)
        self.register(qr_conn)
        self.register(sig_conn)

    def register(self, connector: IssuerConnector) -> None:
        """Registers an IssuerConnector instance."""
        self._connectors[connector.name] = connector
        logger.info(f"Registered verification connector: '{connector.name}'")

    def get_connector(self, name_or_key: str) -> Optional[IssuerConnector]:
        """Looks up a connector by exact name or substring."""
        if name_or_key in self._connectors:
            return self._connectors[name_or_key]
        for name, conn in self._connectors.items():
            if name_or_key.lower() in name.lower():
                return conn
        return None

    def list_connectors(self) -> List[Dict[str, Any]]:
        """Returns metadata for all registered connectors."""
        return [
            {
                "name": conn.name,
                "timeout_seconds": conn.timeout_seconds,
                "max_retries": conn.max_retries,
                "base_backoff_seconds": conn.base_backoff_seconds
            }
            for conn in self._connectors.values()
        ]

    def get_connectors_for_document_type(self, document_type: str) -> List[IssuerConnector]:
        """Finds all connectors supporting the specified document category."""
        return [c for c in self._connectors.values() if c.supports_document_type(document_type)]

    def verify(
        self,
        doc_fields: Dict[str, Any],
        preferred_connector: Optional[str] = None
    ) -> VerificationResult:
        """
        Dispatches verification to the preferred connector or best matching connector.
        
        Args:
            doc_fields: Document fields to verify.
            preferred_connector: Optional connector name/alias ('api', 'qr', 'signature').
            
        Returns:
            VerificationResult: The verification outcome.
        """
        doc_type = str(doc_fields.get("document_type", "Statutory Document"))

        # Explicit connector requested
        if preferred_connector:
            conn = self.get_connector(preferred_connector)
            if conn:
                return conn.verify(doc_fields)

        # Smart Dispatch based on fields present
        # If QR image / payload present -> QR connector
        if any(k in doc_fields for k in ["qr_payload", "qr_image", "qr_text"]):
            qr_conn = self.get_connector("qr")
            if qr_conn:
                return qr_conn.verify(doc_fields)

        # If digital signature / pdf bytes present -> Signature connector
        if any(k in doc_fields for k in ["is_digitally_signed", "cert_authority", "tamper_detected", "file_bytes"]):
            sig_conn = self.get_connector("signature")
            if sig_conn:
                return sig_conn.verify(doc_fields)

        # Default to API Lookup Connector
        api_conn = self.get_connector("api") or next(iter(self._connectors.values()))
        return api_conn.verify(doc_fields)

    def verify_composite(
        self,
        doc_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes multi-channel verification across all applicable connectors
        (e.g. API registry match + QR cross-examination + Digital signature integrity).
        Returns aggregated composite audit report.
        """
        doc_type = str(doc_fields.get("document_type", "Statutory Document"))
        matching_connectors = self.get_connectors_for_document_type(doc_type)

        results: Dict[str, Any] = {}
        overall_status = VerificationStatus.VERIFIED

        for conn in matching_connectors:
            res = conn.verify(doc_fields)
            results[conn.name] = res.to_dict()

            # Priority of failure statuses: mismatch > expired > unavailable > manual_review > pending > verified
            if res.status == VerificationStatus.MISMATCH_DETECTED:
                overall_status = VerificationStatus.MISMATCH_DETECTED
            elif res.status == VerificationStatus.EXPIRED and overall_status != VerificationStatus.MISMATCH_DETECTED:
                overall_status = VerificationStatus.EXPIRED
            elif res.status == VerificationStatus.SOURCE_UNAVAILABLE and overall_status not in [VerificationStatus.MISMATCH_DETECTED, VerificationStatus.EXPIRED]:
                overall_status = VerificationStatus.SOURCE_UNAVAILABLE
            elif res.status == VerificationStatus.MANUAL_REVIEW_REQUIRED and overall_status == VerificationStatus.VERIFIED:
                overall_status = VerificationStatus.MANUAL_REVIEW_REQUIRED

        return {
            "overall_status": overall_status.value,
            "document_type": doc_type,
            "reference_number": doc_fields.get("reference_number"),
            "connector_results": results
        }


# Singleton connector registry instance
connector_registry = ConnectorRegistry()
