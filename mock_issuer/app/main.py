"""
PRAMAAN-X Authoritative Mock Issuer Gateway Service (FastAPI)
Simulates external statutory issuer registries:
1. State Fire & Emergency Services Department (fire)
2. State Technical University Affiliation Body (affiliation)
3. National Board of Accreditation / NBA-like Body (accreditation)
4. State Revenue & Land Records Registry / Bhoomi (land)

Endpoints:
- Unified: GET /verify?ref=...&name=...&authority=...
- Dedicated:
    GET /fire/verify?ref=...&name=...
    GET /affiliation/verify?ref=...&name=...
    GET /accreditation/verify?ref=...&name=...
    GET /land/verify?ref=...&name=...

Response Statuses (Strictly adheres to Prompt 3.1):
- 'verified': Active, matching record
- 'mismatch': Differing parameters (entity name, acres, programme, etc.) with discrepancies list
- 'expired': Lapsed validity certificate
- 'not_found': Unregistered or forged reference number
- 'source_unavailable': HTTP 503 / gateway timeout (randomly triggered by configurable % or flag)

Security & Diagnostics:
- Mandatory X-API-Key header validation
- Latency simulation (configurable jitter)
- Real-time in-memory request logging (/logs)
- Dynamic JSON registry loading from data/registry.json (/registry/reload)
"""
import os
import time
import json
import random
import logging
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Header, HTTPException, Query, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [MOCK-ISSUER] %(message)s")
logger = logging.getLogger("mock_issuer")

app = FastAPI(
    title="PRAMAAN-X Authoritative Mock Issuer Gateway",
    version="2.0.0",
    description="Statutory Government Issuer Verification Service simulating Fire, Affiliation, Accreditation, and Land registries."
)

cors_origins_env = os.getenv("CORS_ORIGINS", "*")
cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
if not cors_origins or "*" in cors_origins:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from Environment
APP_DIR = Path(__file__).resolve().parent
SERVICE_DIR = APP_DIR.parent
REGISTRY_FILE = SERVICE_DIR / "data" / "registry.json"

EXPECTED_API_KEY = os.getenv("ISSUER_API_KEY", "pramaanx-mock-key-2025")
DEFAULT_FAILURE_RATE = float(os.getenv("FAILURE_RATE", "0.0")) # 0.0 by default unless configured or requested
MIN_LATENCY_MS = int(os.getenv("MIN_LATENCY_MS", "60"))
MAX_LATENCY_MS = int(os.getenv("MAX_LATENCY_MS", "180"))

START_TIME = datetime.now(timezone.utc)
REQUEST_AUDIT_LOGS: List[Dict[str, Any]] = []
MAX_AUDIT_LOGS = 500

# Global Registry Storage
registry_cache: Dict[str, Any] = {}

def load_registry() -> Dict[str, Any]:
    """Loads authoritative records from mock_issuer/data/registry.json."""
    global registry_cache
    if not REGISTRY_FILE.exists():
        logger.warning(f"Registry file not found at {REGISTRY_FILE}. Initializing empty registry.")
        registry_cache = {
            "version": "1.0.0",
            "authorities": {
                "fire": {"records": {}},
                "affiliation": {"records": {}},
                "accreditation": {"records": {}},
                "land": {"records": {}}
            }
        }
        return registry_cache

    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            registry_cache = json.load(f)
        total = sum(
            len(a.get("records", {})) 
            for a in registry_cache.get("authorities", {}).values()
        )
        logger.info(f"Loaded registry from {REGISTRY_FILE} with {total} records.")
    except Exception as e:
        logger.error(f"Error reading registry JSON: {e}")
    return registry_cache

# Initial load on module startup
load_registry()

def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
                   authorization: Optional[str] = Header(None, alias="Authorization")) -> str:
    """Validates X-API-Key header or Bearer authorization token."""
    key = x_api_key
    if not key and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() in ["bearer", "token", "apikey"]:
            key = parts[1]
        else:
            key = authorization

    if not key or key != EXPECTED_API_KEY:
        logger.warning(f"Unauthorized API request rejected. Provided key: {key[:4] + '***' if key else 'None'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing or invalid X-API-Key header."
        )
    return key

