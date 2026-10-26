import os
import shutil
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from PIL import Image
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.models import Document, Application
from backend.app.schemas.schemas import DocumentOut
from backend.app.services.ocr_engine import ocr_intelligence
from backend.app.services.forensics_engine import forensics_engine
from backend.app.services.audit_chain import AuditChainService
from backend.app.services.ingestion_pipeline import ingestion_pipeline

router = APIRouter(prefix="/documents", tags=["Documents & OCR Intelligence"])

@router.post("/ingest")
async def ingest_document_api(file: UploadFile = File(...)):
    """
    Ingestion Pipeline Endpoint (Prompt 5.1):
    Accepts PDF/Image -> converts pages -> PaddleOCR / Tesseract / Vector blocks
    -> returns doc_type, per-page OCR (lines with bounding boxes & confidence), and processing time.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")
    result = ingestion_pipeline.ingest_document(file_bytes, file.filename or "uploaded_document.pdf")
    return result

@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    application_id: int = Form(...),
    document_type: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    file_bytes = await file.read()
    file_size = len(file_bytes)
    file_hash = forensics_engine.compute_sha256(file_bytes)

    # Save to uploads directory
    safe_filename = f"{app.application_no}_{file.filename}"
    saved_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    # 1. OCR Text Extraction & Classification
    extracted_text = ocr_intelligence.extract_text_from_file(saved_path, file.filename)
    classified_type, confidence = ocr_intelligence.classify_document(extracted_text, file.filename)
    actual_type = document_type if (document_type and document_type != "Auto-Detect") else classified_type
    structured_fields = ocr_intelligence.extract_structured_fields(actual_type, extracted_text)

    # 2. Metadata Forensics
    metadata_forensics = forensics_engine.scan_metadata_integrity(file_bytes, file.filename)

    # 3. Image Forensics (ELA & Perceptual Hash for photos/scans)
    ela_score = 0.0
    phash_str = None
    if file.content_type and "image" in file.content_type:
        try:
            image_obj = Image.open(saved_path)
            phash_str = forensics_engine.compute_perceptual_hash(image_obj)
            ela_score, ela_details = forensics_engine.perform_error_level_analysis(image_obj)
            metadata_forensics["ela_details"] = ela_details
        except Exception as e:
            print(f"Image forensics failed: {e}")

    # Determine if flagged for review
    is_flagged = metadata_forensics.get("is_suspicious", False) or ela_score > 0.60
    review_tag = "DIGITAL_METADATA_ANOMALY" if is_flagged else None
    review_reason = (
        "Digital manipulation signature or high compression artifact variance detected." 
        if is_flagged else None
    )

    doc = Document(
        application_id=app.id,
        document_type=actual_type,
        filename=file.filename,
        file_path=saved_path,
        file_hash=file_hash,
        file_size_bytes=file_size,
        mime_type=file.content_type or "application/octet-stream",
        classification_confidence=confidence,
        ocr_extracted_text=extracted_text,
        structured_fields=structured_fields,
        metadata_forensics=metadata_forensics,
        ela_score=ela_score,
        phash=phash_str,
        is_flagged_for_review=is_flagged,
        review_indicator_tag=review_tag,
        review_reason=review_reason
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 4. Append to Cryptographic Audit Ledger
    AuditChainService.append_receipt(
        db=db,
        event_type="DOCUMENT_UPLOADED_AND_CLASSIFIED",
        payload={
            "document_id": doc.id,
            "filename": doc.filename,
            "file_hash": doc.file_hash,
            "classified_type": doc.document_type,
            "classification_confidence": doc.classification_confidence,
            "is_flagged": doc.is_flagged_for_review
        },
        actor_email="system@aicte-india.org",
        actor_role="SYSTEM",
        application_id=app.id
    )

    return doc

@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
