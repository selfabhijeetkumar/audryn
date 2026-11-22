import pytest
from backend.services.completeness_service import CompletenessGateService
from backend.models.evidence import EvidenceRecord, DocumentType, ExtractionStatus
from backend.models.completeness import GateStatus


@pytest.fixture
def gate_service():
    return CompletenessGateService()


def _make_record(doc_type: DocumentType, status: ExtractionStatus = ExtractionStatus.SUCCESS) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=f"EV-{doc_type.value}",
        original_filename=f"{doc_type.value}.pdf",
        sha256_hash=f"hash_{doc_type.value}",
        file_size_bytes=1024,
        document_type=doc_type,
        extraction_status=status,
    )


def test_completeness_gate_passes_when_all_mandatory_present(gate_service):
    evidence_list = [
        _make_record(DocumentType.TRIAL_BALANCE),
        _make_record(DocumentType.BALANCE_SHEET),
        _make_record(DocumentType.PROFIT_AND_LOSS),
        _make_record(DocumentType.GENERAL_LEDGER),
        _make_record(DocumentType.FIXED_ASSET_REGISTER),
        _make_record(DocumentType.TAX_RETURN),
        _make_record(DocumentType.BANK_STATEMENT),
    ]
    res = gate_service.evaluate_completeness("AUDIT-2024", evidence_list)
    assert res.gate_status == GateStatus.PASSED
    assert res.can_proceed_to_report is True
    assert len(res.missing_documents) == 0


def test_completeness_gate_blocks_when_mandatory_missing(gate_service):
    # Omit Tax Return and Bank Statement
    evidence_list = [
        _make_record(DocumentType.TRIAL_BALANCE),
        _make_record(DocumentType.BALANCE_SHEET),
        _make_record(DocumentType.PROFIT_AND_LOSS),
        _make_record(DocumentType.GENERAL_LEDGER),
    ]
    res = gate_service.evaluate_completeness("AUDIT-2024", evidence_list)
    assert res.gate_status == GateStatus.BLOCKED
    assert res.can_proceed_to_report is False
    assert any("Tax Computation Schedule" in msg for msg in res.missing_documents)
    assert any("Bank Statements" in msg for msg in res.missing_documents)


def test_completeness_gate_blocks_on_corrupted_document(gate_service):
    evidence_list = [
        _make_record(DocumentType.TRIAL_BALANCE, status=ExtractionStatus.CORRUPTED),
        _make_record(DocumentType.BALANCE_SHEET),
        _make_record(DocumentType.PROFIT_AND_LOSS),
        _make_record(DocumentType.GENERAL_LEDGER),
        _make_record(DocumentType.FIXED_ASSET_REGISTER),
        _make_record(DocumentType.TAX_RETURN),
        _make_record(DocumentType.BANK_STATEMENT),
    ]
    res = gate_service.evaluate_completeness("AUDIT-2024", evidence_list)
    assert res.gate_status == GateStatus.BLOCKED
    assert res.can_proceed_to_report is False
    assert len(res.corrupted_documents) == 1
