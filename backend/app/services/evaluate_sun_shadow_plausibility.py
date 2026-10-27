"""
Sun-Shadow Plausibility Ground Truth Benchmark & Validation Engine:
Validates the physical consistency check against known images with verified dates,
coordinates, camera bearings, and illumination conditions.

Evaluates:
1. Valid Outdoor Morning Photo (New Delhi, 2026-06-21 09:15 IST) -> PLAUSIBLE
2. Valid Outdoor Afternoon Photo (Mumbai, 2026-03-15 16:30 IST) -> PLAUSIBLE
3. Mismatched / Spoofed Timestamp (New Delhi claimed 09:15, afternoon shadow) -> SUSPICIOUS_MISMATCH
4. Indoor Technical Facility / Computer Lab (Bengaluru) -> SKIPPED_INDOOR
5. Nighttime Timestamp (New Delhi, 23:45 IST, Sun -37.2° below horizon) -> SUN_BELOW_HORIZON
6. Outdoor Overcast / Diffuse Lighting (Chennai) -> SKIPPED_DIFFUSE_NO_SHADOWS

Outputs structured JSON report to 'generated_data/sun_shadow_evaluation_results.json'
and prints a formatted scrutiny committee summary table.
"""

import os
import sys
import json
import time
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from backend.app.services.sun_shadow_service import (
    sun_shadow_service,
    SunShadowPlausibilityResult,
    ADVISORY_CAVEAT
)


BENCHMARK_DIR = Path("generated_data/photos/sun_shadow_benchmark")
BENCHMARK_RESULTS_FILE = Path("generated_data/sun_shadow_evaluation_results.json")


# ============================================================================
# IMAGE SYNTHESIS WITH KNOWN GROUND TRUTH GEOMETRY
# ============================================================================

def create_outdoor_benchmark_image(
    filename: str,
    shadow_azimuth_deg: float,
    camera_heading_deg: float,
    is_overcast: bool = False,
    output_dir: Path = BENCHMARK_DIR
) -> Path:
    """
    Renders an outdoor campus infrastructure scene with a vertical lamppost/monument
    and a cast shadow corresponding to the exact expected solar azimuth and camera heading.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    img_path = output_dir / filename

    w, h = 640, 420
    # Sky
    sky_color = (150, 155, 160) if is_overcast else (175, 205, 235)
    img = Image.new("RGB", (w, h), color=sky_color)
    draw = ImageDraw.Draw(img)

    # Campus Ground (Concrete/Paved Plaza)
    ground_y = 160
    ground_color = (165, 165, 162) if is_overcast else (215, 210, 195)
    draw.rectangle([0, ground_y, w, h], fill=ground_color)

    # Campus Building in Background
    draw.rectangle([40, 70, 240, ground_y], fill=(160, 155, 150), outline=(130, 125, 120), width=2)
    # Windows
    for r in range(3):
        for c in range(4):
            draw.rectangle([60 + c * 42, 85 + r * 22, 90 + c * 42, 100 + r * 22], fill=(80, 100, 120))

    # Lamppost base at plaza center
    base_x, base_y = 380, 270

    if not is_overcast:
        # Cast shadow on ground plane
        # Relative ground projection angle: (shadow_azimuth - camera_heading) % 360
        psi_deg = (shadow_azimuth_deg - camera_heading_deg) % 360.0
        psi_rad = math.radians(psi_deg)
        # Vector on ground plane: x right, y down
        vx = math.sin(psi_rad)
        vy = -math.cos(psi_rad)

        shadow_len = 135
        tip_x = base_x + shadow_len * vx
        tip_y = base_y + shadow_len * vy

        # Perpendicular normal for shadow width
        nx = -vy
        ny = vx
        shadow_poly = [
            (base_x - 12 * nx, base_y - 12 * ny),
            (base_x + 12 * nx, base_y + 12 * ny),
            (tip_x + 8 * nx, tip_y + 8 * ny),
            (tip_x - 8 * nx, tip_y - 8 * ny)
        ]
        # Outdoor shadow has cooler skylight fill
        draw.polygon(shadow_poly, fill=(80, 85, 110))

    # Lamppost pillar & base (painted metallic architectural fixture)
    draw.rectangle([base_x - 7, base_y - 95, base_x + 7, base_y], fill=(165, 170, 175), outline=(100, 105, 110))
    draw.ellipse([base_x - 14, base_y - 8, base_x + 14, base_y + 8], fill=(145, 150, 155))
    # Lamppost luminaire top
    draw.ellipse([base_x - 16, base_y - 105, base_x + 16, base_y - 85], fill=(230, 235, 240))

    img.save(img_path, "JPEG", quality=92)
    return img_path


def create_indoor_benchmark_image(
    filename: str,
    output_dir: Path = BENCHMARK_DIR
) -> Path:
    """
    Renders an indoor computer science laboratory / smart classroom
    with uniform diffuse ceiling fluorescent lighting and computer workstations.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    img_path = output_dir / filename

    w, h = 640, 420
    # Interior wall (cream/beige)
    img = Image.new("RGB", (w, h), color=(220, 218, 210))
    draw = ImageDraw.Draw(img)

    # Ceiling LED panels (recessed, white)
    for i in range(3):
        draw.rectangle([80 + i * 180, 20, 180 + i * 180, 45], fill=(255, 255, 250), outline=(200, 200, 195))

    # Floor (Tiled, diffuse reflection)
    floor_y = 200
    draw.rectangle([0, floor_y, w, h], fill=(165, 160, 150))
    for x in range(0, w, 70):
        draw.line([(x, floor_y), (x - 40, h)], fill=(145, 140, 130), width=1)

    # Workstation tables and monitors
    for col in range(3):
        tx = 70 + col * 180
        # Desk
        draw.rectangle([tx, 220, tx + 130, 310], fill=(130, 100, 75))
        # Monitor
        draw.rectangle([tx + 30, 175, tx + 100, 225], fill=(40, 45, 50))
        draw.rectangle([tx + 35, 180, tx + 95, 218], fill=(30, 110, 180)) # Screen
        draw.rectangle([tx + 60, 225, tx + 70, 235], fill=(60, 65, 70))  # Stand

    img.save(img_path, "JPEG", quality=90)
    return img_path


