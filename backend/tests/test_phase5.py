"""
PRAMAAN-X Phase 5 Test Suite:
Validates OCR, Document Classification, Field Extraction, and Application Validation Orchestration:
- Prompt 5.1: Ingestion Pipeline & Document-Type Classifier & POST /documents/ingest
- Prompt 5.2: Field Extraction Module (Schemas, Normalizers, Rules/LLM Fallback) & Benchmark Evaluator
- Prompt 5.3: Application Validation Orchestrator & POST /applications/{app_id}/validate
"""
import io
import pytest
from pathlib import Path
from datetime import date
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.models import Institution, Application, Document
from backend.app.services.ingestion_pipeline import IngestionPipeline, DocumentTypeClassifier, ingestion_pipeline
from backend.app.services.field_extraction import (
    field_extraction_engine,
    DOCUMENT_FIELD_SCHEMAS,
    normalize_date,
    normalize_name,
    normalize_number
)
from backend.app.services.evaluate_field_extraction import evaluate_all_synthetic_documents
from backend.app.services.validation_orchestrator import validation_orchestrator

client = TestClient(app)

# ---------------------------------------------------------------------------
# Prompt 5.1 Tests: Ingestion Pipeline & Classifier
# ---------------------------------------------------------------------------

def test_document_classifier_heuristics():
    """Validates Tier-1 keyword/regex heuristic classifier."""
    classifier = DocumentTypeClassifier()
    
    noc_text = "GOVERNMENT OF KARNATAKA NO OBJECTION CERTIFICATE NOC/2025/1102 Permission granted."
    doc_t, conf, method = classifier.classify(noc_text, "noc_doc.pdf")
    assert doc_t == "NOC"

    fire_text = "STATE FIRE AND EMERGENCY SERVICES CLEARANCE CERTIFICATE NOC Fire Safety inspected."
    doc_t, conf, method = classifier.classify(fire_text, "fire.pdf")
    assert doc_t == "Fire Safety Certificate"

    land_text = "SUB-REGISTRAR DEED OF CONVEYANCE SALE DEED Survey No 88/1 Extent 7.5 Acres."
    doc_t, conf, method = classifier.classify(land_text, "land.pdf")
    assert doc_t == "Land Title Deed"

    affidavit_text = "ON STAMP PAPER BEFORE ME NOTARY PUBLIC AFFIDAVIT solemnly affirm and declare."
    doc_t, conf, method = classifier.classify(affidavit_text, "affidavit.pdf")
    assert doc_t == "Affidavit"


def test_document_classifier_ml_fallback():
    """Validates Tier-2 ML (TF-IDF + Logistic Regression) fallback."""
    classifier = DocumentTypeClassifier()
    # Train on small corpus
    docs = [
        "Government clearance no objection certificate affiliation approval state department",
        "Fire and rescue station safety clearance inspection extinguishers hydrant building",
        "Sub registrar registered sale deed title land revenue survey khata partition",
        "Solemn affirmation sworn oath before notary public depose affidavit stamp paper"
    ]
    labels = ["NOC", "Fire Safety Certificate", "Land Title Deed", "Affidavit"]
    classifier.train_ml_model(docs, labels)
    
    assert classifier.is_trained is True
    # Test ambiguous text without exact title keywords
    pred = classifier.predict_ml("department approval clearance state")
    assert pred in labels


def test_ingestion_pipeline_with_sample_document():
    """Validates ingestion pipeline handling of PDF documents with per-page OCR and bboxes."""
    workspace_root = Path(__file__).resolve().parent.parent.parent
    fire_pdf = workspace_root / "generated_data" / "documents" / "INST_001" / "FIRE_INST_001.pdf"
    
    if not fire_pdf.exists():
        pytest.skip("Synthetic fire PDF not generated.")

    with open(fire_pdf, "rb") as f:
        file_bytes = f.read()

    result = ingestion_pipeline.ingest_document(file_bytes, "FIRE_INST_001.pdf")
    assert result["doc_type"] == "Fire Safety Certificate"
    assert "per_page_ocr" in result
    assert "processing_time_ms" in result
    assert len(result["per_page_ocr"]) >= 1

    # Check bounding box and confidence in lines
    first_page = result["per_page_ocr"][0]
    assert len(first_page["lines"]) > 0
    first_line = first_page["lines"][0]
    assert "text" in first_line
    assert "bounding_box" in first_line
    assert len(first_line["bounding_box"]) == 4  # [ymin, xmin, ymax, xmax]
    assert "confidence" in first_line


