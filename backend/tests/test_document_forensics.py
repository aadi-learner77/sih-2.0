"""
Pytest Test Suite for Document Forensics Module:
Validates all 5 forensic detection capabilities, evidence extraction, threshold calibration,
and strict adherence to regulatory wording constraints ("indicator for review", never "verdict" or "fraud").
"""

import os
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.document_forensics import (
    DocumentForensicsEngine,
    document_forensics_engine,
    ForensicIndicator
)
from backend.app.services.calibrate_forensics import (
    ForensicsCalibrator,
    ensure_ground_truth_fixtures,
    SAMPLE_DIR,
    GT_CATALOG_FILE,
    CALIBRATION_OUTPUT_FILE
)


@pytest.fixture(scope="session", autouse=True)
def setup_forensics_ground_truth():
    """Ensures test samples and ground truth fixtures are initialized once for testing."""
    return ensure_ground_truth_fixtures(SAMPLE_DIR)


@pytest.fixture
def test_client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


# ============================================================================
# CHECK 1: PDF METADATA ANALYSIS
# ============================================================================

def test_check1_pdf_metadata_producer_and_incremental_updates():
    """Validates detection of editing software signature (Canva) and incremental update trailers."""
    meta_path = SAMPLE_DIR / "gt_metadata_anomaly.pdf"
    assert meta_path.exists(), f"Sample not found: {meta_path}"

    with open(meta_path, "rb") as f:
        file_bytes = f.read()

    indicators = document_forensics_engine.check_pdf_metadata(file_bytes, filename=meta_path.name)
    assert len(indicators) >= 1

    indicator_ids = [i.indicator_id for i in indicators]
    assert "PDF_METADATA_PRODUCER_ANOMALY" in indicator_ids
    assert "PDF_INCREMENTAL_UPDATES_DETECTED" in indicator_ids

    producer_ind = next(i for i in indicators if i.indicator_id == "PDF_METADATA_PRODUCER_ANOMALY")
    assert producer_ind.score >= 0.80
    tools = producer_ind.evidence.metadata.get("detected_editing_tools", [])
    assert any("canva" in str(t).lower() for t in tools)
    assert "indicator for review" in producer_ind.human_readable_reason.lower()
    assert "verdict" not in producer_ind.human_readable_reason.lower()
    assert "fraud" not in producer_ind.human_readable_reason.lower()


# ============================================================================
# CHECK 2: FONT INCONSISTENCY INSIDE REGION
# ============================================================================

def test_check2_font_inconsistency_in_region():
    """Validates detection of spliced font in student intake number with bounding box and visual overlay."""
    font_path = SAMPLE_DIR / "gt_font_inconsistency.pdf"
    assert font_path.exists(), f"Sample not found: {font_path}"

    indicators = document_forensics_engine.check_font_inconsistency(font_path, doc_id="font_test")
    assert len(indicators) >= 1

    font_ind = indicators[0]
    assert font_ind.indicator_id == "FONT_INCONSISTENCY_IN_REGION"
    assert font_ind.score >= 0.75
    assert font_ind.evidence.page == 1
    assert font_ind.evidence.bounding_box is not None
    assert len(font_ind.evidence.bounding_box) == 4

    # Verify visual heatmap/overlay exists on disk
    if font_ind.evidence.heatmap_image_path:
        assert Path(font_ind.evidence.heatmap_image_path).exists()

    meta = font_ind.evidence.metadata
    assert meta.get("anomalous_token") == "750"
    assert "times" in meta.get("anomalous_font", "").lower()
    assert "helv" in meta.get("dominant_font", "").lower()
    assert "indicator for review" in font_ind.human_readable_reason.lower()


# ============================================================================
# CHECK 3: ERROR LEVEL ANALYSIS (ELA)
# ============================================================================

