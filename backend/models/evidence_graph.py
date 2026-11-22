"""
AUDRYN Evidence Graph Models.

Defines the typed nodes, relationships, source locations, and traversal schemas
for the AUDRYN Evidence Graph.
"""
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, model_validator


class NodeType(str, Enum):
    AUDIT = "AUDIT"
    ENTITY = "ENTITY"
    EVIDENCE_DOCUMENT = "EVIDENCE_DOCUMENT"
    SOURCE_LOCATION = "SOURCE_LOCATION"
    EXTRACTED_FACT = "EXTRACTED_FACT"
    FINANCIAL_TRANSACTION = "FINANCIAL_TRANSACTION"
    FINANCIAL_CALCULATION = "FINANCIAL_CALCULATION"
    TAX_RULE = "TAX_RULE"
    AUDIT_FINDING = "AUDIT_FINDING"
    COUNTER_EVIDENCE = "COUNTER_EVIDENCE"
    GAP = "GAP"
    REVIEW_DECISION = "REVIEW_DECISION"
    REPORT = "REPORT"
    REPORT_SECTION = "REPORT_SECTION"


class RelationshipType(str, Enum):
    AUDIT_CONTAINS_DOCUMENT = "AUDIT_CONTAINS_DOCUMENT"
    DOCUMENT_CONTAINS_SOURCE_LOCATION = "DOCUMENT_CONTAINS_SOURCE_LOCATION"
    SOURCE_LOCATION_SUPPORTS_FACT = "SOURCE_LOCATION_SUPPORTS_FACT"
    FACT_RELATES_TO_TRANSACTION = "FACT_RELATES_TO_TRANSACTION"
    TRANSACTION_BELONGS_TO_ENTITY = "TRANSACTION_BELONGS_TO_ENTITY"
    TRANSACTION_MATCHES_TRANSACTION = "TRANSACTION_MATCHES_TRANSACTION"
    TRANSACTION_CONTRADICTS_TRANSACTION = "TRANSACTION_CONTRADICTS_TRANSACTION"
    TRANSACTION_SUPPORTS_CALCULATION = "TRANSACTION_SUPPORTS_CALCULATION"
    CALCULATION_USES_RULE = "CALCULATION_USES_RULE"
    CALCULATION_SUPPORTS_FINDING = "CALCULATION_SUPPORTS_FINDING"
    DOCUMENT_SUPPORTS_FINDING = "DOCUMENT_SUPPORTS_FINDING"
    DOCUMENT_CONTRADICTS_FINDING = "DOCUMENT_CONTRADICTS_FINDING"
    FINDING_HAS_COUNTER_EVIDENCE = "FINDING_HAS_COUNTER_EVIDENCE"
    FINDING_HAS_GAP = "FINDING_HAS_GAP"
    FINDING_REQUIRES_REVIEW = "FINDING_REQUIRES_REVIEW"
    FINDING_HAS_REVIEW_DECISION = "FINDING_HAS_REVIEW_DECISION"
    REPORT_CONTAINS_SECTION = "REPORT_CONTAINS_SECTION"
    REPORT_SECTION_REFERENCES_FINDING = "REPORT_SECTION_REFERENCES_FINDING"
    REPORT_SECTION_CITES_EVIDENCE = "REPORT_SECTION_CITES_EVIDENCE"


class SourceLocation(BaseModel):
    """
    Exact coordinates of an extracted fact within an original source document.
    Never fabricated: unfilled fields remain None.
    """
    location_id: str
    evidence_id: str
    file_path: Optional[str] = None
    page_number: Optional[int] = None
    bounding_box: Optional[Dict[str, float]] = None  # x0, y0, x1, y1
    sheet_name: Optional[str] = None
    row_number: Optional[int] = None
    column_name: Optional[str] = None
    cell_reference: Optional[str] = None
    line_reference: Optional[str] = None
    voucher_number: Optional[str] = None
    raw_snippet: Optional[str] = None
    is_traceable: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphNode(BaseModel):
    """
    A typed, auditable node in the AUDRYN Evidence Graph.
    """
    node_id: str
    audit_id: str
    node_type: NodeType
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @model_validator(mode="after")
    def validate_audit_id(self):
        if not self.audit_id or not self.audit_id.strip():
            raise ValueError("Node must have a valid non-empty audit_id.")
        if not self.node_id or not self.node_id.strip():
            raise ValueError("Node must have a valid non-empty node_id.")
        return self


class GraphRelationship(BaseModel):
    """
    A typed, auditable directed edge in the AUDRYN Evidence Graph.
    Enforces audit-level boundary isolation between source and target.
    """
    relationship_id: str
    audit_id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    provenance: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    validation_status: str = "VALIDATED"

    @model_validator(mode="after")
    def validate_ids(self):
        if not self.audit_id or not self.audit_id.strip():
            raise ValueError("Relationship must have a valid non-empty audit_id.")
        if not self.source_id or not self.source_id.strip():
            raise ValueError("Relationship must have a valid non-empty source_id.")
        if not self.target_id or not self.target_id.strip():
            raise ValueError("Relationship must have a valid non-empty target_id.")
        if self.source_id == self.target_id:
            raise ValueError("Self-referencing relationships are prohibited in Evidence Graph.")
        return self


class TraceabilityChain(BaseModel):
    """
    Represents the full provenance chain from source document to report section.
    Chain: Document -> SourceLocation -> ExtractedFact/Transaction -> Calculation -> Finding -> Review -> ReportSection
    """
    audit_id: str
    finding_id: str
    document_ids: List[str] = Field(default_factory=list)
    source_locations: List[Dict[str, Any]] = Field(default_factory=list)
    transactions: List[Dict[str, Any]] = Field(default_factory=list)
    calculations: List[Dict[str, Any]] = Field(default_factory=list)
    counter_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    review_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    report_sections: List[str] = Field(default_factory=list)
    is_complete: bool = False
    unresolved_links: List[str] = Field(default_factory=list)
