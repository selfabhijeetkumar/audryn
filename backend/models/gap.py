from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class GapStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    NOT_CHECKED = "NOT_CHECKED"
    BLOCKED = "BLOCKED"
    UNRESOLVED = "UNRESOLVED"
    RESOLVED = "RESOLVED"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


class GapCategory(str, Enum):
    MISSING_DOCUMENT = "MISSING_DOCUMENT"
    MISSING_PERIOD = "MISSING_PERIOD"
    SOURCE_PROVENANCE_GAP = "SOURCE_PROVENANCE_GAP"
    UNVERIFIED_CALCULATION = "UNVERIFIED_CALCULATION"
    TOOL_FAILURE = "TOOL_FAILURE"
    MISSING_EVIDENCE_LINK = "MISSING_EVIDENCE_LINK"
    UNTESTED_PROCEDURE = "UNTESTED_PROCEDURE"
    UNRESOLVED_FINDING = "UNRESOLVED_FINDING"
    INCOMPLETE_EXECUTION = "INCOMPLETE_EXECUTION"


class GapSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GapItem(BaseModel):
    """
    Individual audit blind-spot tracked by GAP RADAR.
    Distinguishes unknown areas, unverified procedures, and investigation blockers.
    """
    gap_id: str
    category: GapCategory
    severity: GapSeverity
    description: str
    evidence_references: List[str] = Field(default_factory=list)
    root_cause_hypothesis: str
    recommended_resolution: str
    status: GapStatus
    regression_test_reference: Optional[str] = None


class GapRadarReport(BaseModel):
    """
    Comprehensive GAP RADAR report summarizing audit coverage blind spots.
    """
    gaps: List[GapItem] = Field(default_factory=list)
    total_gaps: int = 0
    critical_gaps: int = 0
    coverage_score_percent: float = 100.0
    audit_completeness_blocked: bool = False
