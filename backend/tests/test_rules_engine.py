"""
Unit and integration tests for PRAMAAN-X Regulation-as-Code Engine (Prompt 4.1 & 4.2):
Tests:
1. JSON Schema validation for rule definitions (valid rules pass, invalid rules reject)
2. All 6 rule evaluation types:
   - required_document
   - validity_check
   - numeric_threshold
   - cross_field_consistency
   - ratio_check
   - custom
3. Compliance status trifecta: 'pass', 'fail', 'not_evaluable'
4. Hot-reload mechanism without server restart
5. Dry-run What-If impact simulation metrics across application cohorts
"""
import pytest
import tempfile
import yaml
from pathlib import Path
from backend.app.services.rules_engine import (
    RegulationRulesEngine,
    RuleValidationError,
    Finding
)

@pytest.fixture
def engine():
    """Returns an initialized RegulationRulesEngine instance with default rules."""
    return RegulationRulesEngine()

# ==============================================================================
# 1. JSON SCHEMA VALIDATION TESTS
# ==============================================================================

def test_json_schema_validation_valid_rule(engine):
    """Test that a compliant rule specification passes schema validation."""
    valid_rule = {
        "id": "RULE_TEST_VALID",
        "version": "1.0.0",
        "clause_ref": "APH-2025-Cl-9.9.9",
        "title": "Test Valid Statutory Rule",
        "applies_to": ["Extension of Approval (EoA)"],
        "type": "numeric_threshold",
        "parameters": {"field": "test_metric", "min_value": 10.0},
        "severity": "critical",
        "message_template": "Test metric {found_value} is below {expected_value}.",
        "remediation_hint": "Increase metric to 10.0.",
        "effective_from": "2025-01-01"
    }
    # Should not raise exception
    engine.validate_rule(valid_rule)

def test_json_schema_validation_missing_required_fields(engine):
    """Test that omitting required fields raises RuleValidationError."""
    invalid_rule = {
        "id": "RULE_TEST_INVALID",
        # Missing clause_ref, title, applies_to, remediation_hint, etc.
        "type": "numeric_threshold",
        "parameters": {}
    }
    with pytest.raises(RuleValidationError) as exc_info:
        engine.validate_rule(invalid_rule)
    assert "failed schema validation" in str(exc_info.value)

def test_json_schema_validation_invalid_type_enum(engine):
    """Test that an unapproved rule type enum is rejected."""
    invalid_rule = {
        "id": "RULE_TEST_BAD_TYPE",
        "version": "1.0.0",
        "clause_ref": "APH-2025-Cl-1.1.1",
        "title": "Bad Type Rule",
        "applies_to": ["Extension of Approval (EoA)"],
        "type": "unsupported_magic_check",  # Invalid enum
        "parameters": {},
        "severity": "critical",
        "message_template": "Message",
        "remediation_hint": "Hint",
        "effective_from": "2025-01-01"
    }
    with pytest.raises(RuleValidationError):
        engine.validate_rule(invalid_rule)

def test_json_schema_validation_invalid_severity(engine):
    """Test that an invalid severity level is rejected by schema."""
    invalid_rule = {
        "id": "RULE_TEST_BAD_SEVERITY",
        "version": "1.0.0",
        "clause_ref": "APH-2025-Cl-1.1.1",
        "title": "Bad Severity Rule",
        "applies_to": ["Extension of Approval (EoA)"],
        "type": "validity_check",
        "parameters": {},
        "severity": "catastrophic_emergency",  # Invalid enum
        "message_template": "Message",
        "remediation_hint": "Hint",
        "effective_from": "2025-01-01"
    }
    with pytest.raises(RuleValidationError):
        engine.validate_rule(invalid_rule)

# ==============================================================================
# 2. RULE LOADING & CITATION INTEGRITY
# ==============================================================================

def test_loaded_rules_count_and_types(engine):
    """Verify that all 12 example rules are loaded and indexed properly."""
    all_rules = engine.get_all_rules()
    assert len(all_rules) >= 12
    rule_ids = {r["id"] for r in all_rules}
    
    expected_ids = [
        "RULE_FIRE_NOC_VALIDITY",
        "RULE_FACULTY_STUDENT_RATIO",
        "RULE_BUILT_UP_AREA_PER_STUDENT",
        "RULE_NAME_MATCH_AFFIDAVIT_NOC",
        "RULE_NOC_RECENCY_AGE",
        "RULE_REQUIRED_LAND_DOCUMENT",
        "RULE_REQUIRED_AFFILIATION_ORDER",
        "RULE_CADRE_RATIO_PROFESSORS",
        "RULE_MINIMUM_LAND_AREA",
        "RULE_BUILDING_PLAN_APPROVAL",
        "RULE_SURVEY_NUMBER_CONSISTENCY",
        "RULE_STATUTORY_COMMITTEES_MANDATE"
    ]
    for exp_id in expected_ids:
        assert exp_id in rule_ids, f"Expected rule {exp_id} missing from loaded rules"

