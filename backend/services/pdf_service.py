import io
from typing import List, Dict, Any, Tuple, Optional
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from backend.models.evidence import (
    DocumentType,
    ExtractionStatus,
    ProvenanceCoordinate,
    EvidenceRecord,
)
from backend.services.evidence_service import EvidenceService


class PDFServiceException(Exception):
    pass


class PDFCorruptedError(PDFServiceException):
    pass


class PDFEmptyError(PDFServiceException):
    pass


class PDFIntelligenceService:
    """
    Multi-format PDF Document Intelligence for financial statements and audit packages.
    Implements validation, classification, provenance extraction, and OCR-ready abstraction.
    """

    MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB safety limit
    PDF_MAGIC_BYTES = b"%PDF-"

    def __init__(self, evidence_service: Optional[EvidenceService] = None):
        self.evidence_service = evidence_service or EvidenceService()

    def validate_pdf_bytes(self, file_bytes: bytes, filename: str) -> None:
        """Validates file size, non-emptiness, and magic byte signatures."""
        if not file_bytes or len(file_bytes) == 0:
            raise PDFEmptyError(f"File '{filename}' is empty (0 bytes).")

        if len(file_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise PDFServiceException(
                f"File '{filename}' exceeds maximum allowed size of {self.MAX_FILE_SIZE_BYTES / (1024 * 1024)} MB."
            )

        if not file_bytes.startswith(self.PDF_MAGIC_BYTES):
            raise PDFCorruptedError(f"File '{filename}' does not have a valid PDF header signature (%PDF-).")

    def classify_document(self, combined_text: str) -> DocumentType:
        """Rule-based financial document classifier based on statutory audit keywords."""
        text_lower = combined_text.lower()

        if "trial balance" in text_lower or ("debit" in text_lower and "credit" in text_lower and "opening balance" in text_lower):
            return DocumentType.TRIAL_BALANCE
        if "balance sheet" in text_lower or ("equity and liabilities" in text_lower and "assets" in text_lower):
            return DocumentType.BALANCE_SHEET
        if "profit and loss" in text_lower or "statement of income" in text_lower or "revenue from operations" in text_lower:
            return DocumentType.PROFIT_AND_LOSS
        if "income tax return" in text_lower or "form 3cd" in text_lower or "itr-" in text_lower or "tax computation" in text_lower:
            return DocumentType.TAX_RETURN
        if "general ledger" in text_lower or "ledger account" in text_lower or "voucher no" in text_lower:
            return DocumentType.GENERAL_LEDGER
        if "fixed asset register" in text_lower or "depreciation schedule" in text_lower or "wdv" in text_lower:
            return DocumentType.FIXED_ASSET_REGISTER
        if "bank statement" in text_lower or "account statement" in text_lower or "clearing balance" in text_lower:
            return DocumentType.BANK_STATEMENT
        if "tax invoice" in text_lower or "invoice no" in text_lower or "bill to" in text_lower:
            return DocumentType.INVOICE
        if "receipt voucher" in text_lower or "payment receipt" in text_lower:
            return DocumentType.RECEIPT

        return DocumentType.UNKNOWN

    def ingest_pdf(
        self,
        file_bytes: bytes,
        original_filename: str,
        hint_type: Optional[DocumentType] = None,
    ) -> Tuple[EvidenceRecord, Dict[str, Any]]:
        """
        Comprehensive PDF ingestion pipeline.
        Returns the registered EvidenceRecord and extracted page-by-page contents.
        """
        # 1. Byte & Header Validation
        self.validate_pdf_bytes(file_bytes, original_filename)

        # 2. Register Evidence with SHA-256 fingerprinting
        evidence_record = self.evidence_service.register_evidence(
            file_bytes=file_bytes,
            original_filename=original_filename,
            document_type=hint_type or DocumentType.UNKNOWN,
        )

        # 3. Read and Extract Pages
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
        except (PdfReadError, Exception) as e:
            self.evidence_service.update_extraction_status(
                evidence_record.sha256_hash,
                status=ExtractionStatus.CORRUPTED,
            )
            raise PDFCorruptedError(f"Failed to read PDF '{original_filename}': {str(e)}")

        page_count = len(reader.pages)
        if page_count == 0:
            self.evidence_service.update_extraction_status(
                evidence_record.sha256_hash,
                status=ExtractionStatus.EMPTY,
            )
            raise PDFEmptyError(f"PDF '{original_filename}' has 0 pages.")

        # Metadata extraction
        raw_meta = reader.metadata or {}
        extracted_metadata = {
            "title": str(raw_meta.get("/Title", "")),
            "author": str(raw_meta.get("/Author", "")),
            "creator": str(raw_meta.get("/Creator", "")),
            "producer": str(raw_meta.get("/Producer", "")),
            "creation_date": str(raw_meta.get("/CreationDate", "")),
        }

        # Page-by-page text extraction
        pages_content: List[Dict[str, Any]] = []
        provenance_coords: List[ProvenanceCoordinate] = []
        all_text_accumulated: List[str] = []
        non_empty_page_count = 0

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            text = page.extract_text() or ""
            stripped = text.strip()
            is_empty = len(stripped) == 0

            if not is_empty:
                non_empty_page_count += 1
                all_text_accumulated.append(stripped)

            snippet = stripped[:150] if not is_empty else "[EMPTY PAGE]"

            coord = ProvenanceCoordinate(
                page_number=page_num,
                line_reference=f"Page {page_num}",
                extracted_text_snippet=snippet,
            )
            provenance_coords.append(coord)

            pages_content.append({
                "page_number": page_num,
                "text": text,
                "is_empty": is_empty,
                "char_count": len(stripped),
            })

        combined_text = "\n".join(all_text_accumulated)

        # 4. OCR Abstraction Detection
        # If pages exist but zero text was extractable, document is scanned/image-only
        if non_empty_page_count == 0 and page_count > 0:
            status = ExtractionStatus.REQUIRES_OCR
            doc_type = hint_type or DocumentType.UNKNOWN
            pages_content.append({
                "ocr_warning": "No digital text layer found. Document is image-only/scanned and requires OCR processing."
            })
        else:
            status = ExtractionStatus.SUCCESS
            doc_type = hint_type or self.classify_document(combined_text)

        # Update EvidenceRecord in vault
        self.evidence_service.update_extraction_status(
            sha256_hash=evidence_record.sha256_hash,
            status=status,
            page_count=page_count,
            coordinates=provenance_coords,
            document_type=doc_type,
        )

        extraction_result = {
            "evidence_id": evidence_record.evidence_id,
            "filename": original_filename,
            "sha256_hash": evidence_record.sha256_hash,
            "document_type": doc_type,
            "extraction_status": status,
            "page_count": page_count,
            "non_empty_pages": non_empty_page_count,
            "metadata": extracted_metadata,
            "pages": pages_content,
            "provenance_coordinates": [c.model_dump() for c in provenance_coords],
        }

        return evidence_record, extraction_result
