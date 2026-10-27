"""
Operational Alerts API Router for PRAMAAN-X:
Provides endpoints for listing, filtering, and resolving operational warnings and risk flags.
Enforces RBAC: Institution users only see alerts relating to their own institution.
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import (
    get_current_user,
    require_roles,
    normalize_role,
    ROLE_INSTITUTION_USER,
    ROLE_SCRUTINY_OFFICER,
    ROLE_SENIOR_OFFICER,
    ROLE_ADMIN,
    ROLE_AUDITOR
)
from backend.app.core.logging_service import log_sensitive_access
from backend.app.core.masking import mask_pii_by_role
from backend.app.models.models import Alert, Application, User
from backend.app.schemas.schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["Operational Alerts & Warnings"])


@router.get("", response_model=List[AlertOut])
def list_alerts(
    application_id: Optional[int] = Query(None, description="Filter by application ID"),
    severity: Optional[str] = Query(None, description="CRITICAL, WARNING, INFO"),
    alert_type: Optional[str] = Query(None, description="Filter by alert category"),
    assigned_role: Optional[str] = Query(None, description="Filter by assigned role"),
    is_read: Optional[bool] = Query(None, description="Filter read/unread status"),
    req: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists operational alerts.
    RBAC Rules:
    - Institution Users: strictly limited to alerts on applications belonging to their institution.
    - Scrutiny Officers, Senior Officers, Admin, Auditor: can view cross-institutional alerts.
    """
    query = db.query(Alert).join(Application, Alert.application_id == Application.id)

    user_role = normalize_role(current_user.role)
    if user_role == ROLE_INSTITUTION_USER:
        if not current_user.institution_id:
            return []
        query = query.filter(Application.institution_id == current_user.institution_id)

    if application_id:
        query = query.filter(Alert.application_id == application_id)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type.upper())
    if assigned_role:
        query = query.filter(Alert.assigned_role == assigned_role.lower())
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)

    alerts = query.order_by(Alert.created_at.desc()).all()

    # Log sensitive data access
    log_sensitive_access(
        db=db,
        user=current_user,
        action="LIST_ALERTS",
        resource="/api/v1/alerts",
        details={"count": len(alerts), "severity": severity, "application_id": application_id},
        request=req
    )

    # Apply role-based PII masking to entity_refs (e.g. faculty_pan)
    results = []
    for a in alerts:
        a_dict = AlertOut.model_validate(a).model_dump()
        is_owner = (user_role == ROLE_INSTITUTION_USER)
        a_dict["entity_refs"] = mask_pii_by_role(a_dict.get("entity_refs", {}), user_role, is_owner=is_owner)
        results.append(AlertOut(**a_dict))

    return results