# ==============================================================================
# 3. RULE EVALUATION: ALL 6 TYPES & STATUS TRIFECTA
# ==============================================================================

def test_eval_validity_check_pass_fail_not_evaluable(engine):
    """Test validity_check: future date (pass), expired (fail), missing (not_evaluable)."""
    rule = engine.rules_registry["RULE_FIRE_NOC_VALIDITY"]
    
    # 1. Pass: valid through 2027
    facts_pass = {"fire_noc_expiry_date": "2027-05-14"}
    finding_pass = engine._eval_validity_check(rule, facts_pass)
    assert finding_pass.status == "pass"
    assert finding_pass.clause_ref == "APH-2025-Cl-6.3.2"

    # 2. Fail: expired in 2024
    facts_fail = {"fire_noc_expiry_date": "2024-01-09"}
    finding_fail = engine._eval_validity_check(rule, facts_fail)
    assert finding_fail.status == "fail"
    assert "2024-01-09" in finding_fail.found
    assert finding_fail.severity == "critical"

    # 3. Not Evaluable: date missing
    facts_missing = {}
    finding_ne = engine._eval_validity_check(rule, facts_missing)
    assert finding_ne.status == "not_evaluable"
    assert "not found" in finding_ne.human_readable_explanation

def test_eval_ratio_check_fsr(engine):
    """Test ratio_check: FSR 1:20 compliant (pass), FSR 1:30 deficit (fail), zero faculty."""
    rule = engine.rules_registry["RULE_FACULTY_STUDENT_RATIO"]

    # 1. Pass: 300 students / 15 faculty = 1:20
    facts_pass = {"sanctioned_intake": 300, "total_faculty": 15}
    res_pass = engine._eval_ratio_check(rule, facts_pass)
    assert res_pass.status == "pass"

    # 2. Fail: 300 students / 10 faculty = 1:30 (exceeds 1:20)
    facts_fail = {"sanctioned_intake": 300, "total_faculty": 10}
    res_fail = engine._eval_ratio_check(rule, facts_fail)
    assert res_fail.status == "fail"
    assert "1:30.0" in res_fail.found

    # 3. Fail: 0 faculty (cannot divide by zero)
    facts_zero = {"sanctioned_intake": 300, "total_faculty": 0}
    res_zero = engine._eval_ratio_check(rule, facts_zero)
    assert res_zero.status == "fail"
    assert "0" in res_zero.found

    # 4. Not Evaluable: missing intake
    facts_ne = {"total_faculty": 15}
    res_ne = engine._eval_ratio_check(rule, facts_ne)
    assert res_ne.status == "not_evaluable"

def test_eval_numeric_threshold_built_up_area(engine):
    """Test numeric_threshold: built up area per student."""
    rule = engine.rules_registry["RULE_BUILT_UP_AREA_PER_STUDENT"]

    # 1. Pass: 300 intake * 10.5 = 3150 required; college has 4000
    facts_pass = {"sanctioned_intake": 300, "built_up_area_sqm": 4000.0}
    res_pass = engine._eval_numeric_threshold(rule, facts_pass)
    assert res_pass.status == "pass"

    # 2. Fail: college only has 2500 sqm (< 3150)
    facts_fail = {"sanctioned_intake": 300, "built_up_area_sqm": 2500.0}
    res_fail = engine._eval_numeric_threshold(rule, facts_fail)
    assert res_fail.status == "fail"
    assert res_fail.severity == "critical"

    # 3. Not Evaluable: built_up_area_sqm missing
    facts_ne = {"sanctioned_intake": 300}
    res_ne = engine._eval_numeric_threshold(rule, facts_ne)
    assert res_ne.status == "not_evaluable"

