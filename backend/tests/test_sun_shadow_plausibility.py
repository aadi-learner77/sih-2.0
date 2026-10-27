"""
PyTest Test Suite for Sun-Shadow Plausibility Engine (PRAMAAN-X Forensics Suite):
Tests:
1. Solar ephemeris computation via pvlib (azimuth, elevation, anti-solar expected shadow).
2. Physical feasibility & nighttime detection (solar elevation < 0°).
3. Scene classification & mandatory indoor skipping per regulatory advisory protocol.
4. Edge/gradient analysis for shadow direction estimation.
5. Consistent vs spoofed photo discrimination.
6. Overcast diffuse scene handling.
7. Mandatory advisory caveat inclusion across all outputs.
8. FastAPI REST endpoint POST /api/v1/forensics/photo/sun-shadow-plausibility.
"""

import io
from pathlib import Path
import pytest
from PIL import Image
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.forensics import router as forensics_router
from backend.app.services.sun_shadow_service import (
    sun_shadow_service,
    SunShadowPlausibilityResult,
    SunPositionResult,
    ADVISORY_CAVEAT
)
from backend.app.services.evaluate_sun_shadow_plausibility import (
    SunShadowPlausibilityEvaluator,
    BENCHMARK_DIR,
    create_outdoor_benchmark_image,
    create_indoor_benchmark_image
)

app_under_test = FastAPI()
app_under_test.include_router(forensics_router, prefix="/api/v1")


@pytest.fixture(scope="module")
def client():
    return TestClient(app_under_test)


@pytest.fixture(scope="module")
def evaluator():
    return SunShadowPlausibilityEvaluator()


# ============================================================================
# 1. SOLAR POSITION COMPUTATION VIA PVLIB
# ============================================================================

def test_pvlib_solar_ephemeris_delhi_morning():
    """Verifies pvlib solar position calculations for New Delhi Summer Solstice morning."""
    sol = sun_shadow_service.compute_sun_position(
        latitude=28.5447,
        longitude=77.1558,
        timestamp="2026-06-21T09:15:00+05:30"
    )
    assert isinstance(sol, SunPositionResult)
    # Sun is in East-North-East (~85.7°) at 09:15 IST
    assert 80.0 <= sol.azimuth_deg <= 92.0
    # Sun is well above horizon (~47.7°)
    assert 40.0 <= sol.elevation_deg <= 55.0
    assert sol.is_sun_above_horizon is True
    # Theoretical anti-solar shadow points to West-South-West (~265.7°)
    assert 260.0 <= sol.expected_shadow_azimuth_deg <= 272.0
    assert abs(sol.expected_shadow_azimuth_deg - ((sol.azimuth_deg + 180.0) % 360.0)) < 0.01


def test_pvlib_solar_ephemeris_mumbai_afternoon():
    """Verifies pvlib solar position calculations for Mumbai late afternoon."""
    sol = sun_shadow_service.compute_sun_position(
        latitude=19.1334,
        longitude=72.9133,
        timestamp="2026-03-15T16:30:00+05:30"
    )
    # Afternoon sun in West-South-West (~255.2°)
    assert 250.0 <= sol.azimuth_deg <= 260.0
    # Elevation ~31.4°
    assert 25.0 <= sol.elevation_deg <= 38.0
    # Shadow points East-North-East (~75.2°)
    assert 70.0 <= sol.expected_shadow_azimuth_deg <= 80.0


# ============================================================================
# 2. NIGHTTIME DETECTION & SOLAR DEPRESSION
# ============================================================================

def test_nighttime_rejection():
    """Verifies that claimed daytime outdoor photos with night timestamps are flagged."""
    test_img = Image.new("RGB", (300, 200), color=(200, 200, 200))
    res = sun_shadow_service.evaluate_plausibility(
        image_input=test_img,
        claimed_gps={"latitude": 28.5447, "longitude": 77.1558},
        claimed_timestamp="2026-06-21T23:45:00+05:30",
        camera_heading=0.0
    )
    assert res.status == "SUN_BELOW_HORIZON"
    assert res.plausibility_score == 0.0
    assert res.sun_position.elevation_deg < -20.0
    assert "below the horizon" in res.human_readable_summary


# ============================================================================
# 3. INDOOR SCENE CLASSIFICATION & ADVISORY SKIP
# ============================================================================

def test_indoor_scene_skipping():
    """Verifies that indoor photos are automatically skipped with advisory notice and null score."""
    indoor_img = create_indoor_benchmark_image("test_indoor_fixture.jpg")
    res = sun_shadow_service.evaluate_plausibility(
        image_input=indoor_img,
        claimed_gps={"latitude": 12.9716, "longitude": 77.5946},
        claimed_timestamp="2026-05-10T11:30:00+05:30",
        photo_category="computer_lab"
    )
    assert res.status == "SKIPPED_INDOOR"
    assert res.plausibility_score is None
    assert res.scene_classification.is_indoor is True
    assert "Indoor" in res.human_readable_summary
    assert "ADVISORY" in res.caveat


# ============================================================================
# 4. EDGE & GRADIENT SHADOW DIRECTION ESTIMATION
# ============================================================================

