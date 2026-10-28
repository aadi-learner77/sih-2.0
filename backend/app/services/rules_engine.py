"""
PRAMAAN-X Regulation-as-Code Engine (Phase 4):
Parses YAML handbook clause packs, validates rules against JSON Schema,
evaluates institutional application facts against statutory norms,
and outputs structured, explainable Finding objects with exact regulatory citations.

Features:
- Strict JSON Schema validation on rule definitions
- Full support for 6 evaluation categories:
  * required_document
  * validity_check
  * numeric_threshold
  * cross_field_consistency
  * ratio_check
  * custom
- Multi-state compliance outcomes: 'pass', 'fail', 'not_evaluable'
- Dynamic Hot-Reload from disk without application restart
- Dry-Run What-If Impact Simulation across application cohorts
"""
import os
import json
import logging
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Literal, Union
try:
    import yaml
except ImportError:
    import types
    import io
    import sys
    from ruamel.yaml import YAML
    _y = YAML(typ='safe')
    yaml = types.ModuleType("yaml")
    yaml.safe_load = _y.load
    def _dump(data, stream=None, **kwargs):
        if stream is None:
            buf = io.StringIO()
            YAML().dump(data, buf)
            return buf.getvalue()
        YAML().dump(data, stream)
    yaml.dump = _dump
    yaml.safe_dump = _dump
    sys.modules["yaml"] = yaml

import jsonschema
from pydantic import BaseModel, Field

from backend.app.core.config import settings

logger = logging.getLogger("rules_engine")

# ==============================================================================
# SCHEMA & EXCEPTION DEFINITIONS
# ==============================================================================

class RuleValidationError(Exception):
    """Raised when a YAML rule fails JSON Schema validation."""
    pass

class Finding(BaseModel):
    """
    Structured Regulatory Compliance Finding (Prompt 4.2).
    Represents the evaluation outcome of a single rule against application facts.
    """
    rule_id: str
    rule_version: str
    clause_ref: str = ""
    status: str = "pass"
    expected: Any = None
    found: Any = None
    evidence_refs: List[Dict[str, Any]] = Field(default_factory=list)
    severity: str = "warning"  # "info", "warning", "critical"
    human_readable_explanation: str = ""
    remediation: str = ""

    # Dictionary-like access & compatibility aliases for existing backend models
    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        if item == "passed":
            return self.status == "pass"
        if item == "clause_id":
            return self.clause_ref
        if item == "clause_title":
            return self.clause_ref
        if item == "explanation":
            return self.human_readable_explanation
        if item == "handbook_edition":
            return "AICTE APH 2025-26"
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return self[item]
        except KeyError:
            return default

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    @property
    def clause_id(self) -> str:
        return self.clause_ref

    @property
    def clause_title(self) -> str:
        return self.clause_ref

    @property
    def explanation(self) -> str:
        return self.human_readable_explanation

    @property
    def handbook_edition(self) -> str:
        return "AICTE APH 2025-26"

Finding.model_rebuild()


# ==============================================================================
# REGULATION-AS-CODE RULE ENGINE
# ==============================================================================

