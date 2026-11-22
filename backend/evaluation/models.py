"""
AUDRYN Evaluation Data Models.

Defines schemas for benchmark scenarios, evaluation execution results,
confusion matrices, category breakdowns, bootstrap confidence intervals,
and formal evaluation manifests.
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class BenchmarkVersion(str, Enum):
    V1_BASELINE = "V1_BASELINE"      # Immutable Phase 4 25-scenario baseline
    V2_EXPANDED = "V2_EXPANDED"      # Phase 6 60-scenario multi-scale suite


class ScaleLevel(str, Enum):
    BASELINE = "BASELINE"   # Small: ~100 records, 3 fiscal years
    MEDIUM = "MEDIUM"       # Medium: ~500 records, expanded vendors/customers
    LARGE = "LARGE"         # Large: ~2000 records, complex cash/bank ledgers


class ScenarioCategory(str, Enum):
    FINANCIAL_ANOMALY = "FINANCIAL_ANOMALY"
    BENIGN_COMMERCIAL = "BENIGN_COMMERCIAL"
    AMBIGUOUS_CASE = "AMBIGUOUS_CASE"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    TIMING_CUTOFF = "TIMING_CUTOFF"
    TAX_RULEBOOK = "TAX_RULEBOOK"
    CROSS_YEAR = "CROSS_YEAR"
    COMPOUND_CASE = "COMPOUND_CASE"


class ExpectedOutcome(str, Enum):
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    BENIGN_CLEARED = "BENIGN_CLEARED"
    UNRESOLVED = "UNRESOLVED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INJECTION_NEUTRALIZED = "INJECTION_NEUTRALIZED"
    TAX_BLOCKED = "TAX_BLOCKED"


class ExecutionStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    ERROR = "ERROR"


class ConfidenceInterval(BaseModel):
    metric_name: str
    point_estimate: float
    lower_95: float
    upper_95: float
    bootstrap_samples: int = 1000


class EvaluationScenario(BaseModel):
    scenario_id: str
    benchmark_version: BenchmarkVersion = BenchmarkVersion.V2_EXPANDED
    category: ScenarioCategory
    title: str
    description: str
    input_payload: Dict[str, Any]
    expected_outcome: ExpectedOutcome
    statutory_basis: str
    target_component: str
    scale_applicability: List[ScaleLevel] = Field(
        default_factory=lambda: [ScaleLevel.BASELINE, ScaleLevel.MEDIUM, ScaleLevel.LARGE]
    )
    is_ground_truth_isolated: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScenarioExecutionResult(BaseModel):
    scenario_id: str
    benchmark_version: BenchmarkVersion
    category: ScenarioCategory
    expected_outcome: ExpectedOutcome
    actual_outcome: ExpectedOutcome
    status: ExecutionStatus
    confidence: float = 0.95
    execution_time_ms: float = 0.0
    evidence_linked: bool = True
    source_coordinate_valid: bool = True
    calculation_verified: bool = True
    failure_reason: Optional[str] = None
    finding_reference: Optional[str] = None
    evidence_reference: Optional[str] = None


class ConfusionMatrix(BaseModel):
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous_correct: int = 0
    total_samples: int = 0


class CategoryMetrics(BaseModel):
    category: ScenarioCategory
    total_cases: int
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    specificity: Optional[float] = None
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None
    accuracy: float = 0.0


class BenchmarkManifest(BaseModel):
    benchmark_id: str
    version: BenchmarkVersion
    scale: ScaleLevel
    random_seed: int
    scenario_count: int
    categories_breakdown: Dict[str, int]
    ground_truth_sha256: str
    software_version: str = "AUDRYN v1.0.0-phase6"
    rulebook_version: str = "Income-tax Act, 1961"
    generated_at_utc: str


class BenchmarkEvaluationReport(BaseModel):
    manifest: BenchmarkManifest
    confusion_matrix: ConfusionMatrix
    overall_precision: Optional[float]
    overall_recall: Optional[float]
    overall_f1: Optional[float]
    overall_specificity: Optional[float]
    overall_fpr: Optional[float]
    overall_fnr: Optional[float]
    overall_accuracy: float
    brier_score: float
    expected_calibration_error: float
    confidence_intervals: List[ConfidenceInterval] = Field(default_factory=list)
    category_metrics: Dict[str, CategoryMetrics] = Field(default_factory=dict)
    evidence_link_accuracy: float
    source_coordinate_accuracy: float
    calculation_accuracy: float
    gap_radar_detection_rate: float
    mean_latency_ms: float
    total_execution_time_s: float
    failure_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    executive_verdict: str
