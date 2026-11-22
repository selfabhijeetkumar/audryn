# AUDRYN — Migration Guide

---

## Overview

AUDRYN uses an idempotent SQL migration runner (`backend/db/migrate.py`) that:

- Tracks applied migrations in the `schema_migrations` table
- Verifies each migration's SHA-256 checksum before re-applying
- Skips already-applied migrations (idempotent)
- Applies new migrations in filename order

---

## Running Migrations

### Standard Run

```powershell
Set-Location "C:\FAI AGENT\audryn"
$env:PYTHONPATH = "C:\FAI AGENT\audryn"
& ".\.venv\Scripts\python.exe" -m backend.db.migrate
```

### On a Non-Default DB Path

```powershell
$env:AUDRYN_DB_PATH = "path\to\other.db"
& ".\.venv\Scripts\python.exe" -m backend.db.migrate
```

### Verify Migration State

```powershell
& ".\.venv\Scripts\python.exe" -c "
import sqlite3
conn = sqlite3.connect('data/db/audryn.db')
rows = conn.execute('SELECT filename, applied_at FROM schema_migrations ORDER BY applied_at').fetchall()
for r in rows: print(r)
conn.close()
"
```

---

## Migration File Format

Migration files live in `backend/db/migrations/` and must follow the naming convention:

```
NNN_description.sql
```

Example: `001_initial_schema.sql`, `002_add_engagement_tags.sql`

Migrations are applied in ascending lexicographic order.

---

## Creating a New Migration

1. Create a new file in `backend/db/migrations/`:

```sql
-- 002_add_engagement_tags.sql
-- Description: Add tags column to engagements table

ALTER TABLE engagements ADD COLUMN tags TEXT DEFAULT '[]';
```

2. Run migrations:

```powershell
& ".\.venv\Scripts\python.exe" -m backend.db.migrate
```

3. Verify:

```powershell
& ".\.venv\Scripts\python.exe" -c "
import sqlite3; conn = sqlite3.connect('data/db/audryn.db')
print(conn.execute('PRAGMA table_info(engagements)').fetchall())
conn.close()
"
```

---

## Backup Before Migration

> **[IMPORTANT]** Always back up the database before applying new migrations.

```powershell
# PowerShell backup using SQLite backup API
& ".\.venv\Scripts\python.exe" -c "
import sqlite3, datetime
src = 'data/db/audryn.db'
dst = f'data/db/audryn_backup_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.db'
source = sqlite3.connect(src)
dest = sqlite3.connect(dst)
source.backup(dest)
dest.close(); source.close()
print(f'Backup created: {dst}')
"
```

---

## Rollback

SQLite does not support transactional DDL rollback for `CREATE TABLE`. If a migration fails mid-way:

1. Restore from backup:

```powershell
Copy-Item data\db\audryn_backup_YYYYMMDD_HHMMSS.db data\db\audryn.db -Force
```

2. Fix the migration SQL file.
3. Re-run migrations.

> **[WARNING]** Never delete rows from `schema_migrations` manually — the checksum verification will reject re-application of a migration whose checksum changed.

---

## Testing Migrations on a Disposable DB

```powershell
$env:PYTHONPATH = "C:\FAI AGENT\audryn"
$env:AUDRYN_DB_PATH = "data\db\test_migration.db"
& ".\.venv\Scripts\python.exe" -m backend.db.migrate
# Inspect, test...
Remove-Item "data\db\test_migration.db" -Force
```
