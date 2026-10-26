"""
National Photo Reuse Radar API Router:
Exposes endpoints for photo duplicate scanning, vector similarity search,
cross-institution reuse cluster detection, and ground truth benchmark evaluation.

Adheres strictly to the AICTE regulatory decision-support wording policy:
Formulates all findings as "indicators for review" and never uses "fraud" or "verdict".
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from PIL import Image
import json

from backend.app.services.photo_radar import (
    photo_radar_service,
    RadarQueryResponse,
    RadarClustersResponse,
    EVAL_RESULTS_FILE
)
from backend.app.services.evaluate_photo_radar import PhotoRadarEvaluator


router = APIRouter(prefix="/radar", tags=["National Photo Reuse Radar"])


@router.get("/clusters", response_model=RadarClustersResponse)
def get_photo_reuse_clusters(
    exact_hamming_threshold: int = Query(0, ge=0, le=10, description="Max Hamming distance for exact match"),
    near_duplicate_hamming_threshold: int = Query(12, ge=1, le=25, description="Max Hamming distance for near-duplicate match"),
    clip_semantic_threshold: float = Query(0.82, ge=0.5, le=1.0, description="Min CLIP cosine similarity for semantic match")
):
    """
    Groups institutions sharing the same infrastructure photo across India.
    Returns cluster detection graph JSON with nodes (Institutions, Photos) and edges (claims, reuses).
    """
    try:
        cluster_response = photo_radar_service.detect_photo_reuse_clusters(
            exact_hamming_threshold=exact_hamming_threshold,
            near_duplicate_hamming_threshold=near_duplicate_hamming_threshold,
            clip_semantic_threshold=clip_semantic_threshold
        )
        return cluster_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cluster detection failed: {str(e)}")


@router.post("/query", response_model=RadarQueryResponse)
async def query_photo_radar(
    file: Optional[UploadFile] = File(None),
    file_path: Optional[str] = Form(None, description="Local path to photo file"),
    institution_id: str = Form("INST_CURRENT", description="Current applicant institution ID"),
    exact_hamming_threshold: int = Form(0, ge=0, le=10),
    near_duplicate_hamming_threshold: int = Form(12, ge=1, le=25),
    clip_semantic_threshold: float = Form(0.82, ge=0.5, le=1.0)
):
    """
    Queries an uploaded infrastructure photo against registered campus photos across ALL institutions.
    Computes invariant perceptual hashes (pHash/dHash) and CLIP embedding (FAISS vector search).
    Handles crops, rotations, and brightness/contrast shifts.
    Categorizes matches into 'exact', 'near-duplicate', and 'semantically similar'.
    """
    try:
        if file is not None:
            file_bytes = await file.read()
            import io
            img = Image.open(io.BytesIO(file_bytes))
        elif file_path:
            p = Path(file_path)
            if not p.exists():
                raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
            with open(p, "rb") as fh:
                file_bytes = fh.read()
            img = Image.open(p)
        else:
            raise HTTPException(status_code=400, detail="Must provide either 'file' or 'file_path'")

        result = photo_radar_service.query_photo(
            img=img,
            current_institution_id=institution_id,
            file_bytes=file_bytes,
            exact_hamming_threshold=exact_hamming_threshold,
            near_duplicate_hamming_threshold=near_duplicate_hamming_threshold,
            clip_semantic_threshold=clip_semantic_threshold
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Photo radar query failed: {str(e)}")


@router.get("/evaluation")
def get_photo_radar_evaluation(run_fresh: bool = Query(False, description="Run fresh evaluation if true")):
    """
    Returns ground truth benchmark evaluation results:
    Precision, Recall, F1-Score, Confusion Matrix, and cluster breakdown on planted duplicates.
    """
    if run_fresh or not EVAL_RESULTS_FILE.exists():
        evaluator = PhotoRadarEvaluator(photo_radar_service)
        report = evaluator.run_evaluation()
        return report
    else:
        with open(EVAL_RESULTS_FILE, "r", encoding="utf-8") as fh:
            report = json.load(fh)
        return report


@router.get("/catalog")
def get_photo_radar_catalog():
    """Returns metadata for all indexed campus infrastructure photos."""
    return {
        "total_indexed_photos": len(photo_radar_service.catalog),
        "faiss_index_size": photo_radar_service.faiss_index.ntotal if photo_radar_service.faiss_index else 0,
        "photos": [
            {
                "faiss_id": p.get("faiss_id"),
                "photo_id": p.get("photo_id"),
                "institution_id": p.get("institution_id"),
                "institution_name": p.get("institution_name"),
                "category": p.get("category"),
                "filename": p.get("filename"),
                "phash": p.get("phash"),
                "dhash": p.get("dhash")
            }
            for p in photo_radar_service.catalog
        ]
    }
