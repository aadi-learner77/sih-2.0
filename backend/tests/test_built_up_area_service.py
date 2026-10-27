"""
PyTest Test Suite for Geospatial Built-Up Area Plausibility Engine.
PRAMAAN-X Forensic & Infrastructure Verification Suite.

Tests:
1. Shapely & GeoPandas metric Azimuthal Equidistant projection and area accuracy.
2. Verified campus within-tolerance detection (COEP, VJTI, BMSCE, IIT Bombay).
3. Significant infrastructure deficit anomaly detection (claimed >> measured).
4. Significant infrastructure excess anomaly detection (measured >> claimed).
5. Zero building footprints / vacant parcel detection.
6. Direct custom GeoDataFrame and Shapely Polygon query.
7. Configurable search radius and asymmetric tolerance bands.
8. Multi-story building floor multiplier estimation.
9. Dict-like subscripting and full JSON model serialization.
10. Strict adherence to PRAMAAN-X non-punitive decision-support wording policy.
11. Input boundary validation (invalid coordinates, negative inputs).
12. FastAPI REST API endpoint POST /api/v1/forensics/geospatial/built-up-plausibility.
"""

import pytest
import geopandas as gpd
from shapely.geometry import Point, box, Polygon
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.forensics import router as forensics_router
from backend.app.services.built_up_area_service import (
    verify_built_up_area_footprint,
    BuiltUpAreaVerificationResult,
    BuiltUpAreaNumbersUsed,
    ToleranceBand,
    REGULATORY_CAVEAT
)
from backend.app.services.evaluate_built_up_area import (
    BuiltUpAreaEvaluator,
    BENCHMARK_CASES
)

# Set up test FastAPI client
app_test = FastAPI()
app_test.include_router(forensics_router, prefix="/api/v1")


@pytest.fixture(scope="module")
def client():
    return TestClient(app_test)


# ============================================================================
# 1. SHAPELY & GEOPANDAS METRIC REPROJECTION & AREA ACCURACY
# ============================================================================

def test_geopandas_and_shapely_metric_area_accuracy():
    """
    Verifies that reprojecting a WGS84 polygon to an Azimuthal Equidistant projection
    yields sub-millimetric area accuracy in square meters (m²).
    """
    center_lat, center_lon = 18.5293, 73.8565
    aeqd_crs = f"+proj=aeqd +lat_0={center_lat} +lon_0={center_lon} +datum=WGS84 +units=m"

    # Create a 50m x 40m rectangular polygon in metric projection (2,000 m²)
    known_area = 50.0 * 40.0 # 2,000.0 m²
    metric_box = box(-25.0, -20.0, 25.0, 20.0)

    # Convert to WGS84
    gdf_metric = gpd.GeoDataFrame(geometry=[metric_box], crs=aeqd_crs)
    gdf_wgs84 = gdf_metric.to_crs("EPSG:4326")

    # Reproject back to metric CRS and calculate area
    gdf_reprojected = gdf_wgs84.to_crs(aeqd_crs)
    calculated_area = float(gdf_reprojected.geometry.iloc[0].area)

    # Tolerance within 0.001 m²
    assert abs(calculated_area - known_area) < 0.001


# ============================================================================
# 2. WITHIN-TOLERANCE CAMPUS PLAUSIBILITY TESTS
# ============================================================================

def test_coep_pune_built_up_area_within_tolerance():
    """Verifies that COEP campus (6,042.4 m² claimed) matches detected footprint within ±20%."""
    res = verify_built_up_area_footprint(
        latitude=18.5293,
        longitude=73.8565,
        claimed_built_up_area=6042.4,
        radius_meters=350.0,
        tolerance_pct=20.0
    )

    assert isinstance(res, BuiltUpAreaVerificationResult)
    assert res.status == "WITHIN_TOLERANCE"
    assert res.is_within_tolerance is True
    assert res.review_recommended is False
    assert res.advisory_flag == "PLAUSIBLE_FOOTPRINT_VERIFIED"

    # Numerical audit
    nums = res.numbers_used
    assert nums.claimed_built_up_area_sqm == 6042.4
    assert nums.measured_footprint_sqm == 5980.0
    assert nums.building_count == 5
    assert nums.search_radius_meters == 350.0
    assert abs(nums.discrepancy_pct) < 2.0 # -1.03%
    assert nums.tolerance_lower_bound_sqm <= nums.measured_footprint_sqm <= nums.tolerance_upper_bound_sqm
    assert "consistent with declared educational infrastructure" in res.advisory_summary


