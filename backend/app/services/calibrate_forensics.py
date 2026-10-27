"""
Forensics Calibration Script & Ground Truth Engine:
Sweeps decision thresholds on the ground truth dataset, evaluates precision/recall/F1 curves,
and determines optimal operating points for regulatory scrutiny review indicators.

Ground Truth Benchmark Cases:
1. GT_FORENSIC_01_METADATA: PDF with Canva/Photoshop producer signature + incremental updates.
2. GT_FORENSIC_02_FONT: PDF with spliced font tokens in numerical approved intake fields.
3. GT_FORENSIC_03_ELA: Image document with spliced localized approval stamp/dates.
4. GT_FORENSIC_04_COPYMOVE: Image document with cloned circular seal / signature using ORB.
5. GT_FORENSIC_05_QR_MISMATCH: Document with verification QR payload pointing to mismatched certificate ref.
6. Negative Controls: Clean authentic certificates without metadata anomalies, uniform fonts, homogeneous ELA, no cloned keypoints, and matching QR.

Wording Guarantee:
All outputs strictly formulate findings as "indicators for review" (never "verdicts" or "fraud").
"""

import os
import sys
import json
import io
import math
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

import cv2
import numpy as np
import pymupdf
import qrcode

from backend.app.services.document_forensics import (
    DocumentForensicsEngine,
    document_forensics_engine
)


SAMPLE_DIR = Path("generated_data/forensic_samples")
GT_CATALOG_FILE = Path("generated_data/document_forensics_ground_truth.json")
CALIBRATION_OUTPUT_FILE = Path("generated_data/forensics_calibration_results.json")


# ============================================================================
# GROUND TRUTH FIXTURE GENERATORS
# ============================================================================

