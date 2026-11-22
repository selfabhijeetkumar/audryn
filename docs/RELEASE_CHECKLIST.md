# AUDRYN — Release Checklist

> Pre-release verification checklist. Complete all items before any deployment.

---

## 1. Code Quality

- [ ] All TypeScript errors resolved (`npm run build` clean)
- [ ] Python linting passes (no syntax errors)
- [ ] No TODO/FIXME items in production paths
- [ ] No hardcoded credentials in source (grep for passwords, API keys)
- [ ] No `console.log` debug statements in production frontend build

## 2. Testing

- [ ] Backend baseline tests pass: `pytest -v` (expected: 191+)
- [ ] Phase 7 integration tests pass: 20/20
- [ ] Phase 8 security tests pass
- [ ] Phase 8 DB integrity tests pass
- [ ] Phase 8 E2E journey tests pass
- [ ] No secrets found in `frontend/dist/` (security scan)
- [ ] Ollama-dependent tests pass (if Ollama available)

## 3. Database

- [ ] Migrations applied cleanly on fresh DB
- [ ] Migration idempotency verified (run twice — no errors)
- [ ] Schema integrity check: all 15 tables present
- [ ] WAL mode confirmed
- [ ] Foreign keys enabled
- [ ] Backup procedure tested and documented
- [ ] Restore from backup tested

## 4. Security

- [ ] Default credentials changed
- [ ] `AUDRYN_SECRET_KEY` set to production value
- [ ] CSRF protection verified
- [ ] Session management tested (login → use → idle timeout → expired)
- [ ] RBAC permissions enforced (test each role)
- [ ] Engagement isolation verified (cross-engagement access denied)
- [ ] File upload restrictions verified (dangerous extensions rejected)
- [ ] Security headers present on all responses
- [ ] No `unsafe-inline` in CSP (or documented justification)
- [ ] `pip-audit` or `safety check` run — no critical vulnerabilities
- [ ] `npm audit` run — no critical vulnerabilities

## 5. Frontend

- [ ] Production build succeeds (`npm run build`)
- [ ] Bundle size acceptable (JS < 1MB gzipped)
- [ ] Self-hosted fonts load correctly (no CDN calls)
- [ ] 3D scene renders on target browsers
- [ ] Responsive breakpoints verified (320px, 390px, 768px, 1440px)
- [ ] Single shared WebGL context confirmed
- [ ] Native OS cursor preserved
- [ ] Brass `#C5A059` used exclusively for Partner APPROVE

## 6. Backend

- [ ] FastAPI starts without errors
- [ ] OpenAPI spec generated and matches implementation
- [ ] All 12 router modules registered
- [ ] Seeded data present (engagement, evidence, findings)
- [ ] All existing backend services integrated correctly
- [ ] Python Decimal engine preserves monetary precision
- [ ] Tax calculations match statutory expectations

## 7. Documentation

- [ ] `docs/ARCHITECTURE.md` — current and accurate
- [ ] `docs/API_DOCUMENTATION.md` — all endpoints listed
- [ ] `docs/AUTHENTICATION_AND_RBAC.md` — complete
- [ ] `docs/DATABASE_SCHEMA.md` — 15 tables documented
- [ ] `docs/SECURITY.md` — honest limitations documented
- [ ] `docs/LOCAL_SETUP_GUIDE.md` — setup verified end-to-end
- [ ] `docs/TESTING_GUIDE.md` — all suites documented
- [ ] `docs/TROUBLESHOOTING.md` — common issues covered
- [ ] `docs/BACKUP_AND_RECOVERY.md` — procedures tested
- [ ] `docs/openapi.json` — matches running server

## 8. Evidence Integrity

- [ ] Three evidence dimensions independent (not merged into single badge)
- [ ] `ReviewVerdict` enum values: SUPPORTED, CONTRADICTED, PARTIALLY_SUPPORTED, UNRESOLVED, INSUFFICIENT_EVIDENCE
- [ ] Hash match ≠ evidence acceptance (explicitly documented)
- [ ] SUPPORTED ≠ cleared/approved/proven (documented)
- [ ] Evidence: Pending Review not represented as existing backend state unless verified

## 9. Product Truth

- [ ] AUDRYN pronounced "AW-drin"
- [ ] Category: "Evidence-First Multi-Agent Financial Audit Intelligence System"
- [ ] Promise: "EVIDENCE BEFORE CONCLUSIONS"
- [ ] Multi-agent: "independent-context challenge" (not "model-independent validation")
- [ ] Same Qwen3:4B base model, separate review contexts
- [ ] Synthetic data labeled as "SYNTHETIC DATA"
- [ ] No claim of zero data egress without network-level verification
- [ ] No claim of full WCAG compliance from automated scan alone
- [ ] PROTOTYPE features clearly labeled

## 10. Final Sign-Off

- [ ] Final consolidated test run captured to file
- [ ] Final completion report generated
- [ ] All blockers documented
- [ ] Owner review completed