def test_eval_cross_field_consistency_name_match(engine):
    """Test cross_field_consistency: entity name across affidavit and NOC."""
    rule = engine.rules_registry["RULE_NAME_MATCH_AFFIDAVIT_NOC"]

    # 1. Pass: Matching names
    facts_pass = {
        "affidavit_entity_name": "Apex Institute of Technology & Science",
        "noc_entity_name": "Apex Institute of Technology and Science"
    }
    res_pass = engine._eval_cross_field_consistency(rule, facts_pass)
    assert res_pass.status == "pass"

    # 2. Fail: Discrepant name (College vs Commercial Mall)
    facts_fail = {
        "affidavit_entity_name": "Apex Institute of Technology",
        "noc_entity_name": "Phusro Shopping Mall & Commercial Complex"
    }
    res_fail = engine._eval_cross_field_consistency(rule, facts_fail)
    assert res_fail.status == "fail"
    assert res_fail.severity == "critical"

    # 3. Not Evaluable: One field missing
    facts_ne = {"affidavit_entity_name": "Apex Institute of Technology"}
    res_ne = engine._eval_cross_field_consistency(rule, facts_ne)
    assert res_ne.status == "not_evaluable"

def test_eval_required_document(engine):
    """Test required_document: document uploaded vs missing."""
    rule = engine.rules_registry["RULE_REQUIRED_LAND_DOCUMENT"]

    # 1. Pass: Land Title Deed with clear title
    facts_pass = {
        "documents": [
            {
                "document_id": "DOC_LAND_01",
                "document_type": "Land Title Deed",
                "encumbrance_status": "CLEAR_TITLE",
                "page": 1,
                "bounding_box": [50, 50, 400, 600]
            }
        ]
    }
    res_pass = engine._eval_required_document(rule, facts_pass)
    assert res_pass.status == "pass"
    assert len(res_pass.evidence_refs) > 0
    assert res_pass.evidence_refs[0]["document_id"] == "DOC_LAND_01"

    # 2. Fail: Land Title Deed has litigation
    facts_fail_enc = {
        "documents": [
            {
                "document_id": "DOC_LAND_02",
                "document_type": "Land Title Deed",
                "encumbrance_status": "LITIGATION_PENDING"
            }
        ]
    }
    res_fail = engine._eval_required_document(rule, facts_fail_enc)
    assert res_fail.status == "fail"

    # 3. Fail: Missing document
    facts_missing = {"documents": [{"document_type": "Fire Safety Certificate"}]}
    res_miss = engine._eval_required_document(rule, facts_missing)
    assert res_miss.status == "fail"
    assert "Missing" in res_miss.found

    # 4. Not Evaluable: documents list not provided
    res_ne = engine._eval_required_document(rule, {})
    assert res_ne.status == "not_evaluable"

def test_eval_custom_condition_committees(engine):
    """Test custom condition evaluator: statutory committees establishment."""
    rule = engine.rules_registry["RULE_STATUTORY_COMMITTEES_MANDATE"]

    # 1. Pass: All 4 committees present
    facts_pass = {
        "established_committees": [
            "GRIEVANCE_REDRESSAL",
            "ANTI_RAGGING",
            "INTERNAL_COMPLAINTS",
            "SC_ST_COMMITTEE"
        ]
    }
    res_pass = engine._eval_custom(rule, facts_pass)
    assert res_pass.status == "pass"

    # 2. Fail: Missing Anti-Ragging and SC/ST committees
    facts_fail = {
        "established_committees": ["GRIEVANCE_REDRESSAL", "INTERNAL_COMPLAINTS"]
    }
    res_fail = engine._eval_custom(rule, facts_fail)
    assert res_fail.status == "fail"
    assert "ANTI_RAGGING" in res_fail.human_readable_explanation

# ==============================================================================
# 4. HOT-RELOAD TESTS (Prompt 4.2)
# ==============================================================================

