"""
Access Logging Service for PRAMAAN-X:
Logs every access / read of sensitive institutional, forensic, or personal data
to guarantee regulatory compliance and immutable audit tracking.
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request

from backend.app.models.models import AuditLog, User

logger = logging.getLogger("pramaan_x.access_log")


def log_sensitive_access(
    db: Session,
    user: Optional[User],
    action: str,
    resource: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: str = "127.0.0.1",
    status_code: int = 200,
    request: Optional[Request] = None
) -> AuditLog:
    """
    Records an access event for sensitive data reads in the database audit log.
    Captures actor ID, email, role, requested resource, client IP, and contextual metadata.
    """
    if request:
        client = getattr(request, "client", None)
        if client and getattr(client, "host", None):
            ip_address = client.host

    actor_id = getattr(user, "id", None)
    actor_email = getattr(user, "email", "anonymous@unknown.org")
    actor_role = getattr(user, "role", "anonymous")

    log_entry = AuditLog(
        actor_id=actor_id,
        actor_email=actor_email,
        actor_role=actor_role,
        action=action,
        resource=resource,
        ip_address=ip_address,
        status_code=status_code,
        details=details or {}
    )

    try:
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        logger.info(
            f"[ACCESS_LOG] {actor_role}:{actor_email} -> {action} on {resource} (status={status_code})"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to record access log: {e}")

    return log_entry
