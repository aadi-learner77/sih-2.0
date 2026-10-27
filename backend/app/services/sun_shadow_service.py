"""
Sun-Shadow Plausibility Engine (PRAMAAN-X Forensics Suite):
Given a photo's claimed GPS coordinates and capture timestamp:
1. Computes solar azimuth, elevation, and zenith using pvlib.
2. Evaluates nighttime / solar depression conditions (sun below horizon).
3. Classifies scene (indoor vs outdoor sunlit vs diffuse overcast) and automatically
   skips indoor images where illumination is artificial or diffuse.
4. Performs edge and gradient analysis on segmented shadow regions to estimate dominant
   shadow direction and directional coherence.
5. Maps image shadow vectors to geographic compass bearing using camera heading (EXIF or explicit).
6. Computes angular discrepancy against expected anti-solar shadow direction and calculates
   a normalized plausibility score (0.0 to 1.0).
7. Formulates all findings strictly as an advisory indicator for human reviewer guidance,
   accompanied by a mandatory advisory caveat.
"""

import sys
from unittest.mock import MagicMock

# Ensure pvlib imports cleanly on environments where h5py is not prebuilt
if "h5py" not in sys.modules:
    sys.modules["h5py"] = MagicMock()

import os
import io
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageOps, ExifTags
from scipy import ndimage
import pandas as pd
import pvlib
import pvlib.solarposition
from pydantic import BaseModel, Field


# ============================================================================
# CONSTANTS & ADVISORY STATEMENTS
# ============================================================================

ADVISORY_CAVEAT = (
    "ADVISORY INDICATOR ONLY: This sun-shadow plausibility analysis is an automated "
    "decision-support heuristic for human scrutiny officers. It does NOT provide conclusive "
    "proof of authenticity or manipulation. Results are subject to scene perspective, "
    "camera heading accuracy, terrain slope, architectural geometry, and localized reflections. "
    "Verification is automatically skipped for indoor scenes and overcast conditions."
)

INDOOR_CATEGORIES = {
    "classroom", "smart_classroom", "computer_lab", "materials_lab",
    "chemistry_lab", "physics_lab", "cad_lab", "library", "central_library",
    "auditorium", "cafeteria_hall", "seminar_hall", "indoor_sports",
    "faculty_room", "server_room", "workshop_indoor", "office"
}

DEFAULT_TIMEZONE = "Asia/Kolkata"


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class SunPositionResult(BaseModel):
    latitude: float
    longitude: float
    timestamp_iso: str
    azimuth_deg: float = Field(..., description="Solar azimuth in degrees (0°=N, 90°=E, 180°=S, 270°=W)")
    elevation_deg: float = Field(..., description="Solar elevation angle above horizon (-90° to +90°)")
    zenith_deg: float = Field(..., description="Solar zenith angle from vertical (90° - elevation)")
    expected_shadow_azimuth_deg: float = Field(..., description="Theoretical anti-solar shadow direction on flat ground")
    is_sun_above_horizon: bool
    is_golden_hour: bool


class SceneClassificationResult(BaseModel):
    is_indoor: bool
    outdoor_shadows_visible: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    scene_type: str = Field(..., description="'indoor', 'outdoor_sunlit', or 'outdoor_diffuse'")
    reason: str
    metrics: Dict[str, float] = Field(default_factory=dict)


class ShadowEstimationResult(BaseModel):
    outdoor_shadows_detected: bool
    dominant_image_angle_deg: Optional[float] = Field(
        None, description="Dominant shadow direction in ground-projected image plane (0°=forward/up, 90°=right, 180°=down, 270°=left)"
    )
    estimated_shadow_azimuth_deg: Optional[float] = Field(
        None, description="Estimated geographic azimuth of cast shadow in degrees (0°-360°)"
    )
    directional_coherence: float = Field(
        ..., ge=0.0, le=1.0, description="Resultant vector length R measuring angular concentration"
    )
    shadow_coverage_pct: float = Field(..., ge=0.0, le=100.0)
    boundary_edges_count: int
    dominant_contrast_ratio: float


class SunShadowPlausibilityResult(BaseModel):
    status: str = Field(
        ...,
        description="'PLAUSIBLE', 'QUESTIONABLE', 'SUSPICIOUS_MISMATCH', 'SKIPPED_INDOOR', 'SKIPPED_DIFFUSE_NO_SHADOWS', 'SUN_BELOW_HORIZON'"
    )
    plausibility_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Normalized plausibility index (0.0 to 1.0), None if skipped"
    )
    angular_discrepancy_deg: Optional[float] = Field(
        None, description="Absolute angular error between estimated and expected shadow azimuth"
    )
    claimed_gps: Dict[str, float]
    claimed_timestamp: str
    camera_heading_deg: Optional[float] = None
    camera_heading_source: Optional[str] = None  # 'exif', 'explicit', 'implied_from_sun', 'none'
    sun_position: SunPositionResult
    scene_classification: SceneClassificationResult
    estimated_shadow: ShadowEstimationResult
    advisory_indicator: str
    human_readable_summary: str
    caveat: str = ADVISORY_CAVEAT


