"""
AUDRYN FastAPI Backend Application.
Master application entrypoint providing versioned HTTP routes (/api/v1),
strict CORS, security headers, request correlation IDs, and automated OpenAPI contract generation.
"""
import json
import os
import secrets
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.db.migrate import run_migrations
from backend.db.connection import db_manager, DEFAULT_DB_PATH
from backend.app.bootstrap_admin import bootstrap_admin
from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router
from backend.app.api.engagements import router as engagements_router
from backend.app.api.evidence import router as evidence_router
from backend.app.api.completeness import router as completeness_router
from backend.app.api.investigations import router as investigations_router
from backend.app.api.counter_evidence import router as counter_evidence_router
from backend.app.api.human_review import router as human_review_router
from backend.app.api.calculations import router as calculations_router
from backend.app.api.provenance import router as provenance_router
from backend.app.api.reports import router as reports_router
from backend.app.api.audit_events import router as audit_events_router
from backend.app.api.providers import router as providers_router
from backend.db.repositories import (
    EvidenceRepository,
    FindingsRepository,
    CounterEvidenceRepository,
    CalculationRepository,
    NotCheckedRepository,
    ReportRepository,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    # Ensure directories exist
    db_path = os.environ.get("AUDRYN_DB_PATH", DEFAULT_DB_PATH)
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    vault_path = os.environ.get("AUDRYN_VAULT_PATH", os.path.join("data", "evidence_vault"))
    os.makedirs(vault_path, exist_ok=True)

    # Ensure migrations are applied
    run_migrations(db_path)

    # Bootstrap default Partner user if not exists (environment-controlled)
    is_production = bool(os.environ.get("RENDER") or os.environ.get("ENV") == "production" or os.environ.get("NODE_ENV") == "production")
    partner_pwd = os.environ.get("AUDRYN_PARTNER_PASSWORD") or os.environ.get("AUDRYN_BOOTSTRAP_PASSWORD")

    if is_production and not partner_pwd:
        partner_pwd = secrets.token_urlsafe(32)
        print("[SECURITY NOTICE] Production deployment active: Partner password generated via CSPRNG. Manage via AUDRYN_PARTNER_PASSWORD environment variable.")
    elif not partner_pwd:
        partner_pwd = os.environ.get("AUDRYN_TEST_PASSWORD", "AudrynPartnerSecure2026!")

    partner_id = bootstrap_admin(
        username="partner_sharma",
        email="rajesh.sharma@audryn.local",
        full_name="Rajesh K. Sharma, FCA",
        password=partner_pwd,
        role="Partner",
    )

    # Seed default engagement (Apex Industrial Tech Ltd)
    conn = db_manager.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT engagement_id FROM engagements WHERE engagement_id = 'ENG-APEX-FY24';")
        if not cur.fetchone():
            with conn:
                conn.execute(
                    """
                    INSERT INTO engagements (engagement_id, entity_name, cin, fiscal_year, assessment_year, currency, status)
                    VALUES ('ENG-APEX-FY24', 'Apex Industrial Tech Ltd', 'L29100MH2012PLC234567', 'FY 2023-24', 'AY 2024-25', 'INR', 'ACTIVE');
                    """
                )
                conn.execute(
                    """
                    INSERT INTO engagement_members (engagement_id, user_id, role)
                    VALUES ('ENG-APEX-FY24', ?, 'Partner');
                    """,
                    (partner_id,),
                )

            # Seed evidence records
            EvidenceRepository.create(
                evidence_id="EV-2024-001",
                engagement_id="ENG-APEX-FY24",
                original_filename="trial_balance_FY2023_24_final.xlsx",
                sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                file_size_bytes=452100,
                document_type="TRIAL_BALANCE",
                extraction_status="EXTRACTED",
                raw_storage_path=os.path.join("data", "evidence_vault", "seed_tb.xlsx"),
                uploaded_by=partner_id,
                page_count=1,
            )
            EvidenceRepository.create(
                evidence_id="EV-2024-002",
                engagement_id="ENG-APEX-FY24",
                original_filename="bank_statement_hdfc_q4.pdf",
                sha256_hash="8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
                file_size_bytes=1240500,
                document_type="BANK_STATEMENT",
                extraction_status="EXTRACTED",
                raw_storage_path=os.path.join("data", "evidence_vault", "seed_bank.pdf"),
                uploaded_by=partner_id,
                page_count=14,
            )
            EvidenceRepository.create(
                evidence_id="EV-2024-003",
                engagement_id="ENG-APEX-FY24",
                original_filename="gstr_2b_reconciliation_fy24.xlsx",
                sha256_hash="ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                file_size_bytes=312000,
                document_type="TAX_RETURN",
                extraction_status="EXTRACTED",
                raw_storage_path=os.path.join("data", "evidence_vault", "seed_gstr.xlsx"),
                uploaded_by=partner_id,
                page_count=3,
            )
            EvidenceRepository.create(
                evidence_id="EV-2024-004",
                engagement_id="ENG-APEX-FY24",
                original_filename="fixed_assets_register_fy24.pdf",
                sha256_hash="3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d",
                file_size_bytes=684000,
                document_type="FIXED_ASSET_REGISTER",
                extraction_status="EXTRACTED",
                raw_storage_path=os.path.join("data", "evidence_vault", "seed_far.pdf"),
                uploaded_by=partner_id,
                page_count=6,
            )

            # Seed findings and challenges
            FindingsRepository.create(
                finding_id="ANOMALY-001",
                engagement_id="ENG-APEX-FY24",
                title="Revenue Recognition — Cut-Off Timing Discrepancy",
                category="REVENUE",
                severity="HIGH",
                impact_amount="4500000.00",
                currency="INR",
                source_evidence_ids=["EV-2024-001", "EV-2024-002"],
                agent_role="Revenue Specialist Agent (CrewAI)",
            )
            CounterEvidenceRepository.create_or_update(
                challenge_id="CHAL-001",
                finding_id="ANOMALY-001",
                engagement_id="ENG-APEX-FY24",
                original_hypothesis="Sales invoice INV-2024-889 recognized in Q4 revenue despite dispatch date of 03 April.",
                supporting_evidence=[
                    "Sales invoice INV-2024-889 dated 31 Mar 2024 booked in Q4 revenue for ₹45,00,000.00.",
                    "Customer purchase order confirmed Q4 acceptance terms.",
                ],
                contradictory_evidence=[
                    "Lorry receipt / e-Way bill dated 03 Apr 2024 proves dispatch occurred in subsequent FY 2024-25.",
                ],
                alternative_explanations=[
                    "Goods were staged at warehouse on 31 March but physical carrier gate-out occurred post-midnight on 3 April.",
                ],
                calculation_verification="Deterministic check: Expected=₹0.00, Actual=₹45,00,000.00, Variance=₹45,00,000.00.",
                reviewer_role="Independent Reviewer (MS Agent Framework)",
                reviewer_verdict="PARTIALLY_SUPPORTED",
                verdict_rationale="Evidence confirms goods were invoiced prior to dispatch; counter-evidence proves physical shipment delayed until subsequent period.",
                requires_escalation=True,
                notes="Warehouse CCTV dispatch log not yet furnished by management.",
            )

            FindingsRepository.create(
                finding_id="ANOMALY-002",
                engagement_id="ENG-APEX-FY24",
                title="Section 32 Depreciation — 180-Day Rule Addition Mismatch",
                category="TAX",
                severity="MEDIUM",
                impact_amount="1250000.00",
                currency="INR",
                source_evidence_ids=["EV-2024-004"],
                agent_role="Statutory Tax Specialist (CrewAI)",
            )
            CounterEvidenceRepository.create_or_update(
                challenge_id="CHAL-002",
                finding_id="ANOMALY-002",
                engagement_id="ENG-APEX-FY24",
                original_hypothesis="Asset put-to-use certificate was filed with date 15 Oct 2023 (less than 180 days).",
                supporting_evidence=[
                    "Asset put-to-use certificate was originally filed with date 15 Oct 2023 (less than 180 days).",
                ],
                contradictory_evidence=[
                    "Installation log and electricity sub-meter readings prove trial production began 28 Sep 2023 (used >= 180 days).",
                ],
                alternative_explanations=[
                    "Clerical error on commissioning certificate header: inspection signed in October but trial run active since September.",
                ],
                calculation_verification="Deterministic check: Full 100% statutory rate applicable under Section 32 given usage >= 180 days.",
                reviewer_role="Independent Reviewer (MS Agent Framework)",
                reviewer_verdict="CONTRADICTED",
                verdict_rationale="Contradictory technical logs confirm asset was actively energized and in trial production prior to October cut-off.",
                requires_escalation=False,
            )

            FindingsRepository.create(
                finding_id="ANOMALY-003",
                engagement_id="ENG-APEX-FY24",
                title="Input Tax Credit (ITC) Variance — GSTR-2B vs Books",
                category="TAX",
                severity="CRITICAL",
                impact_amount="7820450.00",
                currency="INR",
                source_evidence_ids=["EV-2024-003"],
                agent_role="Forensic Audit Specialist (CrewAI)",
            )
            CounterEvidenceRepository.create_or_update(
                challenge_id="CHAL-003",
                finding_id="ANOMALY-003",
                engagement_id="ENG-APEX-FY24",
                original_hypothesis="₹78,20,450.00 ITC claimed in GSTR-3B does not reflect in auto-populated GSTR-2B statement.",
                supporting_evidence=[
                    "₹78,20,450.00 ITC claimed in GSTR-3B does not reflect in auto-populated GSTR-2B statement.",
                    "Three suppliers failed to file their GSTR-1 returns for Q3 and Q4.",
                ],
                contradictory_evidence=[],
                alternative_explanations=[
                    "Suppliers have delayed quarterly returns; ITC is inadmissible under Section 16(2)(aa) of CGST Act until supplier files.",
                ],
                calculation_verification="Deterministic check: ITC mismatch of ₹78,20,450.00 exactly confirmed against GSTR-2B ledger.",
                reviewer_role="Independent Reviewer (MS Agent Framework)",
                reviewer_verdict="SUPPORTED",
                verdict_rationale="No contradictory records found in GST portal data; statutory mismatch confirmed.",
                requires_escalation=True,
                notes="Possibility of supplier late-filing in subsequent month has not been reconciled.",
            )

            # Seed Not-Checked items
            NotCheckedRepository.create_or_update(
                procedure_id="NC-001",
                engagement_id="ENG-APEX-FY24",
                audit_area="Physical Inventory Verification",
                title="Year-End Stock Count at Bhiwandi Depot",
                description="Depot under statutory fumigation lockdown on 31 March 2024; auditor physical attendance precluded.",
                status="NOT_CHECKED",
                reason_not_checked="Statutory fumigation lockdown issued by local health authority.",
                mitigating_notes="Roll-forward procedure scheduled with perpetual inventory records and independent spot-check.",
                assigned_reviewer="Priya Sundaram, ACA",
            )
            NotCheckedRepository.create_or_update(
                procedure_id="NC-002",
                engagement_id="ENG-APEX-FY24",
                audit_area="Statutory Dues — ESIC & EPF",
                title="Third-Party Contractor Challan Inspection",
                description="Contractor portal login tokens expired during field audit; challans pending electronic submission.",
                status="NOT_CHECKED",
                reason_not_checked="Contractor portal login expired during fieldwork.",
                mitigating_notes="Indemnity bond secured from vendor; portal reconciliation assigned to Q1 follow-up.",
                assigned_reviewer="Amitav Sen, FCA",
            )
            NotCheckedRepository.create_or_update(
                procedure_id="NC-003",
                engagement_id="ENG-APEX-FY24",
                audit_area="Foreign Exchange Hedging",
                title="Mark-to-Market Bank Valuations",
                description="Direct bank confirmation letter for Singapore branch derivatives pending dispatch.",
                status="NOT_CHECKED",
                reason_not_checked="Direct bank confirmation letter pending dispatch.",
                mitigating_notes="Management internal valuation verified against Bloomberg spot rates on 31 March 2024.",
                assigned_reviewer="Rajesh K. Sharma, FCA",
            )
    finally:
        conn.close()

    yield


app = FastAPI(
    title="AUDRYN Audit Intelligence System API",
    description="Evidence-First Multi-Agent Financial Audit Intelligence & Decision-Support System",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
)

# 1. CORS Middleware (Strict Origin Control)
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:4173",
    "https://frontend-chi-nine-98.vercel.app",
]
_extra_frontend = os.environ.get("FRONTEND_URL")
if _extra_frontend and _extra_frontend not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(_extra_frontend)
_vercel_url = os.environ.get("VERCEL_URL")
if _vercel_url:
    _v_origin = f"https://{_vercel_url}" if not _vercel_url.startswith("http") else _vercel_url
    if _v_origin not in ALLOWED_ORIGINS:
        ALLOWED_ORIGINS.append(_v_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID", "X-CSRF-Token"],
)


# 2. Security Headers & Correlation ID Middleware
@app.middleware("http")
async def security_and_tracing_middleware(request: Request, call_next):
    # Correlation ID
    correlation_id = request.headers.get("X-Correlation-ID") or f"CORR-{secrets.token_hex(8)}"
    start_time = time.time()

    response = await call_next(request)

    # Attach response headers
    duration_ms = int((time.time() - start_time) * 1000)
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

    return response


# 3. Mount Versioned API Routers directly under /api/v1 prefix
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(engagements_router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(completeness_router, prefix="/api/v1")
app.include_router(investigations_router, prefix="/api/v1")
app.include_router(counter_evidence_router, prefix="/api/v1")
app.include_router(human_review_router, prefix="/api/v1")
app.include_router(calculations_router, prefix="/api/v1")
app.include_router(provenance_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(audit_events_router, prefix="/api/v1")
app.include_router(providers_router, prefix="/api/v1")


def generate_openapi_spec():
    """Dumps the live OpenAPI JSON schema to disk for auditing and client generation."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_path = os.path.join(project_root, "docs", "openapi.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(app.openapi(), f, indent=2)
    print(f"OpenAPI contract successfully exported to: {output_path}")


if __name__ == "__main__":
    generate_openapi_spec()
