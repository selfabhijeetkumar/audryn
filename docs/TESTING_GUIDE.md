# AUDRYN — Testing Guide

---

## Test Suite Overview

| Suite | Location | Count | Runner |
|-------|---------|-------|--------|
| Unit — Baseline (Phase 1–6) | `tests/unit/` | 171 | pytest |
| Unit — Phase 7 FastAPI Integration | `tests/unit/test_phase7_fastapi_integration.py` | 20 | pytest |
| Unit — Phase 8 Security | `tests/unit/test_phase8_security.py` | ~30 | pytest |
| Unit — Phase 8 DB Integrity | `tests/unit/test_phase8_db_integrity.py` | ~20 | pytest |
| Integration — Phase 8 E2E Journey | `tests/integration/test_phase8_e2e_journey.py` | 13 | pytest |
| Evaluation — Ollama Capabilities | `tests/evaluation/test_ollama_capabilities.py` | varies | pytest |

---

## Running All Tests

```powershell
Set-Location "C:\FAI AGENT\audryn"
$env:PYTHONPATH = "C:\FAI AGENT\audryn"
& ".\.venv\Scripts\python.exe" -m pytest -v --tb=short
```

**Expected baseline (Phase 7 complete):** 191 passed

---

## Running Specific Suites

```powershell
# Phase 7 integration only
& ".\.venv\Scripts\python.exe" -m pytest tests/unit/test_phase7_fastapi_integration.py -v

# Phase 8 security only
& ".\.venv\Scripts\python.exe" -m pytest tests/unit/test_phase8_security.py -v

# Phase 8 DB integrity only
& ".\.venv\Scripts\python.exe" -m pytest tests/unit/test_phase8_db_integrity.py -v

# Phase 8 E2E journey only
& ".\.venv\Scripts\python.exe" -m pytest tests/integration/test_phase8_e2e_journey.py -v

# All except Ollama-dependent tests
& ".\.venv\Scripts\python.exe" -m pytest -v -k "not ollama"
```

---

## Test Output to File

```powershell
& ".\.venv\Scripts\python.exe" -m pytest -v --tb=short 2>&1 | Tee-Object "docs\test_run_latest.txt"
```

---

## Test Categories

### Phase 7 FastAPI Integration (`test_phase7_fastapi_integration.py`)

Covers all 12 API router modules using `TestClient`:
- Health endpoint + security headers
- Login, CSRF enforcement, session management
- RBAC permission enforcement
- IDOR prevention (cross-engagement access)
- Evidence upload, SHA-256 verify, validity decisions
- Completeness gate evaluation
- Not-checked CRUD
- Investigation run, findings list
- Counter-evidence with canonical ReviewVerdict values
- Human review — UNRESOLVED gate, Partner approval (Brass)
- Decimal financial calculations
- Section 115BAA corporate tax (25.17% effective rate)
- Section 32 depreciation (`total_tax_depreciation` key)
- Provenance graph structure
- Report generation

### Phase 8 Security (`test_phase8_security.py`)

- Security headers on all responses
- Unauthenticated access rejection
- CSRF token enforcement
- XSS payload in evidence filename — stored name must not contain `<script>`
- SQL injection in URL params and login — must not 500 or succeed
- File extension bypass — `.exe`, `.php`, `.js` must be rejected
- IDOR across engagements
- Rate limiting — 7 failed logins must not succeed
- Session logout invalidation
- No password hash in API responses
- No hardcoded credentials in `frontend/dist/`

### Phase 8 DB Integrity (`test_phase8_db_integrity.py`)

- All 15 required tables present after migration
- WAL mode active
- Foreign keys enforced
- Duplicate username rejected (UNIQUE constraint)
- Decimal precision round-trip accuracy
- SHA-256 correctness and idempotency
- SQLite backup API — backup readable, user data preserved
- Transaction rollback behavior

### Phase 8 E2E Journey (`tests/integration/test_phase8_e2e_journey.py`)

12-step synthetic audit workflow:
1. Authenticate as Partner
2. Open seeded engagement ENG-APEX-FY24
3. Upload synthetic evidence PDF
4. Verify SHA-256 hash
5. Evaluate completeness gate
6. Run investigation
7. List findings (verify seeded data)
8. Inspect provenance graph
9. Check counter-evidence canonical verdicts
10. Record human review decision
11. Generate draft report
12. Verify audit event trail
+ Supplemental: Evidence dimensions independence

---

## Prerequisites

- Ollama running with `qwen3:4b` model (for 3 existing tests that call Ollama)
- Production DB migrated (`data/db/audryn.db`)
- Frontend built (`frontend/dist/`) for the "no secrets in dist" security test

---

## Skipped Tests

Some tests are automatically skipped when their prerequisites are not met:
- DB integrity tests skip if `data/db/audryn.db` does not exist
- Security dist scan skips if `frontend/dist/assets/` does not exist
- Tests marked `@pytest.mark.skip` are intentionally deferred

---

## Coverage

Coverage is not enforced but can be measured:

```powershell
pip install pytest-cov
& ".\.venv\Scripts\python.exe" -m pytest --cov=backend --cov-report=html
# View: htmlcov/index.html
```
