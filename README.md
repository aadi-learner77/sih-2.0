# PRAMAAN-X (प्रमाण-X)
### AI Decision-Support Platform for AICTE Extension of Approval (EoA) & Regulatory Document Scrutiny

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4+-38BDF8.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.2+-orange.svg)](https://networkx.org)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.13-blue.svg)](https://python.org)

PRAMAAN-X is an AI-powered regulatory decision-support system engineered for the **All India Council for Technical Education (AICTE)**. It scrutinizes institutional Extension of Approval (EoA) dossiers, extracts and cross-corroborates documentary evidence, executes handbook regulations as declarative code, builds multi-institution knowledge graphs to uncover physically impossible claims, runs forensic image/perceptual hash analysis, verifies claims against mock government issuer portals, and maintains a cryptographically chained, tamper-evident audit ledger.

---

## 🏛 Statutory Hard Constraints & Safeguards
1. **Advisory Decision Support Only**: AI output produces **"Indicators for Review"**, never automated rejections. Statutory scrutiny committees retain sole decision-making authority.
2. **Explainability with Evidentiary Trail**: Every single flagged discrepancy cites handbook clauses, exact mathematical shortfalls, and external registry diffs.
3. **Regulation-as-Code (Configurable Rules)**: Rules are defined declaratively in YAML rule packs (`aicte_aph_2025.yaml`) and can be reconfigured or hot-reloaded dynamically at runtime without codebase modifications.
4. **Data Privacy & PII Masking**: Sensitive identifiers (Aadhaar `XXXX-XXXX-9021`, PAN `AB****89C`) are masked under Indian regulatory standards.
5. **Synthetic Benchmark Data**: All benchmark institutions, faculty names, and documents use anonymized, synthetic test data.

---

## 🚀 Key Functional Modules

### 1. Application Category -> Checklist -> Multi-State Validation
- Maps application categories (`Extension of Approval (EoA)`, `Increase in Intake`, `New Courses`) to dynamic mandatory checklists.
- Automatically flags **Missing**, **Expired**, and **Inconsistent** documents based on session threshold dates.

### 2. OCR Intelligence, Document Classification & Field Extraction
- Modular OCR pipeline supporting **PaddleOCR** with a high-fidelity synthetic heuristic fallback.
- Classifies document types (Fire Safety NOC, Land Deed, Building Plan Approval, Faculty Roster, Affiliation Orders).
- Extracts structured numeric values: sanctioned intake, carpet areas in sq. meters, survey numbers, issue/expiry dates.

### 3. Regulation-as-Code (AICTE Approval Process Handbook)
- Codifies AICTE Approval Process Handbook (APH 2025-26) clauses into declarative YAML:
  - `APH-2025-Cl-4.1.1`: Faculty-to-Student Ratio (FSR <= 1:20 for UG Engineering).
  - `APH-2025-Cl-4.1.3`: Faculty Cadre Proportion (Professor : Associate : Assistant = 1:2:6).
  - `APH-2025-Cl-5.2.4`: Minimum Carpet Area Requirement (10.5 sq.m per student).
  - `APH-2025-Cl-6.3.2`: Fire Safety NOC Validity covering the forthcoming academic session.
  - `APH-2025-Cl-7.1.5`: Land Title & 30-Year Continuous Leasehold norm.
  - `APH-2025-Cl-8.4.1`: Examining University Active Affiliation Order.

### 4. Institution Knowledge Graph & "Impossibility Engine" (NetworkX)
- Builds an interconnected relational graph across technical colleges, faculty members, land parcels, and governing trusts.
- **Ghost Faculty / Dual Employment Detector**: Flags faculty members concurrently reported as full-time regular teachers across two or more institutions simultaneously.
- **Land Parcel Collision Detector**: Flags the identical revenue Khasra/Survey parcel claimed by distinct colleges without joint-campus regulatory approval.
- **Physical Density Impossibility**: Evaluates declared instructional carpet area against student population density.

### 5. Digital Forensics & Photo Reuse Radar
- **Metadata Scanner**: Detects unauthorized digital manipulation tools (e.g. Adobe Photoshop, Canva signatures) in scanned certificates.
- **Error-Level Analysis (ELA)**: Recompression delta analysis identifying localized pixel-level tampering on dates, stamps, and signatures.
- **Photo Reuse Radar**: Uses 64-bit Perceptual Hashing (`pHash` / `dHash`) with Hamming distance lookup across all historic campus photos in India to catch colleges submitting photos from other institutions.

### 6. Mock External Statutory Issuer APIs
- Simulates authoritative government gateways:
  - State Fire & Emergency Services Portal (Fire NOC verification)
  - State Revenue Land Registry Bhoomi/Mahabhulekh (Khata & encumbrance checks)
  - Examining State University Affiliation Cell
  - CBDT TRACES & Form 16 Gateway (TDS salary draw verification)
- Standardized statuses: `verified`, `mismatch_detected`, `expired`, `verification_pending`, `source_unavailable`, `manual_review_required`.

### 7. Hash-Chained, Tamper-Evident "Verification Receipts" Audit Ledger
- Cryptographic hash-chain where every audit event (upload, OCR, verification check, rule evaluation, officer decision) creates a cryptographically linked receipt block:
  $$\text{Receipt Hash} = \text{SHA-256}(\text{Index} \parallel \text{Timestamp} \parallel \text{Event} \parallel \text{Actor} \parallel \text{Payload Hash} \parallel \text{Prev Hash})$$
- Digitally signed with HMAC-SHA256.
- Interactive chain integrity verifier and tampering simulation to prove breach detection.

### 8. Evidence Lens & Pre-Flight Readiness Scorecard
- **Evidence Lens**: 6-Stage decision pipeline:
  `Claim -> Evidence -> Rule -> Source Response -> Confidence -> Officer Action`
- **Pre-Flight Readiness Scorecard**: Institutions run self-assessments before formal submission to identify shortfalls and follow actionable remediation roadmaps.

---

## 🏗 System Architecture

```mermaid
graph TD
    UI[React + Tailwind CSS Frontend] -->|REST / JSON| API[FastAPI Backend Application]
    
    subgraph Backend Core
        API --> CL[Checklist Engine]
        API --> OCR[Modular OCR Intelligence]
        API --> RAC[Regulation-as-Code Engine]
        API --> IMP[NetworkX Impossibility Engine]
        API --> FOR[Forensics & Photo Radar]
        API --> EXT[Mock Issuer Gateways]
        API --> LEDGER[Hash-Chained Audit Ledger]
    end

    subgraph Data Layer
        LEDGER --> DB[(SQLite / PostgreSQL)]
        RAC --> YAML[YAML Handbook Rules]
        IMP --> KG[(Knowledge Graph)]
    end
```

---

## ⚡ Quick Start Instructions

### Prerequisites
- Python 3.11+
- Node.js v18+ and npm

### Method 1: Local Development (Instant, Zero-Docker SQLite)
1. **Activate Backend**:
   ```powershell
   # In project root
   .\venv\Scripts\uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
   # Or run:
   .\run_backend.bat
   ```
   API Docs available at: `http://localhost:8000/api/v1/docs`

2. **Activate Frontend**:
   ```powershell
   cd frontend
   npm run dev
   # Or run:
   .\run_frontend.bat
   ```
   Dashboard available at: `http://localhost:5173`

### Method 2: Docker Compose (PostgreSQL Production Mode)
```bash
docker compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/v1/docs`
- PostgreSQL: `localhost:5432` (database: `pramaan_x`)

---

## 👥 Demo User Credentials & Roles

| Role | Email | Password | Scope |
| :--- | :--- | :--- | :--- |
| **Scrutiny Officer** | `scrutiny.officer@aicte-india.org` | `AicteOfficer@2025` | Full review, Evidence Lens decisions, Clarifications |
| **Regional Officer** | `regional.officer@aicte-india.org` | `AicteRegional@2025` | Regional oversight, hearing orders, policy waivers |
| **Central Admin** | `admin@aicte-india.org` | `AicteAdmin@2025` | Handbook rule parameter configuration, audit logs |
| **Institution User** | `registrar@apextech.edu.in` | `ApexPass@2025` | Pre-flight self-assessment, document uploads |

---

---

## 🏛 Phase 3: Statutory Mock Issuer Service (Port 8001)

The PRAMAAN-X mock issuer service simulates external state and central regulatory authorities:
1. **State Fire & Emergency Services Department** (`fire`) - Fire Safety Certificate / NOC
2. **State Technical University Affiliation Body** (`affiliation`) - Annual Affiliation Orders
3. **National Board of Accreditation (NBA)** (`accreditation`) - Tier-1 / Tier-2 Accreditation Records
4. **State Revenue & Land Records Registry / Bhoomi** (`land`) - Land Title Deeds & Survey Numbers

### API Endpoints:
- **Unified Verification**: `GET /verify?ref=...&name=...&authority=...`
  - Parameters: `ref` (Reference number), `name` (Institution/Trust), `authority` (`fire`, `affiliation`, `accreditation`, `land`), `claimed_expiry`, `claimed_acres`, `latency_ms`, `simulate_failure`
- **Dedicated Authority Endpoints**:
  - Fire: `GET /fire/verify?ref=...&name=...`
  - Affiliation: `GET /affiliation/verify?ref=...&name=...`
  - Accreditation: `GET /accreditation/verify?ref=...&name=...`
  - Land Records: `GET /land/verify?ref=...&name=...`
- **Audit Logging**: `GET /logs?limit=50` (In-memory real-time query ledger)
- **Service Health**: `GET /health` (Operational metrics & record counts by authority)
- **Dynamic Hot Reload**: `POST /registry/reload`

### Security & Protocol:
- **Header Check**: `X-API-Key: pramaanx-mock-key-2025` (enforces HTTP 401 Unauthorized if missing/invalid)
- **Standardized Statuses**: `verified`, `mismatch` (with differing fields), `expired`, `not_found`, and randomly configurable `source_unavailable` (HTTP 503 / timeout)
- **Ground Truth Mapping**: Seeded via `python mock_issuer/seed_registry.py` against `generated_data/ground_truth.csv` with deliberate alterations and missing entries.

### Running & Testing Mock Issuer:
```powershell
# 1. Seed registry from synthetic data
python mock_issuer/seed_registry.py

# 2. Run mock issuer server locally
uvicorn mock_issuer.app.main:app --host 127.0.0.1 --port 8001

# 3. Execute test suite
pytest mock_issuer/test_mock_issuer.py -v
```

---

## 🧪 Automated Testing
Run the comprehensive test suites verifying the 6-stage Evidence Lens, Impossibility Engine, Forensics, and Mock Issuer:
```powershell
# Backend API tests
$env:PYTHONPATH="." ; .\venv\Scripts\pytest backend/test_api.py -v

# Mock Issuer Statutory Gateway tests
$env:PYTHONPATH="." ; .\venv\Scripts\pytest mock_issuer/test_mock_issuer.py -v
```
