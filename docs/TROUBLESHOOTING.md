# AUDRYN — Troubleshooting Guide

---

## Backend Won't Start

### `ModuleNotFoundError: No module named 'backend'`

**Cause:** `PYTHONPATH` not set.

**Fix:**
```powershell
$env:PYTHONPATH = "C:\FAI AGENT\audryn"
& ".\.venv\Scripts\uvicorn.exe" backend.app.main:app --port 8000
```

### `sqlite3.OperationalError: no such table: users`

**Cause:** Migrations not applied.

**Fix:**
```powershell
$env:PYTHONPATH = "C:\FAI AGENT\audryn"
& ".\.venv\Scripts\python.exe" -m backend.db.migrate
```

### `Address already in use` on port 8000

**Fix:**
```powershell
netstat -ano | findstr :8000
# Find the PID and kill it:
taskkill /PID <PID> /F
```

---

## Authentication Issues

### `401 Unauthorized` on all requests after login

**Cause:** Session cookie not being sent (browser security policy or `credentials: 'include'` missing).

**Fix:** Ensure the frontend uses `credentials: 'include'` in all fetch calls. The `AudrynApiClient` in `api.ts` does this by default.

### `403 Forbidden` on CSRF-protected endpoints

**Cause:** `X-CSRF-Token` header not sent or stale.

**Fix:** The `AudrynApiClient` automatically propagates the CSRF token. If calling the API directly:
```
POST /api/v1/auth/login → capture X-CSRF-Token from response header
Include X-CSRF-Token: <token> on all POST/PUT/DELETE requests
```

### Account locked out

**Cause:** 5+ failed login attempts.

**Wait** 15 minutes, or restart the backend process (in-memory lockout resets on restart).

---

## Frontend Issues

### `npm run dev` — `vite: command not found`

**Fix:**
```powershell
Set-Location "C:\FAI AGENT\audryn\frontend"
npm install
npm run dev
```

### TypeScript build errors

```powershell
Set-Location "C:\FAI AGENT\audryn\frontend"
npm run build 2>&1
```

Check for type errors in `src/types/index.ts` if adding new backend response fields.

### 3D scene not rendering

**Cause:** WebGL context not supported or second canvas conflict.

**Check:** Open browser DevTools → Console. Look for `WebGL context lost` errors.

**Fix:** The application uses a single shared WebGL context. If a second `<canvas>` element is present, remove it.

---

## Test Failures

### `pytest: command not found`

```powershell
& "C:\FAI AGENT\audryn\.venv\Scripts\python.exe" -m pytest -v
```

### Tests fail with `Connection refused` to Ollama

**Cause:** Ollama not running or `qwen3:4b` not pulled.

**Fix:**
```powershell
ollama serve  # (or start Ollama app)
ollama pull qwen3:4b
```

**Alternative:** Skip Ollama-dependent tests:
```powershell
& ".\.venv\Scripts\python.exe" -m pytest -v -k "not ollama"
```

### `test_phase8_db_integrity.py` skipped

**Cause:** `data/db/audryn.db` not found.

**Fix:** Apply migrations:
```powershell
$env:PYTHONPATH = "C:\FAI AGENT\audryn"
& ".\.venv\Scripts\python.exe" -m backend.db.migrate
```

### `test_phase8_security.py::TestNoSecretsInBuild` skipped

**Cause:** `frontend/dist/` not built.

**Fix:**
```powershell
Set-Location "C:\FAI AGENT\audryn\frontend"
npm run build
```

---

## Database Issues

### `database is locked`

**Cause:** Multiple connections or a long transaction holding a write lock.

**Fix:** Ensure only one write process at a time. The `DatabaseManager` uses `busy_timeout=5000` (5 seconds). Check for stuck processes:
```powershell
Get-Process python
```

### Corrupted database

**Fix:** Restore from backup. See [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md).

```powershell
& ".\.venv\Scripts\python.exe" -c "
import sqlite3
conn = sqlite3.connect('data/db/audryn.db')
result = conn.execute('PRAGMA integrity_check').fetchone()
print(result)
conn.close()
"
# 'ok' = healthy; anything else = corrupted
```

---

## Evidence Upload Issues

### `415 Unsupported Media Type` on upload

**Cause:** File extension or MIME type not in allowlist.

**Allowed types:** `.pdf`, `.xlsx`, `.xls`, `.csv`, `.png`, `.jpg`, `.jpeg`, `.json`, `.txt`

### Uploaded file not found on disk

**Check:** `data/evidence/` directory exists and is writable.

```powershell
Test-Path "C:\FAI AGENT\audryn\data\evidence"
# If False:
New-Item -ItemType Directory "C:\FAI AGENT\audryn\data\evidence" -Force
```
