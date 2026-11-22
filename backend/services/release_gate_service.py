"""
AUDRYN Release Gate Service.

Deterministic, testable logic that evaluates whether an audit report
may transition from DRAFT to REVIEW_READY or FINALIZED.
No state is ever inferred from finding count alone.
"""
from typing import Dict, Any, List, Optional


class ReleaseBlockReason:
    MISSING_MANDATORY_EVIDENCE = "MISSING_MANDATORY_EVIDENCE"
    CORRUPTED_EVIDENCE = "CORRUPTED_EVIDENCE"
    FAILED_EXTRACTION = "FAILED_EXTRACTION"
    CRITICAL_UNRESOLVED_FINDING = "CRITICAL_UNRESOLVED_FINDING"
    PENDING_HUMAN_REVIEW = "PENDING_HUMAN_REVIEW"
    ESCALATED_FINDING = "ESCALATED_FINDING"
    INCOMPLETE_PROCEDURE = "INCOMPLETE_PROCEDURE"
    INVALID_PROVENANCE_LINK = "INVALID_PROVENANCE_LINK"
    COMPLETENESS_GATE_BLOCKED = "COMPLETENESS_GATE_BLOCKED"


class ReleaseGateResult:
    """Immutable record of a release gate evaluation."""

    def __init__(
        self,
        passed: bool,
        status: str,
        blockers: List[Dict[str, str]],
        warnings: List[Dict[str, str]],
    ):
        self.passed = passed
        self.status = status
        self.blockers = blockers
        self.warnings = warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "status": self.status,
            "blockers": self.blockers,
            "warnings": self.warnings,
        }


class ReleaseGateService:
    """
    Evaluates whether an AUDRYN audit report satisfies release criteria.
    Returns explicit pass/fail with categorized blockers and warnings.
    """

    def evaluate(
        self,
        completeness_status: str,
        findings: List[Dict[str, Any]],
        counter_evidence: List[Dict[str, Any]],
        gap_register: List[Dict[str, Any]],
        human_review_status: str,
        not_checked_items: List[Dict[str, Any]],
        evidence_records: Optional[List[Dict[str, Any]]] = None,
    ) -> ReleaseGateResult:
        blockers: List[Dict[str, str]] = []
        warnings: List[Dict[str, str]] = []

        # 1. Completeness gate
        if completeness_status == "BLOCKED":
            blockers.append({
                "reason": ReleaseBlockReason.COMPLETENESS_GATE_BLOCKED,
                "detail": "Audit completeness gate is BLOCKED. Mandatory documents missing or corrupted.",
            })

        # 2. Evidence corruption / extraction failures
        if evidence_records:
            for ev in evidence_records:
                status = ev.get("extraction_status", "PENDING")
                if status == "CORRUPTED":
                    blockers.append({
                        "reason": ReleaseBlockReason.CORRUPTED_EVIDENCE,
                        "detail": f"Evidence '{ev.get('evidence_id', '?')}' is corrupted.",
                    })
                elif status == "FAILED":
                    blockers.append({
                        "reason": ReleaseBlockReason.FAILED_EXTRACTION,
                        "detail": f"Evidence '{ev.get('evidence_id', '?')}' extraction failed.",
                    })

        # 3. Critical unresolved findings
        for f in findings:
            sev = f.get("severity", "LOW")
            status = f.get("status", "OPEN")
            if sev in ("CRITICAL", "HIGH") and status == "OPEN":
                blockers.append({
                    "reason": ReleaseBlockReason.CRITICAL_UNRESOLVED_FINDING,
                    "detail": f"Finding '{f.get('finding_id', '?')}' (severity={sev}) remains OPEN.",
                })

        # 4. Human review pending
        if human_review_status == "PENDING":
            blockers.append({
                "reason": ReleaseBlockReason.PENDING_HUMAN_REVIEW,
                "detail": "Human review is PENDING. Material findings require auditor signoff.",
            })
        elif human_review_status == "ESCALATED":
            blockers.append({
                "reason": ReleaseBlockReason.ESCALATED_FINDING,
                "detail": "One or more findings have been ESCALATED and require resolution.",
            })

        # 5. Critical gaps
        for g in gap_register:
            gsev = g.get("severity", "LOW")
            gstat = g.get("status", "OPEN")
            if gsev == "CRITICAL" and gstat != "RESOLVED":
                blockers.append({
                    "reason": ReleaseBlockReason.INCOMPLETE_PROCEDURE,
                    "detail": f"Critical audit gap '{g.get('gap_id', '?')}' remains unresolved.",
                })
            elif gsev in ("MEDIUM", "HIGH") and gstat != "RESOLVED":
                warnings.append({
                    "reason": "NON_CRITICAL_GAP",
                    "detail": f"Gap '{g.get('gap_id', '?')}' (severity={gsev}) remains open but non-blocking.",
                })

        # 6. Not-checked items as warnings (disclosed, not blocking)
        for nc in not_checked_items:
            nc_status = nc.get("status", "NOT_STARTED")
            if nc_status not in ("COMPLETED",):
                warnings.append({
                    "reason": "NOT_CHECKED_ITEM",
                    "detail": f"Procedure '{nc.get('procedure_name', '?')}' has not been completed.",
                })

        passed = len(blockers) == 0
        status = "FINALIZED" if passed else "BLOCKED"

        return ReleaseGateResult(
            passed=passed,
            status=status,
            blockers=blockers,
            warnings=warnings,
        )
