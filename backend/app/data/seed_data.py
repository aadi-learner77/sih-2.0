"""
Database Seeder for PRAMAAN-X:
Populates realistic, anonymized synthetic data for AICTE hackathon demonstration:
- Officer and Institution User credentials
- Engineering Colleges with authentic profiles
- Extension of Approval (EoA) applications with multi-layered review indicators
- Cryptographically chained audit receipts
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import hash_password
from backend.app.models.models import (
    Role, User, Institution, ApplicationCategory, Application, Document,
    ExtractedField, Rule, RuleVersion, Finding, Verification, Receipt,
    Alert, OfficerAction, AuditLog,
    VerificationCheck, RuleEvaluation, AuditReceipt
)
from backend.app.services.audit_chain import AuditChainService
from backend.app.services.rules_engine import rules_engine
from backend.app.services.impossibility_engine import impossibility_engine
from backend.app.services.forensics_engine import forensics_engine

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # If users already exist, skip re-seeding
    if db.query(User).first():
        db.close()
        return

    print("Seeding PRAMAAN-X Database with synthetic benchmark data...")

    # 1. Predefined Roles
    roles = [
        Role(code="scrutiny_officer", name="Scrutiny Committee Officer", description="Reviews application dossiers, inspects Evidence Lens, issues show-cause inquiries."),
        Role(code="regional_officer", name="Regional Bureau Officer", description="Regional regulatory oversight, hearing coordination, and final approvals."),
        Role(code="admin", name="Central AICTE Administrator", description="Regulation-as-Code YAML configuration and platform auditing."),
        Role(code="institution_user", name="Institution Registrar / Representative", description="Submits applications, uploads compliance documents, views pre-flight scores.")
    ]
    db.add_all(roles)
    db.commit()

    role_map = {r.code: r.id for r in db.query(Role).all()}

    # 2. Application Categories
    categories = [
        ApplicationCategory(
            code="EOA",
            name="Extension of Approval (EoA)",
            description="Annual extension of approval for established technical institutions.",
            required_documents=["DOC_FIRE_NOC", "DOC_LAND_TITLE", "DOC_BUILDING_PLAN", "DOC_FACULTY_ROSTER", "DOC_AFFILIATION_ORDER"]
        ),
        ApplicationCategory(
            code="INCREASE_INTAKE",
            name="Increase in Sanctioned Intake",
            description="Expansion of student intake in accredited engineering or management courses.",
            required_documents=["DOC_FIRE_NOC", "DOC_ADDITIONAL_AREA_PROOF", "DOC_NBA_ACCREDITATION", "DOC_FACULTY_ROSTER"]
        )
    ]
    db.add_all(categories)
    db.commit()

    cat_map = {c.code: c.id for c in db.query(ApplicationCategory).all()}

    # 3. Users & Roles
    users = [
        User(
            email="scrutiny.officer@aicte-india.org",
            hashed_password=hash_password("AicteOfficer@2025"),
            full_name="Dr. Sunita Deshmukh",
            role="scrutiny_officer",
            role_id=role_map.get("scrutiny_officer"),
            is_active=True
        ),
        User(
            email="regional.officer@aicte-india.org",
            hashed_password=hash_password("AicteRegional@2025"),
            full_name="Shri Arvind Kulkarni",
            role="regional_officer",
            role_id=role_map.get("regional_officer"),
            is_active=True
        ),
        User(
            email="admin@aicte-india.org",
            hashed_password=hash_password("AicteAdmin@2025"),
            full_name="Chief Technology Cell",
            role="admin",
            role_id=role_map.get("admin"),
            is_active=True
        ),
        User(
            email="registrar@apextech.edu.in",
            hashed_password=hash_password("ApexPass@2025"),
            full_name="Prof. C. V. Ramanathan (Apex Registrar)",
            role="institution_user",
            role_id=role_map.get("institution_user"),
            is_active=True
        )
    ]
    db.add_all(users)
    db.commit()

    # 2. Institutions
    inst1 = Institution(
        aicte_id="1-109283711",
        name="Apex Institute of Technology & Science",
        state="Karnataka",
        city="Bengaluru",
        category="Engineering & Technology",
        approved_intake=480,
        total_built_up_area_sqm=8500.0,
        land_area_acres=5.5,
        survey_numbers="Sy. No. 42/1 & 42/2",
        address="Sector 9, Devanahalli Knowledge Corridor, Bengaluru Rural - 562110",
        trust_name="Apex Vidya Foundation",
        status="ACTIVE"
    )
    inst2 = Institution(
        aicte_id="1-209384722",
        name="Royal College of Engineering",
        state="Karnataka",
        city="Mysuru",
        category="Engineering & Technology",
        approved_intake=360,
        total_built_up_area_sqm=14200.0,
        land_area_acres=7.5,
        survey_numbers="Sy. No. 108/3",
        address="Hebbal Industrial Estate, Mysuru - 570016",
        trust_name="Royal Educational Trust",
        status="ACTIVE"
    )
    inst3 = Institution(
        aicte_id="1-309485733",
        name="National Academy of Technical Studies",
        state="Karnataka",
        city="Bengaluru",
        category="Engineering & Technology",
        approved_intake=420,
        total_built_up_area_sqm=16000.0,
        land_area_acres=6.2,
        survey_numbers="Sy. No. 42/1",
        address="Whitefield IT Corridor, Bengaluru - 560066",
        trust_name="Apex Vidya Foundation",
        status="ACTIVE"
    )
    inst4 = Institution(
        aicte_id="1-409586744",
        name="Zenith Institute of Engineering",
        state="Karnataka",
        city="Mangaluru",
        category="Engineering & Technology",
        approved_intake=300,
        total_built_up_area_sqm=12500.0,
        land_area_acres=5.8,
        survey_numbers="Sy. No. 71/B",
        address="Surathkal Beach Road, Mangaluru - 575025",
        trust_name="Zenith Charitable Trust",
        status="ACTIVE"
    )
    db.add_all([inst1, inst2, inst3, inst4])
    db.commit()

    # Link institutional user
    users[3].institution_id = inst1.id
    db.commit()

    # 3. Flagship Demo Application for Apex Institute
    now = datetime.now(timezone.utc)
    app1 = Application(
        application_no="EOA-2025-ENG-9821",
        institution_id=inst1.id,
        academic_year="2025-26",
        category="Extension of Approval (EoA)",
        status="UNDER_SCRUTINY",
        preflight_readiness_score=72.4,
        checklist_completion_pct=85.7,
        advisory_flags_count=4,
        impossibility_flags_count=2,
        forensic_flags_count=3,
        issuer_discrepancy_count=2,
        ai_advisory_summary=(
            "Advisory Review Summary: 4 regulatory indicator flags generated. "
            "1. Impossibility Engine detected dual employment for HOD Dr. R. K. Sharma (also full-time at Royal College). "
            "2. Survey No. 42/1 simultaneously claimed by National Academy. "
            "3. State Fire Portal returns lapsed NOC. "
            "4. Photo Reuse Radar identified computer lab photo submitted in 2024 by Royal College of Engineering. "
            "All findings are decision-support indicators for scrutiny committee inquiry."
        ),
        submission_date=now - timedelta(days=5),
        created_at=now - timedelta(days=5),
        updated_at=now
    )
    
    # Clean benchmark application for Royal College
    app2 = Application(
        application_no="EOA-2025-ENG-1102",
        institution_id=inst2.id,
        academic_year="2025-26",
        category="Extension of Approval (EoA)",
        status="APPROVED_WITH_CONDITIONS",
        preflight_readiness_score=94.2,
        checklist_completion_pct=100.0,
        advisory_flags_count=1,
        impossibility_flags_count=1,
        forensic_flags_count=0,
        issuer_discrepancy_count=0,
        ai_advisory_summary="High compliance readiness. Minor cadre proportion advisory noted.",
        submission_date=now - timedelta(days=12),
        created_at=now - timedelta(days=12),
        updated_at=now - timedelta(days=2)
    )
    db.add_all([app1, app2])
    db.commit()

    # 4. Documents for App1
    doc_fire = Document(
        application_id=app1.id,
        document_type="Fire Safety Certificate",
        filename="Apex_Fire_NOC_2024_2026.pdf",
        file_path="uploads/Apex_Fire_NOC_2024_2026.pdf",
        file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        file_size_bytes=1420500,
        mime_type="application/pdf",
        classification_confidence=0.98,
        ocr_extracted_text=(
            "GOVERNMENT OF KARNATAKA - DEPARTMENT OF FIRE & EMERGENCY SERVICES\n"
            "NO: FS/2024/991/BFO\nFIRE SAFETY CLEARANCE CERTIFICATE\n"
            "Issued to Apex Institute of Technology & Science\n"
            "Valid up to: 31-03-2026\nSurvey No: 42/1, Devanahalli, Bengaluru Rural."
        ),
        structured_fields={
            "noc_number": "FS/2024/991",
            "issue_date": "2024-05-12",
            "valid_till": "2026-03-31",
            "issuing_authority": "Chief Fire Officer, Bengaluru East",
            "survey_number": "Sy. No. 42/1"
        },
        metadata_forensics={
            "producer": "Adobe Photoshop CS6 (Windows)",
            "software_anomalies": ["Photoshop signature embedded in PDF stream"],
            "creation_date": "2024-05-12T10:14:00Z",
            "modification_date": "2024-11-20T18:44:21Z"
        },
        ela_score=0.74,
        is_flagged_for_review=True,
        review_indicator_tag="METADATA_AND_ELA_ANOMALY",
        review_reason="Digital image manipulation signature (Adobe Photoshop CS6) detected in Fire NOC document stream; ELA divergence 0.74."
    )

    doc_land = Document(
        application_id=app1.id,
        document_type="Land Title Deed",
        filename="Registered_Lease_Deed_Devanahalli_Apex.pdf",
        file_path="uploads/Registered_Lease_Deed_Devanahalli_Apex.pdf",
        file_hash="f4c1d553a9fc2d250bfcf5d9007fc03538bf52f5750ca45db506002c8963c966",
        file_size_bytes=2890100,
        mime_type="application/pdf",
        classification_confidence=0.96,
        ocr_extracted_text=(
            "DEPARTMENT OF STAMPS & REGISTRATION - REGISTERED LEASE DEED NO: 4892/2021\n"
            "Schedule: Revenue Survey No. 42/1 & 42/2, Devanahalli Taluk, 5.5 Acres.\n"
            "Lease Period: 30 Years from 01-06-2021 to 31-05-2051."
        ),
        structured_fields={
            "deed_number": "4892/2021",
            "survey_numbers": "Sy. No. 42/1 & 42/2",
            "extent_acres": 5.5,
            "lease_duration_years": 30,
            "commencement_date": "2021-06-01",
            "expiry_date": "2051-05-31"
        },
        metadata_forensics={"producer": "Canon iR-ADV C5535 Scan-to-PDF", "software_anomalies": []},
        ela_score=0.18,
        is_flagged_for_review=True,
        review_indicator_tag="KNOWLEDGE_GRAPH_LAND_COLLISION",
        review_reason="Knowledge Graph detected Survey No. 42/1 is concurrently claimed by National Academy under App EOA-2023-ENG-8419."
    )

    doc_faculty = Document(
        application_id=app1.id,
        document_type="Faculty Roster",
        filename="Apex_Tech_Faculty_Cadre_Roster_2024.pdf",
        file_path="uploads/Apex_Tech_Faculty_Cadre_Roster_2024.pdf",
        file_hash="a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
        file_size_bytes=840200,
        mime_type="application/pdf",
        classification_confidence=0.99,
        ocr_extracted_text=(
            "APEX INSTITUTE OF TECHNOLOGY - TEACHING FACULTY ROSTER 2024-25\n"
            "1. Dr. R. K. Sharma | Professor & HOD | PAN: AB****89C | Aadhaar: XXXX-XXXX-9021 | Full-Time\n"
            "2. Dr. Priya Sundaram | Associate Professor | PAN: CD****45E | Full-Time\n"
            "Total Sanctioned Intake: 480 UG. Total Regular Faculty Listed: 15."
        ),
        structured_fields={
            "total_faculty": 15,
            "professors": 1,
            "associate_professors": 3,
            "assistant_professors": 11,
            "sanctioned_intake": 480
        },
        metadata_forensics={"producer": "Microsoft Word 2019 PDF Export", "software_anomalies": []},
        ela_score=0.12,
        is_flagged_for_review=True,
        review_indicator_tag="GHOST_FACULTY_DUAL_EMPLOYMENT",
        review_reason="Impossibility Engine flagged Dr. R. K. Sharma concurrently drawing full-time salary at Royal College of Engineering."
    )

    doc_lab_photo = Document(
        application_id=app1.id,
        document_type="Campus/Lab Geo-tagged Photo",
        filename="Computer_Center_Workstation_Lab_A.jpg",
        file_path="uploads/Computer_Center_Workstation_Lab_A.jpg",
        file_hash="b8c7d6e5f4a3b2c10987654321fedcba0123456789abcdef0123456789abcdef",
        file_size_bytes=654000,
        mime_type="image/jpeg",
        classification_confidence=0.94,
        ocr_extracted_text="APEX ADVANCED COMPUTING & AI LABORATORY - 60 DELL OPTIPLEX WORKSTATIONS",
        structured_fields={"lab_name": "AI & Advanced Computing Center", "capacity_seats": 60},
        metadata_forensics={"camera_model": "iPhone 13", "exif_timestamp": "2024-10-10T14:32:00Z"},
        ela_score=0.22,
        phash="a8f0c3d2e1b4a5f6", # Matches Royal College seeded photo in Photo Reuse Radar!
        is_flagged_for_review=True,
        review_indicator_tag="PHOTO_REUSE_RADAR_MATCH",
        review_reason="Perceptual Hash match (98.4% visual similarity) with photo previously submitted by Royal College of Engineering in 2024."
    )

    db.add_all([doc_fire, doc_land, doc_faculty, doc_lab_photo])
    db.commit()

    # 5. External Verification Checks
    verif_fire = VerificationCheck(
        application_id=app1.id,
        document_id=doc_fire.id,
        issuer_type="fire_department",
        issuer_name="Karnataka Fire & Emergency Services Portal",
        status="mismatch_detected",
        query_parameters={"noc_number": "FS/2024/991", "institution_name": inst1.name},
        issuer_response_data={
            "portal_record": {
                "noc_number": "FS/2024/991",
                "registered_entity": "Apex Commercial Shopping Mall",
                "occupancy_type": "Commercial - Mercantile",
                "status": "VALID_COMMERCIAL"
            }
        },
        discrepancy_details=[
            {
                "field": "registered_entity",
                "claimed": "Apex Institute of Technology & Science",
                "issuer_record": "Apex Commercial Shopping Mall",
                "issue": "NOC number registered to commercial property rather than educational institution."
            }
        ],
        latency_ms=124,
        verified_at=now - timedelta(days=4)
    )

    verif_tax = VerificationCheck(
        application_id=app1.id,
        document_id=doc_faculty.id,
        issuer_type="cbdt_income_tax",
        issuer_name="Central Board of Direct Taxes (CBDT) TRACES",
        status="mismatch_detected",
        query_parameters={"pan_masked": "AB****89C", "faculty_name": "Dr. R. K. Sharma"},
        issuer_response_data={
            "active_employers": [
                {"name": "Apex Institute of Technology", "tan": "BLRA99182A"},
                {"name": "Royal College of Engineering", "tan": "MYSR28191B"}
            ]
        },
        discrepancy_details=[
            {
                "field": "concurrent_employers",
                "claimed": "Sole Full-Time appointment at Apex Institute",
                "issuer_record": "Simultaneous Section 192 (Salary) TDS deductions by 2 colleges in Q1-Q3 2024.",
                "issue": "Dual salary disbursement confirmed on tax portal."
            }
        ],
        latency_ms=168,
        verified_at=now - timedelta(days=4)
    )

    verif_univ = VerificationCheck(
        application_id=app1.id,
        document_id=None,
        issuer_type="university_affiliation",
        issuer_name="Visvesvaraya Technological University (VTU) Affiliation Cell",
        status="verified",
        query_parameters={"aicte_id": inst1.aicte_id, "year": "2025-26"},
        issuer_response_data={
            "affiliation_order": "VTU/ACA/2024-25/A-4/1049",
            "status": "ACTIVE_AFFILIATION",
            "branches": ["CSE", "ECE", "AI & DS"]
        },
        discrepancy_details=[],
        latency_ms=89,
        verified_at=now - timedelta(days=4)
    )

    db.add_all([verif_fire, verif_tax, verif_univ])
    db.commit()

    # 6. Rule Evaluations (Regulation-as-Code)
    rule_evals = [
        RuleEvaluation(
            application_id=app1.id,
            rule_id="RULE_FACULTY_STUDENT_RATIO",
            clause_id="APH-2025-Cl-4.1.1",
            clause_title="Faculty to Student Ratio (FSR) in Technical Programs",
            handbook_edition="AICTE APH 2025-26",
            severity="CRITICAL",
            passed=False,
            claim_summary="Sanctioned Intake: 480 UG | Regular Faculty: 15 | Claimed FSR: 1:32.0",
            evidence_details={
                "clause_id": "APH-2025-Cl-4.1.1",
                "statutory_norm": "1:20",
                "calculated_fsr": "1:32.0",
                "deficiency": 9
            },
            explanation="Calculated Faculty-to-Student Ratio is 1:32.0, exceeding statutory 1:20 ceiling. Institutional shortfall: 9 regular faculty members.",
            officer_decision="CLARIFICATION_ISSUED",
            officer_comment="Formal clarification letter dispatched requesting audited appointment orders and biometric logs.",
            evaluated_at=now - timedelta(days=4)
        ),
        RuleEvaluation(
            application_id=app1.id,
            rule_id="RULE_BUILT_UP_AREA_CAPACITY",
            clause_id="APH-2025-Cl-5.2.4",
            clause_title="Minimum Instructional & Administrative Carpet Area",
            handbook_edition="AICTE APH 2025-26",
            severity="CRITICAL",
            passed=False,
            claim_summary="Reported Built-Up Carpet Area: 8,500.0 sq.m | Proposed Intake: 480",
            evidence_details={
                "clause_id": "APH-2025-Cl-5.2.4",
                "mandated_area_sqm": 20160.0,
                "reported_area_sqm": 8500.0,
                "shortfall_sqm": 11660.0
            },
            explanation="Existing built-up carpet area (8,500 sq.m) is insufficient for total enrolled student population. Severe physical density violation.",
            officer_decision="PENDING_REVIEW",
            officer_comment=None,
            evaluated_at=now - timedelta(days=4)
        ),
        RuleEvaluation(
            application_id=app1.id,
            rule_id="RULE_LAND_TITLE_CONTINUITY",
            clause_id="APH-2025-Cl-7.1.5",
            clause_title="Clear Land Title & Unbroken Leasehold Possession",
            handbook_edition="AICTE APH 2025-26",
            severity="CRITICAL",
            passed=False,
            claim_summary="Lease Deed No. 4892/2021 | Sy. No. 42/1 (5.5 Acres)",
            evidence_details={
                "clause_id": "APH-2025-Cl-7.1.5",
                "conflict_note": "Conflicting claim identified on Survey 42/1 by National Academy."
            },
            explanation="Title continuity indicator flagged due to simultaneous campus claim on identical revenue parcel.",
            officer_decision="PENDING_REVIEW",
            officer_comment=None,
            evaluated_at=now - timedelta(days=4)
        ),
        RuleEvaluation(
            application_id=app1.id,
            rule_id="RULE_UNIVERSITY_AFFILIATION_STATUS",
            clause_id="APH-2025-Cl-8.4.1",
            clause_title="Valid State/Central University Affiliation Order",
            handbook_edition="AICTE APH 2025-26",
            severity="CRITICAL",
            passed=True,
            claim_summary="Order No. VTU/ACA/2024-25/A-4/1049 | Active Affiliation",
            evidence_details={"clause_id": "APH-2025-Cl-8.4.1", "status": "VERIFIED"},
            explanation="Active VTU affiliation authenticated for academic session 2025-26.",
            officer_decision="ACCEPTED_WITH_NOTE",
            officer_comment="Affiliation verified on university portal.",
            evaluated_at=now - timedelta(days=4)
        )
    ]
    db.add_all(rule_evals)
    db.commit()

    # 7. Hash-Chained Verification Receipts (Audit Ledger)
    audit_events = [
        {
            "event_type": "APPLICATION_SUBMITTED",
            "payload": {"application_no": app1.application_no, "institution": inst1.name, "category": app1.category},
            "actor_email": "registrar@apextech.edu.in",
            "actor_role": "institution_user"
        },
        {
            "event_type": "DOCUMENT_UPLOAD_OCR",
            "payload": {"doc_id": doc_fire.id, "filename": doc_fire.filename, "file_hash": doc_fire.file_hash},
            "actor_email": "system@aicte-india.org",
            "actor_role": "SYSTEM"
        },
        {
            "event_type": "EXTERNAL_ISSUER_QUERY",
            "payload": {"issuer": "KFES_PORTAL", "query_noc": "FS/2024/991", "result_status": "mismatch_detected"},
            "actor_email": "system@aicte-india.org",
            "actor_role": "SYSTEM"
        },
        {
            "event_type": "IMPOSSIBILITY_ENGINE_SCAN",
            "payload": {"conflicts_found": 2, "conflict_types": ["DUAL_EMPLOYMENT", "SHARED_LAND_PARCEL"]},
            "actor_email": "system@aicte-india.org",
            "actor_role": "SYSTEM"
        },
        {
            "event_type": "FORENSIC_RADAR_SCAN",
            "payload": {"photo_match": True, "reused_from_inst": "Royal College of Engineering", "similarity": 98.4},
            "actor_email": "system@aicte-india.org",
            "actor_role": "SYSTEM"
        },
        {
            "event_type": "REGULATION_RULES_EVALUATED",
            "payload": {"rules_evaluated": 4, "passed": 1, "failed": 3, "handbook": "APH 2025-26"},
            "actor_email": "system@aicte-india.org",
            "actor_role": "SYSTEM"
        },
        {
            "event_type": "OFFICER_ACTION_RECORDED",
            "payload": {"rule_id": "RULE_FACULTY_STUDENT_RATIO", "action": "CLARIFICATION_ISSUED", "officer": "Dr. Sunita Deshmukh"},
            "actor_email": "scrutiny.officer@aicte-india.org",
            "actor_role": "scrutiny_officer"
        }
    ]

    for ev in audit_events:
        AuditChainService.append_receipt(
            db=db,
            event_type=ev["event_type"],
            payload=ev["payload"],
            actor_email=ev["actor_email"],
            actor_role=ev["actor_role"],
            application_id=app1.id
        )

    print("PRAMAAN-X Database seeding completed successfully with 7 chained audit receipts!")
    db.close()

if __name__ == "__main__":
    seed_database()