def test_vjti_mumbai_and_bmsce_bangalore_within_tolerance():
    """Verifies that VJTI Mumbai and BMSCE Bengaluru pass tolerance checks."""
    # VJTI
    res_vjti = verify_built_up_area_footprint(
        latitude=19.0222,
        longitude=72.8561,
        claimed_built_up_area=10699.0,
        radius_meters=350.0,
        tolerance_pct=25.0
    )
    assert res_vjti.status == "WITHIN_TOLERANCE"
    assert res_vjti.numbers_used.building_count == 4
    assert res_vjti.numbers_used.measured_footprint_sqm == 10480.0

    # BMSCE
    res_bmsce = verify_built_up_area_footprint(
        latitude=12.9416,
        longitude=77.5655,
        claimed_built_up_area=9444.8,
        radius_meters=350.0,
        tolerance_pct=20.0
    )
    assert res_bmsce.status == "WITHIN_TOLERANCE"
    assert res_bmsce.numbers_used.building_count == 4
    assert res_bmsce.numbers_used.measured_footprint_sqm == 9280.0


# ============================================================================
# 3. DEFICIT ANOMALY DETECTION (CLAIMED >> MEASURED)
# ============================================================================

def test_deficit_anomaly_detection():
    """
    Tests synthetic deficit case: applicant claims 15,000 m², but satellite
    detects only 350 m² across 1 small shed.
    """
    res = verify_built_up_area_footprint(
        latitude=26.8467,
        longitude=80.9462,
        claimed_built_up_area=15000.0,
        radius_meters=350.0,
        tolerance_pct=25.0
    )

    assert res.status == "FOOTPRINT_SIGNIFICANTLY_BELOW_CLAIM"
    assert res.is_within_tolerance is False
    assert res.review_recommended is True
    assert res.advisory_flag == "FOOTPRINT_DEFICIT_FLAGGED_FOR_REVIEW"
    assert res.numbers_used.measured_footprint_sqm == 350.0
    assert res.numbers_used.discrepancy_sqm < -10000.0
    assert res.numbers_used.discrepancy_pct < -90.0
    assert "cross-examine approved master building plan" in res.advisory_summary


# ============================================================================
# 4. EXCESS ANOMALY DETECTION (MEASURED >> CLAIMED)
# ============================================================================

def test_excess_anomaly_detection():
    """
    Tests synthetic excess case: applicant claims 2,500 m², but 14,800 m² of
    massive industrial/warehouse footprints are detected.
    """
    res = verify_built_up_area_footprint(
        latitude=22.5726,
        longitude=88.3639,
        claimed_built_up_area=2500.0,
        radius_meters=350.0,
        tolerance_pct=25.0
    )

    assert res.status == "FOOTPRINT_SIGNIFICANTLY_EXCEEDS_CLAIM"
    assert res.is_within_tolerance is False
    assert res.review_recommended is True
    assert res.advisory_flag == "FOOTPRINT_EXCESS_FLAGGED_FOR_REVIEW"
    assert res.numbers_used.measured_footprint_sqm == 14800.0
    assert res.numbers_used.discrepancy_pct > 400.0
    assert "adjacent institutional structures" in res.advisory_summary


# ============================================================================
# 5. ZERO BUILDINGS / EMPTY PARCEL DETECTION
# ============================================================================

def test_zero_buildings_detected_site():
    """Tests case where coordinates point to open agricultural parcel with 0 polygons."""
    res = verify_built_up_area_footprint(
        latitude=27.1751,
        longitude=78.0421,
        claimed_built_up_area=8000.0,
        radius_meters=350.0,
        tolerance_pct=20.0
    )

    assert res.status == "NO_BUILDINGS_DETECTED"
    assert res.is_within_tolerance is False
    assert res.review_recommended is True
    assert res.advisory_flag == "ZERO_FOOTPRINT_FLAGGED_FOR_REVIEW"
    assert res.numbers_used.building_count == 0
    assert res.numbers_used.measured_footprint_sqm == 0.0
    assert "verify GPS coordinate accuracy" in res.advisory_summary


