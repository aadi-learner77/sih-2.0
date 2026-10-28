import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

from backend.app.core.security import create_access_token, ROLE_SCRUTINY_OFFICER

client = TestClient(app)

def get_headers():
    token = create_access_token(data={"sub": "scrutiny.officer@aicte-india.org", "role": ROLE_SCRUTINY_OFFICER})
    return {"Authorization": f"Bearer {token}"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["platform"] == "PRAMAAN-X"

def test_applications_list():
    response = client.get("/api/v1/applications", headers=get_headers())
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert any("Apex Institute" in app.get("institution_name", "") for app in data)

def test_evidence_lens():
    # Fetch first application
    apps_res = client.get("/api/v1/applications", headers=get_headers())
    app_id = apps_res.json()[0]["id"]
    response = client.get(f"/api/v1/applications/{app_id}/evidence-lens", headers=get_headers())
    assert response.status_code == 200
    lens_data = response.json()
    items = lens_data.get("evidence_lens_items") or lens_data.get("findings", [])
    assert len(items) >= 1
    # Check finding schema
    item = items[0]
    assert "id" in item
    assert "title" in item
    assert "clause_id" in item
    assert "ai_wording" in item

def test_knowledge_graph_and_impossibilities():
    graph_res = client.get("/api/v1/graph", headers=get_headers())
    assert graph_res.status_code == 200
    graph = graph_res.json()
    assert "nodes" in graph
    assert "edges" in graph
    
    imp_res = client.get("/api/v1/graph/impossibilities", headers=get_headers())
    assert imp_res.status_code == 200
    anomalies = imp_res.json()
    assert len(anomalies) >= 2
    # Verify Ghost faculty detected
    types = [a["conflict_type"] for a in anomalies]
    assert "DUAL_EMPLOYMENT_GHOST_FACULTY" in types
    assert "SHARED_LAND_PARCEL_COLLISION" in types

def test_photo_reuse_radar():
    # Test with matching perceptual hash from seed data
    response = client.post("/api/v1/forensics/photo-radar/scan", headers=get_headers(), data={
        "phash": "a8f0c3d2e1b4a5f6",
        "institution_id": "INST_001"
    })
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["match_found"] is True
    assert res_data["top_match"]["matched_institution_name"] == "Royal College of Engineering"

def test_audit_chain_verification():
    response = client.get("/api/v1/audit/verify-chain", headers=get_headers())
    assert response.status_code == 200
    audit_data = response.json()
    assert audit_data["is_intact"] is True
    assert audit_data["status"] == "VALID_VERIFIED"
    assert audit_data["chain_length"] >= 7

def test_rules_engine_listing():
    response = client.get("/api/v1/rules", headers=get_headers())
    assert response.status_code == 200
    rules = response.json()
    assert len(rules) >= 4
    clause_ids = [r["clause_id"] for r in rules]
    assert any("4.1" in c for c in clause_ids)

if __name__ == "__main__":
    print("Running PRAMAAN-X API smoke tests...")
    test_root()
    test_applications_list()
    test_evidence_lens()
    test_knowledge_graph_and_impossibilities()
    test_photo_reuse_radar()
    test_audit_chain_verification()
    test_rules_engine_listing()
    print("All tests passed with flying colors!")
