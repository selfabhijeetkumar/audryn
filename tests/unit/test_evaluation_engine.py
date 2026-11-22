"""
AUDRYN Phase 6 — Evaluation Engine & Benchmark Tests.

Covers:
- Scalable synthetic dataset generator across BASELINE, MEDIUM, and LARGE scales
- Ground-truth isolation verification (no leakage into agent-visible evidence)
- Benchmark Registry V1 (25 scenarios) and V2 (60 scenarios)
- Formal metrics computation: Confusion matrix, Precision, Recall, F1, FPR, FNR
- Zero-division safety guards
- 10-bin Expected Calibration Error (ECE) and Brier Score
- 95% Bootstrap Confidence Intervals
- Metamorphic property-based invariants (row reordering, idempotency, tamper detection)
"""
import os
import json
import pytest
from decimal import Decimal

from backend.evaluation.models import (
    BenchmarkVersion,
    ScaleLevel,
    ScenarioCategory,
    ExpectedOutcome,
    ExecutionStatus,
    ScenarioExecutionResult,
)
from backend.evaluation.dataset_generator import ScalableDatasetGenerator
from backend.evaluation.benchmark_registry import BenchmarkRegistry
from backend.evaluation.metrics_engine import FormalMetricsEngine
from backend.evaluation.evaluation_engine import EvaluationEngine


def test_scalable_dataset_generator_scales(tmp_path):
    """Verify dataset generation across BASELINE, MEDIUM, and LARGE scales."""
    gen = ScalableDatasetGenerator(base_dir=str(tmp_path / "eval_data"))

    # Baseline scale
    res_base = gen.generate_benchmark_dataset(scale=ScaleLevel.BASELINE, seed=42)
    assert res_base["scale"] == ScaleLevel.BASELINE
    assert res_base["total_invoices"] == 75  # 3 FYs * 25
    assert res_base["total_bank_transactions"] == 90  # 3 FYs * 30
    assert os.path.exists(res_base["ground_truth_path"])

    # Medium scale
    res_med = gen.generate_benchmark_dataset(scale=ScaleLevel.MEDIUM, seed=101)
    assert res_med["scale"] == ScaleLevel.MEDIUM
    assert res_med["total_invoices"] == 300  # 3 FYs * 100
    assert res_med["total_bank_transactions"] == 360  # 3 FYs * 120

    # Deterministic reproducibility check
    res_base_repeat = gen.generate_benchmark_dataset(scale=ScaleLevel.BASELINE, seed=42)
    assert res_base["ground_truth_sha256"] == res_base_repeat["ground_truth_sha256"]


def test_ground_truth_isolation(tmp_path):
    """Ground truth registry must reside in a separate directory from agent-visible evidence."""
    gen = ScalableDatasetGenerator(base_dir=str(tmp_path / "eval_data"))
    res = gen.generate_benchmark_dataset(scale=ScaleLevel.BASELINE, seed=42)

    # Check directories are separate
    dataset_dir = res["dataset_dir"]
    gt_path = res["ground_truth_path"]
    assert "datasets" in dataset_dir
    assert "ground_truth" in gt_path
    assert not gt_path.startswith(dataset_dir)

    # Verify agent evidence CSVs do not contain ground-truth expected labels
    for fname in os.listdir(dataset_dir):
        if fname.endswith(".csv"):
            with open(os.path.join(dataset_dir, fname), "r", encoding="utf-8") as f:
                content = f.read()
                assert "expected_variance" not in content
                assert "planted" not in content


def test_benchmark_registry_v1_and_v2():
    """Verify registry maintains V1 (25 cases) and V2 (60 cases)."""
    reg = BenchmarkRegistry()
    v1_cases = reg.get_scenarios(BenchmarkVersion.V1_BASELINE)
    v2_cases = reg.get_scenarios(BenchmarkVersion.V2_EXPANDED)

    assert len(v1_cases) == 25
    assert len(v2_cases) == 60

    # Verify category distribution in V2
    categories = {s.category for s in v2_cases}
    assert ScenarioCategory.FINANCIAL_ANOMALY in categories
    assert ScenarioCategory.BENIGN_COMMERCIAL in categories
    assert ScenarioCategory.AMBIGUOUS_CASE in categories
    assert ScenarioCategory.PROMPT_INJECTION in categories
    assert ScenarioCategory.TIMING_CUTOFF in categories
    assert ScenarioCategory.TAX_RULEBOOK in categories
    assert ScenarioCategory.CROSS_YEAR in categories
    assert ScenarioCategory.COMPOUND_CASE in categories


