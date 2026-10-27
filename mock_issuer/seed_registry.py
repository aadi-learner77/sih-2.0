"""
PRAMAAN-X Mock Issuer Registry Seeding Script
Reads synthetic institution profiles, documents catalog, and ground_truth.csv.
Generates an authoritative registry JSON (mock_issuer/data/registry.json) for:
- State Fire & Emergency Services Portal (fire)
- State Examining University Affiliation Body (affiliation)
- NBA-like Accreditation Body (accreditation)
- State Revenue & Land Records Office / Bhoomi (land)

Deliberately alters or omits records according to planted defects in ground_truth.csv:
- CERTIFICATE_EXPIRED / expired_document: validity date set in the past (< 2024-03-31)
- ENTITY_NAME_MISMATCH / wrong_institution_name: entity registered to a commercial mall / third party
- MISSING_DOCUMENT: left completely out of registry (returns not_found)
- SHARED_LAND_PARCEL / LITIGATION: encumbrance status set to LITIGATION_PENDING with acreage diff
"""
import os
import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_registry")

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_REGISTRY_PATH = DATA_DIR / "registry.json"

SYNTHETIC_DATA_DIR = ROOT_DIR / "generated_data"
INSTITUTIONS_FILE = SYNTHETIC_DATA_DIR / "institutions.json"
DOCUMENTS_FILE = SYNTHETIC_DATA_DIR / "documents_catalog.json"
GROUND_TRUTH_FILE = SYNTHETIC_DATA_DIR / "ground_truth.csv"

def load_ground_truth() -> Dict[str, Dict[str, Any]]:
    """Loads ground truth defects keyed by document_id and reference_number."""
    defects = {}
    if not GROUND_TRUTH_FILE.exists():
        logger.warning(f"Ground truth file not found at {GROUND_TRUTH_FILE}, seeding clean baseline.")
        return defects

    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row.get("document_id")
            if doc_id:
                defects[doc_id] = row
    logger.info(f"Loaded {len(defects)} planted defects from ground_truth.csv")
    return defects

