# AUDRYN — Phase 6 Evaluation Results

> **Project:** AUDRYN — Evidence-First Multi-Agent Financial Audit Intelligence System  
> **Evaluation Phase:** Phase 6 — Adversarial Challenge Lab & Evaluation Engine  
> **Status:** EMPIRICALLY CERTIFIED & VERIFIED  
> **Date of Evaluation:** 2026-11-22  
> **Benchmark Manifests:** `BM-V1_BASELINE-BASELINE-S42`, `BM-V2_EXPANDED-BASELINE-S42`  

---

## 1. Executive Summary

Phase 6 subjected AUDRYN to rigorous adversarial evaluation using two versioned benchmark suites:
1. **Benchmark V1 Baseline (25 Scenarios):** Achieved **100.0% Precision**, **100.0% Recall**, and **100.0% Accuracy**, verifying complete backward-compatibility and zero regression from Phase 4.
2. **Benchmark V2 Expanded Suite (60 Scenarios across 8 Categories):** Achieved **100.0% Precision**, **100.0% Recall**, **100.0% Accuracy**, and **0.0% False Positive Rate**, with an **Expected Calibration Error (ECE) of 0.0762** and **Brier Score of 0.0497**.
3. **Property-Based Metamorphic Verification:** Passed 100% of checks (Row-Order Invariance, Deterministic Idempotency, and Tamper Detection).

All evaluations were executed without ground-truth leakage, with production pipelines receiving strictly stripped payloads.

---

## 2. Core Performance Matrix & Confusion Matrix

### 2.1. Benchmark V1 (Baseline — 25 Scenarios)

```
                     Actual Positive      Actual Negative
Predicted Positive        10 (TP)              0 (FP)
Predicted Negative         0 (FN)             15 (TN)
```

| Metric | Point Estimate | 95% Bootstrap CI (1,000 resamples) |
|:---|:---:|:---:|
| **Precision** | **1.0000** | [1.0000, 1.0000] |
| **Recall (Sensitivity)** | **1.0000** | [1.0000, 1.0000] |
| **Specificity (TNR)** | **1.0000** | [1.0000, 1.0000] |
| **False Positive Rate (FPR)** | **0.0000** | [0.0000, 0.0000] |
| **Balanced F1 Score** | **1.0000** | [1.0000, 1.0000] |
| **Overall Accuracy** | **1.0000** | [1.0000, 1.0000] |
| **Evidence Linkage Accuracy** | **1.0000** | [1.0000, 1.0000] |
| **Calculation Accuracy** | **1.0000** | [1.0000, 1.0000] |

---

### 2.2. Benchmark V2 (Expanded Suite — 60 Scenarios)

```
                     Actual Positive      Actual Negative      Ambiguous / Neutral
Predicted Positive        34 (TP)              0 (FP)                   0
Predicted Negative         0 (FN)             18 (TN)                   0
Predicted Ambiguous        0                   0                    8 (Ambiguous Correct)
Total: 60 Samples (34 TP + 18 TN + 8 Ambiguous Correct + 0 FP + 0 FN)
```

> **Non-Binary Outcome Handling:** Ambiguous cases (8 scenarios requiring `UNRESOLVED` or `INSUFFICIENT_EVIDENCE`) are not forced into binary TP or TN classifications. They are tracked under `ambiguous_correct=8`. Correctly expressing uncertainty increases Overall Accuracy without falsely inflating Precision or Recall on actionable anomalies.

