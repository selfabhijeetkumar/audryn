# AUDRYN — Report Generation & Release Gate Architecture

> **Document Type:** System Architecture Specification  
> **Component:** Report Generation Engine & Statutory Release Gates  
> **Modules:** `backend/services/report_generation_service.py`, `backend/services/pdf_report_service.py`, `backend/services/release_gate_service.py`  
> **Status:** ACTIVE & PRODUCTION-GRADE  
> **Output Formats:** Machine-Readable JSON & Publication-Grade PDF (ReportLab 5.1.0)

---

## 1. Architectural Motivation & Principles

In traditional LLM-assisted systems, report generation often consists of feeding text into a generative model and asking it to write an audit summary. This approach is catastrophic for statutory auditing because LLMs routinely hallucinate numbers, invent non-existent findings, smooth over critical variances, and drop provenance links.

AUDRYN implements **deterministic, data-grounded report synthesis**:
1. **Zero LLM Arithmetic:** Every monetary amount, variance figure, tax rate, and percentage displayed in the report is pulled directly from persisted Python `Decimal` calculation records.
2. **Immutable Structured Schema:** Reports are structured into 12 mandatory sections defined by Pydantic models.
3. **Statutory Release Gate:** A report cannot transition to `FINALIZED` unless an automated gate verifies that mandatory evidence is present, critical gaps are resolved, and all material findings have terminal auditor decisions.
4. **Cryptographic Tamper Detection:** Every report computes a deterministic SHA-256 hash of its logical contents. Modifying even a single character in the company name or finding description invalidates the content hash.
5. **Historical Versioning:** Regenerating a report increments its version number and preserves all historical drafts and releases in SQLite.

---

## 2. Report Generation Pipeline

```
Persisted Audit Records (Evidence, Ledgers, Calculations, Findings, Reviews, Gaps)
                                 │
                                 ▼
                     [ReleaseGateService.evaluate()]
                                 │
              ┌──────────────────┴──────────────────┐
              ▼                                     ▼
      Blockers Detected                     All Conditions Met
       (Gate FAILS)                           (Gate PASSES)
              │                                     │
              ▼                                     ▼
     Status: BLOCKED                      Status: REVIEW_READY
              │                                     │
              └──────────────┬──────────────────────┘
                             ▼
            [ReportGenerationService.generate_report()]
              ├── Builds 12 Structured Sections
              ├── Computes SHA-256 Content Hash
              ├── Assembles Report Manifest
              └── Persists to data/reports/audryn_reports.db
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
       [JSON Export]              [PdfReportService]
   Machine-Readable Output       Publication-Grade PDF
                                (data/reports/pdf/*.pdf)
                                            │
                                            ▼
                           [finalize_report()] (Auditor Action)
                                   Status: FINALIZED
```

---

## 3. Report Status Lifecycle

| Report Status | Operational Definition | Release Permitted? |
|---|---|---|
| **DRAFT** | Initial working snapshot during active investigation. Contains prominent watermark. | Internal Working Copy Only |
| **BLOCKED** | Release is blocked because mandatory evidence is missing/corrupted, critical gaps exist, or findings remain unreviewed. | Strictly Blocked |
| **REVIEW_READY**| All mandatory documents present, all material findings reviewed, and zero critical blockers exist. Awaits auditor release signoff. | Ready for Auditor Release |
| **FINALIZED** | Terminal, released state approved by an auditor. Immutable; cannot be modified or re-finalized. | Released Statutory Report |

---

## 4. Release Gate Rules (`ReleaseGateService`)

The `ReleaseGateService` applies strict deterministic criteria:

1. **Completeness Gate Check:** If `completeness_status == "BLOCKED"`, report release is blocked (`COMPLETENESS_GATE_BLOCKED`).
2. **Evidence Integrity Check:** Any evidence record with extraction status `CORRUPTED` or `FAILED` generates a blocking violation (`CORRUPTED_EVIDENCE` / `FAILED_EXTRACTION`).
3. **Open Material Findings:** Any finding with severity `HIGH` or `CRITICAL` whose status is `OPEN` generates a blocking violation (`CRITICAL_UNRESOLVED_FINDING`).
4. **Human Review Status:** If human review status is `PENDING` or `ESCALATED`, release is blocked (`PENDING_HUMAN_REVIEW` / `ESCALATED_FINDING`).
5. **Critical Gaps:** Any GAP RADAR entry with severity `CRITICAL` not marked `RESOLVED` blocks release (`INCOMPLETE_PROCEDURE`).
6. **Not-Checked Disclosures:** Procedures marked `NOT_STARTED` or `BLOCKED` in the Not-Checked Register do **not** block release if disclosed; they are recorded as warnings and transparently published in the report.

---

## 5. Report Manifest & Reproducibility

Every generated report includes an immutable `ReportManifest` capturing:
- `report_id`: Unique identifier formatted as `RPT-{audit_id}-{timestamp}`.
- `report_version`: Sequential integer version (1, 2, 3...).
- `generated_at_utc`: ISO-8601 UTC timestamp.
- `evidence_document_count`: Total documents processed.
- `evidence_sha256_manifest`: Ordered list of SHA-256 hashes for all examined evidence documents.
- `finding_ids`: List of all finding IDs included in the report.
- `rulebook_version`: Statutory tax rulebook version applied (e.g. `Income-tax Act, 1961`).
- `financial_periods`: Financial years covered (e.g. `["FY2023-24", "FY2024-25"]`).
- `report_content_hash`: Deterministic SHA-256 hash of the complete logical content.

---

## 6. Output Formats

### 6.1 Machine-Readable JSON Export
Exported via `report_service.export_json(report)`. Adheres to the formal Pydantic data contract, enabling seamless ingestion into downstream enterprise ERPs, tax preparation software, or regulatory portals.

### 6.2 Human-Readable PDF Export (`PdfReportService`)
Built on Python standard-library compatible **ReportLab 5.1.0** without external headless browser or NodeJS dependencies:
- **Status Header & Callout Banner:** Color-coded status box (Red for BLOCKED, Gold for REVIEW_READY/DRAFT, Blue for FINALIZED).
- **Synthetic Data Disclaimer:** Prominent alert box stating that data is synthetic when `is_synthetic_data == True`.
- **Structured Sections:** Complete 12 sections with clear typography and clean horizontal rules.
- **Formatted Tables:** Findings, evidence documents, and reconciliations rendered as styled ReportLab tables with alternating rows and bold headers.
- **Cryptographic Stamp:** Footer displaying the exact SHA-256 content hash and verification status.
- **Path Traversal Defense:** Sanitizes all target filenames via `os.path.basename` to prevent directory traversal.
