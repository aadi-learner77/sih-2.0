# PRAMAAN-X: 4-Minute Competition Demo Script
**Event:** Smart India Hackathon (SIH 2.0) — Grand Finale  
**Product:** PRAMAAN-X AICTE Regulatory Decision-Support & Scrutiny Engine  
**Target Duration:** Exactly 4 Minutes (240 Seconds)  
**Roles Demonstrated:** Institution Registrar (`registrar@apextech.edu.in`) ➔ Scrutiny Officer (`scrutiny.officer@aicte-india.org`) ➔ Central AICTE Admin (`admin@aicte-india.org`)

---

## Quick Reference: Demo Credentials & Portals
- **Frontend URL:** `http://localhost:5173` (or `http://localhost:3000`)
- **Backend API:** `http://localhost:8000` | **Mock Issuer:** `http://localhost:8001`
- **Institution User:** `registrar@apextech.edu.in` / `ApexPass@2025`
- **Scrutiny Officer:** `scrutiny.officer@aicte-india.org` / `AicteOfficer@2025`
- **Central Admin:** `admin@aicte-india.org` / `AicteAdmin@2025`
- **Deterministic Reset Command:** `make demo-reset`

---

## 4-Minute Timeline Overview

```
[0:00 - 0:35] ACT 1: Institution Pre-Flight Self-Check (Red Score & Defect Exposure)
[0:35 - 1:10] ACT 2: Real-Time Rectification & Instant Resubmission
[1:10 - 1:50] ACT 3: Scrutiny Officer Triage Dashboard & Alert Latency
[1:50 - 2:30] ACT 4: Evidence Lens & Multi-Hop Faculty Conflict Graph
[2:30 - 3:10] ACT 5: National Photo Reuse Radar (OpenCLIP + pHash)
[3:10 - 3:40] ACT 6: Regulation-as-Code "What-If" Live Impact Simulator
[3:40 - 4:00] ACT 7: Immutable Ed25519 Audit Receipt Chain & Tamper Defense
```

---

## Detailed Minute-by-Minute Script & Click Paths

### ACT 1: Institution Pre-Flight Self-Check (0:00 – 0:35)
- **Speaker:** "Every year, 10,000 technical colleges submit complex regulatory dossiers to AICTE. Scrutiny officers spend weeks catching document defects that colleges could have fixed themselves. PRAMAAN-X introduces the **Pre-Flight Scrutiny Scorecard**—a self-serve pre-submission diagnostics tool."
- **Action / Click Path:**
  1. Open browser to `http://localhost:5173`.
  2. Log in as Institution Registrar: `registrar@apextech.edu.in` / `ApexPass@2025`.
  3. Navigate to **Pre-Flight Scorecard** (`/preflight` or via Sidebar).
  4. Select Seeded Application: **Apex Institute of Technology & Science** (`APP-2025-09812`).
  5. The scorecard renders a **Red Overall Health Score: 28 / 100** with **3 Critical Blockers**.
  6. Point to the primary blocker:
     - Document: `FS/2024/991` (Fire Safety NOC).
     - Indicator: *"Entity Mismatch: Registered to Apex Commercial Shopping Mall, not an approved educational institution."*
     - Status Chip: `Mismatch Detected` (Amber/Red chip with SHA-256 receipt link).
- **Key Callout:** *"Notice the statutory wording: this is formulated strictly as an 'Indicator for review'. The institution is alerted before formal submission, preventing months of scrutiny ping-pong."*
- **Fallback (If Live OCR/Network Lags):** Click the **"Load Cached Pre-Flight Audit"** toggle in the top-right toolbar or view the pre-rendered offline demo report snapshot.

---

### ACT 2: Real-Time Rectification & Resubmission (0:35 – 1:10)
- **Speaker:** "Under traditional AICTE procedures, a flawed certificate leads to formal rejection or a show-cause notice. With PRAMAAN-X, the institution can immediately exercise the **Rectification Pathway** for allowed findings."
- **Action / Click Path:**
  1. On the `FS/2024/991` card, click the blue **"Upload Rectification Document"** button.
  2. File selector opens: Select `uploads/FIRE_INST_001.pdf` (or replacement certificate `FS/2024/7741` issued to *Apex Institute of Technology & Science*, valid through 2027-05-14).
  3. Click **"Submit Rectification & Re-Validate"**.
  4. In **2.08 seconds (measured runtime)**:
     - PaddleOCR extracts the reference number and validity date.
     - The verification connector validates against the Mock Fire Directorate gateway (`100% success rate`).
     - The previous finding is automatically marked **`SUPERSEDED`** with full cryptographic audit trail preserved.
     - The scorecard transitions from **Red (28/100)** to **Compliant Green (88/100)**.
