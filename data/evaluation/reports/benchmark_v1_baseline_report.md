# AUDRYN — Benchmark Evaluation Report
**Benchmark ID:** `BM-V1_BASELINE-BASELINE-S42`  
**Version:** `V1_BASELINE` | **Scale:** `BASELINE` | **Random Seed:** `42`  
**Generated At (UTC):** `2026-11-22T15:30:43.413799+00:00`  
**Ground-Truth Checksum (SHA-256):** `08ff0857889dd51d98ec2045e8aee7b42f044acfd8795a7fcaec318c2f75c299`  
**Executive Verdict:** **PASSED**

---

## 1. Executive Summary & Core Performance Matrix

| Metric Name | Value | Interpretation & Target |
|---|---|---|
| **Total Scenarios Evaluated** | `25` | Complete benchmark coverage |
| **True Positives (TP)** | `17` | Anomalies / Injections correctly flagged |
| **True Negatives (TN)** | `8` | Benign commercial cases correctly cleared |
| **False Positives (FP)** | `0` | False accusations (Target: 0.0) |
| **False Negatives (FN)** | `0` | Missed anomalies (Target: 0.0) |
| **Ambiguous Cases Handled** | `0` | Correctly flagged UNRESOLVED / INSUFFICIENT |
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
- **Brier Score:** `0.0012` (Mean squared probability error; lower is better, optimal $	o 0.000$).
- **Expected Calibration Error (ECE - 10 Bins):** `3.12%` (Average divergence between confidence and empirical accuracy).

### 2.2 95% Bootstrap Confidence Intervals (1,000 Resamples)
| Metric | Point Estimate | 95% CI Lower | 95% CI Upper |
|---|---|---|---|
| **Precision** | `1.0000` | `1.0000` | `1.0000` |
| **Recall** | `1.0000` | `1.0000` | `1.0000` |
| **F1_Score** | `1.0000` | `1.0000` | `1.0000` |

---

## 3. Category Breakdown Matrix

| Category | Total | TP | TN | FP | FN | Precision | Recall | F1 Score | Accuracy |
|---|---|---|---|---|---|---|---|---|---|
| `FINANCIAL_ANOMALY` | 8 | 8 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | 100.0% |
| `TAX_RULEBOOK` | 4 | 4 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | 100.0% |
| `CROSS_YEAR` | 1 | 1 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | 100.0% |
| `BENIGN_COMMERCIAL` | 5 | 0 | 5 | 0 | 0 | N/A | N/A | N/A | 100.0% |
| `PROMPT_INJECTION` | 4 | 4 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | 100.0% |
| `TIMING_CUTOFF` | 3 | 0 | 3 | 0 | 0 | N/A | N/A | N/A | 100.0% |

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

Zero benchmark failures recorded. All scenarios matched expected ground truth outcomes.

---

## 7. Model Independence Limitations

> [!WARNING] Shared Model Weights
> Both the CrewAI specialist investigator and Microsoft Agent Framework reviewer operate on local Ollama `qwen3:4b`. While prompts, context, memory, and roles are isolated, they share underlying neural weights. True audit truth and independence is provided exclusively by the deterministic Python `Decimal` calculation engine.
