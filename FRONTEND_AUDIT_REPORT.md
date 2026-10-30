# PRAMAAN-X (प्रमाण-X) Frontend QA & UX Audit Report

**Audit Date**: October 28, 2026  
**Auditor**: Senior Regulatory QA & UX Auditor  
**Target Platform**: PRAMAAN-X — AICTE Extension of Approval (EoA) Scrutiny System  
**Stack**: React 19 + Vite 8 + Tailwind CSS 3.4, FastAPI 0.110+ Backend, SQLite/PostgreSQL Database, Mock Issuer Gateway  

---

## 1. Executive Summary

| Metric | Evaluation |
| :--- | :--- |
| **Overall Health Score** | **84 / 100** |
| **Demo Readiness Verdict** | **READY WITH FIXES** |
| **Blockers (P0)** | **0** |
| **Major Deficiencies (P1)** | **5** |
| **Minor Deficiencies (P2)** | **6** |
| **Nice-to-Have (P3)** | **1** |
| **Total Findings** | **12** |

### Verdict Justification
PRAMAAN-X has an exceptionally sophisticated, aesthetically striking regulatory decision-support interface. The core 6-stage Evidence Lens, Regulation-as-Code What-If simulator, Photo Reuse Radar with difference overlays, Pre-Flight traffic-light readiness scorecard, and SHA-256 Ed25519 hash-chain verification all function and present real data. 

However, **"READY WITH FIXES"** is mandated prior to presenting before AICTE judges because:
1. **Statutory Keyword Violations**: The non-negotiable statutory rule prohibits the words **"fraud"** or **"forged"** from ever appearing in the UI. Both words were uncovered in live components (`InspectionPlannerPage.jsx:197` displays `"Unrectified Non-Judicial Stamp Paper Fraud Indicator"`, and `mockOfficerData.js:589` contains `"forged land conversion sanction order"`).
2. **Mobile/Tablet Sign Out Defect**: The sign-out button (`#header-signout-btn`) is completely hidden on screens below 768px due to missing icon markup and `hidden md:inline` on the text.
3. **Faked Chain Tampering**: The "Demo: Tamper" toggle modifies client-side React state instead of invoking the existing, fully implemented backend endpoint `POST /api/v1/audit/simulate-tamper-demo`.
4. **Three Ghost API Endpoints**: The frontend `api.js` calls 3 endpoints that do not exist in the FastAPI backend OpenAPI specification.

---

## 2. Environment & Run Results

### 2.1 Services Health & Status

| Service | Port / Protocol | Runtime Status | Observation / Output |
| :--- | :--- | :--- | :--- |
| **FastAPI Backend** | `http://localhost:8000` | **PASS (Operational)** | Responds 200 OK at `/` and `{"status":"HEALTHY","db":"CONNECTED","database_engine":"SQLite"}` at `/health`. |
| **Mock Issuer Gateway** | `http://localhost:8001` | **PASS (Operational)** | Responds 200 OK at `/health`. 510 seeded records (Fire, Affiliation, NBA, Bhoomi Land Records). |
| **React + Vite Frontend** | `http://localhost:5173` | **PASS (Operational)** | Vite v8.3.4 development server running. |
| **Database** | SQLite (`pramaan_x.db`) | **PASS (Operational)** | 100 institutions, faculty rosters, 7 cryptographically linked audit receipts. |

### 2.2 Build & Linter Scan Output

- **Production Bundle Build (`npm run build`)**:
  - **Status**: PASSED in 13.94s.
  - **Output**:
    ```text
    dist/index.html                     0.90 kB │ gzip:   0.48 kB
    dist/assets/index-BRB6uF4t.css    106.57 kB │ gzip:  18.44 kB
    dist/assets/index-B5xbO0CF.js   1,261.46 kB │ gzip: 353.37 kB
    (!) Some chunks are larger than 500 kB after minification.
    ```
  - **Warning**: Main JS bundle is 1.26 MB minified. Route code-splitting via `React.lazy()` is recommended.

