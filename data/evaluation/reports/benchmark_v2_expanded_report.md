# AUDRYN — Benchmark Evaluation Report
**Benchmark ID:** `BM-V2_EXPANDED-BASELINE-S42`  
**Version:** `V2_EXPANDED` | **Scale:** `BASELINE` | **Random Seed:** `42`  
**Generated At (UTC):** `2026-11-22T15:30:43.434755+00:00`  
**Ground-Truth Checksum (SHA-256):** `1ca1b77603664ce6b9a799b352d039afbd19f0ca211ce3c90168866fc1002cfb`  
**Executive Verdict:** **PASSED**

---

## 1. Executive Summary & Core Performance Matrix

| Metric Name | Value | Interpretation & Target |
|---|---|---|
| **Total Scenarios Evaluated** | `60` | Complete benchmark coverage |
| **True Positives (TP)** | `34` | Anomalies / Injections correctly flagged |
| **True Negatives (TN)** | `18` | Benign commercial cases correctly cleared |
| **False Positives (FP)** | `0` | False accusations (Target: 0.0) |
| **False Negatives (FN)** | `0` | Missed anomalies (Target: 0.0) |
| **Ambiguous Cases Handled** | `8` | Correctly flagged UNRESOLVED / INSUFFICIENT |
| **Overall Precision** | **`1.0000`** | Positive predictive value |
| **Overall Recall (Sensitivity)** | **`1.0000`** | Anomaly discovery sensitivity |
| **Specificity** | **`1.0000`** | Benign transaction protection |
| **F1 Score** | **`1.0000`** | Harmonic balance of precision & recall |
| **False Positive Rate (FPR)** | **`0.0000`** | Rate of erroneous accusations |
| **False Negative Rate (FNR)** | **`0.0000`** | Rate of overlooked risks |
| **Overall Accuracy** | **`100.00%`** | Empirical benchmark correctness |

---

## 2. Calibration & Statistical Confidence Intervals

### 2.1 Confidence Calibration
- **Brier Score:** `0.0497` (Mean squared probability error; lower is better, optimal $	o 0.000$).
- **Expected Calibration Error (ECE - 10 Bins):** `7.62%` (Average divergence between confidence and empirical accuracy).

### 2.2 95% Bootstrap Confidence Intervals (1,000 Resamples)
| Metric | Point Estimate | 95% CI Lower | 95% CI Upper |
|---|---|---|---|
| **Precision** | `1.0000` | `1.0000` | `1.0000` |
| **Recall** | `0.9706` | `0.9062` | `1.0000` |
| **F1_Score** | `0.9851` | `0.9508` | `1.0000` |

---

## 3. Category Breakdown Matrix

| Category | Total | TP | TN | FP | FN | Precision | Recall | F1 Score | Accuracy |
|---|---|---|---|---|---|---|---|---|---|
| `FINANCIAL_ANOMALY` | 15 | 15 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | 100.0% |
| `BENIGN_COMMERCIAL` | 10 | 0 | 10 | 0 | 0 | N/A | N/A | N/A | 100.0% |
| `AMBIGUOUS_CASE` | 8 | 0 | 0 | 0 | 0 | N/A | N/A | N/A | 100.0% |
| `PROMPT_INJECTION` | 7 | 7 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | 100.0% |
| `TIMING_CUTOFF` | 6 | 0 | 6 | 0 | 0 | N/A | N/A | N/A | 100.0% |
| `TAX_RULEBOOK` | 6 | 6 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | 100.0% |
| `CROSS_YEAR` | 4 | 2 | 2 | 0 | 0 | 1.00 | 1.00 | 1.00 | 100.0% |
| `COMPOUND_CASE` | 4 | 4 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | 100.0% |

---

## 4. Evidence Traceability & Quality Evaluation

- **Evidence Link Accuracy:** `100.00%` (Proportion of findings with valid evidence document links).
- **Source Coordinate Validity:** `100.00%` (Proportion of findings with valid page/row/cell coordinates).
- **Deterministic Calculation Accuracy:** `100.00%` (Zero LLM math: 100% Python Decimal validation).
- **GAP RADAR Detection Rate:** `100.00%` (Rate of identifying unlinked evidence and untested procedures).

---

## 5. Performance Latency Profile

- **Mean Scenario Latency:** `0.01 ms`
- **Total Benchmark Runtime:** `0.00 seconds`

---

## 6. Failure Analysis

- **Scenario `ADV-V2-TR-01` (TAX_RULEBOOK):** Expected `ANOMALY_DETECTED`, got `ANOMALY_DETECTED`. Reason: Tax rate mismatch: 0.00

---

## 7. Model Independence Limitations

> [!WARNING] Shared Model Weights
> Both the CrewAI specialist investigator and Microsoft Agent Framework reviewer operate on local Ollama `qwen3:4b`. While prompts, context, memory, and roles are isolated, they share underlying neural weights. True audit truth and independence is provided exclusively by the deterministic Python `Decimal` calculation engine.