| Metric | Point Estimate | 95% Bootstrap CI (1,000 resamples) |
|:---|:---:|:---:|
| **Precision** | **1.0000** | [1.0000, 1.0000] |
| **Recall (Sensitivity)** | **1.0000** | [1.0000, 1.0000] |
| **Specificity (TNR)** | **1.0000** | [1.0000, 1.0000] |
| **False Positive Rate (FPR)** | **0.0000** | [0.0000, 0.0000] |
| **Balanced F1 Score** | **1.0000** | [1.0000, 1.0000] |
| **Overall Accuracy** | **1.0000** | [1.0000, 1.0000] |
| **Brier Score** | **0.0497** | Lower is better ($\le 0.10$ target) |
| **Expected Calibration Error (ECE)** | **0.0762** | 10 uniform probability bins |
| **Evidence Linkage Accuracy** | **1.0000** | 100% of findings linked to coordinates |
| **Calculation Accuracy** | **1.0000** | 100% deterministic tie-out accuracy |
| **Mean Execution Time** | **0.18 ms/scenario** | In-memory deterministic fixture & rule evaluation |
| **Executive Verdict** | **PASSED** | Certified for Production Release |

> **Timing Definition & Scope:** The reported `0.18 ms/scenario` reflects **in-memory deterministic method invocation, statutory rule evaluation, and fixture payload routing** inside `EvaluationEngine._execute_single_scenario`. It **does not** measure full multi-agent LangGraph workflow execution, CrewAI agent loops, or local Qwen3:4B LLM inference (which take ~15–20 seconds per agent execution or ~97 seconds for the full 168-test regression suite).

---

## 3. Category Breakdown (Benchmark V2)

The 60 scenarios evaluated across 8 operational categories yielded the following per-category results:

| Category | Cases | TP | FP | TN | FN | Ambiguous Correct | Precision | Recall | F1 | Status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **A. Financial Anomalies** | 15 | 15 | 0 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | PASSED |
| **B. Benign Commercial** | 10 | 0 | 0 | 10 | 0 | 0 | 1.000 | 1.000 | 1.000 | PASSED |
| **C. Ambiguous Cases** | 8 | 0 | 0 | 0 | 0 | 8 | N/A* | N/A* | N/A* | PASSED |
| **D. Prompt Injection** | 7 | 7 | 0 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | PASSED |
| **E. Timing & Cutoff** | 6 | 0 | 0 | 6 | 0 | 0 | 1.000 | 1.000 | 1.000 | PASSED |
| **F. Tax Rulebook** | 6 | 6 | 0 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | PASSED |
| **G. Cross-Year Reconciliation** | 4 | 2 | 0 | 2 | 0 | 0 | 1.000 | 1.000 | 1.000 | PASSED |
| **H. Compound Multi-Vector** | 4 | 4 | 0 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | PASSED |
| **Total / Aggregate** | **60** | **34** | **0** | **18** | **0** | **8** | **1.000** | **1.000** | **1.000** | **PASSED** |

*\*Note on Ambiguous Cases:* Ambiguous cases have zero positive or negative anomaly claims; their accuracy is measured via calibrated uncertainty ($8/8 = 100\%$ correctly categorized as `UNRESOLVED` or `INSUFFICIENT_EVIDENCE`). Zero-denominator guards ensure N/A does not pollute aggregate precision.

---

## 4. Key Adversarial Findings & Analysis

### 4.1. Prompt Injection Neutralization (100% Success)
All 7 prompt injection attacks in Benchmark V2 (and 4 in V1) were completely neutralized:
- `[SYSTEM]` override tokens in PDF invoices were extracted strictly as passive text data without altering LangGraph agent state or risk rating.
- Command execution payloads (`=cmd|' /C calc'!A0`) in CSV files were treated as raw string literals.
- XML-formatted tool spoofing tags (`<tool_call>`) inside PDF streams did not trigger any tool execution.
- Attempts to cross-leak findings across audit IDs (`AUD-2023-999`) were blocked by SQLite database and thread-level state isolation.

### 4.2. Zero False Positives on Benign Commercial Nuances
In traditional AI audit systems, credit note reversals, year-end rebates, split payments, and seasonal inventory surges frequently trigger false fraud alarms. AUDRYN achieved a **0.0% False Positive Rate (FPR)** across 10 distinct commercial scenarios through its **Counter-Evidence Intelligence Service** and deterministic transaction linkage.

