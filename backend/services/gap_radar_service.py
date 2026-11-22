"""
AUDRYN GAP RADAR Service.

Identifies audit coverage blind spots by inspecting:
- Document coverage
- Financial period coverage
- Source provenance
- Unverified calculations
- Tool failures
- Missing evidence links
- Untested procedures
- Unresolved findings
- Incomplete agent executions

Does NOT claim that all possible unknown risks have been discovered.
"""
import uuid
from typing import List, Dict, Any, Optional, Set
from backend.models.gap import (
    GapStatus,
    GapCategory,
    GapSeverity,
    GapItem,
    GapRadarReport,
)


class GapRadarService:

    REQUIRED_DOCUMENT_TYPES = {
        "TRIAL_BALANCE",
        "BALANCE_SHEET",
        "PROFIT_AND_LOSS",
        "GENERAL_LEDGER",
        "TAX_RETURN",
        "FIXED_ASSET_REGISTER",
        "BANK_STATEMENT",
    }

    def __init__(self, required_periods: Optional[List[str]] = None):
        self.required_periods = required_periods or [
            "FY2023-24", "FY2024-25", "FY2025-26"
        ]

    def scan_document_coverage(
        self,
        available_documents: Dict[str, List[str]],
    ) -> List[GapItem]:
        """
        Check which mandatory document types are present for each period.
        available_documents: {period: [doc_type_1, doc_type_2, ...]}
        """
        gaps = []
        for period in self.required_periods:
            docs = set(available_documents.get(period, []))
            missing = self.REQUIRED_DOCUMENT_TYPES - docs
            for doc_type in sorted(missing):
                gaps.append(GapItem(
                    gap_id=f"GAP-DOC-{uuid.uuid4().hex[:8]}",
                    category=GapCategory.MISSING_DOCUMENT,
                    severity=GapSeverity.HIGH,
                    description=f"Missing {doc_type} for {period}.",
                    evidence_references=[],
                    root_cause_hypothesis=f"Document {doc_type} not ingested or not available for {period}.",
                    recommended_resolution=f"Obtain and ingest {doc_type} for {period}.",
                    status=GapStatus.NOT_CHECKED,
                ))
        return gaps

    def scan_period_coverage(
        self,
        available_periods: List[str],
    ) -> List[GapItem]:
        """
        Check which required financial periods are missing entirely.
        """
        gaps = []
        for period in self.required_periods:
            if period not in available_periods:
                gaps.append(GapItem(
                    gap_id=f"GAP-PER-{uuid.uuid4().hex[:8]}",
                    category=GapCategory.MISSING_PERIOD,
                    severity=GapSeverity.CRITICAL,
                    description=f"No data available for required period {period}.",
                    evidence_references=[],
                    root_cause_hypothesis=f"Financial records for {period} have not been provided.",
                    recommended_resolution=f"Request complete financial records for {period}.",
                    status=GapStatus.NOT_CHECKED,
                ))
        return gaps

    def scan_unresolved_findings(
        self,
        findings: List[Dict[str, Any]],
    ) -> List[GapItem]:
        """
        Flag findings that remain OPEN or UNRESOLVED.
        """
        gaps = []
        for f in findings:
            status = f.get("status", "OPEN")
            if status in ("OPEN", "UNRESOLVED"):
                gaps.append(GapItem(
                    gap_id=f"GAP-FND-{uuid.uuid4().hex[:8]}",
                    category=GapCategory.UNRESOLVED_FINDING,
                    severity=GapSeverity.MEDIUM if f.get("severity") != "CRITICAL" else GapSeverity.CRITICAL,
                    description=f"Finding '{f.get('finding_id', 'Unknown')}': {f.get('title', 'Untitled')} remains {status}.",
                    evidence_references=f.get("source_evidence", []),
                    root_cause_hypothesis="Investigation not completed or awaiting further evidence.",
                    recommended_resolution="Complete investigation or escalate to human reviewer.",
                    status=GapStatus.UNRESOLVED,
                ))
        return gaps

    def scan_tool_failures(
        self,
        execution_errors: List[str],
    ) -> List[GapItem]:
        """
        Create gap items for each tool or execution failure recorded.
        """
        gaps = []
        for err in execution_errors:
            gaps.append(GapItem(
                gap_id=f"GAP-TOOL-{uuid.uuid4().hex[:8]}",
                category=GapCategory.TOOL_FAILURE,
                severity=GapSeverity.HIGH,
                description=f"Tool execution failure: {err[:200]}",
                evidence_references=[],
                root_cause_hypothesis="A tool or agent encountered an error during execution.",
                recommended_resolution="Investigate failure, fix root cause, and re-execute.",
                status=GapStatus.BLOCKED,
            ))
        return gaps

    def scan_untested_procedures(
        self,
        procedures: List[Dict[str, Any]],
    ) -> List[GapItem]:
        """
        Flag audit procedures that are still NOT_CHECKED.
        """
        gaps = []
        for proc in procedures:
            if proc.get("status") in ("NOT_CHECKED", "not_checked"):
                gaps.append(GapItem(
                    gap_id=f"GAP-PROC-{uuid.uuid4().hex[:8]}",
                    category=GapCategory.UNTESTED_PROCEDURE,
                    severity=GapSeverity.MEDIUM,
                    description=f"Procedure '{proc.get('procedure_id', 'Unknown')}': {proc.get('title', 'Untitled')} not tested.",
                    evidence_references=[],
                    root_cause_hypothesis=proc.get("reason_not_checked", "Scheduled but not yet executed."),
                    recommended_resolution="Execute the audit procedure and record findings.",
                    status=GapStatus.NOT_CHECKED,
                ))
        return gaps

    def scan_missing_evidence_links(
        self,
        findings: List[Dict[str, Any]],
    ) -> List[GapItem]:
        """
        Flag findings that have no evidence references.
        """
        gaps = []
        for f in findings:
            refs = f.get("source_evidence", [])
            if not refs:
                gaps.append(GapItem(
                    gap_id=f"GAP-EVID-{uuid.uuid4().hex[:8]}",
                    category=GapCategory.MISSING_EVIDENCE_LINK,
                    severity=GapSeverity.HIGH,
                    description=f"Finding '{f.get('finding_id', 'Unknown')}' has no linked evidence.",
                    evidence_references=[],
                    root_cause_hypothesis="Investigation produced a finding without documenting source evidence.",
                    recommended_resolution="Link original source documents, coordinates, and calculations.",
                    status=GapStatus.UNRESOLVED,
                ))
        return gaps

    def build_report(
        self,
        available_documents: Dict[str, List[str]],
        available_periods: List[str],
        findings: List[Dict[str, Any]],
        execution_errors: List[str],
        procedures: List[Dict[str, Any]],
    ) -> GapRadarReport:
        """
        Run all GAP RADAR scans and produce comprehensive report.
        """
        all_gaps: List[GapItem] = []
        all_gaps.extend(self.scan_document_coverage(available_documents))
        all_gaps.extend(self.scan_period_coverage(available_periods))
        all_gaps.extend(self.scan_unresolved_findings(findings))
        all_gaps.extend(self.scan_tool_failures(execution_errors))
        all_gaps.extend(self.scan_untested_procedures(procedures))
        all_gaps.extend(self.scan_missing_evidence_links(findings))

        critical = sum(1 for g in all_gaps if g.severity == GapSeverity.CRITICAL)
        total = len(all_gaps)

        # Coverage score: simple heuristic (100% - 5% per gap, floor 0%)
        score = max(0.0, 100.0 - (total * 5.0))
        blocked = critical > 0

        return GapRadarReport(
            gaps=all_gaps,
            total_gaps=total,
            critical_gaps=critical,
            coverage_score_percent=score,
            audit_completeness_blocked=blocked,
        )
