"""
AUDRYN Engagement Management Endpoints.
Multi-tenancy isolation and team membership assignment.
"""
from typing import Dict, Any, List, Optional
import secrets
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from backend.app.auth import get_current_user, require_permission, verify_csrf
from backend.app.rbac import Permission, Role
from backend.app.isolation import verify_engagement_access, EngagementIsolationService
from backend.db.connection import db_manager
from backend.db.repositories import AuditEventRepository

router = APIRouter(prefix="/engagements", tags=["Engagements"])


class CreateEngagementRequest(BaseModel):
    entity_name: str
    cin: str
    fiscal_year: str
    assessment_year: str
    currency: str = "INR"


class AddMemberRequest(BaseModel):
    user_id: str
    role: str


@router.get("")
def list_engagements(user: Dict[str, Any] = Depends(get_current_user)):
    return EngagementIsolationService.get_user_engagements(user["user_id"])


@router.post("", dependencies=[Depends(verify_csrf)])
def create_engagement(
    payload: CreateEngagementRequest,
    user: Dict[str, Any] = Depends(require_permission(Permission.CONFIGURE_SETTINGS)),
):
    engagement_id = f"ENG-{secrets.token_hex(4).upper()}"
    with db_manager.session() as conn:
        conn.execute(
            """
            INSERT INTO engagements (engagement_id, entity_name, cin, fiscal_year, assessment_year, currency)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                engagement_id,
                payload.entity_name,
                payload.cin,
                payload.fiscal_year,
                payload.assessment_year,
                payload.currency,
            ),
        )
        # Assign creator
        conn.execute(
            """
            INSERT INTO engagement_members (engagement_id, user_id, role)
            VALUES (?, ?, ?);
            """,
            (engagement_id, user["user_id"], user["role"]),
        )

    AuditEventRepository.log_event(
        engagement_id,
        user["user_id"],
        "ENGAGEMENT_CREATED",
        {"entity_name": payload.entity_name, "cin": payload.cin},
    )
    return EngagementIsolationService.get_engagement_or_404(engagement_id)


@router.get("/{engagement_id}")
def get_engagement(
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
):
    return engagement


@router.get("/{engagement_id}/members")
def list_members(
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
):
    conn = db_manager.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT em.role, em.assigned_at, u.user_id, u.username, u.full_name, u.email
            FROM engagement_members em
            JOIN users u ON em.user_id = u.user_id
            WHERE em.engagement_id = ?;
            """,
            (engagement["engagement_id"],),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.post("/{engagement_id}/members", dependencies=[Depends(verify_csrf)])
def add_member(
    payload: AddMemberRequest,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.MANAGE_TEAM)),
):
    if payload.role not in [r.value for r in Role]:
        raise HTTPException(status_code=400, detail=f"Invalid role '{payload.role}'.")

    with db_manager.session() as conn:
        conn.execute(
            """
            INSERT INTO engagement_members (engagement_id, user_id, role)
            VALUES (?, ?, ?)
            ON CONFLICT(engagement_id, user_id) DO UPDATE SET role = excluded.role;
            """,
            (engagement["engagement_id"], payload.user_id, payload.role),
        )

    AuditEventRepository.log_event(
        engagement["engagement_id"],
        user["user_id"],
        "MEMBER_ASSIGNED",
        {"target_user_id": payload.user_id, "role": payload.role},
    )
    return {"message": "Member successfully assigned to engagement."}
