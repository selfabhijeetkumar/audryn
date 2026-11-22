"""
AUDRYN Immutable Audit Trail and Event Log Endpoints.
Provides chronological, append-only traceability of all audit decisions and system actions.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from backend.app.auth import get_current_user, require_permission
from backend.app.rbac import Permission
from backend.app.isolation import verify_engagement_access
from backend.db.repositories import AuditEventRepository

router = APIRouter(prefix="/engagements/{engagement_id}/audit-events", tags=["Audit Events"])


@router.get("")
def list_audit_events(
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.VIEW_AUDIT_LOG)),
):
    return AuditEventRepository.list_by_engagement(engagement["engagement_id"])
