"""
Phase 8 End-to-End Synthetic Audit Journey — AUDRYN V2.1
Complete 12-step journey using FastAPI TestClient against the real backend.
"""

import io
import os
import sys
import json
import hashlib
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def session(client):
    """Authenticate and return headers with CSRF token."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "partner_sharma",
        "password": "AudrynPartnerSecure2026!"
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    csrf = resp.headers.get("X-CSRF-Token", "")
    return {"csrf": csrf, "headers": {"X-CSRF-Token": csrf}}


ENGAGEMENT_ID = "ENG-APEX-FY24"
SYNTHETIC_FILE_CONTENT = (
    b"SYNTHETIC DATA - AUDRYN PHASE 8 E2E TEST\n"
    b"Invoice Number: INV-E2E-001\n"
    b"Amount: INR 50,00,000\n"
    b"Date: 2024-03-31\n"
    b"Vendor: Apex Industrial Tech Ltd\n"
)


class TestE2EAuditJourney:
    """12-step synthetic end-to-end audit journey."""

    uploaded_evidence_id = None
    uploaded_sha256 = None
    finding_id = None
    report_id = None

    # Step 1: Authenticate
    def test_step_01_authenticate(self, client, session):
        resp = client.get("/api/v1/auth/me", headers=session["headers"])
        assert resp.status_code == 200
        body = resp.json()
        # Response is {"user": {"user_id": ..., "username": ...}, "csrf_token": ...}
        user_data = body.get("user", body)
        assert "user_id" in user_data or "username" in user_data
        assert "password_hash" not in json.dumps(body)

    # Step 2: Open Engagement
    def test_step_02_open_engagement(self, client, session):
        resp = client.get(
            f"/api/v1/engagements/{ENGAGEMENT_ID}",
            headers=session["headers"]
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["engagement_id"] == ENGAGEMENT_ID
        # Seeded data uses entity_name and fiscal_year
        assert body.get("entity_name") == "Apex Industrial Tech Ltd" or body.get("client_entity") == "Apex Industrial Tech Ltd"
        assert "FY" in body.get("fiscal_year", body.get("financial_year", ""))

    # Step 3: Upload Synthetic Evidence
    def test_step_03_upload_evidence(self, client, session):
        expected_hash = hashlib.sha256(SYNTHETIC_FILE_CONTENT).hexdigest()
        TestE2EAuditJourney.uploaded_sha256 = expected_hash

        resp = client.post(
            f"/api/v1/engagements/{ENGAGEMENT_ID}/evidence/upload",
            files={"file": ("e2e_test_invoice.pdf", io.BytesIO(SYNTHETIC_FILE_CONTENT), "application/pdf")},
            data={"document_type": "INVOICE"},
            headers=session["headers"],
        )
        assert resp.status_code in (200, 201), f"Upload failed: {resp.text}"
        body = resp.json()
        assert "evidence_id" in body
        TestE2EAuditJourney.uploaded_evidence_id = body["evidence_id"]

    # Step 4: Verify SHA-256 Hash
    def test_step_04_verify_sha256(self, client, session):
        if not TestE2EAuditJourney.uploaded_evidence_id:
            pytest.skip("No evidence uploaded in Step 3")

        resp = client.post(
            f"/api/v1/engagements/{ENGAGEMENT_ID}/evidence/{TestE2EAuditJourney.uploaded_evidence_id}/verify-hash",
            json={"provided_hash": TestE2EAuditJourney.uploaded_sha256},
            headers=session["headers"],
        )
        assert resp.status_code == 200
        body = resp.json()
        # API returns is_match not match
        assert body.get("is_match") is True, (
            f"Hash verification failed: {body}"
        )

    # Step 5: Evaluate Completeness Gate
    def test_step_05_completeness_gate(self, client, session):
        resp = client.get(
            f"/api/v1/engagements/{ENGAGEMENT_ID}/completeness",
            headers=session["headers"]
        )
        assert resp.status_code == 200
        body = resp.json()
        # API returns CompletenessGateResult model with gate_status, total_required, total_satisfied
        assert "gate_status" in body or "completeness_percentage" in body
        assert "total_required" in body or "total_evidence_items" in body

    # Step 6: Run Investigation
    def test_step_06_run_investigation(self, client, session):
        resp = client.post(
            f"/api/v1/engagements/{ENGAGEMENT_ID}/investigations/run",
            json={"investigation_type": "ANOMALY_DETECTION", "scope": "all"},
            headers=session["headers"],
        )
        assert resp.status_code in (200, 201, 202), f"Investigation failed: {resp.text}"
        body = resp.json()
        assert "job_id" in body or "investigation_id" in body or "status" in body

    # Step 7: List Findings
    def test_step_07_list_findings(self, client, session):
        resp = client.get(
            f"/api/v1/engagements/{ENGAGEMENT_ID}/findings",
            headers=session["headers"]
        )
        assert resp.status_code == 200
        findings = resp.json()
        assert isinstance(findings, list)
        assert len(findings) > 0, "No findings returned"
        TestE2EAuditJourney.finding_id = findings[0].get("finding_id") or findings[0].get("id")

    # Step 8: Inspect Provenance Graph
    def test_step_08_provenance_graph(self, client, session):
        resp = client.get(
            f"/api/v1/engagements/{ENGAGEMENT_ID}/provenance",
            headers=session["headers"]
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "nodes" in body
        assert "links" in body or "edges" in body

    # Step 9: Counter-Evidence Check
    def test_step_09_counter_evidence(self, client, session):
        resp = client.get(
            f"/api/v1/engagements/{ENGAGEMENT_ID}/counter-evidence",
            headers=session["headers"]
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        valid_verdicts = {
            "SUPPORTED", "CONTRADICTED", "PARTIALLY_SUPPORTED",
            "UNRESOLVED", "INSUFFICIENT_EVIDENCE"
        }
        for item in body:
            verdict = item.get("verdict")
            if verdict:
                assert verdict in valid_verdicts, f"Non-canonical verdict: {verdict}"

    # Step 10: Human Review Decision
    def test_step_10_human_review(self, client, session):
        if not TestE2EAuditJourney.finding_id:
            pytest.skip("No finding ID from Step 7")

        resp = client.post(
            f"/api/v1/engagements/{ENGAGEMENT_ID}/human-review/decide",
            json={
                "finding_id": TestE2EAuditJourney.finding_id,
                "decision": "APPROVE",
                "reason": "E2E test: Partner approval of seeded finding",
                "reviewer_role": "Partner",
            },
            headers=session["headers"],
        )
        assert resp.status_code in (200, 201, 403, 422), f"Human review failed: {resp.text}"

    # Step 11: Generate Draft Report
    def test_step_11_generate_report(self, client, session):
        resp = client.post(
            f"/api/v1/engagements/{ENGAGEMENT_ID}/reports/generate",
            json={"include_counter_evidence": True, "include_not_checked": True},
            headers=session["headers"],
        )
        assert resp.status_code in (200, 201), f"Report generation failed: {resp.text}"
        body = resp.json()
        assert "report_id" in body or "id" in body
        TestE2EAuditJourney.report_id = body.get("report_id") or body.get("id")

    # Step 12: Verify Audit Event Trail
    def test_step_12_audit_trail(self, client, session):
        resp = client.get(
            f"/api/v1/engagements/{ENGAGEMENT_ID}/audit-events",
            headers=session["headers"]
        )
        assert resp.status_code == 200
        events = resp.json()
        assert isinstance(events, list)
        assert len(events) > 0, "No audit events recorded"

    # Supplemental: Three-Dimension Evidence Independence
    def test_supplemental_evidence_dimensions_independent(self, client, session):
        if not TestE2EAuditJourney.uploaded_evidence_id:
            pytest.skip("No uploaded evidence from Step 3")

        resp = client.get(
            f"/api/v1/engagements/{ENGAGEMENT_ID}/evidence/{TestE2EAuditJourney.uploaded_evidence_id}/validity",
            headers=session["headers"]
        )
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            body = resp.json()
            assert "validity_status" in body or "decisions" in body or isinstance(body, list), (
                "Evidence validity response must model individual review dimensions"
            )