@router.post("/run-scan")
def trigger_alert_scan(
    application_id: Optional[int] = Query(None, description="Optional specific application ID to scan"),
    expiring_within_days: int = Query(30, description="Threshold in days for expiring document warnings"),
    unresolved_days: int = Query(7, description="Threshold in days for unresolved finding escalation"),
    req: Request = None,
    current_user: User = Depends(require_roles(ROLE_SCRUTINY_OFFICER, ROLE_SENIOR_OFFICER, ROLE_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Triggers an on-demand comprehensive regulatory alert scan across all active applications:
    - Missing information (mandatory checklist documents, essential institutional fields)
    - Expired documents and documents expiring soon (within N days)
    - Pending source verifications
    - Unavailable sources / statutory gateway timeouts
    - Anomaly flags (forensic tampering, knowledge graph impossibility conflicts)
    - Unresolved findings older than N days (escalated to Senior Officers)
    
    Supports deduplication, severity assignment, role routing, and notification stub dispatch.
    """
    from backend.app.services.alert_service import alert_service

    report = alert_service.run_full_scan(
        db=db,
        application_id=application_id,
        expiring_within_days=expiring_within_days,
        unresolved_days=unresolved_days
    )

    log_sensitive_access(
        db=db,
        user=current_user,
        action="RUN_ALERT_SCAN",
        resource="/api/v1/alerts/run-scan",
        details=report,
        request=req
    )

    return report


@router.get("/notifications")
def get_notification_logs(
    channel: Optional[str] = Query(None, description="Filter channel: 'in_app' or 'email'"),
    role: Optional[str] = Query(None, description="Filter recipient role"),
    severity: Optional[str] = Query(None, description="Filter severity: CRITICAL, WARNING, INFO"),
    current_user: User = Depends(require_roles(ROLE_SCRUTINY_OFFICER, ROLE_SENIOR_OFFICER, ROLE_ADMIN, ROLE_AUDITOR))
):
    """
    Inspects dispatched mock notification queues (both in-app alerts and formatted mock emails).
    Useful for compliance verification, test assertions, and audit trail inspection.
    """
    from backend.app.services.alert_service import mock_notification_service

    in_app = list(mock_notification_service.in_app_queue)
    emails = list(mock_notification_service.email_queue)

    if role:
        in_app = [n for n in in_app if n.get("assigned_role") == role.lower()]
        emails = [e for e in emails if e.get("recipient_role") == role.lower()]
    if severity:
        in_app = [n for n in in_app if n.get("severity") == severity.upper()]
        emails = [e for e in emails if e.get("severity") == severity.upper()]

    if channel == "in_app":
        return {"channel": "in_app", "count": len(in_app), "items": in_app}
    elif channel == "email":
        return {"channel": "email", "count": len(emails), "items": emails}

    return {
        "total_dispatched": len(in_app) + len(emails),
        "in_app_count": len(in_app),
        "email_count": len(emails),
        "in_app_notifications": in_app[-50:],
        "email_notifications": emails[-50:]
    }


@router.get("/scheduler/status")
def get_scheduler_status(
    current_user: User = Depends(require_roles(ROLE_SCRUTINY_OFFICER, ROLE_SENIOR_OFFICER, ROLE_ADMIN, ROLE_AUDITOR))
):
    """Returns the background scheduler job execution status."""
    from backend.app.services.alert_service import alert_scheduler

    is_running = alert_scheduler._thread is not None and alert_scheduler._thread.is_alive()
    return {
        "status": "RUNNING" if is_running else "STOPPED",
        "interval_seconds": alert_scheduler.interval_seconds,
        "is_alive": is_running,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/scheduler/start")
def start_scheduler(
    current_user: User = Depends(require_roles(ROLE_SENIOR_OFFICER, ROLE_ADMIN))
):
    """Starts the periodic background alert scanner thread."""
    from backend.app.services.alert_service import alert_scheduler
    alert_scheduler.start()
    return {
        "status": "STARTED",
        "interval_seconds": alert_scheduler.interval_seconds,
        "message": "Background alert scan scheduler started successfully."
    }


@router.post("/scheduler/stop")
def stop_scheduler(
    current_user: User = Depends(require_roles(ROLE_SENIOR_OFFICER, ROLE_ADMIN))
):
    """Stops the periodic background alert scanner thread."""
    from backend.app.services.alert_service import alert_scheduler
    alert_scheduler.stop()
    return {
        "status": "STOPPED",
        "message": "Background alert scan scheduler stopped cleanly."
    }


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: int,
    req: Request = None,
    current_user: User = Depends(require_roles(ROLE_SCRUTINY_OFFICER, ROLE_SENIOR_OFFICER, ROLE_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Marks an operational alert as reviewed and resolved.
    Authorized for Scrutiny Officers, Senior Officers, and Admins.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found.")

    alert.is_read = True
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)

    log_sensitive_access(
        db=db,
        user=current_user,
        action="RESOLVE_ALERT",
        resource=f"/api/v1/alerts/{alert_id}/resolve",
        details={"alert_id": alert.id, "alert_type": alert.alert_type},
        request=req
    )

    return alert

