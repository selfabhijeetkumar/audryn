# AUDRYN — Database Schema

> **Engine:** SQLite 3 (WAL mode)  
> **Tables:** 15  
> **Migrations:** `backend/db/migrations/`  
> **Runner:** `backend/db/migrate.py` (idempotent, SHA-256 checksum verification)

---

## Entity Relationship Overview

```mermaid
erDiagram
    users {
        TEXT user_id PK
        TEXT username UK
        TEXT password_hash
        TEXT role
        TEXT full_name
        TEXT email
        INTEGER is_active
        TEXT created_at
    }
    sessions {
        TEXT session_id PK
        TEXT user_id FK
        TEXT csrf_token
        TEXT created_at
        TEXT last_activity
        TEXT expires_at
    }
    engagements {
        TEXT engagement_id PK
        TEXT name
        TEXT client_entity
        TEXT financial_year
        TEXT currency
        TEXT status
        TEXT created_by FK
        TEXT created_at
    }
    engagement_members {
        TEXT id PK
        TEXT engagement_id FK
        TEXT user_id FK
        TEXT role_in_engagement
        TEXT added_at
        TEXT added_by
    }
    evidence_records {
        TEXT evidence_id PK
        TEXT engagement_id FK
        TEXT original_filename
        TEXT stored_path
        TEXT document_type
        TEXT sha256_hash
        INTEGER file_size_bytes
        TEXT mime_type
        TEXT uploaded_by FK
        TEXT uploaded_at
    }
    evidence_validity_decisions {
        TEXT decision_id PK
        TEXT evidence_id FK
        TEXT engagement_id FK
        TEXT validity_dimension
        TEXT validity_status
        TEXT reviewer_id FK
        TEXT rationale
        TEXT decided_at
    }
    not_checked_items {
        TEXT item_id PK
        TEXT engagement_id FK
        TEXT description
        TEXT reason
        TEXT added_by FK
        TEXT added_at
        TEXT resolved_at
        TEXT resolved_by
        TEXT status
    }
    investigation_jobs {
        TEXT job_id PK
        TEXT engagement_id FK
        TEXT investigation_type
        TEXT scope
        TEXT status
        TEXT triggered_by FK
        TEXT triggered_at
        TEXT completed_at
        TEXT error_message
    }
    findings {
        TEXT finding_id PK
        TEXT engagement_id FK
        TEXT job_id FK
        TEXT description
        TEXT severity
        TEXT impact_amount
        TEXT observed_variance_inr
        TEXT status
        TEXT created_at
    }
    counter_evidence_challenges {
        TEXT challenge_id PK
        TEXT finding_id FK
        TEXT engagement_id FK
        TEXT submitted_by FK
        TEXT verdict
        TEXT verdict_rationale
        TEXT supporting_evidence_ids
        TEXT submitted_at
    }
    human_reviews {
        TEXT review_id PK
        TEXT finding_id FK
        TEXT engagement_id FK
        TEXT reviewer_id FK
        TEXT reviewer_role
        TEXT decision
        TEXT reason
        TEXT decided_at
    }
    calculation_records {
        TEXT calculation_id PK
        TEXT engagement_id FK
        TEXT calculation_type
        TEXT input_data
        TEXT result_data
        TEXT computed_by FK
        TEXT computed_at
    }
    audit_reports {
        TEXT report_id PK
        TEXT engagement_id FK
        TEXT status
        TEXT generated_by FK
        TEXT generated_at
        TEXT finalized_by
        TEXT finalized_at
        TEXT report_data
        TEXT evidence_manifest
    }
    audit_events {
        TEXT event_id PK
        TEXT engagement_id FK
        TEXT user_id FK
        TEXT action
        TEXT resource_type
        TEXT resource_id
        TEXT details
        TEXT created_at
    }
    schema_migrations {
        TEXT migration_id PK
        TEXT filename
        TEXT checksum
        TEXT applied_at
    }

    users ||--o{ sessions : "has"
    users ||--o{ engagement_members : "belongs to"
    engagements ||--o{ engagement_members : "has"
    engagements ||--o{ evidence_records : "contains"
    engagements ||--o{ not_checked_items : "has"
    engagements ||--o{ investigation_jobs : "has"
    engagements ||--o{ findings : "has"
    engagements ||--o{ calculation_records : "has"
    engagements ||--o{ audit_reports : "has"
    engagements ||--o{ audit_events : "has"
    evidence_records ||--o{ evidence_validity_decisions : "has"
    findings ||--o{ counter_evidence_challenges : "has"
    findings ||--o{ human_reviews : "has"
    investigation_jobs ||--o{ findings : "produces"
```

