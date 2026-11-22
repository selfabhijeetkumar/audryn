# AUDRYN — Local Setup Guide

> **Prerequisites:** Python 3.13+, Node.js 20+, Ollama (optional — required for LLM agents)

---

## Quick Start

### 1. Clone / Navigate to Project

```powershell
Set-Location "C:\FAI AGENT\audryn"
```

### 2. Create Python Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Set Environment Variables

Create a `.env` file in the project root (this file is **not** committed to source control):

```env
# Required — change before first run
AUDRYN_SECRET_KEY=change-this-to-a-random-256-bit-hex-value

# Optional — defaults shown
AUDRYN_DB_PATH=data/db/audryn.db
AUDRYN_EVIDENCE_DIR=data/evidence
AUDRYN_SESSION_IDLE_MINUTES=30
AUDRYN_SESSION_ABSOLUTE_HOURS=12
AUDRYN_CORS_ORIGINS=http://localhost:5173,http://localhost:4173
```

> **[IMPORTANT]** Generate `AUDRYN_SECRET_KEY` with:  
> ```powershell
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 4. Apply Database Migrations

```powershell
$env:PYTHONPATH = "C:\FAI AGENT\audryn"
& ".\.venv\Scripts\python.exe" -m backend.db.migrate
```

Expected output:
```
Applying migration 001_initial_schema.sql ... OK
Migration complete. 1 migration(s) applied.
```

### 5. Bootstrap Admin User

```powershell
$env:PYTHONPATH = "C:\FAI AGENT\audryn"
& ".\.venv\Scripts\python.exe" -m backend.app.bootstrap_admin --username admin --role Partner
# Enter password at prompt
```

> **[NOTE]** The application auto-bootstraps `partner_sharma` with a default password on first startup when no users exist. Change this password immediately in any non-demo environment.

### 6. Start the Backend

```powershell
$env:PYTHONPATH = "C:\FAI AGENT\audryn"
& ".\.venv\Scripts\uvicorn.exe" backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API is now available at: `http://localhost:8000`  
OpenAPI docs: `http://localhost:8000/docs`

### 7. Start the Frontend

```powershell
Set-Location "C:\FAI AGENT\audryn\frontend"
npm install
npm run dev
```

The application is now available at: `http://localhost:5173`

---

## Ollama Setup (Optional — Required for LLM Agent Features)

```powershell
# Install Ollama from https://ollama.com
# Then pull the model:
ollama pull qwen3:4b

# Verify:
ollama list
# Should show: qwen3:4b
```

> **[NOTE]** Without Ollama, investigation agents return stub responses. All other backend features (evidence ingestion, calculations, human review, reports) function normally.

---

## Default Demo Credentials

| Username | Password | Role |
|---------|---------|------|
| `partner_sharma` | `AudrynPartnerSecure2026!` | Partner |

> **[CAUTION]** These credentials are seeded for demonstration only. Change them before any non-demo use.

---

## Running Tests

```powershell
Set-Location "C:\FAI AGENT\audryn"
$env:PYTHONPATH = "C:\FAI AGENT\audryn"
& ".\.venv\Scripts\python.exe" -m pytest -v
```

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for full test suite documentation.

---

## Directory Permissions

Ensure the following directories are writable by the application process:

```
data/db/          # SQLite database
data/evidence/    # Uploaded evidence files
data/reports/     # Generated reports (legacy service)
logs/             # Application logs (if enabled)
```
