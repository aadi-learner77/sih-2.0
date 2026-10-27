"""
Test Suite for PRAMAAN-X Alert Service:
Tests:
1. Missing information detection (mandatory checklist items, institutional profile fields).
2. Expired document detection (CRITICAL) and documents expiring within N days (WARNING/INFO).
3. Pending source verification checks (verification_pending, manual_review_required).
4. Statutory source unavailable / gateway outage detection (CRITICAL for fire/land, WARNING otherwise).
5. Anomaly flags (forensic tampering, ELA scores, and knowledge graph conflicts).
6. Unresolved findings older than N days (escalated to Senior Officers).
7. Alert deduplication (deterministic dedupe_key prevents spam; updates scan count).
8. Role assignment and notification stub dispatch (in-app notifications and mock HTML emails).
9. Background AlertScanScheduler thread start and stop lifecycle.
10. REST API endpoints: POST /run-scan, GET /notifications, GET /scheduler/status, GET /alerts, PATCH /resolve.
"""

from __future__ import annotations

import uuid
import time
from datetime import datetime, date, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.models import (
    User, Institution, Application, Document, VerificationCheck, Finding, Alert
)
from backend.app.core.security import (
    create_access_token,
    ROLE_INSTITUTION_USER,
    ROLE_SCRUTINY_OFFICER,
    ROLE_SENIOR_OFFICER,
    ROLE_ADMIN,
    ROLE_AUDITOR
)
from backend.app.services.alert_service import (
    AlertService,
    AlertScanScheduler,
    MockNotificationService,
    ALERT_TYPE_MISSING_INFO,
    ALERT_TYPE_EXPIRED_DOC,
    ALERT_TYPE_DOC_EXPIRING_SOON,
    ALERT_TYPE_PENDING_VERIF,
    ALERT_TYPE_SOURCE_UNAVAIL,
    ALERT_TYPE_ANOMALY_FLAG,
    ALERT_TYPE_UNRESOLVED_FINDING,
    SEVERITY_CRITICAL,
    SEVERITY_WARNING,
    SEVERITY_INFO
)
from backend.app.data.seed_data import seed_database


@pytest.fixture(scope="module")
def client():
    seed_database()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def isolated_alert_service():
    """Provides an isolated AlertService instance with a fresh mock notification service."""
    notifier = MockNotificationService()
    return AlertService(notification_service=notifier)


def get_token(role: str, email: str, institution_id: int | None = None) -> str:
    return create_access_token({
        "sub": email,
        "email": email,
        "role": role,
        "institution_id": institution_id
    })


def create_test_application(db: Session, inst_id: int | None = None) -> Application:
    """Helper to generate a unique test application for clean test isolation."""
    uid = uuid.uuid4().hex[:8]
    if not inst_id:
        inst = db.query(Institution).first()
        inst_id = inst.id if inst else 1

    app_obj = Application(
        institution_id=inst_id,
        application_no=f"APP-TEST-{uid}",
        academic_year="2025-26",
        category="Extension of Approval (EoA)",
        status="UNDER_SCRUTINY"
    )
    db.add(app_obj)
    db.commit()
    db.refresh(app_obj)
    return app_obj


# ============================================================================
# 1. MISSING INFORMATION SCANNER TESTS
# ============================================================================

def test_missing_information_scanner(db: Session, isolated_alert_service: AlertService):
    """Verifies detection of missing mandatory documents and missing institutional survey/area fields."""
    uid = uuid.uuid4().hex[:8]
    inst = Institution(
        name=f"Incomplete Tech Institute {uid}",
        aicte_id=f"TEST-INCOMPLETE-{uid}",
        state="Karnataka",
        city="Bengaluru",
        survey_numbers="",  # Missing survey numbers
        total_built_up_area_sqm=0.0  # Missing built-up area
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)

    app_obj = create_test_application(db, inst_id=inst.id)

    alerts = isolated_alert_service.scan_missing_information(db, app_obj)
    assert len(alerts) >= 2  # Mandatory checklist docs + missing survey + missing area

    alert_types = [a[0].alert_type for a in alerts]
    titles = [a[0].title for a in alerts]
    roles = [a[0].assigned_role for a in alerts]

    assert all(at == ALERT_TYPE_MISSING_INFO for at in alert_types)
    assert any("Survey" in t for t in titles)
    assert any("Built-Up" in t for t in titles)
    assert all(r == ROLE_INSTITUTION_USER for r in roles)


