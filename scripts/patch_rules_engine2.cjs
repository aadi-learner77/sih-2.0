const fs = require('fs');
let code = fs.readFileSync('backend/app/services/rules_engine.py', 'utf8');

const target = `        eval_rules = dict(self.rules_registry)
        if rules is not None:
            # Validate and merge custom/tweaked rules on-the-fly
            for r in rules:
                r_id = r.get("id")
                if r_id and r_id in eval_rules:
                    merged = dict(eval_rules[r_id])
                    for k, v in r.items():
                        if k == "parameters" and isinstance(v, dict) and isinstance(merged.get("parameters"), dict):
                            merged["parameters"] = {**merged["parameters"], **v}
                        else:
                            merged[k] = v
                    eval_rules[r_id] = merged
                else:
                    self.validate_rule(r)
                    eval_rules[r["id"]] = r`;

const rep = `        eval_rules = dict(self.rules_registry)
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
                    eval_rules[rule_to_validate["id"]] = rule_to_validate`;

code = code.replace(target, rep).replace(target.replace(/\n/g, '\r\n'), rep.replace(/\n/g, '\r\n'));
fs.writeFileSync('backend/app/services/rules_engine.py', code, 'utf8');
console.log('Successfully updated backend/app/services/rules_engine.py with robust rule matching');

