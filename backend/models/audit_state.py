from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RiskClassification(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class HumanReviewStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"


class FinalReportStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    BLOCKED = "BLOCKED"
    IN_PROGRESS = "IN_PROGRESS"
    FINALIZED = "FINALIZED"


class AuditState(BaseModel):
    """
    Typed, Pydantic-backed state model for AUDRYN LangGraph Supervisor.
    Maintains persistent financial investigation state across checkpoints.
    """
    audit_id: str
    company_id: str
    company_name: str
    financial_periods: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    extracted_records: Dict[str, Any] = Field(default_factory=dict)
    completeness_status: str = "PENDING"
    reconciliation_results: List[Dict[str, Any]] = Field(default_factory=list)
    investigation_findings: List[Dict[str, Any]] = Field(default_factory=list)
    counter_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    verification_results: List[Dict[str, Any]] = Field(default_factory=list)
    gap_register: List[Dict[str, Any]] = Field(default_factory=list)
    risk_classification: RiskClassification = RiskClassification.LOW
    human_review_status: HumanReviewStatus = HumanReviewStatus.NOT_REQUIRED
    human_reviewer_comments: Optional[str] = None
    final_report_status: FinalReportStatus = FinalReportStatus.NOT_STARTED
    execution_errors: List[str] = Field(default_factory=list)
    retry_count: int = 0
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)
