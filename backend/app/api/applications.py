"""
Applications and Scrutiny API Router for PRAMAAN-X:
Handles application submission, validation reports, advisory findings,
officer actions with mandatory comments, verification receipts, and chain audit.

Strict Security & Governance Rules:
1. RBAC: Institution users can only view and submit data for their own institution.
2. PII Masking: Applied to sensitive identifiers (Aadhaar, PAN, contact) based on user role.
3. Access Logging: Every read of sensitive dossier data is recorded in the immutable audit log.
4. No Automatic Rejection: Applications with deficits receive advisory flags; rejection requires an authorized Officer Action.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import (
    get_current_user,
    require_roles,
    enforce_institution_isolation,
    normalize_role,
    ROLE_INSTITUTION_USER,
    ROLE_SCRUTINY_OFFICER,
    ROLE_SENIOR_OFFICER,
    ROLE_ADMIN,
    ROLE_AUDITOR
)
from backend.app.core.logging_service import log_sensitive_access
from backend.app.core.masking import mask_pii_by_role
from backend.app.models.models import (
    Application, Institution, Document, VerificationReceipt,
    Finding, OfficerAction, RuleEvaluation, AuditReceipt
)
from backend.app.schemas.schemas import (
    ApplicationOut, ApplicationDetailOut, ApplicationSubmitRequest,
    OfficerActionRequest, PreflightScanResponse
)
from backend.app.services.checklist_engine import generate_checklist_status
from backend.app.services.validation_orchestrator import validation_orchestrator
from backend.app.services.verification_receipts import verify_chain, append_verification_receipt
from backend.app.services.audit_chain import AuditChainService

router = APIRouter(prefix="/applications", tags=["Applications & Scrutiny"])


# ============================================================================
# 1. LIST & GET APPLICATIONS (RBAC + ACCESS LOGGING + PII MASKING)
# ============================================================================

@router.get("", response_model=List[ApplicationOut])
def list_applications(
    category: Optional[str] = Query(None, description="Extension of Approval (EoA), etc."),
    status: Optional[str] = Query(None, description="Application status filter"),
    req: Request = None,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists applications.
    RBAC:
    - Institution Users: strictly restricted to their own institution's dossiers.
    - Officers, Admin, Auditor: can view all applications.
    """
    query = db.query(Application)
    user_role = normalize_role(current_user.role)

    if user_role == ROLE_INSTITUTION_USER:
        if not current_user.institution_id:
            return []
        query = query.filter(Application.institution_id == current_user.institution_id)

    if category:
        query = query.filter(Application.category == category)
    if status:
        query = query.filter(Application.status == status)

    apps = query.order_by(Application.created_at.desc()).all()

    # Log access for sensitive dossier listings
    log_sensitive_access(
        db=db,
        user=current_user,
        action="LIST_APPLICATIONS",
        resource="/api/v1/applications",
        details={"result_count": len(apps), "category_filter": category, "status_filter": status},
        request=req
    )

    results = []
    is_owner = (user_role == ROLE_INSTITUTION_USER)
    for app in apps:
        app_dict = ApplicationOut.model_validate(app).model_dump()
        app_dict["institution_name"] = app.institution.name if app.institution else "Unknown"
        masked_dict = mask_pii_by_role(app_dict, user_role, is_owner=is_owner)
        results.append(ApplicationOut(**masked_dict))

    return results