# ============================================================================
# 6. DIRECT IN-MEMORY GEODATAFRAME SUPPORT
# ============================================================================

def test_custom_in_memory_geodataframe_query():
    """Verifies that the function accepts an arbitrary caller-provided GeoDataFrame."""
    test_lat, test_lon = 20.0, 75.0
    aeqd_crs = f"+proj=aeqd +lat_0={test_lat} +lon_0={test_lon} +datum=WGS84 +units=m"

    # Create 2 custom polygons: 1,000 m² and 2,500 m²
    box1 = box(10, 10, 60, 30)   # 50 x 20 = 1000 m²
    box2 = box(-70, -50, -20, 0) # 50 x 50 = 2500 m²

    gdf_custom = gpd.GeoDataFrame({
        "id": ["POLY_A", "POLY_B"],
        "name": ["Custom Block A", "Custom Block B"],
        "levels": [2, 3],
        "building_type": ["academic", "lab"],
        "geometry": [box1, box2]
    }, crs=aeqd_crs).to_crs("EPSG:4326")

    # Query with claimed area of 3,500 m²
    res = verify_built_up_area_footprint(
        latitude=test_lat,
        longitude=test_lon,
        claimed_built_up_area=3500.0,
        radius_meters=300.0,
        tolerance_pct=10.0,
        gdf=gdf_custom
    )

    assert res.status == "WITHIN_TOLERANCE"
    assert res.numbers_used.building_count == 2
    assert abs(res.numbers_used.measured_footprint_sqm - 3500.0) < 0.1
    assert res.numbers_used.discrepancy_sqm == 0.0


# ============================================================================
# 7. SEARCH RADIUS & ASYMMETRIC TOLERANCE BANDS
# ============================================================================

def test_search_radius_pruning():
    """Verifies that shrinking search radius filters out distant buildings."""
    # At COEP, closest building polygon boundary starts at ~18.9m, next at ~47m, and 5th at ~80m.
    # Searching with radius = 25m captures only the 1 closest building
    res_tight = verify_built_up_area_footprint(
        latitude=18.5293,
        longitude=73.8565,
        claimed_built_up_area=1850.0,
        radius_meters=25.0,
        tolerance_pct=20.0
    )
    assert res_tight.numbers_used.building_count == 1
    assert res_tight.numbers_used.measured_footprint_sqm == 1850.0

    # Expanding search radius to 350m captures all 5 campus buildings
    res_wide = verify_built_up_area_footprint(
        latitude=18.5293,
        longitude=73.8565,
        claimed_built_up_area=6042.4,
        radius_meters=350.0
    )
    assert res_wide.numbers_used.building_count == 5
    assert res_wide.numbers_used.measured_footprint_sqm == 5980.0



def test_asymmetric_tolerance_band():
    """Verifies asymmetric lower and upper tolerance percentage bounds."""
    res = verify_built_up_area_footprint(
        latitude=18.5293,
        longitude=73.8565,
        claimed_built_up_area=6000.0,
        radius_meters=350.0,
        tolerance_lower_pct=5.0,   # Lower bound: 6000 * 0.95 = 5700.0
        tolerance_upper_pct=50.0  # Upper bound: 6000 * 1.50 = 9000.0
    )

    assert res.tolerance_band.lower_pct == 5.0
    assert res.tolerance_band.upper_pct == 50.0
    assert res.tolerance_band.lower_bound_sqm == 5700.0
    assert res.tolerance_band.upper_bound_sqm == 9000.0
    assert res.status == "WITHIN_TOLERANCE"


# ============================================================================
# 8. MULTI-STORY FLOOR MULTIPLIER ESTIMATION
# ============================================================================

