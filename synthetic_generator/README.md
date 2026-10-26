# PRAMAAN-X Synthetic Data & Benchmark Defect Generator (Phase 2)

This module generates authentic, high-fidelity synthetic regulatory datasets for technical institutions applying for Extension of Approval (EoA) under AICTE guidelines. It systematically plants ground-truth defects across documents, faculty rosters, infrastructure photos, and institutional profiles for rigorous evaluation of PRAMAAN-X's AI decision-support algorithms.

---

## 📁 Output Folder Structure

When the generator runs, it produces the following structured output directory:

```
generated_data/
├── ground_truth.csv                 # Master ground truth ledger of every planted defect
├── institutions.json                # Institutional profiles (intake, built-up area, GPS, trust)
├── faculty.json                     # Generated faculty rosters (cadre, masked PAN/Aadhaar)
├── documents_catalog.json           # Catalog of all generated PDFs and metadata
│
├── documents/                       # Generated ReportLab compliance PDFs
│   ├── INST_001/
│   │   ├── AFF_INST_001.pdf         # Affidavit on Non-Judicial Stamp Paper (with QR code)
│   │   ├── NOC_INST_001.pdf         # State Government / University NOC (with QR code)
│   │   ├── NBA_INST_001.pdf         # Accreditation Certificate (with QR code)
│   │   ├── FIRE_INST_001.pdf        # Fire Safety Clearance Certificate (with QR code)
│   │   └── LAND_INST_001.pdf        # Registered 30-Year Leasehold Document (with QR code)
│   ├── INST_002/
│   │   └── ...
│   └── INST_N/
│
└── photos/                          # Infrastructure photo variants (Prompt 2.2)
    ├── INST_001_computer_lab_original.jpg        # Genuine photo with Apple EXIF + GPS
    ├── INST_002_computer_lab_exact_duplicate.jpg # Verbatim clone assigned to Inst B
    ├── INST_003_computer_lab_near_duplicate.jpg  # Cropped, rotated, brightened near-duplicate
    ├── INST_004_computer_lab_exif_stripped.jpg   # EXIF metadata scrubbed
    └── ...
```

---

## 🚀 CLI Usage & Commands

### 1. Generate Institutional Dossiers & PDFs (Prompt 2.1)
```bash
python -m synthetic_generator.generate_synthetic_data --institutions 100 --defect-rate 0.20 --seed 42 --output-dir generated_data
```

#### Arguments:
- `--institutions N`: Number of institutions to generate (e.g. `10`, `50`, `100`, `300`).
- `--defect-rate F`: Target probability of planting defects across documents and profiles (default: `0.2` = 20%).
- `--seed S`: Deterministic random seed for reproducibility (default: `42`).
- `--institutions-csv PATH`: Optional path to custom CSV of base institution names and states.
- `--output-dir PATH`: Directory where generated PDFs and catalogs will be saved (default: `generated_data`).

### 2. Generate Infrastructure Photo Variants & EXIF (Prompt 2.2)
```bash
python -m synthetic_generator.generate_photo_variants --output-dir generated_data/photos --ground-truth generated_data/ground_truth.csv
```

#### Arguments:
- `--input-photos-dir PATH`: Optional path to folder of real classroom/lab/library photos (if omitted, high-resolution synthetic infrastructure photos are rendered).
- `--output-dir PATH`: Destination folder for photo variants.
- `--ground-truth PATH`: Path to ground truth CSV to append image defect labels.

---

## 🎯 Planted Defect Types & Ground Truth Taxonomy

Every defect planted by the generator is logged into `ground_truth.csv` with the following columns:
`institution_id`, `institution_name`, `document_id`, `document_type`, `defect_type`, `details`, `severity`, `expected_regulatory_flag`, `timestamp`.

| Defect Type | Target Surface | Planted Discrepancy & Evaluation Target | Expected AICTE Flag |
| :--- | :--- | :--- | :--- |
| `expired_document` | PDF Certificate | Certificate validity set in the past relative to the 2025-26 academic session cutoff (e.g. `2024-03-31`). | `CERTIFICATE_EXPIRED` |
| `missing_signature_field` | PDF Certificate | Authorizing officer signature, seal, and notary stamp omitted from the document. | `MISSING_SIGNATURE_FIELD` |
| `wrong_institution_name` | PDF Certificate | Document issued to an unrelated commercial shopping complex or different college. | `ENTITY_NAME_MISMATCH` |
| `mismatched_reference_number` | QR Code / PDF | Embedded QR code encodes verification URL with reference number diverging from header. | `MISMATCHED_REFERENCE_NUMBER` |
| `edited_amount` | Document Data | Carpet area or registered lease duration altered to inconsistent/insufficient numbers. | `AREA_INCONSISTENCY` / `LEASE_DEFICIENCY` |
| `faculty_duplicate_across_institutions` | Faculty Roster | Same faculty member (identical PAN/Aadhaar) simultaneously claimed full-time across 2+ colleges. | `DUAL_EMPLOYMENT_GHOST_FACULTY` |
| `area_too_small_for_intake` | Institution Profile | Declared carpet area drops below the statutory 10.5 sq.m/student physical capacity threshold. | `PHYSICAL_DENSITY_IMPOSSIBILITY` |
| `date_before_issuer_existed` | PDF Certificate | Document issue date (e.g. `1972`) predates the establishment of the issuing state agency and college. | `ANACHRONISTIC_ISSUE_DATE` |
| `reused_photo` | Campus Photos | Identical photo (exact byte-for-byte or cropped/rotated near-duplicate) submitted across colleges. | `PHOTO_REUSE_RADAR_MATCH` |
| `missing_exif_metadata` | Campus Photos | Image metadata completely stripped of camera make, timestamp, and GPS coordinates. | `STRIPPED_EXIF_PROVENANCE` |

---

## 🔬 Scan-Like Degradation (Augraphy)

For ~30% of generated documents, realistic scanner degradation is applied using `Augraphy`:
- **DirtyRollers**: Simulates dirty scanner feed rollers and line smudges.
- **BadPhotoCopy**: Injects realistic photocopy grain, noise iteration, and edge effects.
- **Geometric**: Injects subtle scanner skew and rotation (-1.5° to +1.5°).
- **BleedThrough**: Simulates back-of-page ink bleed on official paper.
- Automatic fallback to high-fidelity Pillow filter degradation (`GaussianBlur`, rotation, contrast scaling) guarantees 100% execution stability across all OS environments.