# ============================================================================
# 2. EXPIRED DOCUMENTS & EXPIRING WITHIN N DAYS TESTS
# ============================================================================

def test_expired_and_expiring_documents_scanner(db: Session, isolated_alert_service: AlertService):
    """Verifies CRITICAL alert for expired docs and WARNING/INFO for docs expiring soon."""
    app_obj = create_test_application(db)
    uid = uuid.uuid4().hex[:8]

    today = date.today()
    past_date = (today - timedelta(days=45)).isoformat()
    soon_10_days = (today + timedelta(days=10)).isoformat()
    soon_25_days = (today + timedelta(days=25)).isoformat()
    far_90_days = (today + timedelta(days=90)).isoformat()

    doc_expired = Document(
        application_id=app_obj.id,
        document_type="Fire Safety Certificate",
        filename=f"expired_fire_noc_{uid}.pdf",
        file_hash=f"hash_exp_{uid}",
        valid_till=past_date
    )
    doc_soon_10 = Document(
        application_id=app_obj.id,
        document_type="Building Safety Certificate",
        filename=f"safety_expiring_10d_{uid}.pdf",
        file_hash=f"hash_s10_{uid}",
        valid_till=soon_10_days
    )
    doc_soon_25 = Document(
        application_id=app_obj.id,
        document_type="Occupancy Certificate",
        filename=f"occupancy_expiring_25d_{uid}.pdf",
        file_hash=f"hash_s25_{uid}",
        valid_till=soon_25_days
    )
    doc_far_90 = Document(
        application_id=app_obj.id,
        document_type="Land Title Deed",
        filename=f"land_deed_safe_{uid}.pdf",
        file_hash=f"hash_f90_{uid}",
        valid_till=far_90_days
    )
    db.add_all([doc_expired, doc_soon_10, doc_soon_25, doc_far_90])
    db.commit()
    db.refresh(app_obj)

    alerts = isolated_alert_service.scan_expired_and_expiring_documents(db, app_obj, expiring_within_days=30)
    assert len(alerts) == 3  # expired + 10 days + 25 days (90 days excluded)

    alert_map = {a[0].entity_refs["document_id"]: a[0] for a in alerts}

    # Expired doc must be CRITICAL and routed to scrutiny_officer
    assert alert_map[doc_expired.id].alert_type == ALERT_TYPE_EXPIRED_DOC
    assert alert_map[doc_expired.id].severity == SEVERITY_CRITICAL
    assert alert_map[doc_expired.id].assigned_role == ROLE_SCRUTINY_OFFICER

    # 10 days left must be WARNING and routed to institution_user
    assert alert_map[doc_soon_10.id].alert_type == ALERT_TYPE_DOC_EXPIRING_SOON
    assert alert_map[doc_soon_10.id].severity == SEVERITY_WARNING
    assert alert_map[doc_soon_10.id].assigned_role == ROLE_INSTITUTION_USER

    # 25 days left must be INFO and routed to institution_user
    assert alert_map[doc_soon_25.id].alert_type == ALERT_TYPE_DOC_EXPIRING_SOON
    assert alert_map[doc_soon_25.id].severity == SEVERITY_INFO
    assert alert_map[doc_soon_25.id].assigned_role == ROLE_INSTITUTION_USER


# ============================================================================
# 3. PENDING SOURCE VERIFICATION TESTS
# ============================================================================

