# AUDRYN — GAP RADAR Engine Design

> **Document ID:** AUDRYN-DESIGN-GAP-001  
> **Status:** APPROVED  
> **Phase:** 3 — Multi-Agent Audit Core  

---

## 1. Objective & Epistemic Humility

The primary failure mode of automated audit agents is "silent assumption": treating areas not examined as if they passed verification.

**GAP RADAR** acts as the system's epistemic watchdog. It continuously maps what the audit system has **not** checked, where evidence chains break, and where tool execution failures create investigative blind spots.

> **Core Principle:** GAP RADAR explicitly distinguishes known unknowns from unverified assumptions. It does not claim that all possible unknown risks in an enterprise have been discovered.

---

## 2. Gap Taxonomy & Detection Criteria

| Gap Category | Severity | Detection Trigger |
|---|---|---|
| `MISSING_DOCUMENT` | `HIGH` | Mandatory document type (e.g., `BANK_STATEMENT`) absent from ingested document catalogue for an audit period. |
| `MISSING_PERIOD` | `CRITICAL` | Complete fiscal year absent from engagement scope (e.g., missing FY 2024-25 in a 3-year audit). |
| `SOURCE_PROVENANCE_GAP` | `HIGH` | Extracted financial amount has missing page coordinates, sheet index, or SHA-256 vault reference. |
| `UNVERIFIED_CALCULATION` | `HIGH` | Anomaly flagged without deterministic Decimal verification record. |
| `TOOL_FAILURE` | `HIGH` | Agent tool timeout, API failure, or unhandled exception logged in `execution_errors`. |
| `MISSING_EVIDENCE_LINK` | `HIGH` | Investigation finding created without linked `source_evidence`. |
| `UNTESTED_PROCEDURE` | `MEDIUM` | Procedure in `NotCheckedRegister` remaining in `NOT_CHECKED` status at audit conclusion. |
| `UNRESOLVED_FINDING` | `MEDIUM` / `CRITICAL` | Finding remaining in `OPEN` or `UNRESOLVED` status without human sign-off. |
| `INCOMPLETE_EXECUTION` | `CRITICAL` | Pipeline termination prior to finalization node. |

---

## 3. Status Lifecycle

```
[NOT_CHECKED] ───► [BLOCKED] ───► [REQUIRES_HUMAN_REVIEW] ───► [RESOLVED]
      │                                     ▲
      └───────────────► [UNRESOLVED] ───────┘
```

---

## 4. Completeness Blocking Rule

If any gap in the register has severity `CRITICAL` and status is not `RESOLVED`, the Audit Completeness Gate immediately sets `audit_completeness_blocked = true`. The LangGraph supervisor's `finalize_audit` node is strictly barred from issuing a `FINALIZED` report status until the gap is resolved or explicitly signed off by a human audit manager.
