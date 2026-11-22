# AUDRYN — API Documentation

> **OpenAPI Specification:** [`docs/openapi.json`](openapi.json) (60,293 bytes)  
> **Base URL:** `http://localhost:8000/api/v1`  
> **Authentication:** Server-side session cookie + `X-CSRF-Token` header

---

## Endpoint Inventory

### Health
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check + security headers |

### Authentication (`api/auth.py`)
| Method | Path | Auth | CSRF | Description |
|--------|------|------|------|-------------|
| POST | `/auth/login` | No | No | Authenticate and create session |
| POST | `/auth/logout` | Yes | Yes | Destroy session |
| GET | `/auth/me` | Yes | No | Current user identity |

### Engagements (`api/engagements.py`)
| Method | Path | Auth | CSRF | Description |
|--------|------|------|------|-------------|
| GET | `/engagements` | Yes | No | List user's engagements |
| POST | `/engagements` | Yes | Yes | Create engagement |
| GET | `/engagements/{id}` | Yes | No | Get engagement details |
| GET | `/engagements/{id}/members` | Yes | No | List engagement members |
| POST | `/engagements/{id}/members` | Yes | Yes | Add member to engagement |

### Evidence (`api/evidence.py`)
| Method | Path | Auth | CSRF | Description |
|--------|------|------|------|-------------|
| GET | `/engagements/{id}/evidence` | Yes | No | List evidence records |
| POST | `/engagements/{id}/evidence/upload` | Yes | Yes | Upload evidence file |
| GET | `/engagements/{id}/evidence/{eid}` | Yes | No | Get evidence details |
| POST | `/engagements/{id}/evidence/{eid}/verify-hash` | Yes | Yes | Verify SHA-256 hash |
| GET | `/engagements/{id}/evidence/{eid}/download` | Yes | No | Download evidence file |
| POST | `/engagements/{id}/evidence/{eid}/validity` | Yes | Yes | Record validity decision |
| GET | `/engagements/{id}/evidence/{eid}/validity` | Yes | No | Get validity decisions |

### Completeness Gate (`api/completeness.py`)
| Method | Path | Auth | CSRF | Description |
|--------|------|------|------|-------------|
| GET | `/engagements/{id}/completeness` | Yes | No | Evaluate completeness |
| GET | `/engagements/{id}/not-checked` | Yes | No | List not-checked items |
| POST | `/engagements/{id}/not-checked` | Yes | Yes | Add not-checked item |
| PUT | `/engagements/{id}/not-checked/{nid}` | Yes | Yes | Update not-checked item |

### Investigations (`api/investigations.py`)
| Method | Path | Auth | CSRF | Description |
|--------|------|------|------|-------------|
| GET | `/engagements/{id}/investigations/jobs` | Yes | No | List investigation jobs |
| POST | `/engagements/{id}/investigations/run` | Yes | Yes | Trigger investigation |
| GET | `/engagements/{id}/findings` | Yes | No | List findings |
| POST | `/engagements/{id}/findings` | Yes | Yes | Create finding manually |
| GET | `/engagements/{id}/findings/{fid}` | Yes | No | Get finding details |

### Counter-Evidence (`api/counter_evidence.py`)
| Method | Path | Auth | CSRF | Description |
|--------|------|------|------|-------------|
| GET | `/engagements/{id}/counter-evidence` | Yes | No | List challenges |
| POST | `/engagements/{id}/counter-evidence` | Yes | Yes | Submit challenge |

**Canonical ReviewVerdict values:**
`SUPPORTED`, `CONTRADICTED`, `PARTIALLY_SUPPORTED`, `UNRESOLVED`, `INSUFFICIENT_EVIDENCE`

### Human Review (`api/human_review.py`)
| Method | Path | Auth | CSRF | Description |
|--------|------|------|------|-------------|
| GET | `/engagements/{id}/human-review/history` | Yes | No | Review decision history |
| POST | `/engagements/{id}/human-review/decide` | Yes | Yes | Record review decision |

> **[IMPORTANT]** `APPROVE` decisions require `APPROVE_FINDING` permission (Partner role only). The UI renders Partner approvals in Brass (`#C5A059`).

### Calculations (`api/calculations.py`)
| Method | Path | Auth | CSRF | Description |
|--------|------|------|------|-------------|
| GET | `/engagements/{id}/calculations` | Yes | No | List calculation records |
| POST | `/engagements/{id}/calculations/run` | Yes | Yes | Run decimal calculation |
| POST | `/engagements/{id}/tax/section115baa` | Yes | Yes | Section 115BAA corporate tax |
| POST | `/engagements/{id}/tax/section32` | Yes | Yes | Section 32 depreciation |

### Provenance Graph (`api/provenance.py`)
| Method | Path | Auth | CSRF | Description |
|--------|------|------|------|-------------|
| GET | `/engagements/{id}/provenance` | Yes | No | Evidence relationship graph |

### Reports (`api/reports.py`)
| Method | Path | Auth | CSRF | Description |
|--------|------|------|------|-------------|
| GET | `/engagements/{id}/reports/latest` | Yes | No | Latest report |
| POST | `/engagements/{id}/reports/generate` | Yes | Yes | Generate draft report |
| POST | `/engagements/{id}/reports/finalize` | Yes | Yes | Finalize report (Partner) |

### Audit Events (`api/audit_events.py`)
| Method | Path | Auth | CSRF | Description |
|--------|------|------|------|-------------|
| GET | `/engagements/{id}/audit-events` | Yes | No | Engagement audit trail |

---

## Authentication Flow

```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"partner_sharma","password":"AudrynPartnerSecure2026!"}' \
  -c cookies.txt -v
# → 200 OK, Set-Cookie: session_id=..., X-CSRF-Token: <token>

# 2. Authenticated request
curl http://localhost:8000/api/v1/engagements \
  -b cookies.txt

# 3. State-changing request (requires CSRF)
curl -X POST http://localhost:8000/api/v1/engagements/ENG-APEX-FY24/evidence/upload \
  -b cookies.txt \
  -H "X-CSRF-Token: <token>" \
  -F "file=@invoice.pdf" \
  -F "document_type=INVOICE"

# 4. Logout
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -b cookies.txt \
  -H "X-CSRF-Token: <token>"
```

---

## Error Response Format

All errors return JSON:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Not authenticated |
| 403 | Insufficient permissions or engagement access denied |
| 404 | Resource not found |
| 413 | File too large |
| 415 | Unsupported file type |
| 422 | Validation error (Pydantic) |
| 429 | Rate limited (login lockout) |
| 500 | Internal server error |