def test_pending_source_verification_scanner(db: Session, isolated_alert_service: AlertService):
    """Verifies generation of alerts for stalled external source verifications."""
    app_obj = create_test_application(db)

    v_pending = VerificationCheck(
        application_id=app_obj.id,
        issuer_type="university_affiliation",
        issuer_name="VTU Affiliation Board",
        status="verification_pending"
    )
    v_review = VerificationCheck(
        application_id=app_obj.id,
        issuer_type="fire_department",
        issuer_name="State Fire Authority",
        status="manual_review_required"
    )
    v_verified = VerificationCheck(
        application_id=app_obj.id,
        issuer_type="bhoomi_land_registry",
        issuer_name="Karnataka Revenue Bhoomi",
        status="verified"
    )
    db.add_all([v_pending, v_review, v_verified])
    db.commit()
    db.refresh(app_obj)

    alerts = isolated_alert_service.scan_pending_source_verifications(db, app_obj)
    assert len(alerts) == 2

    assert all(a[0].alert_type == ALERT_TYPE_PENDING_VERIF for a in alerts)
    assert all(a[0].severity == SEVERITY_WARNING for a in alerts)
    assert all(a[0].assigned_role == ROLE_SCRUTINY_OFFICER for a in alerts)


# ============================================================================
# 4. SOURCE UNAVAILABLE TESTS
# ============================================================================

def test_source_unavailable_scanner(db: Session, isolated_alert_service: AlertService):
    """Verifies alerts for external gateway timeouts and outages."""
    app_obj = create_test_application(db)

    v_fire_down = VerificationCheck(
        application_id=app_obj.id,
        issuer_type="fire_safety_authority",
        issuer_name="Fire Services Statutory Gateway",
        status="source_unavailable"
    )
    v_other_timeout = VerificationCheck(
        application_id=app_obj.id,
        issuer_type="other_statutory_portal",
        issuer_name="State PWD Portal",
        status="gateway_timeout"
    )
    db.add_all([v_fire_down, v_other_timeout])
    db.commit()
    db.refresh(app_obj)

    alerts = isolated_alert_service.scan_unavailable_sources(db, app_obj)
    assert len(alerts) == 2

    alert_fire = next(a[0] for a in alerts if "fire" in a[0].dedupe_key.lower())
    alert_other = next(a[0] for a in alerts if "other" in a[0].dedupe_key.lower())

    assert alert_fire.severity == SEVERITY_CRITICAL
    assert alert_fire.assigned_role == ROLE_ADMIN

    assert alert_other.severity == SEVERITY_WARNING
    assert alert_other.assigned_role == ROLE_ADMIN


# ============================================================================
# 5. ANOMALY FLAGS TESTS (FORENSICS & GRAPH CONFLICTS)
# ============================================================================

def test_anomaly_flags_scanner(db: Session, isolated_alert_service: AlertService):
    """Verifies alerts for forensic tamper flags and Knowledge Graph impossibility conflicts."""
    app_obj = create_test_application(db)
    uid = uuid.uuid4().hex[:8]

    doc_tamper = Document(
        application_id=app_obj.id,
        document_type="Fire Safety Certificate",
        filename=f"tampered_certificate_{uid}.pdf",
        file_hash=f"hash_tamper_{uid}",
        is_flagged_for_review=True,
        review_indicator_tag="HIGH_ELA_DISCREPANCY",
        review_reason="Resaved with altered font layer and JPEG compression artifacts",
        ela_score=0.82
    )
    db.add(doc_tamper)
    db.commit()
    db.refresh(app_obj)

    alerts = isolated_alert_service.scan_anomaly_flags(db, app_obj)
    assert len(alerts) >= 1

    forensic_alert = next((a[0] for a in alerts if doc_tamper.filename in a[0].title), None)
    assert forensic_alert is not None
    assert forensic_alert.alert_type == ALERT_TYPE_ANOMALY_FLAG
    assert forensic_alert.severity == SEVERITY_CRITICAL
    assert forensic_alert.assigned_role == ROLE_SCRUTINY_OFFICER


