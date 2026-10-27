"""
Regulation-as-Code API Router for PRAMAAN-X:
Provides complete Rules CRUD with versioning and What-If Dry Run simulation.

RBAC Policies:
- Read (GET): Scrutiny Officer, Senior Officer, Admin, Auditor, Institution User.
- What-If Simulation: Scrutiny Officer, Senior Officer, Admin, Auditor. (Institution User forbidden).
- Mutation (POST/PUT/DELETE): Central AICTE Admin ONLY.
"""

from typing import List, Dict, Any, Optional
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
from backend.app.models.models import Rule, RuleVersion, RuleEvaluation, Application, User
from backend.app.schemas.schemas import (
    RuleEvaluationOut, OfficerDecisionUpdate,
    RuleCreateRequest, RuleUpdateRequest, WhatIfDryRunRequest
)
from backend.app.services.rules_engine import rules_engine
from backend.app.services.audit_chain import AuditChainService

router = APIRouter(prefix="/rules", tags=["Regulation-as-Code"])


# ============================================================================
# 1. READ RULES & VERSIONS (ALL AUTHENTICATED USERS)
# ============================================================================

@router.get("", response_model=List[Dict[str, Any]])
def list_rules(
    category: Optional[str] = Query(None, description="Faculty & Cadre, Infrastructure, Safety"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns active rules with their current version and handbook parameters."""
    query = db.query(Rule).filter(Rule.is_active == True)
    if category:
        query = query.filter(Rule.category == category)

    db_rules = query.order_by(Rule.id.asc()).all()
    results = []

    if db_rules:
        for r in db_rules:
            curr_ver = next((v for v in r.versions if v.is_current), r.versions[-1] if r.versions else None)
            results.append({
                "id": r.id,
                "rule_code": r.rule_code,
                "clause_id": r.clause_id,
                "title": r.title,
                "category": r.category,
                "severity": r.severity,
                "description": r.description,
                "is_active": r.is_active,
                "current_version": {
                    "id": curr_ver.id if curr_ver else None,
                    "version_number": curr_ver.version_number if curr_ver else "1.0.0",
                    "handbook_edition": curr_ver.handbook_edition if curr_ver else "AICTE APH 2025-26",
                    "parameters": curr_ver.parameters if curr_ver else {},
                    "condition_expression": curr_ver.condition_expression if curr_ver else "",
                    "failure_message_template": curr_ver.failure_message_template if curr_ver else ""
                }
            })
    else:
        # Fallback to runtime rule engine catalog if DB empty
        results = rules_engine.get_all_rules()

    return results


@router.get("/{rule_id}")
def get_rule_details(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns specific rule along with its complete version history."""
    rule = None
    if rule_id.isdigit():
        rule = db.query(Rule).filter(Rule.id == int(rule_id)).first()
    if not rule:
        rule = db.query(Rule).filter(Rule.rule_code == rule_id).first()

    if not rule:
        # Check in YAML engine
        all_rules = rules_engine.get_all_rules()
        matched = next((r for r in all_rules if r.get("rule_id") == rule_id or r.get("clause_id") == rule_id), None)
        if matched:
            return matched
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found.")

    versions = [
        {
            "id": v.id,
            "version_number": v.version_number,
            "handbook_edition": v.handbook_edition,
            "parameters": v.parameters,
            "condition_expression": v.condition_expression,
            "failure_message_template": v.failure_message_template,
            "is_current": v.is_current,
            "effective_from": v.effective_from.isoformat() if v.effective_from else None,
            "created_at": v.created_at.isoformat() if v.created_at else None
        }
        for v in rule.versions
    ]

    return {
        "id": rule.id,
        "rule_code": rule.rule_code,
        "clause_id": rule.clause_id,
        "title": rule.title,
        "category": rule.category,
        "severity": rule.severity,
        "description": rule.description,
        "is_active": rule.is_active,
        "versions": versions
    }


# ============================================================================
# 2. RULES CRUD WITH VERSIONING (ADMIN ONLY)
# ============================================================================

@router.post("", status_code=status.HTTP_201_CREATED)
def create_rule(
    rule_req: RuleCreateRequest,
    req: Request = None,
    current_user: User = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Creates a new regulatory rule with initial version 1.0.0.
    Restricted to Central AICTE Administrators.
    """
    existing = db.query(Rule).filter(Rule.rule_code == rule_req.rule_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Rule with code '{rule_req.rule_code}' already exists."
        )

    rule = Rule(
        rule_code=rule_req.rule_code,
        clause_id=rule_req.clause_id,
        title=rule_req.title,
        category=rule_req.category,
        severity=rule_req.severity.upper(),
        description=rule_req.description,
        is_active=True
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    version = RuleVersion(
        rule_id=rule.id,
        handbook_edition=rule_req.handbook_edition,
        version_number=rule_req.version_number,
        parameters=rule_req.parameters,
        condition_expression=rule_req.condition_expression,
        failure_message_template=rule_req.failure_message_template,
        is_current=True
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    # Sync into runtime engine
    rules_engine.update_rule(rule.rule_code, {
        "rule_id": rule.rule_code,
        "clause_id": rule.clause_id,
        "title": rule.title,
        "category": rule.category,
        "severity": rule.severity,
        "parameters": version.parameters
    })

    log_sensitive_access(
        db=db,
        user=current_user,
        action="CREATE_RULE",
        resource=f"/api/v1/rules/{rule.rule_code}",
        details={"rule_id": rule.id, "rule_code": rule.rule_code, "version": version.version_number},
        request=req
    )

    return {
        "status": "CREATED",
        "rule_id": rule.id,
        "rule_code": rule.rule_code,
        "version_id": version.id,
        "version_number": version.version_number
    }


@router.put("/{rule_id}")
def update_rule(
    rule_id: str,
    update_req: RuleUpdateRequest,
    req: Request = None,
    current_user: User = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Updates rule configuration with automatic version incrementing.
    Prior active version is marked is_current = False, creating an immutable regulatory history.
    Restricted to Central AICTE Administrators.
    """
    rule = None
    if rule_id.isdigit():
        rule = db.query(Rule).filter(Rule.id == int(rule_id)).first()
    if not rule:
        rule = db.query(Rule).filter(Rule.rule_code == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found.")

    # Update base rule fields
    if update_req.title is not None:
        rule.title = update_req.title
    if update_req.category is not None:
        rule.category = update_req.category
    if update_req.severity is not None:
        rule.severity = update_req.severity.upper()
    if update_req.description is not None:
        rule.description = update_req.description
    if update_req.is_active is not None:
        rule.is_active = update_req.is_active

    # Compute new version number
    current_version = next((v for v in rule.versions if v.is_current), None)
    if update_req.version_number:
        new_version_num = update_req.version_number
    elif current_version:
        parts = current_version.version_number.split(".")
        try:
            parts[-1] = str(int(parts[-1]) + 1)
            new_version_num = ".".join(parts)
        except Exception:
            new_version_num = f"{current_version.version_number}.1"
    else:
        new_version_num = "1.1.0"

    # Mark existing versions non-current
    for v in rule.versions:
        v.is_current = False
        if not v.effective_to:
            v.effective_to = datetime.now(timezone.utc)

    # Create new RuleVersion
    new_version = RuleVersion(
        rule_id=rule.id,
        handbook_edition=update_req.handbook_edition or (current_version.handbook_edition if current_version else "AICTE APH 2025-26"),
        version_number=new_version_num,
        parameters=update_req.parameters if update_req.parameters is not None else (current_version.parameters if current_version else {}),
        condition_expression=update_req.condition_expression or (current_version.condition_expression if current_version else "true"),
        failure_message_template=update_req.failure_message_template or (current_version.failure_message_template if current_version else "Rule violation"),
        is_current=True,
        effective_from=datetime.now(timezone.utc)
    )
    db.add(new_version)
    db.commit()
    db.refresh(rule)

    # Sync runtime engine
    rules_engine.update_rule(rule.rule_code, {
        "rule_id": rule.rule_code,
        "title": rule.title,
        "parameters": new_version.parameters
    })

    log_sensitive_access(
        db=db,
        user=current_user,
        action="UPDATE_RULE_VERSION",
        resource=f"/api/v1/rules/{rule.rule_code}",
        details={"rule_id": rule.id, "new_version": new_version_num},
        request=req
    )

    return {
        "status": "SUCCESS",
        "message": f"Rule {rule.rule_code} updated to version {new_version_num}.",
        "rule_code": rule.rule_code,
        "new_version": new_version_num,
        "parameters": new_version.parameters
    }


@router.delete("/{rule_id}")
def deactivate_rule(
    rule_id: str,
    req: Request = None,
    current_user: User = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db)
):
    """Deactivates a rule from statutory evaluation. Admin only."""
    rule = None
    if rule_id.isdigit():
        rule = db.query(Rule).filter(Rule.id == int(rule_id)).first()
    if not rule:
        rule = db.query(Rule).filter(Rule.rule_code == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found.")

    rule.is_active = False
    db.commit()

    log_sensitive_access(
        db=db,
        user=current_user,
        action="DEACTIVATE_RULE",
        resource=f"/api/v1/rules/{rule.rule_code}",
        details={"rule_id": rule.id, "rule_code": rule.rule_code},
        request=req
    )

    return {"status": "SUCCESS", "message": f"Rule {rule.rule_code} deactivated."}


# ============================================================================
# 3. WHAT-IF DRY RUN IMPACT SIMULATION
# ============================================================================

@router.post("/dry-run")
@router.post("/what-if")
def execute_what_if_dry_run(
    req_body: Optional[WhatIfDryRunRequest] = None,
    req: Request = None,
    current_user: User = Depends(require_roles(ROLE_SCRUTINY_OFFICER, ROLE_SENIOR_OFFICER, ROLE_ADMIN, ROLE_AUDITOR)),
    db: Session = Depends(get_db)
):
    """
    What-If Regulatory Dry Run:
    Simulates modified parameters (e.g. changing FSR target from 20 to 15)
    across applicant cohorts without mutating persistent database records.
    Authorized for Scrutiny Officers, Senior Officers, Admins, and Auditors.
    Prohibited for Institution Users.
    """
    apps_facts = []
    if req_body and req_body.applications:
        apps_facts = req_body.applications
    else:
        # Load active applications from DB for simulation cohort
        db_apps = db.query(Application).all()
        for a in db_apps:
            inst = a.institution
            apps_facts.append({
                "id": a.id,
                "application_id": f"APP_{a.id}",
                "app_no": a.application_no,
                "institution_name": inst.name if inst else "College",
                "state": inst.state if inst else "Karnataka",
                "city": inst.city if inst else "Bengaluru",
                "course_type": inst.category if (inst and inst.category) else a.category,
                "sanctioned_intake": inst.approved_intake if inst else 300,
                "built_up_area_sqm": inst.total_built_up_area_sqm if inst else 12000.0,
                "total_faculty": 18,
                "professors_count": 2,
                "fire_noc_expiry_date": "2026-03-31",
                "land_area_acres": inst.land_area_acres if inst else 7.5,
                "location_category": "URBAN",
                "documents": [{"document_type": d.document_type, "status": "ACTIVE"} for d in a.documents]
            })

    rules_list = req_body.rules if req_body else None

    # Execute baseline simulation (current rules) and simulated run (modified rules)
    baseline_results = rules_engine.dry_run(rules=None, applications=apps_facts)
    dry_run_results = rules_engine.dry_run(rules=rules_list, applications=apps_facts)

    baseline_affected = set(str(x) for x in baseline_results.get("affected_applications", []))
    simulated_affected = set(str(x) for x in dry_run_results.get("affected_applications", []))

    # Evaluate before and after status for each applicant
    cleared_count = 0
    newly_flagged_count = 0
    sample_results = []

    for app in apps_facts:
        app_key = str(app.get("id") or app.get("application_id"))
        before_passed = app_key not in baseline_affected
        after_passed = app_key not in simulated_affected

        before_status = "Verified" if before_passed else "Mismatch Detected"
        after_status = "Verified" if after_passed else "Mismatch Detected"

        change_type = "NO_CHANGE"
        if not before_passed and after_passed:
            change_type = "STATUS_CLEARED"
            cleared_count += 1
        elif before_passed and not after_passed:
            change_type = "NEWLY_FLAGGED"
            newly_flagged_count += 1

        sample_results.append({
            "id": app.get("id"),
            "app_no": app.get("app_no") or app.get("application_id"),
            "institution_name": app.get("institution_name"),
            "state": app.get("state", "Karnataka"),
            "city": app.get("city", "City"),
            "course_type": app.get("course_type", "Engineering & Technology"),
            "beforeStatus": before_status,
            "afterStatus": after_status,
            "changeType": change_type,
        })

    # Group by state
    states = sorted(list(set(a.get("state", "Karnataka") for a in apps_facts)))
    state_breakdown = []
    for s in states:
        s_apps = [a for a in apps_facts if a.get("state", "Karnataka") == s]
        base_flagged = sum(1 for a in s_apps if str(a.get("id") or a.get("application_id")) in baseline_affected)
        sim_flagged = sum(1 for a in s_apps if str(a.get("id") or a.get("application_id")) in simulated_affected)
        state_breakdown.append({
            "state": s,
            "baseline": base_flagged,
            "simulated": sim_flagged,
            "total": len(s_apps)
        })

    # Group by course type
    course_types = sorted(list(set(a.get("course_type", "Engineering") for a in apps_facts)))
    course_type_breakdown = []
    for ct in course_types:
        ct_apps = [a for a in apps_facts if a.get("course_type") == ct]
        base_flagged = sum(1 for a in ct_apps if str(a.get("id") or a.get("application_id")) in baseline_affected)
        sim_flagged = sum(1 for a in ct_apps if str(a.get("id") or a.get("application_id")) in simulated_affected)
        course_type_breakdown.append({
            "courseType": ct,
            "baseline": base_flagged,
            "simulated": sim_flagged,
            "total": len(ct_apps)
        })

    dry_run_results["total_cohort"] = len(apps_facts)
    dry_run_results["changed_count"] = cleared_count + newly_flagged_count
    dry_run_results["cleared_count"] = cleared_count
    dry_run_results["newly_flagged_count"] = newly_flagged_count
    dry_run_results["is_relaxation"] = cleared_count >= newly_flagged_count
    dry_run_results["state_breakdown"] = state_breakdown
    dry_run_results["course_type_breakdown"] = course_type_breakdown
    dry_run_results["sample_results"] = sample_results

    log_sensitive_access(
        db=db,
        user=current_user,
        action="EXECUTE_WHAT_IF_DRY_RUN",
        resource="/api/v1/rules/dry-run",
        details={"cohort_size": len(apps_facts)},
        request=req
    )

    return dry_run_results
