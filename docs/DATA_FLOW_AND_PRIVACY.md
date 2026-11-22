# AUDRYN — Data Flow and Privacy

> **[IMPORTANT]** This document describes data flows as observed through code inspection. Network-level verification was not performed.

---

## Data Categories

| Category | Examples | Storage |
|----------|---------|---------|
| Credentials | Username, password hash | SQLite `users` table |
| Session data | Session ID, CSRF token, timestamps | SQLite `sessions` table |
| Client financial data | Evidence documents, amounts | SQLite + `data/evidence/` filesystem |
| Audit findings | Anomalies, variances | SQLite `findings` table |
| Human decisions | Review decisions with identity | SQLite `human_reviews` table |
| Calculation inputs/results | Tax inputs, depreciation | SQLite `calculation_records` table |
| Audit reports | Draft and final reports | SQLite `audit_reports` table |
| LLM context | Evidence text sent to agents | Transient — Ollama loopback |
| Audit trail | Action log | SQLite `audit_events` table |

---

## Data Flow Diagrams

### Evidence Ingestion

```
User Browser
    │  multipart/form-data (file + document_type)
    ▼
FastAPI (localhost:8000)
    │  Validate type, compute SHA-256
    │  Store file: data/evidence/{uuid}.{ext}
    ▼
SQLite: evidence_records
    (evidence_id, sha256_hash, original_filename, stored_path, ...)
    │
    │  SEPARATE from validity decision
    ▼
SQLite: evidence_validity_decisions
    (validity_dimension, validity_status, rationale, reviewer_id, ...)
```

### LLM Inference Flow

```
Investigation trigger (API)
    │
    ▼
LangGraph Orchestrator (Python process)
    │  HTTP POST to localhost:11434 (loopback only)
    │  Request: { model: "qwen3:4b", messages: [...] }
    ▼
Ollama (local daemon, port 11434)
    │  Qwen3:4B model running locally
    │  No data leaves the machine (loopback)
    ▼
Response → stored in SQLite investigation_jobs / findings
```

> **[NOTE]** If an operator configures an external Ollama endpoint or cloud LLM API, evidence text would be transmitted externally. The code supports this configuration; it is not the default.

### Report Generation

```
POST /reports/generate
    │
    ▼
ReportRepository.create_report()
    │  Collects: findings, evidence records, counter-evidence,
    │            not-checked items, human review decisions
    │  Builds evidence_manifest (SHA-256 of each evidence item)
    ▼
SQLite: audit_reports
    (report_data JSON, evidence_manifest JSON, status=DRAFT)
    │
POST /reports/finalize (Partner only)
    │
    ▼
SQLite: audit_reports.status = FINALIZED
    (finalized_by, finalized_at recorded)
```

---

## Egress Analysis

> **[CAUTION]** This analysis is based on static code inspection only. It does NOT constitute a verified zero-egress claim.

| Traffic | Destination | Assessment |
|---------|-------------|-----------|
| LLM inference | `127.0.0.1:11434` | Loopback — no external egress |
| Frontend dev proxy | `localhost:8000` | Loopback |
| Fonts (IBM Plex Sans/Mono, Newsreader) | Self-hosted in `frontend/public/fonts/` | No CDN calls |
| External APIs | None found in codebase | Not called by default config |
| External network | Unknown | **Not packet-capture verified** |

---

## Data Retention

| Data | Retention | Deletion Mechanism |
|------|-----------|------------------|
| Evidence files | Until manually removed | Filesystem deletion |
| Evidence records | Until manually removed | SQL DELETE (application-level) |
| Sessions | Until expired or logout | Automatic: expired sessions inactive |
| Audit events | Indefinite | No automated deletion |
| Reports | Indefinite | No automated deletion |

---

## Privacy Considerations (DPDP 2025 Relevance)

> **[IMPORTANT]** AUDRYN processes financial data of client entities. Personal data may be present in evidence documents (e.g., employee names in payroll records). Legal review is required before processing personal data subject to India's Digital Personal Data Protection Act, 2023, and the DPDP Rules, 2025 (notified 13 November 2025).

Key considerations:

1. **Data Principal Rights** — The system does not currently implement mechanisms for data principals to access, correct, or erase their data processed within audit evidence.

2. **Data Fiduciary Obligations** — The deploying organization (audit firm) is likely the Data Fiduciary. Compliance obligations under DPDP Rules 2025 must be assessed by qualified legal counsel.

3. **Cross-Border Transfers** — If Ollama is configured to use a cloud endpoint, evidence text may cross borders. The default loopback configuration avoids this.

4. **Commencement Schedule** — DPDP Rules 2025 were notified on 13 November 2025. Phased commencement timelines must be tracked against official Gazette notifications. Legal review required for applicable provisions.

> This system does not constitute legal advice. Obtain independent legal review before processing personal data under DPDP.