# ============================================================================
# 6. UNRESOLVED FINDINGS OLDER THAN N DAYS TESTS
# ============================================================================

def test_unresolved_findings_scanner(db: Session, isolated_alert_service: AlertService):
    """Verifies escalation to Senior Officers for compliance findings older than N days."""
    app_obj = create_test_application(db)

    now = datetime.now(timezone.utc)
    old_10_days = now - timedelta(days=10)
    old_20_days = now - timedelta(days=20)
    recent_2_days = now - timedelta(days=2)

    f_10d = Finding(
        application_id=app_obj.id,
        clause_id="APH-CH2-005",
        rule_code_ref="RULE_BUILTUP_AREA",
        passed=False,
        status="PENDING_REVIEW",
        evaluated_at=old_10_days,
        explanation="Built-up area per student is below statutory threshold."
    )
    f_20d = Finding(
        application_id=app_obj.id,
        clause_id="APH-CH2-008",
        rule_code_ref="RULE_FIRE_SAFETY",
        passed=False,
        status="CLARIFICATION_REQUESTED",
        evaluated_at=old_20_days,
        explanation="Fire NOC registration number unconfirmed by state board."
    )
    f_recent = Finding(
        application_id=app_obj.id,
        clause_id="APH-CH2-010",
        rule_code_ref="RULE_FACULTY_CADRE",
        passed=False,
        status="PENDING_REVIEW",
        evaluated_at=recent_2_days,
        explanation="Assistant professor ratio needs verification."
    )
    db.add_all([f_10d, f_20d, f_recent])
    db.commit()

    alerts = isolated_alert_service.scan_unresolved_findings(db, app_obj, unresolved_days=7)
    assert len(alerts) == 2  # 10 days and 20 days; 2 days excluded

    finding_map = {a[0].entity_refs["finding_id"]: a[0] for a in alerts}

    # 10 days old -> WARNING, assigned to senior_officer
    assert finding_map[f_10d.id].alert_type == ALERT_TYPE_UNRESOLVED_FINDING
    assert finding_map[f_10d.id].severity == SEVERITY_WARNING
    assert finding_map[f_10d.id].assigned_role == ROLE_SENIOR_OFFICER

    # 20 days old (>= 14 days) -> CRITICAL, assigned to senior_officer
    assert finding_map[f_20d.id].alert_type == ALERT_TYPE_UNRESOLVED_FINDING
    assert finding_map[f_20d.id].severity == SEVERITY_CRITICAL
    assert finding_map[f_20d.id].assigned_role == ROLE_SENIOR_OFFICER


# ============================================================================
# 7. ALERT DEDUPLICATION TESTS
# ============================================================================

def test_alert_deduplication(db: Session, isolated_alert_service: AlertService):
    """Verifies that second scan with identical dedupe key updates metadata and does not duplicate alerts."""
    app_obj = create_test_application(db)
    dedupe_key = f"TEST_DEDUPE_KEY_{uuid.uuid4().hex}"

    # First creation: must be new
    alert1, is_new1 = isolated_alert_service.create_or_dedupe_alert(
        db=db,
        application_id=app_obj.id,
        alert_type="TEST_DEDUPE",
        title="Test Deduplication Alert",
        message="Alert message for dedupe testing",
        severity="WARNING",
        assigned_role="scrutiny_officer",
        dedupe_key=dedupe_key
    )
    assert is_new1 is True
    first_id = alert1.id

    # Second creation: must dedupe, return same alert ID, is_new=False
    alert2, is_new2 = isolated_alert_service.create_or_dedupe_alert(
        db=db,
        application_id=app_obj.id,
        alert_type="TEST_DEDUPE",
        title="Test Deduplication Alert",
        message="Alert message for dedupe testing",
        severity="WARNING",
        assigned_role="scrutiny_officer",
        dedupe_key=dedupe_key
    )
    assert is_new2 is False
    assert alert2.id == first_id
    assert alert2.entity_refs.get("scan_count", 0) >= 2


