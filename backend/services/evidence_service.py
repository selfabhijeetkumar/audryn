import hashlib
import os
from typing import Dict, Optional, List
from datetime import datetime, timezone
from backend.models.evidence import (
    EvidenceRecord,
    DocumentType,
    ExtractionStatus,
    ProvenanceCoordinate,
)


class EvidenceService:
    """
    Manages cryptographic document integrity, SHA-256 fingerprinting,
    provenance coordinates, and immutability for the AUDRYN evidence graph.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or os.path.join("data", "evidence_vault")
        os.makedirs(self.storage_dir, exist_ok=True)
        # In-memory registry mapping sha256 -> EvidenceRecord
        self._registry: Dict[str, EvidenceRecord] = {}

    @staticmethod
    def compute_sha256(file_bytes: bytes) -> str:
        """Compute deterministic SHA-256 hex digest of raw binary bytes."""
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        return hasher.hexdigest()

    @staticmethod
    def compute_file_sha256(file_path: str) -> str:
        """Compute SHA-256 hex digest of a file on disk."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def register_evidence(
        self,
        file_bytes: bytes,
        original_filename: str,
        document_type: DocumentType = DocumentType.UNKNOWN,
        metadata: Optional[Dict[str, any]] = None,
    ) -> EvidenceRecord:
        """
        Registers raw document bytes into the immutable evidence vault.
        Detects duplicates by cryptographic hash.
        """
        sha256_hash = self.compute_sha256(file_bytes)
        file_size = len(file_bytes)

        # Check for existing duplicate
        if sha256_hash in self._registry:
            existing = self._registry[sha256_hash]
            duplicate_record = EvidenceRecord(
                evidence_id=f"EV-DUP-{sha256_hash[:12]}",
                original_filename=original_filename,
                sha256_hash=sha256_hash,
                file_size_bytes=file_size,
                upload_timestamp=datetime.now(timezone.utc),
                document_type=existing.document_type,
                extraction_status=existing.extraction_status,
                page_count=existing.page_count,
                provenance_coordinates=existing.provenance_coordinates,
                metadata=metadata or {},
                is_duplicate=True,
                duplicate_of_id=existing.evidence_id,
                raw_storage_path=existing.raw_storage_path,
            )
            return duplicate_record

        # Generate unique Evidence ID
        evidence_id = f"EV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{sha256_hash[:10]}"

        # Save to immutable vault path
        ext = os.path.splitext(original_filename)[1]
        vault_filename = f"{evidence_id}_{sha256_hash[:8]}{ext}"
        vault_path = os.path.join(self.storage_dir, vault_filename)

        with open(vault_path, "wb") as f:
            f.write(file_bytes)

        record = EvidenceRecord(
            evidence_id=evidence_id,
            original_filename=original_filename,
            sha256_hash=sha256_hash,
            file_size_bytes=file_size,
            upload_timestamp=datetime.now(timezone.utc),
            document_type=document_type,
            extraction_status=ExtractionStatus.PENDING,
            page_count=0,
            provenance_coordinates=[],
            metadata=metadata or {},
            is_duplicate=False,
            duplicate_of_id=None,
            raw_storage_path=vault_path,
        )

        self._registry[sha256_hash] = record
        return record

    def get_evidence(self, sha256_hash: str) -> Optional[EvidenceRecord]:
        return self._registry.get(sha256_hash)

    def get_evidence_by_id(self, evidence_id: str) -> Optional[EvidenceRecord]:
        for rec in self._registry.values():
            if rec.evidence_id == evidence_id:
                return rec
        return None

    def list_all_evidence(self) -> List[EvidenceRecord]:
        return list(self._registry.values())

    def update_extraction_status(
        self,
        sha256_hash: str,
        status: ExtractionStatus,
        page_count: int = 0,
        coordinates: Optional[List[ProvenanceCoordinate]] = None,
        document_type: Optional[DocumentType] = None,
    ) -> Optional[EvidenceRecord]:
        """Updates provenance details after document parsing."""
        if sha256_hash not in self._registry:
            return None
        rec = self._registry[sha256_hash]
        rec.extraction_status = status
        if page_count > 0:
            rec.page_count = page_count
        if coordinates:
            rec.provenance_coordinates.extend(coordinates)
        if document_type:
            rec.document_type = document_type
        return rec

    def verify_vault_integrity(self, sha256_hash: str) -> bool:
        """Empirically verifies that vault file has not been altered or tampered with."""
        rec = self._registry.get(sha256_hash)
        if not rec or not rec.raw_storage_path or not os.path.exists(rec.raw_storage_path):
            return False
        current_hash = self.compute_file_sha256(rec.raw_storage_path)
        return current_hash == sha256_hash