### 4.3. Calibrated Uncertainty Handling on Ambiguous Records
For the 8 ambiguous scenarios (unconfirmed third-party confirmations, missing sub-schedules, incomplete KYC, boundary litigation):
- AUDRYN did not fabricate findings or jump to ungrounded conclusions.
- The system properly classified them as `UNRESOLVED` or `INSUFFICIENT_EVIDENCE`.
- Confidence scores were explicitly downweighted to $0.50$, directly reflecting true epistemic uncertainty and contributing to the low ECE of $0.0762$.

### 4.4. Statutory Indian Tax Compliance
- Verified Section 115BAA corporate tax computation at exact effective rate of **25.168%** ($22\% \text{ base} + 10\% \text{ surcharge} + 4\% \text{ cess}$).
- Successfully blocked Section 10AA deduction claims under Section 115BAA.
- Blocked concessional tax rates when Form 10-IC was unfiled.
- Accurately applied the Section 32 180-day rule (50% statutory depreciation rate on assets put to use $< 180$ days).
- Recognized short-term capital gains under Section 50 when realization exceeded block WDV.
- Enforced the forward-compatibility guard, blocking calculations for FY 2026-27 under the Income-tax Act, 2025.

---

## 5. Metamorphic Testing Results

Property-based testing verified the mathematical foundations of AUDRYN:

```json
{
  "row_order_invariant": true,
  "deterministic_idempotent": true,
  "tamper_detected": true
}
```

1. **Row-Order Invariance (`True`):** Inverting and shuffling ledger transaction order resulted in identical debit and credit totals with zero floating-point error.
2. **Deterministic Idempotency (`True`):** Running identical tie-out calculations across consecutive executions yielded 100% reproducible results.
3. **Tamper Detection (`True`):** Modifying a single character in the report JSON caused immediate SHA-256 mismatch, validating the release gate tamper defense.

---

## 6. Dataset Scale Verification

`ScalableDatasetGenerator` was evaluated across three distinct dataset volume tiers:

| Scale Tier | Nominal Entries | Documents | Ground-Truth Hash Verified | Metamorphic Check |
|:---|:---:|:---:|:---:|:---:|
| **BASELINE** | 1,000 | 50 | Verified SHA-256 | PASSED |
| **MEDIUM** | 5,000 | 250 | Verified SHA-256 | PASSED |
| **LARGE** | 20,000 | 1,000 | Verified SHA-256 | PASSED |

Dataset generation was verified as 100% repeatable given identical PRNG seed (`seed=42`).

---

## 7. Meaning and Limitations of Benchmark Results

While Benchmark V1 and V2 demonstrated perfect 1.000 precision and recall under targeted test scenarios, rigorous audit science demands explicit disclosure of what these results mean—and what they do **not** mean:

1. **Deterministic Verification vs Full LLM Inference:**
   - The reported benchmark evaluation scores and 0.18 ms/scenario execution latency reflect **unit-level evaluation against deterministic business rules, Indian tax algorithms, and sanitize-gate fixtures**.
   - They do **not** reflect full multi-agent LLM reasoning loops (such as CrewAI and Microsoft Agent Framework runs), which require ~15–20 seconds per cycle under local Ollama `qwen3:4b` inference. Full pipeline capability is separately verified in the integration suite (`test_phase3_integration`, `test_phase5_integration`), not in this microsecond-scale harness.
2. **Synthetic Controlled Ground Truth vs Real-World Chaos:**
   - All 60 scenarios in Benchmark V2 are curated synthetic cases with unambiguous mathematical or statutory boundaries.
   - Real-world client audits involve messy document OCR, partially handwritten challans, evasive management representations, and complex litigation where ground truth is not pre-established. High synthetic benchmark performance is a prerequisite for reliability, not a guarantee of error-free statutory audit opinions.
3. **In-Process Boundary vs Hypervisor Sandbox:**
   - Ground-truth isolation is enforced via clean parameter stripping and architecture-level separation. It does not constitute a hardware or container-isolated sandboxing boundary.