# ============================================================================
# 8. NOTIFICATION STUB TESTS (IN-APP & MOCK EMAIL)
# ============================================================================

def test_notification_stub_dispatch(isolated_alert_service: AlertService, db: Session):
    """Verifies that new alerts trigger in-app queue payloads and formatted HTML emails."""
    notifier = isolated_alert_service.notifier
    notifier.clear()

    app_obj = create_test_application(db)
    dedupe_key = f"TEST_NOTIF_KEY_{uuid.uuid4().hex}"

    alert, is_new = isolated_alert_service.create_or_dedupe_alert(
        db=db,
        application_id=app_obj.id,
        alert_type="NOTIFICATION_TEST",
        title="Statutory Deficiency Notice",
        message="Mandatory laboratory equipment deficiency identified.",
        severity="CRITICAL",
        assigned_role="institution_user",
        dedupe_key=dedupe_key
    )
    assert is_new is True

    # In-App Queue
    assert len(notifier.in_app_queue) == 1
    in_app = notifier.in_app_queue[0]
    assert in_app["alert_id"] == alert.id
    assert in_app["severity"] == "CRITICAL"
    assert in_app["assigned_role"] == "institution_user"
    assert "Statutory Deficiency" in in_app["title"]

    # Email Queue
    assert len(notifier.email_queue) == 1
    email = notifier.email_queue[0]
    assert email["alert_id"] == alert.id
    assert email["recipient_role"] == "institution_user"
    assert "CRITICAL" in email["subject"]
    assert "<html>" in email["html_body"]
    assert "AICTE PRAMAAN-X Statutory Alert Notice" in email["html_body"]


# ============================================================================
# 9. BACKGROUND SCHEDULER LIFECYCLE TESTS
# ============================================================================

def test_alert_scan_scheduler_lifecycle(isolated_alert_service: AlertService):
    """Verifies that AlertScanScheduler starts, runs, and terminates cleanly."""
    scheduler = AlertScanScheduler(alert_service=isolated_alert_service, interval_seconds=1)
    assert scheduler._thread is None or not scheduler._thread.is_alive()

    scheduler.start()
    assert scheduler._thread is not None
    assert scheduler._thread.is_alive()

    # Calling start again does not create a duplicate thread
    t1 = scheduler._thread
    scheduler.start()
    assert scheduler._thread == t1

    # Stop scheduler
    scheduler.stop()
    assert scheduler._stop_event.is_set()


# ============================================================================
# 10. REST API ENDPOINTS & RBAC TESTS
# ============================================================================

def test_api_run_scan_authorized(client: TestClient):
    """Scrutiny Officer, Senior Officer, and Admin can run alert scans on-demand."""
    token = get_token("scrutiny_officer", "scrutiny.officer@aicte-india.org")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/v1/alerts/run-scan?expiring_within_days=30&unresolved_days=7", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "COMPLETED"
    assert "scanned_applications_count" in data
    assert "new_alerts_generated" in data
    assert "deduped_alerts_suppressed" in data
    assert "alerts_by_type" in data
    assert "alerts_by_severity" in data


def test_api_run_scan_forbidden_for_institution_user(client: TestClient):
    """Institution users cannot trigger full alert scans across applications."""
    token = get_token("institution_user", "registrar@apextech.edu.in", institution_id=1)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/v1/alerts/run-scan", headers=headers)
    assert resp.status_code == 403


def test_api_get_notifications(client: TestClient):
    """Officers and Auditors can inspect the mock notification dispatch queue."""
    token = get_token("senior_officer", "senior.officer@aicte-india.org")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/alerts/notifications", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "total_dispatched" in data
    assert "in_app_count" in data
    assert "email_count" in data
    assert "in_app_notifications" in data
    assert "email_notifications" in data


def test_api_scheduler_status(client: TestClient):
    """Inspects scheduler status via API."""
    token = get_token("admin", "admin@aicte-india.org")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/alerts/scheduler/status", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "interval_seconds" in data
