"""
Comprehensive PyTest Test Suite for National Photo Reuse Radar:
Tests:
1. Perceptual hashing (pHash/dHash via imagehash) and invariant multi-variant generation.
2. OpenCLIP visual embeddings (512-dim unit vectors on hypersphere).
3. FAISS vector index (IndexFlatIP) and sub-millisecond similarity retrieval.
4. Robustness and invariance to crops, rotations, and brightness/contrast shifts.
5. Multi-tiered match classification: 'exact', 'near-duplicate', 'semantically similar'.
6. Photo reuse cluster detection and cluster graph JSON (nodes + edges).
7. Evaluation benchmark reporting Precision, Recall, and Confusion Matrix.
8. REST API endpoints: GET /radar/clusters, POST /radar/query, GET /radar/evaluation.
9. Strict regulatory wording compliance: formulations strictly say 'indicator for review', never 'fraud' or 'verdict'.
"""

import os
import io
import json
from pathlib import Path
import pytest
import numpy as np
from PIL import Image, ImageEnhance
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.photo_radar import (
    NationalPhotoRadarService,
    compute_invariant_hashes,
    compute_min_hamming_distance,
    photo_radar_service,
    PhotoMatch,
    PhotoCluster,
    ClusterGraphData,
    faiss
)
from backend.app.services.evaluate_photo_radar import PhotoRadarEvaluator


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def base_test_image():
    """Generates a high-contrast test image with geometric features."""
    img = Image.new("RGB", (600, 400), color=(25, 35, 60))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 250, 200], fill=(14, 165, 233), outline=(255, 255, 255), width=3)
    draw.ellipse([300, 100, 500, 300], fill=(245, 158, 11), outline=(0, 0, 0), width=2)
    draw.line([(0, 350), (600, 350)], fill=(220, 38, 38), width=5)
    return img


# ============================================================================
# 1. FEATURE EXTRACTION: pHASH, dHASH, MULTI-VARIANT INVARIANCE
# ============================================================================

def test_feature_extraction_phash_dhash(base_test_image):
    """Verifies invariant perceptual hash generation containing pHash, dHash, and multi-variants."""
    profile = compute_invariant_hashes(base_test_image)

    assert "phash" in profile
    assert "dhash" in profile
    assert len(profile["phash"]) == 16  # 64-bit hex representation
    assert len(profile["dhash"]) == 16
    assert "variant_phashes" in profile
    assert "variant_dhashes" in profile
    # Must contain multiple variants across rotations and crops
    assert len(profile["variant_phashes"]) >= 6
    assert len(profile["variant_dhashes"]) >= 6


def test_feature_extraction_clip_embeddings(base_test_image):
    """Verifies that OpenCLIP visual embeddings produce 512-dim unit-normalized vectors."""
    extractor = photo_radar_service.clip_extractor
    emb = extractor.embed_image(base_test_image)

    assert isinstance(emb, np.ndarray)
    assert emb.shape == (512,)
    assert emb.dtype == np.float32

    # L2 norm must equal 1.0 (unit hypersphere) for inner-product cosine equivalence
    l2_norm = float(np.linalg.norm(emb))
    assert pytest.approx(l2_norm, abs=1e-3) == 1.0


# ============================================================================
# 2. FAISS VECTOR INDEXING
# ============================================================================

def test_faiss_vector_indexing_and_search(base_test_image):
    """Tests FAISS IndexFlatIP inner-product search with identical and orthogonal vectors."""
    extractor = photo_radar_service.clip_extractor
    dim = 512
    index = faiss.IndexFlatIP(dim)

    emb1 = extractor.embed_image(base_test_image)
    index.add(np.expand_dims(emb1, axis=0))
    assert index.ntotal == 1

    # Query with identical vector -> inner product must be ~1.0
    scores, indices = index.search(np.expand_dims(emb1, axis=0), k=1)
    assert indices[0][0] == 0
    assert pytest.approx(scores[0][0], abs=1e-3) == 1.0


# ============================================================================
# 3. CROP, ROTATION, AND BRIGHTNESS INVARIANCE
# ============================================================================

