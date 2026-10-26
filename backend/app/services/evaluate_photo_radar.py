"""
Photo Reuse Radar Ground Truth Evaluation Engine:
Evaluates detection accuracy across planted duplicates (exact duplicates, cropped/rotated/brightened near-duplicates, EXIF stripped)
and negative controls. Reports Precision, Recall, F1-Score, and cluster detection statistics.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from PIL import Image, ImageDraw
import numpy as np

from backend.app.services.photo_radar import (
    NationalPhotoRadarService,
    photo_radar_service,
    EVAL_RESULTS_FILE
)


PHOTOS_DIR = Path("generated_data/photos")


def create_negative_control_photos(output_dir: Path = PHOTOS_DIR) -> List[Path]:
    """Creates distinct negative control infrastructure photos that should not match any duplicate."""
    output_dir.mkdir(parents=True, exist_ok=True)
    controls = []

    # Control 1: Botanical garden
    p1 = output_dir / "INST_005_distinct_botany_garden.jpg"
    img1 = Image.new("RGB", (1000, 700), (25, 75, 35))
    d1 = ImageDraw.Draw(img1)
    for k in range(90):
        x = int(np.sin(k) * 420 + 500)
        y = int(np.cos(k * 1.7) * 260 + 350)
        d1.ellipse([x - 35, y - 35, x + 35, y + 35], fill=(70, 160, 50), outline=(90, 200, 70), width=2)
    d1.rectangle([30, 30, 970, 90], fill=(15, 45, 20))
    d1.text((50, 48), "INSTITUTE BOTANICAL & MEDICINAL PLANT RESEARCH NURSERY", fill=(230, 255, 230))
    img1.save(p1, "JPEG", quality=92)
    controls.append(p1)

    # Control 2: Solar rooftop
    p2 = output_dir / "INST_006_distinct_solar_rooftop.jpg"
    img2 = Image.new("RGB", (1000, 700), (20, 30, 60))
    d2 = ImageDraw.Draw(img2)
    for i in range(10):
        for j in range(8):
            d2.rectangle([50 + i * 90, 110 + j * 70, 130 + i * 90, 170 + j * 70], fill=(40, 75, 130), outline=(210, 230, 255), width=2)
    d2.rectangle([30, 30, 970, 90], fill=(10, 20, 45))
    d2.text((50, 48), "CAMPUS 500KW ROOFTOP SOLAR PV GENERATION PLANT", fill=(220, 235, 255))
    img2.save(p2, "JPEG", quality=92)
    controls.append(p2)

    # Control 3: Central plaza amphitheater fountain
    p3 = output_dir / "INST_007_distinct_cafeteria_hall.jpg"
    img3 = Image.new("RGB", (1000, 700), (75, 65, 55))
    d3 = ImageDraw.Draw(img3)
    for r in [50, 110, 170, 230, 290]:
        d3.ellipse([500 - r, 390 - r, 500 + r, 390 + r], outline=(220, 210, 180), width=5)
    for a in range(0, 360, 30):
        rad = np.radians(a)
        d3.line([(500, 390), (int(500 + 290 * np.cos(rad)), int(390 + 290 * np.sin(rad)))], fill=(200, 190, 160), width=3)
    d3.rectangle([30, 30, 970, 90], fill=(35, 30, 25))
    d3.text((50, 48), "CENTRAL CAMPUS PLAZA & BOTANICAL MEMORIAL FOUNTAIN", fill=(245, 235, 215))
    img3.save(p3, "JPEG", quality=92)
    controls.append(p3)

    return controls


class PhotoRadarEvaluator:
    """Evaluates National Photo Reuse Radar against ground truth benchmark."""

    def __init__(self, radar: Optional[NationalPhotoRadarService] = None):
        self.radar = radar or photo_radar_service

    def run_evaluation(self, photos_dir: Path = PHOTOS_DIR) -> Dict[str, Any]:
        """Runs full evaluation and reports precision/recall and cluster analysis."""
        # Ensure base photos exist
        if not photos_dir.exists() or len(list(photos_dir.glob("*.jpg"))) < 10:
            import subprocess
            subprocess.run([sys.executable, "-m", "synthetic_generator.generate_photo_variants"], check=True)

        # Create negative controls
        create_negative_control_photos(photos_dir)

        # Reset and index all photos into radar
        self.radar.catalog.clear()
        import faiss
        self.radar.faiss_index = faiss.IndexFlatIP(self.radar.dim)
        self.radar.index_photos_directory(photos_dir)

        # Evaluate test queries
        # Positive cases:
        # 1. INST_002 (Exact duplicates of INST_001) -> expected: True, match_type: 'exact'
        # 2. INST_003 (Cropped/rotated/brightened of INST_001) -> expected: True, match_type: 'near-duplicate' or 'semantically similar'
        # 3. INST_004 (EXIF stripped of INST_001) -> expected: True
        # Negative cases:
        # 4. INST_005, INST_006, INST_007 (Distinct facilities) -> expected: False

        tp = 0
        fp = 0
        tn = 0
        fn = 0

        match_type_counts = {"exact": 0, "near-duplicate": 0, "semantically similar": 0}
        details_list = []

        all_photo_files = sorted(list(photos_dir.glob("*.jpg")))

        for p_file in all_photo_files:
            fname = p_file.name
            parts = fname.split("_")
            inst_id = f"{parts[0]}_{parts[1]}" if len(parts) >= 2 and parts[0] == "INST" else parts[0]

            # We query from the perspective of the institution submitting this photo
            img = Image.open(p_file)
            with open(p_file, "rb") as fh:
                b = fh.read()

            res = self.radar.query_photo(
                img=img,
                current_institution_id=inst_id,
                file_bytes=b,
                exact_hamming_threshold=0,
                near_duplicate_hamming_threshold=12,
                clip_semantic_threshold=0.82
            )

            is_planted_duplicate = inst_id in ["INST_002", "INST_003", "INST_004"]
            is_control = inst_id in ["INST_005", "INST_006", "INST_007"]
            detected = res.has_cross_institution_reuse

            top_match = res.top_match

            if is_planted_duplicate:
                if detected:
                    tp += 1
                    if top_match:
                        match_type_counts[top_match.match_type] = match_type_counts.get(top_match.match_type, 0) + 1
                else:
                    fn += 1
            elif is_control:
                if detected:
                    fp += 1
                else:
                    tn += 1

            if is_planted_duplicate or is_control:
                details_list.append({
                    "filename": fname,
                    "institution_id": inst_id,
                    "is_planted_duplicate": is_planted_duplicate,
                    "detected": detected,
                    "top_match_type": top_match.match_type if top_match else None,
                    "similarity_score": top_match.similarity_score if top_match else 0.0,
                    "matched_institution": top_match.matched_institution_name if top_match else None
                })

        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0

        # Cluster detection
        cluster_res = self.radar.detect_photo_reuse_clusters(
            exact_hamming_threshold=0,
            near_duplicate_hamming_threshold=12,
            clip_semantic_threshold=0.82
        )

        report = {
            "evaluation_timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_queries_evaluated": len(details_list),
                "true_positives": tp,
                "false_positives": fp,
                "true_negatives": tn,
                "false_negatives": fn,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "accuracy": round(accuracy, 4)
            },
            "detection_by_match_type": match_type_counts,
            "clusters_detected_count": cluster_res.total_clusters_count,
            "institutions_involved_count": cluster_res.total_institutions_involved,
            "clusters_summary": [
                {
                    "cluster_id": c.cluster_id,
                    "category": c.photo_category,
                    "institutions_count": c.institutions_count,
                    "risk_level": c.risk_level,
                    "match_types": c.match_types_present
                }
                for c in cluster_res.clusters
            ],
            "query_details": details_list
        }

        EVAL_RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(EVAL_RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report

    def format_evaluation_report(self, report: Dict[str, Any]) -> str:
        """Formats the evaluation report as a clean ASCII summary."""
        m = report["metrics"]
        lines = [
            "=" * 78,
            "  NATIONAL PHOTO REUSE RADAR: GROUND TRUTH BENCHMARK EVALUATION",
            "=" * 78,
            f" Queries Evaluated: {m['total_queries_evaluated']} | Planted Duplicates: {m['true_positives'] + m['false_negatives']} | Controls: {m['true_negatives'] + m['false_positives']}",
            f" Precision: {m['precision']:.4f} ({m['precision']:.1%})  |  Recall: {m['recall']:.4f} ({m['recall']:.1%})",
            f" F1-Score:  {m['f1_score']:.4f}  |  Accuracy: {m['accuracy']:.4f} ({m['accuracy']:.1%})",
            "-" * 78,
            f" Confusion Matrix: TP={m['true_positives']} | FP={m['false_positives']} | TN={m['true_negatives']} | FN={m['false_negatives']}",
            f" Detection Breakdown by Match Type: {report['detection_by_match_type']}",
            "-" * 78,
            f" Photo Reuse Clusters Discovered: {report['clusters_detected_count']}",
            f" Institutions Involved in Cross-Reuses: {report['institutions_involved_count']}",
            "-" * 78
        ]

        for c in report["clusters_summary"]:
            lines.append(f"  * {c['cluster_id']}: '{c['category']}' - {c['institutions_count']} colleges ({', '.join(c['match_types'])}) [{c['risk_level']}]")

        lines.append("=" * 78)
        return "\n".join(lines)


if __name__ == "__main__":
    evaluator = PhotoRadarEvaluator()
    rep = evaluator.run_evaluation()
    print(evaluator.format_evaluation_report(rep))
