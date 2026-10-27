"""
PRAMAAN-X Synthetic Data Generator (Prompt 2.1):
Generates realistic technical education regulatory dossiers:
- Sampled real public technical institutions across Indian states (AICTE / data.gov.in)
- 15-60 faculty members per college with Indian names, qualifications, masked PAN/Aadhaar
- Official PDFs with ReportLab (Affidavit, NOC, Accreditation, Fire NOC, Land Deed)
- Embedded QR codes linking verification URLs
- 30% scan-like degradation (Augraphy dirty rollers, blur, skew, photocopy noise)
- Controlled defect planting logged into ground_truth.csv
"""
import os
import sys
import csv
import json
import random
import argparse
from datetime import datetime, timedelta, timezone
from faker import Faker

from synthetic_generator.defects import GroundTruthLogger
from synthetic_generator.document_generator import (
    generate_affidavit_pdf,
    generate_noc_pdf,
    generate_accreditation_certificate_pdf,
    generate_fire_safety_certificate_pdf,
    generate_land_ownership_pdf
)
from synthetic_generator.augmentations import degrade_pdf_document

DEFAULT_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "public_institutions_sample.csv")

def parse_args():
    parser = argparse.ArgumentParser(description="PRAMAAN-X Synthetic Dataset & Defect Generator")
    parser.add_argument("--institutions", type=int, default=10, help="Number of institutions to generate (e.g. 10, 50, 100, 300)")
    parser.add_argument("--defect-rate", type=float, default=0.2, help="Probability of planting defects in documents/profiles (default: 0.2)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--institutions-csv", type=str, default=DEFAULT_CSV_PATH, help="Path to base institutions CSV")
    parser.add_argument("--output-dir", type=str, default="generated_data", help="Output directory for generated PDFs and metadata")
    return parser.parse_args()