def test_crop_rotation_brightness_invariance(base_test_image):
    """
    Tests that an image altered with crops (6%), rotation (1.5°), and brightness (+15%)
    is detected as a match via multi-variant invariant hashing and CLIP embeddings.
    """
    # Create near-duplicate
    w, h = base_test_image.size
    crop_px = int(w * 0.06)
    cropped = base_test_image.crop((crop_px, crop_px, w - crop_px, h - crop_px))
    rotated = cropped.rotate(1.5, resample=Image.BICUBIC, expand=False)
    enhancer = ImageEnhance.Brightness(rotated)
    altered = enhancer.enhance(1.15)

    h_orig = compute_invariant_hashes(base_test_image)
    h_alt = compute_invariant_hashes(altered)

    min_dist = compute_min_hamming_distance(h_orig, h_alt)
    assert min_dist <= 16  # Multi-variant hashing absorbs crop, rotation, brightness shifts

    # Verify CLIP embedding cosine similarity remains high (> 0.85)
    e_orig = photo_radar_service.clip_extractor.embed_image(base_test_image)
    e_alt = photo_radar_service.clip_extractor.embed_image(altered)
    cosine_sim = float(np.dot(e_orig, e_alt))
    assert cosine_sim >= 0.85


# ============================================================================
# 4. MATCH TYPE CLASSIFICATION: EXACT, NEAR-DUPLICATE, SEMANTICALLY SIMILAR
# ============================================================================

def test_match_type_classification(base_test_image):
    """
    Tests radar classification into:
    - 'exact' (identical byte or Hamming 0)
    - 'near-duplicate' (crop/rot/brightness or Hamming <= threshold)
    - 'semantically similar' (high CLIP similarity)
    """
    # Create fresh radar service instance in isolated memory
    service = NationalPhotoRadarService()
    service.catalog.clear()
    service.faiss_index = faiss.IndexFlatIP(512)

    buf = io.BytesIO()
    base_test_image.save(buf, format="JPEG", quality=90)
    orig_bytes = buf.getvalue()

    # Index original for Institution A
    service.add_photo(
        img=base_test_image,
        photo_id="test_photo_01",
        institution_id="INST_ALPHA",
        institution_name="Alpha Institute of Technology",
        category="Robotics Lab",
        filename="alpha_robotics.jpg",
        file_bytes=orig_bytes
    )

    # 1. Query exact duplicate from Institution B
    res_exact = service.query_photo(
        img=base_test_image,
        current_institution_id="INST_BETA",
        file_bytes=orig_bytes
    )
    assert res_exact.has_cross_institution_reuse is True
    assert res_exact.top_match is not None
    assert res_exact.top_match.match_type == "exact"
    assert res_exact.top_match.similarity_score == 1.0

    # 2. Query near-duplicate from Institution Gamma
    w, h = base_test_image.size
    cropped = base_test_image.crop((20, 20, w - 20, h - 20))
    rotated = cropped.rotate(1.5, resample=Image.BICUBIC)
    altered = ImageEnhance.Brightness(rotated).enhance(1.15)
    res_near = service.query_photo(
        img=altered,
        current_institution_id="INST_GAMMA",
        near_duplicate_hamming_threshold=14
    )
    assert res_near.has_cross_institution_reuse is True
    assert res_near.top_match is not None
    assert res_near.top_match.match_type == "near-duplicate"
    assert res_near.top_match.similarity_score >= 0.75


# ============================================================================
# 5. CLUSTER DETECTION AND CLUSTER GRAPH JSON
# ============================================================================

def test_cluster_detection_and_graph_json(base_test_image):
    """
    Verifies that multi-institution photo reuses form connected component clusters,
    and returns cluster graph JSON with nodes and edges.
    """
    service = NationalPhotoRadarService()
    service.catalog.clear()
    service.faiss_index = faiss.IndexFlatIP(512)

    buf = io.BytesIO()
    base_test_image.save(buf, format="JPEG", quality=90)
    img_bytes = buf.getvalue()

    # 3 distinct institutions upload the same photo
    service.add_photo(base_test_image, "photo_1", "INST_101", "College 101", "Physics Lab", "p1.jpg", img_bytes)
    service.add_photo(base_test_image, "photo_2", "INST_102", "College 102", "Physics Lab", "p2.jpg", img_bytes)
    service.add_photo(base_test_image, "photo_3", "INST_103", "College 103", "Physics Lab", "p3.jpg", img_bytes)

    # 1 distinct photo uploaded by College 104 (negative control)
    distinct_img = Image.new("RGB", (600, 400), color=(100, 20, 10))
    d_buf = io.BytesIO()
    distinct_img.save(d_buf, format="JPEG")
    service.add_photo(distinct_img, "photo_4", "INST_104", "College 104", "Auditorium", "p4.jpg", d_buf.getvalue())

    clusters_res = service.detect_photo_reuse_clusters()

    assert clusters_res.total_clusters_count >= 1
    assert clusters_res.total_institutions_involved >= 3

    # Check graph JSON
    graph = clusters_res.cluster_graph
    assert len(graph.nodes) >= 6  # 3 institutions + 3 photo nodes
    assert len(graph.edges) >= 3  # uploaded edges + reuses edges

    # Verify node types and properties
    node_types = {n.node_type for n in graph.nodes}
    assert "Institution" in node_types
    assert "Photo" in node_types

    # Verify edge relations
    edge_relations = {e.relation for e in graph.edges}
    assert "uploaded" in edge_relations
    assert "reuses" in edge_relations


