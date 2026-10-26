"""
Regulation-as-Code Engine:
Parses YAML handbook clause packs, evaluates institutional application facts,
and outputs explainable compliance indicators with exact regulatory citations.
Advisory-only: All flags generate indicators for review, never automatic rejections.
"""
import os
import yaml
from typing import Dict, List, Any
from backend.app.core.config import settings

class RegulationRulesEngine:
    def __init__(self, rules_dir: str = settings.RULES_DIR):
        self.rules_dir = rules_dir
        self.rule_packs: Dict[str, Any] = {}
        self.load_all_rules()

    def load_all_rules(self):
        """Loads all YAML rule definition files from the rules directory."""
        self.rule_packs.clear()
        if not os.path.exists(self.rules_dir):
            return

        for filename in os.listdir(self.rules_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(self.rules_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if data and "rules" in data:
                            pack_id = data.get("handbook_edition", filename)
                            self.rule_packs[pack_id] = data
                except Exception as e:
                    print(f"Error loading rule file {filename}: {e}")

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Returns flattened list of active rules for administrative review."""
        all_rules = []
        for pack_name, pack_data in self.rule_packs.items():
            edition = pack_data.get("handbook_edition", "APH 2025-26")
            for rule in pack_data.get("rules", []):
                r = dict(rule)
                r["handbook_edition"] = edition
                all_rules.append(r)
        return all_rules

    def update_rule(self, rule_id: str, updated_rule: Dict[str, Any]) -> bool:
        """Dynamically updates a rule parameter or condition in the active YAML pack."""
        for filename in os.listdir(self.rules_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(self.rules_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    
                    found = False
                    if data and "rules" in data:
                        for idx, r in enumerate(data["rules"]):
                            if r.get("id") == rule_id:
                                data["rules"][idx] = {**r, **updated_rule}
                                found = True
                                break
                    if found:
                        with open(filepath, "w", encoding="utf-8") as f:
                            yaml.dump(data, f, sort_keys=False)
                        self.load_all_rules()
                        return True
                except Exception as e:
                    print(f"Error updating rule {rule_id}: {e}")
        return False

    def evaluate_application(self, facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluates institutional facts against all configured handbook rules.
        Returns a structured list of evaluation results with citations and explainability details.
        """
        results = []
        
        # Provide calculated facts if missing
        sanctioned_intake = facts.get("sanctioned_intake", 300)
        total_faculty = facts.get("total_faculty", 15)
        professors = facts.get("professors_count", 2)
        built_up_area = facts.get("built_up_area_sqm", 12000.0)
        
        calculated_fsr = (sanctioned_intake / total_faculty) if total_faculty > 0 else 999.0
        professor_pct = (professors / total_faculty * 100.0) if total_faculty > 0 else 0.0
        
        eval_facts = {
            **facts,
            "calculated_fsr": calculated_fsr,
            "professor_percentage": professor_pct,
            "deficiency_faculty": max(0, int(sanctioned_intake / 20) - total_faculty),
            "required_area": sanctioned_intake * 10.5
        }

        for pack_name, pack_data in self.rule_packs.items():
            edition = pack_data.get("handbook_edition", "AICTE APH 2025-26")
            for rule in pack_data.get("rules", []):
                rule_id = rule.get("id")
                clause_id = rule.get("clause_id")
                clause_title = rule.get("clause_title")
                severity = rule.get("severity", "WARNING")
                condition_expr = rule.get("condition")
                params = rule.get("parameters", {})
                
                passed = True
                failure_msg = ""
                
                try:
                    # Safe evaluation with bounded context
                    eval_scope = {
                        "facts": eval_facts,
                        "params": params,
                        "min": min,
                        "max": max,
                        "len": len
                    }
                    if condition_expr:
                        passed = bool(eval(condition_expr, {"__builtins__": {}}, eval_scope))
                except Exception as ex:
                    # If expression has missing keys or fails, flag for manual review
                    passed = False
                    failure_msg = f"Evaluation prerequisite missing: {ex}"
                
                if not passed:
                    if not failure_msg:
                        raw_msg = rule.get("failure_message", "Rule condition violated.")
                        try:
                            # Render message template with merged facts and params
                            format_dict = {**eval_facts, **params}
                            failure_msg = raw_msg.format(**format_dict).strip()
                        except Exception:
                            failure_msg = raw_msg
                            
                    results.append({
                        "rule_id": rule_id,
                        "clause_id": clause_id,
                        "clause_title": clause_title,
                        "handbook_edition": edition,
                        "severity": severity,
                        "passed": False,
                        "explanation": failure_msg,
                        "claim_summary": f"Institution reported: FSR 1:{calculated_fsr:.1f}, Area: {built_up_area} sqm, Professors: {professors}",
                        "evidence_details": {
                            "clause_reference": f"{clause_id} ({clause_title})",
                            "evaluated_values": {
                                "calculated_fsr": round(calculated_fsr, 1),
                                "built_up_area_sqm": built_up_area,
                                "professor_pct": round(professor_pct, 1),
                                "fire_noc_expiry": eval_facts.get("fire_noc_expiry_date", "N/A")
                            },
                            "regulatory_threshold": params
                        },
                        "advisory_disclaimer": "AI Flag: Indicator for officer review. Not an automated rejection."
                    })
                else:
                    results.append({
                        "rule_id": rule_id,
                        "clause_id": clause_id,
                        "clause_title": clause_title,
                        "handbook_edition": edition,
                        "severity": severity,
                        "passed": True,
                        "explanation": f"Compliant with {clause_title} under {clause_id}.",
                        "claim_summary": "Requirements verified successfully against documented facts.",
                        "evidence_details": {
                            "clause_reference": f"{clause_id} ({clause_title})",
                            "status": "COMPLIANT"
                        },
                        "advisory_disclaimer": "AI Flag: Verified compliant based on submitted documentation."
                    })

        return results

# Singleton instance
rules_engine = RegulationRulesEngine()
