"""
AUDRYN Counter-Evidence Intelligence Service.

For each material investigation finding, creates a structured challenge
that evaluates supporting evidence, contradictory evidence, alternative
explanations, and deterministic calculation verification.

Does NOT automatically label anomalies as fraud.
Disagreements trigger escalation, not automated resolution.
"""
import uuid
from decimal import Decimal
from typing import List, Dict, Any, Optional
from backend.models.counter_evidence import (
    ReviewVerdict,
    CounterEvidenceChallenge,
    CounterEvidenceReport,
)
from backend.services.financial_engine import DeterministicFinancialEngine


class CounterEvidenceService:

    def __init__(
        self,
        engine: Optional[DeterministicFinancialEngine] = None,
    ):
        self.engine = engine or DeterministicFinancialEngine()

    def create_challenge(
        self,
        finding_id: str,
        original_hypothesis: str,
        impact_amount: str,
        supporting_evidence: List[str],
        contradictory_evidence: Optional[List[str]] = None,
        alternative_explanations: Optional[List[str]] = None,
        expected_amount: Optional[str] = None,
        actual_amount: Optional[str] = None,
        reviewer_role: str = "Independent Reviewer",
    ) -> CounterEvidenceChallenge:
        """
        Create a structured counter-evidence challenge for one finding.
        Performs deterministic verification if expected/actual amounts provided.
        """
        calc_verification = "No deterministic verification performed."
        missing = []

        if expected_amount and actual_amount:
            expected = self.engine.round_currency(self.engine.to_decimal(expected_amount))
            actual = self.engine.round_currency(self.engine.to_decimal(actual_amount))
            variance = self.engine.round_currency(actual - expected)
            calc_verification = (
                f"Deterministic check: Expected={expected}, Actual={actual}, "
                f"Variance={variance}. Calculation {'confirms' if variance != Decimal('0') else 'refutes'} discrepancy."
            )

        if not supporting_evidence:
            missing.append("No supporting evidence provided for original hypothesis.")
        if not contradictory_evidence:
            missing.append("No contradictory evidence searched or found.")

        # Determine verdict based on evidence balance
        contra = contradictory_evidence or []
        alt = alternative_explanations or []
        verdict = self._evaluate_verdict(supporting_evidence, contra, alt, missing)
        requires_escalation = verdict in (
            ReviewVerdict.CONTRADICTED,
            ReviewVerdict.UNRESOLVED,
            ReviewVerdict.INSUFFICIENT_EVIDENCE,
            ReviewVerdict.PARTIALLY_SUPPORTED,
        )

        rationale = self._build_rationale(verdict, supporting_evidence, contra, alt, missing)

        return CounterEvidenceChallenge(
            challenge_id=f"CE-{uuid.uuid4().hex[:8]}",
            finding_id=finding_id,
            original_hypothesis=original_hypothesis,
            supporting_evidence=supporting_evidence,
            contradictory_evidence=contra,
            alternative_explanations=alt,
            calculation_verification=calc_verification,
            missing_evidence=missing,
            reviewer_role=reviewer_role,
            reviewer_verdict=verdict,
            verdict_rationale=rationale,
            requires_escalation=requires_escalation,
        )

    def _evaluate_verdict(
        self,
        supporting: List[str],
        contradictory: List[str],
        alternatives: List[str],
        missing: List[str],
    ) -> ReviewVerdict:
        """Deterministic verdict evaluation based on evidence balance."""
        if not supporting and not contradictory:
            return ReviewVerdict.INSUFFICIENT_EVIDENCE
        if contradictory and not supporting:
            return ReviewVerdict.CONTRADICTED
        if supporting and contradictory:
            return ReviewVerdict.PARTIALLY_SUPPORTED
        if supporting and not contradictory and alternatives:
            return ReviewVerdict.PARTIALLY_SUPPORTED
        if supporting and not contradictory:
            return ReviewVerdict.SUPPORTED
        if missing and not supporting:
            return ReviewVerdict.UNRESOLVED
        return ReviewVerdict.UNRESOLVED

    def _build_rationale(
        self,
        verdict: ReviewVerdict,
        supporting: List[str],
        contradictory: List[str],
        alternatives: List[str],
        missing: List[str],
    ) -> str:
        parts = [f"Verdict: {verdict.value}."]
        if supporting:
            parts.append(f"{len(supporting)} supporting evidence item(s).")
        if contradictory:
            parts.append(f"{len(contradictory)} contradictory evidence item(s).")
        if alternatives:
            parts.append(f"{len(alternatives)} alternative explanation(s) identified.")
        if missing:
            parts.append(f"{len(missing)} missing evidence item(s).")
        return " ".join(parts)

    def build_report(
        self,
        challenges: List[CounterEvidenceChallenge],
    ) -> CounterEvidenceReport:
        """
        Aggregate individual challenges into a comprehensive counter-evidence report.
        """
        return CounterEvidenceReport(
            challenges=challenges,
            total_reviewed=len(challenges),
            total_contradicted=sum(
                1 for c in challenges if c.reviewer_verdict == ReviewVerdict.CONTRADICTED
            ),
            total_supported=sum(
                1 for c in challenges if c.reviewer_verdict == ReviewVerdict.SUPPORTED
            ),
            total_unresolved=sum(
                1 for c in challenges if c.reviewer_verdict in (
                    ReviewVerdict.UNRESOLVED,
                    ReviewVerdict.INSUFFICIENT_EVIDENCE,
                    ReviewVerdict.PARTIALLY_SUPPORTED,
                )
            ),
            summary=self._build_summary(challenges),
        )

    def _build_summary(self, challenges: List[CounterEvidenceChallenge]) -> str:
        if not challenges:
            return "No findings reviewed."
        escalations = sum(1 for c in challenges if c.requires_escalation)
        return (
            f"Reviewed {len(challenges)} finding(s). "
            f"{escalations} require(s) further review or escalation."
        )
