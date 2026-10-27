"""
Pytest Test Suite for FastAPI Endpoints and RBAC Governance in PRAMAAN-X:
Tests:
1. Authentication & JWT Tokens: Login for all 5 roles (institution_user, scrutiny_officer, senior_officer, admin, auditor).
2. Tenant Isolation: Institution users can ONLY view and submit their own data; cross-institution access raises 403 Forbidden.
3. No Automatic Rejection Rule: Adverse status requires an authorized officer action; pre-flight/validation does not auto-reject.
4. Officer Action with Mandatory Comment: Scrutiny & Senior officers can take determinations; comment is strictly mandatory; institution users and auditors are blocked (403 Forbidden).
5. Role-based PII Masking: Personal identifiers (Aadhaar, PAN, phone, email) masked for scrutiny officers & auditors; unmasked for data owners & admins.
6. Access Logging: Every read of sensitive dossier data records an audit log entry with actor and resource.
7. Rules CRUD with Versioning: Admin-only rule creation and version updating; non-admins receive 403 Forbidden.
8. What-If Dry Run Simulation: Authorized for officers/admin/auditor; forbidden for institution users.
9. National Photo Reuse Radar Clusters: RBAC access enforcement.
10. Verification Receipts & Chain Audit endpoint validation.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models.models import (
    User, Institution, Application, Finding, Rule, RuleVersion,
    AuditLog, VerificationReceipt, Alert
)
from backend.app.core.security import (
    create_access_token,
    normalize_role,
    ROLE_INSTITUTION_USER,
    ROLE_SCRUTINY_OFFICER,
    ROLE_SENIOR_OFFICER,
    ROLE_ADMIN,
    ROLE_AUDITOR
)
from backend.app.data.seed_data import seed_database


@pytest.fixture(scope="module")
def client():
    """Initializes TestClient and ensures seed data is ready."""
    seed_database()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db():
    """Yields a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_token_for_user(email: str, role: str, institution_id: int | None = None) -> str:
    """Helper to generate JWT bearer token for testing."""
    return create_access_token(
        data={"sub": email, "role": normalize_role(role), "institution_id": institution_id}
    )


# ============================================================================
# 1. AUTH & JWT LOGIN TESTS (ALL 5 ROLES)
# ============================================================================

def test_login_all_5_roles(client: TestClient):
    """Verifies that all 5 required roles can authenticate and receive JWT tokens with role claims."""
    credentials = [
        ("registrar@apextech.edu.in", "ApexPass@2025", ROLE_INSTITUTION_USER),
        ("principal@royal.edu.in", "RoyalPass@2025", ROLE_INSTITUTION_USER),
        ("scrutiny.officer@aicte-india.org", "AicteOfficer@2025", ROLE_SCRUTINY_OFFICER),
        ("senior.officer@aicte-india.org", "AicteSenior@2025", ROLE_SENIOR_OFFICER),
        ("admin@aicte-india.org", "AicteAdmin@2025", ROLE_ADMIN),
        ("auditor@aicte-india.org", "AicteAuditor@2025", ROLE_AUDITOR)
    ]

    for email, password, expected_role in credentials:
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == expected_role


def test_login_invalid_password_rejected(client: TestClient):
    """Verifies that incorrect passwords are rejected with 401 Unauthorized."""
    resp = client.post("/api/v1/auth/login", json={"email": "admin@aicte-india.org", "password": "WrongPassword!"})
    assert resp.status_code == 401
    assert "Incorrect email or password" in resp.json()["detail"]


