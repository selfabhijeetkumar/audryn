"""
AUDRYN Report Models.

Defines report identity, versioning, status lifecycle, section structures,
and the machine-readable JSON report schema.
"""
import hashlib
import json
from enum import Enum
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ReportStatus(str, Enum):
    DRAFT = "DRAFT"
    BLOCKED = "BLOCKED"
    REVIEW_READY = "REVIEW_READY"
    FINALIZED = "FINALIZED"


class ReportSectionType(str, Enum):
    COVER = "COVER"
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    SCOPE_AND_METHODOLOGY = "SCOPE_AND_METHODOLOGY"
    EVIDENCE_INVENTORY = "EVIDENCE_INVENTORY"
    FINANCIAL_RECONCILIATION = "FINANCIAL_RECONCILIATION"
    AUDIT_FINDINGS = "AUDIT_FINDINGS"
    COUNTER_EVIDENCE_ANALYSIS = "COUNTER_EVIDENCE_ANALYSIS"
    GAP_RADAR_COMPLETENESS = "GAP_RADAR_COMPLETENESS"
    HUMAN_REVIEW_REGISTER = "HUMAN_REVIEW_REGISTER"
    NOT_CHECKED_REGISTER = "NOT_CHECKED_REGISTER"
    RULEBOOK_TAX_METHODOLOGY = "RULEBOOK_TAX_METHODOLOGY"
    LIMITATIONS_DISCLAIMERS = "LIMITATIONS_DISCLAIMERS"
    APPENDICES = "APPENDICES"


class ReportSection(BaseModel):
    section_id: str
    section_type: ReportSectionType
    title: str
    content: Dict[str, Any] = Field(default_factory=dict)
    finding_references: List[str] = Field(default_factory=list)
    evidence_references: List[str] = Field(default_factory=list)
    source_hash_references: List[str] = Field(default_factory=list)


class ReportManifest(BaseModel):
    """Immutable record of exactly what data produced a report."""
    report_id: str
    audit_id: str
    report_version: int
    generated_at_utc: str
    evidence_document_count: int = 0
    evidence_sha256_manifest: List[str] = Field(default_factory=list)
    finding_count: int = 0
    finding_ids: List[str] = Field(default_factory=list)
    rulebook_version: str = "Income-tax Act, 1961"
    financial_periods: List[str] = Field(default_factory=list)
    data_snapshot_ref: Optional[str] = None
    report_content_hash: Optional[str] = None


class AuditReport(BaseModel):
    """
    Complete machine-readable AUDRYN audit report.
    Every figure is derived from persisted structured records.
    """
    report_id: str
    audit_id: str
    report_version: int = 1
    report_status: ReportStatus = ReportStatus.DRAFT
    generated_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    company_name: str = ""
    company_id: str = ""
    financial_periods: List[str] = Field(default_factory=list)
    currency: str = "INR"
    is_synthetic_data: bool = True
    synthetic_disclaimer: str = (
        "This report is based on SYNTHETIC demonstration data. "
        "The entity, CIN, financial records, and anomalies are entirely fictional. "
        "This report does not constitute a statutory audit opinion."
    )
    sections: List[ReportSection] = Field(default_factory=list)
    manifest: Optional[ReportManifest] = None
    release_gate_result: Optional[Dict[str, Any]] = None
    report_content_hash: Optional[str] = None

    def compute_content_hash(self) -> str:
        """Deterministic SHA-256 hash of the logical report content for tamper detection."""
        payload = {
            "report_id": self.report_id,
            "audit_id": self.audit_id,
            "report_version": self.report_version,
            "company_name": self.company_name,
            "financial_periods": self.financial_periods,
            "sections": [s.model_dump() for s in self.sections],
        }
        raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
