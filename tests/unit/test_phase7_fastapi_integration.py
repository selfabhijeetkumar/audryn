"""
AUDRYN Phase 7 & Phase 8 Comprehensive Integration and Security Test Suite.
Verifies all FastAPI HTTP routes, authentication, RBAC, engagement isolation,
CSRF protection, Decimal calculation accuracy, and audit workflows.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.auth import hash_password, AuthService
from backend.db.connection import db_manager
from backend.db.repositories import EvidenceRepository


@pytest.fixture(scope="module")
def client():
    """Initializes TestClient triggering app lifespan (migrations & seeding)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def partner_auth(client):
    """Logs in as seeded Partner and returns (session_cookie, csrf_token)."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "partner_sharma", "password": "AudrynPartnerSecure2026!"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    csrf_token = resp.headers.get("X-CSRF-Token") or resp.json().get("csrf_token")
    return resp.cookies, csrf_token


# ─── 1. Health & Status Tests ──────────────────────────────────────────

def test_health_endpoint(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "AUDRYN Audit Intelligence System"
    assert data["version"] == "2.1.0"
    assert "database" in data
    assert data["database"]["connected"] is True


def test_security_headers_and_correlation_id(client):
    resp = client.get("/api/v1/health")
    assert "X-Correlation-ID" in resp.headers
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


# ─── 2. Authentication & Session Security Tests ───────────────────────

def test_login_invalid_credentials(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "partner_sharma", "password": "WrongPassword123!"},
    )
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


def test_auth_me_authenticated(client, partner_auth):
    cookies, csrf = partner_auth
    resp = client.get("/api/v1/auth/me", cookies=cookies)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["username"] == "partner_sharma"
    assert data["user"]["role"] == "Partner"
    assert "APPROVE_FINDING" in data["user"]["permissions"]


def test_csrf_validation_on_state_changing_request(client, partner_auth):
    cookies, _ = partner_auth
    # Missing CSRF header should return 403
    resp = client.post(
        "/api/v1/engagements/ENG-APEX-FY24/calculations/run",
        json={"formula_name": "Test", "input_values": {"a": "100"}},
        cookies=cookies,
    )
    assert resp.status_code == 403
    assert "CSRF validation failed" in resp.json()["detail"]


# ─── 3. RBAC & Engagement Isolation Tests ─────────────────────────────

def test_associate_cannot_approve_findings(client):
    # Create Associate user
    try:
        AuthService.create_user(
            username="assoc_test",
            email="assoc@audryn.local",
            full_name="Associate Auditor",
            role="Associate",
            password="AssociatePass2026!",
        )
    except Exception:
        pass  # already created

    # Assign associate to ENG-APEX-FY24
    conn = db_manager.get_connection()
    with conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO engagement_members (engagement_id, user_id, role)
            SELECT 'ENG-APEX-FY24', user_id, 'Associate' FROM users WHERE username = 'assoc_test';
            """
        )
    conn.close()

    # Login as Associate
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "assoc_test", "password": "AssociatePass2026!"},
    )
    assert resp.status_code == 200
    assoc_cookies = resp.cookies
    assoc_csrf = resp.headers.get("X-CSRF-Token")

    # Associate attempts to APPROVE finding -> must be 403
    approve_resp = client.post(
        "/api/v1/engagements/ENG-APEX-FY24/human-review/decide",
        json={
            "finding_id": "ANOMALY-001",
            "decision": "APPROVED",
            "comments": "Associate trying to sign off.",
            "unresolved_acknowledged": True,
        },
        cookies=assoc_cookies,
        headers={"X-CSRF-Token": assoc_csrf},
    )
    assert approve_resp.status_code == 403
    assert "reserved exclusively for Partners" in approve_resp.json()["detail"]


def test_cross_engagement_idor_isolation(client, partner_auth):
    cookies, csrf = partner_auth

    # Attempt to access an engagement the user is NOT a member of
    resp = client.get("/api/v1/engagements/ENG-OTHER-UNAUTHORIZED/evidence", cookies=cookies)
    # Either 404 or 403
    assert resp.status_code in [403, 404]


