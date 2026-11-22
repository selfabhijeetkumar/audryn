# AUDRYN — Backup and Recovery

---

## Backup Scope

| Component | Backup Required | Method |
|-----------|----------------|--------|
| `data/db/audryn.db` | **Yes — primary** | SQLite backup API or file copy (WAL mode) |
| `data/evidence/` | Yes — uploaded files | File system copy |
| `data/reports/` | Yes — legacy reports | File system copy |
| `.env` | Yes — configuration | Secure vault |
| `backend/db/migrations/` | Yes — schema history | Source control |
| `frontend/dist/` | Rebuild from source | `npm run build` |

---

## Database Backup

### Method 1: SQLite Backup API (Recommended)

```powershell
& "C:\FAI AGENT\audryn\.venv\Scripts\python.exe" -c "
import sqlite3, datetime
src = 'C:/FAI AGENT/audryn/data/db/audryn.db'
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
dst = f'C:/FAI AGENT/audryn/data/db/audryn_backup_{ts}.db'
source = sqlite3.connect(src)
dest = sqlite3.connect(dst)
source.backup(dest)
dest.close()
source.close()
print(f'Backup created: {dst}')
"
```

This method is safe while the database is live (uses WAL checkpointing).

### Method 2: File Copy (Only When Backend is Stopped)

```powershell
# Stop backend first, then:
Copy-Item "data\db\audryn.db" "data\db\audryn_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

> **[WARNING]** Copying the file while the database is open may produce a corrupt backup. Use Method 1 for live backups.

---

## Evidence Files Backup

```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$src = "C:\FAI AGENT\audryn\data\evidence"
$dst = "C:\FAI AGENT\audryn\data\evidence_backup_$ts"
Copy-Item $src $dst -Recurse
```

---

## Verifying a Backup

```powershell
& "C:\FAI AGENT\audryn\.venv\Scripts\python.exe" -c "
import sqlite3
conn = sqlite3.connect('data/db/audryn_backup_YYYYMMDD_HHMMSS.db')
tables = conn.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE type='table'\").fetchone()[0]
users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
engagements = conn.execute('SELECT COUNT(*) FROM engagements').fetchone()[0]
evidence = conn.execute('SELECT COUNT(*) FROM evidence_records').fetchone()[0]
conn.close()
print(f'Tables: {tables}, Users: {users}, Engagements: {engagements}, Evidence: {evidence}')
"
```

---

## Restore Procedure

### From SQLite Backup

```powershell
# 1. Stop the backend application
# 2. Replace the production DB with the backup
Copy-Item "data\db\audryn_backup_YYYYMMDD_HHMMSS.db" "data\db\audryn.db" -Force
# 3. Apply any pending migrations (safe — idempotent)
$env:PYTHONPATH = "C:\FAI AGENT\audryn"
& ".\.venv\Scripts\python.exe" -m backend.db.migrate
# 4. Restart the backend
```

### Evidence Files

```powershell
# Replace the evidence directory with the backup
Remove-Item "data\evidence" -Recurse -Force
Copy-Item "data\evidence_backup_YYYYMMDD_HHMMSS" "data\evidence" -Recurse
```

---

## Scheduled Backup (Recommended)

Create a scheduled task or cron-equivalent to run the backup script daily:

```powershell
# backup_script.ps1
$env:PYTHONPATH = "C:\FAI AGENT\audryn"
& "C:\FAI AGENT\audryn\.venv\Scripts\python.exe" -c "
import sqlite3, datetime, os
src = 'C:/FAI AGENT/audryn/data/db/audryn.db'
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
dst = f'C:/FAI AGENT/audryn/data/db/audryn_backup_{ts}.db'
source = sqlite3.connect(src)
dest = sqlite3.connect(dst)
source.backup(dest)
dest.close(); source.close()
print(f'Backup: {dst}')
"
```

---

## Retention Policy (Recommended)

Keep backups for 90 days. Remove older files:

```powershell
Get-ChildItem "data\db\audryn_backup_*.db" |
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-90) } |
  Remove-Item
```