# ============================================================================
# BENCHMARK EVALUATOR
# ============================================================================

class SunShadowPlausibilityEvaluator:
    """
    Executes automated validation sweep across 6 diverse test scenarios.
    """

    def __init__(self):
        self.benchmark_dir = BENCHMARK_DIR
        self.benchmark_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_benchmark_images(self) -> Dict[str, Path]:
        """Generates all 6 ground truth benchmark test images."""
        images = {}

        # 1. Delhi Morning (Consistent):
        # 2026-06-21 09:15 IST, Sun azimuth = 85.69°, Expected shadow = 265.69°, Camera facing North (0°)
        images["delhi_morning_valid"] = create_outdoor_benchmark_image(
            filename="delhi_campus_morning_valid.jpg",
            shadow_azimuth_deg=265.69,
            camera_heading_deg=0.0,
            is_overcast=False
        )

        # 2. Mumbai Afternoon (Consistent):
        # 2026-03-15 16:30 IST, Sun azimuth = 255.19°, Expected shadow = 75.19°, Camera facing East (90°)
        images["mumbai_afternoon_valid"] = create_outdoor_benchmark_image(
            filename="mumbai_campus_afternoon_valid.jpg",
            shadow_azimuth_deg=75.19,
            camera_heading_deg=90.0,
            is_overcast=False
        )

        # 3. Spoofed Timestamp Delhi (Mismatched):
        # Claimed morning 09:15 IST (expected shadow 265.69°), but shadow points towards 175° (South)
        images["delhi_spoofed_mismatch"] = create_outdoor_benchmark_image(
            filename="delhi_campus_spoofed_timestamp.jpg",
            shadow_azimuth_deg=175.0,
            camera_heading_deg=0.0,
            is_overcast=False
        )

        # 4. Indoor Smart Classroom / Lab (Bengaluru)
        images["indoor_classroom"] = create_indoor_benchmark_image(
            filename="indoor_smart_classroom.jpg"
        )

        # 5. Nighttime Timestamp (Delhi 23:45 IST, Sun -37.2° below horizon)
        images["delhi_nighttime"] = create_outdoor_benchmark_image(
            filename="delhi_campus_nighttime_claimed.jpg",
            shadow_azimuth_deg=265.69,
            camera_heading_deg=0.0,
            is_overcast=False
        )

        # 6. Outdoor Overcast Diffuse (Chennai)
        images["chennai_overcast"] = create_outdoor_benchmark_image(
            filename="chennai_campus_overcast.jpg",
            shadow_azimuth_deg=0.0,
            camera_heading_deg=0.0,
            is_overcast=True
        )

        return images

    def run_validation_suite(self) -> Dict[str, Any]:
        """
        Executes end-to-end evaluation across all test scenarios.
        """
        images = self.generate_all_benchmark_images()

        test_cases = [
            {
                "case_id": "TC_001",
                "name": "Delhi Campus Morning (Valid Anti-Solar Shadow)",
                "image_key": "delhi_morning_valid",
                "location_name": "AICTE Headquarters, New Delhi",
                "latitude": 28.5447,
                "longitude": 77.1558,
                "timestamp": "2026-06-21T09:15:00+05:30",
                "camera_heading": 0.0,
                "photo_category": "campus_plaza_exterior",
                "is_indoor": False,
                "expected_status": "PLAUSIBLE",
                "expected_min_score": 0.85
            },
            {
                "case_id": "TC_002",
                "name": "Mumbai Campus Afternoon (Valid Anti-Solar Shadow)",
                "image_key": "mumbai_afternoon_valid",
                "location_name": "IIT Bombay Campus, Mumbai",
                "latitude": 19.1334,
                "longitude": 72.9133,
                "timestamp": "2026-03-15T16:30:00+05:30",
                "camera_heading": 90.0,
                "photo_category": "academic_quadrangle",
                "is_indoor": False,
                "expected_status": "PLAUSIBLE",
                "expected_min_score": 0.85
            },
            {
                "case_id": "TC_003",
                "name": "Delhi Campus Spoofed Timestamp (Shadow Points South)",
                "image_key": "delhi_spoofed_mismatch",
                "location_name": "AICTE Headquarters, New Delhi",
                "latitude": 28.5447,
                "longitude": 77.1558,
                "timestamp": "2026-06-21T09:15:00+05:30",
                "camera_heading": 0.0,
                "photo_category": "campus_plaza_exterior",
                "is_indoor": False,
                "expected_status": "SUSPICIOUS_MISMATCH",
                "expected_max_score": 0.25
            },
            {
                "case_id": "TC_004",
                "name": "Bengaluru Indoor Smart Classroom (Artificial Diffuse Lighting)",
                "image_key": "indoor_classroom",
                "location_name": "IISc Campus, Bengaluru",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "timestamp": "2026-05-10T11:30:00+05:30",
                "camera_heading": None,
                "photo_category": "smart_classroom",
                "is_indoor": True,
                "expected_status": "SKIPPED_INDOOR",
                "expected_score_is_none": True
            },
            {
                "case_id": "TC_005",
                "name": "Delhi Campus Nighttime Claim (Sun Below Horizon)",
                "image_key": "delhi_nighttime",
                "location_name": "AICTE Headquarters, New Delhi",
                "latitude": 28.5447,
                "longitude": 77.1558,
                "timestamp": "2026-06-21T23:45:00+05:30",
                "camera_heading": 0.0,
                "photo_category": "campus_plaza_exterior",
                "is_indoor": False,
                "expected_status": "SUN_BELOW_HORIZON",
                "expected_max_score": 0.0
            },
            {
                "case_id": "TC_006",
                "name": "Chennai Campus Overcast (Diffuse Overcast Illumination)",
                "image_key": "chennai_overcast",
                "location_name": "IIT Madras Campus, Chennai",
                "latitude": 12.9915,
                "longitude": 80.2337,
                "timestamp": "2026-11-15T12:45:00+05:30",
                "camera_heading": 0.0,
                "photo_category": "campus_courtyard",
                "is_indoor": False,
                "expected_status": "SKIPPED_DIFFUSE_NO_SHADOWS",
                "expected_score_is_none": True
            }
        ]

        results_list = []
        passed_checks = 0

        for tc in test_cases:
            img_path = images[tc["image_key"]]
            start_t = time.perf_counter()

            eval_res: SunShadowPlausibilityResult = sun_shadow_service.evaluate_plausibility(
                image_input=img_path,
                claimed_gps={"latitude": tc["latitude"], "longitude": tc["longitude"]},
                claimed_timestamp=tc["timestamp"],
                camera_heading=tc["camera_heading"],
                photo_category=tc["photo_category"],
                is_indoor=tc["is_indoor"]
            )
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0

            # Verification of criteria
            status_match = (eval_res.status == tc["expected_status"])
            score_match = True
            if tc.get("expected_min_score") is not None:
                score_match = (eval_res.plausibility_score is not None and eval_res.plausibility_score >= tc["expected_min_score"])
            elif tc.get("expected_max_score") is not None:
                score_match = (eval_res.plausibility_score is not None and eval_res.plausibility_score <= tc["expected_max_score"])
            elif tc.get("expected_score_is_none"):
                score_match = (eval_res.plausibility_score is None)

            test_passed = status_match and score_match and bool("ADVISORY" in eval_res.caveat)
            if test_passed:
                passed_checks += 1

            results_list.append({
                "case_id": tc["case_id"],
                "name": tc["name"],
                "location": tc["location_name"],
                "timestamp": tc["timestamp"],
                "status": eval_res.status,
                "expected_status": tc["expected_status"],
                "status_match": status_match,
                "plausibility_score": eval_res.plausibility_score,
                "angular_error_deg": eval_res.angular_discrepancy_deg,
                "sun_azimuth_deg": eval_res.sun_position.azimuth_deg,
                "sun_elevation_deg": eval_res.sun_position.elevation_deg,
                "expected_shadow_azimuth_deg": eval_res.sun_position.expected_shadow_azimuth_deg,
                "estimated_shadow_azimuth_deg": eval_res.estimated_shadow.estimated_shadow_azimuth_deg,
                "directional_coherence": eval_res.estimated_shadow.directional_coherence,
                "elapsed_ms": round(elapsed_ms, 2),
                "advisory_indicator": eval_res.advisory_indicator,
                "summary": eval_res.human_readable_summary,
                "caveat_verified": bool("ADVISORY" in eval_res.caveat),
                "test_passed": test_passed
            })

        total_cases = len(test_cases)
        accuracy_pct = (passed_checks / total_cases) * 100.0

        report = {
            "evaluation_engine": "PRAMAAN-X Sun-Shadow Plausibility Ground Truth Benchmark",
            "evaluated_at": datetime.now().isoformat(),
            "total_test_cases": total_cases,
            "passed_test_cases": passed_checks,
            "accuracy_pct": round(accuracy_pct, 1),
            "benchmark_results": results_list,
            "regulatory_compliance_guarantee": (
                "All results strictly formulate findings as advisory decision-support indicators. "
                "Indoor environments and diffuse overcast conditions are exempted from punitive evaluation."
            ),
            "caveat": ADVISORY_CAVEAT
        }

        # Save to JSON
        with open(BENCHMARK_RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report

    def print_benchmark_summary(self, report: Dict[str, Any]):
        """Prints a clean, formatted ASCII table of the benchmark sweep."""
        print("\n" + "=" * 90)
        print("   PRAMAAN-X PHOTO SUN-SHADOW PLAUSIBILITY BENCHMARK VALIDATION REPORT")
        print("=" * 90)
        print(f"Total Cases Evaluated: {report['total_test_cases']} | Passed: {report['passed_test_cases']} | Accuracy: {report['accuracy_pct']}%\n")
        print(f"{'ID':<7} | {'Status':<24} | {'Score':<7} | {'Diff(°)':<8} | {'Latency':<8} | {'Result':<6}")
        print("-" * 90)
        for r in report["benchmark_results"]:
            score_str = f"{r['plausibility_score']:.3f}" if r["plausibility_score"] is not None else "  None "
            diff_str = f"{r['angular_error_deg']:.1f}°" if r["angular_error_deg"] is not None else "   N/A  "
            pass_str = "PASS" if r["test_passed"] else "FAIL"
            print(f"{r['case_id']:<7} | {r['status']:<24} | {score_str:<7} | {diff_str:<8} | {r['elapsed_ms']:>5.1f}ms | {pass_str:<6}")
        print("-" * 90)
        print("Mandatory Advisory Caveat:")
        print(f"\"{report['caveat']}\"")
        print("=" * 90 + "\n")


# Standalone runner
if __name__ == "__main__":
    evaluator = SunShadowPlausibilityEvaluator()
    report = evaluator.run_validation_suite()
    evaluator.print_benchmark_summary(report)