def test_check3_error_level_analysis_spliced_image():
    """Validates Error Level Analysis on image with localized compression discrepancy."""
    ela_path = SAMPLE_DIR / "gt_ela_tampered.jpg"
    assert ela_path.exists(), f"Sample not found: {ela_path}"

    indicators = document_forensics_engine.check_error_level_analysis(ela_path, doc_id="ela_test", page_num=1)
    assert len(indicators) >= 1

    ela_ind = indicators[0]
    assert ela_ind.indicator_id == "ERROR_LEVEL_ANALYSIS_DISCREPANCY"
    assert ela_ind.score >= 0.75
    assert ela_ind.evidence.bounding_box is not None
    assert len(ela_ind.evidence.bounding_box) == 4

    # Verify generated ELA heatmap image
    assert ela_ind.evidence.heatmap_image_path is not None
    assert Path(ela_ind.evidence.heatmap_image_path).exists()

    meta = ela_ind.evidence.metadata
    assert meta.get("z_score", 0) > 3.0
    assert "indicator for review" in ela_ind.human_readable_reason.lower()


# ============================================================================
# CHECK 4: COPY-MOVE DETECTION VIA ORB KEYPOINTS
# ============================================================================

def test_check4_copy_move_orb_cloned_seal():
    """Validates ORB keypoint matching and translation clustering for cloned seals."""
    cm_path = SAMPLE_DIR / "gt_copymove_tampered.jpg"
    assert cm_path.exists(), f"Sample not found: {cm_path}"

    indicators = document_forensics_engine.check_copy_move_orb(cm_path, doc_id="cm_test", page_num=1)
    assert len(indicators) >= 1

    cm_ind = indicators[0]
    assert cm_ind.indicator_id == "COPY_MOVE_CLONE_DETECTED"
    assert cm_ind.score >= 0.80
    assert cm_ind.evidence.bounding_box is not None

    meta = cm_ind.evidence.metadata
    assert meta.get("matching_pairs_count", 0) >= 18
    assert "translation_vector" in meta

    # Verify visualization overlay exists
    assert cm_ind.evidence.heatmap_image_path is not None
    assert Path(cm_ind.evidence.heatmap_image_path).exists()
    assert "indicator for review" in cm_ind.human_readable_reason.lower()


# ============================================================================
# CHECK 5: QR-ENCODED REFERENCE VS OCR REFERENCE MATCH
# ============================================================================

def test_check5_qr_ocr_reference_mismatch():
    """Validates detection of verification QR code pointing to conflicting certificate reference."""
    qr_path = SAMPLE_DIR / "gt_qr_reference_mismatch.pdf"
    assert qr_path.exists(), f"Sample not found: {qr_path}"

    indicators = document_forensics_engine.check_qr_ocr_reference_match(
        qr_path,
        printed_reference_hint="FIR/2025/98354",
        doc_id="qr_test"
    )
    assert len(indicators) == 1

    qr_ind = indicators[0]
    assert qr_ind.indicator_id == "QR_OCR_REFERENCE_MISMATCH"
    assert qr_ind.score == 1.0
    assert qr_ind.severity == "CRITICAL"
    assert qr_ind.evidence.bounding_box is not None

    meta = qr_ind.evidence.metadata
    assert "FIR/2021/11094" in meta.get("qr_extracted_reference", "")
    assert "FIR/2025/98354" in meta.get("printed_extracted_reference", "")
    assert "indicator for review" in qr_ind.human_readable_reason.lower()


# ============================================================================
# NEGATIVE CONTROLS: CLEAN AUTHENTIC DOCUMENTS
# ============================================================================

def test_negative_controls_clean_authentic_documents():
    """Validates that clean, untampered certificates do not trigger review recommendations at standard threshold."""
    clean_pdf = SAMPLE_DIR / "gt_clean_authentic_affidavit.pdf"
    clean_img = SAMPLE_DIR / "gt_clean_authentic_scan.jpg"
    clean_nba = SAMPLE_DIR / "gt_clean_nba_certificate.pdf"

    for path in [clean_pdf, clean_img, clean_nba]:
        assert path.exists(), f"Missing clean sample: {path}"
        result = document_forensics_engine.analyze_document(path, filename=path.name, decision_threshold=0.75)
        # Clean control should not be recommended for review at calibrated threshold 0.75
        assert not result.is_review_recommended, (
            f"Clean document {path.name} incorrectly flagged: {[i.indicator_id for i in result.indicators]}"
        )


# ============================================================================
# CALIBRATION & THRESHOLD SWEEP EVALUATION
# ============================================================================

