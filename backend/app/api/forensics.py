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
from backend.app.services.sun_shadow_service import (
    sun_shadow_service,
    SunShadowPlausibilityResult
)
from backend.app.services.built_up_area_service import (
    verify_built_up_area_footprint,
    BuiltUpAreaVerificationResult
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


@router.post("/photo/sun-shadow-plausibility", response_model=SunShadowPlausibilityResult)
async def check_photo_sun_shadow_plausibility(
    file: Optional[UploadFile] = File(None),
    file_path: Optional[str] = Form(None, description="Workspace image file path"),
    latitude: Optional[float] = Form(None, description="Claimed GPS latitude"),
    longitude: Optional[float] = Form(None, description="Claimed GPS longitude"),
    timestamp: Optional[str] = Form(None, description="Claimed capture timestamp (ISO format)"),
    camera_heading: Optional[float] = Form(None, description="Camera compass heading in degrees (0-360)"),
    photo_category: Optional[str] = Form(None, description="Infrastructure category (e.g. 'classroom', 'campus_exterior')"),
    is_indoor: Optional[bool] = Form(None, description="Explicit indoor flag")
):
    """
    Sun-Shadow Plausibility Verification:
    Given claimed photo GPS and timestamp, computes expected sun position via pvlib.
    Estimates dominant shadow direction in outdoor images using edge/gradient analysis.
    Returns advisory plausibility score and indicator, automatically skipping indoor photos.
    """
    try:
        if file is not None:
            content = await file.read()
            image_input = content
        elif file_path:
            p = Path(file_path)
            if not p.exists():
                raise HTTPException(status_code=404, detail=f"Image file not found at {file_path}")
            image_input = p
        else:
            raise HTTPException(status_code=400, detail="Must provide either uploaded 'file' or 'file_path'")

        claimed_gps = None
        if latitude is not None and longitude is not None:
            claimed_gps = {"latitude": latitude, "longitude": longitude}

        result = sun_shadow_service.evaluate_plausibility(
            image_input=image_input,
            claimed_gps=claimed_gps,
            claimed_timestamp=timestamp,
            camera_heading=camera_heading,
            photo_category=photo_category,
            is_indoor=is_indoor
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sun-shadow plausibility check failed: {str(e)}")


@router.post("/geospatial/built-up-plausibility", response_model=BuiltUpAreaVerificationResult)
def check_built_up_area_plausibility(
    latitude: float = Form(..., description="Campus centroid latitude (WGS84)"),
    longitude: float = Form(..., description="Campus centroid longitude (WGS84)"),
    claimed_built_up_area: float = Form(..., description="Claimed built-up area in square meters (m²)"),
    radius_meters: float = Form(350.0, description="Search radius in meters"),
    tolerance_pct: float = Form(25.0, description="Tolerance percentage band (±%)"),
    tolerance_lower_pct: Optional[float] = Form(None, description="Optional asymmetric lower tolerance %"),
    tolerance_upper_pct: Optional[float] = Form(None, description="Optional asymmetric upper tolerance %"),
    assume_multi_story_multiplier: Optional[float] = Form(None, description="Optional stories multiplier"),
    institution_id: Optional[str] = Form(None, description="Institution identifier")
):
    """
    Open Buildings / OSM Geospatial Footprint Verification:
    Queries a local copy of Open Buildings / OSM building polygons within a radius,
    sums ground footprint area, and evaluates the declared built-up area using a tolerance band.
    Returns structured advisory indicator with all numbers used.
    """
    try:
        result = verify_built_up_area_footprint(
            latitude=latitude,
            longitude=longitude,
            claimed_built_up_area=claimed_built_up_area,
            radius_meters=radius_meters,
            tolerance_pct=tolerance_pct,
            tolerance_lower_pct=tolerance_lower_pct,
            tolerance_upper_pct=tolerance_upper_pct,
            assume_multi_story_multiplier=assume_multi_story_multiplier
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Built-up area verification failed: {str(e)}")