- **Static Linter Scan (`npm run lint` / `oxlint`)**:
  - **Status**: PASSED (0 errors, 163 warnings).
  - **Primary Warnings**:
    1. Unused imports in `Dashboard.jsx`, `EvidenceLens.jsx`, `Navbar.jsx` (`FileText`, `ArrowRight`, `Filter`, `ShieldCheck`, `ArrowUpDown`, `ExternalLink`).
    2. `react(set-state-in-effect)`: Calling `setState` synchronously within `useEffect` inside `Dashboard.jsx:125` and `EvidenceLens.jsx:92`.
    3. Missing devDependency: `puppeteer-core` is declared in `package.json` devDependencies but was not installed in `node_modules`.

---

## 3. Static Inventory (Step 2)

### 3.1 Route & Tab Mapping

| Tab ID / Route | Component | File Path | Allowed Roles | API Endpoints Invoked |
| :--- | :--- | :--- | :--- | :--- |
| `dashboard` | `Dashboard` | `frontend/src/pages/Dashboard.jsx` | All roles | `GET /applications`, `POST /documents/upload`, `POST /applications/{id}/officer-action` |
| `evidence-lens` | `EvidenceLens` | `frontend/src/components/EvidenceLens.jsx` | Scrutiny, Senior, Admin, Auditor | `GET /applications/{id}/evidence-lens`, `POST /applications/{id}/validate`, `POST /applications/{id}/officer-action`, `POST /applications/{id}/findings/{id}/rectify` |
| `manual-review-queue` | `ManualReviewQueuePage` | `frontend/src/pages/ManualReviewQueuePage.jsx` | Scrutiny, Senior, Admin, Auditor | `GET /verification/connector/manual-review-queue`, `POST /verification/connector/manual-review-queue/{id}/resolve`, `POST /verification/connector/verify` |
| `preflight` | `PreFlightScorecard` | `frontend/src/components/PreFlightScorecard.jsx` | Scrutiny, Senior, Admin, Institution User | `POST /preflight/scan`, `POST /preflight/upload`, `POST /documents/ingest` |
| `document-intelligence`| `DocumentIntelligencePage` | `frontend/src/pages/DocumentIntelligencePage.jsx` | Scrutiny, Senior, Admin, Auditor | `POST /documents/ingest`, `POST /forensics/document/analyze` |
| `photo-radar` | `PhotoReuseRadar` | `frontend/src/components/PhotoReuseRadar.jsx` | Scrutiny, Senior, Admin | `GET /radar/clusters`, `POST /radar/query`, `POST /forensics/photo/sun-shadow-plausibility`, `POST /forensics/geospatial/built-up-plausibility`, `GET /forensics/calibration` |
| `impossibility-engine` | `ImpossibilityGraph` | `frontend/src/components/ImpossibilityGraph.jsx` | Scrutiny, Senior, Admin, Auditor | `GET /graph`, `GET /graph/impossibilities` |
| `audit-ledger` | `AuditAndReceiptsPage` | `frontend/src/pages/AuditAndReceiptsPage.jsx` | All roles | `GET /audit/receipts`, `GET /audit/verify-chain`, `POST /audit/simulate-tamper-demo`, `POST /audit/restore-tamper-demo`, `GET /audit/logs`, `GET /applications/officer-actions/all` |
| `regulations` | `RuleConfigPage` | `frontend/src/pages/RuleConfigPage.jsx` | Senior Officer, Admin | `GET /rules`, `POST /rules/dry-run` |
| `inspection-planner` | `InspectionPlannerPage` | `frontend/src/pages/InspectionPlannerPage.jsx` | Scrutiny, Senior, Admin | `GET /inspections/planner` |

### 3.2 Dead / Orphaned Components

1. **`AuditHistoryTab.jsx`** (`frontend/src/components/AuditHistoryTab.jsx`): An 11-line re-export wrapper component that is never imported or referenced in any file.
2. **`AuditLedgerView.jsx`** (`frontend/src/components/AuditLedgerView.jsx`): A 224-line standalone audit receipt component that was superseded by `AuditAndReceiptsPage.jsx` but left unreferenced.

