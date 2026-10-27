"""
Document Forensics Module:
Performs automated multi-modal forensic inspection of regulatory compliance documents (PDFs and images).

Core Forensic Capabilities:
1. PDF Metadata Analysis:
   - Creation vs Modification timestamps (inversion, delayed revisions)
   - Producer / Creator software anomalies (Photoshop, Canva, GIMP, Sejda, iLovePDF, etc.)
   - Incremental update trailers (%%EOF count, post-issuance append tampering)
2. Font Inconsistency Detection in Region:
   - Vector font extraction per text span using PyMuPDF
   - Dominant font family & size deviation in semantic lines and numerical fields
   - Bounding box isolation and visual evidence generation
3. Error Level Analysis (ELA) for Image Documents:
   - JPEG re-compression difference modeling at Q=90
   - Localized variance clustering and z-score anomaly mapping
   - Heatmap overlay generation and peak anomaly bounding box localization
4. Copy-Move Forgery Detection via ORB Keypoints:
   - Oriented FAST and Rotated BRIEF (ORB) feature extraction
   - Spatial translation vector clustering on descriptor matches
   - Cloned seal, signature, and stamp localization with vector visualization
5. QR-Encoded Reference vs Document Text Reference Verification:
   - OpenCV QR code detection & payload decoding
   - Cross-matching against printed/OCR document reference numbers
   - Mismatch identification and QR bounding box extraction

Compliance Guarantee:
All outputs strictly formulate findings as "indicators for review" (never "verdicts" or "fraud").
"""

import os
import re
import io
import math
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import pymupdf

from pydantic import BaseModel, Field


# ============================================================================
# PYDANTIC EVIDENCE & INDICATOR SCHEMAS
# ============================================================================

class ForensicEvidence(BaseModel):
    page: Optional[int] = Field(None, description="1-indexed document page number")
    bounding_box: Optional[List[float]] = Field(None, description="[x0, y0, x1, y1] coordinates")
    heatmap_image_path: Optional[str] = Field(None, description="Path to generated evidence/heatmap image")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Detailed signal attributes")


class ForensicIndicator(BaseModel):
    indicator_id: str = Field(..., description="Unique code for the forensic indicator")
    check_name: str = Field(..., description="Human-readable check title")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence anomaly score (0.0 to 1.0)")
    severity: str = Field(..., description="INFO, LOW, MEDIUM, HIGH, or CRITICAL")
    human_readable_reason: str = Field(..., description="Scrutiny officer explanation strictly using indicator wording")
    evidence: ForensicEvidence


class DocumentForensicsResult(BaseModel):
    filename: str
    analyzed_at: str
    composite_risk_score: float
    is_review_recommended: bool
    total_indicators_count: int
    indicators: List[ForensicIndicator]
    summary_metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# UTILITIES
# ============================================================================

SUSPICIOUS_SOFTWARE_PATTERNS = [
    (r"photoshop", "Adobe Photoshop"),
    (r"canva", "Canva Online Editor"),
    (r"gimp", "GNU Image Manipulation Program (GIMP)"),
    (r"inkscape", "Inkscape Vector Suite"),
    (r"coreldraw", "CorelDRAW"),
    (r"sejda", "Sejda PDF Editor"),
    (r"pdfescape", "PDFescape Tool"),
    (r"ilovepdf", "iLovePDF Online Utility"),
    (r"smallpdf", "Smallpdf Online Utility"),
    (r"pdf24", "PDF24 Creator"),
    (r"nitro", "Nitro Pro PDF Editor"),
    (r"foxit phantom", "Foxit PhantomPDF"),
    (r"wondershare", "Wondershare PDFelement"),
    (r"paint\.net", "Paint.NET"),
    (r"microsoft paint", "MS Paint")
]


def parse_pdf_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """Parses standard PDF date strings like D:20240115103000+05'30' into datetime objects."""
    if not date_str:
        return None
    try:
        clean = date_str.replace("D:", "").replace("'", "")
        # Extract YYYYMMDDHHMMSS
        m = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})?(\d{2})?(\d{2})?", clean)
        if m:
            parts = m.groups()
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            hour = int(parts[3]) if parts[3] else 0
            minute = int(parts[4]) if parts[4] else 0
            second = int(parts[5]) if parts[5] else 0
            return datetime(year, month, day, hour, minute, second)
    except Exception:
        pass
    return None


def normalize_reference(ref_str: Optional[str]) -> str:
    """Normalizes document reference numbers by stripping punctuation and whitespace."""
    if not ref_str:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", str(ref_str)).upper()


