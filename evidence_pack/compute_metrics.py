"""
PRAMAAN-X Evidence Verification Script:
Reads ground_truth.csv and metrics.json, validates TP/FP/FN/TN, defect counts,
field-level extraction metrics, and timing distributions.
"""
import os
import csv
import json
import numpy as np
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    gen_data = root / "generated_data"
    gt_csv = gen_data / "ground_truth.csv"
    metrics_path = root / "evidence_pack" / "metrics.json"

    print("=" * 80)
    print(" PRAMAAN-X EVIDENCE SCRIPT: RECOMPUTING & VALIDATING METRICS")
    print("=" * 80)

    # 1. Ground Truth Verification
    gt_rows = []
    defect_counts = {}
    if gt_csv.exists():
        with open(gt_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                gt_rows.append(row)
                d = row.get("defect_type", "").strip()
                if d:
                    defect_counts[d] = defect_counts.get(d, 0) + 1

    print(f"Total planted defect records in ground_truth.csv: {len(gt_rows)}")
    print(f"Distinct defect types in ground_truth.csv: {len(defect_counts)}")

    # 2. Metrics JSON Verification
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # Anomaly Flag Detection
    anomaly = metrics.get("anomaly_flag_detection", {})
    tp = anomaly.get("true_positives", 0)
    fp = anomaly.get("false_positives", 0)
    tn = anomaly.get("true_negatives", 0)
    fn = anomaly.get("false_negatives", 0)

    computed_prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    computed_rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    computed_f1 = (2 * computed_prec * computed_rec) / (computed_prec + computed_rec) if (computed_prec + computed_rec) > 0 else 0.0
    computed_fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    print("\n--- ANOMALY FLAG DETECTION ---")
    print(f"TP: {tp}")
    print(f"FP: {fp}")
    print(f"TN: {tn}")
    print(f"FN: {fn}")
    print(f"Precision: {computed_prec:.4f} (recorded: {anomaly.get('precision', 0.0):.4f})")
    print(f"Recall:    {computed_rec:.4f} (recorded: {anomaly.get('recall', 0.0):.4f})")
    print(f"F1 Score:  {computed_f1:.4f} (recorded: {anomaly.get('f1_score', 0.0):.4f})")
    print(f"FPR:       {computed_fpr * 100:.2f}% (recorded: {anomaly.get('false_positive_rate_percent', 0.0):.2f}%)")

    # 3. Field-Level Extraction
    f_ext = metrics.get("field_level_extraction", {})
    print("\n--- FIELD-LEVEL EXTRACTION ---")
    print(f"Total documents evaluated: {f_ext.get('total_documents_evaluated')}")
    print(f"Macro Precision: {f_ext.get('macro_precision'):.4f}")
    print(f"Macro Recall:    {f_ext.get('macro_recall'):.4f}")
    print(f"Macro F1:        {f_ext.get('macro_f1_score'):.4f}")
    print(f"Micro Precision: {f_ext.get('micro_precision'):.4f}")
    print(f"Micro Recall:    {f_ext.get('micro_recall'):.4f}")
    print(f"Micro F1:        {f_ext.get('micro_f1_score'):.4f}")

    per_field = f_ext.get("per_field_metrics", {})
    for field_name, pstats in per_field.items():
        print(f"  • {field_name:20}: P={pstats['precision']:.4f}, R={pstats['recall']:.4f}, F1={pstats['f1_score']:.4f} (TP={pstats['true_positives']}, FP={pstats['false_positives']}, FN={pstats['false_negatives']})")

    # 4. Turnaround Timing
    timing = metrics.get("processing_time_comparison", {})
    print("\n--- PROCESSING TIME ---")
    print(f"Automated seconds per application (mean): {timing.get('automated_seconds_per_application')}s")
    print(f"Manual baseline (assumed): {timing.get('manual_baseline_minutes')}m")
    print(f"Speedup factor: {timing.get('speedup_factor')}x")

    # 5. Defect Breakdown Table Generation
    defects = metrics.get("validation_accuracy_per_defect_type", {})
    print(f"\nTotal defect categories benchmarked in harness: {len(defects)}")

    return {
        "anomaly": {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "precision": computed_prec, "recall": computed_rec, "f1": computed_f1, "fpr": computed_fpr},
        "field_extraction": f_ext,
        "timing": timing,
        "defect_counts": defect_counts
    }

if __name__ == "__main__":
    main()
