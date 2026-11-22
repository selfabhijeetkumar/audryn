"""
AUDRYN Phase 3 — GAP RADAR Tests.

Covers:
- Missing document gaps
- Missing period gaps
- Unresolved findings
- Tool execution failures
- Untested procedures
- Missing evidence links
- Full report generation
"""
import pytest
from backend.services.gap_radar_service import GapRadarService
from backend.models.gap import GapCategory, GapSeverity, GapStatus


@pytest.fixture
def service():
    return GapRadarService(required_periods=["FY2023-24", "FY2024-25"])


def test_no_gaps_when_complete(service):
    """Full document coverage and no issues should produce zero gaps."""
    all_docs = {
        "FY2023-24": list(service.REQUIRED_DOCUMENT_TYPES),
        "FY2024-25": list(service.REQUIRED_DOCUMENT_TYPES),
    }
    report = service.build_report(
        available_documents=all_docs,
        available_periods=["FY2023-24", "FY2024-25"],
        findings=[],
        execution_errors=[],
        procedures=[],
    )
    assert report.total_gaps == 0
    assert report.coverage_score_percent == 100.0
    assert not report.audit_completeness_blocked


def test_missing_document_gap(service):
    """Missing BANK_STATEMENT should create a document gap."""
    docs = {
        "FY2023-24": list(service.REQUIRED_DOCUMENT_TYPES),
        "FY2024-25": [d for d in service.REQUIRED_DOCUMENT_TYPES if d != "BANK_STATEMENT"],
    }
    gaps = service.scan_document_coverage(docs)
    assert any(g.category == GapCategory.MISSING_DOCUMENT for g in gaps)
    bank_gaps = [g for g in gaps if "BANK_STATEMENT" in g.description]
    assert len(bank_gaps) == 1
    assert bank_gaps[0].severity == GapSeverity.HIGH


def test_missing_period_gap(service):
    """Missing entire period should create a CRITICAL gap."""
    gaps = service.scan_period_coverage(["FY2023-24"])  # FY2024-25 missing
    assert len(gaps) == 1
    assert gaps[0].category == GapCategory.MISSING_PERIOD
    assert gaps[0].severity == GapSeverity.CRITICAL


def test_unresolved_finding_gap(service):
    """OPEN findings should be flagged."""
    findings = [
        {"finding_id": "FND-001", "title": "TB Variance", "status": "OPEN", "severity": "HIGH"},
    ]
    gaps = service.scan_unresolved_findings(findings)
    assert len(gaps) == 1
    assert gaps[0].category == GapCategory.UNRESOLVED_FINDING


def test_tool_failure_gap(service):
    """Execution errors should create TOOL_FAILURE gaps."""
    errors = ["CrewAI timeout after 120s", "Ollama connection refused"]
    gaps = service.scan_tool_failures(errors)
    assert len(gaps) == 2
    assert all(g.category == GapCategory.TOOL_FAILURE for g in gaps)
    assert all(g.severity == GapSeverity.HIGH for g in gaps)


def test_untested_procedure_gap(service):
    """NOT_CHECKED procedures should create gaps."""
    procedures = [
        {"procedure_id": "PROC-01", "title": "Bank Reconciliation", "status": "NOT_CHECKED",
         "reason_not_checked": "Deferred."},
    ]
    gaps = service.scan_untested_procedures(procedures)
    assert len(gaps) == 1
    assert gaps[0].category == GapCategory.UNTESTED_PROCEDURE


def test_missing_evidence_link_gap(service):
    """Findings without source_evidence should be flagged."""
    findings = [
        {"finding_id": "FND-001", "title": "Anomaly", "source_evidence": []},
        {"finding_id": "FND-002", "title": "Normal", "source_evidence": ["file.csv"]},
    ]
    gaps = service.scan_missing_evidence_links(findings)
    assert len(gaps) == 1
    assert gaps[0].category == GapCategory.MISSING_EVIDENCE_LINK


def test_report_blocks_on_critical_gaps(service):
    """Report with critical gaps should block audit completeness."""
    report = service.build_report(
        available_documents={"FY2023-24": list(service.REQUIRED_DOCUMENT_TYPES)},
        available_periods=["FY2023-24"],  # FY2024-25 missing = CRITICAL
        findings=[],
        execution_errors=[],
        procedures=[],
    )
    assert report.critical_gaps >= 1
    assert report.audit_completeness_blocked
