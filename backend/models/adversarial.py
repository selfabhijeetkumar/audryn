from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AdversarialScenarioType(str, Enum):
    TRUE_ANOMALY = "TRUE_ANOMALY"                           # System SHOULD flag
    BENIGN_LEGITIMATE_TRANSACTION = "BENIGN_LEGITIMATE_TRANSACTION" # System SHOULD NOT flag


class AdversarialCategory(str, Enum):
    # Existing known categories
    ARITHMETIC_IMBALANCE = "ARITHMETIC_IMBALANCE"
    EQUATION_DISCREPANCY = "EQUATION_DISCREPANCY"
    ROLL_FORWARD_DISCONTINUITY = "ROLL_FORWARD_DISCONTINUITY"
    STATUTORY_TAX_CALCULATION = "STATUTORY_TAX_CALCULATION"
    DEPRECIATION_RATE_ERROR = "DEPRECIATION_RATE_ERROR"
    CROSS_YEAR_INVENTORY_SPIKE = "CROSS_YEAR_INVENTORY_SPIKE"
    MATERIALITY_THRESHOLD_BREACH = "MATERIALITY_THRESHOLD_BREACH"
    
    # Challenging edge categories
    LEGITIMATE_CREDIT_NOTE_REVERSAL = "LEGITIMATE_CREDIT_NOTE_REVERSAL"
    LEGITIMATE_TIMING_DIFFERENCE = "LEGITIMATE_TIMING_DIFFERENCE"
    DUPLICATE_LEGITIMATE_INVOICE_NUMBER = "DUPLICATE_LEGITIMATE_INVOICE_NUMBER"
    SPLIT_TRANSACTION = "SPLIT_TRANSACTION"
    LEDGER_CUTOFF_DIFFERENCE = "LEDGER_CUTOFF_DIFFERENCE"
    SIMILAR_VENDOR_NAME = "SIMILAR_VENDOR_NAME"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    INCORRECT_DATE = "INCORRECT_DATE"
    MISSING_SUPPORTING_EVIDENCE = "MISSING_SUPPORTING_EVIDENCE"
    CORRUPTED_DOCUMENT_PAGE = "CORRUPTED_DOCUMENT_PAGE"
    POOR_OCR_EXTRACTION = "POOR_OCR_EXTRACTION"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    INCOMPLETE_CROSS_YEAR_RECORD = "INCOMPLETE_CROSS_YEAR_RECORD"
    CONFLICTING_FINANCIAL_DOCUMENTS = "CONFLICTING_FINANCIAL_DOCUMENTS"
    INELIGIBLE_TAX_DEDUCTION = "INELIGIBLE_TAX_DEDUCTION"


class AdversarialTestCase(BaseModel):
    """
    Isolated test case for the Adversarial Challenge Lab.
    Ground-truth labels are kept strictly separate from investigation agents.
    """
    test_id: str
    category: AdversarialCategory
    scenario_type: AdversarialScenarioType
    title: str
    description: str
    input_payload: Dict[str, Any]
    expected_detection: bool  # True if system should flag, False if benign
    statutory_ground_truth: str
    target_component: str


class AdversarialTestResult(BaseModel):
    test_id: str
    category: AdversarialCategory
    scenario_type: AdversarialScenarioType
    detected_by_system: bool
    is_correct: bool
    classification: str  # "TRUE_POSITIVE", "TRUE_NEGATIVE", "FALSE_POSITIVE", "FALSE_NEGATIVE"
    confidence_score: float = 1.0
    evidence_linked: bool = True
    execution_time_ms: float = 0.0
    notes: Optional[str] = None
