const fs = require('fs');
let code = fs.readFileSync('backend/app/services/rules_engine.py', 'utf8');

const target = `        if rules is not None:
            # Validate custom rules on-the-fly
            for r in rules:
                self.validate_rule(r)
                eval_rules[r["id"]] = r
        else:
            eval_rules = self.rules_registry`;

const rep = `        eval_rules = dict(self.rules_registry)
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

code = code.replace(target, rep).replace(target.replace(/\n/g, '\r\n'), rep.replace(/\n/g, '\r\n'));
fs.writeFileSync('backend/app/services/rules_engine.py', code, 'utf8');
console.log('Successfully updated backend/app/services/rules_engine.py');

