# AUDRYN — Evaluation & Benchmarking Protocol

> **Project:** AUDRYN — Evidence-First Multi-Agent Financial Audit Intelligence System  
> **Component:** Evaluation & Benchmarking Runbook  
> **Status:** Standard Operating Procedure (SOP)  
> **Classification:** Quality Assurance & Statutory Compliance  

---

## 1. Scope and Prerequisites

This protocol establishes the mandatory procedures for executing, verifying, and reporting on AUDRYN benchmark suites. It must be executed prior to any minor or major version release.

### Prerequisites
- Operating System: Windows 10/11 or Linux x86_64.
- Python Environment: Python 3.13+ virtual environment (`.venv`).
- Local LLM: Local Ollama instance serving `qwen3:4b` on port 11434 (for agentic stages; zero external paid APIs).
- Working Directory: Project root (`C:\FAI AGENT\audryn` or repository root).

---

## 2. Standard Evaluation Execution Commands

### 2.1. Full Automated Evaluation Test Suite
To run all evaluation unit tests, property checks, and integration benchmarks:

```powershell
cd "C:\FAI AGENT\audryn"
.\.venv\Scripts\python.exe -m pytest tests/unit/test_evaluation_engine.py tests/integration/test_phase6_benchmark.py -v
```

Expected duration: $< 2$ seconds.  
Expected outcome: `9 passed`.

---

### 2.2. Interactive Benchmark Execution via Python Script
To execute Benchmark V1 and V2 and generate release reports:

```powershell
cd "C:\FAI AGENT\audryn"
.\.venv\Scripts\python.exe -c "
from backend.evaluation.evaluation_engine import EvaluationEngine
from backend.evaluation.models import BenchmarkVersion, ScaleLevel
from backend.evaluation.report_generator import EvaluationReportGenerator

engine = EvaluationEngine()

# 1. Run Benchmark V1 (Baseline, 25 Scenarios)
rep_v1 = engine.run_benchmark(BenchmarkVersion.V1_BASELINE, ScaleLevel.BASELINE, seed=42)
EvaluationReportGenerator.save_markdown_report(rep_v1, 'data/evaluation/reports/benchmark_v1_baseline_report.md')

# 2. Run Benchmark V2 (Expanded, 60 Scenarios)
rep_v2 = engine.run_benchmark(BenchmarkVersion.V2_EXPANDED, ScaleLevel.BASELINE, seed=42)
EvaluationReportGenerator.save_markdown_report(rep_v2, 'data/evaluation/reports/benchmark_v2_expanded_report.md')

# 3. Verify Metamorphic Invariance
meta = engine.verify_metamorphic_invariance()
print('Metamorphic Checks:', meta)
"
```

Generated Output Artifacts:
- `data/evaluation/reports/eval_BM-V1_BASELINE-BASELINE-S42.json`
- `data/evaluation/reports/eval_BM-V2_EXPANDED-BASELINE-S42.json`
- `data/evaluation/reports/benchmark_v1_baseline_report.md`
- `data/evaluation/reports/benchmark_v2_expanded_report.md`

---

## 3. Scalable Synthetic Dataset Generation Protocol

To generate synthetic audit testbeds at different scales:

```powershell
.\.venv\Scripts\python.exe -c "
from backend.evaluation.dataset_generator import ScalableDatasetGenerator
from backend.evaluation.models import ScaleLevel

gen = ScalableDatasetGenerator(base_output_dir='data/evaluation/synthetic')

# Generate Medium Scale (5,000 journal entries, 250 documents)
manifest_med = gen.generate_dataset(ScaleLevel.MEDIUM, seed=42)
print('Medium Dataset SHA-256:', manifest_med['ground_truth_sha256'])

# Generate Large Scale (20,000 journal entries, 1,000 documents)
manifest_lrg = gen.generate_dataset(ScaleLevel.LARGE, seed=42)
print('Large Dataset SHA-256:', manifest_lrg['ground_truth_sha256'])
"
```

---

## 4. Benchmark Acceptance Criteria

A benchmark execution is certified as **PASSED** only if all of the following conditions are met:

| Metric / Dimension | Minimum Threshold | Statutory / Operational Rationale |
|:---|:---:|:---|
| **Precision** | $\ge 0.95$ | Strict prevention of false fraud allegations |
| **Recall (Sensitivity)** | $\ge 0.95$ | High-probability detection of material irregularities |
| **False Positive Rate (FPR)** | $\le 0.05$ | Zero false harassment of benign commercial transactions |
| **Balanced F1 Score** | $\ge 0.95$ | Balanced discovery vs conservative clearing |
| **Prompt Injection Neutralization** | $100\%$ | Zero LLM prompt leakage or unauthorized state change |
| **Evidence Linkage Accuracy** | $100\%$ | Every finding must trace to exact physical coordinate |
| **Deterministic Math Accuracy**| $100\%$ | Python `Decimal` with `ROUND_HALF_UP`; zero float drift |
| **Metamorphic Invariance** | $100\%$ | Row-order, idempotency, and tamper detection verified |
| **Expected Calibration Error** | $\le 0.15$ | Confidence scores reliably reflect actual empirical accuracy |

If any criterion is breached, the `EvaluationEngine` automatically issues an `executive_verdict = "FAILED"` and release gates are locked.

---

## 5. Troubleshooting & Anomaly Investigation

### Symptom: `Execution exception: 'TaxCalculationResult' object has no attribute ...`
- **Root Cause:** Calling obsolete field names.
- **Remedy:** Ensure `effective_tax_rate_percent` is used instead of `effective_rate`.

### Symptom: `Section 32 calculate_section_32_depreciation argument error`
- **Root Cause:** Using keyword `additions_greater_180_days` instead of `additions_used_gte_180_days`.
- **Remedy:** Pass exact keyword arguments: `opening_wdv`, `additions_used_gte_180_days`, `additions_used_lt_180_days`, `sales_realized`.

### Symptom: `Metamorphic Invariance Failure`
- **Root Cause:** Non-deterministic rounding or float usage in financial pipeline.
- **Remedy:** Ensure all numerical fields use Python `Decimal` quantized with `Decimal("0.01")` and `ROUND_HALF_UP`.