- **Key Callout:** *"Zero human officer time wasted. The college solved its own defect prior to official scrutiny."*
- **Fallback:** If file upload is disabled, click **"Simulate Instant Document Rectification"** button which applies the patch payload in-memory.

---

### ACT 3: Scrutiny Officer Triage Dashboard & Alerts (1:10 – 1:50)
- **Speaker:** "Now let's switch to the perspective of an AICTE Scrutiny Officer reviewing submitted applications across the nation."
- **Action / Click Path:**
  1. Click User Avatar in top navbar -> Click **"Switch User"** -> Select **"Dr. Sunita Deshmukh (Scrutiny Officer)"** (or log in as `scrutiny.officer@aicte-india.org`).
  2. System redirects to **Scrutiny Officer Dashboard** (`/dashboard`).
  3. Show the top KPI bar:
     - **48 Applications in Queue** | **72.5% Verified** | **9 Expired** | **6 Mismatches** | **14 Pending Gateway**.
  4. Point to the **Status Chips Table** showcasing all 6 statutory states:
     - `Verified` (Green)
     - `Mismatch Detected` (Red)
     - `Expired` (Orange)
     - `Verification Pending` (Yellow)
     - `Source Unavailable` (Slate)
     - `Manual Review Required` (Purple)
  5. Click the **Notification Bell** in the top navbar:
     - The **Alert Bell Drawer** slides open.
     - Demonstrates **3.21ms mean dispatch latency** with 100% deduplication.
     - Point to alert: *"Urgent: Cross-institution faculty conflict detected on APP-2025-09812."*
  6. Click **"Inspect Dossier"** directly from the alert.
- **Key Callout:** *"Officers don't inspect applications alphabetically. PRAMAAN-X prioritizes dossiers by statutory risk score, saving up to 180 minutes of manual checking per college."*
- **Fallback:** If alerts drawer is empty, click **"Refresh Alert Queue"** to load the pre-seeded notification stream.

---

### ACT 4: Evidence Lens & Multi-Hop Conflict Graph (1:50 – 2:30)
- **Speaker:** "Document verification is necessary, but the hardest frauds are relational: ghost faculty claimed by two colleges simultaneously. Let's inspect the **Evidence Lens**."
- **Action / Click Path:**
  1. We are now on **Evidence Lens Page** (`/applications/1` or `/evidence-lens`).
  2. Click on the finding: **`RULE_FACULTY_STUDENT_RATIO`** (Calculated FSR 1:32 vs statutory 1:20 norm).
  3. Click **"Expand Twin Knowledge Graph"**:
     - An interactive NetworkX/D3 node-link graph animates into view.
     - Node A: *Apex Institute of Technology & Science* (Bengaluru).
     - Node B: *Royal College of Engineering* (Hubballi).
     - Connecting Edge: **Prof. C. V. Ramanathan** / **Dr. Tejas Joshi** (Aadhaar `XXXX-XXXX-6057`, PAN `CC****8M`).
     - Badge: *"Simultaneous Full-Time Appointment Detected across 2 Institutions (340 km apart)."*
  4. Show Officer Action Bar at bottom:
     - Buttons: `Accept Finding`, `Dismiss with Reason`, `Request Rectification`, `Recommend Surprise Inspection`.
     - Click **"Request Rectification"** -> Enter mandatory justification note: *"Submit biometric attendance logs and bank salary credit receipts for AY 2024-25."*
     - Click **"Sign & Submit Action"** -> Minted into the Ed25519 audit receipt ledger.
- **Key Callout:** *"Under Section 10 of AICTE regulations, automated adverse decisions are prohibited. PRAMAAN-X enforces that no finding becomes final without an officer's digital signature and written justification."*
- **Fallback:** If the canvas graph is slow to render, click the **"Table View"** tab showing the side-by-side employment conflict matrix.

---

### ACT 5: National Photo Reuse Radar (2:30 – 3:10)
- **Speaker:** "Every year, institutions submit glossy photos of Computer Labs, Workshops, and Chemistry Labs. How does AICTE know the college didn't simply download a stock photo or reuse another college's facility? Meet the **National Photo Reuse Radar**."
- **Action / Click Path:**
  1. In Sidebar, click **"Photo Reuse Radar"** (`/photo-radar`).
  2. Point to the benchmark stats: **88.2% Precision, 100.0% Recall** across exact duplicates, rotations, and CLIP embeddings.
  3. Select **Cluster #1: Computer Center & CAD-CAM Laboratory (`RADAR_CLUSTER_001`)**.
  4. The screen shows a side-by-side comparison:
     - **Left Image:** *Apex Institute of Technology & Science* (Claimed CAD Lab, Uploaded Feb 2025).
     - **Right Image:** *Horizon Institute of Technology* (Claimed CAD Lab, Uploaded Jan 2024).
     - **Match Channel:** `OpenCLIP ViT-B/32 Semantic Hypersphere Cosine Similarity = 0.984` & `pHash Hamming Distance = 4`.
  5. Show the **Forensic Metadata Inspection**:
     - Camera EXIF: Identical serial number and focal length.
     - Solar Shadow Azimuth: Sun angle mismatch with stated latitude/longitude coordinates.
