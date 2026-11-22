# AUDRYN — Security Controls and Limitations

> **[CAUTION]** This document is a candid record of security controls and known gaps. It must be reviewed by a qualified security professional before any production deployment.

---

## Implemented Security Controls

### Authentication
| Control | Implementation | Notes |
|---------|---------------|-------|
| Password hashing | PBKDF2-HMAC-SHA256, 600K iterations | OWASP-compliant parameters |
| Session storage | Server-side SQLite `sessions` table | No JWT exposure to client |
| Session cookie | `HttpOnly; SameSite=Lax; Path=/` | Prevents JS access |
| Idle timeout | 30 minutes | Configurable |
| Absolute timeout | 12 hours | Configurable |
| Rate limiting | 5 attempts → 15 min lockout | **In-memory only** |
| Login brute force | Lockout per username | Resets on restart |

### CSRF
| Control | Implementation |
|---------|---------------|
| Token generation | `secrets.token_urlsafe(32)` per session |
| Token verification | Required on all state-changing HTTP methods |
| Token rotation | Rotated in every response header |
| Defense-in-depth | SameSite=Lax cookie attribute |

### Authorization
| Control | Implementation |
|---------|---------------|
| RBAC | 4 roles, 25 permissions, enforced via FastAPI Depends |
| Engagement isolation | `engagement_members` table, `verify_engagement_access` on every route |
| IDOR prevention | 404 (not 403) for non-existent engagement IDs |

### Input Validation
| Control | Implementation |
|---------|---------------|
| File type allowlist | Extension + MIME type check on upload |
| Pydantic validation | All request bodies validated via Pydantic models |
| Path traversal | Evidence stored by UUID, not original filename |
| SQL injection | SQLAlchemy parameterized queries + sqlite3 `?` placeholders |

### Transport
| Control | Implementation |
|---------|---------------|
| Security headers | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` |
| CORS | Restricted to `localhost:5173`, `localhost:4173` |
| CDN dependencies | None — all fonts self-hosted |

### Data Integrity
| Control | Implementation |
|---------|---------------|
| Evidence SHA-256 | Computed at upload, stored in DB |
| Hash verification API | `POST /evidence/{id}/verify-hash` |
| Three independent evidence dimensions | Calculation Correctness / Source Integrity / Evidence Validity — never merged |
| Audit trail | Append-only `audit_events` table |

---

## Known Security Limitations

> **[WARNING]** The following gaps must be addressed before production deployment.

| Gap | Risk | Mitigation Path |
|----|------|----------------|
| In-memory rate limiting | Brute force survives restart | Redis or DB-backed counter |
| No HSTS | Requires HTTPS enforcement | Add `Strict-Transport-Security` header + HTTPS |
| No password reset | Account recovery impossible without admin | Implement email-based reset with time-limited tokens |
| No MFA / TOTP | Single-factor auth only | Add TOTP via `pyotp` |
| Audit log not append-only at DB level | Admin can delete events | Use PostgreSQL with trigger-protected audit table or external SIEM |
| Session secret not rotatable without logout-all | Long-lived sessions persist if secret leaks | Implement session version field |
| No refresh token rotation | Sessions use fixed identifiers | Implement token rotation on each request |
| `unsafe-inline` in some script contexts | XSS risk if injected | Migrate to nonce-based CSP (requires server-side nonce injection) |
| File upload size not enforced at middleware level | Potential DoS | Add `ContentSizeLimitMiddleware` |

---

## Data Egress Profile

> **[IMPORTANT]** The following is based on code-level inspection only. Network-level packet capture was **not performed**.

| Destination | Purpose | Status |
|-------------|---------|--------|
| `127.0.0.1:11434` | Ollama LLM inference | Loopback — no external egress |
| None | External APIs | No external API calls found in code |
| None | CDN / font providers | Self-hosted fonts — no CDN calls |
| **External network** | **Unknown — not packet-captured** | **Unverified** |

> **Never claim zero data egress without OS-level network monitoring confirmation.**

---

## Penetration Testing Checklist (Pre-Production)

Before any production deployment, conduct or commission testing of:

- [ ] Authentication bypass attempts
- [ ] CSRF token theft and replay
- [ ] Session fixation and hijacking
- [ ] IDOR across engagements
- [ ] File upload: malicious content, extension bypass, path traversal
- [ ] SQL injection in all parameterized inputs
- [ ] XSS via all user-controlled inputs
- [ ] Rate limiting effectiveness under distributed attack
- [ ] Dependency vulnerability scan (`pip-audit`, `npm audit`)
- [ ] Secrets in source code and build artifacts
- [ ] Network egress verification (packet capture)
