from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from PIL import Image

from backend.app.services.forensics_engine import forensics_engine
from backend.app.services.document_forensics import (
    document_forensics_engine,
    DocumentForensicsResult
)
from backend.app.services.calibrate_forensics import (
    ForensicsCalibrator,
    CALIBRATION_OUTPUT_FILE
)

router = APIRouter(prefix="/forensics", tags=["Forensics & Photo Radar"])

@router.post("/photo-radar/scan")
def scan_photo_radar(
    phash: str = Form(..., description="Perceptual hash hex string"),
    institution_id: str = Form("INST_001", description="Current applicant institution ID")
):
    """
    Photo Reuse Radar:
    Cross-checks perceptual hash against historical infrastructure photos across all Indian institutions.
    """
    result = forensics_engine.scan_photo_reuse_radar(phash, current_institution_id=institution_id)
    return result

@router.get("/photo-radar/registry", response_model=List[Dict[str, Any]])
def list_photo_registry():
    """Lists all registered campus photos in the cross-institution perceptual hash index."""
    return forensics_engine.photo_radar_registry

@router.post("/ela")
async def run_error_level_analysis(file: UploadFile = File(...)):
    """Executes Error-Level Analysis on an uploaded image to detect localized digital tampering."""
    try:
        image = Image.open(file.file)
        ela_score, details = forensics_engine.perform_error_level_analysis(image)
        phash = forensics_engine.compute_perceptual_hash(image)
        return {
            "filename": file.filename,
            "ela_score": ela_score,
            "perceptual_hash": phash,
            "details": details
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing failed: {str(e)}")

@router.post("/document/analyze", response_model=DocumentForensicsResult)
async def analyze_document_forensics(
    file: Optional[UploadFile] = File(None),
    file_path: Optional[str] = Form(None, description="Existing workspace file path"),
    printed_reference: Optional[str] = Form(None, description="Known or OCR'd printed reference number"),
    threshold: float = Form(0.75, description="Decision threshold for scrutiny review recommendation")
):
    """
    Executes automated 5-check document forensics inspection:
    1. PDF metadata analysis (creation/mod dates, producer software anomalies, incremental updates)
    2. Font inconsistency in region
    3. Error Level Analysis (ELA) for image documents
    4. Copy-move forgery detection with ORB keypoints
    5. QR-encoded reference vs printed reference verification
    
    Returns structured JSON list of indicators for review with scores and evidence (bounding box, page, heatmap path).
    """
    try:
        if file is not None:
            content = await file.read()
            filename = file.filename or "uploaded_document.pdf"
            result = document_forensics_engine.analyze_document(
                content,
                filename=filename,
                printed_reference=printed_reference,
                decision_threshold=threshold
            )
            return result
        elif file_path:
            p = Path(file_path)
            if not p.exists():
                raise HTTPException(status_code=404, detail=f"File not found at {file_path}")
            result = document_forensics_engine.analyze_document(
                p,
                filename=p.name,
                printed_reference=printed_reference,
                decision_threshold=threshold
            )
            return result
        else:
            raise HTTPException(status_code=400, detail="Must provide either uploaded 'file' or 'file_path'")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document forensics analysis failed: {str(e)}")

@router.get("/calibration")
def get_forensics_calibration():
    """Returns the latest threshold calibration sweep results, precision/recall curve, and optimal operating point."""
    calibrator = ForensicsCalibrator()
    if not CALIBRATION_OUTPUT_FILE.exists():
        report = calibrator.run_calibration()
    else:
        import json
        with open(CALIBRATION_OUTPUT_FILE, "r", encoding="utf-8") as f:
            report = json.load(f)
    return report

@router.post("/calibrate")
def run_forensics_calibration(
    min_threshold: float = Query(0.10, ge=0.05, le=0.90),
    max_threshold: float = Query(0.95, ge=0.50, le=1.00),
    step: float = Query(0.05, ge=0.01, le=0.20)
):
    """Triggers a threshold calibration sweep across ground truth benchmark samples and returns precision/recall curves."""
    calibrator = ForensicsCalibrator()
    report = calibrator.run_calibration(
        threshold_min=min_threshold,
        threshold_max=max_threshold,
        step=step
    )
    return report

