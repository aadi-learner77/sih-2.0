"""
Benchmark Evaluation Script for Geospatial Built-Up Area Plausibility Engine.
PRAMAAN-X Infrastructure Forensic Suite.

Evaluates Open Buildings / OSM polygon queries across 8 benchmark sites:
1. COEP Technological University (Pune) - Plausible
2. Veermata Jijabai Technological Institute (VJTI Mumbai) - Plausible
3. BMS College of Engineering (Bengaluru) - Plausible
4. AICTE Headquarters (New Delhi) - Plausible
5. Indian Institute of Technology Bombay (Powai) - Plausible
6. Synthetic Rural Incomplete Site (Deficit) - Flagged for Review
7. Synthetic Industrial Encroachment Site (Excess) - Flagged for Review
8. Remote Agricultural Coordinates (Zero Buildings) - Flagged for Review

Outputs formatted audit table and generates 'generated_data/built_up_area_evaluation_results.json'.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone

from backend.app.services.built_up_area_service import (
    verify_built_up_area_footprint,
    BuiltUpAreaVerificationResult,
    DEFAULT_OPEN_BUILDINGS_FILE
)

EVAL_RESULTS_FILE = Path(__file__).resolve().parent.parent.parent.parent / "generated_data" / "built_up_area_evaluation_results.json"


BENCHMARK_CASES = [
    {
        "case_id": "BENCH_01_COEP",
        "name": "COEP Technological University, Pune",
        "category": "Engineering & Technology (State University)",
        "latitude": 18.5293,
        "longitude": 73.8565,
        "claimed_built_up_area_sqm": 6042.4,
        "radius_meters": 350.0,
        "tolerance_pct": 20.0,
        "expected_status": "WITHIN_TOLERANCE",
        "expected_flag": "PLAUSIBLE_FOOTPRINT_VERIFIED"
    },
    {
        "case_id": "BENCH_02_VJTI",
        "name": "Veermata Jijabai Technological Institute (VJTI Mumbai)",
        "category": "Engineering & Technology (Autonomous)",
        "latitude": 19.0222,
        "longitude": 72.8561,
        "claimed_built_up_area_sqm": 10699.0,
        "radius_meters": 350.0,
        "tolerance_pct": 25.0,
        "expected_status": "WITHIN_TOLERANCE",
        "expected_flag": "PLAUSIBLE_FOOTPRINT_VERIFIED"
    },
    {
        "case_id": "BENCH_03_BMSCE",
        "name": "BMS College of Engineering, Bengaluru",
        "category": "Engineering & Technology (Private Autonomous)",
        "latitude": 12.9416,
        "longitude": 77.5655,
        "claimed_built_up_area_sqm": 9444.8,
        "radius_meters": 350.0,
        "tolerance_pct": 20.0,
        "expected_status": "WITHIN_TOLERANCE",
        "expected_flag": "PLAUSIBLE_FOOTPRINT_VERIFIED"
    },
    {
        "case_id": "BENCH_04_AICTE_HQ",
        "name": "AICTE Headquarters, New Delhi",
        "category": "Statutory Regulatory Authority",
        "latitude": 28.5447,
        "longitude": 77.1558,
        "claimed_built_up_area_sqm": 18500.0,
        "radius_meters": 350.0,
        "tolerance_pct": 20.0,
        "expected_status": "WITHIN_TOLERANCE",
        "expected_flag": "PLAUSIBLE_FOOTPRINT_VERIFIED"
    },
    {
        "case_id": "BENCH_05_IITB",
        "name": "Indian Institute of Technology Bombay (Powai)",
        "category": "Institute of National Importance",
        "latitude": 19.1334,
        "longitude": 72.9133,
        "claimed_built_up_area_sqm": 35000.0,
        "radius_meters": 350.0,
        "tolerance_pct": 20.0,
        "expected_status": "WITHIN_TOLERANCE",
        "expected_flag": "PLAUSIBLE_FOOTPRINT_VERIFIED"
    },
    {
        "case_id": "BENCH_06_DEFICIT",
        "name": "Rural Technical Academy (Deficit Anomaly Site)",
        "category": "Under-Construction / Missing Infrastructure Test",
        "latitude": 26.8467,
        "longitude": 80.9462,
        "claimed_built_up_area_sqm": 15000.0,
        "radius_meters": 350.0,
        "tolerance_pct": 25.0,
        "expected_status": "FOOTPRINT_SIGNIFICANTLY_BELOW_CLAIM",
        "expected_flag": "FOOTPRINT_DEFICIT_FLAGGED_FOR_REVIEW"
    },
    {
        "case_id": "BENCH_07_EXCESS",
        "name": "Industrial Logistics Compound (Excess Anomaly Site)",
        "category": "Unreported / Non-Educational Mega-Structure Test",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "claimed_built_up_area_sqm": 2500.0,
        "radius_meters": 350.0,
        "tolerance_pct": 25.0,
        "expected_status": "FOOTPRINT_SIGNIFICANTLY_EXCEEDS_CLAIM",
        "expected_flag": "FOOTPRINT_EXCESS_FLAGGED_FOR_REVIEW"
    },
    {
        "case_id": "BENCH_08_EMPTY",
        "name": "Remote Agricultural Parcel (Zero Footprint Site)",
        "category": "Unbuilt / Mismatched Coordinates Test",
        "latitude": 27.1751,
        "longitude": 78.0421,
        "claimed_built_up_area_sqm": 8000.0,
        "radius_meters": 350.0,
        "tolerance_pct": 25.0,
        "expected_status": "NO_BUILDINGS_DETECTED",
        "expected_flag": "ZERO_FOOTPRINT_FLAGGED_FOR_REVIEW"
    }
]


class BuiltUpAreaEvaluator:
    """Orchestrates comprehensive benchmark validation sweeps."""

    def run_benchmark_suite(self) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        passed_evaluations = 0

        print("\n" + "=" * 115)
        print("  PRAMAAN-X GEOSPATIAL BUILT-UP AREA PLAUSIBILITY EVALUATION SUITE  ".center(115, "="))
        print("=" * 115)
        print(f"{'Site Name':<32} | {'Claimed (m²)':<12} | {'Measured (m²)':<12} | {'Bldgs':<5} | {'Diff (%)':<9} | {'Tolerance':<11} | {'Status'}")
        print("-" * 115)

        for case in BENCHMARK_CASES:
            res: BuiltUpAreaVerificationResult = verify_built_up_area_footprint(
                latitude=case["latitude"],
                longitude=case["longitude"],
                claimed_built_up_area=case["claimed_built_up_area_sqm"],
                radius_meters=case["radius_meters"],
                tolerance_pct=case["tolerance_pct"]
            )

            is_match = (
                res.status == case["expected_status"] and
                res.advisory_flag == case["expected_flag"]
            )
            if is_match:
                passed_evaluations += 1

            diff_str = f"{res.numbers_used.discrepancy_pct:+.1f}%"
            tol_str = f"±{case['tolerance_pct']:.0f}%"

            print(
                f"{case['name'][:32]:<32} | "
                f"{res.numbers_used.claimed_built_up_area_sqm:>12,.1f} | "
                f"{res.numbers_used.measured_footprint_sqm:>12,.1f} | "
                f"{res.numbers_used.building_count:>5} | "
                f"{diff_str:>9} | "
                f"{tol_str:>11} | "
                f"{res.status}"
            )

            results.append({
                "case_id": case["case_id"],
                "site_name": case["name"],
                "category": case["category"],
                "query_coordinates": {"lat": case["latitude"], "lon": case["longitude"]},
                "claimed_built_up_area_sqm": case["claimed_built_up_area_sqm"],
                "radius_meters": case["radius_meters"],
                "tolerance_pct": case["tolerance_pct"],
                "expected_status": case["expected_status"],
                "expected_flag": case["expected_flag"],
                "actual_status": res.status,
                "actual_flag": res.advisory_flag,
                "is_match": is_match,
                "numbers_used": res.numbers_used.model_dump(),
                "tolerance_band": res.tolerance_band.model_dump(),
                "advisory_summary": res.advisory_summary,
                "building_count": res.numbers_used.building_count,
                "buildings": [b.model_dump() for b in res.buildings]
            })

        print("-" * 115)
        accuracy = (passed_evaluations / len(BENCHMARK_CASES)) * 100.0
        print(f"Benchmark Accuracy: {passed_evaluations}/{len(BENCHMARK_CASES)} ({accuracy:.1f}%) Passed.")
        print("=" * 115 + "\n")

        evaluation_report = {
            "evaluation_title": "PRAMAAN-X Geospatial Built-Up Area Plausibility Benchmark",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "dataset_file": "generated_data/open_buildings_osm.geojson",
            "total_cases": len(BENCHMARK_CASES),
            "passed_cases": passed_evaluations,
            "accuracy_pct": accuracy,
            "cases": results
        }

        # Save to generated_data
        EVAL_RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(EVAL_RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(evaluation_report, f, indent=2)

        print(f"[OK] Evaluation results saved to {EVAL_RESULTS_FILE}\n")
        return evaluation_report


if __name__ == "__main__":
    evaluator = BuiltUpAreaEvaluator()
    evaluator.run_benchmark_suite()
