"""
PRAMAAN-X Inspection Planner API:
Clusters flagged institutions by State and District/City,
calculates priority inspection urgency scores,
and suggests optimal geographical inspection sequences.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from collections import defaultdict

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, require_roles, ROLE_SCRUTINY_OFFICER, ROLE_SENIOR_OFFICER, ROLE_ADMIN, ROLE_AUDITOR
from backend.app.models.models import Institution, Application, Finding, Alert

router = APIRouter(prefix="/inspections", tags=["Inspection Planner"])

@router.get("/planner")
def get_inspection_planner(
    state: Optional[str] = Query(None, description="Filter by state (e.g. Karnataka, Maharashtra)"),
    state_filter: Optional[str] = Query(None, description="Alias for state filter"),
    min_priority: Optional[float] = Query(0.0, description="Minimum urgency priority score"),
    req: Request = None,
    current_user: Any = Depends(require_roles(ROLE_SCRUTINY_OFFICER, ROLE_SENIOR_OFFICER, ROLE_ADMIN, ROLE_AUDITOR)),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Inspection Planner:
    Identifies institutions with critical discrepancies, impossible dual tenures,
    or inspection recommendations.
    Clusters by State and District/City, and computes suggested inspection order.
    """
    target_state = state_filter or state
    effective_state_filter = str(target_state) if (target_state and not hasattr(target_state, "default")) else None
    priority_threshold = float(min_priority) if (min_priority is not None and not hasattr(min_priority, "default")) else 0.0

    query = db.query(Institution)
    if effective_state_filter:
        query = query.filter(Institution.state.ilike(f"%{effective_state_filter}%"))

    institutions = query.all()
    flagged_items = []

    for inst in institutions:
        apps = inst.applications or []
        latest_app = apps[-1] if apps else None
        
        # Calculate risk indicators
        advisory_count = latest_app.advisory_flags_count if latest_app else 0
        readiness_score = latest_app.preflight_readiness_score if latest_app else 85.0
        app_status = latest_app.status if latest_app else "ACTIVE"

        # Check findings
        findings_query = db.query(Finding).join(Application).filter(Application.institution_id == inst.id)
        critical_count = findings_query.filter(Finding.severity == "CRITICAL", Finding.is_superseded == False).count()
        warning_count = findings_query.filter(Finding.severity == "WARNING", Finding.is_superseded == False).count()

        # Check alerts
        alert_count = db.query(Alert).join(Application).filter(Application.institution_id == inst.id, Alert.is_read == False).count()

        # Priority calculation
        is_recommended = (app_status == "INSPECTION_RECOMMENDED")
        priority = (100.0 - readiness_score) * 0.4 + (critical_count * 15.0) + (warning_count * 5.0) + (alert_count * 8.0)
        if is_recommended:
            priority += 25.0

        priority = round(min(100.0, max(10.0, priority)), 1)

        # Flagged condition
        is_flagged = (
            priority >= 40.0 or 
            critical_count > 0 or 
            is_recommended or 
            alert_count > 0 or 
            readiness_score < 75.0
        )

        if is_flagged:
            # Issues list
            issues = []
            if critical_count > 0:
                issues.append(f"{critical_count} Critical Regulatory Violations")
            if is_recommended:
                issues.append("Formal Scrutiny Officer Inspection Mandate")
            if alert_count > 0:
                issues.append(f"{alert_count} Unresolved Forensic / Dual Employment Alerts")
            if readiness_score < 75.0:
                issues.append(f"Sub-Threshold Readiness Score ({readiness_score}/100)")
            if not issues:
                issues.append("Periodic Random Sample Inspection")

            # Risk tier
            if priority >= 75.0:
                risk_tier = "CRITICAL_URGENCY"
                rec_type = "SURPRISE_PHYSICAL_INSPECTION"
            elif priority >= 55.0:
                risk_tier = "HIGH_PRIORITY"
                rec_type = "HYBRID_360_AUDIT"
            else:
                risk_tier = "MODERATE_REVIEW"
                rec_type = "VIRTUAL_INFRASTRUCTURE_VERIFICATION"

            coords = inst.geo_coordinates or {"lat": 12.9716, "lng": 77.5946}

            flagged_items.append({
                "institution_id": inst.id,
                "aicte_id": inst.aicte_id,
                "name": inst.name,
                "state": inst.state or "Karnataka",
                "district": inst.city or "Bengaluru",
                "city": inst.city or "Bengaluru",
                "category": inst.category or "Engineering & Technology",
                "approved_intake": inst.approved_intake,
                "application_id": latest_app.id if latest_app else None,
                "application_no": latest_app.application_no if latest_app else f"APP-2025-{inst.id:04d}",
                "status": app_status,
                "readiness_score": readiness_score,
                "priority_score": priority,
                "risk_tier": risk_tier,
                "critical_findings_count": critical_count,
                "flagged_issues": issues,
                "recommended_inspection_type": rec_type,
                "geo_coordinates": coords,
                "address": inst.address or f"Campus Sector, {inst.city or 'District Area'}, {inst.state or 'State'}"
            })

    # Filter min_priority
    if priority_threshold > 0:
        flagged_items = [f for f in flagged_items if f["priority_score"] >= priority_threshold]

    # Cluster by State -> District
    clusters_map = defaultdict(lambda: defaultdict(list))
    for item in flagged_items:
        clusters_map[item["state"]][item["district"]].append(item)

    formatted_clusters = []
    total_suggested_itinerary_stops = 0

    for state_name, districts in sorted(clusters_map.items()):
        district_list = []
        state_total = 0
        for dist_name, items in sorted(districts.items()):
            # Order institutions within district by priority descending
            items_sorted = sorted(items, key=lambda x: x["priority_score"], reverse=True)
            for seq_idx, itm in enumerate(items_sorted, start=1):
                itm["sequence_in_district"] = seq_idx
                itm["inspection_order"] = seq_idx

            district_list.append({
                "district": dist_name,
                "institution_count": len(items_sorted),
                "highest_priority": items_sorted[0]["priority_score"] if items_sorted else 0.0,
                "institutions": items_sorted
            })
            state_total += len(items_sorted)
            total_suggested_itinerary_stops += len(items_sorted)

        formatted_clusters.append({
            "state": state_name,
            "total_institutions": state_total,
            "districts_count": len(district_list),
            "districts": district_list
        })

    return {
        "status": "success",
        "total_flagged_institutions": len(flagged_items),
        "total_states": len(formatted_clusters),
        "total_clusters": sum(len(c["districts"]) for c in formatted_clusters),
        "state_clusters": formatted_clusters,
        "raw_institutions_sorted": sorted(flagged_items, key=lambda x: x["priority_score"], reverse=True)
    }
