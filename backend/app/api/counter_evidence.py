"""
AUDRYN Counter-Evidence Intelligence Endpoints.
Exposes adversarial challenge structures and preserves exact ReviewVerdict enums.
"""
import secrets
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from backend.app.auth import get_current_user, require_permission, verify_csrf
from backend.app.rbac import Permission
from backend.app.isolation import verify_engagement_access
from backend.db.connection import db_manager
from backend.db.repositories import CounterEvidenceRepository, AuditEventRepository
from backend.services.counter_evidence_service import CounterEvidenceService
from backend.models.counter_evidence import ReviewVerdict

router = APIRouter(prefix="/engagements/{engagement_id}/counter-evidence", tags=["Counter-Evidence"])


class CreateChallengeRequest(BaseModel):
    finding_id: str
    original_hypothesis: str
    impact_amount: str
    supporting_evidence: List[str]
    contradictory_evidence: Optional[List[str]] = None
    alternative_explanations: Optional[List[str]] = None
    expected_amount: Optional[str] = None
    actual_amount: Optional[str] = None
    reviewer_role: str = "Independent Reviewer (MS Agent Framework)"
    notes: Optional[str] = None


@router.get("")
def list_challenges(
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.VIEW_COUNTER_EVIDENCE)),
):
    conn = db_manager.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM counter_evidence_challenges
            WHERE engagement_id = ?
            ORDER BY created_at DESC;
            """,
            (engagement["engagement_id"],),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.post("", dependencies=[Depends(verify_csrf)])
def create_challenge(
    payload: CreateChallengeRequest,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.CREATE_CHALLENGE)),
):
    service = CounterEvidenceService()
    challenge = service.create_challenge(
        finding_id=payload.finding_id,
        original_hypothesis=payload.original_hypothesis,
        impact_amount=payload.impact_amount,
        supporting_evidence=payload.supporting_evidence,
        contradictory_evidence=payload.contradictory_evidence,
        alternative_explanations=payload.alternative_explanations,
        expected_amount=payload.expected_amount,
        actual_amount=payload.actual_amount,
        reviewer_role=payload.reviewer_role,
    )

    record = CounterEvidenceRepository.create_or_update(
        challenge_id=f"CHAL-{secrets.token_hex(4).upper()}",
        finding_id=payload.finding_id,
        engagement_id=engagement["engagement_id"],
        original_hypothesis=challenge.original_hypothesis,
        supporting_evidence=challenge.supporting_evidence,
        contradictory_evidence=challenge.contradictory_evidence,
        alternative_explanations=challenge.alternative_explanations,
        calculation_verification=challenge.calculation_verification,
        reviewer_role=challenge.reviewer_role,
        reviewer_verdict=challenge.reviewer_verdict.value,
        verdict_rationale=challenge.verdict_rationale,
        requires_escalation=challenge.requires_escalation,
        notes=payload.notes,
    )

    AuditEventRepository.log_event(
        engagement["engagement_id"],
        user["user_id"],
        "COUNTER_EVIDENCE_CHALLENGE_CREATED",
        {"finding_id": payload.finding_id, "verdict": challenge.reviewer_verdict.value},
    )

    return record