# ============================================================================
# EXIF PARSER UTILITIES
# ============================================================================

def _convert_dms_to_degrees(dms_value: Any) -> Optional[float]:
    """Converts EXIF Degree-Minute-Second representation to decimal degrees."""
    if not dms_value or len(dms_value) < 3:
        return None
    try:
        def to_float(val):
            if hasattr(val, "numerator") and hasattr(val, "denominator"):
                return float(val.numerator) / float(val.denominator) if val.denominator != 0 else 0.0
            return float(val)

        d = to_float(dms_value[0])
        m = to_float(dms_value[1])
        s = to_float(dms_value[2])
        return d + (m / 60.0) + (s / 3600.0)
    except Exception:
        return None


def extract_exif_metadata(image: Image.Image) -> Dict[str, Any]:
    """
    Extracts GPS coordinates, capture timestamp, and camera heading from image EXIF tags.
    """
    metadata: Dict[str, Any] = {
        "latitude": None,
        "longitude": None,
        "timestamp": None,
        "camera_heading": None,
        "camera_heading_ref": None,
        "make": None,
        "model": None
    }

    try:
        exif_raw = image._getexif()
        if not exif_raw:
            return metadata

        exif: Dict[str, Any] = {}
        for tag_id, value in exif_raw.items():
            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
            exif[tag_name] = value

        metadata["make"] = str(exif.get("Make", "")).strip() or None
        metadata["model"] = str(exif.get("Model", "")).strip() or None

        # Capture timestamp
        date_str = exif.get("DateTimeOriginal") or exif.get("DateTime")
        if date_str:
            try:
                # Format: "YYYY:MM:DD HH:MM:SS"
                parts = str(date_str).strip().split()
                if len(parts) == 2:
                    d_part = parts[0].replace(":", "-")
                    metadata["timestamp"] = f"{d_part}T{parts[1]}"
            except Exception:
                pass

        # GPS Info
        gps_info = exif.get("GPSInfo")
        if gps_info:
            gps_tags: Dict[str, Any] = {}
            for k, v in gps_info.items():
                gps_tag_name = ExifTags.GPSTAGS.get(k, str(k))
                gps_tags[gps_tag_name] = v

            # Latitude
            lat_dms = gps_tags.get("GPSLatitude")
            lat_ref = gps_tags.get("GPSLatitudeRef", "N")
            if lat_dms:
                deg = _convert_dms_to_degrees(lat_dms)
                if deg is not None:
                    metadata["latitude"] = -deg if lat_ref == "S" else deg

            # Longitude
            lon_dms = gps_tags.get("GPSLongitude")
            lon_ref = gps_tags.get("GPSLongitudeRef", "E")
            if lon_dms:
                deg = _convert_dms_to_degrees(lon_dms)
                if deg is not None:
                    metadata["longitude"] = -deg if lon_ref == "W" else deg

            # Camera Bearing / Heading
            img_dir = gps_tags.get("GPSImgDirection")
            if img_dir is not None:
                try:
                    if hasattr(img_dir, "numerator") and hasattr(img_dir, "denominator"):
                        metadata["camera_heading"] = float(img_dir.numerator) / float(img_dir.denominator)
                    else:
                        metadata["camera_heading"] = float(img_dir)
                    metadata["camera_heading_ref"] = str(gps_tags.get("GPSImgDirectionRef", "T"))
                except Exception:
                    pass

            # GPS Timestamp fallback
            if not metadata["timestamp"] and "GPSDateStamp" in gps_tags and "GPSTimeStamp" in gps_tags:
                try:
                    date_stamp = gps_tags["GPSDateStamp"].replace(":", "-")
                    time_tuple = gps_tags["GPSTimeStamp"]
                    h = int(time_tuple[0])
                    m = int(time_tuple[1])
                    s = int(time_tuple[2])
                    metadata["timestamp"] = f"{date_stamp}T{h:02d}:{m:02d}:{s:02d}Z"
                except Exception:
                    pass

    except Exception:
        pass

    return metadata


# ============================================================================
# CORE SUN SHADOW SERVICE
# ============================================================================

