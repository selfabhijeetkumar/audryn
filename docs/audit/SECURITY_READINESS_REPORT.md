# Security Readiness Report — AUDRYN
**Date:** 2026-11-22  
**Audit Class:** Inspection-only | No modifications made  
**Scope:** `c:\FAI AGENT\` workspace + Antigravity configuration

> [!CAUTION]
> This report contains security risk findings. Sensitive values have been REDACTED. No actual secrets are printed in this document.

---

## 1. Environment File Exposure

### Finding
No `.env`, `.env.local`, or `.env.*` files were found in `c:\FAI AGENT\`.

**Status:** NOT APPLICABLE (no application code exists yet)

### Risk for AUDRYN Implementation
When AUDRYN development begins, environment variable handling must be established before the first commit. Required:
- `.env.example` with placeholder keys (committed)
- `.env` with real values (gitignored)
- Python `python-dotenv` for loading (already installed: `1.2.3`)

---

## 2. API Key Storage in MCP Configuration Files

### Finding (HIGH RISK)
Real API keys and tokens are stored in **plaintext** in multiple machine-local JSON files:

| File | Contains | Risk |
|------|----------|------|
| `~/.gemini/antigravity-ide/mcp_config.json` | Stitch API key (REDACTED), Supabase token (REDACTED) | HIGH |
| `~/.gemini/config/mcp_config.json` | Stitch API key (REDACTED, different key), Supabase token (REDACTED) | HIGH |
| `~/.gemini/antigravity/mcp_config.json` | Stitch API key (REDACTED), Supabase token (REDACTED) | HIGH |

**Specific observation:** The Stitch MCP configuration contains two **different** API keys across different config files. This may indicate key rotation was performed but old config was not updated, or multiple API keys are in use.

### Mitigation Assessment
- These files are machine-local and not inside any git-tracked directory → **not at risk of being committed**
- If the user's machine is compromised, all keys are exposed
- No additional mitigation is available within audit scope
- **Action (not implemented here):** Consider using OS credential store or environment variables for MCP key configuration when that feature becomes available in Antigravity

---

## 3. Git Repository Status

### Finding
The workspace root `c:\FAI AGENT` has **no git repository**.

**Status:** NOT APPLICABLE (no git history to audit)

The only git repo is `c:\FAI AGENT\gemini-web2api\` — inspected separately.

### gemini-web2api Git Security
- `config.json` is in `.gitignore` ✅
- `cookie.txt` / `cookie.json` / `gemini-auth.json` are in `.gitignore` ✅  
- No `.env` files found in the directory ✅
- `config.example.json` present (safe template) ✅

No credential exposure found in the gemini-web2api repository.

---

## 4. gemini-web2api Security Assessment

### Configuration
- Server binds to `0.0.0.0:8081` (all network interfaces)
- This exposes the Gemini API proxy to the local network
- **Risk:** If running on a shared network, other devices could use this proxy

### Authentication
- No authentication middleware visible in `server.py` (inspection only — not read fully)
- Intended as a local developer tool — acceptable for local dev, not production

---

## 5. Placeholder Credentials in MCP Config (settings.json)

### Finding (MEDIUM RISK)
`~/.gemini/settings.json` contains MCP configurations with placeholder/dummy credentials:

| MCP | Credential Field | Value (REDACTED) | Risk |
|-----|-----------------|-----------------|------|
| fast-context | WINDSURF_API_KEY | Single character placeholder | LOW — not functional |
| grok-search | TAVILY_API_KEY, GROK_API_KEY, FIRECRAWL_API_KEY | Single character placeholder | LOW — not functional |
| ace-tool | --base-url, --token | Single character placeholder | LOW — not functional |

These will silently fail to connect. They do not expose real credentials.

---

## 6. AUDRYN-Specific Security Requirements (Pre-Implementation Checklist)

### Must implement before first commit

| Security Control | Priority | Notes |
|-----------------|----------|-------|
| `.gitignore` with `.env`, `*.env*`, `config.json`, `*.key`, `*.pem` | CRITICAL | Must be first file committed |
| `python-dotenv` for all secrets | CRITICAL | Already installed |
| `pydantic-settings` for config validation | HIGH | Already installed |
| Input validation on all document uploads | CRITICAL | PDF, Excel path traversal risk |
| File type validation (magic bytes, not extension) | CRITICAL | Malicious file upload vector |
| Supabase Row Level Security (RLS) policies | HIGH | Per-audit isolation |
| API endpoint authentication (JWT) | HIGH | `PyJWT` already installed |
| CORS configuration | HIGH | `fastapi` already installed |
| Rate limiting | MEDIUM | Available via FastAPI middleware |
| XSS protection | MEDIUM | Input sanitization on report generation |
| Security headers | MEDIUM | X-Frame-Options, CSP, HSTS |

### Dependency Security Audit Status
| Check | Status | Notes |
|-------|--------|-------|
| `pip audit` capability | NOT VERIFIED — `pip-audit` not installed | Install for dependency CVE scanning |
| `safety` package | NOT INSTALLED | Alternative CVE scanner |
| `bandit` (Python SAST) | NOT INSTALLED | Static analysis for security issues |
| Secret scanning tool | NOT INSTALLED | `detect-secrets` or `git-secrets` |

> [!WARNING]
> Before the AUDRYN repository's first push to any remote, run `pip install pip-audit && pip-audit` to scan all installed dependencies for known CVEs. The existing pip package list contains several packages that may have known vulnerabilities (torch 2.6.0, openai 2.12.0 should be verified).

---

## 7. Code Review Graph

### Finding
`.code-review-graph/graph.db` exists and contains code structure metadata.

- `.gitignore` correctly excludes `*` (everything) in this directory ✅
- Database contains absolute file paths — machine-specific, not sensitive
- **Status:** ACCEPTABLE

---

## 8. Security Risk Summary

| Risk | Severity | Status | Action Required |
|------|----------|--------|----------------|
| API keys in MCP config plaintext | MEDIUM | EXISTING — machine-local only | Monitor; use env vars when Antigravity supports it |
| gemini-web2api binds 0.0.0.0 | LOW | EXISTING | Acceptable for local dev |
| No .gitignore for AUDRYN project | CRITICAL | NOT YET APPLICABLE | Must create before first commit |
| No dependency security scanner | MEDIUM | NOT INSTALLED | Install pip-audit before first push |
| No SAST tool | LOW | NOT INSTALLED | Install bandit during CI setup phase |
| Python 3.13 security patches | LOW | Current | Python 3.13.15 is current release |
| PyJWT installed | POSITIVE | v2.15.1 | Use for AUDRYN API authentication |
| cryptography installed | POSITIVE | v46.0.6 | Current, no known CVEs at time of audit |
| python-dotenv installed | POSITIVE | v1.2.3 | Use for all secret management |

---

*Report generated: 2026-11-22 | Inspection-only | No secrets printed | No files modified*
