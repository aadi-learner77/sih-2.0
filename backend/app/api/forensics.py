from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from PIL import Image
from backend.app.services.forensics_engine import forensics_engine

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
