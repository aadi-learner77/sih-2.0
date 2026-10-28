import yaml
from pathlib import Path

yaml_path = Path("backend/app/rules/aicte_aph_2025.yaml")
with open(yaml_path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

rules = data.get("rules", [])
print(f"Total rules parsed: {len(rules)}")

# Read raw file lines to get comments on each rule
with open(yaml_path, "r", encoding="utf-8") as f:
    raw_lines = f.readlines()

placeholder_comments = {}
current_rule = None
for line in raw_lines:
    if line.strip().startswith("- id:"):
        current_rule = line.strip().split("- id:")[1].strip().strip('"').strip("'")
        placeholder_comments[current_rule] = []
    elif "PLACEHOLDER:" in line and current_rule:
        comment_part = line[line.find("PLACEHOLDER:") :].strip()
        placeholder_comments[current_rule].append(comment_part)

md_lines = [
    "# AICTE Approval Process Handbook (APH) 2025-26: Regulation-as-Code Rules Catalog",
    "",
    f"**Source File:** [`backend/app/rules/aicte_aph_2025.yaml`](file:///a:/SIH_AKXY/backend/app/rules/aicte_aph_2025.yaml)  ",
    f"**Handbook Edition:** {data.get('handbook_edition', 'AICTE Approval Process Handbook (APH) 2025-26')}  ",
    f"**Rule Pack Version:** {data.get('version', '2.0.0')}  ",
    f"**Total Statutory Rules:** **{len(rules)} Rules**  ",
    "",
    "---",
    "",
    "## Verification & Placeholder Status Summary",
    "",
    "> [!WARNING]",
    "> **APH Verification Finding:**  ",
    "> **All 12 rules (100%)** contain parameters marked with the comment:  ",
    "> `# PLACEHOLDER: Confirm with current Approval Process Handbook edition`.  ",
    "> **Zero (0) numeric parameters have been officially verified against the Gazette of India or statutory AICTE Gazette notification.**  ",
    "> Every numeric threshold (such as FSR 1:20, 10.5 sqm/student, urban 2.5 acres, rural 7.5 acres, NOC age 24 months, grace period 0 days, fuzzy threshold 0.85) is an engineering placeholder pending formal regulatory sign-off.",
    "",
    "---",
    "",
    "## Complete Rules Inventory",
    "",
    "| Rule ID | Clause Ref | Title | Type | Severity | What it Checks | Parameters | Handbook Verification Status |",
    "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
]

for r in rules:
    rule_id = r.get("id", "")
    clause = r.get("clause_ref", "")
    title = r.get("title", "")
    rtype = r.get("type", "")
    sev = r.get("severity", "")
    desc = r.get("description", "")
    params = r.get("parameters", {})
    param_str = "<br>".join([f"• **{k}**: `{v}`" for k, v in params.items()])

    # Check comments
    comments = placeholder_comments.get(rule_id, [])
    if comments:
        status = "NOT VERIFIED<br><small>(Placeholder: " + "; ".join(comments) + ")</small>"
    else:
        status = "NOT VERIFIED"

    md_lines.append(
        f"| `{rule_id}` | `{clause}` | **{title}** | `{rtype}` | `{sev}` | {desc} | {param_str} | {status} |"
    )

out_path = Path("evidence_pack/rules_table.md")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines) + "\n")

print(f"Successfully wrote {len(rules)} rules to {out_path}")
