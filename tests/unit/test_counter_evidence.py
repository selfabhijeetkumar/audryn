"""
AUDRYN Phase 3 — Counter-Evidence Intelligence Tests.

Covers:
- Finding supported (evidence present, no contradictions)
- Finding contradicted (contradictory evidence present)
- Insufficient evidence (no evidence at all)
- Partially supported (conflicting signals)
- Deterministic calculation verification
- Report aggregation
"""
import pytest
from backend.services.counter_evidence_service import CounterEvidenceService
from backend.models.counter_evidence import ReviewVerdict


@pytest.fixture
def service():
    return CounterEvidenceService()


def test_finding_supported(service):
    """Finding with supporting evidence and no contradictions -> SUPPORTED."""
    challenge = service.create_challenge(
        finding_id="FND-001",
        original_hypothesis="Trial balance is unbalanced by $10,000.",
        impact_amount="10000",
        supporting_evidence=["trial_balance_fy2024_25.csv:row_15"],
        contradictory_evidence=[],
        alternative_explanations=[],
        expected_amount="500000",
        actual_amount="510000",
    )
    assert challenge.reviewer_verdict == ReviewVerdict.SUPPORTED
    assert not challenge.requires_escalation
    assert "confirms" in challenge.calculation_verification


def test_finding_contradicted(service):
    """Finding with contradictory evidence and no support -> CONTRADICTED."""
    challenge = service.create_challenge(
        finding_id="FND-002",
        original_hypothesis="Duplicate invoice posted.",
        impact_amount="22400",
        supporting_evidence=[],
        contradictory_evidence=["credit_note_CN_2024_001.pdf"],
        alternative_explanations=[],
    )
    assert challenge.reviewer_verdict == ReviewVerdict.CONTRADICTED
    assert challenge.requires_escalation


def test_finding_insufficient_evidence(service):
    """No supporting or contradictory evidence -> INSUFFICIENT_EVIDENCE."""
    challenge = service.create_challenge(
        finding_id="FND-003",
        original_hypothesis="Unexplained journal entry.",
        impact_amount="5000",
        supporting_evidence=[],
        contradictory_evidence=[],
    )
    assert challenge.reviewer_verdict == ReviewVerdict.INSUFFICIENT_EVIDENCE
    assert challenge.requires_escalation


def test_finding_partially_supported(service):
    """Supporting evidence plus contradictory evidence -> PARTIALLY_SUPPORTED."""
    challenge = service.create_challenge(
        finding_id="FND-004",
        original_hypothesis="Depreciation rate is incorrect.",
        impact_amount="50000",
        supporting_evidence=["fixed_asset_register.csv:row_5"],
        contradictory_evidence=["management_response_note.pdf"],
        alternative_explanations=["Different rate applied under Section 32(1)(ii)"],
    )
    assert challenge.reviewer_verdict == ReviewVerdict.PARTIALLY_SUPPORTED
    assert challenge.requires_escalation


def test_calculation_verification_zero_variance(service):
    """When expected == actual, verification should say 'refutes' discrepancy."""
    challenge = service.create_challenge(
        finding_id="FND-005",
        original_hypothesis="Balance sheet mismatch.",
        impact_amount="0",
        supporting_evidence=["balance_sheet.csv"],
        expected_amount="1000000",
        actual_amount="1000000",
    )
    assert "refutes" in challenge.calculation_verification


def test_report_aggregation(service):
    """Report should correctly count verdicts."""
    c1 = service.create_challenge("F1", "H1", "100", ["e1"])
    c2 = service.create_challenge("F2", "H2", "200", [], ["contra1"])
    c3 = service.create_challenge("F3", "H3", "300", [])
    report = service.build_report([c1, c2, c3])
    assert report.total_reviewed == 3
    assert report.total_supported == 1
    assert report.total_contradicted == 1
    assert report.total_unresolved == 1  # INSUFFICIENT_EVIDENCE counted as unresolved
