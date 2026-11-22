import pytest
import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pypdf import PdfWriter

from backend.services.evidence_service import EvidenceService
from backend.services.pdf_service import (
    PDFIntelligenceService,
    PDFEmptyError,
    PDFCorruptedError,
)
from backend.models.evidence import DocumentType, ExtractionStatus


@pytest.fixture
def pdf_service(tmp_path):
    vault = str(tmp_path / "vault")
    ev_svc = EvidenceService(storage_dir=vault)
    return PDFIntelligenceService(evidence_service=ev_svc)


@pytest.fixture
def valid_pdf_bytes():
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 700, "TRIAL BALANCE FOR FY2024-25")
    c.drawString(100, 680, "Account Code 1001 Debit 15000.00 Credit 0.00")
    c.drawString(100, 660, "Account Code 2001 Debit 0.00 Credit 15000.00")
    c.save()
    return buf.getvalue()


@pytest.fixture
def scanned_pdf_bytes():
    """PDF with a page but zero digital text (simulates a scanned image)."""
    buf = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(buf)
    return buf.getvalue()


def test_valid_pdf_ingestion(pdf_service, valid_pdf_bytes):
    record, result = pdf_service.ingest_pdf(valid_pdf_bytes, "trial_balance.pdf")
    assert record.is_duplicate is False
    assert record.extraction_status == ExtractionStatus.SUCCESS
    assert record.document_type == DocumentType.TRIAL_BALANCE
    assert result["page_count"] == 1
    assert result["non_empty_pages"] == 1
    assert len(result["provenance_coordinates"]) == 1


def test_corrupted_pdf_detection(pdf_service):
    corrupted_bytes = b"NOT_A_PDF_HEADER_JUST_RANDOM_CORRUPT_BYTES"
    with pytest.raises(PDFCorruptedError):
        pdf_service.ingest_pdf(corrupted_bytes, "broken.pdf")


def test_empty_pdf_detection(pdf_service):
    empty_bytes = b""
    with pytest.raises(PDFEmptyError):
        pdf_service.ingest_pdf(empty_bytes, "empty.pdf")


def test_scanned_pdf_flags_ocr_required(pdf_service, scanned_pdf_bytes):
    record, result = pdf_service.ingest_pdf(scanned_pdf_bytes, "scanned_invoice.pdf")
    assert record.extraction_status == ExtractionStatus.REQUIRES_OCR
    assert result["extraction_status"] == ExtractionStatus.REQUIRES_OCR
    assert any("OCR" in str(p) for p in result["pages"])


def test_duplicate_pdf_detection(pdf_service, valid_pdf_bytes):
    rec1, _ = pdf_service.ingest_pdf(valid_pdf_bytes, "original.pdf")
    rec2, _ = pdf_service.ingest_pdf(valid_pdf_bytes, "copy.pdf")
    assert rec1.is_duplicate is False
    assert rec2.is_duplicate is True
    assert rec2.duplicate_of_id == rec1.evidence_id
    assert rec1.sha256_hash == rec2.sha256_hash