@router.get("/{app_id}", response_model=ApplicationDetailOut)
def get_application(
    app_id: int,
    req: Request = None,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves full institutional application dossier.
    Enforces tenant isolation for institution users, logs access, and masks PII.
    """
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Enforce Tenant Isolation
    enforce_institution_isolation(current_user, app.institution_id)

    # Log sensitive data access
    log_sensitive_access(
        db=db,
        user=current_user,
        action="READ_APPLICATION_DOSSIER",
        resource=f"/api/v1/applications/{app_id}",
        details={"application_id": app.id, "institution_id": app.institution_id},
        request=req
    )

    user_role = normalize_role(current_user.role)
    is_owner = (user_role == ROLE_INSTITUTION_USER and current_user.institution_id == app.institution_id)

    app_dict = ApplicationDetailOut.model_validate(app).model_dump()
    app_dict["institution_name"] = app.institution.name if app.institution else "Unknown"

    # Mask sensitive identifiers
    masked_dict = mask_pii_by_role(app_dict, user_role, is_owner=is_owner)
    return ApplicationDetailOut(**masked_dict)


# ============================================================================
# 2. APPLICATION SUBMISSION (NO AUTOMATIC REJECTION)
# ============================================================================

@router.post("/submit", response_model=ApplicationOut)
def submit_application(
    submission: ApplicationSubmitRequest,
    req: Request = None,
    current_user: Any = Depends(require_roles(ROLE_INSTITUTION_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Submits or re-submits an application for statutory scrutiny.
    RBAC: Institution users can only submit for their own institution.
    Governance Rule: Applications are never automatically rejected on submit.
    """
    enforce_institution_isolation(current_user, submission.institution_id)

    inst = db.query(Institution).filter(Institution.id == submission.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail=f"Institution ID {submission.institution_id} not found.")

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    app_no = f"APP-{inst.aicte_id}-{submission.academic_year}-{timestamp_str[:6]}"

    # Check if existing submitted application for this cycle
    existing = db.query(Application).filter(
        Application.institution_id == inst.id,
        Application.academic_year == submission.academic_year
    ).first()

    if existing:
        existing.status = "SUBMITTED"  # Never auto-reject
        existing.updated_at = datetime.now(timezone.utc)
        app = existing
    else:
        app = Application(
            application_no=app_no,
            institution_id=inst.id,
            category=submission.category or "Extension of Approval (EoA)",
            academic_year=submission.academic_year or "2025-26",
            status="SUBMITTED",  # Initial submitted state
            preflight_readiness_score=80.0,
            checklist_completion_pct=85.0
        )
        db.add(app)

    db.commit()
    db.refresh(app)

    log_sensitive_access(
        db=db,
        user=current_user,
        action="SUBMIT_APPLICATION",
        resource=f"/api/v1/applications/{app.id}/submit",
        details={"application_id": app.id, "application_no": app.application_no, "institution_id": inst.id},
        request=req
    )

    app_dict = ApplicationOut.model_validate(app).model_dump()
    app_dict["institution_name"] = inst.name
    return ApplicationOut(**app_dict)


# ============================================================================
# 3. PRE-FLIGHT READINESS SCAN
# ============================================================================

@router.post("/{app_id}/preflight")
def run_preflight_for_application(
    app_id: int,
    req: Request = None,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes pre-flight readiness checks for an application.
    Enforces tenant isolation. Does NOT automatically reject.
    """
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    enforce_institution_isolation(current_user, app.institution_id)

    # Execute validation orchestrator logic in advisory mode
    report = validation_orchestrator.validate_application(db, app.id)

    # Crucial Rule: Preflight readiness never automatically rejects
    if app.status == "REJECTED":
        app.status = "PENDING_OFFICER_REVIEW"
        db.commit()

    log_sensitive_access(
        db=db,
        user=current_user,
        action="RUN_PREFLIGHT",
        resource=f"/api/v1/applications/{app_id}/preflight",
        details={"application_id": app.id, "score": report.get("readiness_score")},
        request=req
    )

    user_role = normalize_role(current_user.role)
    is_owner = (user_role == ROLE_INSTITUTION_USER and current_user.institution_id == app.institution_id)
    return mask_pii_by_role(report, user_role, is_owner=is_owner)


# ============================================================================
# 4. GET VALIDATION REPORT
# ============================================================================

@router.get("/{app_id}/validation-report")
def get_validation_report(
    app_id: int,
    req: Request = None,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates structured statutory validation report:
    - Missing mandatory documents
    - Expired certifications
    - Incomplete schema fields
    - Cross-document / cross-institution inconsistencies
    - Regulation-as-Code rule evaluations
    - Explainable readiness score
    """
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    enforce_institution_isolation(current_user, app.institution_id)

    report = validation_orchestrator.validate_application(db, app.id)

    log_sensitive_access(
        db=db,
        user=current_user,
        action="GET_VALIDATION_REPORT",
        resource=f"/api/v1/applications/{app_id}/validation-report",
        details={"application_id": app.id, "readiness_score": report.get("readiness_score")},
        request=req
    )

    user_role = normalize_role(current_user.role)
    is_owner = (user_role == ROLE_INSTITUTION_USER and current_user.institution_id == app.institution_id)
    return mask_pii_by_role(report, user_role, is_owner=is_owner)


@router.post("/{app_id}/validate")
def validate_application_alias(
    app_id: int,
    req: Request = None,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alias for POST /{app_id}/validate executing application validation."""
    return get_validation_report(app_id=app_id, req=req, current_user=current_user, db=db)



# ============================================================================
# 5. LIST FINDINGS & ADVISORY INDICATORS
# ============================================================================

@router.get("/{app_id}/findings")
def list_application_findings(
    app_id: int,
    severity: Optional[str] = Query(None, description="CRITICAL, WARNING, ADVISORY"),
    status: Optional[str] = Query(None, description="PENDING_REVIEW, etc."),
    req: Request = None,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists advisory findings and discrepancies for an application dossier.
    Enforces tenant isolation, access logging, and PII masking.
    """
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    enforce_institution_isolation(current_user, app.institution_id)

    query = db.query(Finding).filter(Finding.application_id == app_id)
    if severity:
        query = query.filter(Finding.severity == severity.upper())
    if status:
        query = query.filter(Finding.status == status)

    findings = query.all()

    log_sensitive_access(
        db=db,
        user=current_user,
        action="LIST_FINDINGS",
        resource=f"/api/v1/applications/{app_id}/findings",
        details={"application_id": app.id, "count": len(findings)},
        request=req
    )

    user_role = normalize_role(current_user.role)
    is_owner = (user_role == ROLE_INSTITUTION_USER and current_user.institution_id == app.institution_id)

    results = []
    for f in findings:
        f_dict = {
            "id": f.id,
            "application_id": f.application_id,
            "rule_id": f.rule_code_ref or str(f.rule_id),
            "clause_id": f.clause_id,
            "clause_title": f.clause_title,
            "handbook_edition": f.handbook_edition,
            "severity": f.severity,
            "passed": f.passed,
            "status": f.status,
            "confidence": f.confidence,
            "claim_summary": f.claim_summary,
            "evidence_details": f.evidence_details,
            "explanation": f.explanation,
            "officer_decision": f.officer_decision,
            "officer_comment": f.officer_comment,
            "evaluated_at": f.evaluated_at.isoformat() if f.evaluated_at else None
        }
        results.append(mask_pii_by_role(f_dict, user_role, is_owner=is_owner))

    return results


@router.get("/findings/all")
def list_all_findings(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    req: Request = None,
    current_user: Any = Depends(require_roles(ROLE_SCRUTINY_OFFICER, ROLE_SENIOR_OFFICER, ROLE_ADMIN, ROLE_AUDITOR)),
    db: Session = Depends(get_db)
):
    """Lists findings across all applications. Prohibited for Institution Users."""
    query = db.query(Finding)
    if severity:
        query = query.filter(Finding.severity == severity.upper())
    if status:
        query = query.filter(Finding.status == status)

    findings = query.limit(100).all()

    log_sensitive_access(
        db=db,
        user=current_user,
        action="LIST_ALL_FINDINGS",
        resource="/api/v1/applications/findings/all",
        details={"count": len(findings)},
        request=req
    )

    user_role = normalize_role(current_user.role)
    results = []
    for f in findings:
        f_dict = {
            "id": f.id,
            "application_id": f.application_id,
            "rule_id": f.rule_code_ref or str(f.rule_id),
            "clause_id": f.clause_id,
            "severity": f.severity,
            "passed": f.passed,
            "status": f.status,
            "explanation": f.explanation,
            "officer_decision": f.officer_decision
        }
        results.append(mask_pii_by_role(f_dict, user_role, is_owner=False))
    return results


# ============================================================================
# 6. OFFICER ACTION (HUMAN IN THE LOOP - MANDATORY COMMENT)
# ============================================================================

@router.post("/{app_id}/officer-action")
def record_officer_action(
    app_id: int,
    action_req: OfficerActionRequest,
    req: Request = None,
    current_user: Any = Depends(require_roles(ROLE_SCRUTINY_OFFICER, ROLE_SENIOR_OFFICER, ROLE_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Officer Action: Human-in-the-loop statutory determination.
    
    Permitted Actions:
    - accept: Approves the dossier or finding
    - dismiss: Dismisses the advisory indicator
    - escalate: Escalates to Senior / Regional Scrutiny Officer
    - request_more_evidence: Issues formal clarification / show-cause notice
    - recommend_inspection: Mandates surprise physical or virtual 360 inspection
    - reject: Formal adverse rejection (can ONLY be done via this officer action)
    
    Governance Rules:
    - MANDATORY COMMENT: comment must be non-empty and substantiated.
    - Blocked for: institution_user (403), auditor (403).
    - Appends a cryptographically chained verification receipt to the audit log.
    """
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # 1. Validate Mandatory Comment
    comment = action_req.comment.strip() if action_req.comment else ""
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Officer comment is mandatory for all determinations. Please provide substantiating remarks."
        )

    # 2. Normalize and Validate Action
    raw_action = action_req.action.strip().lower()
    allowed_actions = {
        "accept": "APPROVED_WITH_CONDITIONS",
        "dismiss": "DISMISSED",
        "escalate": "ESCALATED_TO_SENIOR",
        "request_more_evidence": "CLARIFICATION_REQUESTED",
        "recommend_inspection": "INSPECTION_RECOMMENDED",
        "reject": "REJECTED"
    }

    # Also support existing enum names for backwards compatibility
    status_map = {
        "accepted_with_note": "APPROVED_WITH_CONDITIONS",
        "waived_with_reason": "DISMISSED",
        "clarification_issued": "CLARIFICATION_REQUESTED",
        "pending_review": "PENDING_REVIEW"
    }
    status_map.update(allowed_actions)

    if raw_action not in status_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Action '{action_req.action}' is not supported. Allowed actions: "
                f"accept, dismiss, escalate, request_more_evidence, recommend_inspection, reject"
            )
        )

    new_app_status = status_map[raw_action]

    # 3. Update Finding if finding_id provided
    finding = None
    if action_req.finding_id:
        finding = db.query(Finding).filter(
            Finding.id == action_req.finding_id,
            Finding.application_id == app.id
        ).first()
        if finding:
            finding.officer_decision = raw_action.upper()
            finding.officer_comment = comment
            finding.status = new_app_status

    # 4. Update Application Status
    app.status = new_app_status
    app.updated_at = datetime.now(timezone.utc)

    # 5. Record OfficerAction Entity
    action_record = OfficerAction(
        application_id=app.id,
        finding_id=finding.id if finding else None,
        officer_id=current_user.id,
        action_type=raw_action.upper(),
        justification_note=comment
    )
    db.add(action_record)
    db.commit()
    db.refresh(action_record)

    # 6. Append Immutable Verification Receipt to Chain
    import hashlib
    action_payload_hash = hashlib.sha256(
        f"{app.id}:{raw_action}:{comment}:{current_user.email}".encode("utf-8")
    ).hexdigest()

    receipt = append_verification_receipt(
        db=db,
        application_id=app.id,
        source=f"OfficerAction:{raw_action.upper()}",
        status="verified" if raw_action == "accept" else raw_action,
        response_hash=action_payload_hash,
        rule_version_set={"officer_email": current_user.email, "role": current_user.role, "action": raw_action}
    )

    # Log action
    log_sensitive_access(
        db=db,
        user=current_user,
        action=f"OFFICER_ACTION_{raw_action.upper()}",
        resource=f"/api/v1/applications/{app_id}/officer-action",
        details={
            "application_id": app.id,
            "action": raw_action,
            "comment_length": len(comment),
            "receipt_id": receipt.id
        },
        request=req
    )

    return {
        "status": "SUCCESS",
        "action_id": action_record.id,
        "action": raw_action,
        "application_id": app.id,
        "new_application_status": app.status,
        "comment": comment,
        "officer": current_user.full_name,
        "receipt_id": receipt.id,
        "receipt_hash": receipt.receipt_hash
    }


# ============================================================================
# 7. RECEIPTS LOG & CRYPTOGRAPHIC CHAIN VERIFICATION
# ============================================================================

@router.get("/{app_id}/receipts")
def get_application_verification_receipts(
    app_id: int,
    req: Request = None,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the chronological append-only hash-chained verification receipts for an application.
    Enforces tenant isolation for institution users.
    """
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    enforce_institution_isolation(current_user, app.institution_id)

    receipts = db.query(VerificationReceipt).filter(
        VerificationReceipt.application_id == app.id
    ).order_by(VerificationReceipt.id.asc()).all()

    log_sensitive_access(
        db=db,
        user=current_user,
        action="GET_RECEIPTS",
        resource=f"/api/v1/applications/{app_id}/receipts",
        details={"application_id": app.id, "receipts_count": len(receipts)},
        request=req
    )

    return [
        {
            "id": r.id,
            "application_id": r.application_id,
            "document_id": r.document_id,
            "source": r.source,
            "status": r.status,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "response_hash": r.response_hash,
            "rule_version_set": r.rule_version_set,
            "previous_hash": r.previous_hash,
            "receipt_hash": r.receipt_hash,
            "public_key": r.public_key,
            "signature": r.signature[:32] + "..."
        }
        for r in receipts
    ]


@router.get("/{app_id}/verify-chain")
def verify_application_receipt_chain(
    app_id: int,
    req: Request = None,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Runs cryptographic chain verification on the verification receipts ledger for an application.
    Validates:
    - Parent hash chaining
    - Canonical JSON SHA-256 integrity
    - Ed25519 digital signature authenticity
    Detects tampering and reports the first broken link.
    """
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    enforce_institution_isolation(current_user, app.institution_id)

    audit_result = verify_chain(db, application_id=app.id)

    log_sensitive_access(
        db=db,
        user=current_user,
        action="VERIFY_CHAIN",
        resource=f"/api/v1/applications/{app_id}/verify-chain",
        details={"application_id": app.id, "is_valid": audit_result.get("is_valid")},
        request=req
    )

    return audit_result
