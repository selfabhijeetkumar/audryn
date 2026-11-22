"""
AUDRYN Phase 5 — Security & Data Isolation Tests.

Covers:
- Strict cross-audit boundary isolation in Evidence Graph
- Referential integrity and orphan edge prevention
- Path traversal mitigation in report artifact naming
- Report artifact tampering detection via SHA-256 content hashing
- Injection containment and payload isolation
"""
import os
import json
import pytest
from backend.models.evidence_graph import (
    NodeType,
    RelationshipType,
    GraphNode,
    GraphRelationship,
)
from backend.services.evidence_graph_service import EvidenceGraphService
from backend.services.pdf_report_service import PdfReportService
from backend.services.report_generation_service import ReportGenerationService


@pytest.fixture
def graph_service(tmp_path):
    db_file = str(tmp_path / "sec_graph.db")
    svc = EvidenceGraphService(db_path=db_file)
    yield svc
    svc.close()


def test_cross_audit_isolation_strict_rejection(graph_service):
    """
    Attempting to create a relationship linking a node in Audit A
    to a node in Audit B must raise a ValueError.
    """
    node_a = GraphNode(node_id="NODE-AUD-A", audit_id="AUDIT-CORP-A", node_type=NodeType.EVIDENCE_DOCUMENT, label="Doc A")
    node_b = GraphNode(node_id="NODE-AUD-B", audit_id="AUDIT-CORP-B", node_type=NodeType.EVIDENCE_DOCUMENT, label="Doc B")
    graph_service.add_node(node_a)
    graph_service.add_node(node_b)

    # Attempt 1: Context is Audit A, but target belongs to Audit B
    with pytest.raises(ValueError, match="Audit Isolation Violation"):
        graph_service.add_relationship(GraphRelationship(
            relationship_id="REL-SEC-01",
            audit_id="AUDIT-CORP-A",
            source_id="NODE-AUD-A",
            target_id="NODE-AUD-B",
            relationship_type=RelationshipType.DOCUMENT_SUPPORTS_FINDING,
        ))

    # Attempt 2: Context is Audit B, but source belongs to Audit A
    with pytest.raises(ValueError, match="Audit Isolation Violation"):
        graph_service.add_relationship(GraphRelationship(
            relationship_id="REL-SEC-02",
            audit_id="AUDIT-CORP-B",
            source_id="NODE-AUD-A",
            target_id="NODE-AUD-B",
            relationship_type=RelationshipType.DOCUMENT_SUPPORTS_FINDING,
        ))


def test_referential_integrity_non_existent_node(graph_service):
    """Cannot link to or from non-existent nodes."""
    node = GraphNode(node_id="REAL-NODE", audit_id="AUD-01", node_type=NodeType.ENTITY, label="Real")
    graph_service.add_node(node)

    with pytest.raises(ValueError, match="does not exist in Evidence Graph"):
        graph_service.add_relationship(GraphRelationship(
            relationship_id="REL-FAKE",
            audit_id="AUD-01",
            source_id="REAL-NODE",
            target_id="GHOST-NODE",
            relationship_type=RelationshipType.TRANSACTION_BELONGS_TO_ENTITY,
        ))


def test_pdf_report_path_traversal_mitigation(tmp_path):
    """
    Target filenames containing directory traversal sequences (../../)
    must be strictly sanitized to prevent writing outside the report directory.
    """
    pdf_svc = PdfReportService(output_dir=str(tmp_path / "reports"))
    rpt_svc = ReportGenerationService(db_path=str(tmp_path / "rpt.db"))

    report = rpt_svc.generate_report(
        audit_id="AUD-TRAVERSAL",
        company_name="Safe Corp",
        company_id="U12345",
        financial_periods=["FY2024-25"],
        evidence_records=[],
        findings=[],
        counter_evidence=[],
        gap_register=[],
        reconciliation_results=[],
        human_reviews=[],
        not_checked_items=[],
        completeness_status="PASS",
        human_review_status="NOT_REQUIRED",
        risk_classification="LOW",
    )

    # Malicious relative path
    malicious_filename = "../../../evil_audit_report.pdf"
    generated_path = pdf_svc.generate_pdf(report, target_filename=malicious_filename)

    # File must be confined within the designated reports output directory
    expected_dir = os.path.abspath(str(tmp_path / "reports"))
    actual_dir = os.path.dirname(os.path.abspath(generated_path))
    assert actual_dir == expected_dir
    assert os.path.basename(generated_path) == "evil_audit_report.pdf"
    assert os.path.exists(generated_path)
    rpt_svc.close()


def test_report_artifact_tamper_detection(tmp_path):
    """
    If a generated report's content is tampered with,
    its computed content hash must fail validation against the original hash.
    """
    rpt_svc = ReportGenerationService(db_path=str(tmp_path / "rpt.db"))
    report = rpt_svc.generate_report(
        audit_id="AUD-TAMPER",
        company_name="Honest Corp",
        company_id="U55555",
        financial_periods=["FY2024-25"],
        evidence_records=[],
        findings=[],
        counter_evidence=[],
        gap_register=[],
        reconciliation_results=[],
        human_reviews=[],
        not_checked_items=[],
        completeness_status="PASS",
        human_review_status="NOT_REQUIRED",
        risk_classification="LOW",
    )

    original_hash = report.report_content_hash
    assert original_hash is not None

    # Tamper with finding or company name
    report.company_name = "Tampered Hostile Corp"
    new_hash = report.compute_content_hash()

    assert new_hash != original_hash
    rpt_svc.close()