def test_multi_story_multiplier_estimation():
    """Verifies that multi-story levels estimate gross built-up floor area."""
    res = verify_built_up_area_footprint(
        latitude=18.5293,
        longitude=73.8565,
        claimed_built_up_area=6042.4,
        radius_meters=350.0,
        assume_multi_story_multiplier=3.0
    )

    # Measured ground footprint is 5,980 m²
    assert res.numbers_used.measured_footprint_sqm == 5980.0
    assert res.numbers_used.estimated_gross_built_up_sqm is not None
    assert res.numbers_used.estimated_gross_built_up_sqm > res.numbers_used.measured_footprint_sqm


# ============================================================================
# 9. DICT SUBSCRIPTING & AUDIT TRANSPARENCY
# ============================================================================

def test_dict_subscripting_and_serialization():
    """Verifies dict subscripting res['status'] and full model serialization."""
    res = verify_built_up_area_footprint(
        latitude=18.5293,
        longitude=73.8565,
        claimed_built_up_area=6042.4
    )

    assert res["status"] == "WITHIN_TOLERANCE"
    assert res["measured_footprint_sqm"] == 5980.0
    assert res["building_count"] == 5

    res_dict = res.to_dict()
    assert isinstance(res_dict, dict)
    assert "numbers_used" in res_dict
    assert "buildings" in res_dict
    assert "regulatory_caveat" in res_dict


# ============================================================================
# 10. NON-PUNITIVE REGULATORY WORDING COMPLIANCE
# ============================================================================

def test_non_punitive_regulatory_advisory_wording():
    """
    Verifies that all returned advisory text adheres to PRAMAAN-X non-punitive guidelines:
    - Never uses 'fraud', 'illegal', 'forged', 'guilty', 'verdict'.
    - Contains the mandatory regulatory caveat.
    """
    for case in BENCHMARK_CASES:
        res = verify_built_up_area_footprint(
            latitude=case["latitude"],
            longitude=case["longitude"],
            claimed_built_up_area=case["claimed_built_up_area_sqm"]
        )

        full_text = (res.advisory_summary + " " + " ".join(res.advisory_notes) + " " + res.regulatory_caveat).lower()
        forbidden_terms = ["fraud", "illegal", "criminal", "forged", "guilty", "scam", "penalty"]
        for term in forbidden_terms:
            assert term not in full_text, f"Forbidden punitive term '{term}' found in output!"

        assert "decision-support" in res.regulatory_caveat.lower()
        assert "does not constitute a punitive finding" in res.regulatory_caveat.lower()


# ============================================================================
# 11. INPUT VALIDATION ERRORS
# ============================================================================

def test_input_validation_errors():
    """Verifies boundary errors for invalid latitude, longitude, and negative areas."""
    with pytest.raises(ValueError, match="Invalid latitude"):
        verify_built_up_area_footprint(latitude=120.0, longitude=73.0, claimed_built_up_area=5000)

    with pytest.raises(ValueError, match="Invalid longitude"):
        verify_built_up_area_footprint(latitude=20.0, longitude=250.0, claimed_built_up_area=5000)

    with pytest.raises(ValueError, match="Claimed built-up area must be positive"):
        verify_built_up_area_footprint(latitude=20.0, longitude=73.0, claimed_built_up_area=-100)

    with pytest.raises(ValueError, match="Search radius must be positive"):
        verify_built_up_area_footprint(latitude=20.0, longitude=73.0, claimed_built_up_area=5000, radius_meters=0)


# ============================================================================
# 12. FASTAPI REST API ENDPOINT TEST
# ============================================================================

def test_fastapi_built_up_plausibility_endpoint(client):
    """
    Verifies FastAPI endpoint POST /api/v1/forensics/geospatial/built-up-plausibility.
    """
    response = client.post(
        "/api/v1/forensics/geospatial/built-up-plausibility",
        data={
            "latitude": 18.5293,
            "longitude": 73.8565,
            "claimed_built_up_area": 6042.4,
            "radius_meters": 350.0,
            "tolerance_pct": 20.0,
            "institution_id": "INST_001"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "WITHIN_TOLERANCE"
    assert data["is_within_tolerance"] is True
    assert data["numbers_used"]["measured_footprint_sqm"] == 5980.0
    assert data["numbers_used"]["claimed_built_up_area_sqm"] == 6042.4
    assert len(data["buildings"]) == 5