### 3.3 Ghost / Non-Existent API Endpoints in `api.js`

| Function in `api.js` | Endpoint Called | Status in Backend OpenAPI | Consequence |
| :--- | :--- | :--- | :--- |
| `api.getChecklist(id)` | `GET /applications/${id}/checklist` | **404 Not Found** | Dead function; never called by components. |
| `api.evaluateRules(appId)` | `POST /rules/evaluate/${appId}` | **404 Not Found** | Dead function; replaced by `/rules/dry-run`. |
| `api.updateOfficerDecision(evalId, ...)` | `PATCH /rules/evaluations/${evalId}/decision` | **404 Not Found** | Dead function; replaced by `/applications/{id}/officer-action`. |

### 3.4 Unused API Functions in `api.js` (12 functions)
`getApplicationDetail`, `getChecklist`, `updateRule`, `evaluateRules`, `updateOfficerDecision`, `scanPhotoRadar`, `getPhotoRegistry`, `runELA`, `queryIssuer`, `getSchedulerStatus`, `compositeVerifyConnector`, `runForensicsCalibration`.

---

## 4. Feature-by-Feature Checklist (Step 4)

| # | Feature | Status | Evidence / Verification Method | Notes |
| :---: | :--- | :---: | :--- | :--- |
| **1** | **Login & Role-Aware Navigation** | **Working** | Tested across 4 roles via preset buttons. Screenshots `F-001`, `F-015`. | Unauthorized tabs are hidden from sidebar and blocked via `#access-restricted-card`. |
| **2** | **Officer Dashboard** | **Working** | Screenshot `F-002`. Verified 5 KPI cards, triage table, status chips, alert bell drawer. | Search, severity, category, and state filters operate smoothly without lag. |
| **3** | **Evidence Lens Pipeline** | **Working** | Screenshot `F-003`. Tested 6-stage pipeline and officer decision form. | **Mandatory comment strictly enforced**: empty submissions blocked with warning. AI flags labeled *"Indicator for review"*. |
| **4** | **Photo Reuse Radar** | **Working** | Screenshot `F-004`, `F-005`, `F-006`. Tested cluster graph, diff overlay, ELA heatmap. | Perceptual hashing (Hamming distance) and sun-shadow plausibility operational. |
| **5** | **Pre-Flight Readiness Scorecard** | **Working** | Screenshot `F-007`. Traffic-light readiness gauge, defect checklist, and scan trigger tested. | Interactive self-improvement checklist works with plain-language corrective guidance. |
| **6** | **Policy What-If Simulator** | **Working** | Screenshots `F-013`, `F-014`. Tested slider parameter modification and dry-run execution. | Displays affected count, bar charts by state and course type, before/after table, and version publish confirmation modal. Admin only. |
| **7** | **Rule Configuration Page** | **Working** | Screenshot `F-012`. AICTE handbook rules catalog with clause citations. | Formatted clause references (`APH-2025-Cl-4.1.1`, etc.) rendered clearly. |
| **8** | **Audit & Receipts Chain** | **Partial** | Screenshots `F-008`, `F-009`, `F-010`. Timeline, green verify animation, and tamper detection tested. | **Finding F-004**: "Demo: Tamper" toggle alters client-side React state (`...dead` hash) instead of invoking the backend API. |
| **9** | **Alerts Bell & Drawer** | **Working** | Tested via Navbar bell icon. Live drawer with count badge, severity indicators, and resolve actions. | Real-time counts synchronized with backend alerts engine. |
| **10**| **Statutory Status Labels** | **Working** | Evaluated `StatusChip.jsx`. | Strictly renders the 6 exact labels: *Verified, Mismatch Detected, Expired, Verification Pending, Source Unavailable, Manual Review Required*. |
| **11**| **Safeguard Checks** | **Broken** | Grepped codebase and UI text. | **Violations detected**: `"fraud"` in `InspectionPlannerPage.jsx:197`, `"forged"` in `mockOfficerData.js:589`. |
| **12**| **Privacy & PII Masking** | **Working** | Inspected `ConflictingSubgraphNetwork.jsx` and network responses. | Aadhaar (`XXXX-XXXX-9021`) and PAN (`AB****89C`) masked. Backend `mask_pii_by_role` applied. |
| **13**| **Tenant Isolation** | **Working** | Logged in as `registrar@apextech.edu.in`. Screenshot `F-015`. | Table filtered to 1 row (Apex Institute). Restricted scrutiny modules completely hidden from navigation. |

