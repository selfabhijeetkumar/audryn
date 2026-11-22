"""
AUDRYN Phase 5 — Financial Linkage Service Tests.

Covers:
- Invoice to ledger deterministic matching
- Invoice to ledger discrepancy detection
- Credit note reversal linking
- Bank reconciliation tie-out with timing differences
- Tax calculation to rulebook version linking
- Finding to counter-evidence linking
- Finding to human review decision linking
"""
import pytest
from decimal import Decimal
from backend.models.evidence_graph import NodeType, RelationshipType, GraphNode
from backend.services.evidence_graph_service import EvidenceGraphService
from backend.services.financial_linkage_service import FinancialLinkageService


@pytest.fixture
def services(tmp_path):
    db_file = str(tmp_path / "test_linkage.db")
    graph = EvidenceGraphService(db_path=db_file)
    linkage = FinancialLinkageService(graph_service=graph)
    yield graph, linkage
    graph.close()


def _add_tx_pair(graph, audit_id, id_a, label_a, id_b, label_b):
    graph.add_node(GraphNode(node_id=id_a, audit_id=audit_id, node_type=NodeType.FINANCIAL_TRANSACTION, label=label_a))
    graph.add_node(GraphNode(node_id=id_b, audit_id=audit_id, node_type=NodeType.FINANCIAL_TRANSACTION, label=label_b))


def test_invoice_to_ledger_exact_match(services):
    """Matching voucher number and amount creates MATCHES relationship."""
    graph, linkage = services
    audit_id = "AUD-LINK-01"
    _add_tx_pair(graph, audit_id, "INV-001", "Vendor Invoice", "GL-001", "GL Journal")

    rel = linkage.link_invoice_to_ledger(
        audit_id=audit_id,
        invoice_node_id="INV-001", invoice_number="INV-001", invoice_amount=Decimal("500000.00"),
        ledger_entry_id="GL-001", ledger_voucher_id="INV-001", ledger_amount=Decimal("500000.00"),
    )
    assert rel.relationship_type == RelationshipType.TRANSACTION_MATCHES_TRANSACTION
    assert rel.properties["is_exact_match"] is True
    assert rel.properties["variance"] == "0.00"


def test_invoice_to_ledger_discrepancy(services):
    """Mismatched amount creates CONTRADICTS relationship."""
    graph, linkage = services
    audit_id = "AUD-LINK-02"
    _add_tx_pair(graph, audit_id, "INV-002", "Invoice", "GL-002", "Ledger")

    rel = linkage.link_invoice_to_ledger(
        audit_id=audit_id,
        invoice_node_id="INV-002", invoice_number="INV-X", invoice_amount=Decimal("500000.00"),
        ledger_entry_id="GL-002", ledger_voucher_id="INV-X", ledger_amount=Decimal("480000.00"),
    )
    assert rel.relationship_type == RelationshipType.TRANSACTION_CONTRADICTS_TRANSACTION
    assert rel.properties["variance"] == "20000.00"
    assert rel.validation_status == "DISCREPANCY_FLAGGED"


def test_credit_note_reversal_link(services):
    """Credit note linked to original invoice preserves commercial context."""
    graph, linkage = services
    audit_id = "AUD-LINK-03"
    _add_tx_pair(graph, audit_id, "CN-100", "Credit Note", "INV-100", "Original Invoice")

    rel = linkage.link_credit_note_reversal(
        audit_id=audit_id,
        credit_note_node_id="CN-100", credit_note_num="CN-100",
        original_invoice_node_id="INV-100", original_invoice_num="INV-100",
        reversal_amount=Decimal("150000.00"), invoice_amount=Decimal("500000.00"),
    )
    assert rel.properties["is_full_reversal"] is False
    assert rel.properties["is_valid_reversal"] is True
    assert rel.validation_status == "VALIDATED"


def test_bank_reconciliation_timing_difference(services):
    """Bank clearance within 5 days is classified as timing difference."""
    graph, linkage = services
    audit_id = "AUD-LINK-04"
    _add_tx_pair(graph, audit_id, "BANK-TX-01", "Bank Payment", "LED-TX-01", "Ledger Payment")

    rel = linkage.link_bank_transaction_to_ledger(
        audit_id=audit_id,
        bank_tx_node_id="BANK-TX-01", bank_ref="CHQ-9001", bank_date="2024-04-02",
        bank_amount=Decimal("250000.00"),
        ledger_tx_node_id="LED-TX-01", ledger_ref="JV-9001", ledger_date="2024-03-30",
        ledger_amount=Decimal("250000.00"),
    )
    assert rel.relationship_type == RelationshipType.TRANSACTION_MATCHES_TRANSACTION
    assert rel.properties["is_timing_difference"] is True
    assert rel.properties["day_difference"] == 3


def test_calculation_to_tax_rule_link(services):
    """Corporate tax calculation links to versioned rulebook section."""
    graph, linkage = services
    audit_id = "AUD-LINK-05"
    graph.add_node(GraphNode(node_id="CALC-TAX-01", audit_id=audit_id, node_type=NodeType.FINANCIAL_CALCULATION, label="Corp Tax"))
    graph.add_node(GraphNode(node_id="RULE-115BAA", audit_id=audit_id, node_type=NodeType.TAX_RULE, label="Section 115BAA"))

    rel = linkage.link_calculation_to_tax_rule(
        audit_id=audit_id,
        calc_node_id="CALC-TAX-01", tax_rule_node_id="RULE-115BAA",
        section_reference="Section 115BAA", effective_rate="25.168%",
        rulebook_version="Income-tax Act, 1961",
    )
    assert rel.relationship_type == RelationshipType.CALCULATION_USES_RULE
    assert rel.properties["rulebook_version"] == "Income-tax Act, 1961"


def test_finding_to_counter_evidence_link(services):
    """Finding linked to counter-evidence challenge preserves verdict."""
    graph, linkage = services
    audit_id = "AUD-LINK-06"
    graph.add_node(GraphNode(node_id="FIND-01", audit_id=audit_id, node_type=NodeType.AUDIT_FINDING, label="Finding"))
    graph.add_node(GraphNode(node_id="CE-01", audit_id=audit_id, node_type=NodeType.COUNTER_EVIDENCE, label="Challenge"))

    rel = linkage.link_finding_to_counter_evidence(
        audit_id=audit_id,
        finding_node_id="FIND-01", counter_evidence_node_id="CE-01",
        challenge_id="CHG-001", verdict="CONTRADICTED",
        rationale="Credit note CN-100 explains the variance.",
    )
    assert rel.properties["verdict"] == "CONTRADICTED"


def test_finding_to_human_review_link(services):
    """Finding linked to human review decision preserves reviewer and decision."""
    graph, linkage = services
    audit_id = "AUD-LINK-07"
    graph.add_node(GraphNode(node_id="FIND-02", audit_id=audit_id, node_type=NodeType.AUDIT_FINDING, label="Finding"))
    graph.add_node(GraphNode(node_id="REV-02", audit_id=audit_id, node_type=NodeType.REVIEW_DECISION, label="Review"))

    rel = linkage.link_finding_to_human_review(
        audit_id=audit_id,
        finding_node_id="FIND-02", review_decision_node_id="REV-02",
        decision="APPROVED", reviewer_name="CA Sharma", comments="Verified against bank statement.",
    )
    assert rel.properties["decision"] == "APPROVED"
    assert rel.properties["reviewer"] == "CA Sharma"
