import os
import pytest
from backend.services.evidence_service import EvidenceService
from backend.models.evidence import DocumentType


@pytest.fixture
def evidence_service(tmp_path):
    vault = str(tmp_path / "vault")
    return EvidenceService(storage_dir=vault)


def test_sha256_reproducibility(evidence_service):
    data = b"Statutory Trial Balance Data FY2024-25"
    h1 = evidence_service.compute_sha256(data)
    h2 = evidence_service.compute_sha256(data)
    assert h1 == h2
    assert len(h1) == 64


def test_register_and_retrieve_evidence(evidence_service):
    data = b"General Ledger Content"
    rec = evidence_service.register_evidence(
        file_bytes=data,
        original_filename="gl.csv",
        document_type=DocumentType.GENERAL_LEDGER,
    )
    assert rec.is_duplicate is False
    assert rec.sha256_hash == evidence_service.compute_sha256(data)
    assert os.path.exists(rec.raw_storage_path)

    retrieved = evidence_service.get_evidence(rec.sha256_hash)
    assert retrieved is not None
    assert retrieved.evidence_id == rec.evidence_id


def test_vault_tampering_detection(evidence_service):
    data = b"Original Immutable Audit Workpaper"
    rec = evidence_service.register_evidence(
        file_bytes=data,
        original_filename="workpaper.pdf",
        document_type=DocumentType.BALANCE_SHEET,
    )

    # Initial integrity check passes
    assert evidence_service.verify_vault_integrity(rec.sha256_hash) is True

    # Tamper with file on disk
    with open(rec.raw_storage_path, "ab") as f:
        f.write(b"TAMPERED_MALICIOUS_BYTES")

    # Integrity check must now fail
    assert evidence_service.verify_vault_integrity(rec.sha256_hash) is False