---

## 5. Demo-Flow Rehearsal (Step 5)

We rehearsed the standard **4-Minute Judge Presentation Path** end-to-end:

| Step & Timestamp | Action / Feature | Result | Judge Risk / What Could Go Wrong |
| :--- | :--- | :---: | :--- |
| **1. [0:00 - 0:45]** | **Pre-Flight Scorecard** (Institution Role): Show initial low readiness score (64/100, Amber/Red), explain missing Land title deed and Fire NOC lapse. | **PASS** | *Risk*: If backend is slow, preflight calculation spinner takes > 3s. *Mitigation*: Preflight has deterministic synthetic heuristic fallback. |
| **2. [0:45 - 1:15]** | **Document Upload & Score Improvement**: Upload renewed Fire NOC, click re-run scan, score jumps to 94/100 (Green). | **PASS** | *Risk*: Document ingestion format error. *Mitigation*: System handles synthetic PDF and image uploads smoothly. |
| **3. [1:15 - 1:50]** | **Scrutiny Officer Dashboard**: Switch to Scrutiny Officer, show risk-ranked triage queue, alert bell with active count, and high-risk flags. | **PASS** | *Risk*: On screens < 768px, Sign Out button is hidden. *Mitigation*: Presenter must use desktop resolution (1440px+). |
| **4. [1:50 - 2:40]** | **Evidence Lens on Faculty Conflict**: Open Apex Tech dossier, examine 6-stage pipeline for Dr. R. K. Sharma dual-employment, show conflicting subgraph, attempt submit without comment (rejected), enter signed comment and escalate. | **PASS** | *Risk*: Officer forgets to type 10+ characters in comment box. *Mitigation*: Rehearsed comment ready. |
| **5. [2:40 - 3:10]** | **Photo Reuse Radar**: Open Photo Radar, click cluster node, inspect side-by-side photo comparison with 98.4% pHash match and difference heatmap overlay. | **PASS** | *Risk*: Missing image links. *Mitigation*: Base64/mock campus images render cleanly. |
| **6. [3:10 - 3:40]** | **Policy What-If Simulator** (Admin): Switch to Admin, open Regulation-as-Code, slide FSR from 1:20 to 1:25, run dry-run, show cohort impact bar chart and version publish modal. | **PASS** | *Risk*: Backend timeout on 150-college dry run. *Mitigation*: Client has offline simulation fallback if backend dry-run fails. |
| **7. [3:40 - 4:10]** | **Audit Receipt Ledger & Tamper Demo**: Open Audit and Receipts, click "Verify Audit Chain" (green flowing pulse), toggle "Demo: Tamper" (Block #2 turns red with severed hash explanation). | **PASS** | *Risk*: Judge asks if tampering actually altered the database. *Mitigation*: Acknowledge this is a client demonstration of cryptographic verification principles. |

### Degradation & Backup Strategy
- **Backend Offline**: The frontend gracefully falls back to rich mock data mode with the yellow/amber "Demo / Mock Data" indicator.
- **Mock Issuer Offline**: External verification requests fall back to `Source Unavailable` / `Manual Review Required` routing without crashing the application.
- **OCR Engine Offline**: The backend provides synthetic heuristic field-extraction fallbacks.

---

## 6. Detailed Findings List

### [F-001] Forbidden Word "Fraud" in Inspection Planner Page
- **Severity**: **Major (Statutory Rule Violation)**
- **Page / File**: `frontend/src/pages/InspectionPlannerPage.jsx`, Line 197
- **Role**: Scrutiny Officer / Senior Officer / Admin
- **Steps to Reproduce**:
  1. Log in as Scrutiny Officer.
  2. Click `Inspection Planner` in the left sidebar.
  3. Inspect the high-priority risk indicators for Cluster 1.
- **Expected**: UI must strictly adhere to statutory non-punitive language: *"Indicator for review"* or *"Documentary Discrepancy Indicator"*. The word *"fraud"* is prohibited.
- **Actual**: Line 197 explicitly states: `'Unrectified Non-Judicial Stamp Paper Fraud Indicator'`.
- **Screenshot**: `audit_screenshots/F-002_officer_dashboard.png` (Planner module)
- **Suggested Fix**: Replace `'Unrectified Non-Judicial Stamp Paper Fraud Indicator'` with `'Unrectified Non-Judicial Stamp Paper Discrepancy Indicator'`.

---

### [F-002] Forbidden Word "Forged" in Mock Regulatory Findings
- **Severity**: **Major (Statutory Rule Violation)**
- **Page / File**: `frontend/src/data/mockOfficerData.js`, Line 589
- **Role**: All Roles
- **Steps to Reproduce**:
  1. Open Audit and Receipts -> Officer Decisions tab.
  2. Inspect decision comments for historical adverse determinations.
- **Expected**: No occurrence of the word *"forged"*. Adverse indicators must refer to *"unverified external registry record"* or *"unauthorized alteration indicator"*.
- **Actual**: Line 589 states: `comment: 'Adverse status determination recorded by committee: Unrectifiable legal title litigation and forged land conversion sanction order...'`.
- **Screenshot**: `audit_screenshots/F-008_audit_receipts_timeline.png`
- **Suggested Fix**: Replace `'forged land conversion sanction order'` with `'unverified land conversion sanction order with conflicting registry seal'`.

---

### [F-003] Sign-Out Button Invisible and Inoperable on Mobile / Tablet Screens
- **Severity**: **Major (Usability / Accessibility)**
- **Page / File**: `frontend/src/components/Navbar.jsx`, Lines 216–224
- **Role**: All Roles
- **Steps to Reproduce**:
  1. Resize browser viewport to 768px or below (or open on tablet/mobile).
  2. Attempt to sign out of the active session.
- **Expected**: An accessible `LogOut` icon button is visible and tappable at all viewport widths.
- **Actual**: The `<button id="header-signout-btn">` has no icon child element; its only content is `<span className="text-[11px] font-medium hidden md:inline">Sign Out</span>`. When viewport is < 768px, Tailwind hides the span (`display: none`), collapsing the button to 0×0 pixels and rendering it impossible to click.
- **Screenshot**: `audit_screenshots/F-018_layout_768px.png`, `audit_screenshots/F-019_layout_375px.png`
- **Suggested Fix**: Import `LogOut` from `lucide-react` and render `<LogOut className="w-4 h-4 text-slate-500 hover:text-rose-600" />` inside the button alongside the text span.

---

### [F-004] Audit Ledger Tamper Demo Operates Exclusively on Client-Side State
- **Severity**: **Major (Functional / Integrity Truthfulness)**
- **Page / File**: `frontend/src/pages/AuditAndReceiptsPage.jsx`, Lines 284–320
- **Role**: Central Admin / Auditor / Scrutiny Officer
- **Steps to Reproduce**:
  1. Navigate to `Audit and Receipts` page.
  2. Toggle `Demo: Tamper` switch to ON.
  3. Inspect browser Network tab.
- **Expected**: Frontend invokes `POST /api/v1/audit/simulate-tamper-demo?receipt_index=2` to test server-side mathematical verification.
- **Actual**: Zero network requests are made. The toggle mutates local React state (`receipt_hash` ending in `'dead'`) and recalculates client-side. The backend implementation in `audit.py` is bypassed.
- **Screenshot**: `audit_screenshots/F-010_audit_receipts_tampered.png`
- **Suggested Fix**: In `handleToggleTamperDemo`, invoke `await api.simulateTampering(2)` when checked, and `await api.restoreTamperDemo()` when unchecked.

---

### [F-005] Non-Existent API Endpoints Defined in Frontend Client (`api.js`)
- **Severity**: **Major (Code Integrity)**
- **Page / File**: `frontend/src/services/api.js`, Lines 61, 107, 111
- **Role**: Developer / System
- **Steps to Reproduce**:
  1. Inspect `api.getChecklist`, `api.evaluateRules`, `api.updateOfficerDecision`.
  2. Query FastAPI OpenAPI docs (`/api/v1/openapi.json`).
- **Expected**: Every endpoint method in `api.js` corresponds to a registered FastAPI route.
- **Actual**: 
  - `GET /applications/${id}/checklist` does not exist on backend (checklist is served within `/applications/{id}`).
  - `POST /rules/evaluate/${appId}` does not exist (backend uses `/rules/dry-run`).
  - `PATCH /rules/evaluations/${evalId}/decision` does not exist (backend uses `/applications/{app_id}/officer-action`).
- **Screenshot**: N/A (Static API discrepancy)
- **Suggested Fix**: Remove the 3 obsolete functions or update their signatures to the active endpoints.

---

### [F-006] Dead Components Retained in Source Tree
- **Severity**: **Minor (Technical Debt)**
- **Page / File**: `frontend/src/components/AuditHistoryTab.jsx`, `frontend/src/components/AuditLedgerView.jsx`
- **Role**: Developer
- **Steps to Reproduce**:
  1. Search for imports of `AuditHistoryTab` and `AuditLedgerView` across `frontend/src`.
- **Expected**: All source components are wired into the application.
- **Actual**: Both files have 0 external references across the entire repository.
- **Screenshot**: N/A
- **Suggested Fix**: Delete both files to eliminate developer confusion and reduce audit surface.

---

### [F-007] 12 Unreferenced API Functions in `frontend/src/services/api.js`
- **Severity**: **Minor (Dead Code)**
- **Page / File**: `frontend/src/services/api.js`
- **Role**: Developer
- **Steps to Reproduce**: Run static grep scan for `api.<function>` across `.jsx` files.
- **Expected**: Exported API surface is utilized by UI pages.
- **Actual**: 12 methods (`getApplicationDetail`, `scanPhotoRadar`, `queryIssuer`, `getSchedulerStatus`, etc.) are never invoked.
- **Suggested Fix**: Prune unused wrappers or wire them into specialized tooling pages.

---

### [F-008] 163 Linter Warnings in `oxlint`
- **Severity**: **Minor (Code Hygiene)**
- **Page / File**: `frontend/src/pages/Dashboard.jsx`, `frontend/src/components/EvidenceLens.jsx`
- **Role**: Developer
- **Steps to Reproduce**: Run `npm --prefix frontend run lint`.
- **Expected**: Clean lint output with 0 warnings.
- **Actual**: 163 warnings for unused icon imports and `react(set-state-in-effect)` synchronous state resets.
- **Suggested Fix**: Remove unused Lucide imports and derive state during render rather than calling `setState` directly inside effects.

---

### [F-009] Large Single Bundle Chunk (> 1.26 MB) Without Code Splitting
- **Severity**: **Minor (Performance)**
- **Page / File**: `frontend/src/App.jsx`, `frontend/vite.config.js`
- **Role**: All Roles
- **Steps to Reproduce**: Run `npm --prefix frontend run build`.
- **Expected**: Chunk sizes below 500 kB with lazy-loaded routes.
- **Actual**: `dist/assets/index-B5xbO0CF.js` is 1,261.46 kB minified.
- **Suggested Fix**: Use `React.lazy()` for heavy secondary views (`PhotoReuseRadar`, `InspectionPlannerPage`, `ImpossibilityGraph`).

---

### [F-010] Hardcoded Masked PII Without Privileged Role Unmasking Option
- **Severity**: **Minor (Regulatory UX)**
- **Page / File**: `frontend/src/components/ConflictingSubgraphNetwork.jsx`, Lines 407–418
- **Role**: Central Admin / Senior Officer
- **Steps to Reproduce**:
  1. Log in as Central Admin.
  2. View faculty node detail panel in Impossibility Engine or Evidence Lens.
- **Expected**: Authorized Central Admins or Statutory Inquiry Committee Chairs have a logged "Unmask PII" inspection action.
- **Actual**: PAN (`AB****89C`) and Aadhaar (`XXXX-XXXX-9021`) are hardcoded text strings with no role-conditional reveal control.
- **Screenshot**: `audit_screenshots/F-003_evidence_lens_determination.png`
- **Suggested Fix**: Support an authorized unmasking toggle for Central Admin role with an immutable audit log receipt dispatch.

---

### [F-011] Dropdown Option Value Uses Forbidden "REJECTED" Key
- **Severity**: **Minor (Semantic Governance)**
- **Page / File**: `frontend/src/pages/ManualReviewQueuePage.jsx`, Line 625
- **Role**: Scrutiny Officer
- **Steps to Reproduce**:
  1. Open `Manual Review Queue`.
  2. Click `Resolve Case` on any queued item.
  3. Inspect `<select>` options.
- **Expected**: Option values align strictly with advisory terminology: `RECOMMEND_INSPECTION`.
- **Actual**: `<option value="REJECTED">Recommend On-Site Physical Inspection</option>`. While the visible label is compliant, the underlying value uses `REJECTED`.
- **Suggested Fix**: Change value to `RECOMMEND_INSPECTION`.

---

### [F-012] Tab Navigation Lacks Browser URL Synchronization (No Deep Linking)
- **Severity**: **Nice-to-Have (UX Navigation)**
- **Page / File**: `frontend/src/App.jsx`, Lines 32–33
- **Role**: All Roles
- **Steps to Reproduce**:
  1. Navigate to `photo-radar` tab.
  2. Hit browser Refresh (F5) or click Browser Back button.
- **Expected**: Active tab is preserved via URL hash (`#/photo-radar`) or query param.
- **Actual**: Application reloads and defaults back to `dashboard` tab every time.
- **Suggested Fix**: Synchronize `activeTab` with `window.location.hash`.

---

## 7. Top 10 Prioritized Fixes (Demo Impact Order)

1. **Purge Forbidden Word "Fraud"** (`InspectionPlannerPage.jsx:197`): Replace with *"Discrepancy Indicator"*. High risk of statutory disqualification during presentation.
2. **Purge Forbidden Word "Forged"** (`mockOfficerData.js:589`): Replace with *"unverified external registry record"*.
3. **Fix Sign-Out Button on Tablet/Mobile Viewports** (`Navbar.jsx:219`): Add visible `LogOut` icon so touch/responsive users can switch roles.
4. **Connect Live Backend for Tamper Demo** (`AuditAndReceiptsPage.jsx:284`): Replace local state mutation with `api.simulateTampering(2)`.
5. **Harmonize Dropdown Value** (`ManualReviewQueuePage.jsx:625`): Replace `value="REJECTED"` with `value="RECOMMEND_INSPECTION"`.
6. **Remove Dead Components** (`AuditHistoryTab.jsx`, `AuditLedgerView.jsx`): Delete unused files.
7. **Clean 3 Non-Existent API Functions** (`api.js:61, 107, 111`): Prevent developer errors.
8. **URL Hash Synchronization for Active Tab** (`App.jsx`): Preserve tab on F5 refresh.
9. **Eliminate High-Frequency Oxlint Warnings** (`Dashboard.jsx`, `EvidenceLens.jsx`): Remove unused imports.
10. **Implement Route Code Splitting** (`App.jsx`): Wrap heavy graph and canvas components in `React.lazy` to drop initial bundle under 500 kB.

---

## 8. Not Tested / Could Not Verify

1. **Multi-GB Real PDF Concurrency**: Tested with synthetic single-page and multi-page PDFs up to 5 MB; did not stress-test with 500 MB scanned dossiers.
2. **PostgreSQL Container Replication**: Tested live in SQLite local development mode; PostgreSQL failover clustering was not tested on Windows host.
3. **Hardware Biometric Aadhaar Device Integration**: Verified mock UIDAI/TRACES gateway responses; physical fingerprint scanner drivers were simulated.
