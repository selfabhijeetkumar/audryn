"""
AUDRYN Completeness Gate and Not-Checked Register Endpoints.
Evaluates documentation completeness against statutory rules and tracks omitted procedures.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from backend.app.auth import get_current_user, require_permission, verify_csrf
from backend.app.rbac import Permission
from backend.app.isolation import verify_engagement_access
from backend.db.repositories import (
    EvidenceRepository,
    NotCheckedRepository,
    AuditEventRepository,
)
from backend.services.completeness_service import CompletenessGateService
from backend.models.evidence import EvidenceRecord, DocumentType, ExtractionStatus

router = APIRouter(prefix="/engagements/{engagement_id}", tags=["Completeness & Not-Checked"])


class UpdateNotCheckedRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    audit_area: Optional[str] = None
    status: Optional[str] = None
    reason_not_checked: Optional[str] = None
    mitigating_notes: Optional[str] = None
    assigned_reviewer: Optional[str] = None


class CreateNotCheckedRequest(BaseModel):
    procedure_id: str
    audit_area: str
    title: str
    description: str
    reason_not_checked: Optional[str] = None
    mitigating_notes: Optional[str] = None
    assigned_reviewer: str = "Unassigned"


@router.get("/completeness")
def evaluate_completeness(
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.VIEW_COMPLETENESS)),
):
    raw_records = EvidenceRepository.list_by_engagement(engagement["engagement_id"])

    evidence_models = []
    for r in raw_records:
        doc_type_val = r.get("document_type", "UNKNOWN")
        try:
            doc_type = DocumentType(doc_type_val)
        except ValueError:
            doc_type = DocumentType.UNKNOWN

        extract_status_val = r.get("extraction_status", "PENDING")
        try:
            extract_status = ExtractionStatus(extract_status_val)
        except ValueError:
            extract_status = ExtractionStatus.PENDING

        evidence_models.append(
            EvidenceRecord(
                evidence_id=r["evidence_id"],
                original_filename=r["original_filename"],
                sha256_hash=r["sha256_hash"],
                file_size_bytes=r["file_size_bytes"],
                document_type=doc_type,
                extraction_status=extract_status,
                page_count=r.get("page_count", 0),
                raw_storage_path=r.get("raw_storage_path"),
            )
        )

    service = CompletenessGateService()
    result = service.evaluate_completeness(
        audit_id=engagement["engagement_id"],
        evidence_records=evidence_models,
    )

    return result.model_dump()


@router.get("/not-checked")
def list_not_checked(
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.VIEW_COMPLETENESS)),
):
    return NotCheckedRepository.list_by_engagement(engagement["engagement_id"])


@router.post("/not-checked", dependencies=[Depends(verify_csrf)])
def create_not_checked(
    payload: CreateNotCheckedRequest,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.UPDATE_NOT_CHECKED)),
):
    item = NotCheckedRepository.create_or_update(
        procedure_id=payload.procedure_id,
        engagement_id=engagement["engagement_id"],
        audit_area=payload.audit_area,
        title=payload.title,
        description=payload.description,
        status="NOT_CHECKED",
        reason_not_checked=payload.reason_not_checked,
        mitigating_notes=payload.mitigating_notes,
        assigned_reviewer=payload.assigned_reviewer,
    )

    AuditEventRepository.log_event(
        engagement["engagement_id"],
        user["user_id"],
        "NOT_CHECKED_CREATED",
        {"procedure_id": payload.procedure_id, "title": payload.title},
    )
    return item


@router.put("/not-checked/{procedure_id}", dependencies=[Depends(verify_csrf)])
def update_not_checked(
    procedure_id: str,
    payload: UpdateNotCheckedRequest,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.UPDATE_NOT_CHECKED)),
):
    existing = None
    all_items = NotCheckedRepository.list_by_engagement(engagement["engagement_id"])
    for it in all_items:
        if it["procedure_id"] == procedure_id:
            existing = it
            break

    if not existing:
        raise HTTPException(status_code=404, detail=f"Procedure '{procedure_id}' not found.")

    updated = NotCheckedRepository.create_or_update(
        procedure_id=procedure_id,
        engagement_id=engagement["engagement_id"],
        audit_area=payload.audit_area or existing["audit_area"],
        title=payload.title or existing["title"],
        description=payload.description or existing["description"],
        status=payload.status or existing["status"],
        reason_not_checked=payload.reason_not_checked or existing.get("reason_not_checked"),
        mitigating_notes=payload.mitigating_notes or existing.get("mitigating_notes"),
        assigned_reviewer=payload.assigned_reviewer or existing.get("assigned_reviewer", "Unassigned"),
    )

    AuditEventRepository.log_event(
        engagement["engagement_id"],
        user["user_id"],
        "NOT_CHECKED_UPDATED",
        {"procedure_id": procedure_id, "status": updated["status"]},
    )
    return updated
