# AUDRYN — Changelog

---

## V2.1 Phase 8 — Production Hardening & Release Readiness

**Date:** 2026-11-23

### Added
- **Phase 8 Security Test Suite** (`tests/unit/test_phase8_security.py`)
  - Security headers verification
  - Unauthenticated access rejection
  - CSRF enforcement tests
  - XSS payload sanitization (evidence filename, query string)
  - SQL injection resistance (URL params, login)
  - File extension bypass prevention (.exe, .php, .js)
  - IDOR cross-engagement access prevention
  - Rate limiting / login lockout verification
  - Session management (logout invalidation, no hash exposure)
  - Secrets-in-dist scanner (no credentials in frontend build)

- **Phase 8 DB Integrity Test Suite** (`tests/unit/test_phase8_db_integrity.py`)
  - Schema integrity: all 15 tables present after migration
  - WAL mode active on production DB
  - Foreign key enforcement enabled
  - UNIQUE constraint enforcement (duplicate username rejected)
  - Duplicate evidence hash detection
  - Transaction rollback behavior
  - Decimal precision preservation round-trip
  - SHA-256 correctness and idempotency
  - SQLite backup API: backup readable, user data preserved

- **Phase 8 E2E Audit Journey** (`tests/integration/test_phase8_e2e_journey.py`)
  - 12-step synthetic audit: authenticate → upload → verify → completeness → investigate → findings → provenance → counter-evidence → human review → report → audit trail
  - Three-dimension evidence independence supplemental test

- **Documentation** (15 files in `docs/`)
  - `ARCHITECTURE.md` — System architecture with mermaid diagrams
  - `API_DOCUMENTATION.md` — Complete endpoint inventory (40+ endpoints)
  - `AUTHENTICATION_AND_RBAC.md` — Auth flow, PBKDF2, 4 roles × 25 permissions
  - `DATABASE_SCHEMA.md` — 15-table ER diagram and descriptions
  - `SECURITY.md` — Controls and known limitations
  - `DATA_FLOW_AND_PRIVACY.md` — Data flows, egress analysis, DPDP 2025
  - `LOCAL_SETUP_GUIDE.md` — Full local setup instructions
  - `MIGRATION_GUIDE.md` — Migration runner usage, backup, rollback
  - `TESTING_GUIDE.md` — All test suites documented
  - `BACKUP_AND_RECOVERY.md` — SQLite backup API, verification, restore
  - `TROUBLESHOOTING.md` — Common issues and fixes
  - `PRODUCTION_DEPLOYMENT_GUIDE.md` — Deployment topology options
  - `RELEASE_CHECKLIST.md` — Pre-release verification checklist
  - `CHANGELOG.md` — This file

- **Deployment Infrastructure**
  - `Dockerfile` — Python 3.13-slim container
  - `docker-compose.yml` — Backend + Ollama services
  - `scripts/start_backend.ps1` — Backend startup script
  - `scripts/start_frontend.ps1` — Frontend dev startup script
  - `scripts/run_tests.ps1` — Full test suite runner

### Changed
- `frontend/src/services/api.ts` — Added `uploadEvidence()` public method (replaced private `request[]` accessor in AppShell)
- `frontend/src/pages/app/AppShell.tsx` — Uses `api.uploadEvidence()` instead of `api['request'](...)`

### Fixed
- AppShell private method access: `api['request']` → `api.uploadEvidence()` (TypeScript encapsulation)

---

## V2.1 Phase 7 — Production Backend Integration

**Date:** 2026-11-22

### Added
- **Database Layer**
  - 15-table SQLite schema (`backend/db/migrations/001_initial_schema.sql`)
  - `DatabaseManager` with WAL mode (`backend/db/connection.py`)
  - Idempotent migration runner with SHA-256 checksum (`backend/db/migrate.py`)
  - 9 repository classes (`backend/db/repositories.py`)

- **Authentication & Authorization**
  - PBKDF2-HMAC-SHA256 password hashing (600K iterations)
  - Server-side session management with httpOnly cookie
  - CSRF token propagation and verification
  - Rate limiting (5 attempts → 15-minute lockout)
  - 4-role RBAC with 25 permissions (`backend/app/rbac.py`)

- **Engagement Isolation**
  - `EngagementIsolationService` with IDOR prevention (`backend/app/isolation.py`)

- **12 FastAPI Router Modules** (40+ endpoints)
  - health, auth, engagements, evidence, completeness, investigations, counter_evidence, human_review, calculations, provenance, reports, audit_events

- **Frontend API Client** (`frontend/src/services/api.ts`)
  - Typed HTTP client with CSRF propagation
  - 11 workflow area coverage

- **Frontend Integration** (`frontend/src/pages/app/AppShell.tsx`)
  - Real backend API calls with graceful fallback to fixtures
  - Backend connection status badge
  - Live sync button

- **Phase 7 Integration Tests** (20/20 passed)
- **OpenAPI Specification** (`docs/openapi.json` — 60,293 bytes)

### Test Results
- Backend baseline: 171/171 passed
- Phase 7 integration: 20/20 passed
- Combined: 191/191 passed (279.48s)
- Frontend build: clean (0 errors)

---

## V2.1 Phases 1–6 — Core Backend + Frontend Implementation

**Date:** 2026-11-22

### Core Backend Services
- Multi-agent audit orchestration (LangGraph + CrewAI)
- Evidence ingestion and SHA-256 verification
- Deterministic Financial Engine (Python Decimal)
- Indian Tax Rulebook Service (Section 115BAA, Section 32)
- Completeness Gate Service
- Counter-Evidence Service with ReviewVerdict enum
- Human Review Service
- Report Generation Service
- Adversarial Lab

### Frontend
- React 18 + TypeScript application
- Three.js 3D Ledger Folio scene with 7-chapter scroll
- GSAP animation system
- Tailwind CSS responsive design (320px–1440px)
- 11 workspace navigation
- Accessibility compliance (WCAG 2.2 AA target)