def test_hot_reload_dynamic_update():
    """Test that hot-reloading dynamically re-reads modified rules from disk."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_rule_file = temp_dir_path / "temp_rules.yaml"

        initial_rule_pack = {
            "handbook_edition": "Temporary Test Handbook",
            "version": "1.0.0",
            "rules": [
                {
                    "id": "RULE_TEMP_001",
                    "version": "1.0.0",
                    "clause_ref": "TEST-Cl-1.0",
                    "title": "Initial Rule",
                    "applies_to": ["Extension of Approval (EoA)"],
                    "type": "numeric_threshold",
                    "parameters": {"field": "test_score", "min_value": 50.0},
                    "severity": "critical",
                    "message_template": "Score {found_value} below {expected_value}.",
                    "remediation_hint": "Increase score.",
                    "effective_from": "2025-01-01"
                }
            ]
        }
        with open(temp_rule_file, "w", encoding="utf-8") as f:
            yaml.dump(initial_rule_pack, f)

        engine = RegulationRulesEngine(rules_dir=temp_dir)
        assert len(engine.rules_registry) == 1
        assert "RULE_TEMP_001" in engine.rules_registry

        # Modify the rule file on disk (add second rule)
        initial_rule_pack["rules"].append({
            "id": "RULE_TEMP_002",
            "version": "1.0.0",
            "clause_ref": "TEST-Cl-2.0",
            "title": "Second Rule Added at Runtime",
            "applies_to": ["Extension of Approval (EoA)"],
            "type": "validity_check",
            "parameters": {"field": "temp_date", "min_valid_date": "2026-06-30"},
            "severity": "warning",
            "message_template": "Date invalid.",
            "remediation_hint": "Fix date.",
            "effective_from": "2025-01-01"
        })
        with open(temp_rule_file, "w", encoding="utf-8") as f:
            yaml.dump(initial_rule_pack, f)

        # Trigger hot-reload
        reload_result = engine.hot_reload()
        assert reload_result["status"] == "HOT_RELOAD_SUCCESS"
        assert reload_result["rules_count"] == 2
        assert "RULE_TEMP_002" in engine.rules_registry

# ==============================================================================
# 5. DRY-RUN WHAT-IF SIMULATION (Prompt 4.2)
# ==============================================================================

def test_dry_run_what_if_simulator(engine):
    """Test dry_run aggregate impact metrics for the What-If simulator."""
    # Build 3 application cohorts
    app_cohorts = [
        # App 1: Fully compliant institution
        {
            "id": "APP_COHORT_1",
            "application_category": "Extension of Approval (EoA)",
            "sanctioned_intake": 300,
            "total_faculty": 16,
            "professors_count": 3,
            "built_up_area_sqm": 12000.0,
            "fire_noc_expiry_date": "2027-06-30",
            "state_noc_issue_date": "2025-06-15",
            "land_area_acres": 8.5,
            "location_category": "RURAL",
            "affidavit_entity_name": "Apex Engineering College",
            "noc_entity_name": "Apex Engineering College",
            "land_survey_numbers": "Sy. No. 101/A",
            "building_plan_survey_numbers": "Sy. No. 101/A",
            "established_committees": ["GRIEVANCE_REDRESSAL", "ANTI_RAGGING", "INTERNAL_COMPLAINTS", "SC_ST_COMMITTEE"],
            "documents": [
                {"document_type": "Land Title Deed", "encumbrance_status": "CLEAR_TITLE"},
                {"document_type": "University Affiliation Order", "status": "ACTIVE"},
                {"document_type": "Building Plan Approval"}
            ]
        },
        # App 2: Non-compliant (expired fire NOC + FSR deficit)
        {
            "id": "APP_COHORT_2",
            "application_category": "Extension of Approval (EoA)",
            "sanctioned_intake": 300,
            "total_faculty": 8,  # FSR 1:37.5 (Deficit!)
            "professors_count": 0, # Cadre shortfall!
            "built_up_area_sqm": 2000.0, # Area shortfall!
            "fire_noc_expiry_date": "2023-12-31", # Expired!
            "documents": []
        },
        # App 3: Partial facts (some not_evaluable)
        {
            "id": "APP_COHORT_3",
            "application_category": "Extension of Approval (EoA)",
            "sanctioned_intake": 300
            # Everything else missing
        }
    ]

    stats = engine.dry_run(applications=app_cohorts)

    assert stats["total_applications"] == 3
    assert stats["total_rules_evaluated"] >= 12
    assert stats["total_evaluations"] > 0
    assert "summary_by_status" in stats
    assert stats["summary_by_status"]["pass"] > 0
    assert stats["summary_by_status"]["fail"] > 0
    assert stats["summary_by_status"]["not_evaluable"] > 0
    assert "findings_by_severity" in stats
    assert stats["findings_by_severity"]["critical"] > 0
    assert "APP_COHORT_2" in stats["affected_applications"]
    assert "rule_impact" in stats
    assert "RULE_FACULTY_STUDENT_RATIO" in stats["rule_impact"]
    assert stats["rule_impact"]["RULE_FACULTY_STUDENT_RATIO"]["failed"] >= 1
