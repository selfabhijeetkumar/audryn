"""
AUDRYN Human Review and Statutory Approval Endpoints.
Enforces statutory reviewer sign-off, immutable review history, and brass sign-off discipline.
"""
import secrets
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from backend.app.auth import get_current_user, require_permission, verify_csrf
from backend.app.rbac import Permission, Role
from backend.app.isolation import verify_engagement_access
from backend.db.repositories import (
    HumanReviewRepository,
    FindingsRepository,
    AuditEventRepository,
)
from backend.services.human_review_service import HumanReviewDecision

router = APIRouter(prefix="/engagements/{engagement_id}/human-review", tags=["Human Review"])


class ReviewDecisionRequest(BaseModel):
    finding_id: str
    decision: str  # APPROVED, REJECTED, REQUEST_EVIDENCE, ESCALATED
    comments: str
    reviewer_membership_no: Optional[str] = "ICAI-084920"
    unresolved_acknowledged: bool = False


@router.get("/history")
def get_review_history(
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.VIEW_INVESTIGATION)),
):
    return HumanReviewRepository.list_by_engagement(engagement["engagement_id"])


@router.post("/decide", dependencies=[Depends(verify_csrf)])
def record_decision(
    payload: ReviewDecisionRequest,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(get_current_user),
):
    valid_decisions = {"APPROVED", "REJECTED", "REQUEST_EVIDENCE", "ESCALATED"}
    dec = payload.decision.upper()
    if dec not in valid_decisions:
        raise HTTPException(status_code=400, detail=f"Invalid decision '{dec}'. Must be one of {valid_decisions}")

    user_role = user.get("role", "")

    # Role-based validation
    if dec == "APPROVED":
        if user_role != Role.PARTNER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Statutory approval of audit findings is reserved exclusively for Partners.",
            )
    elif dec == "REJECTED":
        if user_role not in [Role.PARTNER.value, Role.MANAGER.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rejecting audit findings requires Manager or Partner authority.",
            )
    elif dec in ["REQUEST_EVIDENCE", "ESCALATED"]:
        if user_role not in [Role.SENIOR.value, Role.MANAGER.value, Role.PARTNER.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requesting additional evidence or escalating findings requires Senior level or above.",
            )

    # Comments required for rejection, escalation, or additional evidence
    if dec in ["REJECTED", "REQUEST_EVIDENCE", "ESCALATED"] and not payload.comments.strip():
        raise HTTPException(
            status_code=400,
            detail=f"Written justification is mandatory when selecting {dec}.",
        )

    # Check finding exists
    finding = FindingsRepository.get_by_id(engagement["engagement_id"], payload.finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail=f"Finding '{payload.finding_id}' not found.")

    # Counter-evidence unresolved gate
    ce = finding.get("counter_evidence", {})
    verdict = ce.get("verdict")
    if dec == "APPROVED" and verdict in ["PARTIALLY_SUPPORTED", "UNRESOLVED", "INSUFFICIENT_EVIDENCE"]:
        if not payload.unresolved_acknowledged:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Approval requires explicit acknowledgment of unresolved counter-evidence "
                    f"(Current verdict: {verdict}). Check 'unresolved_acknowledged' before signing."
                ),
            )

    review_id = f"REV-{secrets.token_hex(4).upper()}"
    review_record = HumanReviewRepository.record_decision(
        review_id=review_id,
        audit_id=engagement["engagement_id"],
        finding_id=payload.finding_id,
        engagement_id=engagement["engagement_id"],
        reviewer_id=user["user_id"],
        reviewer_name=user["full_name"],
        reviewer_role=user_role,
        reviewer_membership_no=payload.reviewer_membership_no or "ICAI-MEMBER",
        decision=dec,
        comments=payload.comments,
    )

    AuditEventRepository.log_event(
        engagement["engagement_id"],
        user["user_id"],
        "HUMAN_REVIEW_DECISION",
        {
            "finding_id": payload.finding_id,
            "decision": dec,
            "reviewer": user["full_name"],
            "role": user_role,
        },
    )

    return {
        "message": f"Review decision '{dec}' successfully persisted to immutable audit register.",
        "review": review_record,
        "is_brass_signoff_active": dec == "APPROVED",
    }
