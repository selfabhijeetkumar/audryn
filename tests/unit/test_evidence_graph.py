"""
AUDRYN Phase 5 — Evidence Graph Service Tests.

Covers:
- Node creation, retrieval, and schema typing
- Relationship creation, validation, and retrieval
- Self-referencing relationship prevention
- Strict cross-audit boundary isolation enforcement
- Foreign key referential integrity
- Lineage traversal: Finding -> Calculations -> Transactions -> Source Locations -> Documents
- Graph statistics aggregation
"""
import pytest
from backend.models.evidence_graph import (
    NodeType,
    RelationshipType,
    GraphNode,
    GraphRelationship,
)
from backend.services.evidence_graph_service import EvidenceGraphService


@pytest.fixture
def graph_service(tmp_path):
    db_file = str(tmp_path / "test_evidence_graph.db")
    service = EvidenceGraphService(db_path=db_file)
    yield service
    service.close()


def test_add_and_retrieve_nodes(graph_service):
    """Verify adding typed nodes and retrieving them by node_id."""
    audit_node = GraphNode(
        node_id="AUD-2024-001",
        audit_id="AUD-2024-001",
        node_type=NodeType.AUDIT,
        label="Apex Industrial Audit FY2024-25",
        properties={"entity": "Apex Industrial Dynamics Pvt Ltd", "year": "FY2024-25"},
    )
    doc_node = GraphNode(
        node_id="EV-DOC-TB-2024",
        audit_id="AUD-2024-001",
        node_type=NodeType.EVIDENCE_DOCUMENT,
        label="Trial Balance FY24-25",
        properties={"sha256": "abcdef1234567890", "type": "TRIAL_BALANCE"},
    )

    graph_service.add_node(audit_node)
    graph_service.add_node(doc_node)

    retrieved = graph_service.get_node("EV-DOC-TB-2024")
    assert retrieved is not None
    assert retrieved.node_type == NodeType.EVIDENCE_DOCUMENT
    assert retrieved.properties["type"] == "TRIAL_BALANCE"


def test_add_and_query_relationships(graph_service):
    """Verify linking nodes with typed relationships and querying directions."""
    audit_id = "AUD-2024-001"
    n1 = GraphNode(node_id="AUD-01", audit_id=audit_id, node_type=NodeType.AUDIT, label="Audit")
    n2 = GraphNode(node_id="DOC-01", audit_id=audit_id, node_type=NodeType.EVIDENCE_DOCUMENT, label="Doc")
    graph_service.add_node(n1)
    graph_service.add_node(n2)

    rel = GraphRelationship(
        relationship_id="REL-01",
        audit_id=audit_id,
        source_id="AUD-01",
        target_id="DOC-01",
        relationship_type=RelationshipType.AUDIT_CONTAINS_DOCUMENT,
        provenance="Ingestion Manifest",
    )
    graph_service.add_relationship(rel)

    # Query outgoing
    outgoing = graph_service.get_outgoing_relationships("AUD-01")
    assert len(outgoing) == 1
    assert outgoing[0].relationship_type == RelationshipType.AUDIT_CONTAINS_DOCUMENT
    assert outgoing[0].target_id == "DOC-01"

    # Query incoming
    incoming = graph_service.get_incoming_relationships("DOC-01")
    assert len(incoming) == 1
    assert incoming[0].source_id == "AUD-01"


def test_self_referencing_relationship_rejected(graph_service):
    """Evidence graph must forbid self-loops."""
    audit_id = "AUD-2024-001"
    n = GraphNode(node_id="NODE-X", audit_id=audit_id, node_type=NodeType.ENTITY, label="Self")
    graph_service.add_node(n)

    with pytest.raises(ValueError, match="Self-referencing relationships are prohibited"):
        GraphRelationship(
            relationship_id="REL-SELF",
            audit_id=audit_id,
            source_id="NODE-X",
            target_id="NODE-X",
            relationship_type=RelationshipType.TRANSACTION_MATCHES_TRANSACTION,
        )


def test_cross_audit_isolation_enforced(graph_service):
    """Relationships cannot link nodes across disparate audit_ids."""
    # Node in Audit A
    n_a = GraphNode(node_id="AUD-A-NODE", audit_id="AUD-CORP-A", node_type=NodeType.EVIDENCE_DOCUMENT, label="Doc A")
    # Node in Audit B
    n_b = GraphNode(node_id="AUD-B-NODE", audit_id="AUD-CORP-B", node_type=NodeType.EVIDENCE_DOCUMENT, label="Doc B")
    graph_service.add_node(n_a)
    graph_service.add_node(n_b)

    # Attempt to link Node A to Node B within Audit A context
    rel = GraphRelationship(
        relationship_id="REL-LEAK",
        audit_id="AUD-CORP-A",
        source_id="AUD-A-NODE",
        target_id="AUD-B-NODE",
        relationship_type=RelationshipType.DOCUMENT_SUPPORTS_FINDING,
    )

    with pytest.raises(ValueError, match="Audit Isolation Violation"):
        graph_service.add_relationship(rel)


def test_missing_node_referential_integrity(graph_service):
    """Adding relationship to a non-existent node must raise ValueError."""
    audit_id = "AUD-2024-001"
    n1 = GraphNode(node_id="EXISTING", audit_id=audit_id, node_type=NodeType.ENTITY, label="Exists")
    graph_service.add_node(n1)

    rel = GraphRelationship(
        relationship_id="REL-ORPHAN",
        audit_id=audit_id,
        source_id="EXISTING",
        target_id="NON_EXISTENT",
        relationship_type=RelationshipType.TRANSACTION_BELONGS_TO_ENTITY,
    )

    with pytest.raises(ValueError, match="does not exist in Evidence Graph"):
        graph_service.add_relationship(rel)


