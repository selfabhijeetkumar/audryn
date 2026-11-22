"""
AUDRYN Evaluation Metrics Engine.

Calculates reproducible, empirical metrics across:
- Precision, Recall, F1 Score
- False Positive Rate (FPR), False Negative Rate (FNR)
- Evidence-Link Accuracy
- Tool Selection Accuracy
- Task Completion Rate
- Processing Latency
- Confidence Calibration (Brier Score & Calibration Error)

STRICT RULE: Does NOT claim high confidence guarantees accuracy.
Measures confidence against actual benchmark outcomes.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.models.adversarial import AdversarialTestResult


class ConfidenceBin(BaseModel):
    bin_range: str
    count: int
    mean_confidence: float
    empirical_accuracy: float
    calibration_gap: float


class EvaluationReport(BaseModel):
    total_cases: int
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    false_negative_rate: float
    evidence_link_accuracy: float
    tool_selection_accuracy: float
    task_completion_rate: float
    mean_latency_ms: float
    brier_score: float
    expected_calibration_error: float
    confidence_bins: List[ConfidenceBin] = Field(default_factory=list)
    category_breakdown: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    summary_verdict: str


class EvaluationMetricsService:
    """
    Computes rigorous mathematical audit metrics for autonomous agent systems.
    """

    @classmethod
    def compute_metrics(
        cls,
        results: List[AdversarialTestResult],
        tool_selection_accuracy: float = 1.0,
        task_completion_rate: float = 1.0,
    ) -> EvaluationReport:
        """
        Computes precision, recall, F1, FPR, FNR, calibration error, and category breakdowns.
        """
        if not results:
            raise ValueError("Cannot compute evaluation metrics on empty results list.")

        total = len(results)
        tp = sum(1 for r in results if r.classification == "TRUE_POSITIVE")
        tn = sum(1 for r in results if r.classification == "TRUE_NEGATIVE")
        fp = sum(1 for r in results if r.classification == "FALSE_POSITIVE")
        fn = sum(1 for r in results if r.classification == "FALSE_NEGATIVE")

        # Precision & Recall
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # Rates
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0

        # Evidence link accuracy
        linked_count = sum(1 for r in results if r.evidence_linked)
        evidence_accuracy = linked_count / total

        # Latency
        mean_latency = sum(r.execution_time_ms for r in results) / total

        # Calibration & Brier Score
        # Brier Score = (1/N) * sum((confidence - actual_outcome)^2)
        brier_sum = 0.0
        # Group into 3 confidence bins: [0.0 - 0.5], (0.5 - 0.8], (0.8 - 1.0]
        bins = {
            "LOW (0.0-0.5)": {"conf": [], "correct": []},
            "MEDIUM (0.5-0.8)": {"conf": [], "correct": []},
            "HIGH (0.8-1.0)": {"conf": [], "correct": []},
        }

        for r in results:
            outcome = 1.0 if r.is_correct else 0.0
            brier_sum += (r.confidence_score - outcome) ** 2

            if r.confidence_score <= 0.5:
                b_key = "LOW (0.0-0.5)"
            elif r.confidence_score <= 0.8:
                b_key = "MEDIUM (0.5-0.8)"
            else:
                b_key = "HIGH (0.8-1.0)"

            bins[b_key]["conf"].append(r.confidence_score)
            bins[b_key]["correct"].append(outcome)

        brier_score = round(brier_sum / total, 4)

        confidence_bins = []
        total_ece = 0.0

        for b_name, b_data in bins.items():
            b_count = len(b_data["conf"])
            if b_count > 0:
                mean_conf = sum(b_data["conf"]) / b_count
                acc = sum(b_data["correct"]) / b_count
                gap = abs(acc - mean_conf)
                total_ece += (b_count / total) * gap
                confidence_bins.append(ConfidenceBin(
                    bin_range=b_name,
                    count=b_count,
                    mean_confidence=round(mean_conf, 3),
                    empirical_accuracy=round(acc, 3),
                    calibration_gap=round(gap, 3),
                ))

        ece = round(total_ece, 4)

        # Category breakdown
        category_breakdown = {}
        for r in results:
            cat_name = r.category.value
            if cat_name not in category_breakdown:
                category_breakdown[cat_name] = {"total": 0, "correct": 0, "tp": 0, "tn": 0, "fp": 0, "fn": 0}
            category_breakdown[cat_name]["total"] += 1
            if r.is_correct:
                category_breakdown[cat_name]["correct"] += 1
            if r.classification == "TRUE_POSITIVE":
                category_breakdown[cat_name]["tp"] += 1
            elif r.classification == "TRUE_NEGATIVE":
                category_breakdown[cat_name]["tn"] += 1
            elif r.classification == "FALSE_POSITIVE":
                category_breakdown[cat_name]["fp"] += 1
            elif r.classification == "FALSE_NEGATIVE":
                category_breakdown[cat_name]["fn"] += 1

        summary = (
            f"Adversarial Benchmark: {total} cases evaluated. "
            f"Precision: {precision:.2%}, Recall: {recall:.2%}, F1: {f1:.2%}, "
            f"FPR: {fpr:.2%}, FNR: {fnr:.2%}, Brier Score: {brier_score}."
        )

        return EvaluationReport(
            total_cases=total,
            true_positives=tp,
            true_negatives=tn,
            false_positives=fp,
            false_negatives=fn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            false_positive_rate=round(fpr, 4),
            false_negative_rate=round(fnr, 4),
            evidence_link_accuracy=round(evidence_accuracy, 4),
            tool_selection_accuracy=round(tool_selection_accuracy, 4),
            task_completion_rate=round(task_completion_rate, 4),
            mean_latency_ms=round(mean_latency, 2),
            brier_score=brier_score,
            expected_calibration_error=ece,
            confidence_bins=confidence_bins,
            category_breakdown=category_breakdown,
            summary_verdict=summary,
        )
