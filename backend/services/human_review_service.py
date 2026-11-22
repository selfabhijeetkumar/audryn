"""
AUDRYN Human Review Service.

Manages human-in-the-loop review lifecycle:
- Record reviewer decisions (approve, reject, escalate, request evidence)
- Persist decisions to auditable JSON files
- Track review history with timestamps
- Never automatically issue a final audit opinion

All reviewer decisions are immutable once recorded.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


class HumanReviewDecision:
    APPROVE = "APPROVED"
    REJECT = "REJECTED"
    REQUEST_EVIDENCE = "REQUEST_EVIDENCE"
    ESCALATE = "ESCALATED"

    VALID_DECISIONS = {APPROVE, REJECT, REQUEST_EVIDENCE, ESCALATE}


class HumanReviewService:

    def __init__(self, persistence_dir: Optional[str] = None):
        self.persistence_dir = persistence_dir or os.path.join("data", "human_reviews")
        os.makedirs(self.persistence_dir, exist_ok=True)
        self._reviews: Dict[str, List[Dict[str, Any]]] = {}

    def record_decision(
        self,
        audit_id: str,
        finding_id: str,
        reviewer_name: str,
        decision: str,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record a human reviewer's decision on a finding.
        Validates decision type and persists to disk.
        """
        if decision not in HumanReviewDecision.VALID_DECISIONS:
            raise ValueError(
                f"Invalid decision '{decision}'. "
                f"Must be one of: {HumanReviewDecision.VALID_DECISIONS}"
            )

        record = {
            "review_id": f"REV-{uuid.uuid4().hex[:8]}",
            "audit_id": audit_id,
            "finding_id": finding_id,
            "reviewer_name": reviewer_name,
            "decision": decision,
            "comments": comments or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Append to in-memory store
        if audit_id not in self._reviews:
            self._reviews[audit_id] = []
        self._reviews[audit_id].append(record)

        # Persist to disk
        self._persist(audit_id)

        return record

    def get_reviews_for_audit(self, audit_id: str) -> List[Dict[str, Any]]:
        """Get all review decisions for an audit run."""
        if audit_id not in self._reviews:
            self._load(audit_id)
        return self._reviews.get(audit_id, [])

    def get_reviews_for_finding(
        self, audit_id: str, finding_id: str
    ) -> List[Dict[str, Any]]:
        """Get all review decisions for a specific finding."""
        all_reviews = self.get_reviews_for_audit(audit_id)
        return [r for r in all_reviews if r["finding_id"] == finding_id]

    def get_latest_decision(
        self, audit_id: str, finding_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent decision for a finding."""
        reviews = self.get_reviews_for_finding(audit_id, finding_id)
        return reviews[-1] if reviews else None

    def is_audit_fully_reviewed(
        self, audit_id: str, required_finding_ids: List[str]
    ) -> bool:
        """
        Check if all required findings have been reviewed.
        A finding is considered reviewed if its latest decision is APPROVED or REJECTED.
        """
        for fid in required_finding_ids:
            latest = self.get_latest_decision(audit_id, fid)
            if not latest or latest["decision"] not in (
                HumanReviewDecision.APPROVE,
                HumanReviewDecision.REJECT,
            ):
                return False
        return True

    def _persist(self, audit_id: str):
        """Persist audit reviews to JSON file."""
        filepath = os.path.join(self.persistence_dir, f"{audit_id}_reviews.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._reviews.get(audit_id, []), f, indent=2)

    def _load(self, audit_id: str):
        """Load audit reviews from JSON file if exists."""
        filepath = os.path.join(self.persistence_dir, f"{audit_id}_reviews.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                self._reviews[audit_id] = json.load(f)
        else:
            self._reviews[audit_id] = []
