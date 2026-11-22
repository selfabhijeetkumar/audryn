from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    TAX_RETURN = "TAX_RETURN"
    BALANCE_SHEET = "BALANCE_SHEET"
    PROFIT_AND_LOSS = "PROFIT_AND_LOSS"
    TRIAL_BALANCE = "TRIAL_BALANCE"
    GENERAL_LEDGER = "GENERAL_LEDGER"
    INVOICE = "INVOICE"
    RECEIPT = "RECEIPT"
    BANK_STATEMENT = "BANK_STATEMENT"
    FIXED_ASSET_REGISTER = "FIXED_ASSET_REGISTER"
    UNKNOWN = "UNKNOWN"


class ExtractionStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    REQUIRES_OCR = "REQUIRES_OCR"
    CORRUPTED = "CORRUPTED"
    EMPTY = "EMPTY"
    FAILED = "FAILED"


class ProvenanceCoordinate(BaseModel):
    page_number: Optional[int] = None
    sheet_name: Optional[str] = None
    row_number: Optional[int] = None
    column_name: Optional[str] = None
    line_reference: Optional[str] = None
    extracted_text_snippet: Optional[str] = None


class EvidenceRecord(BaseModel):
    evidence_id: str
    original_filename: str
    sha256_hash: str
    file_size_bytes: int
    upload_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    document_type: DocumentType = DocumentType.UNKNOWN
    extraction_status: ExtractionStatus = ExtractionStatus.PENDING
    page_count: int = 0
    provenance_coordinates: List[ProvenanceCoordinate] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None
    raw_storage_path: Optional[str] = None
