-- ==============================================================================
-- AUDRYN Phase 7/8 Initial Database Schema (SQLite with WAL & Strict Foreign Keys)
-- Migration: 001_initial_schema.sql
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- Migration Tracker
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT NOT NULL
);

-- Users
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Associate', 'Senior', 'Manager', 'Partner')),
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions (Server-side Session Management)
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    csrf_token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- Engagements
CREATE TABLE IF NOT EXISTS engagements (
    engagement_id TEXT PRIMARY KEY,
    entity_name TEXT NOT NULL,
    cin TEXT NOT NULL,
    fiscal_year TEXT NOT NULL,
    assessment_year TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'INR',
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'COMPLETED', 'ARCHIVED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Engagement Team Members (Authorization & Isolation)
CREATE TABLE IF NOT EXISTS engagement_members (
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('Associate', 'Senior', 'Manager', 'Partner')),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (engagement_id, user_id)
);

-- Evidence Records
CREATE TABLE IF NOT EXISTS evidence_records (
    evidence_id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    document_type TEXT NOT NULL DEFAULT 'UNKNOWN',
    extraction_status TEXT NOT NULL DEFAULT 'PENDING',
    page_count INTEGER NOT NULL DEFAULT 0,
    raw_storage_path TEXT,
    uploaded_by TEXT NOT NULL REFERENCES users(user_id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_evidence_engagement ON evidence_records(engagement_id);
CREATE INDEX IF NOT EXISTS idx_evidence_hash ON evidence_records(sha256_hash);

-- Scoped Human Evidence Acceptance Workflow
CREATE TABLE IF NOT EXISTS evidence_validity_decisions (
    decision_id TEXT PRIMARY KEY,
    evidence_id TEXT NOT NULL REFERENCES evidence_records(evidence_id) ON DELETE CASCADE,
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    reviewer_id TEXT NOT NULL REFERENCES users(user_id),
    reviewer_role TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING_REVIEW', 'ACCEPTED_FOR_STATED_PURPOSE', 'REJECTED', 'DISPUTED', 'INSUFFICIENT_EVIDENCE')),
    purpose_scope TEXT NOT NULL,
    rationale TEXT NOT NULL,
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_validity_engagement ON evidence_validity_decisions(engagement_id);

-- Not-Checked Register Items
CREATE TABLE IF NOT EXISTS not_checked_items (
    procedure_id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    audit_area TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'NOT_CHECKED',
    reason_not_checked TEXT,
    mitigating_notes TEXT,
    assigned_reviewer TEXT NOT NULL DEFAULT 'Unassigned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_not_checked_engagement ON not_checked_items(engagement_id);

-- Investigation Execution Jobs (Durable job persistence)
CREATE TABLE IF NOT EXISTS investigation_jobs (
    job_id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'QUEUED' CHECK(status IN ('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    progress INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    triggered_by TEXT NOT NULL REFERENCES users(user_id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_investigation_jobs_engagement ON investigation_jobs(engagement_id);

-- Findings
CREATE TABLE IF NOT EXISTS findings (
    finding_id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    impact_amount TEXT NOT NULL DEFAULT '0.00',
    currency TEXT NOT NULL DEFAULT 'INR',
    source_evidence_ids_json TEXT NOT NULL DEFAULT '[]',
    coordinates_json TEXT NOT NULL DEFAULT '{}',
    agent_role TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_findings_engagement ON findings(engagement_id);

-- Counter-Evidence Challenges
CREATE TABLE IF NOT EXISTS counter_evidence_challenges (
    challenge_id TEXT PRIMARY KEY,
    finding_id TEXT NOT NULL REFERENCES findings(finding_id) ON DELETE CASCADE,
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    original_hypothesis TEXT NOT NULL,
    supporting_evidence_json TEXT NOT NULL DEFAULT '[]',
    contradictory_evidence_json TEXT NOT NULL DEFAULT '[]',
    alternative_explanations_json TEXT NOT NULL DEFAULT '[]',
    calculation_verification TEXT NOT NULL,
    reviewer_role TEXT NOT NULL,
    reviewer_verdict TEXT NOT NULL CHECK(reviewer_verdict IN ('SUPPORTED', 'CONTRADICTED', 'PARTIALLY_SUPPORTED', 'UNRESOLVED', 'INSUFFICIENT_EVIDENCE')),
    verdict_rationale TEXT NOT NULL,
    requires_escalation INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_counter_evidence_engagement ON counter_evidence_challenges(engagement_id);

-- Human Reviews (Immutable Audit Trail)
CREATE TABLE IF NOT EXISTS human_reviews (
    review_id TEXT PRIMARY KEY,
    audit_id TEXT NOT NULL,
    finding_id TEXT NOT NULL REFERENCES findings(finding_id) ON DELETE CASCADE,
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    reviewer_id TEXT NOT NULL REFERENCES users(user_id),
    reviewer_name TEXT NOT NULL,
    reviewer_role TEXT NOT NULL,
    reviewer_membership_no TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('APPROVED', 'REJECTED', 'REQUEST_EVIDENCE', 'ESCALATED')),
    comments TEXT NOT NULL,
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_human_reviews_engagement ON human_reviews(engagement_id);

-- Calculation Records (Deterministic Decimal Math)
CREATE TABLE IF NOT EXISTS calculation_records (
    calculation_id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    calculation_name TEXT NOT NULL,
    statutory_section TEXT,
    method TEXT NOT NULL,
    input_values_json TEXT NOT NULL DEFAULT '{}',
    result TEXT NOT NULL,
    variance TEXT,
    is_verified INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_calculation_records_engagement ON calculation_records(engagement_id);

-- Audit Reports & Manifests
CREATE TABLE IF NOT EXISTS audit_reports (
    report_id TEXT PRIMARY KEY,
    audit_id TEXT NOT NULL,
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    report_version INTEGER NOT NULL DEFAULT 1,
    report_status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(report_status IN ('BLOCKED', 'DRAFT', 'REVIEW_READY', 'FINALIZED')),
    company_name TEXT NOT NULL,
    financial_periods_json TEXT NOT NULL DEFAULT '[]',
    report_content_hash TEXT,
    manifest_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_reports_engagement ON audit_reports(engagement_id);

-- Append-Only Audit Event Log
CREATE TABLE IF NOT EXISTS audit_events (
    event_id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    event_type TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_events_engagement ON audit_events(engagement_id);
