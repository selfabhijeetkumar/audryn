import pytest
import io
import pandas as pd
import openpyxl
from decimal import Decimal

from backend.services.evidence_service import EvidenceService
from backend.services.spreadsheet_service import (
    SpreadsheetIntelligenceService,
    SpreadsheetCorruptedError,
)
from backend.models.evidence import DocumentType, ExtractionStatus


@pytest.fixture
def spreadsheet_service(tmp_path):
    vault = str(tmp_path / "vault")
    ev_svc = EvidenceService(storage_dir=vault)
    return SpreadsheetIntelligenceService(evidence_service=ev_svc)


def test_currency_normalization(spreadsheet_service):
    norm = spreadsheet_service.normalize_currency_decimal
    assert norm("$1,250.75") == Decimal("1250.75")
    assert norm("(500.00)") == Decimal("-500.00")
    assert norm("-$250.50") == Decimal("-250.50")
    assert norm(" 10,000 ") == Decimal("10000.00")
    assert norm("") == Decimal("0.00")
    assert norm(None) == Decimal("0.00")


def test_valid_csv_ingestion(spreadsheet_service):
    csv_data = "account_code,particulars,debit,credit\n1001,Cash,1500.00,0.00\n2001,Capital,0.00,1500.00\n"
    record, result = spreadsheet_service.ingest_csv(csv_data.encode("utf-8"), "tb.csv")
    assert record.extraction_status == ExtractionStatus.SUCCESS
    assert record.document_type == DocumentType.TRIAL_BALANCE
    assert result["row_count"] == 2
    assert result["duplicate_rows"] == 0
    assert len(result["provenance_coordinates"]) == 2


def test_duplicate_row_detection(spreadsheet_service):
    csv_data = "invoice_id,amount\nINV-01,100\nINV-01,100\nINV-02,200\n"
    record, result = spreadsheet_service.ingest_csv(csv_data.encode("utf-8"), "invoices.csv")
    assert result["duplicate_rows"] == 1
    assert result["row_count"] == 3


def test_empty_csv_detection(spreadsheet_service):
    with pytest.raises(SpreadsheetCorruptedError):
        spreadsheet_service.ingest_csv(b"", "empty.csv")


def test_multi_sheet_excel_ingestion(spreadsheet_service):
    buf = io.BytesIO()
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Trial_Balance"
    ws1.append(["account_code", "particulars", "debit", "credit"])
    ws1.append(["1001", "Bank", "50000.00", "0.00"])

    ws2 = wb.create_sheet(title="Fixed_Assets")
    ws2.append(["asset_id", "asset_name", "depreciation", "cost"])
    ws2.append(["AST-01", "Lathe", "1500.00", "10000.00"])

    wb.save(buf)
    excel_bytes = buf.getvalue()

    record, result = spreadsheet_service.ingest_excel(excel_bytes, "audit_schedules.xlsx")
    assert record.extraction_status == ExtractionStatus.SUCCESS
    assert result["sheet_count"] == 2
    assert "Trial_Balance" in result["sheets"]
    assert "Fixed_Assets" in result["sheets"]
    assert result["sheets"]["Trial_Balance"]["row_count"] == 1
    assert result["sheets"]["Fixed_Assets"]["row_count"] == 1