def seed_registry() -> Dict[str, Any]:
    """Generates the authoritative multi-authority registry JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load synthetic data or fall back to default benchmark institutions
    institutions = []
    if INSTITUTIONS_FILE.exists():
        with open(INSTITUTIONS_FILE, "r", encoding="utf-8") as f:
            institutions = json.load(f)
    else:
        institutions = [
            {
                "id": "INST_001",
                "aicte_id": "1-109283711",
                "name": "College of Engineering Pune (COEP Technological University)",
                "state": "Maharashtra",
                "district": "Pune",
                "approved_intake": 300,
                "land_area_acres": 10.8,
                "trust_name": "Shri Ben Educational & Charitable Trust",
                "survey_numbers": "Sy. No. 88/1, Village Amritapura"
            },
            {
                "id": "INST_002",
                "aicte_id": "1-209384722",
                "name": "Veermata Jijabai Technological Institute (VJTI)",
                "state": "Maharashtra",
                "district": "Mumbai City",
                "approved_intake": 480,
                "land_area_acres": 7.5,
                "trust_name": "Shri Chahal Educational & Charitable Trust",
                "survey_numbers": "Sy. No. 33/2, Village Nikitapura"
            },
            {
                "id": "INST_003",
                "aicte_id": "1-309485733",
                "name": "BMS College of Engineering",
                "state": "Karnataka",
                "district": "Bengaluru Urban",
                "approved_intake": 420,
                "land_area_acres": 10.3,
                "trust_name": "Shri Lata Educational & Charitable Trust",
                "survey_numbers": "Sy. No. 61/1, Village Hritikpura"
            }
        ]

    # Map institutions by ID
    inst_map = {inst["id"]: inst for inst in institutions}

    # 2. Load documents
    documents = []
    if DOCUMENTS_FILE.exists():
        with open(DOCUMENTS_FILE, "r", encoding="utf-8") as f:
            documents = json.load(f)

    # 3. Load planted defects
    defects = load_ground_truth()

    registry = {
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "description": "PRAMAAN-X Authoritative Government Issuer Database Registry",
        "authorities": {
            "fire": {
                "name": "State Fire & Emergency Services Department",
                "code": "SFES_REGISTRY",
                "records": {}
            },
            "affiliation": {
                "name": "State Technical University Affiliation Gateway",
                "code": "UNIV_AFFILIATION_REGISTRY",
                "records": {}
            },
            "accreditation": {
                "name": "National Board of Accreditation (NBA) Registry",
                "code": "NBA_ACCREDITATION_REGISTRY",
                "records": {}
            },
            "land": {
                "name": "State Revenue Department Land Registry (Bhoomi / Mahabhulekh)",
                "code": "LAND_REVENUE_BHOOMI",
                "records": {}
            }
        }
    }

    fire_records = registry["authorities"]["fire"]["records"]
    affil_records = registry["authorities"]["affiliation"]["records"]
    accr_records = registry["authorities"]["accreditation"]["records"]
    land_records = registry["authorities"]["land"]["records"]

    # 4. Process each document from catalog and seed authorities
    for doc in documents:
        inst_id = doc.get("institution_id")
        inst = inst_map.get(inst_id, {})
        inst_name = inst.get("name", "Unknown Institution")
        doc_type = doc.get("document_type", "")
        ref = doc.get("reference_number", "")
        validity = doc.get("validity_date", "2027-06-30")
        doc_id = doc.get("document_id", "")
        defect = defects.get(doc_id)

        # Check if defect says MISSING_DOCUMENT -> deliberately omit from registry!
        if defect and defect.get("defect_type") == "missing_document":
            logger.info(f"Deliberately omitting {doc_id} ({ref}) from registry: simulates unissued/forged certificate.")
            continue

        if doc_type == "Fire Safety Certificate":
            is_expired = (defect and "expired" in defect.get("defect_type", "")) or validity < "2025-01-01"
            is_mismatch = (defect and "wrong_institution_name" in defect.get("defect_type", ""))
            
            registered_entity = "Phusro Shopping Mall & Commercial Complex" if is_mismatch else inst_name
            occupancy = "Commercial - Mercantile" if is_mismatch else "Educational (Group B)"
            expiry_date = "2024-03-31" if is_expired else validity

            fire_records[ref] = {
                "reference_number": ref,
                "document_id": doc_id,
                "institution_id": inst_id,
                "registered_entity": registered_entity,
                "occupancy_type": occupancy,
                "sanctioned_floors": "G+4",
                "expiry_date": expiry_date,
                "fire_safety_measure_status": "COMPLIANT" if not is_expired else "LAPSED",
                "issuing_division": f"{inst.get('district', 'State')} Fire Command",
                "status": "VALID_ACTIVE" if not is_expired else "EXPIRED"
            }

        elif doc_type in ["NOC", "Affidavit"]:
            is_expired = (defect and "expired" in defect.get("defect_type", ""))
            is_mismatch = (defect and "mismatch" in defect.get("defect_type", ""))

            registered_inst = "Unrelated Commercial Academy" if is_mismatch else inst_name
            sanctioned_intake = (inst.get("approved_intake", 300) - 120) if is_mismatch else inst.get("approved_intake", 300)

            clean_validity = "2027-06-30" if validity <= "2026-10-01" else validity
            affil_records[ref] = {
                "reference_number": ref,
                "document_id": doc_id,
                "institution_id": inst_id,
                "institution_name": registered_inst,
                "aicte_id": inst.get("aicte_id", "1-00000000"),
                "academic_year": "2025-26",
                "affiliation_status": "ACTIVE_AFFILIATION" if not is_expired else "LAPSED_AFFILIATION",
                "approved_intake": sanctioned_intake,
                "approved_programmes": inst.get("programmes", ["Engineering & Technology"]),
                "expiry_date": "2024-03-31" if is_expired else clean_validity,
                "examining_authority": f"{inst.get('state', 'State')} Technological University"
            }

        elif doc_type == "Accreditation":
            is_expired = (defect and "expired" in defect.get("defect_type", "")) or validity < "2025-01-01"
            is_mismatch = (defect and "mismatch" in defect.get("defect_type", ""))

            expiry_date = "2024-03-31" if is_expired else validity
            registered_inst = "Apex Polytechnic Institute" if is_mismatch else inst_name

            accr_records[ref] = {
                "reference_number": ref,
                "document_id": doc_id,
                "institution_id": inst_id,
                "institution_name": registered_inst,
                "tier": "Tier-1 (Washington Accord)",
                "accreditation_score": 768,
                "accredited_programmes": [
                    "Computer Science and Engineering",
                    "Electronics and Communication Engineering",
                    "Mechanical Engineering"
                ],
                "valid_till": expiry_date,
                "expiry_date": expiry_date,
                "nba_file_ref": f"NBA/EVAL/2025/{inst_id}",
                "status": "ACCREDITED" if not is_expired else "ACCREDITATION_LAPSED"
            }

        elif doc_type == "Land Title Deed":
            is_expired = (defect and "expired" in defect.get("defect_type", "")) or validity < "2025-01-01"
            is_mismatch = (defect and "shared_land" in defect.get("defect_type", "")) or ("42/1" in inst.get("survey_numbers", ""))

            expiry_date = "2024-03-31" if is_expired else validity
            recorded_acres = (inst.get("land_area_acres", 10.0) - 3.5) if is_mismatch else inst.get("land_area_acres", 10.0)
            encumbrance = "LITIGATION_PENDING" if is_mismatch else "CLEAR_TITLE_NIL_ENCUMBRANCE"

            land_records[ref] = {
                "reference_number": ref,
                "document_id": doc_id,
                "institution_id": inst_id,
                "survey_no": inst.get("survey_numbers", "Sy. No. 101/A"),
                "village": "Vidyanagar",
                "taluk": inst.get("district", "Urban"),
                "extent_acres": recorded_acres,
                "registered_title_holder": inst.get("trust_name", "Educational Trust"),
                "applicant_institution": inst_name,
                "land_classification": "Non-Agricultural (Educational)",
                "encumbrance_status": encumbrance,
                "lease_tenure_years": 99,
                "expiry_date": expiry_date,
                "status": "VALID_TITLE" if not is_expired else "LEASE_EXPIRED"
            }

    # 5. Add default benchmark entries for standard reference codes used in tests & Evidence Lens
    # Standard Fire NOCs
    fire_records["FIR/2025/98354"] = {
        "reference_number": "FIR/2025/98354",
        "registered_entity": "College of Engineering Pune (COEP Technological University)",
        "occupancy_type": "Educational (Group B)",
        "sanctioned_floors": "G+3",
        "expiry_date": "2027-06-30",
        "fire_safety_measure_status": "COMPLIANT",
        "issuing_division": "Pune Central Fire Division",
        "status": "VALID_ACTIVE"
    }
    fire_records["FIR/2025/89612"] = {
        "reference_number": "FIR/2025/89612",
        "registered_entity": "Phusro Commercial Complex",
        "occupancy_type": "Commercial - Mercantile",
        "sanctioned_floors": "G+2",
        "expiry_date": "2026-12-31",
        "fire_safety_measure_status": "COMPLIANT",
        "issuing_division": "Bokaro Regional Fire Command",
        "status": "VALID_ACTIVE"
    }
    fire_records["FS/2024/991"] = {
        "reference_number": "FS/2024/991",
        "registered_entity": "Apex Commercial Shopping Mall (Not Educational)",
        "occupancy_type": "Commercial - Mercantile",
        "sanctioned_floors": "G+3",
        "expiry_date": "2026-12-31",
        "fire_safety_measure_status": "COMPLIANT",
        "issuing_division": "Bengaluru Central Fire Division",
        "status": "VALID_ACTIVE"
    }
    fire_records["FS/2023/8812"] = {
        "reference_number": "FS/2023/8812",
        "registered_entity": "Apex Institute of Technology & Science",
        "occupancy_type": "Educational (Group B)",
        "sanctioned_floors": "G+3",
        "expiry_date": "2024-01-09",
        "fire_safety_measure_status": "LAPSED",
        "issuing_division": "Bengaluru East Fire Command",
        "status": "EXPIRED"
    }
    fire_records["FS/2024/7741"] = {
        "reference_number": "FS/2024/7741",
        "registered_entity": "Apex Institute of Technology & Science",
        "occupancy_type": "Educational (Group B)",
        "sanctioned_floors": "G+3",
        "expiry_date": "2027-05-14",
        "fire_safety_measure_status": "COMPLIANT",
        "issuing_division": "Bengaluru East Fire Command",
        "status": "VALID_ACTIVE"
    }

    # Standard Affiliation orders
    affil_records["VTU/ACA/2024-25/A-4/1049"] = {
        "reference_number": "VTU/ACA/2024-25/A-4/1049",
        "institution_name": "Apex Institute of Technology & Science",
        "aicte_id": "1-982173491",
        "academic_year": "2025-26",
        "affiliation_status": "ACTIVE_AFFILIATION",
        "approved_intake": 480,
        "approved_programmes": ["Engineering & Technology", "Computer Applications"],
        "expiry_date": "2027-06-30",
        "examining_authority": "Visvesvaraya Technological University"
    }
    affil_records["VTU/ACA/2023-24/LAPSED"] = {
        "reference_number": "VTU/ACA/2023-24/LAPSED",
        "institution_name": "Apex Institute of Technology & Science",
        "aicte_id": "1-982173491",
        "academic_year": "2023-24",
        "affiliation_status": "LAPSED_AFFILIATION",
        "approved_intake": 300,
        "approved_programmes": ["Engineering & Technology"],
        "expiry_date": "2024-05-31",
        "examining_authority": "Visvesvaraya Technological University"
    }

    # Standard Accreditation records
    accr_records["NBA/2024/TIER1/9921"] = {
        "reference_number": "NBA/2024/TIER1/9921",
        "institution_name": "Apex Institute of Technology & Science",
        "tier": "Tier-1 (Washington Accord)",
        "accreditation_score": 745,
        "accredited_programmes": ["Computer Science and Engineering", "Information Science"],
        "valid_till": "2027-06-30",
        "expiry_date": "2027-06-30",
        "nba_file_ref": "NBA/EVAL/2024/BLR-01",
        "status": "ACCREDITED"
    }
    accr_records["NBA/2021/EXPIRED/1102"] = {
        "reference_number": "NBA/2021/EXPIRED/1102",
        "institution_name": "Apex Institute of Technology & Science",
        "tier": "Tier-2",
        "accreditation_score": 620,
        "accredited_programmes": ["Civil Engineering"],
        "valid_till": "2023-06-30",
        "expiry_date": "2023-06-30",
        "nba_file_ref": "NBA/EVAL/2021/BLR-02",
        "status": "ACCREDITATION_LAPSED"
    }

    # Standard Land Deed records
    land_records["LAND/DEED/2021/8821"] = {
        "reference_number": "LAND/DEED/2021/8821",
        "survey_no": "Sy. No. 42/1",
        "village": "Devanahalli",
        "taluk": "Bengaluru North",
        "extent_acres": 6.2,
        "registered_title_holder": "Apex Vidya Foundation & Joint Claimants",
        "applicant_institution": "Apex Institute of Technology & Science",
        "land_classification": "Non-Agricultural (Educational)",
        "encumbrance_status": "LITIGATION_PENDING",
        "lease_tenure_years": 30,
        "expiry_date": "2051-12-31",
        "status": "LITIGATION_LOGGED"
    }
    land_records["LAND/DEED/2020/CLEAR"] = {
        "reference_number": "LAND/DEED/2020/CLEAR",
        "survey_no": "Sy. No. 102/2",
        "village": "Yelahanka",
        "taluk": "Bengaluru North",
        "extent_acres": 12.5,
        "registered_title_holder": "Apex Educational Trust",
        "applicant_institution": "Apex Institute of Technology & Science",
        "land_classification": "Non-Agricultural (Educational)",
        "encumbrance_status": "CLEAR_TITLE_NIL_ENCUMBRANCE",
        "lease_tenure_years": 99,
        "expiry_date": "2119-03-31",
        "status": "VALID_TITLE"
    }

    # Write registry to file
    with open(OUTPUT_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

    total_records = (
        len(fire_records) + len(affil_records) + len(accr_records) + len(land_records)
    )
    logger.info(
        f"Seeded registry successfully at {OUTPUT_REGISTRY_PATH} with {total_records} authoritative records "
        f"({len(fire_records)} fire, {len(affil_records)} affiliation, {len(accr_records)} accreditation, {len(land_records)} land)."
    )
    return registry

if __name__ == "__main__":
    seed_registry()