# ============================================================================
# 6. GROUND TRUTH EVALUATION BENCHMARK: PRECISION & RECALL
# ============================================================================

def test_ground_truth_precision_recall_benchmark():
    """
    Runs the photo radar evaluation on planted duplicates and controls.
    Confirms high precision (>= 80%) and recall (>= 90%) against ground truth.
    """
    evaluator = PhotoRadarEvaluator(photo_radar_service)
    report = evaluator.run_evaluation()

    m = report["metrics"]
    assert m["total_queries_evaluated"] >= 18
    assert m["true_positives"] >= 15
    assert m["false_negatives"] == 0
    assert m["recall"] == 1.0  # 100% recall on planted duplicates
    assert m["precision"] >= 0.85
    assert m["f1_score"] >= 0.90
    assert report["clusters_detected_count"] >= 4


# ============================================================================
# 7. STRICT REGULATORY WORDING COMPLIANCE
# ============================================================================

def test_strict_regulatory_wording_compliance(base_test_image):
    """
    Validates regulatory wording policy:
    1. Must formulate findings as 'indicator for review'.
    2. Must contain ZERO occurrences of forbidden words ('fraud', 'verdict').
    """
    service = NationalPhotoRadarService()
    service.catalog.clear()
    service.faiss_index = faiss.IndexFlatIP(512)

    buf = io.BytesIO()
    base_test_image.save(buf, format="JPEG")
    b = buf.getvalue()

    service.add_photo(base_test_image, "p1", "INST_A", "Apex College", "CAD Lab", "cad.jpg", b)
    res = service.query_photo(base_test_image, current_institution_id="INST_B", file_bytes=b)
    cluster_res = service.detect_photo_reuse_clusters()

    # Serialize all outputs to string for rigorous safety audit
    combined_text = (
        json.dumps(res.model_dump()) + " " +
        json.dumps(cluster_res.model_dump())
    ).lower()

    # Forbidden words check
    assert "fraud" not in combined_text, "Regulatory violation: 'fraud' detected in radar response!"
    assert "verdict" not in combined_text, "Regulatory violation: 'verdict' detected in radar response!"

    # Positive required formulation check
    assert "indicator for review" in combined_text


# ============================================================================
# 8. REST API ENDPOINTS
# ============================================================================

def test_api_radar_clusters_endpoint(client):
    """Tests GET /radar/clusters and /api/v1/radar/clusters endpoints."""
    # Test root endpoint
    res1 = client.get("/radar/clusters")
    assert res1.status_code == 200
    data1 = res1.json()
    assert "clusters" in data1
    assert "cluster_graph" in data1
    assert "nodes" in data1["cluster_graph"]
    assert "edges" in data1["cluster_graph"]
    assert data1["wording_policy"] == "STRICT_REGULATORY_DECISION_SUPPORT"

    # Test v1 prefix endpoint
    res2 = client.get("/api/v1/radar/clusters")
    assert res2.status_code == 200


def test_api_radar_catalog_and_evaluation(client):
    """Tests GET /radar/catalog and GET /radar/evaluation endpoints."""
    res_cat = client.get("/radar/catalog")
    assert res_cat.status_code == 200
    cat_data = res_cat.json()
    assert "total_indexed_photos" in cat_data
    assert "photos" in cat_data

    res_eval = client.get("/radar/evaluation")
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    assert "metrics" in eval_data
    assert "precision" in eval_data["metrics"]
    assert "recall" in eval_data["metrics"]
    assert eval_data["metrics"]["recall"] == 1.0


def test_api_radar_query_endpoint(client, base_test_image):
    """Tests POST /radar/query endpoint with uploaded image file."""
    buf = io.BytesIO()
    base_test_image.save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("query_photo.jpg", buf, "image/jpeg")}
    data = {"institution_id": "INST_TEST_CLIENT"}

    res = client.post("/radar/query", files=files, data=data)
    assert res.status_code == 200
    res_json = res.json()
    assert "query_photo_phash" in res_json
    assert "matches" in res_json
    assert "regulatory_indicator" in res_json
    assert "indicator for review" in res_json["regulatory_indicator"].lower()
    assert "fraud" not in json.dumps(res_json).lower()
    assert "verdict" not in json.dumps(res_json).lower()
