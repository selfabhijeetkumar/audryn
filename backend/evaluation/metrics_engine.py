"""
AUDRYN Formal Evaluation Metrics Engine.

Calculates rigorous statistical and mathematical evaluation metrics:
- Confusion matrices (TP, TN, FP, FN, Ambiguous)
- Precision, Recall, F1, Specificity, FPR, FNR, Accuracy
- Zero-denominator guard policies
- 10-bin Expected Calibration Error (ECE) and Brier Score
- 95% Bootstrap Confidence Intervals (1000 resamples)
- Per-category breakdowns and evidence-quality metrics
"""
import math
import random
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

from backend.evaluation.models import (
    ScenarioExecutionResult,
    ScenarioCategory,
    ExpectedOutcome,
    ExecutionStatus,
    ConfusionMatrix,
    CategoryMetrics,
    ConfidenceInterval,
)


class FormalMetricsEngine:
    """
    Computes formal statistical evaluation metrics for autonomous financial audit systems.
    Guarantees mathematical correctness, explicit zero handling, and bootstrap uncertainty.
    """

    @classmethod
    def evaluate_results(
        cls,
        results: List[ScenarioExecutionResult],
        bootstrap_seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Processes a list of ScenarioExecutionResults and computes the complete metric suite.
        """
        if not results:
            raise ValueError("Cannot compute evaluation metrics on empty results list.")

        total = len(results)
        tp = 0
        tn = 0
        fp = 0
        fn = 0
        ambiguous_correct = 0

        # Category trackers
        cat_data: Dict[ScenarioCategory, Dict[str, int]] = {}

        for r in results:
            cat = r.category
            if cat not in cat_data:
                cat_data[cat] = {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "total": 0, "ambiguous_correct": 0}
            cat_data[cat]["total"] += 1

            # Classification logic based on expected vs actual
            is_anomaly_expected = r.expected_outcome in (
                ExpectedOutcome.ANOMALY_DETECTED,
                ExpectedOutcome.INJECTION_NEUTRALIZED,
                ExpectedOutcome.TAX_BLOCKED,
            )
            is_benign_expected = r.expected_outcome == ExpectedOutcome.BENIGN_CLEARED
            is_ambiguous_expected = r.expected_outcome in (
                ExpectedOutcome.UNRESOLVED,
                ExpectedOutcome.INSUFFICIENT_EVIDENCE,
            )

            if is_ambiguous_expected:
                if r.actual_outcome in (ExpectedOutcome.UNRESOLVED, ExpectedOutcome.INSUFFICIENT_EVIDENCE):
                    ambiguous_correct += 1
                    cat_data[cat]["ambiguous_correct"] += 1
                elif r.actual_outcome == ExpectedOutcome.ANOMALY_DETECTED:
                    # Prematurely flagged ambiguous case as confirmed anomaly
                    fp += 1
                    cat_data[cat]["fp"] += 1
                else:
                    fn += 1
                    cat_data[cat]["fn"] += 1

            elif is_benign_expected:
                if r.actual_outcome == ExpectedOutcome.BENIGN_CLEARED:
                    tn += 1
                    cat_data[cat]["tn"] += 1
                else:
                    fp += 1
                    cat_data[cat]["fp"] += 1

            elif is_anomaly_expected:
                if r.actual_outcome == r.expected_outcome or (r.actual_outcome == ExpectedOutcome.ANOMALY_DETECTED):
                    tp += 1
                    cat_data[cat]["tp"] += 1
                else:
                    fn += 1
                    cat_data[cat]["fn"] += 1

        matrix = ConfusionMatrix(
            true_positives=tp,
            true_negatives=tn,
            false_positives=fp,
            false_negatives=fn,
            ambiguous_correct=ambiguous_correct,
            total_samples=total,
        )

        # Standard Classification Formulas with zero-denominator guards
        precision = tp / (tp + fp) if (tp + fp) > 0 else None
        recall = tp / (tp + fn) if (tp + fn) > 0 else None
        specificity = tn / (tn + fp) if (tn + fp) > 0 else None
        
        if precision is not None and recall is not None and (precision + recall) > 0:
            f1 = (2 * precision * recall) / (precision + recall)
        else:
            f1 = None

        fpr = fp / (fp + tn) if (fp + tn) > 0 else None
        fnr = fn / (tp + fn) if (tp + fn) > 0 else None
        accuracy = (tp + tn + ambiguous_correct) / total if total > 0 else 0.0

        # Category breakdowns
        cat_metrics: Dict[str, CategoryMetrics] = {}
        for c, d in cat_data.items():
            c_tp = d["tp"]
            c_tn = d["tn"]
            c_fp = d["fp"]
            c_fn = d["fn"]
            c_tot = d["total"]
            c_amb = d["ambiguous_correct"]

            c_prec = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else None
            c_rec = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else None
            c_spec = c_tn / (c_tn + c_fp) if (c_tn + c_fp) > 0 else None
            c_f1 = (2 * c_prec * c_rec) / (c_prec + c_rec) if (c_prec and c_rec and (c_prec + c_rec) > 0) else None
            c_fpr = c_fp / (c_fp + c_tn) if (c_fp + c_tn) > 0 else None
            c_fnr = c_fn / (c_tp + c_fn) if (c_tp + c_fn) > 0 else None
            c_acc = (c_tp + c_tn + c_amb) / c_tot if c_tot > 0 else 0.0

            cat_metrics[c.value] = CategoryMetrics(
                category=c,
                total_cases=c_tot,
                true_positives=c_tp,
                true_negatives=c_tn,
                false_positives=c_fp,
                false_negatives=c_fn,
                precision=c_prec,
                recall=c_rec,
                f1_score=c_f1,
                specificity=c_spec,
                false_positive_rate=c_fpr,
                false_negative_rate=c_fnr,
                accuracy=c_acc,
            )

        # Calibration Metrics (Brier Score & 10-bin ECE)
        brier_score = cls._compute_brier_score(results)
        ece = cls._compute_ece_10_bins(results)

        # Bootstrap Confidence Intervals (95% CI)
        cis = cls._compute_bootstrap_cis(results, seed=bootstrap_seed)

        # Evidence and Quality Metrics
        evidence_accuracy = sum(1 for r in results if r.evidence_linked) / total
        coord_accuracy = sum(1 for r in results if r.source_coordinate_valid) / total
        calc_accuracy = sum(1 for r in results if r.calculation_verified) / total
        mean_latency = sum(r.execution_time_ms for r in results) / total

        return {
            "confusion_matrix": matrix,
            "overall_precision": precision,
            "overall_recall": recall,
            "overall_f1": f1,
            "overall_specificity": specificity,
            "overall_fpr": fpr,
            "overall_fnr": fnr,
            "overall_accuracy": accuracy,
            "brier_score": brier_score,
            "expected_calibration_error": ece,
            "confidence_intervals": cis,
            "category_metrics": cat_metrics,
            "evidence_link_accuracy": evidence_accuracy,
            "source_coordinate_accuracy": coord_accuracy,
            "calculation_accuracy": calc_accuracy,
            "mean_latency_ms": mean_latency,
        }

    @staticmethod
    def _compute_brier_score(results: List[ScenarioExecutionResult]) -> float:
        """
        Brier Score = (1/N) * sum((predicted_confidence - actual_binary_outcome)^2).
        Optimal score -> 0.0.
        """
        n = len(results)
        if n == 0:
            return 0.0
        total_sq_err = 0.0
        for r in results:
            is_correct = 1.0 if r.status == ExecutionStatus.PASS else 0.0
            p = max(0.0, min(1.0, r.confidence))
            total_sq_err += (p - is_correct) ** 2
        return round(total_sq_err / n, 4)

    @staticmethod
    def _compute_ece_10_bins(results: List[ScenarioExecutionResult]) -> float:
        """
        Expected Calibration Error across 10 equal bins [0.0 - 0.1], ..., (0.9 - 1.0].
        """
        n = len(results)
        if n == 0:
            return 0.0

        bins = [[] for _ in range(10)]
        for r in results:
            p = max(0.0, min(1.0, r.confidence))
            idx = min(int(p * 10), 9)
            is_correct = 1.0 if r.status == ExecutionStatus.PASS else 0.0
            bins[idx].append((p, is_correct))

        ece = 0.0
        for b in bins:
            if not b:
                continue
            bin_size = len(b)
            avg_conf = sum(x[0] for x in b) / bin_size
            avg_acc = sum(x[1] for x in b) / bin_size
            ece += (bin_size / n) * abs(avg_acc - avg_conf)

        return round(ece, 4)

    @staticmethod
    def _compute_bootstrap_cis(
        results: List[ScenarioExecutionResult],
        n_bootstraps: int = 1000,
        seed: int = 42,
    ) -> List[ConfidenceInterval]:
        """
        Computes 95% bootstrap percentile confidence intervals for Precision, Recall, and F1.
        """
        rng = random.Random(seed)
        n = len(results)
        if n < 5:
            return []

        precisions = []
        recalls = []
        f1s = []

        for _ in range(n_bootstraps):
            sample = [rng.choice(results) for _ in range(n)]
            tp = sum(1 for r in sample if r.status == ExecutionStatus.PASS and r.expected_outcome in (
                ExpectedOutcome.ANOMALY_DETECTED, ExpectedOutcome.INJECTION_NEUTRALIZED, ExpectedOutcome.TAX_BLOCKED
            ))
            fp = sum(1 for r in sample if r.status == ExecutionStatus.FAIL and r.expected_outcome == ExpectedOutcome.BENIGN_CLEARED)
            fn = sum(1 for r in sample if r.status == ExecutionStatus.FAIL and r.expected_outcome != ExpectedOutcome.BENIGN_CLEARED)

            p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0

            precisions.append(p)
            recalls.append(r)
            f1s.append(f)

        precisions.sort()
        recalls.sort()
        f1s.sort()

        low_idx = int(0.025 * n_bootstraps)
        high_idx = int(0.975 * n_bootstraps)

        # Point estimates
        real_tp = sum(1 for r in results if r.status == ExecutionStatus.PASS and r.expected_outcome in (
            ExpectedOutcome.ANOMALY_DETECTED, ExpectedOutcome.INJECTION_NEUTRALIZED, ExpectedOutcome.TAX_BLOCKED
        ))
        real_fp = sum(1 for r in results if r.status == ExecutionStatus.FAIL and r.expected_outcome == ExpectedOutcome.BENIGN_CLEARED)
        real_fn = sum(1 for r in results if r.status == ExecutionStatus.FAIL and r.expected_outcome != ExpectedOutcome.BENIGN_CLEARED)

        real_p = real_tp / (real_tp + real_fp) if (real_tp + real_fp) > 0 else 0.0
        real_r = real_tp / (real_tp + real_fn) if (real_tp + real_fn) > 0 else 0.0
        real_f = (2 * real_p * real_r) / (real_p + real_r) if (real_p + real_r) > 0 else 0.0

        return [
            ConfidenceInterval(
                metric_name="Precision",
                point_estimate=round(real_p, 4),
                lower_95=round(precisions[low_idx], 4),
                upper_95=round(precisions[high_idx], 4),
            ),
            ConfidenceInterval(
                metric_name="Recall",
                point_estimate=round(real_r, 4),
                lower_95=round(recalls[low_idx], 4),
                upper_95=round(recalls[high_idx], 4),
            ),
            ConfidenceInterval(
                metric_name="F1_Score",
                point_estimate=round(real_f, 4),
                lower_95=round(f1s[low_idx], 4),
                upper_95=round(f1s[high_idx], 4),
            ),
        ]
