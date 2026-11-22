# AUDRYN — Counter-Evidence Intelligence Engine Design

> **Document ID:** AUDRYN-DESIGN-CE-001  
> **Status:** APPROVED  
> **Phase:** 3 — Multi-Agent Audit Core  

---

## 1. Objective & Philosophy

In traditional AI systems, an anomaly detection agent generates a hypothesis and an automated workflow often accepts it uncritically. In statutory financial audit, this introduces unacceptable false-positive risks and accusations.

The **Counter-Evidence Intelligence Engine** enforces institutional skepticism. For every material finding produced by investigation agents, an independent challenger must:
1. Actively seek contradictory evidence (e.g., subsequent journal reversals, credit notes, management explanations).
2. Investigate alternative business justifications (e.g., standard timing differences between invoice issuance and bank settlement).
3. Validate mathematical calculations deterministically (expected vs actual variance check using Python `Decimal`).
4. Prevent automated fraud labeling.

---

## 2. Verdict Taxonomy

| Verdict | Definition | Escalation Trigger |
|---|---|---|
| `SUPPORTED` | Finding is corroborated by original evidence, no reversals or valid alternative explanations found, and calculation verified. | No automatic escalation required. |
| `CONTRADICTED` | Direct contradictory evidence found (e.g., full credit note or reversing entry identified). Original finding refuted. | Escalation triggered to review discrepancy. |
| `PARTIALLY_SUPPORTED` | Supporting evidence exists, but valid alternative explanations or commercial mitigating factors are present. | Mandatory escalation to Senior Auditor. |
| `UNRESOLVED` | Evidence is conflicting or incomplete; investigation cannot confirm or refute hypothesis. | Mandatory escalation to Audit Manager. |
| `INSUFFICIENT_EVIDENCE` | Original finding lacks supporting documentation or coordinate provenance. | Rejected back to investigation team. |

---

## 3. Data Structure & Workflow

```json
{
  "challenge_id": "CE-9f9c2063",
  "finding_id": "FND-004",
  "original_hypothesis": "Depreciation rate is incorrect on Machinery.",
  "supporting_evidence": ["fixed_asset_register.csv:row_5"],
  "contradictory_evidence": ["management_response_note.pdf"],
  "alternative_explanations": ["Different rate applied under Section 32 demonstration rules."],
  "calculation_verification": "Deterministic check: Expected=75000.00, Actual=125000.00, Variance=50000.00.",
  "missing_evidence": [],
  "reviewer_role": "Independent Finding Reviewer",
  "reviewer_verdict": "PARTIALLY_SUPPORTED",
  "requires_escalation": true
}
```

---

## 4. Integration with LangGraph

Counter-evidence challenges are dispatched in node 8 (`dispatch_independent_review`). Findings flagged with `requires_escalation = true` increase the audit risk score in `classify_risk`, triggering a human review interrupt before final audit opinion formation.