def test_trace_finding_to_source_lineage(graph_service):
    """
    Test full lineage tracing:
    Document -> Location -> Fact -> Transaction -> Calculation -> Finding
    """
    audit_id = "AUD-LINEAGE-01"

    # 1. Document
    doc = GraphNode(node_id="DOC-INVOICE-01", audit_id=audit_id, node_type=NodeType.EVIDENCE_DOCUMENT, label="Invoice #9901")
    # 2. Source Location
    loc = GraphNode(
        node_id="LOC-PAGE-1-ROW-4",
        audit_id=audit_id,
        node_type=NodeType.SOURCE_LOCATION,
        label="Page 1 Coordinates",
        properties={"page": 1, "row": 4, "snippet": "Vendor Taxable Amount ₹ 5,00,000.00"},
    )
    # 3. Fact
    fact = GraphNode(node_id="FACT-01", audit_id=audit_id, node_type=NodeType.EXTRACTED_FACT, label="Billed Amount Fact")
    # 4. Transaction
    tx = GraphNode(
        node_id="TX-INV-9901",
        audit_id=audit_id,
        node_type=NodeType.FINANCIAL_TRANSACTION,
        label="Purchase Invoice",
        properties={"amount": "500000.00", "vendor": "Steel Works Ltd"},
    )
    # 5. Calculation
    calc = GraphNode(
        node_id="CALC-VAR-01",
        audit_id=audit_id,
        node_type=NodeType.FINANCIAL_CALCULATION,
        label="GL Tie-Out Variance",
        properties={"variance": "500000.00", "status": "UNRECONCILED"},
    )
    # 6. Finding
    finding = GraphNode(
        node_id="FIND-ANOM-01",
        audit_id=audit_id,
        node_type=NodeType.AUDIT_FINDING,
        label="Unrecorded Liability Anomaly",
        properties={"title": "Unrecorded purchase invoice in general ledger"},
    )
    # 7. Counter Evidence
    ce = GraphNode(
        node_id="CE-01",
        audit_id=audit_id,
        node_type=NodeType.COUNTER_EVIDENCE,
        label="Counter Evidence Challenge",
        properties={"verdict": "CONTRADICTED", "rationale": "Credit note #CN-12 issued on 02/04/2024"},
    )
    # 8. Review Decision
    rev = GraphNode(
        node_id="REV-01",
        audit_id=audit_id,
        node_type=NodeType.REVIEW_DECISION,
        label="Human Review Decision",
        properties={"decision": "APPROVED", "reviewer": "Senior Auditor CA Sharma"},
    )

    for n in [doc, loc, fact, tx, calc, finding, ce, rev]:
        graph_service.add_node(n)

    # Add edges
    graph_service.add_relationship(GraphRelationship(
        relationship_id="R1", audit_id=audit_id, source_id="DOC-INVOICE-01", target_id="LOC-PAGE-1-ROW-4",
        relationship_type=RelationshipType.DOCUMENT_CONTAINS_SOURCE_LOCATION,
    ))
    graph_service.add_relationship(GraphRelationship(
        relationship_id="R2", audit_id=audit_id, source_id="LOC-PAGE-1-ROW-4", target_id="FACT-01",
        relationship_type=RelationshipType.SOURCE_LOCATION_SUPPORTS_FACT,
    ))
    graph_service.add_relationship(GraphRelationship(
        relationship_id="R3", audit_id=audit_id, source_id="FACT-01", target_id="TX-INV-9901",
        relationship_type=RelationshipType.FACT_RELATES_TO_TRANSACTION,
    ))
    graph_service.add_relationship(GraphRelationship(
        relationship_id="R4", audit_id=audit_id, source_id="TX-INV-9901", target_id="CALC-VAR-01",
        relationship_type=RelationshipType.TRANSACTION_SUPPORTS_CALCULATION,
    ))
    graph_service.add_relationship(GraphRelationship(
        relationship_id="R5", audit_id=audit_id, source_id="CALC-VAR-01", target_id="FIND-ANOM-01",
        relationship_type=RelationshipType.CALCULATION_SUPPORTS_FINDING,
    ))
    graph_service.add_relationship(GraphRelationship(
        relationship_id="R6", audit_id=audit_id, source_id="FIND-ANOM-01", target_id="CE-01",
        relationship_type=RelationshipType.FINDING_HAS_COUNTER_EVIDENCE,
    ))
    graph_service.add_relationship(GraphRelationship(
        relationship_id="R7", audit_id=audit_id, source_id="FIND-ANOM-01", target_id="REV-01",
        relationship_type=RelationshipType.FINDING_HAS_REVIEW_DECISION,
    ))

    # Reconstruct lineage
    chain = graph_service.trace_finding_to_source("FIND-ANOM-01")
    assert chain.is_complete is True
    assert "DOC-INVOICE-01" in chain.document_ids
    assert len(chain.source_locations) == 1
    assert chain.source_locations[0]["page"] == 1
    assert len(chain.transactions) == 1
    assert chain.transactions[0]["amount"] == "500000.00"
    assert len(chain.calculations) == 1
    assert len(chain.counter_evidence) == 1
    assert chain.counter_evidence[0]["verdict"] == "CONTRADICTED"
    assert len(chain.review_decisions) == 1
    assert chain.review_decisions[0]["decision"] == "APPROVED"