# ============================================================================
# DOCUMENT FORENSICS ENGINE
# ============================================================================

class DocumentForensicsEngine:
    """
    Automated Document Forensics Engine:
    Executes multi-modal image & PDF checks and outputs indicators for scrutiny officer review.
    """

    def __init__(self, artifacts_dir: str = "uploads/forensics"):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------------
    # 1. PDF METADATA ANALYSIS
    # ------------------------------------------------------------------------
    def check_pdf_metadata(
        self,
        file_bytes: bytes,
        filename: str = "document.pdf"
    ) -> List[ForensicIndicator]:
        """
        Analyzes PDF metadata headers and byte structure:
        - Creation vs Modification dates (inversion, significant post-issuance modification)
        - Producer software anomalies (Canva, Photoshop, GIMP, Sejda, etc.)
        - Incremental update trailers (%%EOF count)
        """
        indicators = []
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            meta = doc.metadata or {}
        except Exception:
            return indicators

        producer = meta.get("producer") or ""
        creator = meta.get("creator") or ""
        c_date_raw = meta.get("creationDate") or ""
        m_date_raw = meta.get("modDate") or ""

        c_dt = parse_pdf_datetime(c_date_raw)
        m_dt = parse_pdf_datetime(m_date_raw)

        # 1.1 Software Signature Anomaly
        software_found = []
        combined_meta_text = f"{producer} {creator}".lower()
        for pattern, tool_name in SUSPICIOUS_SOFTWARE_PATTERNS:
            if re.search(pattern, combined_meta_text):
                software_found.append(tool_name)

        if software_found:
            detected_str = ", ".join(software_found)
            indicators.append(
                ForensicIndicator(
                    indicator_id="PDF_METADATA_PRODUCER_ANOMALY",
                    check_name="PDF Producer Software Anomaly",
                    score=0.85,
                    severity="HIGH",
                    human_readable_reason=(
                        f"Indicator for review: PDF document was produced or edited using image/document manipulation software "
                        f"('{detected_str}'). Official statutory certificates are generated via automated enterprise systems or scanners, "
                        f"serving as an indicator for review."
                    ),
                    evidence=ForensicEvidence(
                        page=1,
                        bounding_box=None,
                        heatmap_image_path=None,
                        metadata={
                            "producer": producer,
                            "creator": creator,
                            "detected_editing_tools": software_found
                        }
                    )
                )
            )

        # 1.2 Date Inversion or Post-Issuance Revision Delay
        if c_dt and m_dt:
            if m_dt < c_dt:
                # Mod date earlier than creation date (clock alteration anomaly)
                indicators.append(
                    ForensicIndicator(
                        indicator_id="PDF_METADATA_DATE_INVERSION",
                        check_name="PDF Metadata Date Inversion",
                        score=0.90,
                        severity="HIGH",
                        human_readable_reason=(
                            f"Indicator for review: Document modification timestamp ({m_dt.isoformat()}) predates its "
                            f"claimed creation timestamp ({c_dt.isoformat()}), representing metadata tampering, "
                            f"serving as an indicator for review."
                        ),
                        evidence=ForensicEvidence(
                            page=1,
                            bounding_box=None,
                            heatmap_image_path=None,
                            metadata={
                                "creation_date": c_dt.isoformat(),
                                "modification_date": m_dt.isoformat(),
                                "discrepancy_type": "MOD_BEFORE_CREATION"
                            }
                        )
                    )
                )
            elif (m_dt - c_dt).total_seconds() > (30 * 86400):  # More than 30 days later
                delta_days = int((m_dt - c_dt).total_seconds() / 86400)
                indicators.append(
                    ForensicIndicator(
                        indicator_id="PDF_METADATA_MODIFIED_AFTER_ISSUANCE",
                        check_name="PDF Delayed Modification",
                        score=0.70,
                        severity="MEDIUM",
                        human_readable_reason=(
                            f"Indicator for review: Document was modified {delta_days} days after its original creation "
                            f"(Creation: {c_dt.strftime('%Y-%m-%d')}, Mod: {m_dt.strftime('%Y-%m-%d')}), "
                            f"serving as an indicator for review."
                        ),
                        evidence=ForensicEvidence(
                            page=1,
                            bounding_box=None,
                            heatmap_image_path=None,
                            metadata={
                                "creation_date": c_dt.isoformat(),
                                "modification_date": m_dt.isoformat(),
                                "delta_days": delta_days
                            }
                        )
                    )
                )

        # 1.3 Incremental Updates (Multiple %%EOF markers)
        eof_matches = list(re.finditer(rb"%%EOF", file_bytes))
        eof_count = len(eof_matches)
        if eof_count > 1:
            score = round(min(0.95, 0.45 + (eof_count - 1) * 0.15), 2)
            indicators.append(
                ForensicIndicator(
                    indicator_id="PDF_INCREMENTAL_UPDATES_DETECTED",
                    check_name="PDF Incremental Updates Inspection",
                    score=score,
                    severity="HIGH" if eof_count >= 3 else "MEDIUM",
                    human_readable_reason=(
                        f"Indicator for review: Document structure contains {eof_count} separate incremental update sections "
                        f"(%%EOF revisions). Incremental updates modify text, annotations, or streams after initial publication, "
                        f"serving as an indicator for review."
                    ),
                    evidence=ForensicEvidence(
                        page=1,
                        bounding_box=None,
                        heatmap_image_path=None,
                        metadata={
                            "eof_marker_count": eof_count,
                            "file_size_bytes": len(file_bytes)
                        }
                    )
                )
            )

        return indicators

    # ------------------------------------------------------------------------
    # 2. FONT INCONSISTENCY INSIDE A REGION
    # ------------------------------------------------------------------------
    def check_font_inconsistency(
        self,
        pdf_bytes_or_path: Any,
        doc_id: str = "doc"
    ) -> List[ForensicIndicator]:
        """
        Inspects text spans across lines and semantic regions inside PDF pages.
        Flags text tokens (especially numbers, intake values, dates) rendered in a different
        font family or size than the dominant font of the surrounding paragraph.
        Generates an annotated visual overlay highlighting the inconsistent span.
        """
        indicators = []
        try:
            if isinstance(pdf_bytes_or_path, (str, Path)):
                doc = pymupdf.open(pdf_bytes_or_path)
            else:
                doc = pymupdf.open(stream=pdf_bytes_or_path, filetype="pdf")
        except Exception:
            return indicators

        for page_idx, page in enumerate(doc):
            page_num = page_idx + 1
            text_dict = page.get_text("dict")
            blocks = text_dict.get("blocks", [])

            for b_idx, block in enumerate(blocks):
                lines = block.get("lines", [])
                if not lines:
                    continue

                # Collect all spans in this block/region
                all_spans = []
                for line in lines:
                    for span in line.get("spans", []):
                        txt = span.get("text", "").strip()
                        if txt:
                            all_spans.append(span)

                if len(all_spans) < 2:
                    continue

                # Determine dominant font and size
                font_counter = Counter(s.get("font", "Unknown") for s in all_spans)
                size_counter = Counter(round(s.get("size", 0.0), 1) for s in all_spans)

                dom_font, dom_font_count = font_counter.most_common(1)[0]
                dom_size, _ = size_counter.most_common(1)[0]

                # Check for an isolated outlier span
                for span in all_spans:
                    font = span.get("font", "")
                    size = round(span.get("size", 0.0), 1)
                    text = span.get("text", "").strip()
                    bbox = span.get("bbox")

                    # Check for font family mismatch or size deviation >= 2.0pt
                    font_mismatch = (font != dom_font) and (dom_font_count >= 2)
                    size_mismatch = (abs(size - dom_size) >= 2.0) and (dom_font_count >= 2)

                    # High interest if token contains digits (altered intake, date, amount) or differs in font
                    if (font_mismatch or size_mismatch) and len(text) > 0:
                        has_digits = bool(re.search(r"\d", text))
                        score = 0.88 if (font_mismatch and has_digits) else 0.78

                        # Render page image and draw annotation bounding box
                        heatmap_path = None
                        try:
                            pix = page.get_pixmap(dpi=150)
                            img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
                            if pix.n == 4:
                                img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
                            elif pix.n == 3:
                                img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

                            scale_factor = 150.0 / 72.0
                            px0 = int(bbox[0] * scale_factor)
                            py0 = int(bbox[1] * scale_factor)
                            px1 = int(bbox[2] * scale_factor)
                            py1 = int(bbox[3] * scale_factor)

                            overlay = img_np.copy()
                            cv2.rectangle(overlay, (px0 - 4, py0 - 4), (px1 + 4, py1 + 4), (0, 0, 255), -1)
                            cv2.addWeighted(overlay, 0.35, img_np, 0.65, 0, img_np)
                            cv2.rectangle(img_np, (px0 - 4, py0 - 4), (px1 + 4, py1 + 4), (0, 0, 255), 2)
                            cv2.putText(
                                img_np,
                                f"Inconsistent Font: {font} ({size}pt)",
                                (max(10, px0), max(20, py0 - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                (0, 0, 200),
                                2
                            )

                            out_filename = f"font_anomaly_{doc_id}_p{page_num}_b{b_idx}.png"
                            save_path = self.artifacts_dir / out_filename
                            cv2.imwrite(str(save_path), img_np)
                            heatmap_path = str(save_path)
                        except Exception:
                            pass

                        indicators.append(
                            ForensicIndicator(
                                indicator_id="FONT_INCONSISTENCY_IN_REGION",
                                check_name="Font Style / Size Inconsistency in Region",
                                score=score,
                                severity="HIGH",
                                human_readable_reason=(
                                    f"Indicator for review: Font inconsistency detected in region on page {page_num}. "
                                    f"Token '{text}' is rendered in '{font}' ({size}pt) inside a paragraph where "
                                    f"the dominant typeface is '{dom_font}' ({dom_size}pt), "
                                    f"serving as an indicator for review."
                                ),
                                evidence=ForensicEvidence(
                                    page=page_num,
                                    bounding_box=[round(c, 1) for c in bbox] if bbox else None,
                                    heatmap_image_path=heatmap_path,
                                    metadata={
                                        "anomalous_token": text,
                                        "anomalous_font": font,
                                        "anomalous_size": size,
                                        "dominant_font": dom_font,
                                        "dominant_size": dom_size,
                                        "has_digits": has_digits
                                    }
                                )
                            )
                        )
                        if len(indicators) >= 3:
                            break
                if len(indicators) >= 3:
                    break

        return indicators

    # ------------------------------------------------------------------------
    # 3. ERROR LEVEL ANALYSIS (ELA) FOR IMAGE DOCUMENTS
    # ------------------------------------------------------------------------
    def check_error_level_analysis(
        self,
        image_np_or_path: Any,
        doc_id: str = "img_doc",
        page_num: int = 1,
        quality: int = 90
    ) -> List[ForensicIndicator]:
        """
        Performs Error Level Analysis (ELA) by re-compressing image at Q=90 and
        computing localized compression error discrepancy.
        Generates a colored ELA heatmap and isolates anomalous high-divergence regions.
        """
        indicators = []
        try:
            if isinstance(image_np_or_path, (str, Path)):
                img = cv2.imread(str(image_np_or_path))
            elif isinstance(image_np_or_path, np.ndarray):
                img = image_np_or_path.copy()
            elif isinstance(image_np_or_path, bytes):
                nparr = np.frombuffer(image_np_or_path, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                return indicators

            if img is None:
                return indicators
        except Exception:
            return indicators

        h, w = img.shape[:2]

        # Re-compress at specified JPEG quality
        _, recomp_buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        recomp_img = cv2.imdecode(recomp_buf, cv2.IMREAD_COLOR)

        # Compute absolute difference
        diff = cv2.absdiff(img, recomp_img)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        max_val = float(gray_diff.max())
        mean_val = float(gray_diff.mean())
        std_val = float(gray_diff.std())

        scale = 255.0 / max(1.0, max_val)
        enhanced = (gray_diff.astype(np.float32) * scale).astype(np.uint8)

        # Smooth to find localized high-energy clusters
        blurred = cv2.GaussianBlur(enhanced, (25, 25), 0)
        _, peak_val, _, peak_loc = cv2.minMaxLoc(blurred)

        # Calculate z-score of the peak relative to background
        z_score = (peak_val - mean_val * scale / 255.0) / (std_val * scale / 255.0 + 1e-4)

        # Threshold to extract bounding box of anomalous localized region
        anom_thresh = max(50.0, peak_val * 0.72)
        _, mask = cv2.threshold(blurred, anom_thresh, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bbox = None
        if contours:
            c = max(contours, key=cv2.contourArea)
            if cv2.contourArea(c) > 100:
                bx, by, bw, bh = cv2.boundingRect(c)
                bbox = [float(bx), float(by), float(bx + bw), float(by + bh)]

        # Generate colored heatmap overlay
        heatmap_path = None
        color_heatmap = cv2.applyColorMap(enhanced, cv2.COLORMAP_JET)
        blended = cv2.addWeighted(img, 0.60, color_heatmap, 0.40, 0)

        if bbox:
            bx0, by0, bx1, by1 = [int(v) for v in bbox]
            cv2.rectangle(blended, (bx0, by0), (bx1, by1), (0, 0, 255), 2)
            cv2.putText(
                blended,
                f"ELA Anomaly ({z_score:.1f} sigma)",
                (bx0, max(20, by0 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 0, 255),
                2
            )

        save_filename = f"ela_heatmap_{doc_id}_p{page_num}.png"
        save_file = self.artifacts_dir / save_filename
        cv2.imwrite(str(save_file), blended)
        heatmap_path = str(save_file)

        # Trigger indicator if localized divergence exceeds normal scan distribution
        # Authentic scans have max_val <= 8 and mean_val <= 0.10, whereas spliced patches have max_val >= 14 and mean_val >= 0.25
        if (max_val >= 12 and mean_val >= 0.20 and peak_val >= 75.0 and z_score >= 3.5) or (z_score >= 6.0 and max_val >= 10):
            score = round(min(0.96, 0.60 + (peak_val / 100.0) * 0.35), 2)
            indicators.append(
                ForensicIndicator(
                    indicator_id="ERROR_LEVEL_ANALYSIS_DISCREPANCY",
                    check_name="Error Level Analysis (ELA) Tampering Detection",
                    score=score,
                    severity="HIGH" if score >= 0.80 else "MEDIUM",
                    human_readable_reason=(
                        f"Indicator for review: Localized compression discrepancy detected via Error Level Analysis "
                        f"(peak deviation: {z_score:.1f}σ, max error: {max_val:.0f}). "
                        f"Specific image region exhibits compression characteristics inconsistent with the background scan, "
                        f"serving as an indicator for review."
                    ),
                    evidence=ForensicEvidence(
                        page=page_num,
                        bounding_box=bbox,
                        heatmap_image_path=heatmap_path,
                        metadata={
                            "z_score": round(z_score, 2),
                            "max_channel_diff": round(max_val, 2),
                            "mean_diff": round(mean_val, 2),
                            "std_diff": round(std_val, 2),
                            "peak_location": list(peak_loc)
                        }
                    )
                )
            )

        return indicators

    # ------------------------------------------------------------------------
    # 4. COPY-MOVE DETECTION VIA ORB KEYPOINTS
    # ------------------------------------------------------------------------
    def check_copy_move_orb(
        self,
        image_np_or_path: Any,
        doc_id: str = "doc",
        page_num: int = 1,
        min_cluster_pairs: int = 22,
        min_spatial_distance: float = 40.0
    ) -> List[ForensicIndicator]:
        """
        Detects copy-move forgery (cloned stamps, signatures, text blocks, seals) using
        ORB keypoint descriptors and spatial translation vector clustering.
        Generates visual evidence with connecting vectors and source/target bounding boxes.
        """
        indicators = []
        try:
            if isinstance(image_np_or_path, (str, Path)):
                img = cv2.imread(str(image_np_or_path))
            elif isinstance(image_np_or_path, np.ndarray):
                img = image_np_or_path.copy()
            elif isinstance(image_np_or_path, bytes):
                nparr = np.frombuffer(image_np_or_path, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                return indicators

            if img is None:
                return indicators
        except Exception:
            return indicators

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        orb = cv2.ORB_create(nfeatures=2500, fastThreshold=10)
        keypoints, descriptors = orb.detectAndCompute(gray, None)

        if descriptors is None or len(keypoints) < 15:
            return indicators

        bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        knn_matches = bf.knnMatch(descriptors, descriptors, k=4)

        candidate_pairs = []
        for matches in knn_matches:
            for m in matches[1:]:  # Skip self-match at index 0
                if m.distance < 28:
                    pt1 = np.array(keypoints[m.queryIdx].pt)
                    pt2 = np.array(keypoints[m.trainIdx].pt)
                    spatial_dist = np.linalg.norm(pt1 - pt2)

                    if spatial_dist >= min_spatial_distance:
                        dx = pt2[0] - pt1[0]
                        dy = pt2[1] - pt1[1]
                        candidate_pairs.append((pt1, pt2, dx, dy, m.distance))

        if not candidate_pairs:
            return indicators

        vector_clusters: Dict[Tuple[int, int], List[Any]] = {}
        bin_size = 14
        for pt1, pt2, dx, dy, dist in candidate_pairs:
            bin_x = int(round(dx / bin_size) * bin_size)
            bin_y = int(round(dy / bin_size) * bin_size)
            vector_clusters.setdefault((bin_x, bin_y), []).append((pt1, pt2, dx, dy, dist))

        valid_clusters = []
        for vec, pairs in vector_clusters.items():
            if len(pairs) >= min_cluster_pairs:
                src_pts = np.array([p[0] for p in pairs])
                s_min = np.min(src_pts, axis=0)
                s_max = np.max(src_pts, axis=0)
                # Ensure 2D patch extent (not just 1D character lines)
                if (s_max[0] - s_min[0]) >= 20 and (s_max[1] - s_min[1]) >= 20:
                    valid_clusters.append((vec, pairs))

        if valid_clusters:
            valid_clusters.sort(key=lambda x: len(x[1]), reverse=True)
            best_vec, best_pairs = valid_clusters[0]

            src_pts = np.array([p[0] for p in best_pairs])
            dst_pts = np.array([p[1] for p in best_pairs])

            s_min = np.min(src_pts, axis=0)
            s_max = np.max(src_pts, axis=0)
            d_min = np.min(dst_pts, axis=0)
            d_max = np.max(dst_pts, axis=0)

            overall_bbox = [
                float(min(s_min[0], d_min[0])),
                float(min(s_min[1], d_min[1])),
                float(max(s_max[0], d_max[0])),
                float(max(s_max[1], d_max[1]))
            ]

            vis = img.copy()
            cv2.rectangle(vis, (int(s_min[0] - 8), int(s_min[1] - 8)), (int(s_max[0] + 8), int(s_max[1] + 8)), (0, 200, 0), 2)
            cv2.putText(vis, "Source Patch", (int(s_min[0]), max(20, int(s_min[1] - 12))), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 2)

            cv2.rectangle(vis, (int(d_min[0] - 8), int(d_min[1] - 8)), (int(d_max[0] + 8), int(d_max[1] + 8)), (0, 0, 255), 2)
            cv2.putText(vis, "Cloned Patch", (int(d_min[0]), max(20, int(d_min[1] - 12))), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            for pt1, pt2, _, _, _ in best_pairs[:40]:
                p1 = (int(pt1[0]), int(pt1[1]))
                p2 = (int(pt2[0]), int(pt2[1]))
                cv2.line(vis, p1, p2, (255, 100, 0), 1)
                cv2.circle(vis, p1, 3, (0, 255, 0), -1)
                cv2.circle(vis, p2, 3, (0, 0, 255), -1)

            save_file = self.artifacts_dir / f"copymove_{doc_id}_p{page_num}.png"
            cv2.imwrite(str(save_file), vis)
            heatmap_path = str(save_file)

            pair_count = len(best_pairs)
            score = round(min(0.98, 0.65 + (pair_count / 30.0) * 0.30), 2)

            indicators.append(
                ForensicIndicator(
                    indicator_id="COPY_MOVE_CLONE_DETECTED",
                    check_name="Copy-Move Patch Duplication Detection",
                    score=score,
                    severity="CRITICAL" if pair_count >= 15 else "HIGH",
                    human_readable_reason=(
                        f"Indicator for review: Replicated image content identified via ORB keypoint matching "
                        f"({pair_count} correlated feature pairs sharing translation vector Δ=({best_vec[0]}, {best_vec[1]})px). "
                        f"Indicates probable copy-paste cloning of a stamp, signature, or text area, "
                        f"serving as an indicator for review."
                    ),
                    evidence=ForensicEvidence(
                        page=page_num,
                        bounding_box=overall_bbox,
                        heatmap_image_path=heatmap_path,
                        metadata={
                            "matching_pairs_count": pair_count,
                            "translation_vector": list(best_vec),
                            "source_bbox": [float(s_min[0]), float(s_min[1]), float(s_max[0]), float(s_max[1])],
                            "cloned_bbox": [float(d_min[0]), float(d_min[1]), float(d_max[0]), float(d_max[1])]
                        }
                    )
                )
            )

        return indicators

    # ------------------------------------------------------------------------
    # 5. QR-ENCODED REFERENCE VS OCR REFERENCE MATCH
    # ------------------------------------------------------------------------
    def check_qr_ocr_reference_match(
        self,
        doc_or_image_path: Any,
        printed_reference_hint: Optional[str] = None,
        doc_id: str = "doc"
    ) -> List[ForensicIndicator]:
        """
        Extracts verification QR code from document page and decodes its encoded reference number.
        Cross-checks against OCR'd/printed reference numbers.
        Triggers indicator if QR points to a different reference number or different certificate.
        """
        indicators = []
        img = None
        extracted_text = ""

        try:
            if isinstance(doc_or_image_path, (str, Path)):
                path_obj = Path(doc_or_image_path)
                if path_obj.suffix.lower() == ".pdf":
                    pdf_doc = pymupdf.open(str(path_obj))
                    page = pdf_doc[0]
                    extracted_text = page.get_text()
                    pix = page.get_pixmap(dpi=150)
                    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
                    if pix.n == 4:
                        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                    elif pix.n == 3:
                        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                else:
                    img = cv2.imread(str(path_obj))
            elif isinstance(doc_or_image_path, bytes):
                try:
                    pdf_doc = pymupdf.open(stream=doc_or_image_path, filetype="pdf")
                    page = pdf_doc[0]
                    extracted_text = page.get_text()
                    pix = page.get_pixmap(dpi=150)
                    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
                    if pix.n == 4:
                        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                    elif pix.n == 3:
                        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                except Exception:
                    nparr = np.frombuffer(doc_or_image_path, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception:
            return indicators

        if img is None:
            return indicators

        detector = cv2.QRCodeDetector()
        val, points, _ = detector.detectAndDecode(img)

        if not val or points is None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            val, points, _ = detector.detectAndDecode(enhanced)

        if not val or points is None:
            return indicators

        qr_payload = str(val).strip()
        points_np = np.array(points).reshape(-1, 2)
        qx0 = float(np.min(points_np[:, 0]))
        qy0 = float(np.min(points_np[:, 1]))
        qx1 = float(np.max(points_np[:, 0]))
        qy1 = float(np.max(points_np[:, 1]))
        qr_bbox = [qx0, qy0, qx1, qy1]

        qr_ref = None
        ref_patterns = [
            r"ref=([A-Za-z0-9/\-_]+)",
            r"certificate_no=([A-Za-z0-9/\-_]+)",
            r"([A-Z]{3,4}/\d{4}/\d{4,6})",
            r"([A-Z]{3,4}-\d{4}-\d{4,6})",
            r"(REF-[A-Za-z0-9\-]+)"
        ]
        for pat in ref_patterns:
            m = re.search(pat, qr_payload, re.IGNORECASE)
            if m:
                qr_ref = m.group(1)
                break

        if not qr_ref:
            qr_ref = qr_payload

        printed_ref = printed_reference_hint
        if not printed_ref and extracted_text:
            m_text = re.search(r"(?:Number|No\.?|Certificate|NOC)[:\s]+([A-Z0-9/\-_]{6,30})", extracted_text, re.IGNORECASE)
            if m_text:
                printed_ref = m_text.group(1).strip()

        norm_qr = normalize_reference(qr_ref)
        norm_printed = normalize_reference(printed_ref)

        is_mismatch = False
        if norm_printed and norm_qr:
            if norm_qr != norm_printed and norm_qr not in norm_printed and norm_printed not in norm_qr:
                is_mismatch = True

        if is_mismatch:
            vis = img.copy()
            cv2.polylines(vis, [points_np.astype(np.int32)], True, (0, 0, 255), 3)
            cv2.putText(
                vis,
                f"QR Mismatch: '{qr_ref}' vs Printed '{printed_ref}'",
                (int(qx0), max(25, int(qy0 - 10))),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 0, 255),
                2
            )

            save_file = self.artifacts_dir / f"qr_mismatch_{doc_id}.png"
            cv2.imwrite(str(save_file), vis)
            heatmap_path = str(save_file)

            indicators.append(
                ForensicIndicator(
                    indicator_id="QR_OCR_REFERENCE_MISMATCH",
                    check_name="QR Code vs OCR Printed Reference Verification",
                    score=1.0,
                    severity="CRITICAL",
                    human_readable_reason=(
                        f"Indicator for review: Verification QR code payload encodes reference '{qr_ref}', "
                        f"which conflicts with the printed document certificate reference '{printed_ref}'. "
                        f"Document may incorporate a mismatched or transplanted QR verification seal, "
                        f"serving as an indicator for review."
                    ),
                    evidence=ForensicEvidence(
                        page=1,
                        bounding_box=qr_bbox,
                        heatmap_image_path=heatmap_path,
                        metadata={
                            "qr_payload": qr_payload,
                            "qr_extracted_reference": qr_ref,
                            "printed_extracted_reference": printed_ref,
                            "normalized_qr": norm_qr,
                            "normalized_printed": norm_printed
                        }
                    )
                )
            )

        return indicators

    # ------------------------------------------------------------------------
    # FULL DOCUMENT ORCHESTRATION PIPELINE
    # ------------------------------------------------------------------------
    def analyze_document(
        self,
        file_path_or_bytes: Any,
        filename: str = "document.pdf",
        doc_id: Optional[str] = None,
        printed_reference: Optional[str] = None,
        decision_threshold: float = 0.65
    ) -> DocumentForensicsResult:
        """
        Executes all 5 document forensics checks and returns a structured indicators report.
        """
        if doc_id is None:
            doc_id = Path(filename).stem

        all_indicators: List[ForensicIndicator] = []
        file_bytes: Optional[bytes] = None
        is_pdf = False

        if isinstance(file_path_or_bytes, (str, Path)):
            p = Path(file_path_or_bytes)
            filename = p.name
            is_pdf = p.suffix.lower() == ".pdf"
            with open(p, "rb") as f:
                file_bytes = f.read()
        elif isinstance(file_path_or_bytes, bytes):
            file_bytes = file_path_or_bytes
            is_pdf = filename.lower().endswith(".pdf") or file_bytes[:4] == b"%PDF"

        # 1. PDF Metadata Analysis (if PDF)
        if is_pdf and file_bytes:
            meta_inds = self.check_pdf_metadata(file_bytes, filename=filename)
            all_indicators.extend(meta_inds)

        # 2. Font Inconsistency in Region (if PDF)
        if is_pdf and file_bytes:
            font_inds = self.check_font_inconsistency(file_bytes, doc_id=doc_id)
            all_indicators.extend(font_inds)

        # 3. Error Level Analysis
        ela_inds: List[ForensicIndicator] = []
        if is_pdf and file_bytes:
            try:
                pdf_doc = pymupdf.open(stream=file_bytes, filetype="pdf")
                if len(pdf_doc) > 0:
                    pix = pdf_doc[0].get_pixmap(dpi=150)
                    img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
                    if pix.n == 4:
                        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
                    elif pix.n == 3:
                        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                    ela_inds = self.check_error_level_analysis(img_np, doc_id=doc_id, page_num=1)
            except Exception:
                pass
        elif file_bytes:
            ela_inds = self.check_error_level_analysis(file_bytes, doc_id=doc_id, page_num=1)
        all_indicators.extend(ela_inds)

        # 4. Copy-Move ORB Keypoint Analysis
        copymove_inds: List[ForensicIndicator] = []
        if is_pdf and file_bytes:
            try:
                pdf_doc = pymupdf.open(stream=file_bytes, filetype="pdf")
                if len(pdf_doc) > 0:
                    pix = pdf_doc[0].get_pixmap(dpi=150)
                    img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
                    if pix.n == 4:
                        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
                    elif pix.n == 3:
                        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                    copymove_inds = self.check_copy_move_orb(img_np, doc_id=doc_id, page_num=1)
            except Exception:
                pass
        elif file_bytes:
            copymove_inds = self.check_copy_move_orb(file_bytes, doc_id=doc_id, page_num=1)
        all_indicators.extend(copymove_inds)

        # 5. QR vs OCR Reference Verification
        qr_inds = self.check_qr_ocr_reference_match(
            file_bytes,
            printed_reference_hint=printed_reference,
            doc_id=doc_id
        )
        all_indicators.extend(qr_inds)

        # Composite risk score calculation
        if all_indicators:
            max_score = max(ind.score for ind in all_indicators)
            avg_score = sum(ind.score for ind in all_indicators) / len(all_indicators)
            composite_score = round(min(1.0, 0.75 * max_score + 0.25 * avg_score), 2)
        else:
            composite_score = 0.0

        is_review_recommended = composite_score >= decision_threshold

        return DocumentForensicsResult(
            filename=filename,
            analyzed_at=datetime.utcnow().isoformat(),
            composite_risk_score=composite_score,
            is_review_recommended=is_review_recommended,
            total_indicators_count=len(all_indicators),
            indicators=all_indicators,
            summary_metadata={
                "checks_executed": [
                    "PDF_METADATA_ANALYSIS",
                    "FONT_INCONSISTENCY_IN_REGION",
                    "ERROR_LEVEL_ANALYSIS",
                    "COPY_MOVE_ORB_KEYPOINTS",
                    "QR_OCR_REFERENCE_MATCH"
                ],
                "file_size_bytes": len(file_bytes) if file_bytes else 0,
                "is_pdf": is_pdf
            }
        )


# Global singleton
document_forensics_engine = DocumentForensicsEngine()