---

## Table Descriptions

### `users`
Stores auditor accounts. Passwords are stored as PBKDF2-HMAC-SHA256 hashes (never plaintext).  
`role` values: `Associate`, `Senior`, `Manager`, `Partner`.

### `sessions`
Server-side session records. Each login creates a new row.  
Sessions expire by idle timeout (30 min) and absolute timeout (12 hr).  
Logout deletes the row.

### `engagements`
One row per audit engagement. The `engagement_id` (e.g., `ENG-APEX-FY24`) is the primary routing key for all engagement-scoped APIs.

### `engagement_members`
Junction table linking users to engagements with their role in that engagement.  
Drives the `verify_engagement_access` IDOR prevention dependency.

### `evidence_records`
One row per uploaded document. `sha256_hash` is the content fingerprint computed at upload time.  
**Hash match ≠ evidence acceptance** — see `evidence_validity_decisions`.

### `evidence_validity_decisions`
Tracks reviewer decisions across three independent dimensions:
- `CALCULATION_CORRECTNESS`
- `SOURCE_INTEGRITY`
- `EVIDENCE_VALIDITY`

Valid `validity_status` values: `ACCEPTED_FOR_STATED_PURPOSE`, `REJECTED`, `PENDING_REVIEW`, `INSUFFICIENT`.

> **[IMPORTANT]** These three dimensions must remain independent. Never combine them into a single VERIFIED badge.

### `not_checked_items`
Audit items explicitly marked as outside scope or not inspected, with mandatory reasons.

### `investigation_jobs`
Job records for LLM-orchestrated investigation runs.

### `findings`
Anomalies, discrepancies, or issues identified by investigation agents or manually.

### `counter_evidence_challenges`
Challenges submitted against findings. `verdict` must be one of the canonical `ReviewVerdict` values:  
`SUPPORTED`, `CONTRADICTED`, `PARTIALLY_SUPPORTED`, `UNRESOLVED`, `INSUFFICIENT_EVIDENCE`.

### `human_reviews`
Immutable records of human review decisions with reviewer identity, role, reason, and timestamp.  
`APPROVE` decisions by `Partner` role display in Brass (`#C5A059`).

### `calculation_records`
Stores inputs and results of deterministic financial calculations (Python `Decimal` engine).

### `audit_reports`
Draft and finalized audit report records. `evidence_manifest` contains SHA-256 hashes of all evidence referenced in the report.

### `audit_events`
Append-only audit trail. Every significant system action inserts a row.  
Not delete-protected at the DB level — append-only discipline is application-enforced.

### `schema_migrations`
Migration history. Each migration's SQL file content is SHA-256 hashed and stored to detect tampering.

---

## Indexes

Key indexes defined in `001_initial_schema.sql`:

| Table | Index Column(s) |
|-------|----------------|
| `sessions` | `user_id`, `expires_at` |
| `engagement_members` | `(engagement_id, user_id)` UNIQUE |
| `evidence_records` | `engagement_id`, `sha256_hash` |
| `findings` | `engagement_id`, `job_id` |
| `audit_events` | `engagement_id`, `user_id`, `created_at` |

---

## SQLite Configuration

```sql
PRAGMA journal_mode = WAL;        -- Write-Ahead Logging for concurrent reads
PRAGMA foreign_keys = ON;         -- Enforce referential integrity
PRAGMA synchronous = NORMAL;      -- Balance durability vs. performance
PRAGMA busy_timeout = 5000;       -- 5s timeout on locked DB
```
