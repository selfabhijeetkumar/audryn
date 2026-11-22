from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class FindingCategory(str, Enum):
    REVENUE_AND_SALES = "REVENUE_AND_SALES"
    GENERAL_LEDGER = "GENERAL_LEDGER"
    FIXED_ASSETS_AND_DEPRECIATION = "FIXED_ASSETS_AND_DEPRECIATION"
    STATUTORY_RECONCILIATION = "STATUTORY_RECONCILIATION"
    TAX_COMPLIANCE = "TAX_COMPLIANCE"
    FORENSIC_ANOMALY = "FORENSIC_ANOMALY"


class FindingSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InvestigationFinding(BaseModel):
    """
    Structured audit finding produced by specialized investigation agents.
    Strictly evidence-backed with file, coordinate, and arithmetic provenance.
    """
    finding_id: str
    category: FindingCategory
    severity: FindingSeverity
    title: str
    description: str
    impact_amount: str = "0.00"  # String representation of Decimal
    currency: str = "USD"
    source_evidence: List[str] = Field(default_factory=list)
    coordinates: Dict[str, Any] = Field(default_factory=dict)  # page, row, sheet coordinates
    agent_role: str
    status: str = "OPEN"
    notes: Optional[str] = None


class InvestigationReport(BaseModel):
    """
    Aggregated investigation report returned by the CrewAI investigation team.
    """
    findings: List[InvestigationFinding] = Field(default_factory=list)
    summary: str
    total_anomalies_detected: int = 0
    total_impact_amount: str = "0.00"
    execution_successful: bool = True
