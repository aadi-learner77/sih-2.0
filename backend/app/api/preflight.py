from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import Institution
from backend.app.schemas.schemas import PreflightScanRequest, PreflightScanResponse
from backend.app.services.checklist_engine import generate_checklist_status
from backend.app.services.rules_engine import rules_engine
from backend.app.services.impossibility_engine import impossibility_engine

router = APIRouter(prefix="/preflight", tags=["Institution Pre-Flight Readiness"])

@router.post("/scan", response_model=PreflightScanResponse)
def run_preflight_readiness_scan(
    request: PreflightScanRequest,
    db: Session = Depends(get_db)
):
    """
    Pre-Flight Readiness Engine:
    Allows institutions to run a pre-submission self-assessment:
    - Checklist completeness & expired certification warnings
    - Regulation-as-Code clause compliance check
    - Cross-institutional conflict early warnings
    - Actionable recommendations to improve readiness score prior to official submission
    """
    inst = db.query(Institution).filter(Institution.id == request.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    # 1. Checklist completeness
    # Mock / user supplied docs
    checklist_status = generate_checklist_status(request.application_category, [])
    
    # 2. Rule evaluation on submitted facts
    eval_facts = {
        "sanctioned_intake": request.facts.get("sanctioned_intake", inst.approved_intake),
        "built_up_area_sqm": request.facts.get("built_up_area_sqm", inst.total_built_up_area_sqm),
        "total_faculty": request.facts.get("total_faculty", 20),
        "professors_count": request.facts.get("professors_count", 2),
        "fire_noc_expiry_date": request.facts.get("fire_noc_expiry_date", "2026-06-30"),
        "land_ownership_type": request.facts.get("land_ownership_type", "LEASEHOLD_PERMANENT"),
        "lease_duration_years": request.facts.get("lease_duration_years", 30),
        "affiliation_status": request.facts.get("affiliation_status", "ACTIVE")
    }

    rule_results = rules_engine.evaluate_application(eval_facts)
    failed_rules = [r for r in rule_results if not r["passed"]]

    # 3. Knowledge Graph impossibility check
    impossibilities = impossibility_engine.detect_all_impossibilities(target_inst_id=f"INST_00{inst.id}")

    # 4. Calculate Readiness Score (0 to 100)
    score = 100.0
    recommendations = []

    # Penalty for missing mandatory checklist items
    missing_penalty = checklist_status["missing_items"] * 8.0
    score -= missing_penalty
    if checklist_status["missing_items"] > 0:
        recommendations.append(f"Upload {checklist_status['missing_items']} missing mandatory compliance documents.")

    # Penalty for failed rules
    rule_penalty = len(failed_rules) * 6.0
    score -= rule_penalty
    for f in failed_rules:
        recommendations.append(f"Review {f['clause_id']}: {f['explanation']}")

    # Penalty for graph impossibilities
    if impossibilities:
        score -= (len(impossibilities) * 10.0)
        for imp in impossibilities:
            recommendations.append(f"Resolve conflict: {imp['title']} ({imp['conflict_type']})")

    final_score = round(max(15.0, min(100.0, score)), 1)

    return {
        "readiness_score": final_score,
        "category": request.application_category,
        "checklist_summary": checklist_status,
        "rule_indicators": rule_results,
        "impossibility_indicators": impossibilities,
        "recommendations": recommendations or ["Institution dossier is 100% compliant with AICTE APH 2025-26 guidelines."]
    }
