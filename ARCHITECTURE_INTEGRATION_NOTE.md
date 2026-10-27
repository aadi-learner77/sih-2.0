# PRAMAAN-X: Architecture & Production Integration Note
**AICTE National Scrutiny & Regulatory Decision-Support Framework**  
*Technical Architecture, National Infrastructure Integration & Real vs Mocked Assessment*

---

## 1. System Architecture & Component Blueprint

PRAMAAN-X is engineered as a loosely-coupled, high-throughput microservices architecture that layers over existing AICTE approval workflows:

```
[ AICTE Web Portal / Mobile App / Institution Client ]
                     │ (HTTPS / TLS 1.3 / Parichay SSO)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 FASTAPI API GATEWAY (Port 8000)             │
│  • RBAC & JWT Authentication (5 Statutory Roles)            │
│  • Rate Limiting, Request Validation & Deduplication Bus    │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
       (Asynchronous Pipeline)        (Sync Lookups & Rules)
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│ AI/ML SCRUTINY ENGINE        │ │ INSTITUTIONAL TWIN ENGINE  │
│ • PaddleOCR Text & Bounding  │ │ • NetworkX Dynamic Graph   │
│ • ELA & ORB Image Forensics  │ │ • Impossibility Logic      │
│ • pHash + OpenCLIP Radar     │ │ • Regulation-as-Code YAML │
│ • FAISS 512-dim Vector Index │ │ • What-If Impact Simulator │
└──────────────┬───────────────┘ └────────────┬───────────────┘
               │                              │
               └──────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│             STATUTORY SOURCE-VERIFICATION GATEWAYS          │
│ • REST API Connectors  • QR Decode Pipeline  • Ed25519 PKI  │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│             CRYPTOGRAPHIC AUDIT CHAIN & PERSISTENCE         │
│ • PostgreSQL / SQLite Relational Models                     │
│ • RFC 8032 Ed25519 Append-Only Hash-Chained Receipt Ledger   │
│ • S3 / MinIO Encrypted Document & Forensic Heatmap Store     │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Enterprise Integration Specification

### 2.1 Single Sign-On (SSO) & Identity Federation
- **Protocol:** SAML 2.0 and OpenID Connect (OIDC).
- **National Gateway:** Integrates with Government of India **Parichay / MeriPehchaan** National Single Sign-On.
- **Role Mapping:**
  - `institution_user`: Authenticated using AICTE Institution ID and authorized Registrar digital token.
  - `scrutiny_officer` & `senior_officer`: Authenticated via AICTE official email and Parichay 2FA biometric/OTP.
  - `admin`: Central AICTE Policy Cell administrator with hardware security key (FIDO2) access.

### 2.2 Core REST API & Webhook Specifications
- `POST /api/v1/preflight/evaluate`: Asynchronous dossier evaluation returning preliminary defect indicators and overall health score.
- `POST /api/v1/verification/connector/verify`: Direct source-verification lookup against registered external gateways.
- `GET /api/v1/radar/clusters`: Fetches cross-institution infrastructure photo reuse clusters with cosine similarity metrics.
- `POST /api/v1/rules/simulate`: In-memory What-If regulatory simulation without database mutations.
- `GET /api/v1/receipts/chain/verify`: Mathematical cryptographic verification of the complete Ed25519 receipt ledger.

### 2.3 Authoritative External Issuer Connectors (Production Pathway)
1. **DigiLocker & National Academic Depository (NAD):** Direct OAuth2 mTLS integration with DigiLocker API gateways for machine-readable XML certificates and PKI-signed credentials.
2. **State Land Revenue Portals (Bhoomi, Mahabhulekh, BanglarBhumi):** Direct REST query using district, taluk, and survey number to confirm registered landholder title, non-agricultural zoning, and nil-encumbrance status.
3. **CBDT TRACES & EPFO Portal:** Direct statutory data-sharing accords to verify Form 16 / 26AS TDS deductions and Provident Fund contributions, permanently terminating ghost faculty double-counting across technical institutions.

---

## 3. Phased 3-Stage National Rollout Plan

```
[ Phase 1: Dual-Run Sandbox ] ➔ [ Phase 2: Regional Bureau Co-Pilot ] ➔ [ Phase 3: Full National Statutory Run ]
     (Months 1 - 3)                       (Months 4 - 8)                         (Months 9 - 12)
