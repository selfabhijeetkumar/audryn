import io
from typing import List, Dict, Any, Tuple, Optional
from decimal import Decimal, InvalidOperation
import pandas as pd
import openpyxl

from backend.models.evidence import (
    DocumentType,
    ExtractionStatus,
    ProvenanceCoordinate,
    EvidenceRecord,
)
from backend.services.evidence_service import EvidenceService


class SpreadsheetServiceException(Exception):
    pass


class SpreadsheetCorruptedError(SpreadsheetServiceException):
    pass


class SpreadsheetIntelligenceService:
    """
    Excel (.xlsx) and CSV document intelligence.
    Handles workbook inspection, column mapping, row extraction,
    data validation, currency normalization, and provenance tracking.
    """

    def __init__(self, evidence_service: Optional[EvidenceService] = None):
        self.evidence_service = evidence_service or EvidenceService()

    @staticmethod
    def normalize_currency_decimal(value: Any) -> Decimal:
        """
        Converts monetary amounts (e.g., '$1,200.50', '(500.00)', '1200')
        deterministically to Decimal without using floating point numbers.
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return Decimal("0.00")
        if isinstance(value, Decimal):
            return value

        val_str = str(value).strip()
        if not val_str or val_str.lower() in ("nan", "none", "-", ""):
            return Decimal("0.00")

        # Handle accounting parenthesis for negative numbers, e.g., (1,000.00)
        is_negative = False
        if val_str.startswith("(") and val_str.endswith(")"):
            is_negative = True
            val_str = val_str[1:-1]
        elif val_str.startswith("-"):
            is_negative = True
            val_str = val_str[1:]

        # Strip currency symbols, commas, spaces
        for char in ("$", "₹", "€", "£", ",", " "):
            val_str = val_str.replace(char, "")

        try:
            dec = Decimal(val_str)
            return -dec if is_negative else dec
        except InvalidOperation:
            raise ValueError(f"Cannot parse '{value}' as valid monetary Decimal.")

    def classify_dataset_headers(self, headers: List[str]) -> DocumentType:
        """Classify dataset based on normalized column names."""
        norm = [h.lower().replace("_", " ").strip() for h in headers]
        norm_str = " ".join(norm)

        if "debit" in norm_str and "credit" in norm_str and ("account" in norm_str or "particulars" in norm_str):
            return DocumentType.TRIAL_BALANCE
        if "voucher" in norm_str and ("debit" in norm_str or "credit" in norm_str):
            return DocumentType.GENERAL_LEDGER
        if "asset" in norm_str and ("depreciation" in norm_str or "wdv" in norm_str or "rate" in norm_str):
            return DocumentType.FIXED_ASSET_REGISTER
        if "invoice" in norm_str and ("customer" in norm_str or "buyer" in norm_str or "gst" in norm_str):
            return DocumentType.INVOICE
        if "bank" in norm_str or ("withdrawal" in norm_str and "deposit" in norm_str):
            return DocumentType.BANK_STATEMENT

        return DocumentType.UNKNOWN

    def ingest_csv(
        self,
        file_bytes: bytes,
        original_filename: str,
        hint_type: Optional[DocumentType] = None,
    ) -> Tuple[EvidenceRecord, Dict[str, Any]]:
        """Ingests and validates a CSV financial schedule."""
        if not file_bytes or len(file_bytes) == 0:
            raise SpreadsheetCorruptedError(f"CSV file '{original_filename}' is empty.")

        evidence_record = self.evidence_service.register_evidence(
            file_bytes=file_bytes,
            original_filename=original_filename,
            document_type=hint_type or DocumentType.UNKNOWN,
        )

        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as e:
            self.evidence_service.update_extraction_status(
                evidence_record.sha256_hash, status=ExtractionStatus.CORRUPTED
            )
            raise SpreadsheetCorruptedError(f"Failed to parse CSV '{original_filename}': {str(e)}")

        headers = [str(c) for c in df.columns]
        doc_type = hint_type or self.classify_dataset_headers(headers)

        rows: List[Dict[str, Any]] = []
        provenance_coords: List[ProvenanceCoordinate] = []

        duplicate_count = int(df.duplicated().sum())

        for row_idx, row in df.iterrows():
            row_num = row_idx + 2  # 1-indexed, accounting for header
            row_dict = {}
            for col in headers:
                val = row[col]
                row_dict[col] = None if pd.isna(val) else str(val)

            coord = ProvenanceCoordinate(
                sheet_name="CSV_DATA",
                row_number=row_num,
                line_reference=f"Row {row_num}",
                extracted_text_snippet=str(row_dict)[:100],
            )
            provenance_coords.append(coord)
            rows.append(row_dict)

        self.evidence_service.update_extraction_status(
            sha256_hash=evidence_record.sha256_hash,
            status=ExtractionStatus.SUCCESS,
            page_count=1,
            coordinates=provenance_coords,
            document_type=doc_type,
        )

        result = {
            "evidence_id": evidence_record.evidence_id,
            "filename": original_filename,
            "sha256_hash": evidence_record.sha256_hash,
            "document_type": doc_type,
            "headers": headers,
            "row_count": len(rows),
            "duplicate_rows": duplicate_count,
            "rows": rows,
            "provenance_coordinates": [c.model_dump() for c in provenance_coords],
        }

        return evidence_record, result

    def ingest_excel(
        self,
        file_bytes: bytes,
        original_filename: str,
        hint_type: Optional[DocumentType] = None,
    ) -> Tuple[EvidenceRecord, Dict[str, Any]]:
        """Ingests and validates a multi-sheet Excel (.xlsx) workbook."""
        if not file_bytes or len(file_bytes) == 0:
            raise SpreadsheetCorruptedError(f"Excel file '{original_filename}' is empty.")

        evidence_record = self.evidence_service.register_evidence(
            file_bytes=file_bytes,
            original_filename=original_filename,
            document_type=hint_type or DocumentType.UNKNOWN,
        )

        try:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        except Exception as e:
            self.evidence_service.update_extraction_status(
                evidence_record.sha256_hash, status=ExtractionStatus.CORRUPTED
            )
            raise SpreadsheetCorruptedError(f"Failed to parse Excel workbook '{original_filename}': {str(e)}")

        sheet_names = wb.sheetnames
        sheets_data: Dict[str, Any] = {}
        provenance_coords: List[ProvenanceCoordinate] = []
        overall_doc_type = hint_type or DocumentType.UNKNOWN

        for sheet_name in sheet_names:
            ws = wb[sheet_name]
            rows_raw = list(ws.iter_rows(values_only=True))
            if not rows_raw:
                sheets_data[sheet_name] = {"headers": [], "row_count": 0, "rows": []}
                continue

            # First non-empty row as header
            header_row_idx = 0
            while header_row_idx < len(rows_raw) and not any(rows_raw[header_row_idx]):
                header_row_idx += 1

            if header_row_idx >= len(rows_raw):
                sheets_data[sheet_name] = {"headers": [], "row_count": 0, "rows": []}
                continue

            headers = [str(c) if c is not None else f"Col_{i}" for i, c in enumerate(rows_raw[header_row_idx])]
            if overall_doc_type == DocumentType.UNKNOWN:
                overall_doc_type = self.classify_dataset_headers(headers)

            rows: List[Dict[str, Any]] = []
            for r_idx in range(header_row_idx + 1, len(rows_raw)):
                row_vals = rows_raw[r_idx]
                if not any(row_vals):
                    continue  # skip completely blank rows
                row_dict = {}
                for c_idx, col_name in enumerate(headers):
                    val = row_vals[c_idx] if c_idx < len(row_vals) else None
                    row_dict[col_name] = str(val) if val is not None else None

                actual_row_num = r_idx + 1
                coord = ProvenanceCoordinate(
                    sheet_name=sheet_name,
                    row_number=actual_row_num,
                    line_reference=f"Sheet '{sheet_name}', Row {actual_row_num}",
                    extracted_text_snippet=str(row_dict)[:100],
                )
                provenance_coords.append(coord)
                rows.append(row_dict)

            sheets_data[sheet_name] = {
                "headers": headers,
                "row_count": len(rows),
                "rows": rows,
            }

        self.evidence_service.update_extraction_status(
            sha256_hash=evidence_record.sha256_hash,
            status=ExtractionStatus.SUCCESS,
            page_count=len(sheet_names),
            coordinates=provenance_coords,
            document_type=overall_doc_type,
        )

        result = {
            "evidence_id": evidence_record.evidence_id,
            "filename": original_filename,
            "sha256_hash": evidence_record.sha256_hash,
            "document_type": overall_doc_type,
            "sheet_count": len(sheet_names),
            "sheets": sheets_data,
            "provenance_coordinates": [c.model_dump() for c in provenance_coords],
        }

        return evidence_record, result