class RegulationRulesEngine:
    def __init__(self, rules_dir: Optional[str] = None, schema_path: Optional[str] = None):
        self.rules_dir = Path(rules_dir) if rules_dir else Path(settings.RULES_DIR)
        
        default_schema = Path(__file__).resolve().parent.parent / "rules" / "rule_schema.json"
        self.schema_path = Path(schema_path) if schema_path else default_schema
        
        self.schema: Dict[str, Any] = self._load_json_schema()
        self.rules_registry: Dict[str, Dict[str, Any]] = {}
        self.rule_packs: Dict[str, Any] = {}
        
        self.load_all_rules()

    def _load_json_schema(self) -> Dict[str, Any]:
        """Loads and caches the JSON Schema for rule validation."""
        if not self.schema_path.exists():
            logger.warning(f"Rule schema JSON not found at {self.schema_path}. Schema validation will be bypassed.")
            return {}
        try:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to parse rule schema JSON: {e}")
            return {}

    def validate_rule(self, rule_dict: Dict[str, Any]):
        """
        Validates a single rule dictionary against the formal JSON Schema.
        Raises RuleValidationError if validation fails.
        """
        if not self.schema:
            return
        try:
            jsonschema.validate(instance=rule_dict, schema=self.schema)
        except jsonschema.ValidationError as e:
            raise RuleValidationError(f"Rule '{rule_dict.get('id', 'UNKNOWN')}' failed schema validation: {e.message}") from e

    def load_all_rules(self) -> int:
        """
        Loads all YAML rule definition files from the rules directory,
        validates each rule against the JSON schema, and populates the in-memory registry.
        """
        self.rules_registry.clear()
        self.rule_packs.clear()

        if not self.rules_dir.exists():
            logger.warning(f"Rules directory {self.rules_dir} does not exist.")
            return 0

        for file_path in self.rules_dir.glob("*.y*ml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                
                if not data:
                    continue

                pack_edition = data.get("handbook_edition", file_path.stem)
                self.rule_packs[pack_edition] = data

                rules_list = data.get("rules", []) if isinstance(data, dict) and "rules" in data else ([data] if isinstance(data, dict) else [])

                for rule in rules_list:
                    # Validate schema
                    self.validate_rule(rule)
                    rule_id = rule.get("id")
                    if rule_id:
                        self.rules_registry[rule_id] = rule

            except RuleValidationError as rve:
                logger.error(f"Schema validation error in {file_path.name}: {rve}")
                raise
            except Exception as e:
                logger.error(f"Error reading YAML rule file {file_path.name}: {e}")

        logger.info(f"Loaded and validated {len(self.rules_registry)} regulatory rules from {self.rules_dir}")
        return len(self.rules_registry)

    def hot_reload(self, rules_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Hot-reload handler (Prompt 4.2).
        Reloads rules from disk on-the-fly without server restart.
        """
        if rules_dir:
            self.rules_dir = Path(rules_dir)
        count = self.load_all_rules()
        return {
            "status": "HOT_RELOAD_SUCCESS",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rules_count": count,
            "rules_directory": str(self.rules_dir),
            "loaded_rule_ids": list(self.rules_registry.keys())
        }

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Returns flattened list of active rules for administration & scrutiny."""
        rules = []
        for r in self.rules_registry.values():
            rd = dict(r)
            rd["clause_id"] = rd.get("clause_ref")
            rd["clause_title"] = rd.get("title")
            rules.append(rd)
        return rules

    def update_rule(self, rule_id: str, updated_fields: Dict[str, Any]) -> bool:
        """
        Dynamically updates a rule in-place, validates against schema, and writes back to disk.
        """
        if rule_id not in self.rules_registry:
            return False

        current = dict(self.rules_registry[rule_id])
        merged = {**current, **updated_fields}
        self.validate_rule(merged)

        # Write back to file
        for file_path in self.rules_dir.glob("*.y*ml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data and "rules" in data:
                    for idx, r in enumerate(data["rules"]):
                        if r.get("id") == rule_id:
                            data["rules"][idx] = merged
                            with open(file_path, "w", encoding="utf-8") as wf:
                                yaml.dump(data, wf, sort_keys=False)
                            self.load_all_rules()
                            return True
            except Exception as e:
                logger.error(f"Failed to write rule update to {file_path}: {e}")
        return False

    # ==========================================================================
    # EVALUATION DISPATCHER & RULE HANDLERS
    # ==========================================================================

    def evaluate(self, facts: Dict[str, Any], application_category: Optional[str] = None) -> List[Finding]:
        """
        Evaluates institutional facts against all configured handbook rules.
        Returns a structured list of Finding objects.
        """
        findings: List[Finding] = []
        app_cat = application_category or facts.get("application_category") or "Extension of Approval (EoA)"

        for rule_id, rule in self.rules_registry.items():
            applies_to = rule.get("applies_to", ["ALL"])
            if "ALL" not in applies_to and app_cat not in applies_to:
                continue

            rule_type = rule.get("type", "custom")
            eval_fn = getattr(self, f"_eval_{rule_type}", self._eval_custom)
            
            try:
                finding = eval_fn(rule, facts)
            except Exception as e:
                logger.warning(f"Error evaluating rule {rule_id}: {e}")
                finding = Finding(
                    rule_id=rule.get("id", "UNKNOWN"),
                    rule_version=rule.get("version", "1.0.0"),
                    clause_ref=rule.get("clause_ref", "N/A"),
                    status="not_evaluable",
                    expected="Evaluation error",
                    found=str(e),
                    severity=rule.get("severity", "warning").lower(),
                    human_readable_explanation=f"Rule could not be evaluated due to unexpected runtime error: {e}",
                    remediation=rule.get("remediation_hint", "Verify fact parameters and rule configuration.")
                )

            findings.append(finding)

        return findings

    # Alias for backward compatibility with existing API endpoints
    def evaluate_application(self, facts: Dict[str, Any]) -> List[Finding]:
        return self.evaluate(facts)

    # --------------------------------------------------------------------------
    # 1. Required Document Evaluator
    # --------------------------------------------------------------------------
    def _eval_required_document(self, rule: Dict[str, Any], facts: Dict[str, Any]) -> Finding:
        params = rule.get("parameters", {})
        doc_type = params.get("document_type", "")
        req_encumbrance = params.get("required_encumbrance_status")
        req_status = params.get("required_status")

        docs = facts.get("documents")
        if docs is None:
            # Check if doc_type has a dedicated fact flag
            doc_flag = facts.get(f"has_{doc_type.lower().replace(' ', '_')}")
            if doc_flag is None and "submitted_documents" not in facts:
                return self._create_not_evaluable(rule, f"Mandatory document catalog '{doc_type}' not provided in application facts.")
            docs = facts.get("submitted_documents", [])

        # Search for document in docs
        matching_doc = None
        for d in docs:
            if isinstance(d, dict) and d.get("document_type", "").lower() == doc_type.lower():
                matching_doc = d
                break
            elif isinstance(d, str) and doc_type.lower() in d.lower():
                matching_doc = {"document_type": d, "status": "ACTIVE"}
                break

        evidence_refs = []
        if matching_doc:
            if "document_id" in matching_doc:
                evidence_refs.append({
                    "document_id": matching_doc["document_id"],
                    "page": matching_doc.get("page", 1),
                    "bounding_box": matching_doc.get("bounding_box", [0, 0, 100, 100])
                })

        if not matching_doc:
            return Finding(
                rule_id=rule["id"],
                rule_version=rule.get("version", "1.0.0"),
                clause_ref=rule.get("clause_ref", "N/A"),
                status="fail",
                expected=f"Submitted {doc_type}",
                found="Missing / Not Uploaded",
                evidence_refs=evidence_refs,
                severity=rule.get("severity", "critical").lower(),
                human_readable_explanation=rule.get("message_template", "").format(doc_type=doc_type) or f"Mandatory document '{doc_type}' was not submitted.",
                remediation=rule.get("remediation_hint", f"Upload the mandatory {doc_type} certificate.")
            )

        # Check secondary document parameters if requested
        if req_encumbrance:
            found_enc = matching_doc.get("encumbrance_status") or facts.get("land_encumbrance_status", "CLEAR_TITLE")
            if found_enc != req_encumbrance:
                return Finding(
                    rule_id=rule["id"],
                    rule_version=rule.get("version", "1.0.0"),
                    clause_ref=rule.get("clause_ref", "N/A"),
                    status="fail",
                    expected=f"{doc_type} with {req_encumbrance}",
                    found=f"{doc_type} with {found_enc}",
                    evidence_refs=evidence_refs,
                    severity=rule.get("severity", "critical").lower(),
                    human_readable_explanation=f"Submitted {doc_type} reflects '{found_enc}', failing the '{req_encumbrance}' mandate.",
                    remediation=rule.get("remediation_hint", "Clear legal encumbrances before proceeding.")
                )

        if req_status:
            found_status = matching_doc.get("status") or facts.get("affiliation_status", "ACTIVE")
            if found_status != req_status:
                return Finding(
                    rule_id=rule["id"],
                    rule_version=rule.get("version", "1.0.0"),
                    clause_ref=rule.get("clause_ref", "N/A"),
                    status="fail",
                    expected=f"{doc_type} status {req_status}",
                    found=f"{doc_type} status {found_status}",
                    evidence_refs=evidence_refs,
                    severity=rule.get("severity", "critical").lower(),
                    human_readable_explanation=f"{doc_type} is currently reported as '{found_status}'.",
                    remediation=rule.get("remediation_hint", "Provide active status endorsement from the issuing authority.")
                )

        return Finding(
            rule_id=rule["id"],
            rule_version=rule.get("version", "1.0.0"),
            clause_ref=rule.get("clause_ref", "N/A"),
            status="pass",
            expected=f"Valid {doc_type}",
            found=f"Submitted {doc_type} (Verified)",
            evidence_refs=evidence_refs,
            severity=rule.get("severity", "critical").lower(),
            human_readable_explanation=f"Mandatory document '{doc_type}' verified compliant under {rule.get('clause_ref')}.",
            remediation=rule.get("remediation_hint", "Maintain record in compliance repository.")
        )

    # --------------------------------------------------------------------------
    # 2. Validity Check Evaluator
    # --------------------------------------------------------------------------
    def _eval_validity_check(self, rule: Dict[str, Any], facts: Dict[str, Any]) -> Finding:
        params = rule.get("parameters", {})
        field = params.get("field", "")
        min_valid_date_str = params.get("min_valid_date")
        max_age_months = params.get("max_age_months")

        raw_val = facts.get(field)
        if raw_val is None:
            return self._create_not_evaluable(rule, f"Date field '{field}' not found in application facts.")

        try:
            val_date = datetime.strptime(str(raw_val).strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            return self._create_not_evaluable(rule, f"Date field '{field}' contains unparseable date '{raw_val}'.")

        evidence_refs = self._extract_evidence_refs(facts, field)

        # Check 1: min_valid_date (future validity threshold)
        if min_valid_date_str:
            cutoff = datetime.strptime(min_valid_date_str, "%Y-%m-%d").date()
            if val_date < cutoff:
                msg = self._safe_format(rule.get("message_template", ""), {
                    "found_value": str(val_date),
                    "expected_value": str(cutoff),
                    **facts,
                    **params
                })
                return Finding(
                    rule_id=rule["id"],
                    rule_version=rule.get("version", "1.0.0"),
                    clause_ref=rule.get("clause_ref", "N/A"),
                    status="fail",
                    expected=f">= {min_valid_date_str}",
                    found=str(val_date),
                    evidence_refs=evidence_refs,
                    severity=rule.get("severity", "critical").lower(),
                    human_readable_explanation=msg or f"Validity expired on {val_date}, prior to mandatory cutoff {cutoff}.",
                    remediation=rule.get("remediation_hint", "Obtain renewed certificate covering the full academic year.")
                )

        # Check 2: max_age_months (recency window)
        if max_age_months is not None:
            today = date.today()
            age_months = (today.year - val_date.year) * 12 + (today.month - val_date.month)
            if age_months > max_age_months:
                msg = self._safe_format(rule.get("message_template", ""), {
                    "found_value": str(val_date),
                    "expected_value": max_age_months,
                    "age_months": age_months,
                    **facts,
                    **params
                })
                return Finding(
                    rule_id=rule["id"],
                    rule_version=rule.get("version", "1.0.0"),
                    clause_ref=rule.get("clause_ref", "N/A"),
                    status="fail",
                    expected=f"Age <= {max_age_months} months",
                    found=f"{age_months} months old (issued {val_date})",
                    evidence_refs=evidence_refs,
                    severity=rule.get("severity", "warning").lower(),
                    human_readable_explanation=msg or f"Document is {age_months} months old, exceeding allowable window of {max_age_months} months.",
                    remediation=rule.get("remediation_hint", "Obtain a fresh revalidated NOC from the issuing state department.")
                )

        return Finding(
            rule_id=rule["id"],
            rule_version=rule.get("version", "1.0.0"),
            clause_ref=rule.get("clause_ref", "N/A"),
            status="pass",
            expected=f">= {min_valid_date_str}" if min_valid_date_str else f"Age <= {max_age_months} months",
            found=str(val_date),
            evidence_refs=evidence_refs,
            severity=rule.get("severity", "critical").lower(),
            human_readable_explanation=f"Validity verified compliant with {rule.get('clause_ref')}.",
            remediation=rule.get("remediation_hint", "No action needed.")
        )

    # --------------------------------------------------------------------------
    # 3. Numeric Threshold Evaluator
    # --------------------------------------------------------------------------
    def _eval_numeric_threshold(self, rule: Dict[str, Any], facts: Dict[str, Any]) -> Finding:
        params = rule.get("parameters", {})
        field = params.get("field", "")
        op = params.get("operator", ">=")

        raw_val = facts.get(field)
        if raw_val is None:
            return self._create_not_evaluable(rule, f"Numeric field '{field}' not found in application facts.")

        try:
            val = float(raw_val)
        except (ValueError, TypeError):
            return self._create_not_evaluable(rule, f"Numeric field '{field}' has non-numeric value '{raw_val}'.")

        # Determine threshold
        if "threshold_multiplier_field" in params:
            mult_field = params["threshold_multiplier_field"]
            mult_val = facts.get(mult_field)
            if mult_val is None:
                return self._create_not_evaluable(rule, f"Multiplier field '{mult_field}' not found in application facts.")
            min_per_unit = float(params.get("min_per_unit", 1.0))
            threshold = float(mult_val) * min_per_unit
            sqm_per_student = (val / float(mult_val)) if float(mult_val) > 0 else 0.0
            extra_format = {"sqm_per_student": sqm_per_student, "min_per_unit": min_per_unit, mult_field: mult_val}
        elif "min_value_urban" in params or "min_value_rural" in params:
            loc_cat = str(facts.get(params.get("category_field", "location_category"), "RURAL")).upper()
            threshold = float(params.get("min_value_urban", 2.5)) if "URBAN" in loc_cat else float(params.get("min_value_rural", 7.5))
            extra_format = {"location_category": loc_cat}
        else:
            threshold = float(params.get("min_value", params.get("threshold", 0.0)))
            extra_format = {}

        # Evaluate operator
        passed = False
        if op == ">=":
            passed = val >= threshold
        elif op == ">":
            passed = val > threshold
        elif op == "<=":
            passed = val <= threshold
        elif op == "<":
            passed = val < threshold
        elif op == "==":
            passed = val == threshold

        evidence_refs = self._extract_evidence_refs(facts, field)

        if not passed:
            format_dict = {
                "found_value": val,
                "expected_value": threshold,
                **facts,
                **params,
                **extra_format
            }
            msg = self._safe_format(rule.get("message_template", ""), format_dict)
            return Finding(
                rule_id=rule["id"],
                rule_version=rule.get("version", "1.0.0"),
                clause_ref=rule.get("clause_ref", "N/A"),
                status="fail",
                expected=f"{op} {threshold:.2f}",
                found=f"{val:.2f}",
                evidence_refs=evidence_refs,
                severity=rule.get("severity", "critical").lower(),
                human_readable_explanation=msg or f"Value {val} failed threshold condition {op} {threshold}.",
                remediation=rule.get("remediation_hint", "Adjust metric to meet regulatory requirement.")
            )

        return Finding(
            rule_id=rule["id"],
            rule_version=rule.get("version", "1.0.0"),
            clause_ref=rule.get("clause_ref", "N/A"),
            status="pass",
            expected=f"{op} {threshold:.2f}",
            found=f"{val:.2f}",
            evidence_refs=evidence_refs,
            severity=rule.get("severity", "critical").lower(),
            human_readable_explanation=f"Threshold condition {op} {threshold:.2f} met successfully ({val:.2f}).",
            remediation=rule.get("remediation_hint", "Maintain prescribed infrastructure capacity.")
        )

    # --------------------------------------------------------------------------
    # 4. Cross-Field Consistency Evaluator
    # --------------------------------------------------------------------------
    def _eval_cross_field_consistency(self, rule: Dict[str, Any], facts: Dict[str, Any]) -> Finding:
        params = rule.get("parameters", {})
        field_a = params.get("field_a", "")
        field_b = params.get("field_b", "")
        mode = params.get("match_mode", "exact")

        val_a = facts.get(field_a)
        val_b = facts.get(field_b)

        if val_a is None:
            return self._create_not_evaluable(rule, f"Field '{field_a}' missing from application facts.")
        if val_b is None:
            return self._create_not_evaluable(rule, f"Field '{field_b}' missing from application facts.")

        str_a = str(val_a).strip()
        str_b = str(val_b).strip()

        passed = False
        if mode == "exact":
            passed = str_a.lower() == str_b.lower()
        elif mode == "fuzzy_token":
            # Token set comparison
            stops = {"the", "and", "of", "in", "for", "college", "institute", "technology", "engineering"}
            tokens_a = {w.lower() for w in str_a.replace(",", " ").replace("-", " ").split() if w.lower() not in stops}
            tokens_b = {w.lower() for w in str_b.replace(",", " ").replace("-", " ").split() if w.lower() not in stops}
            if tokens_a and tokens_b:
                intersection = tokens_a.intersection(tokens_b)
                union = tokens_a.union(tokens_b)
                jaccard = len(intersection) / len(union) if union else 0.0
                thresh = float(params.get("similarity_threshold", 0.70))
                passed = jaccard >= thresh or tokens_a.issubset(tokens_b) or tokens_b.issubset(tokens_a)
            else:
                passed = str_a.lower() == str_b.lower()
        elif mode == "exact_or_subset":
            passed = (str_a.lower() in str_b.lower()) or (str_b.lower() in str_a.lower())

        evidence_refs = self._extract_evidence_refs(facts, field_a) + self._extract_evidence_refs(facts, field_b)

        if not passed:
            msg = self._safe_format(rule.get("message_template", ""), {
                "field_a_value": str_a,
                "field_b_value": str_b,
                **facts,
                **params
            })
            return Finding(
                rule_id=rule["id"],
                rule_version=rule.get("version", "1.0.0"),
                clause_ref=rule.get("clause_ref", "N/A"),
                status="fail",
                expected=f"Matching {field_a} and {field_b}",
                found=f"'{str_a}' vs '{str_b}'",
                evidence_refs=evidence_refs,
                severity=rule.get("severity", "critical").lower(),
                human_readable_explanation=msg or f"Discrepancy detected between '{field_a}' and '{field_b}'.",
                remediation=rule.get("remediation_hint", "Rectify discrepancies across submitted statutory documents.")
            )

        return Finding(
            rule_id=rule["id"],
            rule_version=rule.get("version", "1.0.0"),
            clause_ref=rule.get("clause_ref", "N/A"),
            status="pass",
            expected=f"Matching {field_a} and {field_b}",
            found=f"Corroborated '{str_a}'",
            evidence_refs=evidence_refs,
            severity=rule.get("severity", "critical").lower(),
            human_readable_explanation=f"Cross-field consistency verified between {field_a} and {field_b}.",
            remediation=rule.get("remediation_hint", "Maintain consistency in records.")
        )

    # --------------------------------------------------------------------------
    # 5. Ratio Check Evaluator
    # --------------------------------------------------------------------------
    def _eval_ratio_check(self, rule: Dict[str, Any], facts: Dict[str, Any]) -> Finding:
        params = rule.get("parameters", {})
        num_field = params.get("numerator_field", "")
        den_field = params.get("denominator_field", "")

        raw_num = facts.get(num_field)
        raw_den = facts.get(den_field)

        if raw_num is None:
            return self._create_not_evaluable(rule, f"Numerator field '{num_field}' missing from facts.")
        if raw_den is None:
            return self._create_not_evaluable(rule, f"Denominator field '{den_field}' missing from facts.")

        try:
            num = float(raw_num)
            den = float(raw_den)
        except (ValueError, TypeError):
            return self._create_not_evaluable(rule, "Numerator or denominator has non-numeric value.")

        if den <= 0:
            return Finding(
                rule_id=rule["id"],
                rule_version=rule.get("version", "1.0.0"),
                clause_ref=rule.get("clause_ref", "N/A"),
                status="fail",
                expected="Denominator > 0",
                found=f"{den_field} = 0",
                evidence_refs=[],
                severity=rule.get("severity", "critical").lower(),
                human_readable_explanation=f"Denominator '{den_field}' is 0, indicating total absence of required personnel.",
                remediation=rule.get("remediation_hint", "Recruit mandatory faculty members immediately.")
            )

        evidence_refs = self._extract_evidence_refs(facts, num_field) + self._extract_evidence_refs(facts, den_field)

        # Mode A: max_ratio (e.g. FSR 1:20 -> intake / faculty <= 20)
        if "max_ratio" in params:
            max_r = float(params["max_ratio"])
            tolerance_pct = float(params.get("tolerance_pct", 0.0))
            eff_max = max_r * (1.0 + tolerance_pct / 100.0)
            ratio = num / den
            required_faculty = int(num / max_r)
            shortfall = max(0, required_faculty - int(den))

            passed = ratio <= eff_max

            if not passed:
                msg = self._safe_format(rule.get("message_template", ""), {
                    "found_value": ratio,
                    "expected_value": max_r,
                    "tolerance_pct": tolerance_pct,
                    "shortfall": shortfall,
                    **facts,
                    **params
                })
                return Finding(
                    rule_id=rule["id"],
                    rule_version=rule.get("version", "1.0.0"),
                    clause_ref=rule.get("clause_ref", "N/A"),
                    status="fail",
                    expected=f"Ratio <= 1:{max_r:.0f}",
                    found=f"1:{ratio:.1f}",
                    evidence_refs=evidence_refs,
                    severity=rule.get("severity", "critical").lower(),
                    human_readable_explanation=msg or f"Calculated ratio 1:{ratio:.1f} exceeds allowable 1:{max_r:.0f}.",
                    remediation=rule.get("remediation_hint", "Appoint required faculty members or reduce student intake.")
                )

            return Finding(
                rule_id=rule["id"],
                rule_version=rule.get("version", "1.0.0"),
                clause_ref=rule.get("clause_ref", "N/A"),
                status="pass",
                expected=f"Ratio <= 1:{max_r:.0f}",
                found=f"1:{ratio:.1f}",
                evidence_refs=evidence_refs,
                severity=rule.get("severity", "critical").lower(),
                human_readable_explanation=f"Ratio condition satisfied (1:{ratio:.1f} <= 1:{max_r:.0f}).",
                remediation=rule.get("remediation_hint", "Maintain required faculty staffing.")
            )

        # Mode B: min_ratio_pct (e.g. Professor cadre proportion >= 11.1%)
        if "min_ratio_pct" in params:
            min_pct = float(params["min_ratio_pct"])
            ratio_pct = (num / den) * 100.0
            passed = ratio_pct >= min_pct

            if not passed:
                msg = self._safe_format(rule.get("message_template", ""), {
                    "found_value": ratio_pct,
                    "expected_value": min_pct,
                    **facts,
                    **params
                })
                return Finding(
                    rule_id=rule["id"],
                    rule_version=rule.get("version", "1.0.0"),
                    clause_ref=rule.get("clause_ref", "N/A"),
                    status="fail",
                    expected=f">= {min_pct:.1f}%",
                    found=f"{ratio_pct:.1f}%",
                    evidence_refs=evidence_refs,
                    severity=rule.get("severity", "warning").lower(),
                    human_readable_explanation=msg or f"Cadre percentage {ratio_pct:.1f}% below minimum {min_pct:.1f}%.",
                    remediation=rule.get("remediation_hint", "Recruit senior cadre faculty.")
                )

            return Finding(
                rule_id=rule["id"],
                rule_version=rule.get("version", "1.0.0"),
                clause_ref=rule.get("clause_ref", "N/A"),
                status="pass",
                expected=f">= {min_pct:.1f}%",
                found=f"{ratio_pct:.1f}%",
                evidence_refs=evidence_refs,
                severity=rule.get("severity", "warning").lower(),
                human_readable_explanation=f"Cadre percentage requirement satisfied ({ratio_pct:.1f}% >= {min_pct:.1f}%).",
                remediation=rule.get("remediation_hint", "Maintain faculty cadre balance.")
            )

        return self._create_not_evaluable(rule, "Ratio check parameters lack 'max_ratio' or 'min_ratio_pct'.")

    # --------------------------------------------------------------------------
    # 6. Custom Condition Evaluator
    # --------------------------------------------------------------------------
    def _eval_custom(self, rule: Dict[str, Any], facts: Dict[str, Any]) -> Finding:
        params = rule.get("parameters", {})
        cond_expr = params.get("condition") or rule.get("condition")

        if not cond_expr:
            return self._create_not_evaluable(rule, "No condition expression specified for custom rule.")

        if "required_committees" in params and "established_committees" not in facts:
            return self._create_not_evaluable(rule, "Field 'established_committees' missing from application facts.")

        eval_scope = {
            "facts": facts,
            "params": params,
            "all": all,
            "any": any,
            "len": len,
            "max": max,
            "min": min
        }

        try:
            passed = bool(eval(cond_expr, eval_scope))
        except (KeyError, NameError, TypeError) as ex:
            return self._create_not_evaluable(rule, f"Prerequisite facts missing for custom condition: {ex}")
        except Exception as ex:
            return self._create_not_evaluable(rule, f"Runtime error in condition expression: {ex}")

        # Compute missing committees if relevant
        missing_comm = []
        if "required_committees" in params:
            est = facts.get("established_committees", [])
            missing_comm = [c for c in params["required_committees"] if c not in est]

        if not passed:
            msg = self._safe_format(rule.get("message_template", ""), {
                "missing_committees": ", ".join(missing_comm) if missing_comm else "Required conditions unsatisfied",
                **facts,
                **params
            })
            return Finding(
                rule_id=rule["id"],
                rule_version=rule.get("version", "1.0.0"),
                clause_ref=rule.get("clause_ref", "N/A"),
                status="fail",
                expected="Custom condition satisfied",
                found="Condition failed",
                evidence_refs=[],
                severity=rule.get("severity", "warning").lower(),
                human_readable_explanation=msg or "Custom statutory condition was not satisfied.",
                remediation=rule.get("remediation_hint", "Comply with prescribed statutory mandate.")
            )

        return Finding(
            rule_id=rule["id"],
            rule_version=rule.get("version", "1.0.0"),
            clause_ref=rule.get("clause_ref", "N/A"),
            status="pass",
            expected="Custom condition satisfied",
            found="Condition satisfied",
            evidence_refs=[],
            severity=rule.get("severity", "warning").lower(),
            human_readable_explanation=f"Custom statutory condition verified under {rule.get('clause_ref')}.",
            remediation=rule.get("remediation_hint", "Maintain compliance.")
        )

    # ==========================================================================
    # DRY RUN / WHAT-IF SIMULATOR (Prompt 4.2)
    # ==========================================================================

    def dry_run(self, rules: Optional[List[Dict[str, Any]]] = None,
                applications: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Executes a dry-run evaluation across multiple application facts.
        Enables the What-If Simulator by calculating aggregate impact metrics,
        pass/fail distributions, and pinpointing affected institutions.
        """
        apps = applications or []
        eval_rules = {}

        eval_rules = dict(self.rules_registry)
        if rules is not None:
            # Validate and merge custom/tweaked rules on-the-fly
            for r in rules:
                r_id = r.get("id")
                target_id = r_id if (r_id and r_id in eval_rules) else None
                if not target_id:
                    # Match by keyword or clause reference
                    ref_text = f"{r_id or ''} {r.get('clause_ref') or ''}".upper()
                    for cand_id, cand_rule in eval_rules.items():
                        cand_ref = str(cand_rule.get("clause_ref", "")).upper()
                        if cand_id in ref_text or (cand_ref and cand_ref in ref_text):
                            target_id = cand_id
                            break
                        if ("FSR" in ref_text or "2.7" in ref_text) and "FACULTY_STUDENT_RATIO" in cand_id:
                            target_id = cand_id
                            break
                        if ("AREA" in ref_text or "2.4" in ref_text) and "AREA" in cand_id:
                            target_id = cand_id
                            break
                        if ("LAND" in ref_text or "2.3" in ref_text) and "MINIMUM_LAND" in cand_id:
                            target_id = cand_id
                            break
                if target_id and target_id in eval_rules:
                    merged = dict(eval_rules[target_id])
                    for k, v in r.items():
                        if k == "parameters" and isinstance(v, dict) and isinstance(merged.get("parameters"), dict):
                            merged["parameters"] = {**merged["parameters"], **v}
                        elif k not in ("id", "version"):
                            merged[k] = v
                    eval_rules[target_id] = merged
                else:
                    # Ensure minimal schema properties before validation
                    rule_to_validate = {
                        "version": "1.0.0",
                        "clause_ref": r.get("clause_ref", "APH-2025-Cl-General"),
                        "title": r.get("title", r_id or "Custom Rule"),
                        "applies_to": ["Extension of Approval (EoA)"],
                        "type": "custom",
                        "parameters": {},
                        "severity": "warning",
                        "message_template": "Indicator for review: rule condition evaluated",
                        "remediation_hint": "Review institution compliance parameters",
                        "effective_from": "2025-01-01",
                        **r
                    }
                    self.validate_rule(rule_to_validate)
                    eval_rules[rule_to_validate["id"]] = rule_to_validate

        total_evaluations = 0
        status_counts = {"pass": 0, "fail": 0, "not_evaluable": 0}
        severity_counts = {"critical": 0, "warning": 0, "info": 0}
        affected_apps = set()

        rule_impact: Dict[str, Dict[str, Any]] = {}
        for r_id, r in eval_rules.items():
            rule_impact[r_id] = {
                "rule_id": r_id,
                "clause_ref": r.get("clause_ref", "N/A"),
                "title": r.get("title", ""),
                "severity": r.get("severity", "warning").lower(),
                "type": r.get("type", "custom"),
                "evaluated": 0,
                "passed": 0,
                "failed": 0,
                "not_evaluable": 0,
                "failure_rate_pct": 0.0
            }

        # Temporarily swap active registry if custom rules provided
        saved_registry = self.rules_registry
        try:
            self.rules_registry = eval_rules

            for app_idx, app_facts in enumerate(apps):
                app_id = app_facts.get("id") or app_facts.get("application_id") or f"APP_{app_idx+1}"
                findings = self.evaluate(app_facts)

                for f in findings:
                    total_evaluations += 1
                    status_counts[f.status] += 1
                    
                    r_stat = rule_impact[f.rule_id]
                    r_stat["evaluated"] += 1

                    if f.status == "pass":
                        r_stat["passed"] += 1
                    elif f.status == "fail":
                        r_stat["failed"] += 1
                        sev = f.severity.lower()
                        if sev in severity_counts:
                            severity_counts[sev] += 1
                        if sev in ["critical", "warning"]:
                            affected_apps.add(str(app_id))
                    elif f.status == "not_evaluable":
                        r_stat["not_evaluable"] += 1

        finally:
            self.rules_registry = saved_registry

        # Compute percentage metrics
        for r_stat in rule_impact.values():
            if r_stat["evaluated"] > 0:
                r_stat["failure_rate_pct"] = round((r_stat["failed"] / r_stat["evaluated"]) * 100.0, 2)

        total_passed = status_counts["pass"]
        overall_compliance = round((total_passed / total_evaluations * 100.0), 2) if total_evaluations > 0 else 100.0

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_applications": len(apps),
            "total_rules_evaluated": len(eval_rules),
            "total_evaluations": total_evaluations,
            "overall_compliance_rate_pct": overall_compliance,
            "summary_by_status": status_counts,
            "findings_by_severity": severity_counts,
            "affected_applications_count": len(affected_apps),
            "affected_applications": sorted(list(affected_apps)),
            "rule_impact": rule_impact
        }

    # ==========================================================================
    # HELPER UTILITIES
    # ==========================================================================

    def _create_not_evaluable(self, rule: Dict[str, Any], reason: str) -> Finding:
        return Finding(
            rule_id=rule.get("id", "UNKNOWN"),
            rule_version=rule.get("version", "1.0.0"),
            clause_ref=rule.get("clause_ref", "N/A"),
            status="not_evaluable",
            expected="Extracted fact data",
            found=None,
            evidence_refs=[],
            severity=rule.get("severity", "warning").lower(),
            human_readable_explanation=f"Cannot evaluate rule {rule.get('clause_ref')}: {reason}",
            remediation=rule.get("remediation_hint", "Provide complete institutional facts for evaluation.")
        )

    def _extract_evidence_refs(self, facts: Dict[str, Any], field_name: str) -> List[Dict[str, Any]]:
        """Extracts documentary citation references (doc id, page, bbox) if present in facts."""
        refs = facts.get("evidence_refs", {})
        if field_name in refs:
            ref_data = refs[field_name]
            return [ref_data] if isinstance(ref_data, dict) else ref_data
        return []

    def _safe_format(self, template: str, data: Dict[str, Any]) -> str:
        """Safely formats a message template without crashing on missing keys."""
        try:
            return template.format(**data).strip()
        except Exception:
            return template


# Singleton instance
rules_engine = RegulationRulesEngine()
