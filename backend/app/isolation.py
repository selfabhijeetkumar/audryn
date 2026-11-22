"""
AUDRYN Engagement Scoping and Isolation Layer.
Enforces multi-engagement boundary checks and prevents Insecure Direct Object References (IDOR).
"""
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status, Depends
from backend.db.connection import db_manager
from backend.app.auth import get_current_user


class EngagementIsolationService:
    """Verifies that authenticated users only access authorized engagements."""

    @staticmethod
    def is_user_member(engagement_id: str, user_id: str) -> bool:
        """Checks if a user is an authorized member of an engagement."""
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM engagement_members
                WHERE engagement_id = ? AND user_id = ?;
                """,
                (engagement_id, user_id),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()

    @staticmethod
    def get_engagement_or_404(engagement_id: str) -> Dict[str, Any]:
        """Retrieves engagement metadata or raises 404."""
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM engagements WHERE engagement_id = ?;", (engagement_id,))
            eng = cur.fetchone()
            if not eng:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Engagement '{engagement_id}' not found.",
                )
            return dict(eng)
        finally:
            conn.close()

    @staticmethod
    def get_user_engagements(user_id: str) -> List[Dict[str, Any]]:
        """Lists all engagements the user has access to."""
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT e.*, em.role as member_role
                FROM engagements e
                JOIN engagement_members em ON e.engagement_id = em.engagement_id
                WHERE em.user_id = ?
                ORDER BY e.created_at DESC;
                """,
                (user_id,),
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()


def verify_engagement_access(
    engagement_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    FastAPI dependency: Guarantees the engagement exists and current user has membership.
    Raises 403 Forbidden for cross-engagement / IDOR attempts.
    """
    eng = EngagementIsolationService.get_engagement_or_404(engagement_id)
    if not EngagementIsolationService.is_user_member(engagement_id, user["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cross-engagement access denied. You are not assigned to engagement '{engagement_id}'.",
        )
    return eng