def load_base_institutions(csv_path: str, count: int, fake: Faker) -> list:
    """Loads base institution names/states from CSV and supplements with Faker if count exceeds CSV rows."""
    base_list = []
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                base_list.append(row)

    institutions = []
    for i in range(count):
        if i < len(base_list):
            item = base_list[i]
            name = item["name"]
            state = item["state"]
            district = item["district"]
            lat = float(item["latitude"])
            lon = float(item["longitude"])
            progs = item["programmes"].split(";")
            aicte_id = item["aicte_id"]
        else:
            state = fake.random_element(["Karnataka", "Maharashtra", "Tamil Nadu", "Gujarat", "Delhi", "Uttar Pradesh", "Telangana", "Kerala", "West Bengal", "Rajasthan"])
            district = fake.city()
            prefixes = [
                "B.R. Ambedkar", "Sardar Vallabhbhai Patel", "Acharya", "Swami Vivekananda",
                "Rajiv Gandhi", "K.L.N.", "Dr. A.P.J. Abdul Kalam", "Rabindranath Tagore",
                "Aryabhata", "Sir C.V. Raman", "Netaji Subhas", "National", "Imperial", "Global", "Heritage"
            ]
            types = [
                "Institute of Technology & Engineering", "College of Engineering & Technology",
                "Institute of Technical Studies", "Technological Institute", "Engineering College",
                "Institute of Engineering & Research"
            ]
            idx_offset = i - len(base_list)
            pfx = prefixes[idx_offset % len(prefixes)]
            typ = types[(idx_offset // len(prefixes)) % len(types)]
            name = f"{pfx} {district} {typ}"
            lat = round(random.uniform(8.0, 30.0), 4)
            lon = round(random.uniform(72.0, 88.0), 4)
            progs = ["Engineering & Technology", "Management"]
            aicte_id = f"1-{random.randint(100000000, 999999999)}"

        intake = random.choice([300, 360, 420, 480, 600, 720])
        # Standard norm is ~10.5 to 15 sq.m per student
        built_up_area = round(intake * random.uniform(18.0, 26.0), 1)
        land_area = round(random.uniform(5.0, 12.5), 1)
        trust_name = f"Shri {fake.last_name()} Educational & Charitable Trust"

        institutions.append({
            "id": f"INST_{i+1:03d}",
            "aicte_id": aicte_id,
            "name": name,
            "state": state,
            "district": district,
            "latitude": lat,
            "longitude": lon,
            "programmes": progs,
            "approved_intake": intake,
            "built_up_area_sqm": built_up_area,
            "land_area_acres": land_area,
            "trust_name": trust_name,
            "survey_numbers": f"Sy. No. {random.randint(20, 150)}/{random.randint(1, 5)}, Village {fake.first_name()}pura",
            "establishment_year": random.randint(1985, 2018)
        })

    return institutions

def generate_faculty_roster(inst: dict, fake: Faker, count: int) -> list:
    """Generates 15-60 faculty members complying with cadre hierarchy."""
    roster = []
    designations = (
        ["Professor & Head", "Professor"] * 2 +
        ["Associate Professor"] * 6 +
        ["Assistant Professor"] * 20
    )
    
    qualifications = {
        "Professor": ["Ph.D. IIT Delhi", "Ph.D. IISc Bengaluru", "Ph.D. IIT Bombay", "Ph.D. State Tech University"],
        "Associate Professor": ["Ph.D. NIT Surathkal", "Ph.D. Anna University", "Ph.D. VTU", "M.Tech Gold Medalist"],
        "Assistant Professor": ["M.Tech Computer Science", "M.Tech Electronics", "M.Tech Thermal Engineering", "M.Tech AI & Data"]
    }

    start_date = datetime(2015, 1, 1)

    for idx in range(count):
        desig = designations[idx % len(designations)]
        clean_desig = "Professor" if "Professor &" in desig or desig == "Professor" else ("Associate Professor" if "Associate" in desig else "Assistant Professor")
        qual = random.choice(qualifications[clean_desig])
        
        # PAN format: 5 letters, 4 digits, 1 letter. Mask middle 4 chars
        pan_prefix = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
        pan_num = f"{random.randint(1000, 9999)}"
        pan_suffix = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        pan_raw = f"{pan_prefix}{pan_num}{pan_suffix}"
        pan_masked = f"{pan_raw[:2]}****{pan_raw[-2:]}"
        
        join_dt = start_date + timedelta(days=random.randint(0, 3200))

        roster.append({
            "faculty_id": f"FAC_{inst['id']}_{idx+1:03d}",
            "name": f"Dr. {fake.name()}" if "Ph.D." in qual else f"Prof. {fake.name()}",
            "pan_raw": pan_raw,
            "pan_masked": pan_masked,
            "aadhaar_masked": f"XXXX-XXXX-{random.randint(1000, 9999)}",
            "designation": desig,
            "qualification": qual,
            "joining_date": join_dt.strftime("%Y-%m-%d"),
            "employment_type": "Full-Time Regular"
        })

    return roster

def main():
    args = parse_args()
    print("=" * 70)
    print("PRAMAAN-X Synthetic Regulatory Dataset Generator (Prompt 2.1)")
    print(f"Target Institutions: {args.institutions} | Defect Rate: {args.defect_rate*100:.1f}% | Seed: {args.seed}")
    print("=" * 70)

    # Set seeds
    random.seed(args.seed)
    fake = Faker("en_IN")
    Faker.seed(args.seed)

    # Prepare directories
    out_dir = args.output_dir
    os.makedirs(out_dir, exist_ok=True)
    docs_dir = os.path.join(out_dir, "documents")
    os.makedirs(docs_dir, exist_ok=True)

    ground_truth_path = os.path.join(out_dir, "ground_truth.csv")
    gt_logger = GroundTruthLogger(ground_truth_path)

    # 1. Load Base Institutions
    institutions = load_base_institutions(args.institutions_csv, args.institutions, fake)
    all_faculty = []
    
    # Track cross-institution shared items for intentional collision defects
    shared_faculty_pool = []
    all_documents_meta = []

    print(f"Loaded {len(institutions)} institutions. Generating faculty & compliance dossiers...")

    for inst_idx, inst in enumerate(institutions):
        inst_id = inst["id"]
        inst_name = inst["name"]
        inst_dir = os.path.join(docs_dir, inst_id)
        os.makedirs(inst_dir, exist_ok=True)

        # Faculty Roster (15 to 60 members)
        fac_count = random.randint(18, 45)
        roster = generate_faculty_roster(inst, fake, fac_count)

        # Defect 6: Faculty Duplicate Across Institutions (Ghost Faculty)
        if random.random() < args.defect_rate and shared_faculty_pool:
            borrowed_faculty = random.choice(shared_faculty_pool)
            duplicate_entry = dict(borrowed_faculty)
            duplicate_entry["faculty_id"] = f"FAC_{inst_id}_GHOST"
            roster.insert(0, duplicate_entry)
            
            gt_logger.log_defect(
                institution_id=inst_id,
                institution_name=inst_name,
                document_id=f"ROSTER_{inst_id}",
                document_type="Faculty Roster",
                defect_type="faculty_duplicate_across_institutions",
                details=(
                    f"Faculty member '{duplicate_entry['name']}' (PAN: {duplicate_entry['pan_masked']}) "
                    f"is concurrently claimed as full-time regular faculty by both {duplicate_entry['original_inst_name']} and {inst_name}."
                ),
                severity="CRITICAL",
                expected_regulatory_flag="DUAL_EMPLOYMENT_GHOST_FACULTY"
            )
        else:
            # Add top professor to shared pool for potential future collision
            if roster:
                top_prof = dict(roster[0])
                top_prof["original_inst_name"] = inst_name
                top_prof["original_inst_id"] = inst_id
                shared_faculty_pool.append(top_prof)

        all_faculty.extend(roster)

        # Defect 7: Area Too Small for Intake (Physical Density Impossibility)
        area_defect_planted = False
        if random.random() < (args.defect_rate * 0.7):
            original_area = inst["built_up_area_sqm"]
            # Squeeze area to below 8 sqm/student
            collapsed_area = round(inst["approved_intake"] * 6.5, 1)
            inst["built_up_area_sqm"] = collapsed_area
            area_defect_planted = True
            
            gt_logger.log_defect(
                institution_id=inst_id,
                institution_name=inst_name,
                document_id=f"PROFILE_{inst_id}",
                document_type="Institutional Profile",
                defect_type="area_too_small_for_intake",
                details=(
                    f"Reported carpet area ({collapsed_area} sqm) is physically incapable of holding sanctioned intake "
                    f"({inst['approved_intake']} students/year). Minimum AICTE area norm requires 10.5 sqm/student."
                ),
                severity="CRITICAL",
                expected_regulatory_flag="PHYSICAL_DENSITY_IMPOSSIBILITY"
            )

        # Generate 5 Official PDFs per institution
        docs_to_generate = [
            ("Affidavit", generate_affidavit_pdf, f"AFF_{inst_id}.pdf"),
            ("NOC", generate_noc_pdf, f"NOC_{inst_id}.pdf"),
            ("Accreditation", generate_accreditation_certificate_pdf, f"NBA_{inst_id}.pdf"),
            ("Fire Safety Certificate", generate_fire_safety_certificate_pdf, f"FIRE_{inst_id}.pdf"),
            ("Land Title Deed", generate_land_ownership_pdf, f"LAND_{inst_id}.pdf"),
        ]

        for doc_name, doc_func, doc_filename in docs_to_generate:
            doc_path = os.path.join(inst_dir, doc_filename)
            doc_id = f"DOC_{inst_id}_{doc_name[:4].upper()}"

            # Base document parameters
            current_yr = 2025
            issue_date = f"{current_yr - random.randint(1, 3)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
            valid_date = f"{current_yr + random.randint(1, 2)}-06-30"
            ref_no = f"{doc_name[:3].upper()}/{current_yr}/{random.randint(10000, 99999)}"

            doc_data = {
                "reference_number": ref_no,
                "institution_name": inst_name,
                "issue_date": issue_date,
                "validity_date": valid_date,
                "trust_name": inst["trust_name"],
                "built_up_area_sqm": inst["built_up_area_sqm"],
                "land_area_acres": inst["land_area_acres"],
                "survey_number": inst["survey_numbers"],
                "signatory_name": f"Dr. {fake.name()}",
                "omit_signature": False,
                "qr_verification_url": None
            }

            # -------------------------------------------------------------
            # Plant Specific Document Defects
            # -------------------------------------------------------------
            plant_this_defect = random.random() < args.defect_rate

            if plant_this_defect:
                defect_choice = random.choice([
                    "expired_document",
                    "missing_signature_field",
                    "wrong_institution_name",
                    "mismatched_reference_number",
                    "edited_amount",
                    "date_before_issuer_existed"
                ])

                if defect_choice == "expired_document":
                    # Expired before academic year 2025-26 cutoff
                    doc_data["validity_date"] = "2024-03-31"
                    gt_logger.log_defect(
                        institution_id=inst_id,
                        institution_name=inst_name,
                        document_id=doc_id,
                        document_type=doc_name,
                        defect_type="expired_document",
                        details=f"Document certificate validity expired on 2024-03-31 prior to academic session cutoff.",
                        severity="CRITICAL",
                        expected_regulatory_flag="CERTIFICATE_EXPIRED"
                    )

                elif defect_choice == "missing_signature_field":
                    doc_data["omit_signature"] = True
                    gt_logger.log_defect(
                        institution_id=inst_id,
                        institution_name=inst_name,
                        document_id=doc_id,
                        document_type=doc_name,
                        defect_type="missing_signature_field",
                        details=f"Mandatory authorizing seal, signature line, and notary attestation omitted.",
                        severity="WARNING",
                        expected_regulatory_flag="MISSING_SIGNATURE_FIELD"
                    )

                elif defect_choice == "wrong_institution_name":
                    tampered_name = f"{fake.city()} Shopping Mall & Commercial Complex"
                    doc_data["institution_name"] = tampered_name
                    gt_logger.log_defect(
                        institution_id=inst_id,
                        institution_name=inst_name,
                        document_id=doc_id,
                        document_type=doc_name,
                        defect_type="wrong_institution_name",
                        details=f"Document certificate issued to '{tampered_name}', completely unrelated to applicant college.",
                        severity="CRITICAL",
                        expected_regulatory_flag="ENTITY_NAME_MISMATCH"
                    )

                elif defect_choice == "mismatched_reference_number":
                    doc_data["qr_verification_url"] = f"https://aicte-india.org/verify?ref=TAMPERED_REF_99999&type={doc_name}"
                    gt_logger.log_defect(
                        institution_id=inst_id,
                        institution_name=inst_name,
                        document_id=doc_id,
                        document_type=doc_name,
                        defect_type="mismatched_reference_number",
                        details=f"Embedded QR verification URL encodes reference 'TAMPERED_REF_99999', mismatching header '{ref_no}'.",
                        severity="CRITICAL",
                        expected_regulatory_flag="MISMATCHED_REFERENCE_NUMBER"
                    )

                elif defect_choice == "edited_amount":
                    if doc_name == "Land Title Deed":
                        doc_data["lease_duration_years"] = 15  # Violates 30-year norm!
                        gt_logger.log_defect(
                            institution_id=inst_id,
                            institution_name=inst_name,
                            document_id=doc_id,
                            document_type=doc_name,
                            defect_type="edited_amount",
                            details="Registered leasehold duration is 15 years, violating AICTE statutory 30-year requirement.",
                            severity="CRITICAL",
                            expected_regulatory_flag="LEASE_DURATION_DEFICIENCY"
                        )
                    else:
                        doc_data["built_up_area_sqm"] = 3500.0
                        gt_logger.log_defect(
                            institution_id=inst_id,
                            institution_name=inst_name,
                            document_id=doc_id,
                            document_type=doc_name,
                            defect_type="edited_amount",
                            details="Reported built-up area statement modified to 3,500 sqm, inconsistent with municipal approvals.",
                            severity="CRITICAL",
                            expected_regulatory_flag="AREA_INCONSISTENCY"
                        )

                elif defect_choice == "date_before_issuer_existed":
                    doc_data["issue_date"] = "1972-04-12"
                    gt_logger.log_defect(
                        institution_id=inst_id,
                        institution_name=inst_name,
                        document_id=doc_id,
                        document_type=doc_name,
                        defect_type="date_before_issuer_existed",
                        details=f"Document issue date (1972) predates the establishment of the issuing state agency and college.",
                        severity="CRITICAL",
                        expected_regulatory_flag="ANACHRONISTIC_ISSUE_DATE"
                    )

            is_hard_case = False
            hard_case_type = None

            if not plant_this_defect:
                # Clean documents: partition into clean controls and hard cases (NOT defects!)
                hard_roll = random.random()
                if hard_roll < 0.15:
                    # Hard case: unusual date format on a completely valid certificate
                    is_hard_case = True
                    fmt_style = random.choice(["dots", "slashes", "ordinal", "tenure"])
                    if fmt_style == "dots":
                        doc_data["validity_date"] = "31.03.2027"
                        hard_case_type = "unusual_date_format_dots"
                    elif fmt_style == "slashes":
                        doc_data["validity_date"] = "30/06/2027"
                        hard_case_type = "unusual_date_format_slashes"
                    elif fmt_style == "ordinal":
                        doc_data["validity_date"] = "31st March 2027"
                        hard_case_type = "unusual_date_format_ordinal"
                    elif fmt_style == "tenure":
                        doc_data["validity_date"] = "valid for 3 years from issue"
                        hard_case_type = "unusual_date_format_tenure_phrase"
                elif hard_roll < 0.30:
                    # Hard case: blurred / photocopy degraded scan of authentic certificate
                    is_hard_case = True
                    hard_case_type = "blurred_degraded_clean_scan"

            # Generate original PDF
            doc_func(doc_path, doc_data)

            # Apply Scan Degradation (Augraphy / Skew / Dirty Rollers / Blur)
            should_degrade = (hard_case_type == "blurred_degraded_clean_scan") or (random.random() < 0.25)
            if should_degrade:
                degraded_temp = os.path.join(inst_dir, f"degraded_{doc_filename}")
                success = degrade_pdf_document(doc_path, degraded_temp)
                if success and os.path.exists(degraded_temp):
                    os.replace(degraded_temp, doc_path)

            all_documents_meta.append({
                "institution_id": inst_id,
                "document_id": doc_id,
                "document_type": doc_name,
                "filename": doc_filename,
                "file_path": doc_path,
                "is_scan_degraded": should_degrade,
                "is_hard_case": is_hard_case,
                "hard_case_type": hard_case_type,
                "is_clean_control": (not plant_this_defect and not is_hard_case),
                "is_planted_defect": plant_this_defect,
                "reference_number": doc_data["reference_number"],
                "validity_date": doc_data["validity_date"],
                "issue_date": doc_data.get("issue_date")
            })

    # Save summary metadata JSONs
    with open(os.path.join(out_dir, "institutions.json"), "w", encoding="utf-8") as f:
        json.dump(institutions, f, indent=2)

    with open(os.path.join(out_dir, "faculty.json"), "w", encoding="utf-8") as f:
        json.dump(all_faculty, f, indent=2)

    with open(os.path.join(out_dir, "documents_catalog.json"), "w", encoding="utf-8") as f:
        json.dump(all_documents_meta, f, indent=2)

    summary = gt_logger.get_summary()

    print("\n" + "=" * 70)
    print("SYNTHETIC DATA GENERATION COMPLETE!")
    print(f"Total Institutions Generated: {len(institutions)}")
    print(f"Total Faculty Profiles:      {len(all_faculty)}")
    print(f"Total Compliance PDFs:       {len(all_documents_meta)}")
    print(f"Total Planted Defects:       {summary['total_defects_planted']}")
    print("Breakdown by Defect Type:")
    for d_type, cnt in summary["breakdown_by_defect_type"].items():
        print(f"  • {d_type:35s}: {cnt}")
    print(f"\nGround Truth Ledger: {ground_truth_path}")
    print("=" * 70)

if __name__ == "__main__":
    main()
