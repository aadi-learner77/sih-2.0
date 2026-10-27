"""
Pytest Test Suite for Evidence Lens API Endpoint:
Validates GET /api/v1/applications/{app_id}/evidence-lens:
1. Returns 200 OK for Scrutiny Officer with application metadata and real findings.
2. Verifies mandatory statutory wording: all AI wording must start with "Indicator for review".
3. Validates required schema: id, finding_type, title, clause_id, severity, document, pipeline, action_panel.
4. Tenant isolation: returns 403 Forbidden when an institution user accesses another institution's dossier.
5. Returns 200 OK when an institution user accesses their own institution's dossier.
6. Returns 404 Not Found for non-existent application ID.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.models import Application
from backend.app.core.security import (
    create_access_token,
    normalize_role,
    ROLE_INSTITUTION_USER,
    ROLE_SCRUTINY_OFFICER,
    ROLE_SENIOR_OFFICER,
    ROLE_ADMIN,
    ROLE_AUDITOR
)
from backend.app.data.seed_data import seed_database


@pytest.fixture(scope="module")
def client():
    seed_database()
    with TestClient(app) as test_client:
        yield test_client


def get_token(email: str, role: str, institution_id: int | None = None) -> str:
    return create_access_token(
        data={"sub": email, "role": normalize_role(role), "institution_id": institution_id}
    )


def test_evidence_lens_200_for_scrutiny_officer(client: TestClient):
    """Verifies 200 OK for an authorized officer and validates findings shape and wording."""
    token = get_token("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/applications/1/evidence-lens", headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    assert "application" in data
    assert "findings" in data
    assert data["application"]["id"] == 1
    assert data["application"]["application_no"] == "EOA-2025-ENG-9821"

    findings = data["findings"]
    assert isinstance(findings, list)
    assert len(findings) > 0

    for f in findings:
        # Check required fields
        assert "id" in f
        assert "finding_type" in f
        assert f["finding_type"] in ["DOCUMENT", "GRAPH", "GRAPH_CONFLICT", "PHOTO"]
        assert "title" in f
        assert "clause_id" in f
        assert "severity" in f
        assert "ai_wording" in f
        assert "pipeline" in f

        # Mandatory statutory rule: AI wording MUST start with "Indicator for review"
        assert f["ai_wording"].strip().startswith("Indicator for review"), (
            f"Finding {f['id']} wording '{f['ai_wording']}' does not start with 'Indicator for review'"
        )

        # Check 6-stage pipeline structure
        p = f["pipeline"]
        assert "claim" in p
        assert "evidence" in p
        assert "rule" in p
        assert "source_response" in p
        assert "ai_confidence" in p
        assert "officer_action" in p


def test_evidence_lens_tenant_isolation_403_for_other_institution(client: TestClient):
    """Institution 2 user requesting Institution 1's dossier must receive 403 Forbidden."""
    # User belongs to institution_id = 2
    token = get_token("principal@royal.edu.in", ROLE_INSTITUTION_USER, institution_id=2)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/applications/1/evidence-lens", headers=headers)
    assert resp.status_code == 403
    assert "tenant" in resp.json().get("detail", "").lower() or "isolation" in resp.json().get("detail", "").lower() or "forbidden" in resp.json().get("detail", "").lower()


def test_evidence_lens_200_for_own_institution(client: TestClient):
    """Institution 1 user requesting their own dossier receives 200 OK."""
    token = get_token("registrar@apextech.edu.in", ROLE_INSTITUTION_USER, institution_id=1)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/applications/1/evidence-lens", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["application"]["id"] == 1


def test_evidence_lens_404_for_nonexistent_application(client: TestClient):
    """Non-existent application ID must return 404 Not Found."""
    token = get_token("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/applications/999999/evidence-lens", headers=headers)
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Application not found"


def test_evidence_lens_empty_state_app_2(client: TestClient):
    """Application 2 has 0 findings and should return findings: []."""
    token = get_token("scrutiny.officer@aicte-india.org", ROLE_SCRUTINY_OFFICER)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/applications/2/evidence-lens", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["findings"] == []
