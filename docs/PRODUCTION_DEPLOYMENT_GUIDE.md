# AUDRYN — Production Deployment Guide

> **[WARNING]** This document describes deployment topology options for reference. AUDRYN is a local-first application. Production deployment requires security review, penetration testing, and legal compliance review before exposing to any network.

---

## Deployment Options

### Option A: Single-Server (Recommended for Audit Firm Internal Use)

```
┌─────────────────────────────────────────────┐
│  Single Server (Linux / Windows Server)      │
│                                              │
│  ┌────────────┐     ┌────────────────┐      │
│  │  Nginx     │────▶│  Uvicorn       │      │
│  │  (reverse  │     │  (FastAPI app)  │      │
│  │   proxy)   │     │  port 8000     │      │
│  │  port 443  │     └───────┬────────┘      │
│  └────────────┘             │               │
│                     ┌───────▼────────┐      │
│                     │  SQLite WAL    │      │
│                     │  audryn.db     │      │
│                     └────────────────┘      │
│                                              │
│  ┌────────────────┐  ┌───────────────┐      │
│  │  Ollama       │  │  Static Files │      │
│  │  localhost:    │  │  (frontend    │      │
│  │  11434        │  │   dist/)      │      │
│  └────────────────┘  └───────────────┘      │
└─────────────────────────────────────────────┘
```

### Option B: Docker Compose

```yaml
# See docker-compose.yml in project root
services:
  backend:
    build: .
    ports: ["8000:8000"]
    volumes: ["./data:/app/data"]
  ollama:
    image: ollama/ollama
    ports: ["11434:11434"]
```

---

## Pre-Deployment Checklist

### Security
- [ ] Generate production `AUDRYN_SECRET_KEY` (256-bit random hex)
- [ ] Change default `partner_sharma` password
- [ ] Enable HTTPS with valid TLS certificate
- [ ] Add `Strict-Transport-Security` header
- [ ] Configure CORS to production domain only
- [ ] Implement persistent rate limiting (Redis or DB-backed)
- [ ] Enable `Secure` flag on session cookie
- [ ] Review CSP headers — eliminate any `unsafe-inline`
- [ ] Run `pip-audit` and `npm audit`
- [ ] Penetration test completed

### Database
- [ ] Apply all migrations
- [ ] Verify WAL mode: `PRAGMA journal_mode`
- [ ] Configure automated backups (daily minimum)
- [ ] Test backup + restore procedure

### Network
- [ ] Ollama exposed only on loopback or via private network
- [ ] No unintended external egress (verify with network monitoring)
- [ ] Firewall rules: only ports 443 (HTTPS) and 11434 (Ollama loopback)

### Legal
- [ ] DPDP 2025 compliance review completed
- [ ] Data processing agreement in place if processing personal data
- [ ] Data retention policy documented
- [ ] Audit trail retention meets regulatory requirements

---

## Nginx Configuration Example

```nginx
server {
    listen 443 ssl http2;
    server_name audryn.internal.firm.example;

    ssl_certificate     /etc/ssl/certs/audryn.crt;
    ssl_certificate_key /etc/ssl/private/audryn.key;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend static files
    location / {
        root /opt/audryn/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }
}
```

---

## Uvicorn Production Configuration

```bash
uvicorn backend.app.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 4 \
  --log-level warning \
  --access-log \
  --no-use-colors
```

> **[NOTE]** Use `--host 127.0.0.1` (not `0.0.0.0`) when behind a reverse proxy.

---

## Monitoring

| Metric | Endpoint | Expected |
|--------|---------|----------|
| Health | `GET /api/v1/health` | `200 OK` |
| DB size | `ls -la data/db/audryn.db` | Grows with usage |
| Evidence disk | `du -sh data/evidence/` | Monitor for capacity |
| Process | `ps aux | grep uvicorn` | Workers running |

---

## This Is NOT Production-Ready

> **[CAUTION]** The following items remain unimplemented and are required for genuine production deployment:

| Item | Status |
|------|--------|
| HTTPS enforcement | Requires TLS certificate + reverse proxy |
| Persistent rate limiting | In-memory only |
| Email notifications / password reset | Not implemented |
| MFA / TOTP | Not implemented |
| External audit log forwarding (SIEM) | Not implemented |
| Database connection pooling | SQLite single-writer limitation |
| Horizontal scaling | SQLite does not support multi-server writes |
| Automated testing in CI/CD | No pipeline configured |
| Container image scanning | Not performed |
