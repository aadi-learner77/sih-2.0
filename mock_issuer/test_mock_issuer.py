"""
Unit and integration tests for PRAMAAN-X Mock Issuer Gateway Service
Validates:
1. API-Key Header Security (401 on missing/invalid)
2. All 5 Return Statuses: 'verified', 'mismatch', 'expired', 'not_found', 'source_unavailable' (HTTP 503)
3. All 4 Authorities: fire, affiliation, accreditation, land
4. Unified GET /verify endpoint and dedicated per-authority endpoints
5. Latency simulation & Request audit logging (/logs)
"""
import pytest
from fastapi.testclient import TestClient
from mock_issuer.app.main import app, EXPECTED_API_KEY, load_registry

client = TestClient(app)

@pytest.fixture(autouse=True)
def ensure_registry_loaded():
    """Ensure registry data is loaded prior to test execution."""
    load_registry()

def test_health_endpoint():
    """Test health check returns operational metrics and record counts."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "pramaanx-mock-issuer"
    assert "total_registry_records" in data
    assert data["total_registry_records"] > 0
    assert "fire" in data["record_counts_by_authority"]

def test_api_key_security_unauthorized():
    """Test that requests lacking valid X-API-Key return HTTP 401 Unauthorized."""
    # Missing header
    res = client.get("/verify?ref=FS/2024/7741&name=Apex+Institute")
    assert res.status_code == 401
    assert "detail" in res.json()

    # Invalid header
    res = client.get(
        "/verify?ref=FS/2024/7741&name=Apex+Institute",
        headers={"X-API-Key": "wrong-bogus-key"}
    )
    assert res.status_code == 401

def test_status_verified():
    """Test clean valid document returns status 'verified' with zero discrepancies."""
    res = client.get(
        "/verify?ref=FS/2024/7741&name=Apex+Institute+of+Technology+%26+Science&authority=fire&latency_ms=10",
        headers={"X-API-Key": EXPECTED_API_KEY}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "verified"
    assert data["authority"] == "fire"
    assert data["mismatched_fields"] == []
    assert data["discrepancies"] == []
    assert data["authoritative_record"]["status"] == "VALID_ACTIVE"

def test_status_mismatch():
    """Test document with altered entity name or occupancy returns 'mismatch' with detailed discrepancies."""
    # FS/2024/991 is registered to Apex Commercial Shopping Mall
    res = client.get(
        "/verify?ref=FS/2024/991&name=Apex+Institute+of+Technology&authority=fire&latency_ms=10",
        headers={"X-API-Key": EXPECTED_API_KEY}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "mismatch"
    assert len(data["discrepancies"]) > 0
    assert any(d["field"] == "registered_entity" for d in data["discrepancies"])
    assert "Apex Commercial Shopping Mall" in data["discrepancies"][0]["issuer_value"]

def test_status_expired():
    """Test certificate with past validity returns 'expired'."""
    # FS/2023/8812 expired on 2024-01-09
    res = client.get(
        "/verify?ref=FS/2023/8812&name=Apex+Institute&authority=fire&latency_ms=10",
        headers={"X-API-Key": EXPECTED_API_KEY}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "expired"
    assert len(data["discrepancies"]) > 0
    assert any("expired" in d["issue"].lower() for d in data["discrepancies"])

def test_status_not_found():
    """Test non-existent / forged reference returns 'not_found'."""
    res = client.get(
        "/verify?ref=FORGED/NOC/99999&name=Unknown+College&authority=fire&latency_ms=10",
        headers={"X-API-Key": EXPECTED_API_KEY}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "not_found"
    assert data["authoritative_record"] is None
    assert any("not found" in d["issue"].lower() for d in data["discrepancies"])

def test_source_unavailable_503():
    """Test simulated gateway timeout / source unavailable returns HTTP 503."""
    res = client.get(
        "/verify?ref=FS/2024/7741&name=Apex+Institute&simulate_failure=true&latency_ms=10",
        headers={"X-API-Key": EXPECTED_API_KEY}
    )
    assert res.status_code == 503
    assert "unreachable" in res.json()["detail"].lower()

def test_dedicated_authority_endpoints():
    """Test each authority's dedicated endpoint: fire, affiliation, accreditation, land."""
    headers = {"X-API-Key": EXPECTED_API_KEY}

    # 1. State Fire Department
    res_fire = client.get("/fire/verify?ref=FS/2024/7741&name=Apex+Institute&latency_ms=5", headers=headers)
    assert res_fire.status_code == 200
    assert res_fire.json()["authority"] == "fire"

    # 2. University Affiliation Body
    res_affil = client.get("/affiliation/verify?ref=VTU/ACA/2024-25/A-4/1049&name=Apex+Institute&latency_ms=5", headers=headers)
    assert res_affil.status_code == 200
    assert res_affil.json()["authority"] == "affiliation"
    assert res_affil.json()["status"] == "verified"

    # 3. NBA Accreditation Body
    res_accr = client.get("/accreditation/verify?ref=NBA/2024/TIER1/9921&name=Apex+Institute&latency_ms=5", headers=headers)
    assert res_accr.status_code == 200
    assert res_accr.json()["authority"] == "accreditation"
    assert res_accr.json()["status"] == "verified"

    # 4. Land-Records Office (Bhoomi)
    res_land = client.get("/land/verify?ref=LAND/DEED/2020/CLEAR&name=Apex+Institute&claimed_acres=12.5&latency_ms=5", headers=headers)
    assert res_land.status_code == 200
    assert res_land.json()["authority"] == "land"
    assert res_land.json()["status"] == "verified"

def test_request_logging_audit_endpoint():
    """Test that all verification calls are recorded in the /logs endpoint."""
    res = client.get("/logs?limit=10", headers={"X-API-Key": EXPECTED_API_KEY})
    assert res.status_code == 200
    data = res.json()
    assert "logs" in data
    assert len(data["logs"]) > 0
    latest = data["logs"][0]
    assert "timestamp" in latest
    assert "authority" in latest
    assert "result_status" in latest
    assert "latency_ms" in latest
