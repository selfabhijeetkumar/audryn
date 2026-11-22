from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ProcedureStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    NOT_CHECKED = "NOT_CHECKED"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class AuditArea(str, Enum):
    CASH_AND_BANK = "CASH_AND_BANK"
    REVENUE_AND_SALES = "REVENUE_AND_SALES"
    PURCHASES_AND_PAYABLES = "PURCHASES_AND_PAYABLES"
    FIXED_ASSETS_AND_DEPRECIATION = "FIXED_ASSETS_AND_DEPRECIATION"
    PAYROLL_AND_EXPENSES = "PAYROLL_AND_EXPENSES"
    TAX_COMPLIANCE = "TAX_COMPLIANCE"
    STATUTORY_RECONCILIATION = "STATUTORY_RECONCILIATION"
    GENERAL_LEDGER = "GENERAL_LEDGER"


class NotCheckedItem(BaseModel):
    procedure_id: str
    audit_area: AuditArea
    title: str
    description: str
    status: ProcedureStatus = ProcedureStatus.NOT_CHECKED
    reason_not_checked: Optional[str] = None
    required_evidence: List[str] = Field(default_factory=list)
    associated_evidence_ids: List[str] = Field(default_factory=list)
    responsible_reviewer: str = "Unassigned"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None
