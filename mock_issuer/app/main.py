"""
PRAMAAN-X Mock Authoritative Issuer Gateway Service:
Simulates external statutory issuer registries:
- State Fire & Emergency Services Portal
- State Revenue & Land Records (Bhoomi / Mahabhulekh)
- State Technical University Affiliation Gateway
- Central Board of Direct Taxes (CBDT) TRACES Form 16 / TDS Gateway
"""
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(
    title="PRAMAAN-X Mock Issuer Gateway",
    version="1.0.0",
    description="Simulated authoritative government issuer verification endpoints for AICTE scrutiny."
)

start_time = datetime.now(timezone.utc)

class FireNocQuery(BaseModel):
    noc_number: str
    institution_name: Optional[str] = None
    state: Optional[str] = "Karnataka"
    expiry_date: Optional[str] = None

class LandRecordQuery(BaseModel):
    survey_no: str
    village: Optional[str] = "Devanahalli"
    claimed_acres: Optional[float] = 5.0
    trust_name: Optional[str] = None

class AffiliationQuery(BaseModel):
    aicte_id: str
    institution_name: Optional[str] = None
    year: Optional[str] = "2025-26"

class TaxRecordQuery(BaseModel):
    pan_masked: str
    faculty_name: Optional[str] = None
    institution_name: Optional[str] = None

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint for container orchestrators and monitoring."""
    uptime_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
    return {
        "status": "HEALTHY",
        "service": "mock-issuer-service",
        "uptime_seconds": round(uptime_seconds, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gateways_operational": {
            "fire_services_portal": True,
            "state_land_registry_bhoomi": True,
            "university_affiliation_portal": True,
            "cbdt_traces_gateway": True
        }
    }

@app.post("/api/v1/fire-noc/verify")
def verify_fire_noc(query: FireNocQuery):
    noc = query.noc_number.strip().upper()
    
    if "EXPIRED" in noc or noc == "FS/2023/8812":
        return {
            "issuer_name": "State Fire & Emergency Services Portal",
            "issuer_code": "KFES_PORTAL",
            "status": "expired",
            "latency_ms": 130,
            "authoritative_record": {
                "noc_number": noc,
                "registered_entity": query.institution_name,
                "expiry_date": "2024-01-09",
                "status": "LAPSED"
            },
            "discrepancies": [
                {
                    "field": "expiry_date",
                    "claimed": query.expiry_date,
                    "issuer_value": "2024-01-09",
                    "issue": "NOC lapsed on 2024-01-09 without renewal."
                }
            ]
        }
    elif "MISMATCH" in noc or noc == "FS/2024/991":
        return {
            "issuer_name": "State Fire & Emergency Services Portal",
            "issuer_code": "KFES_PORTAL",
            "status": "mismatch_detected",
            "latency_ms": 110,
            "authoritative_record": {
                "noc_number": noc,
                "registered_entity": "Apex Commercial Shopping Mall",
                "occupancy_type": "Commercial - Mercantile",
                "status": "VALID_COMMERCIAL"
            },
            "discrepancies": [
                {
                    "field": "registered_entity",
                    "claimed": query.institution_name,
                    "issuer_value": "Apex Commercial Shopping Mall",
                    "issue": "Registered to commercial shopping complex, not an educational institution."
                }
            ]
        }
    else:
        return {
            "issuer_name": "State Fire & Emergency Services Portal",
            "issuer_code": "KFES_PORTAL",
            "status": "verified",
            "latency_ms": 95,
            "authoritative_record": {
                "noc_number": noc,
                "registered_entity": query.institution_name,
                "occupancy_type": "Educational (Group B)",
                "expiry_date": "2027-05-14",
                "status": "VALID_ACTIVE"
            },
            "discrepancies": []
        }

@app.post("/api/v1/land-records/verify")
def verify_land_records(query: LandRecordQuery):
    if "42/1" in query.survey_no:
        return {
            "issuer_name": "State Revenue Department Land Registry (Bhoomi)",
            "issuer_code": "REV_BHOOMI_API",
            "status": "manual_review_required",
            "latency_ms": 175,
            "authoritative_record": {
                "survey_no": query.survey_no,
                "village": query.village,
                "extent_acres": 6.2,
                "encumbrance_status": "LITIGATION_PENDING",
                "registered_title_holder": "Apex Vidya Foundation & Joint Claimants"
            },
            "discrepancies": [
                {
                    "field": "encumbrance_status",
                    "claimed": "CLEAR_TITLE",
                    "issuer_value": "LITIGATION_PENDING",
                    "issue": "Caveat petition and multiple claimants logged on state revenue records."
                }
            ]
        }
    return {
        "issuer_name": "State Revenue Department Land Registry (Bhoomi)",
        "issuer_code": "REV_BHOOMI_API",
        "status": "verified",
        "latency_ms": 105,
        "authoritative_record": {
            "survey_no": query.survey_no,
            "village": query.village,
            "extent_acres": query.claimed_acres,
            "encumbrance_status": "CLEAR_TITLE_NIL_ENCUMBRANCE",
            "registered_title_holder": query.trust_name or "Educational Trust"
        },
        "discrepancies": []
    }

@app.post("/api/v1/affiliation/verify")
def verify_affiliation(query: AffiliationQuery):
    return {
        "issuer_name": "State Examining University Affiliation Cell",
        "issuer_code": "UNIV_AFFILIATION_PORTAL",
        "status": "verified",
        "latency_ms": 80,
        "authoritative_record": {
            "aicte_id": query.aicte_id,
            "institution_name": query.institution_name,
            "affiliation_period": query.year,
            "affiliation_status": "ACTIVE_AFFILIATION"
        },
        "discrepancies": []
    }

@app.post("/api/v1/tax-records/verify")
def verify_tax_record(query: TaxRecordQuery):
    if "89C" in query.pan_masked:
        return {
            "issuer_name": "Central Board of Direct Taxes (CBDT) TRACES Gateway",
            "issuer_code": "CBDT_TRACES_MOCK",
            "status": "mismatch_detected",
            "latency_ms": 160,
            "authoritative_record": {
                "pan_masked": query.pan_masked,
                "active_employers": [
                    {"name": "Apex Institute of Technology", "tan": "BLRA99182A"},
                    {"name": "Royal College of Engineering", "tan": "MYSR28191B"}
                ]
            },
            "discrepancies": [
                {
                    "field": "active_employers",
                    "issue": "Simultaneous Section 192 (Regular Salary) TDS by two distinct technical colleges."
                }
            ]
        }
    return {
        "issuer_name": "Central Board of Direct Taxes (CBDT) TRACES Gateway",
        "issuer_code": "CBDT_TRACES_MOCK",
        "status": "verified",
        "latency_ms": 90,
        "authoritative_record": {
            "pan_masked": query.pan_masked,
            "active_employers": [{"name": query.institution_name or "Technical College"}]
        },
        "discrepancies": []
    }