# ─── 4. Evidence Workflow & Integrity Tests ───────────────────────────

def test_list_evidence(client, partner_auth):
    cookies, _ = partner_auth
    resp = client.get("/api/v1/engagements/ENG-APEX-FY24/evidence", cookies=cookies)
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) >= 4
    assert any(r["evidence_id"] == "EV-2024-001" for r in records)


def test_upload_and_verify_evidence(client, partner_auth):
    cookies, csrf = partner_auth
    test_content = b"INVOICE-2024-TEST-CONTENT-FOR-SHA256"
    resp = client.post(
        "/api/v1/engagements/ENG-APEX-FY24/evidence/upload",
        files={"file": ("test_invoice.csv", test_content, "text/csv")},
        data={"document_type": "INVOICE"},
        cookies=cookies,
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    data = resp.json()
    ev_id = data["evidence_id"]
    recorded_hash = data["sha256_hash"]

    # Verify hash endpoint
    v_resp = client.post(
        f"/api/v1/engagements/ENG-APEX-FY24/evidence/{ev_id}/verify-hash",
        cookies=cookies,
        headers={"X-CSRF-Token": csrf},
    )
    assert v_resp.status_code == 200
    v_data = v_resp.json()
    assert v_data["is_match"] is True
    assert v_data["computed_sha256"] == recorded_hash


def test_evidence_validity_workflow(client, partner_auth):
    cookies, csrf = partner_auth
    resp = client.post(
        "/api/v1/engagements/ENG-APEX-FY24/evidence/EV-2024-001/validity",
        json={
            "status": "ACCEPTED_FOR_STATED_PURPOSE",
            "purpose_scope": "Statutory audit revenue and asset tie-out.",
            "rationale": "Verified against audited trial balance signed by statutory auditors.",
        },
        cookies=cookies,
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ACCEPTED_FOR_STATED_PURPOSE"


# ─── 5. Completeness Gate & Not-Checked Register Tests ────────────────

def test_completeness_gate(client, partner_auth):
    cookies, _ = partner_auth
    resp = client.get("/api/v1/engagements/ENG-APEX-FY24/completeness", cookies=cookies)
    assert resp.status_code == 200
    data = resp.json()
    assert "gate_status" in data
    assert "total_required" in data
    assert data["total_required"] > 0


def test_not_checked_register_crud(client, partner_auth):
    cookies, csrf = partner_auth
    # Update NC-001
    resp = client.put(
        "/api/v1/engagements/ENG-APEX-FY24/not-checked/NC-001",
        json={
            "status": "REQUIRES_REVIEW",
            "reason_not_checked": "Depot under mandatory quarantine on 31 March.",
            "mitigating_notes": "Spot count scheduled for next fortnight.",
        },
        cookies=cookies,
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["status"] == "REQUIRES_REVIEW"
    assert "mandatory quarantine" in updated["reason_not_checked"]


# ─── 6. Investigation & Counter-Evidence Tests ────────────────────────

def test_investigation_run_and_findings(client, partner_auth):
    cookies, csrf = partner_auth
    resp = client.post(
        "/api/v1/engagements/ENG-APEX-FY24/investigations/run",
        cookies=cookies,
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    job_data = resp.json()
    assert job_data["status"] == "COMPLETED"
    assert job_data["findings_count"] >= 3

    # Check findings list
    f_resp = client.get("/api/v1/engagements/ENG-APEX-FY24/findings", cookies=cookies)
    assert f_resp.status_code == 200
    findings = f_resp.json()
    assert len(findings) >= 3

    # Verify counter-evidence verdicts are preserved
    f1 = next(f for f in findings if f["finding_id"] == "ANOMALY-001")
    assert f1["counter_evidence"]["verdict"] == "PARTIALLY_SUPPORTED"

    f2 = next(f for f in findings if f["finding_id"] == "ANOMALY-002")
    assert f2["counter_evidence"]["verdict"] == "CONTRADICTED"


# ─── 7. Human Review & Brass Sign-Off Tests ───────────────────────────

def test_human_review_unresolved_acknowledgment_gate(client, partner_auth):
    cookies, csrf = partner_auth
    # ANOMALY-001 is PARTIALLY_SUPPORTED. Trying to approve without unresolved_acknowledged should fail
    resp = client.post(
        "/api/v1/engagements/ENG-APEX-FY24/human-review/decide",
        json={
            "finding_id": "ANOMALY-001",
            "decision": "APPROVED",
            "comments": "Approved without acknowledgment.",
            "unresolved_acknowledged": False,
        },
        cookies=cookies,
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 400
    assert "requires explicit acknowledgment of unresolved counter-evidence" in resp.json()["detail"]


def test_human_review_partner_brass_approval(client, partner_auth):
    cookies, csrf = partner_auth
    resp = client.post(
        "/api/v1/engagements/ENG-APEX-FY24/human-review/decide",
        json={
            "finding_id": "ANOMALY-001",
            "decision": "APPROVED",
            "comments": "Confirmed post-period delivery note. Cut-off timing verified.",
            "reviewer_membership_no": "ICAI-084920",
            "unresolved_acknowledged": True,
        },
        cookies=cookies,
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_brass_signoff_active"] is True
    assert data["review"]["decision"] == "APPROVED"


# ─── 8. Financial Engine & Tax Rulebook Tests ─────────────────────────

def test_financial_decimal_math(client, partner_auth):
    cookies, csrf = partner_auth
    resp = client.post(
        "/api/v1/engagements/ENG-APEX-FY24/calculations/run",
        json={
            "formula_name": "Gross Profit Reconciliation",
            "input_values": {
                "Revenue": "10000000.00",
                "COGS": "6500000.00",
            },
        },
        cookies=cookies,
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "3500000.00"


def test_section_115baa_tax_computation(client, partner_auth):
    cookies, csrf = partner_auth
    resp = client.post(
        "/api/v1/engagements/ENG-APEX-FY24/tax/section115baa",
        json={
            "gross_total_income": "10000000.00",
            "claimed_deductions": [],
            "deduction_amounts": {},
            "financial_year": "FY 2023-24",
        },
        cookies=cookies,
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_eligible"] is True
    # 22% Base + 10% Surcharge + 4% Cess = 25.168% => ₹25,16,800.00 on ₹1,00,00,000.00
    assert data["total_tax_liability"] == "2516800.00"
    assert data["effective_tax_rate_percent"] == "25.17"


def test_section_32_depreciation_computation(client, partner_auth):
    cookies, csrf = partner_auth
    resp = client.post(
        "/api/v1/engagements/ENG-APEX-FY24/tax/section32",
        json={
            "block_id": "IN-SEC32-PLANT-MACHINERY-GENERAL",
            "opening_wdv": "1000000.00",
            "additions_used_gte_180_days": "200000.00",
            "additions_used_lt_180_days": "100000.00",
            "sales_realized": "0.00",
        },
        cookies=cookies,
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    data = resp.json()
    # 15% on opening (150,000) + 15% on >=180 days (30,000) + 7.5% on <180 days (7,500) = 187,500.00
    assert str(data["total_tax_depreciation"]) == "187500.00"


# ─── 9. Provenance Graph & Report Manifest Tests ──────────────────────

def test_provenance_graph(client, partner_auth):
    cookies, _ = partner_auth
    resp = client.get("/api/v1/engagements/ENG-APEX-FY24/provenance", cookies=cookies)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_nodes"] > 0
    assert data["total_links"] > 0


def test_report_generation_and_manifest(client, partner_auth):
    cookies, csrf = partner_auth
    resp = client.post(
        "/api/v1/engagements/ENG-APEX-FY24/reports/generate",
        json={"include_counter_evidence": True, "include_not_checked": True},
        cookies=cookies,
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    report = resp.json()
    manifest = report["manifest"]
    assert "evidence_hashes" in manifest
    assert len(manifest["evidence_hashes"]) >= 4
    assert manifest["status"] in ["REVIEW_READY", "DRAFT"]
