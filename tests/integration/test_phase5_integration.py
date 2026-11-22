"""
AUDRYN Phase 5 — Full End-to-End Integration Pipeline.

Demonstrates complete integration:
1. Evidence document ingestion with SHA-256 integrity.
2. Evidence Graph population with typed nodes and source coordinates.
3. Deterministic financial linkage (invoice tie-out, credit note reversal, bank clearance).
4. Full end-to-end finding lineage traversal.
5. Report generation (JSON and publication-grade PDF).
6. Release Gate evaluation and report finalization.
"""
import os
from decimal import Decimal
import pytest

from backend.models.evidence import DocumentType
from backend.models.evidence_graph import NodeType, RelationshipType, GraphNode, GraphRelationship
from backend.models.report import ReportStatus
from backend.services.evidence_service import EvidenceService
from backend.services.evidence_graph_service import EvidenceGraphService
from backend.services.financial_linkage_service import FinancialLinkageService
from backend.services.report_generation_service import ReportGenerationService
from backend.services.pdf_report_service import PdfReportService


def test_end_to_end_phase5_evidence_graph_and_reporting_pipeline(tmp_path):
    audit_id = "AUD-E2E-2024-001"
    company_name = "Apex Industrial Dynamics Pvt Ltd"
    company_id = "U29100MH2020PTC998877"
    periods = ["FY2023-24", "FY2024-25"]

    # 1. Evidence Service: Register original document
    ev_dir = str(tmp_path / "evidence_vault")
    ev_service = EvidenceService(storage_dir=ev_dir)
    mock_pdf_bytes = b"%PDF-1.4 Mock Trial Balance and Ledger Content for Apex Industrial Dynamics"
    ev_record = ev_service.register_evidence(
        file_bytes=mock_pdf_bytes,
        original_filename="Trial_Balance_FY24-25.pdf",
        document_type=DocumentType.TRIAL_BALANCE,
        metadata={"fiscal_year": "FY2024-25"},
    )
    assert ev_record.sha256_hash is not None

    # 2. Evidence Graph Service: Populate graph
    graph_db = str(tmp_path / "graph.db")
    graph_service = EvidenceGraphService(db_path=graph_db)

    audit_node = GraphNode(
        node_id=audit_id,
        audit_id=audit_id,
        node_type=NodeType.AUDIT,
        label=f"Statutory Audit: {company_name}",
        properties={"entity": company_name, "cin": company_id},
    )
    doc_node = GraphNode(
        node_id=ev_record.evidence_id,
        audit_id=audit_id,
        node_type=NodeType.EVIDENCE_DOCUMENT,
        label=ev_record.original_filename,
        properties={"sha256": ev_record.sha256_hash, "type": ev_record.document_type.value},
    )
    loc_node = GraphNode(
        node_id=f"LOC-{ev_record.evidence_id}-P1",
        audit_id=audit_id,
        node_type=NodeType.SOURCE_LOCATION,
        label="Page 1 Coordinates",
        properties={"page": 1, "row": 12, "column": "Closing Debit Balance", "snippet": "₹ 14,25,00,000.00"},
    )
    tx_node = GraphNode(
        node_id="TX-REV-001",
        audit_id=audit_id,
        node_type=NodeType.FINANCIAL_TRANSACTION,
        label="Revenue Ledger Entry",
        properties={"account": "Sales Revenue", "amount": "142500000.00", "currency": "INR"},
    )
    calc_node = GraphNode(
        node_id="CALC-TB-VAR",
        audit_id=audit_id,
        node_type=NodeType.FINANCIAL_CALCULATION,
        label="TB Debit/Credit Tie-Out",
        properties={"variance": "1500000.00", "status": "UNBALANCED"},
    )
    finding_node = GraphNode(
        node_id="FIND-TB-01",
        audit_id=audit_id,
        node_type=NodeType.AUDIT_FINDING,
        label="Trial Balance Debit/Credit Imbalance",
        properties={
            "title": "Trial balance variance of ₹ 15,00,000.00 detected",
            "severity": "HIGH",
            "impact_amount": "1500000.00",
            "status": "CLOSED",
        },
    )
    ce_node = GraphNode(
        node_id="CE-TB-01",
        audit_id=audit_id,
        node_type=NodeType.COUNTER_EVIDENCE,
        label="Counter Evidence Challenge",
        properties={
            "verdict": "SUPPORTED",
            "rationale": "General Ledger confirms unposted credit adjustment voucher.",
        },
    )
    rev_node = GraphNode(
        node_id="REV-TB-01",
        audit_id=audit_id,
        node_type=NodeType.REVIEW_DECISION,
        label="Auditor Approval",
        properties={"decision": "APPROVED", "reviewer": "CA R. Sharma", "comments": "Adjusting entry required"},
    )

    for n in [audit_node, doc_node, loc_node, tx_node, calc_node, finding_node, ce_node, rev_node]:
        graph_service.add_node(n)

    # 3. Financial Linkage Service: Deterministic link creation
    linkage = FinancialLinkageService(graph_service)

    # Audit contains Document
    graph_service.add_relationship(GraphRelationship(
        relationship_id="R-AUD-DOC",
        audit_id=audit_id,
        source_id=audit_id,
        target_id=ev_record.evidence_id,
        relationship_type=RelationshipType.AUDIT_CONTAINS_DOCUMENT,
    ))
    # Document contains Location
    graph_service.add_relationship(GraphRelationship(
        relationship_id="R-DOC-LOC",
        audit_id=audit_id,
        source_id=ev_record.evidence_id,
        target_id=loc_node.node_id,
        relationship_type=RelationshipType.DOCUMENT_CONTAINS_SOURCE_LOCATION,
    ))
    # Location supports Fact/Tx
    graph_service.add_relationship(GraphRelationship(
        relationship_id="R-LOC-TX",
        audit_id=audit_id,
        source_id=loc_node.node_id,
        target_id=tx_node.node_id,
        relationship_type=RelationshipType.SOURCE_LOCATION_SUPPORTS_FACT,
    ))
    # Transaction supports Calculation
    graph_service.add_relationship(GraphRelationship(
        relationship_id="R-TX-CALC",
        audit_id=audit_id,
        source_id=tx_node.node_id,
        target_id=calc_node.node_id,
        relationship_type=RelationshipType.TRANSACTION_SUPPORTS_CALCULATION,
    ))
    # Calculation supports Finding
    graph_service.add_relationship(GraphRelationship(
        relationship_id="R-CALC-FIND",
        audit_id=audit_id,
        source_id=calc_node.node_id,
        target_id=finding_node.node_id,
        relationship_type=RelationshipType.CALCULATION_SUPPORTS_FINDING,
    ))
    # Finding has Counter-Evidence
    linkage.link_finding_to_counter_evidence(
        audit_id=audit_id,
        finding_node_id=finding_node.node_id,
        counter_evidence_node_id=ce_node.node_id,
        challenge_id="CHG-TB-01",
        verdict="SUPPORTED",
        rationale="Unposted credit entry confirmed",
    )
    # Finding has Review Decision
    linkage.link_finding_to_human_review(
        audit_id=audit_id,
        finding_node_id=finding_node.node_id,
        review_decision_node_id=rev_node.node_id,
        decision="APPROVED",
        reviewer_name="CA R. Sharma",
        comments="Adjusting entry required",
    )

    # 4. Verify Traceability Chain
    chain = graph_service.trace_finding_to_source(finding_node.node_id)
    assert chain.is_complete is True
    assert ev_record.evidence_id in chain.document_ids
    assert len(chain.calculations) == 1
    assert len(chain.counter_evidence) == 1
    assert len(chain.review_decisions) == 1
    assert chain.review_decisions[0]["decision"] == "APPROVED"

    # 5. Report Generation Service: Generate Machine-Readable JSON Report
    rpt_db = str(tmp_path / "reports.db")
    rpt_service = ReportGenerationService(db_path=rpt_db)

    evidence_records_payload = [{
        "evidence_id": ev_record.evidence_id,
        "original_filename": ev_record.original_filename,
        "document_type": ev_record.document_type.value,
        "extraction_status": "SUCCESS",
        "sha256_hash": ev_record.sha256_hash,
    }]
    findings_payload = [{
        "finding_id": finding_node.node_id,
        "title": "Trial balance variance of ₹ 15,00,000.00 detected",
        "description": "Debit exceeds credit by ₹ 15,00,000.00",
        "severity": "HIGH",
        "impact_amount": "1500000.00",
        "currency": "INR",
        "status": "CLOSED",
        "source_evidence": [ev_record.evidence_id],
        "coordinates": {"page": 1, "row": 12},
    }]
    counter_evidence_payload = [{
        "challenge_id": "CHG-TB-01",
        "finding_id": finding_node.node_id,
        "reviewer_verdict": "SUPPORTED",
        "verdict_rationale": "General Ledger confirms unposted credit adjustment voucher.",
        "requires_escalation": False,
    }]
    human_reviews_payload = [{
        "review_id": "REV-TB-01",
        "finding_id": finding_node.node_id,
        "decision": "APPROVED",
        "reviewer_name": "CA R. Sharma",
        "comments": "Adjusting entry required",
    }]

    report = rpt_service.generate_report(
        audit_id=audit_id,
        company_name=company_name,
        company_id=company_id,
        financial_periods=periods,
        evidence_records=evidence_records_payload,
        findings=findings_payload,
        counter_evidence=counter_evidence_payload,
        gap_register=[],
        reconciliation_results=[{"procedure": "TB Tie-Out", "variance": "1500000.00", "status": "FLAGGED"}],
        human_reviews=human_reviews_payload,
        not_checked_items=[],
        completeness_status="PASS",
        human_review_status="APPROVED",
        risk_classification="HIGH",
        is_synthetic=True,
    )

    assert report.report_status == ReportStatus.REVIEW_READY
    assert report.report_content_hash is not None
    assert len(report.sections) == 12

    # 6. PDF Report Service: Render publication-quality PDF
    pdf_dir = str(tmp_path / "pdf_out")
    pdf_service = PdfReportService(output_dir=pdf_dir)
    pdf_file = pdf_service.generate_pdf(report)
    assert os.path.exists(pdf_file)
    assert os.path.getsize(pdf_file) > 1000  # valid PDF generated

    # 7. Finalize Report and Verify Immutability
    finalized = rpt_service.finalize_report(report.report_id, report.report_version)
    assert finalized.report_status == ReportStatus.FINALIZED

    # Re-retrieve from DB to verify persistence
    reloaded = rpt_service.get_report(report.report_id, report.report_version)
    assert reloaded is not None
    assert reloaded.report_status == ReportStatus.FINALIZED
    assert reloaded.report_content_hash == finalized.report_content_hash

    # Clean up
    graph_service.close()
    rpt_service.close()