def test_formal_metrics_computation():
    """Verify confusion matrix and metrics with explicit calculations."""
    results = [
        # 3 True Positives
        ScenarioExecutionResult(scenario_id="S1", benchmark_version=BenchmarkVersion.V2_EXPANDED, category=ScenarioCategory.FINANCIAL_ANOMALY, expected_outcome=ExpectedOutcome.ANOMALY_DETECTED, actual_outcome=ExpectedOutcome.ANOMALY_DETECTED, status=ExecutionStatus.PASS, confidence=0.98),
        ScenarioExecutionResult(scenario_id="S2", benchmark_version=BenchmarkVersion.V2_EXPANDED, category=ScenarioCategory.TAX_RULEBOOK, expected_outcome=ExpectedOutcome.TAX_BLOCKED, actual_outcome=ExpectedOutcome.TAX_BLOCKED, status=ExecutionStatus.PASS, confidence=0.95),
        ScenarioExecutionResult(scenario_id="S3", benchmark_version=BenchmarkVersion.V2_EXPANDED, category=ScenarioCategory.PROMPT_INJECTION, expected_outcome=ExpectedOutcome.INJECTION_NEUTRALIZED, actual_outcome=ExpectedOutcome.INJECTION_NEUTRALIZED, status=ExecutionStatus.PASS, confidence=0.99),
        # 2 True Negatives
        ScenarioExecutionResult(scenario_id="S4", benchmark_version=BenchmarkVersion.V2_EXPANDED, category=ScenarioCategory.BENIGN_COMMERCIAL, expected_outcome=ExpectedOutcome.BENIGN_CLEARED, actual_outcome=ExpectedOutcome.BENIGN_CLEARED, status=ExecutionStatus.PASS, confidence=0.92),
        ScenarioExecutionResult(scenario_id="S5", benchmark_version=BenchmarkVersion.V2_EXPANDED, category=ScenarioCategory.TIMING_CUTOFF, expected_outcome=ExpectedOutcome.BENIGN_CLEARED, actual_outcome=ExpectedOutcome.BENIGN_CLEARED, status=ExecutionStatus.PASS, confidence=0.94),
        # 1 Ambiguous Correct
        ScenarioExecutionResult(scenario_id="S6", benchmark_version=BenchmarkVersion.V2_EXPANDED, category=ScenarioCategory.AMBIGUOUS_CASE, expected_outcome=ExpectedOutcome.UNRESOLVED, actual_outcome=ExpectedOutcome.UNRESOLVED, status=ExecutionStatus.PASS, confidence=0.50),
    ]

    metrics = FormalMetricsEngine.evaluate_results(results)
    cm = metrics["confusion_matrix"]
    assert cm.true_positives == 3
    assert cm.true_negatives == 2
    assert cm.false_positives == 0
    assert cm.false_negatives == 0
    assert cm.ambiguous_correct == 1
    assert metrics["overall_precision"] == 1.0
    assert metrics["overall_recall"] == 1.0
    assert metrics["overall_f1"] == 1.0
    assert metrics["overall_fpr"] == 0.0
    assert metrics["overall_fnr"] == 0.0
    assert metrics["overall_accuracy"] == 1.0


def test_zero_denominator_guards():
    """Verify that zero division returns None safely without raising errors."""
    only_benign = [
        ScenarioExecutionResult(scenario_id="B1", benchmark_version=BenchmarkVersion.V2_EXPANDED, category=ScenarioCategory.BENIGN_COMMERCIAL, expected_outcome=ExpectedOutcome.BENIGN_CLEARED, actual_outcome=ExpectedOutcome.BENIGN_CLEARED, status=ExecutionStatus.PASS, confidence=0.95),
    ]
    # TP = 0, FP = 0 -> Precision denominator is 0
    metrics = FormalMetricsEngine.evaluate_results(only_benign)
    assert metrics["overall_precision"] is None
    assert metrics["overall_recall"] is None
    assert metrics["overall_f1"] is None
    assert metrics["overall_specificity"] == 1.0
    assert metrics["overall_fpr"] == 0.0


def test_calibration_and_bootstrap_cis():
    """Verify Brier score, ECE 10-bin calculation, and bootstrap confidence intervals."""
    results = [
        ScenarioExecutionResult(scenario_id=f"T{i}", benchmark_version=BenchmarkVersion.V2_EXPANDED, category=ScenarioCategory.FINANCIAL_ANOMALY, expected_outcome=ExpectedOutcome.ANOMALY_DETECTED, actual_outcome=ExpectedOutcome.ANOMALY_DETECTED, status=ExecutionStatus.PASS, confidence=0.95)
        for i in range(10)
    ]
    metrics = FormalMetricsEngine.evaluate_results(results, bootstrap_seed=42)
    assert metrics["brier_score"] >= 0.0
    assert metrics["expected_calibration_error"] >= 0.0
    assert len(metrics["confidence_intervals"]) == 3
    for ci in metrics["confidence_intervals"]:
        assert ci.lower_95 <= ci.point_estimate <= ci.upper_95


def test_metamorphic_invariance(tmp_path):
    """Verify metamorphic properties (row-order invariance, idempotency, tamper detection)."""
    engine = EvaluationEngine(reports_dir=str(tmp_path / "reports"))
    invariance = engine.verify_metamorphic_invariance()

    assert invariance["row_order_invariant"] is True
    assert invariance["deterministic_idempotent"] is True
    assert invariance["tamper_detected"] is True
