# AUDRYN — Statutory Audit Report Schema Specification

> **Document Type:** Data Contract & JSON Schema Specification  
> **Component:** Report Data Contract  
> **Module:** `backend/models/report.py`  
> **Status:** ACTIVE & PRODUCTION-GRADE  
> **Format:** JSON Schema (Draft 2020-12 Compatible)

---

## 1. Overview & Data Invariants

The AUDRYN `AuditReport` data contract defines the complete machine-readable representation of a statutory financial audit report. 

### Core Data Invariants:
1. **Zero LLM Arithmetic:** All figures, variances, and percentages are formatted string representations of Python `Decimal` values (`ROUND_HALF_UP`, 2 decimal places).
2. **Deterministic Content Hashing:** The `report_content_hash` field contains a SHA-256 digest of the canonical logical report content.
3. **Mandatory 12 Sections:** Every report contains exactly 12 structured sections in standard chronological order.
4. **Traceable Manifest:** The `manifest` sub-object explicitly catalogs all evidence document SHA-256 hashes, finding IDs, and the governing statutory rulebook version.
5. **Synthetic Data Disclosure:** When `is_synthetic_data == true`, the report must include explicit synthetic warnings across the cover, executive summary, and limitations sections.

---

## 2. Top-Level Entity Schema (`AuditReport`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AuditReport",
  "type": "object",
  "required": [
    "report_id",
    "audit_id",
    "report_version",
    "report_status",
    "generated_at_utc",
    "company_name",
    "company_id",
    "financial_periods",
    "currency",
    "is_synthetic_data",
    "sections",
    "manifest",
    "release_gate_result",
    "report_content_hash"
  ],
  "properties": {
    "report_id": {
      "type": "string",
      "description": "Unique identifier formatted as RPT-{audit_id}-{timestamp}"
    },
    "audit_id": {
      "type": "string",
      "description": "Unique audit engagement identifier (e.g. AUD-2024-001)"
    },
    "report_version": {
      "type": "integer",
      "minimum": 1,
      "description": "Monotonically increasing version number for this report_id"
    },
    "report_status": {
      "type": "string",
      "enum": ["DRAFT", "BLOCKED", "REVIEW_READY", "FINALIZED"]
    },
    "generated_at_utc": {
      "type": "string",
      "format": "date-time"
    },
    "company_name": {
      "type": "string"
    },
    "company_id": {
      "type": "string",
      "description": "Corporate Identity Number (CIN) or registration number"
    },
    "financial_periods": {
      "type": "array",
      "items": { "type": "string" }
    },
    "currency": {
      "type": "string",
      "default": "INR"
    },
    "is_synthetic_data": {
      "type": "boolean"
    },
    "synthetic_disclaimer": {
      "type": "string"
    },
    "sections": {
      "type": "array",
      "items": { "$ref": "#/$defs/ReportSection" }
    },
    "manifest": {
      "$ref": "#/$defs/ReportManifest"
    },
    "release_gate_result": {
      "$ref": "#/$defs/ReleaseGateResult"
    },
    "report_content_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    }
  },
  "$defs": {
    "ReportSection": {
      "type": "object",
      "required": ["section_id", "section_type", "title", "content"],
      "properties": {
        "section_id": { "type": "string" },
        "section_type": {
          "type": "string",
          "enum": [
            "COVER",
            "EXECUTIVE_SUMMARY",
            "SCOPE_AND_METHODOLOGY",
            "EVIDENCE_INVENTORY",
            "FINANCIAL_RECONCILIATION",
            "AUDIT_FINDINGS",
            "COUNTER_EVIDENCE_ANALYSIS",
            "GAP_RADAR_COMPLETENESS",
            "HUMAN_REVIEW_REGISTER",
            "NOT_CHECKED_REGISTER",
            "RULEBOOK_TAX_METHODOLOGY",
            "LIMITATIONS_DISCLAIMERS",
            "APPENDICES"
          ]
        },
        "title": { "type": "string" },
        "content": { "type": "object" },
        "finding_references": {
          "type": "array",
          "items": { "type": "string" }
        },
        "evidence_references": {
          "type": "array",
          "items": { "type": "string" }
        },
        "source_hash_references": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "ReportManifest": {
      "type": "object",
      "required": [
        "report_id",
        "audit_id",
        "report_version",
        "generated_at_utc",
        "evidence_document_count",
        "evidence_sha256_manifest",
        "finding_count",
        "finding_ids",
        "rulebook_version",
        "financial_periods"
      ],
      "properties": {
        "report_id": { "type": "string" },
        "audit_id": { "type": "string" },
        "report_version": { "type": "integer" },
        "generated_at_utc": { "type": "string", "format": "date-time" },
        "evidence_document_count": { "type": "integer" },
        "evidence_sha256_manifest": {
          "type": "array",
          "items": { "type": "string", "pattern": "^[a-f0-9]{64}$" }
        },
        "finding_count": { "type": "integer" },
        "finding_ids": { "type": "array", "items": { "type": "string" } },
        "rulebook_version": { "type": "string" },
        "financial_periods": { "type": "array", "items": { "type": "string" } },
        "data_snapshot_ref": { "type": ["string", "null"] },
        "report_content_hash": { "type": ["string", "null"] }
      }
    },
    "ReleaseGateResult": {
      "type": "object",
      "required": ["passed", "status", "blockers", "warnings"],
      "properties": {
        "passed": { "type": "boolean" },
        "status": { "type": "string" },
        "blockers": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["reason", "detail"],
            "properties": {
              "reason": { "type": "string" },
              "detail": { "type": "string" }
            }
          }
        },
        "warnings": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["reason", "detail"],
            "properties": {
              "reason": { "type": "string" },
              "detail": { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

---

## 3. Mandatory Report Sections Breakdown

| Section Type | Mandatory Keys in `content` | Description |
|---|---|---|
| **COVER** | `report_id`, `audit_id`, `company_name`, `company_id`, `financial_periods`, `report_status` | Formal title block, entity identity, and generation metadata. |
| **EXECUTIVE_SUMMARY** | `total_findings`, `material_findings`, `approved_findings`, `rejected_findings`, `open_gaps`, `risk_classification` | High-level quantitative synthesis of audit outcomes. |
| **SCOPE_AND_METHODOLOGY**| `documents_examined`, `financial_periods`, `deterministic_validation`, `rulebook_version` | Procedures performed, tie-out standards, and testing boundaries. |
| **EVIDENCE_INVENTORY** | `evidence_documents` (list of `evidence_id`, `document_name`, `sha256_short`, `status`) | Complete catalog of client files with SHA-256 hashes. |
| **FINANCIAL_RECONCILIATION**| `reconciliation_results` (procedure, status, variance) | Trial balance, balance sheet, and general ledger tie-out logs. |
| **AUDIT_FINDINGS** | `findings` (list of `finding_id`, `title`, `severity`, `impact_amount`, `coordinates`) | Detailed findings with source references and monetary impact. |
| **COUNTER_EVIDENCE_ANALYSIS**| `counter_evidence_challenges` (`challenge_id`, `verdict`, `rationale`) | Independent review challenger verdicts on each finding. |
| **GAP_RADAR_COMPLETENESS** | `completeness_status`, `gaps`, `coverage_disclaimer` | Missing document analysis, untested areas, and coverage notes. |
| **HUMAN_REVIEW_REGISTER** | `review_decisions` (`review_id`, `decision`, `reviewer_name`, `comments`) | Auditor approvals, rejections, or escalations. |
| **NOT_CHECKED_REGISTER** | `not_checked_items` (`procedure_name`, `status`) | Transparent disclosure of unexamined areas. |
| **RULEBOOK_TAX_METHODOLOGY**| `applicable_statute`, `income_tax_act_2025_guard` | Governing direct tax framework (1961 Act vs 2025 Act guard). |
| **LIMITATIONS_DISCLAIMERS**| `limitations` (list of statements) | Fictional/synthetic data disclosure and auditor disclaimer. |
