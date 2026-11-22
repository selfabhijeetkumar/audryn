"""
AUDRYN Evidence Ingestion and Integrity Endpoints.
SHA-256 integrity calculation, MIME validation, safe storage, and human evidence acceptance.
"""
import os
import secrets
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.app.auth import get_current_user, require_permission, verify_csrf
from backend.app.rbac import Permission
from backend.app.isolation import verify_engagement_access
from backend.db.repositories import EvidenceRepository, EvidenceValidityRepository, AuditEventRepository
from backend.services.evidence_service import EvidenceService

router = APIRouter(prefix="/engagements/{engagement_id}/evidence", tags=["Evidence"])

ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".json"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class ValidityDecisionRequest(BaseModel):
    status: str
    purpose_scope: str
    rationale: str


@router.get("")
def list_evidence(
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.READ_EVIDENCE)),
):
    return EvidenceRepository.list_by_engagement(engagement["engagement_id"])


@router.post("/upload", dependencies=[Depends(verify_csrf)])
async def upload_evidence(
    file: UploadFile = File(...),
    document_type: str = Form("UNKNOWN"),
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.UPLOAD_EVIDENCE)),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Permitted formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum permissible size of 50MB (received {len(file_bytes)} bytes).",
        )

    sha256 = EvidenceService.compute_sha256(file_bytes)
    evidence_id = f"EV-{secrets.token_hex(4).upper()}"

    vault_dir = os.path.join("data", "evidence_vault")
    os.makedirs(vault_dir, exist_ok=True)
    stored_name = f"{evidence_id}_{secrets.token_hex(8)}{ext}"
    stored_path = os.path.join(vault_dir, stored_name)

    with open(stored_path, "wb") as f:
        f.write(file_bytes)

    record = EvidenceRepository.create(
        evidence_id=evidence_id,
        engagement_id=engagement["engagement_id"],
        original_filename=file.filename or "unknown_evidence",
        sha256_hash=sha256,
        file_size_bytes=len(file_bytes),
        document_type=document_type,
        extraction_status="EXTRACTED",
        raw_storage_path=stored_path,
        uploaded_by=user["user_id"],
        page_count=1,
        metadata={"content_type": file.content_type},
    )

    AuditEventRepository.log_event(
        engagement["engagement_id"],
        user["user_id"],
        "EVIDENCE_UPLOADED",
        {"evidence_id": evidence_id, "filename": file.filename, "sha256": sha256},
    )

    return record


@router.get("/{evidence_id}")
def get_evidence(
    evidence_id: str,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.READ_EVIDENCE)),
):
    record = EvidenceRepository.get_by_id(engagement["engagement_id"], evidence_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Evidence record '{evidence_id}' not found.")
    return record


@router.post("/{evidence_id}/verify-hash")
def verify_hash(
    evidence_id: str,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.VERIFY_EVIDENCE)),
):
    record = EvidenceRepository.get_by_id(engagement["engagement_id"], evidence_id)
    if not record:
        raise HTTPException(status_code=404, detail="Evidence not found.")

    storage_path = record.get("raw_storage_path")
    if not storage_path or not os.path.exists(storage_path):
        raise HTTPException(status_code=500, detail="Underlying vault storage file missing.")

    computed_hash = EvidenceService.compute_file_sha256(storage_path)
    is_match = (computed_hash == record["sha256_hash"])

    AuditEventRepository.log_event(
        engagement["engagement_id"],
        user["user_id"],
        "HASH_VERIFIED",
        {"evidence_id": evidence_id, "is_match": is_match, "hash": computed_hash},
    )

    return {
        "evidence_id": evidence_id,
        "recorded_sha256": record["sha256_hash"],
        "computed_sha256": computed_hash,
        "is_match": is_match,
        "verified_at": record["uploaded_at"],
    }


@router.get("/{evidence_id}/download")
def download_evidence(
    evidence_id: str,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.READ_EVIDENCE)),
):
    record = EvidenceRepository.get_by_id(engagement["engagement_id"], evidence_id)
    if not record:
        raise HTTPException(status_code=404, detail="Evidence not found.")

    storage_path = record.get("raw_storage_path")
    if not storage_path or not os.path.exists(storage_path):
        raise HTTPException(status_code=500, detail="Vault storage file missing.")

    return FileResponse(
        path=storage_path,
        filename=record["original_filename"],
        media_type="application/octet-stream",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.post("/{evidence_id}/validity", dependencies=[Depends(verify_csrf)])
def record_validity_decision(
    evidence_id: str,
    payload: ValidityDecisionRequest,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.ACCEPT_EVIDENCE)),
):
    valid_statuses = {
        "PENDING_REVIEW",
        "ACCEPTED_FOR_STATED_PURPOSE",
        "REJECTED",
        "DISPUTED",
        "INSUFFICIENT_EVIDENCE",
    }
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status '{payload.status}'.")

    decision_id = f"VAL-{secrets.token_hex(4).upper()}"
    decision = EvidenceValidityRepository.record_decision(
        decision_id=decision_id,
        evidence_id=evidence_id,
        engagement_id=engagement["engagement_id"],
        reviewer_id=user["user_id"],
        reviewer_role=user["role"],
        status=payload.status,
        purpose_scope=payload.purpose_scope,
        rationale=payload.rationale,
    )

    AuditEventRepository.log_event(
        engagement["engagement_id"],
        user["user_id"],
        "EVIDENCE_VALIDITY_RECORDED",
        {"evidence_id": evidence_id, "status": payload.status, "purpose": payload.purpose_scope},
    )

    return decision


@router.get("/{evidence_id}/validity")
def list_validity_decisions(
    evidence_id: str,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.READ_EVIDENCE)),
):
    return EvidenceValidityRepository.list_decisions(engagement["engagement_id"], evidence_id)
