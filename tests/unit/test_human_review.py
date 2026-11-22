"""
AUDRYN Phase 3 — Human Review Service Tests.

Covers:
- Record approve decision
- Record reject decision
- Record request evidence decision
- Record escalate decision
- Invalid decision rejection
- Review history retrieval
- Persistence and reload
- Audit fully reviewed check
"""
import os
import tempfile
import pytest
from backend.services.human_review_service import HumanReviewService, HumanReviewDecision


@pytest.fixture
def service(tmp_path):
    return HumanReviewService(persistence_dir=str(tmp_path))


def test_approve_decision(service):
    record = service.record_decision(
        audit_id="AUD-001",
        finding_id="FND-001",
        reviewer_name="Auditor A",
        decision=HumanReviewDecision.APPROVE,
        comments="Verified and approved.",
    )
    assert record["decision"] == "APPROVED"
    assert record["reviewer_name"] == "Auditor A"
    assert record["finding_id"] == "FND-001"
    assert "timestamp" in record


def test_reject_decision(service):
    record = service.record_decision(
        audit_id="AUD-001",
        finding_id="FND-002",
        reviewer_name="Auditor B",
        decision=HumanReviewDecision.REJECT,
        comments="Insufficient evidence.",
    )
    assert record["decision"] == "REJECTED"


def test_request_evidence_decision(service):
    record = service.record_decision(
        audit_id="AUD-001",
        finding_id="FND-003",
        reviewer_name="Manager C",
        decision=HumanReviewDecision.REQUEST_EVIDENCE,
        comments="Need bank confirmation letter.",
    )
    assert record["decision"] == "REQUEST_EVIDENCE"


def test_escalate_decision(service):
    record = service.record_decision(
        audit_id="AUD-001",
        finding_id="FND-004",
        reviewer_name="Partner D",
        decision=HumanReviewDecision.ESCALATE,
    )
    assert record["decision"] == "ESCALATED"


def test_invalid_decision_rejected(service):
    with pytest.raises(ValueError, match="Invalid decision"):
        service.record_decision(
            audit_id="AUD-001",
            finding_id="FND-005",
            reviewer_name="Auditor E",
            decision="INVALID_STATUS",
        )


def test_review_history_retrieval(service):
    service.record_decision("AUD-002", "FND-010", "A", HumanReviewDecision.APPROVE)
    service.record_decision("AUD-002", "FND-010", "B", HumanReviewDecision.REJECT)
    reviews = service.get_reviews_for_finding("AUD-002", "FND-010")
    assert len(reviews) == 2


def test_latest_decision(service):
    service.record_decision("AUD-003", "FND-020", "A", HumanReviewDecision.REQUEST_EVIDENCE)
    service.record_decision("AUD-003", "FND-020", "A", HumanReviewDecision.APPROVE)
    latest = service.get_latest_decision("AUD-003", "FND-020")
    assert latest["decision"] == "APPROVED"


def test_persistence_and_reload(service):
    service.record_decision("AUD-004", "FND-030", "A", HumanReviewDecision.APPROVE)
    # Create new service instance pointing to same directory
    service2 = HumanReviewService(persistence_dir=service.persistence_dir)
    reviews = service2.get_reviews_for_audit("AUD-004")
    assert len(reviews) == 1
    assert reviews[0]["decision"] == "APPROVED"


def test_audit_fully_reviewed(service):
    service.record_decision("AUD-005", "FND-A", "X", HumanReviewDecision.APPROVE)
    service.record_decision("AUD-005", "FND-B", "X", HumanReviewDecision.REJECT)
    assert service.is_audit_fully_reviewed("AUD-005", ["FND-A", "FND-B"])


def test_audit_not_fully_reviewed(service):
    service.record_decision("AUD-006", "FND-A", "X", HumanReviewDecision.APPROVE)
    # FND-B not reviewed yet
    assert not service.is_audit_fully_reviewed("AUD-006", ["FND-A", "FND-B"])


def test_resume_interrupted_workflow(service):
    """Simulate an interrupted workflow resuming with human input."""
    # Phase 1: Record initial escalation
    service.record_decision("AUD-007", "FND-C", "Mgr", HumanReviewDecision.ESCALATE)
    latest = service.get_latest_decision("AUD-007", "FND-C")
    assert latest["decision"] == "ESCALATED"
    # Not fully reviewed
    assert not service.is_audit_fully_reviewed("AUD-007", ["FND-C"])
    # Phase 2: Partner approves after escalation
    service.record_decision("AUD-007", "FND-C", "Partner", HumanReviewDecision.APPROVE, "Partner reviewed.")
    assert service.is_audit_fully_reviewed("AUD-007", ["FND-C"])