- **Key Callout:** *"Even if an institution crops, compresses, or rotates the image, our hybrid pHash + OpenCLIP pipeline catches the reuse across the national repository."*
- **Fallback:** Click the **"Inspect Pre-computed Cluster Gallery"** to view static cached comparison cards.

---

### ACT 6: Regulation-as-Code "What-If" Simulator (3:10 – 3:40)
- **Speaker:** "Statutory regulations are not static. When the AICTE Council revises the Approval Process Handbook, what happens to ongoing applications? We built **Regulation-as-Code with Live What-If Impact Simulation**."
- **Action / Click Path:**
  1. Switch user to **Central AICTE Administrator** (`admin@aicte-india.org`).
  2. In Sidebar, click **"Rule Configuration & Simulation"** (`/rules`).
  3. Locate rule: **`RULE_FACULTY_STUDENT_RATIO`** (Clause APH-2025-Cl-4.1.1).
  4. Click **"Configure Parameters & Test Impact"**:
     - Change statutory ratio ceiling parameter from `20.0` (1:20) to `25.0` (1:25).
  5. Click **"Run What-If Impact Simulation"**:
     - Engine evaluates 100 seeded institutions in **0.42 seconds**.
     - Renders visual impact gauge: **14 pending applications immediately transition from Non-Compliant to Compliant**.
     - Average compliance rate increases from **74% to 88%**.
- **Key Callout:** *"Zero database corruption. The simulation runs on an in-memory clone of the institutional twin graph, giving council policymakers data-driven foresight before gazette notification."*
- **Fallback:** If simulation button is busy, click **"View 2025-26 vs 2026-27 Policy Comparison Matrix"**.

---

### ACT 7: Immutable Ed25519 Audit Chain & Tamper Defense (3:40 – 4:00)
- **Speaker:** "Finally, in court, AICTE must prove its evidence was never tampered with. PRAMAAN-X seals every action in an **RFC 8032 Ed25519 cryptographically chained audit ledger**."
- **Action / Click Path:**
  1. In Sidebar, click **"Audit Receipts & Integrity"** (`/receipts`).
  2. Inspect the **7-block receipt chain**:
     - `rcpt_001` (Application Submitted) ➔ `rcpt_002` (OCR Field Extraction) ➔ `rcpt_003` (Issuer Query) ➔ ... ➔ `rcpt_007` (Officer Decision Recorded).
     - Each receipt displays: Timestamp, Actor, Ed25519 Signature, and `prev_receipt_hash`.
  3. Click **"Verify Chain Integrity"**:
     - Green Banner: *"Audit Chain Valid: 7/7 blocks verified cryptographically with zero discrepancies."*
  4. Click **"Simulate Byte-Level Tampering"** (Simulates malicious DB modification on Receipt #3):
     - The verification engine re-hashes the ledger.
     - Screen flashes red warning: **"TAMPER DETECTED at Block #3 (`rcpt_003`)! Broken hash link detected. Root signature invalid."**
- **Speaker Closing (Last 5 Seconds):** *"Explainable AI. Zero automatic rejections. Ironclad legal auditability. That is PRAMAAN-X. Thank you."*
- **Fallback:** Click **"Reset Chain to Valid State"** to return the ledger to 100% green integrity.

---

## Complete Demo Emergency Runbook (1-Page Cheat Sheet)

| What Happened | Quick Recovery Action | Time to Recover |
| :--- | :--- | :--- |
| Database state dirty or inconsistent | Run `make demo-reset` in terminal | 6 seconds |
| Backend server unreachable | Run `.venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000` | 2 seconds |
| Mock Issuer port 8001 busy | Run `.venv\Scripts\python.exe -m uvicorn mock_issuer.app.main:app --port 8001` | 2 seconds |
| Frontend React dev server frozen | Refresh tab (`Ctrl+F5`) or click `DemoDataBadge` offline cache | 1 second |
| OCR extraction hangs on live PDF | System defaults to pre-extracted bounding-box catalog in `generated_data` | Instant |
| Video projector aspect ratio cuts off | Press `Ctrl + -` to zoom browser to 90% | Instant |
