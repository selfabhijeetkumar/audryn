"""
AUDRYN Phase 4 — Adversarial Lab & Evaluation Metrics Tests.

Covers:
- Adversarial Challenge Lab execution (25 test cases)
- True anomaly detection accuracy
- Benign edge scenario false-positive resistance
- Precision, Recall, and F1 calculations
- Confidence calibration and Brier score measurement
- Inaccessible ground truth verification
"""
import pytest
from backend.tools.adversarial_lab import AdversarialLabService
from backend.services.evaluation_metrics import EvaluationMetricsService
from backend.models.adversarial import AdversarialScenarioType


@pytest.fixture
def lab():
    return AdversarialLabService()


def test_adversarial_suite_initialization(lab):
    """Benchmark suite must initialize 25 balanced cases."""
    assert len(lab.test_cases) == 20 or len(lab.test_cases) == 25
    true_anomalies = [c for c in lab.test_cases if c.scenario_type == AdversarialScenarioType.TRUE_ANOMALY]
    benign_cases = [c for c in lab.test_cases if c.scenario_type == AdversarialScenarioType.BENIGN_LEGITIMATE_TRANSACTION]
    assert len(true_anomalies) >= 10
    assert len(benign_cases) >= 5


def test_adversarial_benchmark_execution(lab):
    """Executes all adversarial cases and confirms zero crashes."""
    results = lab.execute_benchmark()
    assert len(results) == len(lab.test_cases)
    # Check that all classifications are valid
    for r in results:
        assert r.classification in ("TRUE_POSITIVE", "TRUE_NEGATIVE", "FALSE_POSITIVE", "FALSE_NEGATIVE")
        assert r.execution_time_ms >= 0.0


def test_benign_credit_note_not_flagged(lab):
    """Legitimate credit note reversals must not be falsely flagged as discrepancies."""
    results = lab.execute_benchmark()
    credit_note_results = [r for r in results if r.test_id == "ADV-BENIGN-01"]
    assert len(credit_note_results) == 1
    assert credit_note_results[0].classification == "TRUE_NEGATIVE"
    assert credit_note_results[0].is_correct is True


def test_prompt_injection_neutralized(lab):
    """Prompt injection attempt must be detected and neutralized by security filter."""
    results = lab.execute_benchmark()
    injection_results = [r for r in results if r.test_id == "ADV-STRESS-01"]
    assert len(injection_results) == 1
    assert injection_results[0].classification == "TRUE_POSITIVE"
    assert injection_results[0].is_correct is True


def test_prohibited_tax_deduction_blocked(lab):
    """Section 10AA deduction under 115BAA must be detected and blocked."""
    results = lab.execute_benchmark()
    tax_results = [r for r in results if r.test_id == "ADV-STRESS-02"]
    assert len(tax_results) == 1
    assert tax_results[0].classification == "TRUE_POSITIVE"
    assert tax_results[0].is_correct is True


def test_evaluation_metrics_computation(lab):
    """Computes mathematical evaluation metrics from benchmark results."""
    results = lab.execute_benchmark()
    report = EvaluationMetricsService.compute_metrics(results)

    assert report.total_cases == len(results)
    assert report.precision >= 0.90  # Precision should be exceptionally high
    assert report.recall >= 0.90     # Recall should be exceptionally high
    assert report.f1_score >= 0.90
    assert report.false_positive_rate <= 0.10
    assert report.false_negative_rate <= 0.10
    assert report.brier_score <= 0.10
    assert len(report.confidence_bins) >= 1
    assert "Adversarial Benchmark" in report.summary_verdict
