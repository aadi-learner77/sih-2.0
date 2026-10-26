from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import RuleEvaluation, Application
from backend.app.schemas.schemas import RuleEvaluationOut, OfficerDecisionUpdate
from backend.app.services.rules_engine import rules_engine
from backend.app.services.audit_chain import AuditChainService

router = APIRouter(prefix="/rules", tags=["Regulation-as-Code"])

@router.get("", response_model=List[Dict[str, Any]])
def list_rules():
    """Returns all active handbook rules parsed from YAML rule packs."""
    return rules_engine.get_all_rules()

@router.put("/{rule_id}")
def update_rule_configuration(rule_id: str, updated_rule: Dict[str, Any]):
    """Configurable rules: updates rule parameters or condition dynamically without code changes."""
    success = rules_engine.update_rule(rule_id, updated_rule)
    if not success:
        raise HTTPException(status_code=404, detail="Rule ID not found in active handbook packs")
    return {"status": "SUCCESS", "message": f"Rule {rule_id} updated and reloaded in runtime engine."}

@router.post("/evaluate/{app_id}", response_model=List[RuleEvaluationOut])
def evaluate_rules_for_application(app_id: int, db: Session = Depends(get_db)):
    """Executes all handbook rules on institutional application facts."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Aggregate facts from documents and institution
    facts = {
        "sanctioned_intake": app.institution.approved_intake if app.institution else 300,
        "built_up_area_sqm": app.institution.total_built_up_area_sqm if app.institution else 12000.0,
        "total_faculty": 15,
        "professors_count": 1,
        "fire_noc_expiry_date": "2026-03-31",
        "land_ownership_type": "LEASEHOLD_PERMANENT",
        "lease_duration_years": 30,
        "affiliation_status": "ACTIVE"
    }

    # Extract fields from existing documents if present
    for doc in app.documents:
        fields = doc.structured_fields or {}
        if "fire" in doc.document_type.lower() and "valid_till" in fields:
            facts["fire_noc_expiry_date"] = fields["valid_till"]
        if "faculty" in doc.document_type.lower():
            if "total_faculty" in fields:
                facts["total_faculty"] = fields["total_faculty"]
            if "professors" in fields:
                facts["professors_count"] = fields["professors"]

    eval_results = rules_engine.evaluate_application(facts)

    # Clear prior evaluations and save new ones
    db.query(RuleEvaluation).filter(RuleEvaluation.application_id == app.id).delete()
    
    saved_evals = []
    advisory_count = 0
    for res in eval_results:
        if not res["passed"]:
            advisory_count += 1
        eval_record = RuleEvaluation(
            application_id=app.id,
            rule_id=res["rule_id"],
            clause_id=res["clause_id"],
            clause_title=res["clause_title"],
            handbook_edition=res["handbook_edition"],
            severity=res["severity"],
            passed=res["passed"],
            claim_summary=res.get("claim_summary"),
            evidence_details=res.get("evidence_details", {}),
            explanation=res["explanation"],
            officer_decision="PENDING_REVIEW"
        )
        db.add(eval_record)
        saved_evals.append(eval_record)

    app.advisory_flags_count = advisory_count
    db.commit()

    # Append evaluation event to audit chain
    AuditChainService.append_receipt(
        db=db,
        event_type="RULES_EVALUATION_EXECUTED",
        payload={
            "rules_count": len(eval_results),
            "flags_generated": advisory_count,
            "handbook": "AICTE APH 2025-26"
        },
        actor_email="system@aicte-india.org",
        actor_role="SYSTEM",
        application_id=app.id
    )

    return saved_evals

@router.patch("/evaluations/{eval_id}/decision", response_model=RuleEvaluationOut)
def record_officer_decision(
    eval_id: int,
    update: OfficerDecisionUpdate,
    db: Session = Depends(get_db)
):
    """
    Officer Action: Scrutiny Officer records explainable decision on an advisory indicator.
    Valid choices: ACCEPTED_WITH_NOTE, CLARIFICATION_ISSUED, WAIVED_WITH_REASON, PENDING_REVIEW.
    Appends an immutable tamper-evident receipt to the audit ledger.
    """
    evaluation = db.query(RuleEvaluation).filter(RuleEvaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Rule evaluation not found")

    evaluation.officer_decision = update.decision
    evaluation.officer_comment = update.comment
    db.commit()
    db.refresh(evaluation)

    # Append to cryptographic audit chain
    AuditChainService.append_receipt(
        db=db,
        event_type="OFFICER_DECISION_RECORDED",
        payload={
            "evaluation_id": evaluation.id,
            "clause_id": evaluation.clause_id,
            "decision": update.decision,
            "officer_comment": update.comment
        },
        actor_email="scrutiny.officer@aicte-india.org",
        actor_role="scrutiny_officer",
        application_id=evaluation.application_id
    )

    return evaluation

class DryRunRequest(BaseModel):
    rules: Optional[List[Dict[str, Any]]] = None
    applications: Optional[List[Dict[str, Any]]] = None

@router.post("/reload")
def reload_rules_endpoint():
    """Hot-reloads all YAML rules from disk into runtime engine."""
    return rules_engine.hot_reload()

@router.post("/dry-run")
def execute_dry_run(req: Optional[DryRunRequest] = None, db: Session = Depends(get_db)):
    """Executes What-If dry run impact simulation."""
    apps_facts = []
    if req and req.applications:
        apps_facts = req.applications
    else:
        # Load active applications from DB
        db_apps = db.query(Application).limit(50).all()
        for a in db_apps:
            apps_facts.append({
                "id": a.id,
                "application_id": f"APP_{a.id}",
                "institution_name": a.institution.name if a.institution else "College",
                "sanctioned_intake": a.institution.approved_intake if a.institution else 300,
                "built_up_area_sqm": a.institution.total_built_up_area_sqm if a.institution else 12000.0,
                "total_faculty": 15,
                "professors_count": 1,
                "fire_noc_expiry_date": "2026-03-31",
                "land_area_acres": a.institution.land_area_acres if a.institution else 7.5,
                "location_category": "URBAN",
                "documents": [{"document_type": d.document_type, "status": "ACTIVE"} for d in a.documents]
            })
    rules_list = req.rules if req else None
    return rules_engine.dry_run(rules=rules_list, applications=apps_facts)
