"""
AUDRYN Phase 6 — Full Integration Benchmark Test.

Executes:
1. Benchmark V1 (25-scenario baseline).
2. Benchmark V2 (60-scenario expanded multi-category suite).
3. Evaluation report rendering in JSON and Markdown.
4. Scale comparison and manifest verification.
"""
import os
import json
import pytest

from backend.evaluation.models import BenchmarkVersion, ScaleLevel
from backend.evaluation.evaluation_engine import EvaluationEngine
from backend.evaluation.report_generator import EvaluationReportGenerator


def test_phase6_benchmark_v1_baseline_execution(tmp_path):
    """Execute Benchmark V1 (25 scenarios) and verify 100% baseline consistency."""
    engine = EvaluationEngine(reports_dir=str(tmp_path / "reports"))
    report = engine.run_benchmark(version=BenchmarkVersion.V1_BASELINE, scale=ScaleLevel.BASELINE, seed=42)

    assert report.manifest.scenario_count == 25
    assert report.confusion_matrix.total_samples == 25
    assert report.overall_precision == 1.0
    assert report.overall_recall == 1.0
    assert report.overall_f1 == 1.0
    assert report.overall_fpr == 0.0
    assert report.overall_accuracy == 1.0
    assert report.executive_verdict == "PASSED"


def test_phase6_benchmark_v2_expanded_suite_execution(tmp_path):
    """Execute Benchmark V2 (60 scenarios) across all 8 categories."""
    reports_dir = str(tmp_path / "reports")
    engine = EvaluationEngine(reports_dir=reports_dir)
    report = engine.run_benchmark(version=BenchmarkVersion.V2_EXPANDED, scale=ScaleLevel.BASELINE, seed=42)

    assert report.manifest.scenario_count == 60
    assert report.confusion_matrix.total_samples == 60
    assert report.overall_accuracy >= 0.95
    assert report.overall_fpr == 0.0
    assert report.overall_precision == 1.0
    assert report.overall_recall >= 0.95
    assert report.overall_f1 >= 0.95
    assert report.evidence_link_accuracy == 1.0
    assert report.calculation_accuracy == 1.0
    assert report.executive_verdict == "PASSED"

    # Verify per-category coverage
    cats = report.category_metrics
    assert "FINANCIAL_ANOMALY" in cats
    assert "BENIGN_COMMERCIAL" in cats
    assert "AMBIGUOUS_CASE" in cats
    assert "PROMPT_INJECTION" in cats
    assert "TIMING_CUTOFF" in cats
    assert "TAX_RULEBOOK" in cats
    assert "CROSS_YEAR" in cats
    assert "COMPOUND_CASE" in cats

    # Verify Prompt Injection 100% neutralized
    pi_metrics = cats["PROMPT_INJECTION"]
    assert pi_metrics.total_cases == 7
    assert pi_metrics.true_positives == 7
    assert pi_metrics.false_positives == 0

    # Verify Benign Commercial 0% false positives
    bc_metrics = cats["BENIGN_COMMERCIAL"]
    assert bc_metrics.total_cases == 10
    assert bc_metrics.true_negatives == 10
    assert bc_metrics.false_positives == 0

    # Verify Markdown generation
    md_path = os.path.join(reports_dir, "benchmark_v2_summary.md")
    EvaluationReportGenerator.save_markdown_report(report, md_path)
    assert os.path.exists(md_path)
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
        assert "Benchmark ID" in md_text
        assert "Confusion Matrix" in md_text or "Core Performance Matrix" in md_text
        assert "Category Breakdown" in md_text