```

### Phase 1: Dual-Run Sandbox (Months 1–3)
- **Scope:** 2 State Directorates (e.g., Maharashtra & Karnataka) covering ~500 institutions.
- **Operational Mode:** Shadow advisory mode. Existing scrutiny committees conduct manual review while PRAMAAN-X runs in parallel in the background.
- **Objective:** Empirically calibrate regional date formats, local municipal seal variants, and measure true time savings.

### Phase 2: Regional Bureau Co-Pilot (Months 4–8)
- **Scope:** All 8 AICTE Regional Bureaus (Northern, Western, Southern, etc.).
- **Operational Mode:** Scrutiny officers use PRAMAAN-X as their primary decision-support dashboard. Mandatory written justifications recorded for all dismissals.
- **Objective:** Connect live pilot endpoints with DigiLocker and state revenue gateways.

### Phase 3: Nationwide Statutory Enforcement (Months 9–12)
- **Scope:** 10,000+ approved institutions nationwide.
- **Operational Mode:** Self-serve Pre-Flight Scorecard unlocked for all colleges prior to formal submission. Complete Ed25519 receipt chain active for all approval files.
- **Objective:** Full statutory compliance under AICTE Approval Process Handbook (APH).

---

## 4. Comprehensive "What is Real vs Mocked" Comparative Table

| System Dimension / Module | Real Algorithm / Implementation (Functional Today) | Simulated / Mocked in Current Prototype | Production Integration Requirement |
| :--- | :--- | :--- | :--- |
| **Field Extraction (OCR)** | **REAL:** PaddleOCR text detection, layout-aware bounding box locator, and regex boundary normalizer (`0.9013 Macro F1`). | None (Processes raw binary PDF files directly). | GPU acceleration (Nvidia T4/A10) for 10x higher batch throughput. |
| **Document Forensics** | **REAL:** Error Level Analysis (ELA) compression divergence, ORB keypoint copy-move matching, and PDF trailer revision parser. | None (Runs directly on uploaded raster scans and PDFs). | Expansion of font consistency dictionaries for legacy Indic vernacular fonts. |
| **Photo Reuse Radar** | **REAL:** pHash 64-bit Hamming distance, OpenCLIP ViT-B/32 512-dim hypersphere embeddings, and FAISS nearest-neighbor index. | Photo corpus contains 42 planted synthetic duplicates across 100 colleges. | Cloud storage integration (S3/GCS bucket indexing 100,000+ national photos). |
| **Institutional Twin Graph** | **REAL:** NetworkX bipartite graph resolving cross-college faculty Aadhaar/PAN tokens and shared land survey numbers. | Graph populated from 100 synthetic institution rosters (3,067 profiles). | Direct integration with AICTE permanent database and state university portals. |
| **Regulation-as-Code** | **REAL:** In-memory rule execution engine evaluating YAML schemas with live What-If impact simulation across applications. | Current rules model 17 key clauses from APH 2025-26. | Formal codification of all 180+ clauses across engineering, management, and pharmacy. |
| **Cryptographic Receipts** | **REAL:** RFC 8032 Ed25519 digital signature chain with asymmetric keypair, SHA-256 state hashing, and tamper detection. | Local filesystem key generation (`backend/keys/ed25519_receipt_signing.key`). | Cloud Hardware Security Module (HSM) or NIC Digital Signature CA (PKCS#11). |
| **External Issuer Portals** | **MOCKED:** Python FastAPI Mock Issuer (`port 8001`) simulating State Fire, Affiliation, NBA, and Land gateways. | 510 authoritative synthetic records in `mock_issuer/data/registry.json`. | Formal inter-agency API agreements, DigiLocker gateways, and state portal tokens. |
| **Institutional Dataset** | **MOCKED:** 100 technical colleges, 500 documents, and 3,067 faculty profiles generated via ReportLab and Faker. | Synthetic ground truth ledger (`generated_data/ground_truth.csv`). | Direct migration and ingestion from current AICTE National Portal relational store. |
| **Scrutiny Time Baseline** | **ASSUMED:** 180.0 minutes manual baseline per application dossier (labeled as explicit model assumption). | 2.08s automated time is **REAL & MEASURED** via Python `time.perf_counter()`. | Formal time-and-motion study across AICTE regional scrutiny committees. |
