from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from backend.models.evidence import DocumentType


class GateStatus(str, Enum):
    PASSED = "PASSED"
    BLOCKED = "BLOCKED"
    IN_PROGRESS = "IN_PROGRESS"


class RequiredDocumentRule(BaseModel):
    rule_id: str
    document_type: DocumentType
    display_name: str
    is_mandatory: bool = True
    minimum_count: int = 1
    description: str


class CompletenessEvaluation(BaseModel):
    rule: RequiredDocumentRule
    matched_count: int = 0
    matched_evidence_ids: List[str] = Field(default_factory=list)
    is_satisfied: bool = False
    missing_count: int = 0
    remarks: Optional[str] = None


class CompletenessGateResult(BaseModel):
    audit_id: str
    gate_status: GateStatus
    total_required: int
    total_satisfied: int
    evaluations: List[CompletenessEvaluation] = Field(default_factory=list)
    missing_documents: List[str] = Field(default_factory=list)
    corrupted_documents: List[str] = Field(default_factory=list)
    unprocessed_documents: List[str] = Field(default_factory=list)
    requires_human_review: List[str] = Field(default_factory=list)
    can_proceed_to_report: bool = False
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