def ensure_ground_truth_fixtures(sample_dir: Path = SAMPLE_DIR) -> Dict[str, Any]:
    """Generates synthetic ground truth benchmark documents for all 5 forensic checks."""
    sample_dir.mkdir(parents=True, exist_ok=True)
    records = []

    # ------------------------------------------------------------------------
    # 1. POSITIVE CASE: PDF Metadata Anomaly
    # ------------------------------------------------------------------------
    meta_pdf_path = sample_dir / "gt_metadata_anomaly.pdf"
    doc1 = pymupdf.open()
    page1 = doc1.new_page(width=595, height=842)
    page1.insert_text((50, 80), "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION", fontname="helv", fontsize=14)
    page1.insert_text((50, 110), "APPROVAL PROCESS 2025-26 - EXTENSION OF APPROVAL", fontname="helv", fontsize=11)
    page1.insert_text((50, 140), "Application No: 1-109283711 | Institution: Apex Institute of Technology", fontname="helv", fontsize=10)
    page1.insert_text((50, 170), "Approved Intake: 480 Seats", fontname="helv", fontsize=10)
    
    # Injected metadata with Canva Producer and older creation date
    doc1.set_metadata({
        "producer": "Canva Online PDF Editor (v3.2)",
        "creator": "Adobe InDesign 2024",
        "creationDate": "D:20240110090000+05'30'",
        "modDate": "D:20240520143000+05'30'"
    })
    
    # Save base PDF
    base_bytes = doc1.tobytes()
    # Append an incremental update revision (%%EOF trailer)
    incremental_tampered_bytes = base_bytes + b"\n% Tampered revision block\n12 0 obj\n<< /Type /Annot /Subtype /Text >>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<< /Size 13 >>\nstartxref\n" + str(len(base_bytes)).encode() + b"\n%%EOF\n"
    with open(meta_pdf_path, "wb") as f:
        f.write(incremental_tampered_bytes)

    records.append({
        "sample_id": "GT_FORENSIC_01_METADATA",
        "file_path": str(meta_pdf_path),
        "filename": meta_pdf_path.name,
        "is_tampered": True,
        "expected_check": "PDF_METADATA_ANALYSIS",
        "expected_indicator_id": "PDF_METADATA_PRODUCER_ANOMALY",
        "defect_description": "PDF metadata contains Canva editing signature and post-creation incremental update trailers",
        "category": "positive_case"
    })

    # ------------------------------------------------------------------------
    # 2. POSITIVE CASE: Font Inconsistency in Region
    # ------------------------------------------------------------------------
    font_pdf_path = sample_dir / "gt_font_inconsistency.pdf"
    doc2 = pymupdf.open()
    page2 = doc2.new_page(width=595, height=842)
    page2.insert_text((50, 80), "STATE HIGHER EDUCATION REGULATORY AUTHORITY", fontname="helv", fontsize=14)
    page2.insert_text((50, 120), "OFFICIAL AFFILIATION NOTIFICATION - SANCTIONED STUDENT INTAKE", fontname="helv", fontsize=11)
    
    # Line with dominant font 'helv' (Helvetica) 10pt, but injected intake '750' in 'times-bold' 14pt
    page2.insert_text((50, 180), "The competent authority hereby sanctions approved intake of ", fontname="helv", fontsize=10)
    # Anomalous span
    page2.insert_text((350, 180), "750", fontname="times-bold", fontsize=14)
    page2.insert_text((385, 180), " students for the 2025-26 academic session.", fontname="helv", fontsize=10)
    page2.insert_text((50, 210), "All infrastructure and teaching requirements must be maintained continuously.", fontname="helv", fontsize=10)
    page2.insert_text((50, 240), "Reference Number: AFF/KA/2025/11092", fontname="helv", fontsize=10)

    doc2.set_metadata({
        "producer": "ReportLab PDF Library - (opensource)",
        "creator": "Affiliation System"
    })
    doc2.save(str(font_pdf_path))

    records.append({
        "sample_id": "GT_FORENSIC_02_FONT",
        "file_path": str(font_pdf_path),
        "filename": font_pdf_path.name,
        "is_tampered": True,
        "expected_check": "FONT_INCONSISTENCY_IN_REGION",
        "expected_indicator_id": "FONT_INCONSISTENCY_IN_REGION",
        "defect_description": "Approved intake number '750' injected in Times-Bold 14pt inside Helvetica 10pt paragraph",
        "category": "positive_case"
    })

    # ------------------------------------------------------------------------
    # 3. POSITIVE CASE: Error Level Analysis (ELA) Spliced Patch
    # ------------------------------------------------------------------------
    ela_img_path = sample_dir / "gt_ela_tampered.jpg"
    # Create base certificate background with texture
    base_img = np.ones((500, 700, 3), dtype=np.uint8) * 235
    # Add subtle scan noise
    noise = np.random.normal(0, 3, base_img.shape).astype(np.uint8)
    base_img = cv2.add(base_img, noise)
    cv2.putText(base_img, "MUNICIPAL FIRE & RESCUE SERVICE - NOC", (60, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (40, 40, 40), 2)
    cv2.putText(base_img, "This certificate confirms inspection of premises on: 2022-04-10", (60, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2)
    cv2.putText(base_img, "Original Validity Till: 2023-04-09", (60, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2)
    
    # Save as heavily compressed baseline JPEG (Q=75)
    _, buf_base = cv2.imencode(".jpg", base_img, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    reloaded_base = cv2.imdecode(buf_base, cv2.IMREAD_COLOR)

    # Spliced uncompressed digital patch altering date to 2028-04-09
    cv2.rectangle(reloaded_base, (280, 175), (550, 220), (240, 240, 240), -1)
    cv2.putText(reloaded_base, "VALID TILL: 2028-04-09", (290, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 160), 2)
    cv2.rectangle(reloaded_base, (280, 175), (550, 220), (0, 0, 160), 2)

    # Save final image at Q=98 so the spliced patch has vastly distinct error level from background
    cv2.imwrite(str(ela_img_path), reloaded_base, [int(cv2.IMWRITE_JPEG_QUALITY), 98])

    records.append({
        "sample_id": "GT_FORENSIC_03_ELA",
        "file_path": str(ela_img_path),
        "filename": ela_img_path.name,
        "is_tampered": True,
        "expected_check": "ERROR_LEVEL_ANALYSIS",
        "expected_indicator_id": "ERROR_LEVEL_ANALYSIS_DISCREPANCY",
        "defect_description": "Digitally spliced validity date patch with high localized ELA compression discrepancy",
        "category": "positive_case"
    })

    # ------------------------------------------------------------------------
    # 4. POSITIVE CASE: Copy-Move Forgery with ORB Keypoints
    # ------------------------------------------------------------------------
    copymove_img_path = sample_dir / "gt_copymove_tampered.jpg"
    cm_base = np.ones((500, 750, 3), dtype=np.uint8) * 242
    cv2.putText(cm_base, "STATE LAND & REVENUE DEPARTMENT - RECORD OF RIGHTS", (40, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
    cv2.putText(cm_base, "Survey No: 104/2 | Total Extent: 12.50 Acres", (40, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 2)
    cv2.putText(cm_base, "Authorized Signatory & Revenue Officer Attestation", (40, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 2)

    # Draw a complex circular official seal at (120, 240)
    seal_center = (140, 240)
    cv2.circle(cm_base, seal_center, 45, (160, 20, 20), 2)
    cv2.circle(cm_base, seal_center, 38, (160, 20, 20), 1)
    cv2.putText(cm_base, "* GOVT OF KARNATAKA *", (100, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (160, 20, 20), 1)
    cv2.putText(cm_base, "SEAL OF COLLECTOR", (105, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (160, 20, 20), 1)
    cv2.putText(cm_base, "* REVENUE DEPT *", (108, 265), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (160, 20, 20), 1)

    # Copy the seal patch to another section (450, 240) -> translation dx=+310, dy=0
    seal_patch = cm_base[185:295, 85:195].copy()
    cm_base[185:295, 395:505] = seal_patch
    cv2.putText(cm_base, "DUPLICATE ATTESTATION", (400, 315), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 20, 20), 1)

    cv2.imwrite(str(copymove_img_path), cm_base, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

    records.append({
        "sample_id": "GT_FORENSIC_04_COPYMOVE",
        "file_path": str(copymove_img_path),
        "filename": copymove_img_path.name,
        "is_tampered": True,
        "expected_check": "COPY_MOVE_ORB_KEYPOINTS",
        "expected_indicator_id": "COPY_MOVE_CLONE_DETECTED",
        "defect_description": "Official revenue seal cloned across two positions on the document",
        "category": "positive_case"
    })

    # ------------------------------------------------------------------------
    # 5. POSITIVE CASE: QR Code vs OCR Reference Mismatch
    # ------------------------------------------------------------------------
    qr_pdf_path = sample_dir / "gt_qr_reference_mismatch.pdf"
    doc5 = pymupdf.open()
    page5 = doc5.new_page(width=595, height=842)
    page5.insert_text((50, 80), "KARNATAKA STATE FIRE & EMERGENCY SERVICES", fontname="helv", fontsize=14)
    page5.insert_text((50, 110), "FIRE SAFETY CLEARANCE NOC", fontname="helv", fontsize=12)
    # Printed reference says FIR/2025/98354
    page5.insert_text((50, 150), "NOC Sanction Number: FIR/2025/98354", fontname="helv", fontsize=11)
    page5.insert_text((50, 180), "Certified that the premises of Apex Institute comply with NBC standards.", fontname="helv", fontsize=10)
    page5.insert_text((50, 210), "Validity Period: 2025-06-01 to 2028-05-31", fontname="helv", fontsize=10)

    # Generate QR code pointing to a conflicting reference number: REF-TRANSPLANT-99102
    qr_img = qrcode.make("https://aicte-india.org/scrutiny/verify?ref=FIR/2021/11094&type=FireNOC")
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_bytes = qr_buf.getvalue()

    # Insert QR image onto top-right of page
    page5.insert_image(pymupdf.Rect(450, 50, 550, 150), stream=qr_bytes)
    doc5.save(str(qr_pdf_path))

    records.append({
        "sample_id": "GT_FORENSIC_05_QR_MISMATCH",
        "file_path": str(qr_pdf_path),
        "filename": qr_pdf_path.name,
        "is_tampered": True,
        "expected_check": "QR_OCR_REFERENCE_MATCH",
        "expected_indicator_id": "QR_OCR_REFERENCE_MISMATCH",
        "defect_description": "QR code payload points to FIR/2021/11094, conflicting with printed FIR/2025/98354",
        "category": "positive_case"
    })

    # ------------------------------------------------------------------------
    # 6. NEGATIVE CONTROL 1: Clean Authentic PDF with Matching QR
    # ------------------------------------------------------------------------
    clean_pdf_path = sample_dir / "gt_clean_authentic_affidavit.pdf"
    doc6 = pymupdf.open()
    page6 = doc6.new_page(width=595, height=842)
    page6.insert_text((50, 80), "AFFIDAVIT ON NON-JUDICIAL E-STAMP PAPER", fontname="helv", fontsize=14)
    page6.insert_text((50, 110), "Certificate No: AFF/2025/89955", fontname="helv", fontsize=11)
    page6.insert_text((50, 150), "I, Dr. Chairman, do hereby solemnly affirm and state on oath as under:", fontname="helv", fontsize=10)
    page6.insert_text((50, 180), "1. That the institution has fulfilled all land and building norms.", fontname="helv", fontsize=10)
    page6.insert_text((50, 210), "2. That no student shall be admitted beyond approved intake.", fontname="helv", fontsize=10)
    page6.insert_text((50, 240), "Date of Attestation: 2025-01-15 | Delhi Notary", fontname="helv", fontsize=10)

    # Matching QR code
    qr_clean = qrcode.make("https://aicte-india.org/scrutiny/verify?ref=AFF/2025/89955&type=Affidavit")
    qr_clean_buf = io.BytesIO()
    qr_clean.save(qr_clean_buf, format="PNG")
    page6.insert_image(pymupdf.Rect(450, 50, 550, 150), stream=qr_clean_buf.getvalue())

    doc6.set_metadata({
        "producer": "ReportLab PDF Library - (opensource)",
        "creator": "E-Stamp Server",
        "creationDate": "D:20250115100000+05'30'",
        "modDate": "D:20250115100000+05'30'"
    })
    doc6.save(str(clean_pdf_path))

    records.append({
        "sample_id": "GT_CONTROL_01_CLEAN_PDF",
        "file_path": str(clean_pdf_path),
        "filename": clean_pdf_path.name,
        "is_tampered": False,
        "expected_check": None,
        "expected_indicator_id": None,
        "defect_description": "Clean authentic affidavit with consistent font, matching QR, and clean metadata",
        "category": "negative_control"
    })

    # ------------------------------------------------------------------------
    # 7. NEGATIVE CONTROL 2: Clean Image Document
    # ------------------------------------------------------------------------
    clean_img_path = sample_dir / "gt_clean_authentic_scan.jpg"
    clean_img = np.ones((500, 700, 3), dtype=np.uint8) * 238
    # Uniform texture
    noise_clean = np.random.normal(0, 2, clean_img.shape).astype(np.uint8)
    clean_img = cv2.add(clean_img, noise_clean)
    cv2.putText(clean_img, "GOVERNMENT REVENUE RECORD - CERTIFIED COPY", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (30, 30, 30), 2)
    cv2.putText(clean_img, "Plot No: 44-B, Industrial Development Area", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2)
    cv2.putText(clean_img, "Sanction Order Date: 2024-03-22 | Stamp Duty Paid: Verified", (50, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 40, 40), 2)
    cv2.putText(clean_img, "Inspected by Assistant Commissioner of Land Records", (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 40, 40), 2)
    # Save once as standard JPEG
    cv2.imwrite(str(clean_img_path), clean_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

    records.append({
        "sample_id": "GT_CONTROL_02_CLEAN_IMG",
        "file_path": str(clean_img_path),
        "filename": clean_img_path.name,
        "is_tampered": False,
        "expected_check": None,
        "expected_indicator_id": None,
        "defect_description": "Clean authentic municipal scan image with homogeneous compression and no cloned elements",
        "category": "negative_control"
    })

    # ------------------------------------------------------------------------
    # 8. NEGATIVE CONTROL 3: Clean NBA Accreditation Certificate
    # ------------------------------------------------------------------------
    clean_nba_path = sample_dir / "gt_clean_nba_certificate.pdf"
    doc8 = pymupdf.open()
    page8 = doc8.new_page(width=595, height=842)
    page8.insert_text((50, 80), "NATIONAL BOARD OF ACCREDITATION", fontname="helv", fontsize=15)
    page8.insert_text((50, 110), "CERTIFICATE OF ACCREDITATION", fontname="helv", fontsize=12)
    page8.insert_text((50, 150), "File No: NBA/2025/10701", fontname="helv", fontsize=11)
    page8.insert_text((50, 180), "Programme: Computer Science & Engineering - Tier-I Accredited", fontname="helv", fontsize=10)
    page8.insert_text((50, 210), "Accreditation Status: Valid for Academic Years 2025-2028", fontname="helv", fontsize=10)
    
    # Matching QR
    qr_nba = qrcode.make("https://aicte-india.org/scrutiny/verify?ref=NBA/2025/10701&type=Accreditation")
    qr_nba_buf = io.BytesIO()
    qr_nba.save(qr_nba_buf, format="PNG")
    page8.insert_image(pymupdf.Rect(450, 50, 550, 150), stream=qr_nba_buf.getvalue())
    
    doc8.set_metadata({
        "producer": "ReportLab PDF Library - (opensource)",
        "creator": "NBA Portal",
        "creationDate": "D:20250101000000+05'30'",
        "modDate": "D:20250101000000+05'30'"
    })
    doc8.save(str(clean_nba_path))

    records.append({
        "sample_id": "GT_CONTROL_03_CLEAN_NBA",
        "file_path": str(clean_nba_path),
        "filename": clean_nba_path.name,
        "is_tampered": False,
        "expected_check": None,
        "expected_indicator_id": None,
        "defect_description": "Clean authentic NBA certificate with matching QR code and standard metadata",
        "category": "negative_control"
    })

    gt_data = {
        "catalog_version": "1.0",
        "updated_at": datetime.utcnow().isoformat(),
        "total_benchmark_samples": len(records),
        "positive_defect_cases": sum(1 for r in records if r["is_tampered"]),
        "negative_controls": sum(1 for r in records if not r["is_tampered"]),
        "samples": records
    }

    with open(GT_CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(gt_data, f, indent=2)

    return gt_data


# ============================================================================
# CALIBRATION & THRESHOLD SWEEP ENGINE
# ============================================================================

class ForensicsCalibrator:
    """
    Evaluates DocumentForensicsEngine across threshold range [0.10, 0.95]
    calculating Precision, Recall, F1, and identifying optimal operating points.
    """

    def __init__(self, engine: Optional[DocumentForensicsEngine] = None):
        self.engine = engine or document_forensics_engine

    def run_calibration(
        self,
        threshold_min: float = 0.10,
        threshold_max: float = 0.95,
        step: float = 0.05
    ) -> Dict[str, Any]:
        """
        Runs full threshold sweep against ground truth samples.
        """
        # Ensure test ground truth files exist
        if not GT_CATALOG_FILE.exists():
            gt_data = ensure_ground_truth_fixtures()
        else:
            with open(GT_CATALOG_FILE, "r", encoding="utf-8") as f:
                gt_data = json.load(f)

        samples = gt_data["samples"]

        # Run forensics once per sample and cache raw indicator results
        sample_evaluations = []
        for s in samples:
            filepath = s["file_path"]
            result = self.engine.analyze_document(filepath, filename=s["filename"])
            indicators = result.indicators

            max_score = max([i.score for i in indicators], default=0.0)
            indicator_ids = [i.indicator_id for i in indicators]

            sample_evaluations.append({
                "sample_id": s["sample_id"],
                "filename": s["filename"],
                "is_tampered": s["is_tampered"],
                "expected_indicator_id": s.get("expected_indicator_id"),
                "max_score": max_score,
                "composite_score": result.composite_risk_score,
                "indicators": indicators,
                "detected_indicator_ids": indicator_ids
            })

        # Sweep thresholds
        thresholds = []
        curr = threshold_min
        while curr <= threshold_max + 1e-6:
            thresholds.append(round(curr, 2))
            curr += step

        sweep_results = []
        best_f1 = -1.0
        optimal_threshold = 0.65

        for tau in thresholds:
            tp, fp, tn, fn = 0, 0, 0, 0

            for ev in sample_evaluations:
                # Flagged positive if composite score or max indicator score >= tau
                predicted_positive = ev["max_score"] >= tau
                actual_positive = ev["is_tampered"]

                if actual_positive and predicted_positive:
                    tp += 1
                elif not actual_positive and predicted_positive:
                    fp += 1
                elif not actual_positive and not predicted_positive:
                    tn += 1
                elif actual_positive and not predicted_positive:
                    fn += 1

            precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0

            if f1 > best_f1:
                best_f1 = f1
                optimal_threshold = tau

            sweep_results.append({
                "threshold": tau,
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "accuracy": round(accuracy, 4)
            })

        # Calculate per-check recall at optimal threshold
        per_check_stats = {}
        for ev in sample_evaluations:
            if ev["is_tampered"]:
                exp_id = ev["expected_indicator_id"]
                detected = (exp_id in ev["detected_indicator_ids"]) and (ev["max_score"] >= optimal_threshold)
                per_check_stats[exp_id] = {
                    "sample_id": ev["sample_id"],
                    "detected_at_optimal": detected,
                    "max_score": ev["max_score"],
                    "expected_indicator": exp_id
                }

        calibration_report = {
            "calibration_timestamp": datetime.utcnow().isoformat(),
            "optimal_threshold": optimal_threshold,
            "best_f1_score": round(best_f1, 4),
            "total_benchmark_samples": len(samples),
            "positive_tampered_samples": sum(1 for s in samples if s["is_tampered"]),
            "negative_clean_samples": sum(1 for s in samples if not s["is_tampered"]),
            "threshold_sweep_curve": sweep_results,
            "per_check_detection_breakdown": per_check_stats
        }

        # Save to disk
        CALIBRATION_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CALIBRATION_OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(calibration_report, f, indent=2)

        return calibration_report

    def format_calibration_table(self, report: Dict[str, Any]) -> str:
        """Formats the threshold sweep as an ASCII table."""
        curve = report["threshold_sweep_curve"]
        opt_tau = report["optimal_threshold"]

        lines = [
            "=" * 78,
            "  PRAMAAN-X DOCUMENT FORENSICS: THRESHOLD CALIBRATION SWEEP REPORT",
            "=" * 78,
            f" Optimal Threshold: {opt_tau:.2f}  |  Peak F1-Score: {report['best_f1_score']:.4f}",
            f" Benchmark Samples: {report['total_benchmark_samples']} ({report['positive_tampered_samples']} Planted Defect, {report['negative_clean_samples']} Clean Controls)",
            "-" * 78,
            f" {'Threshold':^10} | {'TP':^4} | {'FP':^4} | {'TN':^4} | {'FN':^4} | {'Precision':^10} | {'Recall':^10} | {'F1-Score':^10} | {'Status'}",
            "-" * 78
        ]

        for pt in curve:
            is_opt = "* OPTIMAL" if pt["threshold"] == opt_tau else ""
            lines.append(
                f" {pt['threshold']:^10.2f} | {pt['tp']:^4} | {pt['fp']:^4} | {pt['tn']:^4} | {pt['fn']:^4} | "
                f"{pt['precision']:^10.4f} | {pt['recall']:^10.4f} | {pt['f1_score']:^10.4f} | {is_opt}"
            )

        lines.append("-" * 78)
        lines.append("\n  PER-CHECK GROUND TRUTH DETECTION AT OPTIMAL THRESHOLD:")
        for chk, details in report["per_check_detection_breakdown"].items():
            status = "DETECTED" if details["detected_at_optimal"] else "MISSED"
            lines.append(f"  - [{status}] {chk:<35} (Score: {details['max_score']:.2f})")
        lines.append("=" * 78)
        return "\n".join(lines)


# Standalone runner
if __name__ == "__main__":
    calibrator = ForensicsCalibrator()
    rep = calibrator.run_calibration()
    print(calibrator.format_calibration_table(rep))