def test_post_documents_ingest_endpoint():
    """Validates POST /documents/ingest FastAPI endpoint."""
    workspace_root = Path(__file__).resolve().parent.parent.parent
    noc_pdf = workspace_root / "generated_data" / "documents" / "INST_001" / "NOC_INST_001.pdf"
    
    if not noc_pdf.exists():
        pytest.skip("Synthetic NOC PDF not generated.")

    with open(noc_pdf, "rb") as f:
        pdf_bytes = f.read()

    files = {"file": ("NOC_INST_001.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = client.post("/documents/ingest", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["doc_type"] == "NOC"
    assert "per_page_ocr" in data
    assert "processing_time_ms" in data
    assert len(data["per_page_ocr"]) >= 1


# ---------------------------------------------------------------------------
# Prompt 5.2 Tests: Field Extraction & Normalization
# ---------------------------------------------------------------------------

def test_field_normalization():
    """Validates Indian date, name, and numeric normalizations."""
    # Date normalizations
    assert normalize_date("25-06-2025") == "2025-06-25"
    assert normalize_date("31/03/2027") == "2027-03-31"
    assert normalize_date("15 August 2026") == "2026-08-15"
    assert normalize_date("2025.12.31") == "2025-12-31"

    # Name normalizations
    assert normalize_name("  Apex Institute of Technology, Bangalore.  ") == "Apex Institute of Technology Bangalore"
    assert normalize_name("Dr.  R.K.  Sharma   ") == "Dr R K Sharma"

    # Number normalizations
    assert normalize_number("1,25,000") == 125000.0
    assert normalize_number("7.50 acres") == 7.5
    assert normalize_number("300 seats") == 300.0


def test_field_schemas_defined():
    """Validates that all mandatory document types have defined JSON schemas."""
    expected_types = [
        "NOC", "Fire Safety Certificate", "Land Title Deed",
        "University Affiliation Order", "Building Plan Approval",
        "Affidavit", "Accreditation Certificate", "Faculty Roster"
    ]
    for doc_t in expected_types:
        assert doc_t in DOCUMENT_FIELD_SCHEMAS
        schema = DOCUMENT_FIELD_SCHEMAS[doc_t]
        assert schema.get("type") == "object"
        assert "properties" in schema
        assert "required" in schema
        assert len(schema["required"]) >= 3


def test_field_extraction_rule_and_llm_fallback():
    """Validates field extraction with schema validation and metadata."""
    sample_text = """
    GOVERNMENT OF KARNATAKA
    HIGHER EDUCATION DEPARTMENT
    NO OBJECTION CERTIFICATE
    Reference No: ED/NOC/2025/8819
    Issue Date: 15-05-2025
    Valid Until: 31-03-2027
    Institution Name: Apex Institute of Technology
    Signatory: Dr. S. K. Rao, Principal Secretary
    """
    
    ocr_pages = [{
        "page_number": 1,
        "lines": [
            {"text": "Reference No: ED/NOC/2025/8819", "bounding_box": [100, 50, 120, 300], "confidence": 0.98},
            {"text": "Valid Until: 31-03-2027", "bounding_box": [130, 50, 150, 250], "confidence": 0.96},
            {"text": "Institution Name: Apex Institute of Technology", "bounding_box": [160, 50, 180, 400], "confidence": 0.99}
        ]
    }]

    fields = field_extraction_engine.extract_fields("NOC", sample_text, ocr_pages)
    
    # Check field objects
    assert "reference_number" in fields
    assert "institution_name" in fields
    assert "validity_date" in fields

    ref_field = fields["reference_number"]
    assert ref_field.value == "ED/NOC/2025/8819"
    assert ref_field.confidence >= 0.85
    assert ref_field.source_page == 1
    assert ref_field.bounding_box is not None

    val_field = fields["validity_date"]
    assert val_field.value == "2027-03-31"  # Normalized to ISO date


def test_field_extraction_benchmark_evaluator():
    """Validates the field-level evaluation benchmark script."""
    eval_results = evaluate_all_synthetic_documents()
    assert "error" not in eval_results
    assert "per_field" in eval_results
    assert "macro_f1" in eval_results
    assert "micro_f1" in eval_results

    # Ensure Macro F1 is over 80% on synthetic ground truth
    assert eval_results["macro_f1"] >= 0.80
    assert eval_results["evaluated_documents_count"] > 0


# ---------------------------------------------------------------------------
# Prompt 5.3 Tests: Application Validation Orchestrator
# ---------------------------------------------------------------------------

def test_application_validation_orchestrator_structure():
    """Validates that validation orchestrator produces all mandated sections."""
    db = SessionLocal()
    try:
        app_record = db.query(Application).first()
        if not app_record:
            pytest.skip("No application seeded in test database.")

        report = validation_orchestrator.validate_application(db, app_record.id)

        # Check mandated sections from Prompt 5.3
        assert "application_id" in report
        assert "application_no" in report
        assert "category" in report
        assert "institution_profile" in report
        assert "missing_documents" in report
        assert "expired_documents" in report
        assert "incomplete_fields" in report
        assert "inconsistencies" in report
        assert "readiness_score" in report
        assert "readiness_explanation" in report
        assert "rectification_summary" in report
        assert "rule_findings" in report

        # Verify readiness score is within 0 to 100
        score = report["readiness_score"]
        assert 0.0 <= score <= 100.0

        # Verify institution profile DB records
        profile = report["institution_profile"]
        assert "approved_intake" in profile
        assert "built_up_area_sqm" in profile
        assert "previous_eoa_status" in profile
        assert "ter_payment_status" in profile

        # Verify rectification-allowed flag per rule finding
        for finding in report["rule_findings"]:
            assert "rectification_allowed" in finding
            assert isinstance(finding["rectification_allowed"], bool)
            assert "clause_ref" in finding
            assert "status" in finding
            assert "remediation" in finding

    finally:
        db.close()


def test_post_applications_validate_endpoint():
    """Validates POST /api/v1/applications/{app_id}/validate API endpoint."""
    db = SessionLocal()
    try:
        app_record = db.query(Application).first()
        if not app_record:
            pytest.skip("No application found to validate.")
        app_id = app_record.id
    finally:
        db.close()

    response = client.post(f"/api/v1/applications/{app_id}/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["application_id"] == app_id
    assert "missing_documents" in data
    assert "expired_documents" in data
    assert "incomplete_fields" in data
    assert "inconsistencies" in data
    assert "readiness_score" in data
    assert "readiness_explanation" in data
    assert "rule_findings" in data