def test_forensics_calibration_precision_recall_sweep():
    """Runs threshold calibration sweep, verifying precision, recall, and peak F1-score >= 0.90."""
    calibrator = ForensicsCalibrator()
    report = calibrator.run_calibration(threshold_min=0.10, threshold_max=0.95, step=0.05)

    assert "optimal_threshold" in report
    assert "best_f1_score" in report
    assert report["best_f1_score"] >= 0.90, f"Expected F1 >= 0.90, got {report['best_f1_score']}"

    curve = report["threshold_sweep_curve"]
    assert len(curve) > 5

    # Check that optimal point has 100% precision or high balance
    opt_point = next(p for p in curve if p["threshold"] == report["optimal_threshold"])
    assert opt_point["precision"] >= 0.90
    assert opt_point["recall"] >= 0.90

    # Verify per-check detection recall
    breakdown = report["per_check_detection_breakdown"]
    assert len(breakdown) == 5
    for chk, d in breakdown.items():
        assert d["detected_at_optimal"], f"Check {chk} missed at optimal threshold {report['optimal_threshold']}"

    # Verify report saved to disk
    assert CALIBRATION_OUTPUT_FILE.exists()


# ============================================================================
# REGULATORY WORDING COMPLIANCE AUDIT
# ============================================================================

def test_regulatory_wording_constraint_strictly_adhered():
    """
    Strictly verifies that:
    1. Every indicator explanation explicitly says 'indicator for review'.
    2. Prohibited terms ('verdict', 'fraud', 'guilty', 'forgery verdict') NEVER appear in any indicator.
    """
    prohibited_terms = ["verdict", "fraud", "guilty", "forgery verdict", "convicted"]
    sample_files = list(SAMPLE_DIR.glob("*.*"))
    assert len(sample_files) >= 5

    checked_indicators = 0
    for s_file in sample_files:
        result = document_forensics_engine.analyze_document(s_file, filename=s_file.name)
        for ind in result.indicators:
            checked_indicators += 1
            reason_lower = ind.human_readable_reason.lower()
            title_lower = ind.check_name.lower()

            # Must contain indicator wording
            assert "indicator for review" in reason_lower, (
                f"Indicator {ind.indicator_id} missing mandatory phrase 'indicator for review': {ind.human_readable_reason}"
            )

            # Must never contain prohibited words
            for term in prohibited_terms:
                assert term not in reason_lower, (
                    f"Prohibited word '{term}' found in indicator explanation: {ind.human_readable_reason}"
                )
                assert term not in title_lower, (
                    f"Prohibited word '{term}' found in check title: {ind.check_name}"
                )

    assert checked_indicators >= 5, f"Expected at least 5 indicators checked, found {checked_indicators}"


# ============================================================================
# REST API ENDPOINT INTEGRATION TESTS
# ============================================================================

def test_api_analyze_document_endpoint(test_client: TestClient):
    """Tests POST /api/v1/forensics/document/analyze using file_path."""
    sample_file = SAMPLE_DIR / "gt_metadata_anomaly.pdf"
    assert sample_file.exists()

    response = test_client.post(
        "/api/v1/forensics/document/analyze",
        data={
            "file_path": str(sample_file),
            "threshold": "0.70"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert "composite_risk_score" in data
    assert "indicators" in data
    assert len(data["indicators"]) >= 1

    # Check evidence structure
    ind = data["indicators"][0]
    assert "indicator_id" in ind
    assert "score" in ind
    assert "human_readable_reason" in ind
    assert "evidence" in ind
    assert "page" in ind["evidence"]
    assert "bounding_box" in ind["evidence"]
    assert "heatmap_image_path" in ind["evidence"]


def test_api_calibration_endpoints(test_client: TestClient):
    """Tests GET /api/v1/forensics/calibration and POST /api/v1/forensics/calibrate."""
    # GET existing calibration
    get_res = test_client.get("/api/v1/forensics/calibration")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert "optimal_threshold" in get_data
    assert "threshold_sweep_curve" in get_data

    # POST run new calibration sweep
    post_res = test_client.post("/api/v1/forensics/calibrate?min_threshold=0.20&max_threshold=0.90&step=0.10")
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert "optimal_threshold" in post_data
    assert len(post_data["threshold_sweep_curve"]) > 0
