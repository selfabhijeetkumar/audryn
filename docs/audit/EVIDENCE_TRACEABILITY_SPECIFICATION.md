# AUDRYN — Evidence Traceability Specification

> **Document Type:** Audit Methodology & Traceability Specification  
> **Status:** ACTIVE & PRODUCTION-GRADE  
> **Governing Principle:** Evidence Before Conclusions  
> **Lineage Chain:** Original Document $\to$ Source Location $\to$ Extracted Record $\to$ Deterministic Calculation $\to$ Audit Finding $\to$ Counter-Evidence $\to$ Review Decision $\to$ Report Section

---

## 1. Traceability Axioms & Legal Standards

In statutory financial auditing under the Institute of Chartered Accountants of India (ICAI) and International Standards on Auditing (ISA 500 — Audit Evidence):
1. **Sufficiency & Appropriateness:** An audit finding is only as strong as its underlying evidence. Unsubstantiated claims must never be reported as confirmed anomalies.
2. **Deterministic Reproducibility:** An independent third-party auditor must be able to follow the chain of custody from the final report back to the exact page, cell, or voucher in the original client files.
3. **No Fabricated Provenance:** If coordinate data (e.g. bounding box or row index) is missing or unavailable, the system must explicitly disclose the limitation rather than invent fictional coordinates.

---

## 2. Complete End-to-End Lineage Chain

AUDRYN enforces an unbroken, 8-stage chain of custody for every material finding:

```
[1] Original Evidence Document (PDF / CSV / XLSX in Evidence Vault)
     │   • SHA-256 Checksum: f834ae9831921bbd083e4633fc5c90b76d8d83abd1be33f39219e8808f180bf9
     │   • Storage Reference: data/evidence_vault/EV-2024-001_f834ae98.pdf
     ▼
[2] Source Location (Coordinates)
     │   • PDF Page: 1 | Line / Row: 12 | Column: "Closing Debit Balance"
     │   • Raw Snippet: "₹ 14,25,00,000.00"
     ▼
[3] Extracted Financial Record / Transaction
     │   • Transaction ID: TX-REV-001
     │   • Account: "Sales Revenue" | Amount: ₹ 14,25,00,000.00 (Decimal)
     ▼
[4] Deterministic Calculation / Reconciliation
     │   • Calculation ID: CALC-TB-VAR
     │   • Procedure: Trial Balance Tie-Out (Total Debits - Total Credits)
     │   • Variance: ₹ 15,00,000.00 (Calculated via Decimal with ROUND_HALF_UP)
     ▼
[5] Audit Finding
     │   • Finding ID: FIND-TB-01
     │   • Title: "Trial balance variance of ₹ 15,00,000.00 detected"
     │   • Severity: HIGH | Category: STATUTORY_RECONCILIATION
     ▼
[6] Independent Counter-Evidence Challenge
     │   • Challenge ID: CHG-TB-01 | Reviewer: Independent Review Engine
     │   • Alternative Explanation: "General Ledger confirms unposted credit adjustment voucher."
     │   • Reviewer Verdict: SUPPORTED
     ▼
[7] Human Auditor Review Decision
     │   • Review ID: REV-TB-01 | Reviewer: CA R. Sharma
     │   • Decision: APPROVED | Action: Adjusting journal voucher required
     ▼
[8] Final Report Section
         • Report ID: RPT-AUD-2024-001 | Section: AUDIT_FINDINGS & Appendices
         • Direct Citing: EV-2024-001 at Page 1, Row 12
```

---

## 3. Financial Relationship Linkage Types

The `FinancialLinkageService` supports 6 core deterministic linkage scenarios:

### 3.1 Invoice to General Ledger
- Matches vendor invoices to purchase ledger entries and customer invoices to sales ledger entries.
- Tie-out condition: `variance == Decimal("0.00")` and `invoice_number == voucher_id`.
- If amounts or vouchers differ, the relationship is labeled `TRANSACTION_CONTRADICTS_TRANSACTION` and marked `DISCREPANCY_FLAGGED`.

### 3.2 Credit Note Reversals
- Connects subsequent credit notes to original billed invoices.
- Confirms valid commercial reversals (e.g. goods return or pricing adjustment), preventing false fraud allegations.
- Verdict: `CONTRADICTED` or `PARTIALLY_SUPPORTED`.

### 3.3 Bank Reconciliation & Timing Differences
- Matches bank statement debits/credits to general ledger cash/bank book entries.
- Detects legitimate timing differences (e.g. cheque issued 29 March, cleared 03 April per Bank Reconciliation Statement) where date difference $\le 5$ days.
- Distinguishes timing differences from unrecorded withdrawals or deposits.

### 3.4 Fixed Asset to Statutory Depreciation
- Traces asset additions to vendor invoices and the Fixed Asset Register (FAR).
- Connects book depreciation under Companies Act, 2013 to tax depreciation under Section 32 of the Income-tax Act, 1961.
- Links calculations directly to statutory tax rule nodes (`CALCULATION_USES_RULE`).

### 3.5 Cross-Year Continuity
- Links opening balance of current financial year to closing balance of previous financial year.
- Validates balance sheet continuity ($Assets = Liabilities + Equity$) across multi-year cycles.

### 3.6 Anomaly to Independent Review
- Maps each planted or detected anomaly to its supporting evidence, counter-evidence challenge, and human review decision.

---

## 4. Counter-Evidence Verdict Hierarchy

To prevent premature fraud accusations, AUDRYN strictly maintains 5 distinct counter-evidence verdicts:

1. **`SUPPORTED`**: The initial finding is fully corroborated by independent calculations and records.
2. **`CONTRADICTED`**: The apparent anomaly is explained by valid commercial counter-evidence (e.g. a valid credit note reversal or timing difference). The finding is suppressed from the final risk register.
3. **`PARTIALLY_SUPPORTED`**: Part of the variance is explained, but an unexplained residual variance remains.
4. **`UNRESOLVED`**: Contradictory evidence exists, but records are insufficient to confirm either hypothesis. Escalated for human auditor inquiry.
5. **`INSUFFICIENT_EVIDENCE`**: Critical source documents are missing; no conclusive verification can be performed. Registered in GAP RADAR.

---

## 5. Auditor Accountability & Human Sign-Off

AUDRYN explicitly adheres to the principle that AI assistants cannot issue statutory audit opinions.
- Every material finding requires sign-off from a named human reviewer (e.g. `CA R. Sharma`).
- Review decisions are immutable once recorded.
- The `ReleaseGateService` will strictly block report finalization if any material finding has `status == "OPEN"` or `human_review_status == "PENDING"`.
