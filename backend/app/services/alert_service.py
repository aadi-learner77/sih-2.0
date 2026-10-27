"""
PRAMAAN-X Alert Generation, Deduplication, Role Assignment & Notification Service.

Monitors active institutional applications and triggers alerts for:
1. Missing Information (mandatory checklist documents, essential institutional fields)
2. Expired Documents (lapsed certifications)
3. Documents Expiring Within N Days (proactive renewal warnings)
4. Pending Source Verifications (stalled external API checks)
5. Source Unavailable (external statutory gateway outages)
6. Anomaly Flags (forensic image manipulation, photo reuse radar, ghost faculty graph conflicts)
7. Unresolved Findings Older than N Days (stagnant regulatory scrutiny items requiring escalation)

Governance & Architecture:
- Deduplication: Deterministic dedupe keys prevent alert spam.
- Severity Assignment: CRITICAL, WARNING, INFO based on statutory regulatory risk.
- Role Assignment: Routes alerts to institution_user, scrutiny_officer, senior_officer, admin, auditor.
- Notification Stub: Dispatches in-app notification records and mock formatted regulatory emails.
- Periodic Scheduler: Runs periodic automated checks across all active applications.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.core.database import SessionLocal
from backend.app.models.models import (
    Alert, Application, Document, VerificationCheck, Finding,
    Institution, User
)
from backend.app.services.checklist_engine import generate_checklist_status
from backend.app.services.impossibility_engine import impossibility_engine

logger = logging.getLogger("pramaan_x.alert_service")

# Alert Types
ALERT_TYPE_MISSING_INFO = "MISSING_INFORMATION"
ALERT_TYPE_EXPIRED_DOC = "EXPIRED_DOCUMENT"
ALERT_TYPE_DOC_EXPIRING_SOON = "DOCUMENT_EXPIRING_SOON"
ALERT_TYPE_PENDING_VERIF = "PENDING_SOURCE_VERIFICATION"
ALERT_TYPE_SOURCE_UNAVAIL = "SOURCE_UNAVAILABLE"
ALERT_TYPE_ANOMALY_FLAG = "ANOMALY_FLAG"
ALERT_TYPE_UNRESOLVED_FINDING = "UNRESOLVED_FINDINGS"

# Severities
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFO"

# Role Targets
ROLE_INSTITUTION_USER = "institution_user"
ROLE_SCRUTINY_OFFICER = "scrutiny_officer"
ROLE_SENIOR_OFFICER = "senior_officer"
ROLE_ADMIN = "admin"
ROLE_AUDITOR = "auditor"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================================
# 1. NOTIFICATION STUB (IN-APP & MOCK EMAIL)
# ============================================================================

class MockNotificationService:
    """
    Mock notification dispatcher for statutory alerts:
    - In-App notification logging
    - Mock email dispatch with rich HTML formatting and recipient resolution
    """
    def __init__(self):
        self.email_queue: List[Dict[str, Any]] = []
        self.in_app_queue: List[Dict[str, Any]] = []

    def clear(self):
        self.email_queue.clear()
        self.in_app_queue.clear()

    def dispatch_in_app(
        self,
        alert_id: int,
        application_no: str,
        title: str,
        severity: str,
        assigned_role: str
    ) -> Dict[str, Any]:
        """Dispatches in-app notification payload."""
        payload = {
            "notification_id": len(self.in_app_queue) + 1,
            "alert_id": alert_id,
            "application_no": application_no,
            "title": title,
            "severity": severity,
            "assigned_role": assigned_role,
            "created_at": utc_now().isoformat()
        }
        self.in_app_queue.append(payload)
        logger.info(f"[IN-APP NOTIFICATION] [{severity}] Role: {assigned_role} | {title}")
        return payload

    def dispatch_mock_email(
        self,
        alert_id: int,
        to_email: str,
        recipient_role: str,
        application_no: str,
        institution_name: str,
        alert_type: str,
        title: str,
        message: str,
        severity: str
    ) -> Dict[str, Any]:
        """Dispatches formatted mock email for statutory alert."""
        subject = f"[AICTE PRAMAAN-X Alert] [{severity}] {title} - {application_no}"
        
        # HTML Email Template
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #1e293b; background: #f8fafc; padding: 24px;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden;">
                <div style="background: {'#dc2626' if severity == 'CRITICAL' else ('#d97706' if severity == 'WARNING' else '#2563eb')}; padding: 16px; color: #ffffff;">
                    <h3 style="margin: 0;">AICTE PRAMAAN-X Statutory Alert Notice</h3>
                    <small>Application: {application_no} | Severity: {severity}</small>
                </div>
                <div style="padding: 24px;">
                    <p>Dear <strong>{recipient_role.replace('_', ' ').title()}</strong>,</p>
                    <p>An operational alert has been triggered for <strong>{institution_name}</strong>:</p>
                    <div style="background: #f1f5f9; padding: 16px; border-left: 4px solid {'#dc2626' if severity == 'CRITICAL' else '#d97706'}; margin: 16px 0;">
                        <h4 style="margin: 0 0 8px 0;">{title}</h4>
                        <p style="margin: 0; font-size: 14px; line-height: 1.5;">{message}</p>
                    </div>
                    <p style="font-size: 13px; color: #64748b;">
                        Alert Category: <code>{alert_type}</code><br/>
                        Generated at: {utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </p>
                    <div style="margin-top: 24px;">
                        <a href="http://127.0.0.1:8000/api/v1/applications/{application_no}" style="background: #0f172a; color: #ffffff; padding: 10px 18px; text-decoration: none; border-radius: 4px; font-size: 14px;">
                            Review Dossier in Portal
                        </a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        email_record = {
            "email_id": len(self.email_queue) + 1,
            "alert_id": alert_id,
            "to_email": to_email,
            "recipient_role": recipient_role,
            "subject": subject,
            "severity": severity,
            "html_body": html_body,
            "sent_at": utc_now().isoformat()
        }
        self.email_queue.append(email_record)
        logger.info(f"[EMAIL DISPATCH] To: {to_email} ({recipient_role}) | Subject: {subject}")
        return email_record


mock_notification_service = MockNotificationService()


# ============================================================================
# 2. CORE ALERT GENERATION & DEDUPLICATION ENGINE
# ============================================================================

class AlertService:
    """
    Statutory Alert Generation & Management Engine.
    Scans application dossiers, documents, verifications, and findings.
    """

    def __init__(self, notification_service: Optional[MockNotificationService] = None):
        self.notifier = notification_service or mock_notification_service

    def create_or_dedupe_alert(
        self,
        db: Session,
        application_id: int,
        alert_type: str,
        title: str,
        message: str,
        severity: str,
        assigned_role: str,
        dedupe_key: str,
        entity_refs: Optional[Dict[str, Any]] = None
    ) -> Tuple[Alert, bool]:
        """
        Creates alert if not already active; otherwise dedupes and prevents alert spam.
        Returns: (Alert instance, is_new boolean)
        """
        # Check for unread active alert with the same dedupe key
        if dedupe_key:
            existing = db.query(Alert).filter(
                Alert.application_id == application_id,
                Alert.is_read == False,
                Alert.dedupe_key == dedupe_key
            ).first()
        else:
            existing = db.query(Alert).filter(
                Alert.application_id == application_id,
                Alert.is_read == False,
                Alert.title == title
            ).first()

        if existing:
            # Update entity refs with latest timestamp without spamming
            updated_refs = dict(existing.entity_refs or {})
            updated_refs["last_scanned_at"] = utc_now().isoformat()
            updated_refs["scan_count"] = updated_refs.get("scan_count", 1) + 1
            existing.entity_refs = updated_refs
            db.commit()
            return existing, False

        # Build entity refs
        refs = dict(entity_refs or {})
        refs["dedupe_key"] = dedupe_key
        refs["assigned_role"] = assigned_role
        refs["first_scanned_at"] = utc_now().isoformat()

        new_alert = Alert(
            application_id=application_id,
            alert_type=alert_type,
            severity=severity.upper(),
            title=title,
            message=message,
            entity_refs=refs,
            assigned_role=assigned_role,
            dedupe_key=dedupe_key,
            is_read=False,
            created_at=utc_now()
        )
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)

        # Retrieve application and institution details for notification dispatch
        app = db.query(Application).filter(Application.id == application_id).first()
        app_no = app.application_no if app else f"APP_{application_id}"
        inst_name = app.institution.name if (app and app.institution) else "Educational Institution"

        # 1. In-App Notification
        self.notifier.dispatch_in_app(
            alert_id=new_alert.id,
            application_no=app_no,
            title=title,
            severity=severity,
            assigned_role=assigned_role
        )

        # 2. Email Notification Stub
        target_email = self._resolve_target_email(db, app, assigned_role)
        self.notifier.dispatch_mock_email(
            alert_id=new_alert.id,
            to_email=target_email,
            recipient_role=assigned_role,
            application_no=app_no,
            institution_name=inst_name,
            alert_type=alert_type,
            title=title,
            message=message,
            severity=severity
        )

        return new_alert, True

    def _resolve_target_email(self, db: Session, app: Optional[Application], role: str) -> str:
        """Finds representative user email for the given role or provides standard address."""
        if role == ROLE_INSTITUTION_USER and app and app.institution_id:
            u = db.query(User).filter(User.institution_id == app.institution_id).first()
            if u:
                return u.email
            return f"registrar@inst{app.institution_id}.edu.in"
        elif role == ROLE_SCRUTINY_OFFICER:
            return "scrutiny.officer@aicte-india.org"
        elif role == ROLE_SENIOR_OFFICER:
            return "senior.officer@aicte-india.org"
        elif role == ROLE_ADMIN:
            return "admin@aicte-india.org"
        elif role == ROLE_AUDITOR:
            return "auditor@aicte-india.org"
        return "compliance.desk@aicte-india.org"

    # ========================================================================
    # 3. INDIVIDUAL SCANNERS / DETECTORS
    # ========================================================================

    def scan_missing_information(self, db: Session, app: Application) -> List[Tuple[Alert, bool]]:
        """Scans for missing mandatory checklist documents and missing institutional fields."""
        results = []
        checklist_status = generate_checklist_status(app.category, app.documents)

        # Check missing mandatory checklist documents
        if checklist_status.get("missing_items", 0) > 0:
            for item in checklist_status.get("items", []):
                if item.get("status") == "MISSING" and item.get("mandatory", True):
                    doc_name = item.get("document_type", "Mandatory Document")
                    item_code = item.get("checklist_code", doc_name.replace(" ", "_").upper())
                    
                    alert, is_new = self.create_or_dedupe_alert(
                        db=db,
                        application_id=app.id,
                        alert_type=ALERT_TYPE_MISSING_INFO,
                        title=f"Missing Mandatory Document: {doc_name}",
                        message=(
                            f"Application {app.application_no} is missing mandatory document '{doc_name}' "
                            f"under {app.category} requirements. Upload is required before scrutiny cutoff."
                        ),
                        severity=SEVERITY_CRITICAL if "fire" in doc_name.lower() or "land" in doc_name.lower() else SEVERITY_WARNING,
                        assigned_role=ROLE_INSTITUTION_USER,
                        dedupe_key=f"APP_{app.id}:MISSING_DOC:{item_code}",
                        entity_refs={"checklist_code": item_code, "document_type": doc_name}
                    )
                    results.append((alert, is_new))

        # Check essential institutional profile fields
        inst = app.institution
        if inst:
            if not inst.survey_numbers or "none" in str(inst.survey_numbers).lower():
                alert, is_new = self.create_or_dedupe_alert(
                    db=db,
                    application_id=app.id,
                    alert_type=ALERT_TYPE_MISSING_INFO,
                    title="Missing Land Survey / Khasra Numbers",
                    message=f"Institution '{inst.name}' has no registered survey/khasra numbers in profile.",
                    severity=SEVERITY_CRITICAL,
                    assigned_role=ROLE_INSTITUTION_USER,
                    dedupe_key=f"APP_{app.id}:MISSING_FIELD:survey_numbers",
                    entity_refs={"field": "survey_numbers", "institution_id": inst.id}
                )
                results.append((alert, is_new))

            if not inst.total_built_up_area_sqm or inst.total_built_up_area_sqm <= 0:
                alert, is_new = self.create_or_dedupe_alert(
                    db=db,
                    application_id=app.id,
                    alert_type=ALERT_TYPE_MISSING_INFO,
                    title="Missing Built-Up Area Specification",
                    message=f"Institution '{inst.name}' has declared 0.0 or unspecified total built-up area.",
                    severity=SEVERITY_CRITICAL,
                    assigned_role=ROLE_INSTITUTION_USER,
                    dedupe_key=f"APP_{app.id}:MISSING_FIELD:built_up_area",
                    entity_refs={"field": "total_built_up_area_sqm", "institution_id": inst.id}
                )
                results.append((alert, is_new))

        return results

    def scan_expired_and_expiring_documents(
        self,
        db: Session,
        app: Application,
        expiring_within_days: int = 30
    ) -> List[Tuple[Alert, bool]]:
        """
        Scans all documents for:
        1. Already expired documents (valid_till < today) -> CRITICAL alert.
        2. Documents expiring within N days (today <= valid_till <= today + N) -> WARNING/INFO alert.
        """
        results = []
        today = date.today()
        threshold_date = today + timedelta(days=expiring_within_days)

        for doc in app.documents:
            expiry_date = self._parse_document_expiry_date(doc)
            if not expiry_date:
                continue

            if expiry_date < today:
                # Already expired!
                days_expired = (today - expiry_date).days
                alert, is_new = self.create_or_dedupe_alert(
                    db=db,
                    application_id=app.id,
                    alert_type=ALERT_TYPE_EXPIRED_DOC,
                    title=f"Expired Statutory Document: {doc.document_type}",
                    message=(
                        f"Document '{doc.filename}' ({doc.document_type}) lapsed on {expiry_date.isoformat()} "
                        f"({days_expired} days ago). Submission of active renewed certificate is mandatory."
                    ),
                    severity=SEVERITY_CRITICAL,
                    assigned_role=ROLE_SCRUTINY_OFFICER,
                    dedupe_key=f"APP_{app.id}:DOC_EXPIRED:{doc.id}",
                    entity_refs={"document_id": doc.id, "expiry_date": expiry_date.isoformat(), "days_expired": days_expired}
                )
                results.append((alert, is_new))

            elif today <= expiry_date <= threshold_date:
                # Expiring soon within N days
                days_left = (expiry_date - today).days
                severity = SEVERITY_WARNING if days_left <= 15 else SEVERITY_INFO
                alert, is_new = self.create_or_dedupe_alert(
                    db=db,
                    application_id=app.id,
                    alert_type=ALERT_TYPE_DOC_EXPIRING_SOON,
                    title=f"Document Expiring in {days_left} Days: {doc.document_type}",
                    message=(
                        f"Document '{doc.filename}' ({doc.document_type}) will expire on {expiry_date.isoformat()} "
                        f"(in {days_left} days). Initiate renewal with issuing authority."
                    ),
                    severity=severity,
                    assigned_role=ROLE_INSTITUTION_USER,
                    dedupe_key=f"APP_{app.id}:DOC_EXPIRING_SOON:{doc.id}",
                    entity_refs={"document_id": doc.id, "expiry_date": expiry_date.isoformat(), "days_left": days_left}
                )
                results.append((alert, is_new))

        return results

    def _parse_document_expiry_date(self, doc: Document) -> Optional[date]:
        """Extracts and parses expiry date from document fields."""
        fields = doc.structured_fields or {}
        raw_val = fields.get("valid_till") or fields.get("expiry_date") or doc.valid_till
        if not raw_val:
            return None

        if isinstance(raw_val, date) and not isinstance(raw_val, datetime):
            return raw_val
        if isinstance(raw_val, datetime):
            return raw_val.date()

        clean_val = str(raw_val).strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(clean_val, fmt).date()
            except ValueError:
                pass
        return None

    def scan_pending_source_verifications(
        self,
        db: Session,
        app: Application,
        pending_hours: int = 24
    ) -> List[Tuple[Alert, bool]]:
        """Scans for verification queries with status 'verification_pending'."""
        results = []
        for v in app.verifications:
            if v.status in ("verification_pending", "manual_review_required"):
                alert, is_new = self.create_or_dedupe_alert(
                    db=db,
                    application_id=app.id,
                    alert_type=ALERT_TYPE_PENDING_VERIF,
                    title=f"Pending Verification Check: {v.issuer_name}",
                    message=(
                        f"Verification query against '{v.issuer_name}' ({v.issuer_type}) remains {v.status}. "
                        f"Awaiting response or manual committee routing."
                    ),
                    severity=SEVERITY_WARNING,
                    assigned_role=ROLE_SCRUTINY_OFFICER,
                    dedupe_key=f"APP_{app.id}:PENDING_VERIF:{v.issuer_type}:{v.id}",
                    entity_refs={"verification_id": v.id, "issuer_type": v.issuer_type, "status": v.status}
                )
                results.append((alert, is_new))
        return results

    def scan_unavailable_sources(self, db: Session, app: Application) -> List[Tuple[Alert, bool]]:
        """Scans for external gateway outages or timeouts ('source_unavailable')."""
        results = []
        for v in app.verifications:
            if v.status in ("source_unavailable", "gateway_timeout", "service_error"):
                # Critical if fire NOC or land title gateway is down
                is_critical = any(kw in v.issuer_type.lower() for kw in ("fire", "land", "revenue", "bhoomi"))
                severity = SEVERITY_CRITICAL if is_critical else SEVERITY_WARNING

                alert, is_new = self.create_or_dedupe_alert(
                    db=db,
                    application_id=app.id,
                    alert_type=ALERT_TYPE_SOURCE_UNAVAIL,
                    title=f"Statutory Gateway Unavailable: {v.issuer_name}",
                    message=(
                        f"Authoritative issuer gateway '{v.issuer_name}' ({v.issuer_type}) is currently unavailable "
                        f"or timing out. Retry scheduled with exponential backoff."
                    ),
                    severity=severity,
                    assigned_role=ROLE_ADMIN,
                    dedupe_key=f"APP_{app.id}:SOURCE_UNAVAIL:{v.issuer_type}",
                    entity_refs={"issuer_type": v.issuer_type, "issuer_name": v.issuer_name, "severity": severity}
                )
                results.append((alert, is_new))
        return results

    def scan_anomaly_flags(self, db: Session, app: Application) -> List[Tuple[Alert, bool]]:
        """
        Scans for forensic anomalies:
        - Image manipulation / ELA anomalies / metadata tampering
        - Knowledge Graph impossibility conflicts (dual employment, ghost faculty)
        - Photo Reuse Radar cross-institutional duplicates
        """
        results = []

        # 1. Document Forensics Anomaly Flags
        for doc in app.documents:
            if doc.is_flagged_for_review or (doc.ela_score and doc.ela_score > 0.60):
                tag = doc.review_indicator_tag or "DIGITAL_FORENSICS_ANOMALY"
                alert, is_new = self.create_or_dedupe_alert(
                    db=db,
                    application_id=app.id,
                    alert_type=ALERT_TYPE_ANOMALY_FLAG,
                    title=f"Forensic Tamper Indicator: {doc.filename}",
                    message=(
                        f"Document '{doc.filename}' ({doc.document_type}) triggered forensic indicator [{tag}]. "
                        f"Reason: {doc.review_reason or 'Compression variance or manipulation signature detected.'}"
                    ),
                    severity=SEVERITY_CRITICAL if (doc.ela_score and doc.ela_score > 0.70) else SEVERITY_WARNING,
                    assigned_role=ROLE_SCRUTINY_OFFICER,
                    dedupe_key=f"APP_{app.id}:FORENSIC_FLAG:{doc.id}",
                    entity_refs={"document_id": doc.id, "ela_score": doc.ela_score, "tag": tag}
                )
                results.append((alert, is_new))

        # 2. Knowledge Graph Impossibility Conflicts
        try:
            target_inst_code = f"INST_00{app.institution_id}"
            impossibilities = impossibility_engine.detect_all_impossibilities(target_inst_id=target_inst_code)
            for imp in impossibilities:
                conflict_type = imp.get("conflict_type") or imp.get("check_id") or "GRAPH_CONFLICT"
                entity_ids = imp.get("entity_ids") or []
                entity_key = imp.get("entity_id") or (entity_ids[0] if entity_ids else "E1")
                sanitized_refs = {k: v for k, v in imp.items() if k != "conflicting_subgraph"}

                alert, is_new = self.create_or_dedupe_alert(
                    db=db,
                    application_id=app.id,
                    alert_type=ALERT_TYPE_ANOMALY_FLAG,
                    title=f"Conflict Anomaly: {imp.get('title', 'Regulatory Conflict')}",
                    message=imp.get("explanation", "Cross-institutional constraint conflict detected."),
                    severity=SEVERITY_CRITICAL if imp.get("severity") == "CRITICAL" else SEVERITY_WARNING,
                    assigned_role=ROLE_SENIOR_OFFICER,
                    dedupe_key=f"APP_{app.id}:GRAPH_CONFLICT:{conflict_type}:{entity_key}",
                    entity_refs=sanitized_refs
                )
                results.append((alert, is_new))
        except Exception as e:
            logger.debug(f"Knowledge graph impossibility scan skipped: {e}")

        return results

    def scan_unresolved_findings(
        self,
        db: Session,
        app: Application,
        unresolved_days: int = 7
    ) -> List[Tuple[Alert, bool]]:
        """
        Scans for scrutiny findings that have remained in PENDING_REVIEW or CLARIFICATION_REQUESTED
        for more than N days without determination. Escalates to Senior Officers.
        """
        results = []
        now = utc_now()
        threshold_dt = now - timedelta(days=unresolved_days)

        findings = db.query(Finding).filter(
            Finding.application_id == app.id,
            Finding.passed == False,
            Finding.status.in_(["PENDING_REVIEW", "CLARIFICATION_REQUESTED"]),
            Finding.evaluated_at <= threshold_dt
        ).all()

        for f in findings:
            eval_dt = f.evaluated_at
            if not eval_dt:
                continue
            if eval_dt.tzinfo is None:
                eval_dt = eval_dt.replace(tzinfo=timezone.utc)
            age_days = max(0, (now - eval_dt).days)
            severity = SEVERITY_CRITICAL if age_days >= 14 else SEVERITY_WARNING

            alert, is_new = self.create_or_dedupe_alert(
                db=db,
                application_id=app.id,
                alert_type=ALERT_TYPE_UNRESOLVED_FINDING,
                title=f"Unresolved Finding ({age_days} Days Old): {f.clause_id}",
                message=(
                    f"Compliance finding on clause '{f.clause_id}' has remained unresolved for {age_days} days. "
                    f"Explanation: {f.explanation[:140]}... Immediate officer determination required."
                ),
                severity=severity,
                assigned_role=ROLE_SENIOR_OFFICER,  # Escalated to Senior Officer
                dedupe_key=f"APP_{app.id}:UNRESOLVED_FINDING:{f.id}",
                entity_refs={"finding_id": f.id, "clause_id": f.clause_id, "age_days": age_days, "status": f.status}
            )
            results.append((alert, is_new))

        return results

    # ========================================================================
    # 4. COMPREHENSIVE SCAN FOR ALL APPLICATIONS
    # ========================================================================

    def run_full_scan(
        self,
        db: Session,
        application_id: Optional[int] = None,
        expiring_within_days: int = 30,
        unresolved_days: int = 7
    ) -> Dict[str, Any]:
        """
        Executes end-to-end alert scan across active applications:
        - Missing information
        - Expired documents and documents expiring soon
        - Pending source verifications
        - Unavailable sources
        - Anomaly flags (forensics, graph conflicts)
        - Unresolved findings older than N days
        """
        query = db.query(Application).filter(Application.status != "REJECTED")
        if application_id:
            query = query.filter(Application.id == application_id)

        apps = query.all()
        total_new_alerts = 0
        total_deduped_alerts = 0
        alerts_by_type: Dict[str, int] = {}
        alerts_by_severity: Dict[str, int] = {}

        for app in apps:
            # Run all 6 scanners
            all_results: List[Tuple[Alert, bool]] = []
            all_results.extend(self.scan_missing_information(db, app))
            all_results.extend(self.scan_expired_and_expiring_documents(db, app, expiring_within_days))
            all_results.extend(self.scan_pending_source_verifications(db, app))
            all_results.extend(self.scan_unavailable_sources(db, app))
            all_results.extend(self.scan_anomaly_flags(db, app))
            all_results.extend(self.scan_unresolved_findings(db, app, unresolved_days))

            for alert, is_new in all_results:
                if is_new:
                    total_new_alerts += 1
                    alerts_by_type[alert.alert_type] = alerts_by_type.get(alert.alert_type, 0) + 1
                    alerts_by_severity[alert.severity] = alerts_by_severity.get(alert.severity, 0) + 1
                else:
                    total_deduped_alerts += 1

        return {
            "status": "COMPLETED",
            "timestamp": utc_now().isoformat(),
            "scanned_applications_count": len(apps),
            "new_alerts_generated": total_new_alerts,
            "deduped_alerts_suppressed": total_deduped_alerts,
            "alerts_by_type": alerts_by_type,
            "alerts_by_severity": alerts_by_severity,
            "notifications_dispatched": {
                "in_app": len(self.notifier.in_app_queue),
                "emails": len(self.notifier.email_queue)
            }
        }


# ============================================================================
# 5. PERIODIC SCHEDULER JOB
# ============================================================================

class AlertScanScheduler:
    """
    Background scheduler job that triggers periodic regulatory alert scans.
    Runs scans at regular intervals (e.g. hourly or daily).
    """

    def __init__(self, alert_service: AlertService, interval_seconds: int = 3600):
        self.service = alert_service
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Starts periodic background scanning thread."""
        if self._thread and self._thread.is_alive():
            logger.info("Alert scheduler thread already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="PramaanAlertScheduler")
        self._thread.start()
        logger.info(f"Started AlertScanScheduler thread (interval={self.interval_seconds}s)")

    def stop(self):
        """Signals scheduler thread to terminate cleanly."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            logger.info("Stopped AlertScanScheduler thread.")

    def _run_loop(self):
        """Periodic loop executing alert scan."""
        while not self._stop_event.is_set():
            db = SessionLocal()
            try:
                report = self.service.run_full_scan(db)
                logger.info(f"[SCHEDULER SCAN] Created {report['new_alerts_generated']} new alerts across {report['scanned_applications_count']} applications.")
            except Exception as e:
                logger.error(f"Error in AlertScanScheduler loop: {e}")
            finally:
                db.close()

            # Wait for next interval or stop event
            self._stop_event.wait(self.interval_seconds)


# Global Singleton Instances
alert_service = AlertService()
alert_scheduler = AlertScanScheduler(alert_service=alert_service, interval_seconds=3600)
