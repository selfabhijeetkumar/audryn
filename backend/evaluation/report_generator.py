"""
AUDRYN Evaluation Report Generator.

Transforms BenchmarkEvaluationReport models into publication-grade
Markdown summaries and machine-readable JSON files.
"""
import os
from typing import Optional
from backend.evaluation.models import BenchmarkEvaluationReport


class EvaluationReportGenerator:
    """
    Renders structured audit evaluation reports into markdown and json formats.
    """

    @classmethod
    def render_markdown(cls, report: BenchmarkEvaluationReport) -> str:
        """Renders comprehensive evaluation report to GitHub-flavored Markdown."""
        m = report.manifest
        cm = report.confusion_matrix

        prec_str = f"{report.overall_precision:.4f}" if report.overall_precision is not None else "N/A"
        rec_str = f"{report.overall_recall:.4f}" if report.overall_recall is not None else "N/A"
        f1_str = f"{report.overall_f1:.4f}" if report.overall_f1 is not None else "N/A"
        spec_str = f"{report.overall_specificity:.4f}" if report.overall_specificity is not None else "N/A"
        fpr_str = f"{report.overall_fpr:.4f}" if report.overall_fpr is not None else "N/A"
        fnr_str = f"{report.overall_fnr:.4f}" if report.overall_fnr is not None else "N/A"

        md = f"""# AUDRYN — Benchmark Evaluation Report
**Benchmark ID:** `{m.benchmark_id}`  
**Version:** `{m.version.value}` | **Scale:** `{m.scale.value}` | **Random Seed:** `{m.random_seed}`  
**Generated At (UTC):** `{m.generated_at_utc}`  
**Ground-Truth Checksum (SHA-256):** `{m.ground_truth_sha256}`  
**Executive Verdict:** **{report.executive_verdict}**

---

## 1. Executive Summary & Core Performance Matrix

| Metric Name | Value | Interpretation & Target |
|---|---|---|
| **Total Scenarios Evaluated** | `{cm.total_samples}` | Complete benchmark coverage |
| **True Positives (TP)** | `{cm.true_positives}` | Anomalies / Injections correctly flagged |
| **True Negatives (TN)** | `{cm.true_negatives}` | Benign commercial cases correctly cleared |
| **False Positives (FP)** | `{cm.false_positives}` | False accusations (Target: 0.0) |
| **False Negatives (FN)** | `{cm.false_negatives}` | Missed anomalies (Target: 0.0) |
| **Ambiguous Cases Handled** | `{cm.ambiguous_correct}` | Correctly flagged UNRESOLVED / INSUFFICIENT |
| **Overall Precision** | **`{prec_str}`** | Positive predictive value |
| **Overall Recall (Sensitivity)** | **`{rec_str}`** | Anomaly discovery sensitivity |
| **Specificity** | **`{spec_str}`** | Benign transaction protection |
| **F1 Score** | **`{f1_str}`** | Harmonic balance of precision & recall |
| **False Positive Rate (FPR)** | **`{fpr_str}`** | Rate of erroneous accusations |
| **False Negative Rate (FNR)** | **`{fnr_str}`** | Rate of overlooked risks |
| **Overall Accuracy** | **`{report.overall_accuracy * 100:.2f}%`** | Empirical benchmark correctness |

---

## 2. Calibration & Statistical Confidence Intervals

### 2.1 Confidence Calibration
- **Brier Score:** `{report.brier_score:.4f}` (Mean squared probability error; lower is better, optimal $\to 0.000$).
- **Expected Calibration Error (ECE - 10 Bins):** `{report.expected_calibration_error * 100:.2f}%` (Average divergence between confidence and empirical accuracy).

### 2.2 95% Bootstrap Confidence Intervals (1,000 Resamples)
| Metric | Point Estimate | 95% CI Lower | 95% CI Upper |
|---|---|---|---|
"""
        for ci in report.confidence_intervals:
            md += f"| **{ci.metric_name}** | `{ci.point_estimate:.4f}` | `{ci.lower_95:.4f}` | `{ci.upper_95:.4f}` |\n"

        md += """
---

## 3. Category Breakdown Matrix

| Category | Total | TP | TN | FP | FN | Precision | Recall | F1 Score | Accuracy |
|---|---|---|---|---|---|---|---|---|---|
"""
        for cat_name, cm_row in report.category_metrics.items():
            c_p = f"{cm_row.precision:.2f}" if cm_row.precision is not None else "N/A"
            c_r = f"{cm_row.recall:.2f}" if cm_row.recall is not None else "N/A"
            c_f = f"{cm_row.f1_score:.2f}" if cm_row.f1_score is not None else "N/A"
            md += f"| `{cat_name}` | {cm_row.total_cases} | {cm_row.true_positives} | {cm_row.true_negatives} | {cm_row.false_positives} | {cm_row.false_negatives} | {c_p} | {c_r} | {c_f} | {cm_row.accuracy * 100:.1f}% |\n"

        md += f"""
---

## 4. Evidence Traceability & Quality Evaluation

- **Evidence Link Accuracy:** `{report.evidence_link_accuracy * 100:.2f}%` (Proportion of findings with valid evidence document links).
- **Source Coordinate Validity:** `{report.source_coordinate_accuracy * 100:.2f}%` (Proportion of findings with valid page/row/cell coordinates).
- **Deterministic Calculation Accuracy:** `{report.calculation_accuracy * 100:.2f}%` (Zero LLM math: 100% Python Decimal validation).
- **GAP RADAR Detection Rate:** `{report.gap_radar_detection_rate * 100:.2f}%` (Rate of identifying unlinked evidence and untested procedures).

---

## 5. Performance Latency Profile

- **Mean Scenario Latency:** `{report.mean_latency_ms:.2f} ms`
- **Total Benchmark Runtime:** `{report.total_execution_time_s:.2f} seconds`

---

## 6. Failure Analysis

"""
        if not report.failure_analysis:
            md += "Zero benchmark failures recorded. All scenarios matched expected ground truth outcomes.\n"
        else:
            for fail in report.failure_analysis:
                md += f"- **Scenario `{fail['scenario_id']}` ({fail['category']}):** Expected `{fail['expected']}`, got `{fail['actual']}`. Reason: {fail['reason']}\n"

        md += """
---

## 7. Model Independence Limitations

> [!WARNING] Shared Model Weights
> Both the CrewAI specialist investigator and Microsoft Agent Framework reviewer operate on local Ollama `qwen3:4b`. While prompts, context, memory, and roles are isolated, they share underlying neural weights. True audit truth and independence is provided exclusively by the deterministic Python `Decimal` calculation engine.
"""
        return md

    @classmethod
    def save_markdown_report(cls, report: BenchmarkEvaluationReport, output_path: str):
        """Writes the markdown report to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        content = cls.render_markdown(report)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