class SunShadowPlausibilityService:
    """
    Evaluates physical consistency between claimed photo GPS/timestamp and visible outdoor cast shadows.
    """

    def compute_sun_position(
        self,
        latitude: float,
        longitude: float,
        timestamp: Union[datetime, str],
        altitude_m: float = 0.0,
        tz_override: Optional[str] = None
    ) -> SunPositionResult:
        """
        Computes accurate solar position (azimuth, elevation, zenith) using pvlib.
        """
        # Parse timestamp safely into a timezone-aware pandas datetime
        if isinstance(timestamp, str):
            clean_ts = timestamp.strip()
            # If naive ISO timestamp without offset, localize to default timezone
            try:
                dt = pd.to_datetime(clean_ts)
                if dt.tzinfo is None:
                    tz = tz_override or DEFAULT_TIMEZONE
                    dt = dt.tz_localize(tz)
                times = pd.DatetimeIndex([dt])
            except Exception as e:
                raise ValueError(f"Failed to parse timestamp '{timestamp}': {e}")
        elif isinstance(timestamp, datetime):
            if timestamp.tzinfo is None:
                tz = tz_override or DEFAULT_TIMEZONE
                dt = pd.to_datetime(timestamp).tz_localize(tz)
            else:
                dt = pd.to_datetime(timestamp)
            times = pd.DatetimeIndex([dt])
        else:
            raise TypeError(f"Unsupported timestamp type: {type(timestamp)}")

        # Query pvlib ephemeris
        sol = pvlib.solarposition.get_solarposition(
            time=times,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude_m
        )

        azimuth = float(sol["azimuth"].iloc[0])
        elevation = float(sol["apparent_elevation"].iloc[0])
        zenith = float(sol["apparent_zenith"].iloc[0])

        # Theoretical ground shadow direction points directly away from the sun (anti-solar)
        expected_shadow = (azimuth + 180.0) % 360.0
        is_above_horizon = elevation > 0.0
        is_golden = 0.0 <= elevation < 6.0

        return SunPositionResult(
            latitude=latitude,
            longitude=longitude,
            timestamp_iso=dt.isoformat(),
            azimuth_deg=round(azimuth, 2),
            elevation_deg=round(elevation, 2),
            zenith_deg=round(zenith, 2),
            expected_shadow_azimuth_deg=round(expected_shadow, 2),
            is_sun_above_horizon=is_above_horizon,
            is_golden_hour=is_golden
        )

    def classify_scene(
        self,
        image: Image.Image,
        category: Optional[str] = None,
        is_indoor_override: Optional[bool] = None
    ) -> SceneClassificationResult:
        """
        Detects whether an image is an indoor environment or lacks directional outdoor solar shadows.
        Indoor images are automatically flagged for advisory skip.
        """
        if is_indoor_override is True:
            return SceneClassificationResult(
                is_indoor=True,
                outdoor_shadows_visible=False,
                confidence=1.0,
                scene_type="indoor",
                reason="Explicit indoor classification specified in metadata."
            )
        elif is_indoor_override is False:
            category_indoor = False
        else:
            category_indoor = bool(category and str(category).lower().strip() in INDOOR_CATEGORIES)

        # Computer Vision Analysis
        # Ensure image is in RGB and reasonable dimensions
        img_rgb = image.convert("RGB")
        w, h = img_rgb.size
        # Resize to fixed scale for uniform statistical metrics
        scale = 400 / max(w, h)
        if scale < 1.0:
            proc_img = img_rgb.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
        else:
            proc_img = img_rgb

        arr = np.array(proc_img, dtype=np.float64)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        lum = 0.299 * r + 0.587 * g + 0.114 * b

        # 1. Dynamic Contrast in Lower Half (Ground Plane)
        ground_lum = lum[int(proc_img.height * 0.4):, :]
        p_low = float(np.percentile(ground_lum, 0.5))
        p_high = float(np.percentile(ground_lum, 95))
        contrast_ratio = (p_high + 5.0) / (p_low + 5.0)

        # 2. Chromaticity Shift (Skylight Blue Shift in Shadows)
        denom = r + g + b + 1e-5
        blue_ratio = b / denom
        shadow_thresh = p_low + 0.35 * (p_high - p_low)
        shadow_mask = (lum[int(proc_img.height * 0.4):, :] <= shadow_thresh) & (lum[int(proc_img.height * 0.4):, :] > 15)
        lit_mask = lum[int(proc_img.height * 0.4):, :] > float(np.percentile(ground_lum, 70))

        if np.sum(shadow_mask) > 50 and np.sum(lit_mask) > 50:
            mean_shadow_blue = float(np.mean(blue_ratio[int(proc_img.height * 0.4):, :][shadow_mask]))
            mean_lit_blue = float(np.mean(blue_ratio[int(proc_img.height * 0.4):, :][lit_mask]))
            sky_blue_shift = mean_shadow_blue - mean_lit_blue
        else:
            sky_blue_shift = 0.0

        # 3. High Dynamic Range & Sky Presence in Top
        sky_region = arr[:int(proc_img.height * 0.25), :]
        sky_lum = lum[:int(proc_img.height * 0.25)]
        sky_frac = float(np.mean((sky_lum > 185) & (sky_region[:, :, 2] >= sky_region[:, :, 0] - 5)))

        metrics = {
            "ground_contrast_ratio": round(contrast_ratio, 2),
            "sky_blue_shift": round(sky_blue_shift, 4),
            "sky_pixel_fraction": round(sky_frac, 3)
        }

        # Decision rule:
        if category_indoor:
            return SceneClassificationResult(
                is_indoor=True,
                outdoor_shadows_visible=False,
                confidence=0.95,
                scene_type="indoor",
                reason=f"Infrastructure category '{category}' represents an indoor technical facility.",
                metrics=metrics
            )

        # Empirical thresholding:
        sky_mean = float(np.mean(sky_lum))
        is_sunlit_outdoor = (contrast_ratio >= 1.65 and (sky_blue_shift > 0.010 or sky_frac > 0.05)) or (contrast_ratio >= 2.1)
        is_diffuse_outdoor = (contrast_ratio < 1.65 and (sky_frac > 0.10 or sky_mean > 140))

        if is_sunlit_outdoor:
            return SceneClassificationResult(
                is_indoor=False,
                outdoor_shadows_visible=True,
                confidence=0.88,
                scene_type="outdoor_sunlit",
                reason="Direct outdoor solar illumination detected with high ground contrast and daylight spectrum.",
                metrics=metrics
            )
        elif is_diffuse_outdoor:
            return SceneClassificationResult(
                is_indoor=False,
                outdoor_shadows_visible=False,
                confidence=0.82,
                scene_type="outdoor_diffuse",
                reason="Outdoor diffuse / overcast scene detected: lacking sharp directional cast shadows.",
                metrics=metrics
            )
        else:
            return SceneClassificationResult(
                is_indoor=True,
                outdoor_shadows_visible=False,
                confidence=0.80,
                scene_type="indoor",
                reason="Indoor scene detected: diffuse artificial lighting with low contrast and lack of solar cast shadows.",
                metrics=metrics
            )

    def estimate_dominant_shadow_direction(
        self,
        image: Image.Image
    ) -> ShadowEstimationResult:
        """
        Performs edge and gradient analysis on segmented shadow regions to estimate:
        - Dominant shadow cast direction in ground image coordinates.
        - Resultant vector length R (directional coherence).
        - Shadow coverage and boundary edge count.
        """
        img_rgb = image.convert("RGB")
        w, h = img_rgb.size
        max_dim = 600
        scale = max_dim / max(w, h) if max(w, h) > max_dim else 1.0
        if scale < 1.0:
            proc_img = img_rgb.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
        else:
            proc_img = img_rgb

        arr = np.array(proc_img, dtype=np.float64)
        pw, ph = proc_img.size
        lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]

        ground_top = int(ph * 0.35)
        ground_lum = lum[ground_top:, :]

        p_low = float(np.percentile(ground_lum, 0.5))
        p_high = float(np.percentile(ground_lum, 95))
        contrast_spread = p_high - p_low

        if contrast_spread < 20.0:
            return ShadowEstimationResult(
                outdoor_shadows_detected=False,
                dominant_image_angle_deg=None,
                estimated_shadow_azimuth_deg=None,
                directional_coherence=0.0,
                shadow_coverage_pct=0.0,
                boundary_edges_count=0,
                dominant_contrast_ratio=1.0
            )

        thresh = p_low + 0.40 * contrast_spread

        shadow_mask = np.zeros_like(lum, dtype=bool)
        shadow_mask[ground_top:, :] = (ground_lum <= thresh) & (ground_lum > 12)

        # Morphological noise removal
        shadow_mask = ndimage.binary_opening(shadow_mask, structure=np.ones((3, 3)))
        shadow_mask = ndimage.binary_closing(shadow_mask, structure=np.ones((5, 5)))

        total_pixels = pw * ph
        shadow_pixels = int(np.sum(shadow_mask))
        coverage_pct = (shadow_pixels / total_pixels) * 100.0

        if coverage_pct < 0.4 or coverage_pct > 60.0:
            return ShadowEstimationResult(
                outdoor_shadows_detected=False,
                dominant_image_angle_deg=None,
                estimated_shadow_azimuth_deg=None,
                directional_coherence=0.0,
                shadow_coverage_pct=round(coverage_pct, 2),
                boundary_edges_count=0,
                dominant_contrast_ratio=1.0
            )

        # Boundary extraction: dilated minus eroded shadow mask
        dilated = ndimage.binary_dilation(shadow_mask, iterations=2)
        eroded = ndimage.binary_erosion(shadow_mask, iterations=2)
        boundary_mask = dilated & ~eroded

        # Spatial gradients using Sobel operators
        blurred = ndimage.gaussian_filter(lum, sigma=1.2)
        gx = ndimage.sobel(blurred, axis=1)  # horizontal (pointing towards increasing brightness)
        gy = ndimage.sobel(blurred, axis=0)  # vertical (pointing downward towards increasing brightness)
        grad_mag = np.hypot(gx, gy)

        # Filter boundary pixels with significant gradient
        min_grad = max(20.0, float(np.percentile(grad_mag[boundary_mask], 25)) if np.any(boundary_mask) else 20.0)
        valid_edges = boundary_mask & (grad_mag >= min_grad)
        edge_count = int(np.sum(valid_edges))

        if edge_count < 20:
            return ShadowEstimationResult(
                outdoor_shadows_detected=False,
                dominant_image_angle_deg=None,
                estimated_shadow_azimuth_deg=None,
                directional_coherence=0.0,
                shadow_coverage_pct=round(coverage_pct, 2),
                boundary_edges_count=edge_count,
                dominant_contrast_ratio=1.0
            )

        ey, ex = np.where(valid_edges)
        edge_gx = gx[ey, ex]
        edge_gy = gy[ey, ex]
        edge_weights = grad_mag[ey, ex]

        # -------------------------------------------------------------------------
        # Tangent Orientation & Axial Double-Angle Statistics:
        # Lateral edges of a cast shadow run parallel to the cast direction.
        # Tangent vector along edge: t = (-gy, gx).
        # Ground angle psi = atan2(tx, -ty) in degrees.
        # -------------------------------------------------------------------------
        txs = -edge_gy
        tys = edge_gx
        tangent_ground_deg = np.degrees(np.arctan2(txs, -tys)) % 180.0

        rad2 = np.radians(2.0 * tangent_ground_deg)
        w_sum = np.sum(edge_weights)
        c2 = np.sum(edge_weights * np.cos(rad2)) / w_sum
        s2 = np.sum(edge_weights * np.sin(rad2)) / w_sum
        r2 = math.sqrt(c2**2 + s2**2)  # axial coherence

        axis_tangent_deg = float(np.degrees(0.5 * np.arctan2(s2, c2)) % 180.0)

        # -------------------------------------------------------------------------
        # Connected Component Second Moments (PCA of Ground Shadows):
        # -------------------------------------------------------------------------
        labeled, num_features = ndimage.label(shadow_mask[ground_top:, :])
        best_size = 0
        best_pca_deg = axis_tangent_deg
        for feat_id in range(1, num_features + 1):
            comp = (labeled == feat_id)
            sz = int(np.sum(comp))
            if sz > best_size and sz > 40:
                best_size = sz
                cy, cx = np.where(comp)
                mx, my = np.mean(cx), np.mean(cy)
                u20 = np.mean((cx - mx)**2)
                u02 = np.mean((cy - my)**2)
                u11 = np.mean((cx - mx) * (cy - my))
                axis_rad = 0.5 * np.arctan2(2 * u11, u20 - u02)
                axis_dx = np.cos(axis_rad)
                axis_dy = np.sin(axis_rad)
                best_pca_deg = float(np.degrees(np.arctan2(axis_dx, -axis_dy)) % 180.0)

        # Combined dominant axial direction (0 to 180 deg)
        if best_size >= 80:
            diff_pca = abs(best_pca_deg - axis_tangent_deg) % 180.0
            if min(diff_pca, 180.0 - diff_pca) < 30.0:
                dominant_axial = (best_pca_deg + axis_tangent_deg) / 2.0
            else:
                dominant_axial = best_pca_deg
        else:
            dominant_axial = axis_tangent_deg

        # Default directed candidates
        cand1 = dominant_axial % 360.0
        cand2 = (dominant_axial + 180.0) % 360.0

        v1 = np.array([np.sin(np.radians(cand1)), -np.cos(np.radians(cand1))])
        v2 = np.array([np.sin(np.radians(cand2)), -np.cos(np.radians(cand2))])

        # Directional gradient score: measure alignment of boundary gradient vectors
        dot1 = float(np.sum(edge_weights * (edge_gx * v1[0] + edge_gy * v1[1])))
        dot2 = float(np.sum(edge_weights * (edge_gx * v2[0] + edge_gy * v2[1])))

        chosen_angle = cand1 if dot1 >= dot2 else cand2

        # Contrast ratio between boundary lit ground and shadowed interior
        lit_lum = lum[valid_edges]
        contrast = float(np.mean(lit_lum) / (p_low + 2.0))

        return ShadowEstimationResult(
            outdoor_shadows_detected=True,
            dominant_image_angle_deg=round(chosen_angle, 2),
            estimated_shadow_azimuth_deg=None,
            directional_coherence=round(min(1.0, max(0.20, r2)), 3),
            shadow_coverage_pct=round(coverage_pct, 2),
            boundary_edges_count=edge_count,
            dominant_contrast_ratio=round(contrast, 2)
        )

    estimate_shadow_direction = estimate_dominant_shadow_direction

    def evaluate_plausibility(
        self,
        image_input: Union[str, Path, bytes, Image.Image],
        claimed_gps: Optional[Dict[str, float]] = None,
        claimed_timestamp: Optional[Union[datetime, str]] = None,
        camera_heading: Optional[float] = None,
        photo_category: Optional[str] = None,
        is_indoor: Optional[bool] = None
    ) -> SunShadowPlausibilityResult:
        """
        Main entry point for Sun-Shadow Plausibility Verification.
        Coordinates:
        - Image loading and EXIF extraction.
        - Solar ephemeris calculation via pvlib.
        - Physical feasibility (solar altitude / nighttime rejection).
        - Scene classification and indoor skipping.
        - Edge and gradient analysis of shadow direction.
        - Geographic orientation mapping and angular error calculation.
        - Plausibility score generation with mandatory advisory caveat.
        """
        # Load Image
        if isinstance(image_input, (str, Path)):
            p = Path(image_input)
            if not p.exists():
                raise FileNotFoundError(f"Image not found at {p}")
            img = Image.open(p)
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

        # Respect EXIF orientation if present
        img = ImageOps.exif_transpose(img)

        # Extract EXIF metadata
        exif_meta = extract_exif_metadata(img)

        # Resolve GPS coordinates
        lat = (claimed_gps.get("latitude") if claimed_gps else None) or exif_meta.get("latitude")
        lon = (claimed_gps.get("longitude") if claimed_gps else None) or exif_meta.get("longitude")

        if lat is None or lon is None:
            raise ValueError(
                "GPS coordinates missing. Provide 'claimed_gps' ({'latitude': ..., 'longitude': ...}) "
                "or ensure photo contains valid GPS EXIF tags."
            )

        # Resolve Timestamp
        ts = claimed_timestamp or exif_meta.get("timestamp")
        if not ts:
            raise ValueError(
                "Capture timestamp missing. Provide 'claimed_timestamp' (ISO 8601 string or datetime) "
                "or ensure photo contains EXIF DateTimeOriginal."
            )

        # Resolve Camera Heading
        cam_heading = camera_heading if camera_heading is not None else exif_meta.get("camera_heading")
        cam_source = "explicit" if camera_heading is not None else ("exif" if exif_meta.get("camera_heading") is not None else None)

        # Step 1: Solar Position via pvlib
        sun_pos = self.compute_sun_position(latitude=lat, longitude=lon, timestamp=ts)

        # Step 2: Nighttime / Solar Depression Check
        # If the sun is below the horizon (elevation <= 0°), direct solar illumination is physically impossible.
        if not sun_pos.is_sun_above_horizon:
            # Check scene classification anyway to confirm if artificial lights or nighttime
            scene_class = self.classify_scene(img, category=photo_category, is_indoor_override=is_indoor)
            
            # If the user passed an indoor image at night, it is simply skipped as indoor
            if scene_class.is_indoor:
                return SunShadowPlausibilityResult(
                    status="SKIPPED_INDOOR",
                    plausibility_score=None,
                    angular_discrepancy_deg=None,
                    claimed_gps={"latitude": lat, "longitude": lon},
                    claimed_timestamp=sun_pos.timestamp_iso,
                    camera_heading_deg=cam_heading,
                    camera_heading_source=cam_source,
                    sun_position=sun_pos,
                    scene_classification=scene_class,
                    estimated_shadow=ShadowEstimationResult(
                        outdoor_shadows_detected=False,
                        dominant_image_angle_deg=None,
                        estimated_shadow_azimuth_deg=None,
                        directional_coherence=0.0,
                        shadow_coverage_pct=0.0,
                        boundary_edges_count=0,
                        dominant_contrast_ratio=1.0
                    ),
                    advisory_indicator="SKIPPED_INDOOR",
                    human_readable_summary=(
                        f"Indoor technical facility detected. Solar verification is skipped per regulatory advisory guidelines. "
                        f"(Sun elevation is {sun_pos.elevation_deg:.1f}° below horizon)."
                    )
                )

            # Otherwise, an outdoor photo claimed at night when sun is below horizon
            return SunShadowPlausibilityResult(
                status="SUN_BELOW_HORIZON",
                plausibility_score=0.0,
                angular_discrepancy_deg=None,
                claimed_gps={"latitude": lat, "longitude": lon},
                claimed_timestamp=sun_pos.timestamp_iso,
                camera_heading_deg=cam_heading,
                camera_heading_source=cam_source,
                sun_position=sun_pos,
                scene_classification=scene_class,
                estimated_shadow=ShadowEstimationResult(
                    outdoor_shadows_detected=False,
                    dominant_image_angle_deg=None,
                    estimated_shadow_azimuth_deg=None,
                    directional_coherence=0.0,
                    shadow_coverage_pct=0.0,
                    boundary_edges_count=0,
                    dominant_contrast_ratio=1.0
                ),
                advisory_indicator="CRITICAL_INCONSISTENCY: Sun is below the horizon at claimed capture coordinates.",
                human_readable_summary=(
                    f"Physical Impossibility Indicator: At claimed coordinates ({lat:.4f}, {lon:.4f}) and timestamp "
                    f"({sun_pos.timestamp_iso}), the sun is {abs(sun_pos.elevation_deg):.1f}° below the horizon. "
                    f"Direct sunlight cast shadows cannot physically exist."
                )
            )

        # Step 3: Scene Classification (Outdoor vs Indoor Diffuse)
        scene_class = self.classify_scene(img, category=photo_category, is_indoor_override=is_indoor)

        # If image is an indoor environment, automatically skip per user requirement
        if scene_class.is_indoor:
            return SunShadowPlausibilityResult(
                status="SKIPPED_INDOOR",
                plausibility_score=None,
                angular_discrepancy_deg=None,
                claimed_gps={"latitude": lat, "longitude": lon},
                claimed_timestamp=sun_pos.timestamp_iso,
                camera_heading_deg=cam_heading,
                camera_heading_source=cam_source,
                sun_position=sun_pos,
                scene_classification=scene_class,
                estimated_shadow=ShadowEstimationResult(
                    outdoor_shadows_detected=False,
                    dominant_image_angle_deg=None,
                    estimated_shadow_azimuth_deg=None,
                    directional_coherence=0.0,
                    shadow_coverage_pct=0.0,
                    boundary_edges_count=0,
                    dominant_contrast_ratio=1.0
                ),
                advisory_indicator="EXEMPT_INDOOR: Sun-shadow verification skipped for indoor environments.",
                human_readable_summary=(
                    f"Indoor technical scene detected ({scene_class.reason}). "
                    f"Diffuse artificial lighting lacks directional solar cast shadows. "
                    f"Plausibility check skipped per regulatory advisory protocol."
                )
            )

        # Step 4: Shadow Direction Estimation (Edge/Gradient Analysis)
        shadow_est = self.estimate_shadow_direction(img)

        # If no distinct outdoor directional shadows were detected (e.g. overcast or diffuse day)
        if not shadow_est.outdoor_shadows_detected or shadow_est.dominant_image_angle_deg is None:
            return SunShadowPlausibilityResult(
                status="SKIPPED_DIFFUSE_NO_SHADOWS",
                plausibility_score=None,
                angular_discrepancy_deg=None,
                claimed_gps={"latitude": lat, "longitude": lon},
                claimed_timestamp=sun_pos.timestamp_iso,
                camera_heading_deg=cam_heading,
                camera_heading_source=cam_source,
                sun_position=sun_pos,
                scene_classification=scene_class,
                estimated_shadow=shadow_est,
                advisory_indicator="INCONCLUSIVE: No distinct directional outdoor shadows detected.",
                human_readable_summary=(
                    "Outdoor photo lacks sharp directional cast shadows (diffuse/overcast illumination or high solar zenith). "
                    "Verification skipped as shadow boundary gradients cannot be reliably measured."
                )
            )

        image_angle = shadow_est.dominant_image_angle_deg

        # Step 5: Geographic Orientation Mapping & Angular Error
        expected_azimuth = sun_pos.expected_shadow_azimuth_deg

        if cam_heading is not None:
            # Camera heading is known: map 2D image angle to geographic compass azimuth
            # Physical cast shadows define a ground axis with two candidate directions (A and B=A+180°)
            cand_A = (cam_heading + image_angle) % 360.0
            cand_B = (cand_A + 180.0) % 360.0

            diff_A = min(abs(cand_A - expected_azimuth), 360.0 - abs(cand_A - expected_azimuth))
            diff_B = min(abs(cand_B - expected_azimuth), 360.0 - abs(cand_B - expected_azimuth))

            # Anti-solar candidate aligns with expected cast shadow direction
            if diff_A <= diff_B:
                geo_shadow_azimuth = cand_A
                angular_err = diff_A
            else:
                geo_shadow_azimuth = cand_B
                angular_err = diff_B

            shadow_est.estimated_shadow_azimuth_deg = round(geo_shadow_azimuth, 2)

            # Plausibility score calculation:
            # Quadratic angular tolerance falloff modulated by shadow directional coherence R
            norm_err = min(1.0, angular_err / 90.0)
            angle_plausibility = max(0.0, 1.0 - (norm_err ** 2))
            coherence_factor = 0.75 + (0.25 * shadow_est.directional_coherence)
            score = round(max(0.0, min(1.0, angle_plausibility * coherence_factor)), 3)

            # Determine qualitative status
            if angular_err <= 28.0:
                status = "PLAUSIBLE"
                indicator = "PLAUSIBLE: Visible cast shadow direction aligns closely with theoretical solar position."
                summary = (
                    f"Consistent: Shadow estimated at {geo_shadow_azimuth:.1f}° azimuth matches theoretical anti-solar "
                    f"direction ({expected_azimuth:.1f}°) within {angular_err:.1f}°. Sun elevation: {sun_pos.elevation_deg:.1f}°."
                )
            elif angular_err <= 55.0:
                status = "PLAUSIBLE"
                indicator = "PLAUSIBLE_WITH_MARGIN: Shadow direction is broadly consistent within terrain and perspective margins."
                summary = (
                    f"Tolerant Match: Shadow estimated at {geo_shadow_azimuth:.1f}° diverges by {angular_err:.1f}° from "
                    f"theoretical ({expected_azimuth:.1f}°). Within acceptable camera tilt/perspective allowance."
                )
            elif angular_err <= 80.0:
                status = "QUESTIONABLE"
                indicator = "QUESTIONABLE: Noticeable divergence between visible shadow direction and expected solar azimuth."
                summary = (
                    f"Discrepancy: Visible shadow ({geo_shadow_azimuth:.1f}°) differs by {angular_err:.1f}° from expected "
                    f"solar shadow ({expected_azimuth:.1f}°). Review camera heading or terrain slope."
                )
            else:
                status = "SUSPICIOUS_MISMATCH"
                indicator = "POTENTIAL_MISMATCH: Significant divergence between visible shadows and claimed solar azimuth."
                summary = (
                    f"Mismatched Shadow Direction: Estimated shadow ({geo_shadow_azimuth:.1f}°) diverges by {angular_err:.1f}° "
                    f"from expected ({expected_azimuth:.1f}°). Shadow orientation is physically inconsistent with claimed sun position."
                )

        else:
            # Camera heading NOT provided in EXIF:
            # Compute the implied camera heading required for physical alignment
            implied_heading = (expected_azimuth - image_angle) % 360.0
            cam_heading = round(implied_heading, 2)
            cam_source = "implied_from_sun"
            geo_shadow_azimuth = expected_azimuth
            shadow_est.estimated_shadow_azimuth_deg = round(geo_shadow_azimuth, 2)
            angular_err = 0.0

            # Score is based on coherence and solar altitude feasibility
            # If sun elevation is high, shadows should be relatively compact
            score = round(0.85 * min(1.0, shadow_est.directional_coherence + 0.15), 3)
            status = "PLAUSIBLE"
            indicator = "PLAUSIBLE (UNORIENTED): Shadows physically coherent; camera heading inferred from solar position."
            summary = (
                f"Camera heading not recorded in EXIF. Physical shadow patterns are coherent (R={shadow_est.directional_coherence:.2f}). "
                f"Consistent if camera was facing approximately {implied_heading:.1f}° (implied bearing)."
            )

        return SunShadowPlausibilityResult(
            status=status,
            plausibility_score=score,
            angular_discrepancy_deg=round(angular_err, 2) if angular_err is not None else None,
            claimed_gps={"latitude": lat, "longitude": lon},
            claimed_timestamp=sun_pos.timestamp_iso,
            camera_heading_deg=cam_heading,
            camera_heading_source=cam_source,
            sun_position=sun_pos,
            scene_classification=scene_class,
            estimated_shadow=shadow_est,
            advisory_indicator=indicator,
            human_readable_summary=summary
        )


# Singleton Service Instance
sun_shadow_service = SunShadowPlausibilityService()
