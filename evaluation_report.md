# PRAMAAN-X End-to-End Pipeline Evaluation Report
**AICTE National Scrutiny & Regulatory Decision-Support Framework**  
*Evaluation Timestamp: 2026-10-27T20:01:51.319148+00:00* | *Harness Runtime: 27.12s*  
*Tuning Set: Seed 42 (100 Institutions) | Evaluation Test Set: Seed 7 (100 Institutions - Held-out)*

---

## Executive Summary

The **PRAMAAN-X Evaluation Harness** calibrated all decision thresholds strictly on the development set (Seed 42) and evaluated the complete regulatory verification pipeline across the held-out test set (Seed 7, 100 institutions, 500 statutory documents, 3,000+ faculty profiles, 400+ clean controls and hard cases). All findings were benchmarked directly against [`ground_truth.csv`](generated_data/ground_truth.csv).

| Metric Dimension | PRAMAAN-X Result | Target Benchmark | Statutory Compliance |
| :--- | :---: | :---: | :--- |
| **Field Extraction Macro F1** | **0.901** (P: 0.886, R: 0.917) | $\ge 0.900$ | Meets/Exceeds AICTE Target |
| **Defect Detection Accuracy** | **100.0%** across 20 defect types | $\ge 95.0\%$ | Perfect recall on planted breaches |
| **Anomaly Flag Precision / Recall** | **P: 0.992** / **R: 1.000** | $\ge 0.900$ | F1-Score: **0.996** |
| **False-Positive Rate (FPR)** | **3.51%** (2/57) | $\le 5.0\%$ | Low scrutiny committee burden |
| **Photo Reuse Radar Precision / Recall** | **P: 0.882** / **R: 1.000** | $\ge 0.900$ | 4 multi-college clusters detected |
| **Source-Verification Success Rate** | **100.0%** (7/7) | $\ge 98.0\%$ | API, QR, Digital Signatures |
| **Average Processing Time / Dossier** | **2.08 seconds (Measured)** | Assumption: 180 min manual | **5203x Speedup** (180.0 min saved) |
| **Alert Dispatch Latency** | **Mean: 3.2ms** (P95: 3.2ms) | $\le 500$ ms | 100% Deduplicated Dispatch |

> [!IMPORTANT]
> **Statutory Non-Punitive Safeguard Guarantee:**  
> In accordance with AICTE procedural guidelines, **every AI anomaly and defect indicator strictly displays the wording `"Indicator for review"`**. Automated rejections are strictly prohibited across all endpoints under regulatory policy and enforced via database schema constraints; adverse decisions strictly require an authorized Scrutiny Officer action with a mandatory written justification.

---

## 1. Development Set Tuning vs Held-out Test Set Evaluation

To prevent data snooping and threshold over-fitting:
- **Development Set (Seed 42)**: 100 institutions, 500 documents. Evaluated candidate parameter ranges:
  - Perceptual Hash Hamming threshold ($\le 10$)
  - CLIP Semantic Cosine Similarity ($\ge 0.85$)
  - Forensic Anomaly Decision Threshold ($0.65$)
  - Area Density Norm (10.5 sqm/student minimum standard)
- **Held-out Evaluation Test Set (Seed 7)**: 100 distinct institutions, 500 documents, clean control documents, and hard cases (blurred scans, unusual date formats). **All performance metrics in this report are evaluated strictly on Seed 7 using the locked parameters**.

---

## 2. Field-Level Extraction Performance

Evaluates PaddleOCR and rule-based boundary extraction across 6 statutory certificate fields:

| `reference_number` | 41 | 9 | 10 | **0.820** | **0.804** | **0.812** |
| `institution_name` | 37 | 23 | 0 | **0.617** | **1.000** | **0.763** |
| `validity_date` | 44 | 6 | 10 | **0.880** | **0.815** | **0.846** |
| `issue_date` | 53 | 0 | 7 | **1.000** | **0.883** | **0.938** |
| `survey_numbers` | 12 | 0 | 0 | **1.000** | **1.000** | **1.000** |
| `extent_acres` | 12 | 0 | 0 | **1.000** | **1.000** | **1.000** |
| **Overall Macro Average** | — | — | — | **0.886** | **0.917** | **0.901** |
| **Overall Micro Average** | — | — | — | **0.840** | **0.880** | **0.860** |

---

## 3. Validation Accuracy per Planted Defect Type

Evaluates detection accuracy against [`ground_truth.csv`](generated_data/ground_truth.csv) across all document, institutional twin graph, and physical infrastructure categories:

| Defect Type Identifier | Planted | Detected | Accuracy | Statutory Regulatory Action |
| :--- | :---: | :---: | :---: | :--- |
| `expired_document` | 19 | 19 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `missing_signature_field` | 22 | 22 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `wrong_institution_name` | 15 | 15 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `shared_document_reference_number` | 3 | 3 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `faculty_duplicate_across_institutions` | 21 | 21 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `area_too_small_for_intake` | 17 | 17 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `date_before_issuer_existed` | 21 | 21 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `inverted_validity_interval` | 3 | 3 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `reused_photo` | 42 | 42 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `missing_exif_metadata` | 21 | 21 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `pdf_metadata_producer_anomaly` | 3 | 3 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `font_inconsistency_in_region` | 3 | 3 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `error_level_analysis_spliced_patch` | 3 | 3 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `copymove_cloned_seal` | 3 | 3 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `qr_ocr_reference_mismatch` | 3 | 3 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `sun_shadow_angle_discrepancy` | 3 | 3 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `built_up_area_footprint_discrepancy` | 3 | 3 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `lab_equipment_inconsistent` | 2 | 2 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `mismatched_reference_number` | 20 | 20 | **100.0%** | `INDICATOR_FOR_REVIEW` |
| `edited_amount` | 13 | 13 | **100.0%** | `INDICATOR_FOR_REVIEW` |

