# AUDRYN — Authentication and RBAC

---

## Authentication Architecture

AUDRYN uses a **server-side session** architecture with no JWT tokens issued to the client.

### Password Hashing

| Parameter | Value |
|-----------|-------|
| Algorithm | PBKDF2-HMAC-SHA256 |
| Iterations | 600,000 (NIST SP 800-132 compliant) |
| Salt | 32 bytes, `os.urandom()` |
| Implementation | Python stdlib `hashlib.pbkdf2_hmac` |

> **[NOTE]** `passlib` and `bcrypt` are **not** installed in this environment. The stdlib implementation meets OWASP recommended parameters for PBKDF2.

### Session Lifecycle

```
Login → session_id generated (secrets.token_urlsafe(32))
      → stored in DB: sessions table (session_id, user_id, created_at, last_activity, expires_at)
      → Set-Cookie: session_id=<value>; HttpOnly; SameSite=Lax; Path=/
      → X-CSRF-Token: <token> in response header

Request → Cookie verified → session_id looked up in DB
        → idle timeout: last_activity + 30min
        → absolute timeout: created_at + 12hr
        → Both checks must pass

Logout → DELETE FROM sessions WHERE session_id=?
       → Cookie cleared (Max-Age=0)
```

### CSRF Protection

- CSRF token is generated on login and stored server-side in the session record.
- All `POST`, `PUT`, `DELETE`, `PATCH` requests must include `X-CSRF-Token: <token>` header.
- The token is rotated on each response in the `X-CSRF-Token` response header.
- SameSite=Lax provides defense-in-depth against CSRF.

### Rate Limiting

- **Threshold:** 5 consecutive failed login attempts per username
- **Lockout duration:** 15 minutes
- **Storage:** In-memory (resets on process restart)

> **[WARNING]** In-memory rate limiting does not persist across server restarts. For production, implement Redis or DB-backed rate limiting.

---

## Role-Based Access Control

### Roles

| Role | Description |
|------|-------------|
| `Associate` | Junior auditor — read and upload access |
| `Senior` | Senior auditor — can run investigations and submit counter-evidence |
| `Manager` | Audit manager — can make human review decisions and generate reports |
| `Partner` | Engagement partner — can approve findings (Brass `#C5A059`) and finalize reports |

### Permissions (25 Total)

```python
class Permission(str, Enum):
    # Evidence
    VIEW_EVIDENCE = "view_evidence"
    UPLOAD_EVIDENCE = "upload_evidence"
    VERIFY_HASH = "verify_hash"
    RECORD_VALIDITY_DECISION = "record_validity_decision"
    VIEW_VALIDITY_DECISIONS = "view_validity_decisions"
    
    # Engagements
    VIEW_ENGAGEMENT = "view_engagement"
    CREATE_ENGAGEMENT = "create_engagement"
    MANAGE_ENGAGEMENTS = "manage_engagements"
    ADD_MEMBERS = "add_members"
    
    # Investigations & Findings
    RUN_INVESTIGATION = "run_investigation"
    VIEW_FINDINGS = "view_findings"
    SUBMIT_COUNTER_EVIDENCE = "submit_counter_evidence"
    VIEW_COUNTER_EVIDENCE = "view_counter_evidence"
    
    # Human Review
    HUMAN_REVIEW_DECIDE = "human_review_decide"
    APPROVE_FINDING = "approve_finding"  # Partner only — Brass color
    VIEW_HUMAN_REVIEW_HISTORY = "view_human_review_history"
    
    # Completeness
    VIEW_COMPLETENESS = "view_completeness"
    MANAGE_NOT_CHECKED = "manage_not_checked"
    
    # Calculations
    RUN_CALCULATION = "run_calculation"
    VIEW_CALCULATIONS = "view_calculations"
    
    # Reports
    GENERATE_REPORT = "generate_report"
    FINALIZE_REPORT = "finalize_report"  # Partner only
    VIEW_REPORTS = "view_reports"
    
    # Audit Trail
    VIEW_AUDIT_EVENTS = "view_audit_events"
    
    # Provenance
    VIEW_PROVENANCE = "view_provenance"
```

### FastAPI Dependency Usage

```python
# Require authentication only
@router.get("/endpoint")
async def endpoint(user = Depends(get_current_user)):
    ...

# Require specific permission
@router.post("/endpoint")
async def endpoint(
    user = Depends(require_permission(Permission.UPLOAD_EVIDENCE))
):
    ...

# Require engagement membership + permission
@router.get("/engagements/{engagement_id}/evidence")
async def list_evidence(
    engagement_id: str,
    user = Depends(require_permission(Permission.VIEW_EVIDENCE)),
    engagement = Depends(verify_engagement_access),
):
    ...
```

---

## Engagement Isolation

Every engagement route uses `verify_engagement_access`, which:

1. Checks `engagement_members` table: `SELECT * WHERE engagement_id=? AND user_id=?`
2. Returns `HTTP 404` (not 403) for non-existent engagements to prevent engagement ID enumeration
3. Returns `HTTP 403` for authenticated users who lack membership

This prevents IDOR (Insecure Direct Object Reference) attacks across engagements.

---

## Security Limitations (Known)

| Limitation | Status |
|-----------|--------|
| Password reset via email | NOT IMPLEMENTED — requires email service |
| MFA / TOTP | NOT IMPLEMENTED |
| HSTS | Requires HTTPS — not applicable for local dev |
| Persistent rate limiting | In-memory only — resets on restart |
| Audit log tamper-proofing | Events stored in SQLite — no append-only guarantee |
| Token rotation on privilege escalation | NOT IMPLEMENTED |