def simulate_latency_and_failures(override_latency: Optional[int] = None,
                                  simulate_failure: bool = False,
                                  failure_rate: Optional[float] = None) -> int:
    """Applies realistic simulated latency and handles random/forced 503 unavailability."""
    # Check failure rate
    eff_failure_rate = failure_rate if failure_rate is not None else DEFAULT_FAILURE_RATE
    should_fail = simulate_failure or (eff_failure_rate > 0 and random.random() < eff_failure_rate)

    # Compute latency
    if override_latency is not None and override_latency >= 0:
        latency = override_latency
    else:
        latency = random.randint(MIN_LATENCY_MS, MAX_LATENCY_MS)

    # Sleep to simulate network trip
    if latency > 0:
        time.sleep(latency / 1000.0)

    if should_fail:
        logger.warning("Simulated external statutory portal timeout/unavailability (HTTP 503).")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External statutory registry gateway temporarily unreachable (HTTP 503 timeout)."
        )

    return latency

def log_request_audit(request: Request, authority: str, ref: str, name: str, result_status: str, latency_ms: int, http_code: int = 200):
    """Logs verification query to persistent in-memory audit log for security scrutiny."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client_ip": request.client.host if request.client else "127.0.0.1",
        "authority": authority,
        "ref": ref,
        "name": name,
        "result_status": result_status,
        "http_code": http_code,
        "latency_ms": latency_ms
    }
    REQUEST_AUDIT_LOGS.insert(0, entry)
    if len(REQUEST_AUDIT_LOGS) > MAX_AUDIT_LOGS:
        REQUEST_AUDIT_LOGS.pop()
    logger.info(f"[{authority.upper()}] Ref '{ref}' | Query: '{name}' -> Status: '{result_status}' ({latency_ms}ms)")

def auto_detect_authority(ref: str) -> str:
    """Infers authority category from reference number prefix if authority is not explicitly passed."""
    u_ref = ref.upper()
    if u_ref.startswith("FIR") or "FS/" in u_ref or "FIRE" in u_ref:
        return "fire"
    if u_ref.startswith("NOC") or "VTU" in u_ref or "AFF" in u_ref or "UNIV" in u_ref:
        return "affiliation"
    if u_ref.startswith("ACC") or "NBA" in u_ref or "NAAC" in u_ref:
        return "accreditation"
    if u_ref.startswith("LAN") or "REV" in u_ref or "SY." in u_ref or "SURVEY" in u_ref or "DEED" in u_ref:
        return "land"
    return "fire" # default fallback

def check_string_match(claimed: Optional[str], authoritative: Optional[str]) -> bool:
    """Fuzzy entity name comparator to accommodate minor legal suffix variances."""
    if not claimed or not authoritative:
        return False
    c = claimed.lower().strip()
    a = authoritative.lower().strip()
    if c == a:
        return True
    # Strip common suffixes for robust evaluation
    stopwords = ["pvt", "ltd", "trust", "society", "the", "institute", "college", "engineering", "technology"]
    c_tokens = set([w for w in c.replace("(", " ").replace(")", " ").replace(",", " ").split() if w not in stopwords])
    a_tokens = set([w for w in a.replace("(", " ").replace(")", " ").replace(",", " ").split() if w not in stopwords])
    if c_tokens and a_tokens and (c_tokens.issubset(a_tokens) or a_tokens.issubset(c_tokens)):
        return True
    return False

# ==============================================================================
# CORE VERIFICATION LOGIC (Discrepancy detection & status assignment)
# ==============================================================================
def process_verification(
    authority: str,
    ref: str,
    name: str,
    claimed_expiry: Optional[str] = None,
    claimed_acres: Optional[float] = None
) -> Dict[str, Any]:
    """
    Evaluates reference against authoritative JSON registry.
    Returns:
    - 'verified'
    - 'mismatch' (with discrepancies)
    - 'expired'
    - 'not_found'
    """
    clean_ref = ref.strip().upper()
    auth_data = registry_cache.get("authorities", {}).get(authority, {})
    records = auth_data.get("records", {})

    # Case 1: Ref not found in registry (Forged/Bogus certificate)
    if clean_ref not in records:
        return {
            "authority": authority,
            "issuer_name": auth_data.get("name", "Statutory Registry"),
            "issuer_code": auth_data.get("code", "REGISTRY_PORTAL"),
            "status": "not_found",
            "reference_number": ref,
            "queried_name": name,
            "authoritative_record": None,
            "mismatched_fields": [],
            "discrepancies": [
                {
                    "field": "reference_number",
                    "claimed": ref,
                    "issuer_value": None,
                    "issue": f"Reference number '{ref}' not found on official statutory register."
                }
            ],
            "advisory": f"Critical review flag: Reference number '{ref}' does not exist on official government register."
        }

    rec = records[clean_ref]
    discrepancies: List[Dict[str, Any]] = []

    # Check Expiry Date across all document types
    expiry_date_str = rec.get("expiry_date") or rec.get("valid_till")
    is_expired = False
    if expiry_date_str:
        try:
            exp_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            if exp_date < date.today():
                is_expired = True
                discrepancies.append({
                    "field": "expiry_date",
                    "claimed": claimed_expiry or "Active Session",
                    "issuer_value": expiry_date_str,
                    "issue": f"Certificate validity expired on {expiry_date_str} prior to current academic session."
                })
        except ValueError:
            pass

    if is_expired or rec.get("status") in ["EXPIRED", "ACCREDITATION_LAPSED", "LAPSED_AFFILIATION", "LEASE_EXPIRED"]:
        return {
            "authority": authority,
            "issuer_name": auth_data.get("name", "Statutory Registry"),
            "issuer_code": auth_data.get("code", "REGISTRY_PORTAL"),
            "status": "expired",
            "reference_number": ref,
            "queried_name": name,
            "authoritative_record": rec,
            "mismatched_fields": [d["field"] for d in discrepancies],
            "discrepancies": discrepancies,
            "advisory": f"Certificate expired on {expiry_date_str}; institution must produce valid renewal."
        }

    # Authority-specific field comparisons (Detect 'mismatch')
    if authority == "fire":
        reg_entity = rec.get("registered_entity", "")
        if name and not check_string_match(name, reg_entity):
            discrepancies.append({
                "field": "registered_entity",
                "claimed": name,
                "issuer_value": reg_entity,
                "issue": f"Registered entity differs: officially registered to '{reg_entity}'."
            })
        if rec.get("occupancy_type") == "Commercial - Mercantile":
            discrepancies.append({
                "field": "occupancy_type",
                "claimed": "Educational (Group B)",
                "issuer_value": "Commercial - Mercantile",
                "issue": "Property registered for commercial shopping occupancy, not educational."
            })

    elif authority == "affiliation":
        inst_name = rec.get("institution_name", "")
        if name and not check_string_match(name, inst_name):
            discrepancies.append({
                "field": "institution_name",
                "claimed": name,
                "issuer_value": inst_name,
                "issue": f"Affiliation order issued to '{inst_name}', not applicant institution."
            })

    elif authority == "accreditation":
        inst_name = rec.get("institution_name", "")
        if name and not check_string_match(name, inst_name):
            discrepancies.append({
                "field": "institution_name",
                "claimed": name,
                "issuer_value": inst_name,
                "issue": f"Accreditation certificate belongs to '{inst_name}'."
            })

    elif authority == "land":
        if rec.get("encumbrance_status") == "LITIGATION_PENDING":
            discrepancies.append({
                "field": "encumbrance_status",
                "claimed": "CLEAR_TITLE",
                "issuer_value": "LITIGATION_PENDING",
                "issue": "Caveat petition and multiple claimants logged on state revenue records."
            })
        rec_acres = rec.get("extent_acres")
        if claimed_acres is not None and rec_acres is not None:
            if abs(claimed_acres - float(rec_acres)) > 0.5:
                discrepancies.append({
                    "field": "extent_acres",
                    "claimed": claimed_acres,
                    "issuer_value": rec_acres,
                    "issue": f"Claimed land extent ({claimed_acres} Acres) exceeds revenue record ({rec_acres} Acres)."
                })

    # Determine final status
    if discrepancies:
        return {
            "authority": authority,
            "issuer_name": auth_data.get("name", "Statutory Registry"),
            "issuer_code": auth_data.get("code", "REGISTRY_PORTAL"),
            "status": "mismatch",
            "reference_number": ref,
            "queried_name": name,
            "authoritative_record": rec,
            "mismatched_fields": [d["field"] for d in discrepancies],
            "discrepancies": discrepancies,
            "advisory": "Discrepancy detected between applicant declaration and statutory government portal."
        }

    # Case 4: Clean Verified
    return {
        "authority": authority,
        "issuer_name": auth_data.get("name", "Statutory Registry"),
        "issuer_code": auth_data.get("code", "REGISTRY_PORTAL"),
        "status": "verified",
        "reference_number": ref,
        "queried_name": name,
        "authoritative_record": rec,
        "mismatched_fields": [],
        "discrepancies": [],
        "advisory": "All parameters authenticated against authoritative state government registry."
    }

# ==============================================================================
# FASTAPI ENDPOINTS
# ==============================================================================

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint exposing operational metrics and record counts."""
    uptime_seconds = (datetime.now(timezone.utc) - START_TIME).total_seconds()
    counts = {
        k: len(v.get("records", {})) 
        for k, v in registry_cache.get("authorities", {}).items()
    }
    return {
        "status": "HEALTHY",
        "service": "pramaanx-mock-issuer",
        "uptime_seconds": round(uptime_seconds, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_registry_records": sum(counts.values()),
        "record_counts_by_authority": counts,
        "security": {
            "api_key_required": True,
            "header": "X-API-Key"
        },
        "config": {
            "min_latency_ms": MIN_LATENCY_MS,
            "max_latency_ms": MAX_LATENCY_MS,
            "default_failure_rate": DEFAULT_FAILURE_RATE
        }
    }

@app.get("/verify")
def unified_verify(
    request: Request,
    ref: str = Query(..., description="Document / Certificate reference number"),
    name: str = Query(..., description="Applicant institution / entity name"),
    authority: Optional[str] = Query(None, description="Authority: 'fire', 'affiliation', 'accreditation', 'land'"),
    claimed_expiry: Optional[str] = Query(None, description="Claimed validity date (YYYY-MM-DD)"),
    claimed_acres: Optional[float] = Query(None, description="Claimed land area in acres"),
    latency_ms: Optional[int] = Query(None, description="Override latency simulation in ms"),
    simulate_failure: bool = Query(False, description="Simulate HTTP 503 gateway timeout"),
    failure_rate: Optional[float] = Query(None, description="Override failure rate probability"),
    api_key: str = Depends(verify_api_key)
):
    """
    Unified Verification Endpoint (Prompt 3.1)
    Exposes GET /verify?ref=...&name=...&authority=...
    Checks API-key, simulates latency & potential gateway 503 failures, and logs request.
    """
    # 1. Identify Authority
    auth_category = authority.lower().strip() if authority else auto_detect_authority(ref)
    if auth_category not in ["fire", "affiliation", "accreditation", "land"]:
        auth_category = "fire"

    # 2. Simulate Latency & Failures
    eff_latency = simulate_latency_and_failures(latency_ms, simulate_failure, failure_rate)

    # 3. Perform Registry Query
    result = process_verification(auth_category, ref, name, claimed_expiry, claimed_acres)
    result["latency_ms"] = eff_latency
    result["timestamp"] = datetime.now(timezone.utc).isoformat()

    # 4. Log Request
    log_request_audit(request, auth_category, ref, name, result["status"], eff_latency, 200)

    return result

# Dedicated Per-Authority Endpoints
@app.get("/fire/verify")
def verify_fire_department(
    request: Request,
    ref: str = Query(..., description="NOC reference number"),
    name: str = Query(..., description="Institution name"),
    claimed_expiry: Optional[str] = Query(None),
    latency_ms: Optional[int] = Query(None),
    simulate_failure: bool = Query(False),
    failure_rate: Optional[float] = Query(None),
    api_key: str = Depends(verify_api_key)
):
    """Verify Fire Safety Certificate / NOC with State Fire Department."""
    eff_latency = simulate_latency_and_failures(latency_ms, simulate_failure, failure_rate)
    result = process_verification("fire", ref, name, claimed_expiry)
    result["latency_ms"] = eff_latency
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    log_request_audit(request, "fire", ref, name, result["status"], eff_latency, 200)
    return result

@app.get("/affiliation/verify")
def verify_university_affiliation(
    request: Request,
    ref: str = Query(..., description="Affiliation order reference"),
    name: str = Query(..., description="Institution name"),
    claimed_expiry: Optional[str] = Query(None),
    latency_ms: Optional[int] = Query(None),
    simulate_failure: bool = Query(False),
    failure_rate: Optional[float] = Query(None),
    api_key: str = Depends(verify_api_key)
):
    """Verify University Affiliation Order with State Technical University."""
    eff_latency = simulate_latency_and_failures(latency_ms, simulate_failure, failure_rate)
    result = process_verification("affiliation", ref, name, claimed_expiry)
    result["latency_ms"] = eff_latency
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    log_request_audit(request, "affiliation", ref, name, result["status"], eff_latency, 200)
    return result

@app.get("/accreditation/verify")
def verify_nba_accreditation(
    request: Request,
    ref: str = Query(..., description="Accreditation certificate reference"),
    name: str = Query(..., description="Institution name"),
    claimed_expiry: Optional[str] = Query(None),
    latency_ms: Optional[int] = Query(None),
    simulate_failure: bool = Query(False),
    failure_rate: Optional[float] = Query(None),
    api_key: str = Depends(verify_api_key)
):
    """Verify Accreditation Status with National Board of Accreditation (NBA)."""
    eff_latency = simulate_latency_and_failures(latency_ms, simulate_failure, failure_rate)
    result = process_verification("accreditation", ref, name, claimed_expiry)
    result["latency_ms"] = eff_latency
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    log_request_audit(request, "accreditation", ref, name, result["status"], eff_latency, 200)
    return result

@app.get("/land/verify")
def verify_land_records(
    request: Request,
    ref: str = Query(..., description="Land Title Deed / Survey number"),
    name: str = Query(..., description="Institution / Trust name"),
    claimed_acres: Optional[float] = Query(None),
    claimed_expiry: Optional[str] = Query(None),
    latency_ms: Optional[int] = Query(None),
    simulate_failure: bool = Query(False),
    failure_rate: Optional[float] = Query(None),
    api_key: str = Depends(verify_api_key)
):
    """Verify Land Registry Title with State Revenue Department (Bhoomi)."""
    eff_latency = simulate_latency_and_failures(latency_ms, simulate_failure, failure_rate)
    result = process_verification("land", ref, name, claimed_expiry, claimed_acres)
    result["latency_ms"] = eff_latency
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    log_request_audit(request, "land", ref, name, result["status"], eff_latency, 200)
    return result

# ==============================================================================
# AUDIT LOGS & REGISTRY MANAGEMENT
# ==============================================================================

@app.get("/logs", status_code=status.HTTP_200_OK)
def get_audit_logs(limit: int = Query(50, ge=1, le=500),
                   api_key: str = Depends(verify_api_key)):
    """Returns in-memory request logging audit trail for committee inspection."""
    return {
        "total_logged_requests": len(REQUEST_AUDIT_LOGS),
        "limit": limit,
        "logs": REQUEST_AUDIT_LOGS[:limit]
    }

@app.get("/registry", status_code=status.HTTP_200_OK)
def get_registry_info():
    """Returns registry summary statistics and available references."""
    return {
        "version": registry_cache.get("version", "1.0.0"),
        "authorities": list(registry_cache.get("authorities", {}).keys()),
        "record_counts": {
            k: len(v.get("records", {}))
            for k, v in registry_cache.get("authorities", {}).items()
        }
    }

@app.post("/registry/reload", status_code=status.HTTP_200_OK)
def reload_registry_endpoint(api_key: str = Depends(verify_api_key)):
    """Hot-reloads registry.json from disk without downtime."""
    data = load_registry()
    total = sum(len(a.get("records", {})) for a in data.get("authorities", {}).values())
    return {
        "status": "RELOADED",
        "total_records": total,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ==============================================================================
# BACKWARD-COMPATIBLE POST ROUTES (For existing legacy integration)
# ==============================================================================
class LegacyFireQuery(BaseModel):
    noc_number: str
    institution_name: Optional[str] = None
    expiry_date: Optional[str] = None

class LegacyLandQuery(BaseModel):
    survey_no: str
    village: Optional[str] = "Devanahalli"
    claimed_acres: Optional[float] = 5.0
    trust_name: Optional[str] = None

class LegacyAffiliationQuery(BaseModel):
    aicte_id: str
    institution_name: Optional[str] = None
    year: Optional[str] = "2025-26"

@app.post("/api/v1/fire-noc/verify")
def legacy_fire(query: LegacyFireQuery):
    res = process_verification("fire", query.noc_number, query.institution_name or "", query.expiry_date)
    res["latency_ms"] = 90
    return res

@app.post("/api/v1/land-records/verify")
def legacy_land(query: LegacyLandQuery):
    res = process_verification("land", query.survey_no, query.trust_name or "", None, query.claimed_acres)
    res["latency_ms"] = 110
    return res

@app.post("/api/v1/affiliation/verify")
def legacy_affil(query: LegacyAffiliationQuery):
    res = process_verification("affiliation", query.aicte_id, query.institution_name or "", None)
    res["latency_ms"] = 85
    return res
