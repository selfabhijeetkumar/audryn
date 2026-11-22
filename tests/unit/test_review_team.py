"""
AUDRYN Phase 3 — MS Agent Framework Independent Review Tests.

Covers:
- Counter-evidence review (deterministic path)
- Blind-spot detection
- Independent finding review verdicts
- Reversal detection
- Timing difference detection
- Invalid verdict rejection
"""
import pytest
from backend.agents.review_team import (
    run_counter_evidence_review,
    run_blind_spot_review,
    run_independent_finding_review,
    verify_variance_tool,
    check_reversal_tool,
    check_timing_difference_tool,
)
from backend.models.counter_evidence import ReviewVerdict


class TestCounterEvidenceReview:
    def test_supported_finding(self):
        finding = {
            "finding_id": "FND-001",
            "description": "TB variance $10k",
            "source_evidence": ["trial_balance.csv"],
            "impact_amount": "10000",
            "expected_amount": "500000",
        }
        result = run_counter_evidence_review(finding, {})
        assert result["verdict"] == ReviewVerdict.SUPPORTED.value

    def test_contradicted_by_reversal(self):
        finding = {
            "finding_id": "FND-002",
            "description": "Duplicate payment",
            "source_evidence": ["ledger.csv"],
            "impact_amount": "5000",
        }
        data = {
            "related_transactions": [
                {"amount": "5000"},
                {"amount": "-5000"},
            ]
        }
        result = run_counter_evidence_review(finding, data)
        assert result["verdict"] == ReviewVerdict.CONTRADICTED.value
        assert len(result["contradictory_evidence"]) > 0

    def test_timing_difference_partially_supported(self):
        finding = {
            "finding_id": "FND-003",
            "description": "Unreconciled payment",
            "source_evidence": ["bank_stmt.csv"],
            "record_date": "2025-03-31",
        }
        data = {"settlement_date": "2025-04-04"}
        result = run_counter_evidence_review(finding, data)
        assert result["verdict"] == ReviewVerdict.PARTIALLY_SUPPORTED.value

    def test_insufficient_evidence(self):
        finding = {
            "finding_id": "FND-004",
            "description": "Missing voucher",
            "source_evidence": [],
        }
        result = run_counter_evidence_review(finding, {})
        assert result["verdict"] == ReviewVerdict.INSUFFICIENT_EVIDENCE.value


class TestBlindSpotReview:
    def test_unsupported_conclusion_detected(self):
        state = {
            "investigation_findings": [
                {"finding_id": "F1", "title": "No evidence", "source_evidence": []},
            ],
            "execution_errors": [],
            "counter_evidence": [],
        }
        spots = run_blind_spot_review(state)
        assert any(s["type"] == "UNSUPPORTED_CONCLUSION" for s in spots)

    def test_execution_gaps_detected(self):
        state = {
            "investigation_findings": [],
            "execution_errors": ["CrewAI timeout"],
            "counter_evidence": [],
        }
        spots = run_blind_spot_review(state)
        assert any(s["type"] == "EXECUTION_GAPS" for s in spots)

    def test_incomplete_review_detected(self):
        state = {
            "investigation_findings": [],
            "execution_errors": [],
            "counter_evidence": [
                {"reviewer_verdict": "UNRESOLVED"},
            ],
        }
        spots = run_blind_spot_review(state)
        assert any(s["type"] == "INCOMPLETE_REVIEW" for s in spots)

    def test_clean_state_no_blind_spots(self):
        state = {
            "investigation_findings": [
                {"finding_id": "F1", "title": "OK", "source_evidence": ["file.csv"]},
            ],
            "execution_errors": [],
            "counter_evidence": [
                {"reviewer_verdict": "SUPPORTED"},
            ],
        }
        spots = run_blind_spot_review(state)
        assert len(spots) == 0


class TestIndependentFindingReview:
    def test_supported_verdict(self):
        finding = {"finding_id": "F1", "source_evidence": ["x.csv"]}
        ce = {"calculation_check": "Variance: 100", "contradictory_evidence": []}
        result = run_independent_finding_review(finding, ce)
        assert result["independent_verdict"] == ReviewVerdict.SUPPORTED.value

    def test_contradicted_verdict(self):
        finding = {"finding_id": "F2", "source_evidence": ["x.csv"]}
        ce = {"contradictory_evidence": ["reversal found"], "calculation_check": ""}
        result = run_independent_finding_review(finding, ce)
        assert result["independent_verdict"] == ReviewVerdict.CONTRADICTED.value

    def test_insufficient_evidence_verdict(self):
        finding = {"finding_id": "F3", "source_evidence": []}
        ce = {"contradictory_evidence": [], "calculation_check": ""}
        result = run_independent_finding_review(finding, ce)
        assert result["independent_verdict"] == ReviewVerdict.INSUFFICIENT_EVIDENCE.value


class TestDeterministicTools:
    def test_verify_variance_material(self):
        result = verify_variance_tool("100000", "108000")
        assert "8000" in result
        assert "MATERIAL" in result

    def test_verify_variance_immaterial(self):
        result = verify_variance_tool("100000", "100100")
        assert "IMMATERIAL" in result

    def test_reversal_detected(self):
        result = check_reversal_tool("5000, -5000, 3000")
        assert "REVERSALS FOUND" in result

    def test_no_reversal(self):
        result = check_reversal_tool("5000, 3000, 2000")
        assert "No reversals" in result

    def test_timing_difference(self):
        result = check_timing_difference_tool("2025-03-31", "2025-04-04")
        assert "TIMING DIFFERENCE" in result

    def test_no_timing_difference(self):
        result = check_timing_difference_tool("2025-03-31", "2025-03-31")
        assert "No timing difference" in result