def test_edge_gradient_direction_accuracy():
    """Verifies edge and gradient direction estimation accuracy against ground truth."""
    # Delhi morning photo: expected shadow = 265.69°, camera heading = 0.0°
    delhi_img = create_outdoor_benchmark_image(
        filename="test_delhi_fixture.jpg",
        shadow_azimuth_deg=265.69,
        camera_heading_deg=0.0
    )
    res = sun_shadow_service.evaluate_plausibility(
        image_input=delhi_img,
        claimed_gps={"latitude": 28.5447, "longitude": 77.1558},
        claimed_timestamp="2026-06-21T09:15:00+05:30",
        camera_heading=0.0
    )
    assert res.status == "PLAUSIBLE"
    assert res.plausibility_score is not None and res.plausibility_score >= 0.90
    assert res.angular_discrepancy_deg is not None and res.angular_discrepancy_deg < 5.0
    assert res.estimated_shadow.directional_coherence > 0.40


# ============================================================================
# 5. CONSISTENT VS MISMATCHED DISCRIMINATION
# ============================================================================

def test_spoofed_timestamp_detection():
    """Verifies that a photo with afternoon shadows claimed at morning time is flagged as mismatch."""
    # Create photo with afternoon shadow (175.0° / South), but claim morning 09:15 (expected 265.7°)
    spoofed_img = create_outdoor_benchmark_image(
        filename="test_spoofed_fixture.jpg",
        shadow_azimuth_deg=175.0,
        camera_heading_deg=0.0
    )
    res = sun_shadow_service.evaluate_plausibility(
        image_input=spoofed_img,
        claimed_gps={"latitude": 28.5447, "longitude": 77.1558},
        claimed_timestamp="2026-06-21T09:15:00+05:30",
        camera_heading=0.0
    )
    assert res.status == "SUSPICIOUS_MISMATCH"
    assert res.plausibility_score is not None and res.plausibility_score <= 0.25
    assert res.angular_discrepancy_deg is not None and res.angular_discrepancy_deg > 70.0
    assert "POTENTIAL_MISMATCH" in res.advisory_indicator or "Mismatched" in res.human_readable_summary


# ============================================================================
# 6. OVERCAST DIFFUSE LIGHTING EXEMPTION
# ============================================================================

def test_overcast_diffuse_skipping():
    """Verifies that outdoor overcast/diffuse lighting scenes without sharp shadows are skipped."""
    overcast_img = create_outdoor_benchmark_image(
        filename="test_overcast_fixture.jpg",
        shadow_azimuth_deg=0.0,
        camera_heading_deg=0.0,
        is_overcast=True
    )
    res = sun_shadow_service.evaluate_plausibility(
        image_input=overcast_img,
        claimed_gps={"latitude": 12.9915, "longitude": 80.2337},
        claimed_timestamp="2026-11-15T12:45:00+05:30",
        camera_heading=0.0
    )
    assert res.status in ("SKIPPED_DIFFUSE_NO_SHADOWS", "SKIPPED_INDOOR")
    assert res.plausibility_score is None


# ============================================================================
# 7. MANDATORY ADVISORY CAVEAT COMPLIANCE
# ============================================================================

def test_mandatory_advisory_caveat():
    """Verifies that every response strictly contains the prominent decision-support caveat."""
    indoor_img = create_indoor_benchmark_image("test_caveat.jpg")
    res = sun_shadow_service.evaluate_plausibility(
        image_input=indoor_img,
        claimed_gps={"latitude": 28.5447, "longitude": 77.1558},
        claimed_timestamp="2026-06-21T09:15:00+05:30",
        photo_category="central_library"
    )
    assert res.caveat == ADVISORY_CAVEAT
    assert "ADVISORY INDICATOR ONLY" in res.caveat
    assert "decision-support" in res.caveat


# ============================================================================
# 8. REST API ENDPOINT INTEGRATION
# ============================================================================

def test_api_sun_shadow_plausibility_file_upload(client):
    """Tests POST /api/v1/forensics/photo/sun-shadow-plausibility with file upload."""
    # Create test image in memory
    img = Image.new("RGB", (400, 300), color=(140, 135, 130))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/api/v1/forensics/photo/sun-shadow-plausibility",
        files={"file": ("test_room.jpg", buf, "image/jpeg")},
        data={
            "latitude": "28.5447",
            "longitude": "77.1558",
            "timestamp": "2026-06-21T09:15:00+05:30",
            "photo_category": "smart_classroom",
            "is_indoor": "true"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SKIPPED_INDOOR"
    assert data["plausibility_score"] is None
    assert "ADVISORY INDICATOR ONLY" in data["caveat"]
    assert "sun_position" in data
    assert data["sun_position"]["azimuth_deg"] > 0


def test_api_sun_shadow_plausibility_file_path(client):
    """Tests POST /api/v1/forensics/photo/sun-shadow-plausibility with existing workspace path."""
    benchmark_path = BENCHMARK_DIR / "delhi_campus_morning_valid.jpg"
    assert benchmark_path.exists()

    response = client.post(
        "/api/v1/forensics/photo/sun-shadow-plausibility",
        data={
            "file_path": str(benchmark_path),
            "latitude": "28.5447",
            "longitude": "77.1558",
            "timestamp": "2026-06-21T09:15:00+05:30",
            "camera_heading": "0.0"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PLAUSIBLE"
    assert data["plausibility_score"] is not None and data["plausibility_score"] >= 0.85
    assert data["angular_discrepancy_deg"] is not None and data["angular_discrepancy_deg"] < 10.0
    assert "caveat" in data