---

## 4. Anomaly-Flag Detection & False-Positive Rate (FPR)

Evaluates the anomaly flagging engine against authentic control certificates and defective assets:

- **True Positives (TP):** 240
- **False Positives (FP):** 2
- **True Negatives (TN):** 55
- **False Negatives (FN):** 0
- **Precision:** **99.17%**
- **Recall:** **100.00%**
- **F1-Score:** **99.59%**
- **False-Positive Rate (FPR):** **3.51%** ($FP / (FP + TN)$)

---

## 5. National Photo Reuse Radar Benchmark

Cross-institution infrastructure photo comparison across exact duplicates, invariant crops/rotations, and OpenCLIP hypersphere embeddings:

- **Precision:** **88.24%**
- **Recall:** **100.00%** (Zero false negatives on shared facilities)
- **F1-Score:** **93.75%**
- **Identified Cross-Institution Clusters:** **4 Clusters**
- **Invariant Match Channels:** `exact_sha256`, `perceptual_hash_crop_rotate`, `clip_semantic_hypersphere`

---

## 6. Source-Verification Success Rate

Exercises the `IssuerConnector` framework across authoritative gateways:

- **Total Verification Queries:** 7
- **Successful Determinations:** 7
- **Success Rate:** **100.0%**
- **Mean Connector Latency:** **2.79 ms**
- **Failure Resilience:** Inconclusive outcomes automatically routed to `ManualReviewQueue`.

---

## 7. Processing Time vs Manual Baseline (Assumed)

Benchmarked against an assumed **180-minute** (3-hour) manual scrutiny baseline per institutional application dossier:

- **Automated PRAMAAN-X Processing Time (Measured):** **2.08 seconds** (0.035 minutes)
- **Manual Scrutiny Committee Baseline (Explicit Assumption):** **180.0 minutes**
- **Time Saved per Application:** **180.0 minutes**
- **Speedup Factor:** **5203x Faster**
- **Turnaround Efficiency Gain:** **99.98% reduction**

*Note: The manual baseline of 180 minutes is an explicit model assumption representing standard AICTE scrutiny committee review duration for a multi-document institutional filing, not an empirically timed study.*

---

## 8. Limitations & Production Integration Pathway

While PRAMAAN-X demonstrates state-of-the-art accuracy across regulatory compliance dimensions, several key operational limitations should be noted:

### 1. Synthetic Dataset Characteristics
All institutions, faculty rosters, land title deeds, Fire NOCs, and university affiliation certificates in the benchmark dataset are synthetically generated using ReportLab, Faker, and Augraphy scanner degradation. Although calibrated directly to the statutory clauses of the AICTE Approval Process Handbook (APH 2025-26), synthetic documents exhibit regularized font geometry and clean tabular structures that do not fully capture real-world noise (such as skewed handheld mobile phone photographs, uneven rubber-stamp ink saturation, physical crease lines, or non-standard regional formats from legacy municipal bodies).

### 2. Mocked External Issuer Gateways
External statutory verification was benchmarked against a local mock issuer gateway simulating state Fire Services, University Affiliation directorates, NBA accreditation ledgers, and State Revenue (Bhoomi) land portals. In production environments, live external state and central portals exhibit dynamic failure modes, varying network latencies, schema drift, downtime, and strict rate-limiting quotas that require caching proxies and resilient retry semantics.

### 3. Benchmark Sample Scale
The current benchmark dataset encompasses 100 technical institutions, 3,000+ faculty profiles, and 500 multi-page compliance certificates. While statistically sufficient for evaluating module precision/recall, algorithmic correctness, and multi-hop graph connectivity, nationwide AICTE deployment encompasses over 10,000 approved institutions and hundreds of thousands of faculty claims, requiring horizontal database sharding and distributed graph partitions.

### 4. Production Integration Requirements
Full real-world deployment requires integration with authoritative national digital infrastructure:
- **Authorized Government APIs**: Secure mutual TLS (mTLS) and OAuth2 integrations with State Revenue Portals (e.g. Mahabhulekh, Karnataka Bhoomi, BanglarBhumi), State Fire & Disaster Management Directorates, and State Technical University examination portals.
- **DigiLocker & National Academic Depository (NAD)**: Direct integration with DigiLocker API gateways for verifiable digital credentials, tamper-evident XML certificates, and PKI-validated digital signatures, eliminating manual PDF OCR verification where native digital credentials exist.
- **CBDT TRACES & EPFO Gateways**: Direct statutory data-sharing accords with CBDT (Form 16 / 26AS TDS deduction records) and EPFO to authenticate regular full-time faculty employment and conclusively prevent ghost faculty dual-employment across institutions.

---

## 9. Slide-Ready Presentation Charts

The following high-resolution 16:9 presentation slide charts were generated by matplotlib:

1. `1_field_extraction_metrics.png`: Precision, Recall, and F1 across all statutory document fields.
2. `2_defect_type_accuracy.png`: Accuracy percentage per defect type with 90% benchmark threshold.
3. `3_processing_time_comparison.png`: Automated runtime (2.1s measured) vs Manual Baseline (180m assumed) with 5203x callout.
4. `4_radar_and_anomaly_metrics.png`: Radar & Anomaly Precision, Recall, and False Positive Rate.
5. `5_alert_latency_distribution.png`: Latency breakdown across OCR, Forensics, Radar, and Alert Dispatch.
