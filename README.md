# AUDRYN (V2.1 Production Baseline)

> **Category:** Evidence-First Multi-Agent Financial Audit Intelligence System  
> **Promise:** EVIDENCE BEFORE CONCLUSIONS  
> **Pronunciation:** AW-drin  
> **Automated Verification:** 269 / 269 Tests Passing (100% Success)  
> **Live Frontend (Vercel):** [https://frontend-chi-nine-98.vercel.app/app](https://frontend-chi-nine-98.vercel.app/app)  
> **Live Backend API (Render):** [https://audryn-api.onrender.com](https://audryn-api.onrender.com)  
> **Live API Health Check:** [https://audryn-api.onrender.com/api/v1/health](https://audryn-api.onrender.com/api/v1/health)  
> **Live Swagger API Docs:** [https://audryn-api.onrender.com/docs](https://audryn-api.onrender.com/docs)  

---

## Executive Summary

AUDRYN is a specialized financial audit intelligence workstation engineering a verifiable, evidence-first pipeline for statutory financial audits under the Indian regulatory regime (Companies Act, 2013, Income Computation and Disclosure Standards, and the Indian Income Tax Act, 1961).

Unlike standard conversational AI systems, AUDRYN enforces a strict non-hallucinatory standard: **every calculation is deterministically evaluated using arbitrary-precision decimal mathematics**, **every evidence document is cryptographic-hash anchored (SHA-256)**, **every multi-agent challenge operates under adversarial review**, and **inference is resilient across four local and cloud providers with automatic circuit-breaker failover**.

---

## Key Pillars & Safeguards

1. **Independent Verification Dimensions**
   - **Calculation Correctness:** Validated via deterministic Python `Decimal` engine (e.g., Section 115BAA corporate tax, Section 32 block asset depreciation).
   - **Source Integrity:** Cryptographic SHA-256 fingerprinting at ingestion.
   - **Evidence Validity:** Separate human auditor acceptance state (`ACCEPTED_FOR_STATED_PURPOSE`, `REJECTED`, `PENDING_REVIEW`, `INSUFFICIENT`).
   - *These three dimensions are never merged into a single generic "VERIFIED" badge.*

2. **Multi-Agent Challenge Architecture**
   - Agents (LangGraph, CrewAI) operate in **isolated execution contexts** with distinct review mandates.
   - All agents utilize local inference (`qwen3:4b` on loopback `127.0.0.1:11434`).
   - *Accurately characterized as independent-context challenge, not model-independent validation.*

3. **Strict RBAC & Segregation of Duties**
   - 4-Tier Roles: `Associate`, `Senior`, `Manager`, `Partner`.
   - 25 Fine-Grained Permissions.
   - Partner-exclusive privilege for finding approval (styled in distinctive Brass `#C5A059`) and audit report finalization.

4. **Zero-Egress by Design**
   - Local Ollama inference without cloud gateway dependencies.
   - Self-hosted typography (Newsreader, IBM Plex Sans, IBM Plex Mono) without external CDN requests.
   - Complete engagement-level tenant isolation preventing cross-audit data leakage.

---

## Repository Structure

```
audryn/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application, lifespan, middleware
│   │   ├── auth.py                 # PBKDF2 auth, session lifecycle, CSRF, rate-limit
│   │   ├── rbac.py                 # Role & Permission enums, permission matrix
│   │   ├── isolation.py            # Engagement isolation & IDOR prevention
│   │   └── api/                    # 12 REST API router modules (40+ endpoints)
│   ├── db/
│   │   ├── connection.py           # SQLite WAL connection manager
│   │   ├── migrate.py              # Idempotent migration runner (SHA-256 verified)
│   │   ├── migrations/             # 001_initial_schema.sql (15 tables)
│   │   └── repositories.py         # 9 domain repositories
│   └── services/                   # Pre-existing core audit and calculation services
├── frontend/
│   ├── src/
│   │   ├── pages/app/AppShell.tsx  # Interactive audit workstation (11 workspaces)
│   │   ├── services/api.ts         # Typed API client with auto-CSRF propagation
│   │   ├── components/             # 3D Folio scene, canvas, widgets
│   │   └── types/                  # TypeScript domain models
│   └── dist/                       # Production frontend build
├── docs/                           # 15+ comprehensive documentation specifications
│   ├── openapi.json                # Complete OpenAPI v3 schema (60 KB)
│   ├── ARCHITECTURE.md             # System & data flow architecture
│   ├── API_DOCUMENTATION.md        # Endpoint inventory and contracts
│   ├── AUTHENTICATION_AND_RBAC.md  # Security controls and permission matrix
│   ├── DATABASE_SCHEMA.md          # 15-table relational schema & ER diagrams
│   └── ...                         # Security, deployment, testing, and privacy guides
├── scripts/                        # Automated launch and testing scripts
│   ├── start_backend.ps1           # Starts FastAPI uvicorn daemon
│   ├── start_frontend.ps1          # Launches Vite development server
│   └── run_tests.ps1               # Autonomous test runner
├── tests/
│   ├── unit/                       # Unit tests (baseline + Phase 7 + Phase 8)
│   └── integration/                # End-to-end synthetic audit journey tests
├── data/
│   ├── db/audryn.db                # SQLite WAL database
│   └── evidence/                   # Ingested evidence files
├── Dockerfile                      # Production container spec (Python 3.13-slim)
└── docker-compose.yml              # Local orchestration (Backend + Ollama)
```

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.13+
- Node.js 20+
- Ollama (running locally with `qwen3:4b` pulled)

### 1. Initialize Backend & Database
```powershell
Set-Location "C:\FAI AGENT\audryn"
$env:PYTHONPATH = "C:\FAI AGENT\audryn"

# Apply migrations
& ".\.venv\Scripts\python.exe" -m backend.db.migrate

# Start Backend Server
.\scripts\start_backend.ps1 -Reload
```
Backend will be available at: `http://localhost:8000` (OpenAPI docs: `http://localhost:8000/docs`).

### 2. Launch Frontend Workstation
```powershell
.\scripts\start_frontend.ps1
```
Workstation will open at: `http://localhost:5173`.

### 3. Demo Account Access
- **Partner Account:** `partner_sharma` / `AudrynPartnerSecure2026!`
- **Default Engagement:** `ENG-APEX-FY24` (Apex Industrial Tech Ltd, FY 2023-24)

---

## Testing & Verification

Run the comprehensive test suite spanning unit, security, database integrity, and integration workflows:

```powershell
.\scripts\run_tests.ps1 -Suite all -Verbose
```

Specific test targets:
- `.\scripts\run_tests.ps1 -Suite phase7` (FastAPI integration suite: 20/20)
- `.\scripts\run_tests.ps1 -Suite phase8-security` (Security hardening suite)
- `.\scripts\run_tests.ps1 -Suite phase8-db` (Database integrity & WAL tests)
- `.\scripts\run_tests.ps1 -Suite phase8-e2e` (12-step synthetic audit journey)

---

## License & Compliance Note
All synthetic audit records, companies, and transactions are generated purely for validation and demonstration purposes. Review [DATA_FLOW_AND_PRIVACY.md](docs/DATA_FLOW_AND_PRIVACY.md) and [SECURITY.md](docs/SECURITY.md) before production evaluation.