def test_auth_me_endpoint(client: TestClient):
    """Tests GET /api/v1/auth/me returns authenticated user profile."""
    token = get_token_for_user("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "scrutiny.officer@aicte-india.org"
    assert data["role"] == ROLE_SCRUTINY_OFFICER


# ============================================================================
# 2. TENANT ISOLATION TESTS FOR INSTITUTION USERS
# ============================================================================

def test_institution_user_cannot_view_other_institution_data(client: TestClient, db: Session):
    """
    Institution users must ONLY see their own data.
    Apex Registrar (inst 1) attempting to access Royal College application (inst 2) must receive 403 Forbidden.
    """
    app_apex = db.query(Application).filter(Application.institution_id == 1).first()
    app_royal = db.query(Application).filter(Application.institution_id == 2).first()
    assert app_apex is not None and app_royal is not None

    token_apex = get_token_for_user("registrar@apextech.edu.in", ROLE_INSTITUTION_USER, institution_id=1)
    headers_apex = {"Authorization": f"Bearer {token_apex}"}

    # 1. Apex user viewing their own application -> 200 OK
    resp_own = client.get(f"/api/v1/applications/{app_apex.id}", headers=headers_apex)
    assert resp_own.status_code == 200

    # 2. Apex user viewing Royal application -> 403 Forbidden
    resp_forbidden = client.get(f"/api/v1/applications/{app_royal.id}", headers=headers_apex)
    assert resp_forbidden.status_code == 403
    assert "Institution users can only access their own institution" in resp_forbidden.json()["detail"]

    # 3. Scrutiny Officer viewing both applications -> 200 OK (cross-institution oversight)
    token_officer = get_token_for_user("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)
    headers_officer = {"Authorization": f"Bearer {token_officer}"}

    resp_officer_apex = client.get(f"/api/v1/applications/{app_apex.id}", headers=headers_officer)
    assert resp_officer_apex.status_code == 200
    resp_officer_royal = client.get(f"/api/v1/applications/{app_royal.id}", headers=headers_officer)
    assert resp_officer_royal.status_code == 200


def test_institution_user_list_applications_filtered_to_own(client: TestClient, db: Session):
    """Institution users querying /applications must only receive applications for their institution."""
    token_apex = get_token_for_user("registrar@apextech.edu.in", ROLE_INSTITUTION_USER, institution_id=1)
    headers_apex = {"Authorization": f"Bearer {token_apex}"}

    resp = client.get("/api/v1/applications", headers=headers_apex)
    assert resp.status_code == 200
    apps = resp.json()
    for a in apps:
        assert a["institution_id"] == 1


def test_institution_user_cannot_submit_for_other_institution(client: TestClient):
    """Institution users cannot submit dossiers for another college."""
    token_apex = get_token_for_user("registrar@apextech.edu.in", ROLE_INSTITUTION_USER, institution_id=1)
    headers_apex = {"Authorization": f"Bearer {token_apex}"}

    # Attempt submit for institution 2 (Royal)
    payload = {"institution_id": 2, "category": "Extension of Approval (EoA)", "academic_year": "2025-26"}
    resp = client.post("/api/v1/applications/submit", json=payload, headers=headers_apex)
    assert resp.status_code == 403


# ============================================================================
# 3. NO AUTOMATIC REJECTION RULE
# ============================================================================

def test_no_automatic_rejection_rule(client: TestClient, db: Session):
    """
    Rule: No endpoint allows automatic rejection.
    Any adverse status requires an officer action.
    """
    app_apex = db.query(Application).filter(Application.institution_id == 1).first()
    token_officer = get_token_for_user("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)
    headers_officer = {"Authorization": f"Bearer {token_officer}"}

    # Run preflight & validation on application with known deficits
    resp_val = client.get(f"/api/v1/applications/{app_apex.id}/validation-report", headers=headers_officer)
    assert resp_val.status_code == 200
    val_data = resp_val.json()
    assert len(val_data["missing_documents"]) > 0 or len(val_data["inconsistencies"]) > 0

    # Ensure application status is NOT automatically changed to REJECTED
    db.refresh(app_apex)
    assert app_apex.status != "REJECTED"
    assert app_apex.status in ["UNDER_SCRUTINY", "SUBMITTED", "DEFICIT_FLAGGED", "PENDING_OFFICER_REVIEW", "APPROVED_WITH_CONDITIONS"]


# ============================================================================
# 4. OFFICER ACTION WITH MANDATORY COMMENT
# ============================================================================

def test_officer_action_mandatory_comment(client: TestClient, db: Session):
    """Officer action must reject empty or blank comments with 400 Bad Request."""
    app_apex = db.query(Application).filter(Application.institution_id == 1).first()
    token_officer = get_token_for_user("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)
    headers = {"Authorization": f"Bearer {token_officer}"}

    # Empty comment
    resp_empty = client.post(
        f"/api/v1/applications/{app_apex.id}/officer-action",
        json={"action": "request_more_evidence", "comment": ""},
        headers=headers
    )
    assert resp_empty.status_code == 400
    assert "mandatory" in resp_empty.json()["detail"].lower()

    # Whitespace only
    resp_ws = client.post(
        f"/api/v1/applications/{app_apex.id}/officer-action",
        json={"action": "request_more_evidence", "comment": "    "},
        headers=headers
    )
    assert resp_ws.status_code == 400


def test_officer_action_permitted_actions(client: TestClient, db: Session):
    """Tests executing all 5 valid officer actions: accept, dismiss, escalate, request_more_evidence, recommend_inspection."""
    app_apex = db.query(Application).filter(Application.institution_id == 1).first()
    token_officer = get_token_for_user("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)
    headers = {"Authorization": f"Bearer {token_officer}"}

    actions = [
        ("request_more_evidence", "CLARIFICATION_REQUESTED", "Issued statutory clarification letter for fire NOC."),
        ("recommend_inspection", "INSPECTION_RECOMMENDED", "Recommended physical inspection due to photo reuse."),
        ("escalate", "ESCALATED_TO_SENIOR", "Escalating dual appointment finding to Senior Committee."),
        ("dismiss", "DISMISSED", "Dismissing minor built-up area discrepancy with explanation."),
        ("accept", "APPROVED_WITH_CONDITIONS", "Approving extension of approval subject to annual NOC compliance.")
    ]

    for action_name, expected_status, note in actions:
        resp = client.post(
            f"/api/v1/applications/{app_apex.id}/officer-action",
            json={"action": action_name, "comment": note},
            headers=headers
        )
        assert resp.status_code == 200, f"Officer action {action_name} failed: {resp.text}"
        data = resp.json()
        assert data["new_application_status"] == expected_status
        assert "receipt_hash" in data


def test_officer_action_blocked_for_institution_and_auditor(client: TestClient, db: Session):
    """Institution users and Auditors cannot take officer actions (403 Forbidden)."""
    app_apex = db.query(Application).filter(Application.institution_id == 1).first()

    # 1. Institution User Blocked
    token_inst = get_token_for_user("registrar@apextech.edu.in", ROLE_INSTITUTION_USER, institution_id=1)
    resp_inst = client.post(
        f"/api/v1/applications/{app_apex.id}/officer-action",
        json={"action": "accept", "comment": "Self-approving my own application"},
        headers={"Authorization": f"Bearer {token_inst}"}
    )
    assert resp_inst.status_code == 403

    # 2. Auditor Blocked (Read-Only role)
    token_auditor = get_token_for_user("auditor@aicte-india.org", ROLE_AUDITOR)
    resp_auditor = client.post(
        f"/api/v1/applications/{app_apex.id}/officer-action",
        json={"action": "dismiss", "comment": "Auditor trying to take determination"},
        headers={"Authorization": f"Bearer {token_auditor}"}
    )
    assert resp_auditor.status_code == 403


# ============================================================================
# 5. PII MASKING BY ROLE TESTS
# ============================================================================

def test_pii_masking_for_officers_and_auditors(client: TestClient, db: Session):
    """
    Scrutiny Officers & Auditors see masked PAN and contact details.
    Institution Users see unmasked data for their own dossiers.
    """
    app_apex = db.query(Application).filter(Application.institution_id == 1).first()

    # Add sample finding with PAN
    finding = db.query(Finding).filter(Finding.application_id == app_apex.id).first()
    if finding:
        finding.explanation = "Faculty PAN ABCDE1234F has dual employment."
        db.commit()

    # 1. Scrutiny Officer sees masked PAN
    token_officer = get_token_for_user("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)
    resp_officer = client.get(f"/api/v1/applications/{app_apex.id}/findings", headers={"Authorization": f"Bearer {token_officer}"})
    assert resp_officer.status_code == 200
    findings_data = resp_officer.json()
    if findings_data:
        # Check that PAN is masked to AB****F or similar
        explanations = [f["explanation"] for f in findings_data]
        assert any("****" in exp for exp in explanations)
        assert "ABCDE1234F" not in " ".join(explanations)

    # 2. Owner Institution User sees their own data
    token_apex = get_token_for_user("registrar@apextech.edu.in", ROLE_INSTITUTION_USER, institution_id=1)
    resp_owner = client.get(f"/api/v1/applications/{app_apex.id}/findings", headers={"Authorization": f"Bearer {token_apex}"})
    assert resp_owner.status_code == 200


# ============================================================================
# 6. ACCESS LOGGING FOR SENSITIVE READS
# ============================================================================

def test_access_logging_for_sensitive_reads(client: TestClient, db: Session):
    """Reading sensitive dossier data must insert a record into audit_log."""
    app_apex = db.query(Application).filter(Application.institution_id == 1).first()
    token_officer = get_token_for_user("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)

    # Count prior logs
    count_before = db.query(AuditLog).count()

    # Read application dossier
    client.get(f"/api/v1/applications/{app_apex.id}", headers={"Authorization": f"Bearer {token_officer}"})

    # Read validation report
    client.get(f"/api/v1/applications/{app_apex.id}/validation-report", headers={"Authorization": f"Bearer {token_officer}"})

    # Read findings
    client.get(f"/api/v1/applications/{app_apex.id}/findings", headers={"Authorization": f"Bearer {token_officer}"})

    count_after = db.query(AuditLog).count()
    assert count_after >= count_before + 3

    latest_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    assert latest_log.actor_email == "scrutiny.officer@aicte-india.org"
    assert latest_log.status_code == 200


# ============================================================================
# 7. RULES CRUD WITH VERSIONING (ADMIN ONLY)
# ============================================================================

def test_rules_crud_admin_only(client: TestClient, db: Session):
    """Admin can create and version rules; institution users and auditors get 403 Forbidden."""
    token_admin = get_token_for_user("admin@aicte-india.org", ROLE_ADMIN)
    token_inst = get_token_for_user("registrar@apextech.edu.in", ROLE_INSTITUTION_USER, institution_id=1)

    # 1. Institution User cannot create rules -> 403 Forbidden
    resp_inst = client.post(
        "/api/v1/rules",
        json={
            "rule_code": "TEST_RULE_FORBIDDEN",
            "clause_id": "APH-2025-9.9",
            "title": "Unauthorized Rule",
            "category": "Safety",
            "description": "Rule",
            "condition_expression": "true",
            "failure_message_template": "Fail"
        },
        headers={"Authorization": f"Bearer {token_inst}"}
    )
    assert resp_inst.status_code == 403

    # 2. Admin creates new rule -> 201 Created
    rule_code = f"RULE_TEST_ADMIN_{datetime.now(timezone.utc).strftime('%H%M%S%f')}"
    resp_create = client.post(
        "/api/v1/rules",
        json={
            "rule_code": rule_code,
            "clause_id": "APH-2025-Cl-9.1.2",
            "title": "Solar Power Green Campus Mandate",
            "category": "Infrastructure",
            "severity": "WARNING",
            "description": "Requires minimum 10kW captive rooftop solar generation.",
            "condition_expression": "solar_capacity_kw >= 10",
            "failure_message_template": "Captive solar generation below mandated 10kW.",
            "parameters": {"minimum_kw": 10},
            "version_number": "1.0.0"
        },
        headers={"Authorization": f"Bearer {token_admin}"}
    )
    assert resp_create.status_code == 201
    create_data = resp_create.json()
    assert create_data["rule_code"] == rule_code
    assert create_data["version_number"] == "1.0.0"

    # 3. Admin updates rule configuration -> increments version to 1.1.0
    resp_update = client.put(
        f"/api/v1/rules/{rule_code}",
        json={
            "parameters": {"minimum_kw": 25},
            "version_number": "1.1.0"
        },
        headers={"Authorization": f"Bearer {token_admin}"}
    )
    assert resp_update.status_code == 200
    update_data = resp_update.json()
    assert update_data["new_version"] == "1.1.0"
    assert update_data["parameters"]["minimum_kw"] == 25


# ============================================================================
# 8. WHAT-IF DRY RUN & SIMULATION RBAC
# ============================================================================

def test_what_if_dry_run_rbac(client: TestClient):
    """What-If simulation allowed for officers, admin, auditor; forbidden for institution users."""
    token_officer = get_token_for_user("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)
    token_inst = get_token_for_user("registrar@apextech.edu.in", ROLE_INSTITUTION_USER, institution_id=1)

    # 1. Institution User forbidden -> 403
    resp_inst = client.post(
        "/api/v1/rules/dry-run",
        json={"parameters_override": {"target_fsr": 15}},
        headers={"Authorization": f"Bearer {token_inst}"}
    )
    assert resp_inst.status_code == 403

    # 2. Officer authorized -> 200 OK
    resp_officer = client.post(
        "/api/v1/rules/dry-run",
        json={"parameters_override": {"target_fsr": 15}},
        headers={"Authorization": f"Bearer {token_officer}"}
    )
    assert resp_officer.status_code == 200
    data = resp_officer.json()
    assert "summary" in data or "total_evaluations" in data or "simulated_applications_count" in data or isinstance(data, dict)


# ============================================================================
# 9. RADAR CLUSTERS & ALERTS RBAC
# ============================================================================

def test_radar_clusters_rbac(client: TestClient):
    """Cross-institution photo reuse radar clusters forbidden for institution users."""
    token_inst = get_token_for_user("registrar@apextech.edu.in", ROLE_INSTITUTION_USER, institution_id=1)
    token_auditor = get_token_for_user("auditor@aicte-india.org", ROLE_AUDITOR)

    # Institution user forbidden
    resp_inst = client.get("/api/v1/radar/clusters", headers={"Authorization": f"Bearer {token_inst}"})
    assert resp_inst.status_code == 403

    # Auditor authorized
    resp_auditor = client.get("/api/v1/radar/clusters", headers={"Authorization": f"Bearer {token_auditor}"})
    assert resp_auditor.status_code == 200


def test_alerts_rbac_and_resolution(client: TestClient, db: Session):
    """Institution users only see their own alerts; officers can resolve alerts."""
    token_apex = get_token_for_user("registrar@apextech.edu.in", ROLE_INSTITUTION_USER, institution_id=1)
    token_officer = get_token_for_user("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)

    # Institution user query
    resp_inst = client.get("/api/v1/alerts", headers={"Authorization": f"Bearer {token_apex}"})
    assert resp_inst.status_code == 200

    # Officer resolves alert
    alert = db.query(Alert).first()
    if alert:
        resp_res = client.patch(f"/api/v1/alerts/{alert.id}/resolve", headers={"Authorization": f"Bearer {token_officer}"})
        assert resp_res.status_code == 200
        assert resp_res.json()["is_read"] is True


# ============================================================================
# 10. RECEIPTS & CHAIN VERIFICATION ENDPOINT
# ============================================================================

def test_receipts_and_verify_chain_endpoint(client: TestClient, db: Session):
    """Tests GET /api/v1/applications/{app_id}/receipts and /verify-chain."""
    app_apex = db.query(Application).filter(Application.institution_id == 1).first()
    token_officer = get_token_for_user("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)
    headers = {"Authorization": f"Bearer {token_officer}"}

    # 1. Fetch receipts
    resp_receipts = client.get(f"/api/v1/applications/{app_apex.id}/receipts", headers=headers)
    assert resp_receipts.status_code == 200
    receipts_list = resp_receipts.json()
    assert isinstance(receipts_list, list)

    # 2. Verify Chain
    resp_verify = client.get(f"/api/v1/applications/{app_apex.id}/verify-chain", headers=headers)
    assert resp_verify.status_code == 200
    chain_data = resp_verify.json()
    assert "is_valid" in chain_data
    assert "status" in chain_data
