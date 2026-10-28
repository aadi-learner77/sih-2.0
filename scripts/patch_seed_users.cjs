const fs = require('fs');
let content = fs.readFileSync('backend/app/data/seed_data.py', 'utf8');

// Ensure auditor and senior_officer roles are in roles list
const targetRoles = `    # 1. Predefined Roles
    roles = [
        Role(code="scrutiny_officer", name="Scrutiny Committee Officer", description="Reviews application dossiers, inspects Evidence Lens, issues show-cause inquiries."),
        Role(code="regional_officer", name="Regional Bureau Officer", description="Regional regulatory oversight, hearing coordination, and final approvals."),
        Role(code="admin", name="Central AICTE Administrator", description="Regulation-as-Code YAML configuration and platform auditing."),
        Role(code="institution_user", name="Institution Registrar / Representative", description="Submits applications, uploads compliance documents, views pre-flight scores.")
    ]`;

const repRoles = `    # 1. Predefined Roles
    roles = [
        Role(code="scrutiny_officer", name="Scrutiny Committee Officer", description="Reviews application dossiers, inspects Evidence Lens, issues show-cause inquiries."),
        Role(code="senior_officer", name="Senior Regulatory Officer", description="Senior regulatory oversight, What-If dry-runs, and rule pack management."),
        Role(code="regional_officer", name="Regional Bureau Officer", description="Regional regulatory oversight, hearing coordination, and final approvals."),
        Role(code="admin", name="Central AICTE Administrator", description="Regulation-as-Code YAML configuration and platform auditing."),
        Role(code="auditor", name="Statutory Compliance Auditor", description="Read-only audit access to immutable ledger receipts and access logs."),
        Role(code="institution_user", name="Institution Registrar / Representative", description="Submits applications, uploads compliance documents, views pre-flight scores.")
    ]`;

content = content.replace(targetRoles, repRoles).replace(targetRoles.replace(/\n/g, '\r\n'), repRoles.replace(/\n/g, '\r\n'));

// Add auditor to users list
const targetUsers = `        User(
            email="admin@aicte-india.org",
            hashed_password=hash_password("AicteAdmin@2025"),
            full_name="Chief Technology Cell",
            role="admin",
            role_id=role_map.get("admin"),
            is_active=True
        ),`;

const repUsers = `        User(
            email="admin@aicte-india.org",
            hashed_password=hash_password("AicteAdmin@2025"),
            full_name="Chief Technology Cell",
            role="admin",
            role_id=role_map.get("admin"),
            is_active=True
        ),
        User(
            email="auditor@aicte-india.org",
            hashed_password=hash_password("AicteAuditor@2025"),
            full_name="Independent Statutory Auditor",
            role="auditor",
            role_id=role_map.get("auditor"),
            is_active=True
        ),`;

content = content.replace(targetUsers, repUsers).replace(targetUsers.replace(/\n/g, '\r\n'), repUsers.replace(/\n/g, '\r\n'));

fs.writeFileSync('backend/app/data/seed_data.py', content, 'utf8');
console.log('Patched seed_data.py with auditor and senior_officer accounts');

