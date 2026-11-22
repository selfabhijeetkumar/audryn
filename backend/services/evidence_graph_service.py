"""
AUDRYN Evidence Graph Service.

Provides ACID-compliant relational persistence, traversal, referential integrity,
and strict cross-audit isolation for the AUDRYN Evidence Graph.
Uses standard library sqlite3 in WAL mode with mutex locking.
"""
import os
import json
import sqlite3
import threading
from typing import Dict, Any, List, Optional, Tuple
from backend.models.evidence_graph import (
    NodeType,
    RelationshipType,
    GraphNode,
    GraphRelationship,
    TraceabilityChain,
)


class EvidenceGraphService:
    """
    Operational Evidence Graph service managing graph nodes, relationships,
    and traversal queries for statutory audit evidence chains.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self.db_path = db_path or os.path.join("data", "evidence_graph", "audryn_evidence_graph.db")
        self.timeout = timeout
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._conn = sqlite3.connect(
            self.db_path,
            timeout=self.timeout,
            check_same_thread=False,
            isolation_level=None,  # Explicit transaction management
        )
        self._configure_database()

    def _configure_database(self):
        """Configure SQLite pragmas, tables, and performance indexes."""
        with self._lock, self._conn:
            self._conn.execute("PRAGMA journal_mode = WAL;")
            self._conn.execute("PRAGMA synchronous = NORMAL;")
            self._conn.execute("PRAGMA foreign_keys = ON;")
            self._conn.execute("PRAGMA busy_timeout = 5000;")

            self._conn.execute("""
            CREATE TABLE IF NOT EXISTS graph_nodes (
                node_id TEXT PRIMARY KEY,
                audit_id TEXT NOT NULL,
                node_type TEXT NOT NULL,
                label TEXT NOT NULL,
                properties_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """)

            self._conn.execute("""
            CREATE TABLE IF NOT EXISTS graph_relationships (
                relationship_id TEXT PRIMARY KEY,
                audit_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                rel_type TEXT NOT NULL,
                provenance TEXT,
                properties_json TEXT NOT NULL,
                validation_status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES graph_nodes(node_id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES graph_nodes(node_id) ON DELETE CASCADE
            );
            """)

            self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_nodes_audit 
            ON graph_nodes(audit_id, node_type);
            """)

            self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rel_audit 
            ON graph_relationships(audit_id, rel_type);
            """)

            self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rel_source 
            ON graph_relationships(source_id);
            """)

            self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rel_target 
            ON graph_relationships(target_id);
            """)

    def add_node(self, node: GraphNode) -> GraphNode:
        """Adds or updates a node in the Evidence Graph."""
        with self._lock, self._conn:
            self._conn.execute("""
            INSERT OR REPLACE INTO graph_nodes (node_id, audit_id, node_type, label, properties_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (
                node.node_id,
                node.audit_id,
                node.node_type.value,
                node.label,
                json.dumps(node.properties),
                node.created_at,
            ))
        return node

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Retrieves a node by its unique node_id."""
        with self._lock:
            cursor = self._conn.execute("""
            SELECT node_id, audit_id, node_type, label, properties_json, created_at
            FROM graph_nodes WHERE node_id = ?;
            """, (node_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return GraphNode(
                node_id=row[0],
                audit_id=row[1],
                node_type=NodeType(row[2]),
                label=row[3],
                properties=json.loads(row[4]),
                created_at=row[5],
            )

    def add_relationship(self, rel: GraphRelationship) -> GraphRelationship:
        """
        Adds a relationship between two existing nodes.
        Strictly enforces audit isolation: source and target must belong to rel.audit_id.
        """
        with self._lock, self._conn:
            # 1. Verify source node exists and check audit_id
            s_cursor = self._conn.execute("SELECT audit_id FROM graph_nodes WHERE node_id = ?;", (rel.source_id,))
            s_row = s_cursor.fetchone()
            if not s_row:
                raise ValueError(f"Source node '{rel.source_id}' does not exist in Evidence Graph.")
            if s_row[0] != rel.audit_id:
                raise ValueError(
                    f"Audit Isolation Violation: Source node belongs to audit '{s_row[0]}', "
                    f"cannot create relationship in audit '{rel.audit_id}'."
                )

            # 2. Verify target node exists and check audit_id
            t_cursor = self._conn.execute("SELECT audit_id FROM graph_nodes WHERE node_id = ?;", (rel.target_id,))
            t_row = t_cursor.fetchone()
            if not t_row:
                raise ValueError(f"Target node '{rel.target_id}' does not exist in Evidence Graph.")
            if t_row[0] != rel.audit_id:
                raise ValueError(
                    f"Audit Isolation Violation: Target node belongs to audit '{t_row[0]}', "
                    f"cannot create cross-audit relationship with audit '{rel.audit_id}'."
                )

            # 3. Insert or replace relationship
            self._conn.execute("""
            INSERT OR REPLACE INTO graph_relationships (
                relationship_id, audit_id, source_id, target_id, rel_type, provenance, properties_json, validation_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                rel.relationship_id,
                rel.audit_id,
                rel.source_id,
                rel.target_id,
                rel.relationship_type.value,
                rel.provenance,
                json.dumps(rel.properties),
                rel.validation_status,
                rel.created_at,
            ))
        return rel

    def get_relationship(self, relationship_id: str) -> Optional[GraphRelationship]:
        """Retrieves a relationship by ID."""
        with self._lock:
            cursor = self._conn.execute("""
            SELECT relationship_id, audit_id, source_id, target_id, rel_type, provenance, properties_json, validation_status, created_at
            FROM graph_relationships WHERE relationship_id = ?;
            """, (relationship_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return GraphRelationship(
                relationship_id=row[0],
                audit_id=row[1],
                source_id=row[2],
                target_id=row[3],
                relationship_type=RelationshipType(row[4]),
                provenance=row[5],
                properties=json.loads(row[6]),
                validation_status=row[7],
                created_at=row[8],
            )

    def get_outgoing_relationships(
        self, node_id: str, rel_type: Optional[RelationshipType] = None
    ) -> List[GraphRelationship]:
        """Finds outgoing relationships originating from node_id."""
        with self._lock:
            if rel_type:
                cursor = self._conn.execute("""
                SELECT relationship_id, audit_id, source_id, target_id, rel_type, provenance, properties_json, validation_status, created_at
                FROM graph_relationships WHERE source_id = ? AND rel_type = ?;
                """, (node_id, rel_type.value))
            else:
                cursor = self._conn.execute("""
                SELECT relationship_id, audit_id, source_id, target_id, rel_type, provenance, properties_json, validation_status, created_at
                FROM graph_relationships WHERE source_id = ?;
                """, (node_id,))
            rows = cursor.fetchall()
            return [
                GraphRelationship(
                    relationship_id=r[0],
                    audit_id=r[1],
                    source_id=r[2],
                    target_id=r[3],
                    relationship_type=RelationshipType(r[4]),
                    provenance=r[5],
                    properties=json.loads(r[6]),
                    validation_status=r[7],
                    created_at=r[8],
                )
                for r in rows
            ]

    def get_incoming_relationships(
        self, node_id: str, rel_type: Optional[RelationshipType] = None
    ) -> List[GraphRelationship]:
        """Finds incoming relationships pointing to node_id."""
        with self._lock:
            if rel_type:
                cursor = self._conn.execute("""
                SELECT relationship_id, audit_id, source_id, target_id, rel_type, provenance, properties_json, validation_status, created_at
                FROM graph_relationships WHERE target_id = ? AND rel_type = ?;
                """, (node_id, rel_type.value))
            else:
                cursor = self._conn.execute("""
                SELECT relationship_id, audit_id, source_id, target_id, rel_type, provenance, properties_json, validation_status, created_at
                FROM graph_relationships WHERE target_id = ?;
                """, (node_id,))
            rows = cursor.fetchall()
            return [
                GraphRelationship(
                    relationship_id=r[0],
                    audit_id=r[1],
                    source_id=r[2],
                    target_id=r[3],
                    relationship_type=RelationshipType(r[4]),
                    provenance=r[5],
                    properties=json.loads(r[6]),
                    validation_status=r[7],
                    created_at=r[8],
                )
                for r in rows
            ]

    def get_nodes_by_type(self, audit_id: str, node_type: NodeType) -> List[GraphNode]:
        """Lists all nodes of a specific type for an audit."""
        with self._lock:
            cursor = self._conn.execute("""
            SELECT node_id, audit_id, node_type, label, properties_json, created_at
            FROM graph_nodes WHERE audit_id = ? AND node_type = ?;
            """, (audit_id, node_type.value))
            return [
                GraphNode(
                    node_id=r[0],
                    audit_id=r[1],
                    node_type=NodeType(r[2]),
                    label=r[3],
                    properties=json.loads(r[4]),
                    created_at=r[5],
                )
                for r in cursor.fetchall()
            ]

    def trace_finding_to_source(self, finding_id: str) -> TraceabilityChain:
        """
        Reconstructs the full end-to-end evidence lineage for an audit finding:
        Finding -> Calculations -> Transactions -> SourceLocations -> Documents.
        Also attaches CounterEvidence and ReviewDecisions.
        """
        finding_node = self.get_node(finding_id)
        if not finding_node:
            raise ValueError(f"Finding node '{finding_id}' not found.")

        audit_id = finding_node.audit_id
        chain = TraceabilityChain(audit_id=audit_id, finding_id=finding_id)

        # 1. Counter-Evidence challenges
        ce_rels = self.get_outgoing_relationships(finding_id, RelationshipType.FINDING_HAS_COUNTER_EVIDENCE)
        for r in ce_rels:
            ce_node = self.get_node(r.target_id)
            if ce_node:
                chain.counter_evidence.append(ce_node.properties)

        # 2. Review Decisions
        rev_rels = self.get_outgoing_relationships(finding_id, RelationshipType.FINDING_HAS_REVIEW_DECISION)
        for r in rev_rels:
            rev_node = self.get_node(r.target_id)
            if rev_node:
                chain.review_decisions.append(rev_node.properties)

        # 3. Direct document support / contradiction
        doc_sup = self.get_incoming_relationships(finding_id, RelationshipType.DOCUMENT_SUPPORTS_FINDING)
        doc_con = self.get_incoming_relationships(finding_id, RelationshipType.DOCUMENT_CONTRADICTS_FINDING)
        for r in doc_sup + doc_con:
            if r.source_id not in chain.document_ids:
                chain.document_ids.append(r.source_id)

        # 4. Calculations supporting finding
        calc_rels = self.get_incoming_relationships(finding_id, RelationshipType.CALCULATION_SUPPORTS_FINDING)
        for r in calc_rels:
            calc_node = self.get_node(r.source_id)
            if calc_node:
                chain.calculations.append(calc_node.properties)
                # Transactions supporting calculation
                tx_rels = self.get_incoming_relationships(calc_node.node_id, RelationshipType.TRANSACTION_SUPPORTS_CALCULATION)
                for tr in tx_rels:
                    tx_node = self.get_node(tr.source_id)
                    if tx_node:
                        chain.transactions.append(tx_node.properties)
                        # Source locations for transaction via facts
                        self._trace_tx_to_sources(tx_node.node_id, chain)

        # 5. Report sections referencing finding
        sec_rels = self.get_incoming_relationships(finding_id, RelationshipType.REPORT_SECTION_REFERENCES_FINDING)
        for r in sec_rels:
            if r.source_id not in chain.report_sections:
                chain.report_sections.append(r.source_id)

        # Completeness evaluation
        chain.is_complete = bool(chain.document_ids or chain.source_locations or chain.calculations)
        if not chain.document_ids and not chain.source_locations:
            chain.unresolved_links.append("No primary source document or coordinate linked.")
        return chain

    def _trace_tx_to_sources(self, tx_node_id: str, chain: TraceabilityChain):
        """Helper to find source locations and document IDs for a transaction."""
        # 1. Direct location -> transaction link
        direct_loc_rels = self.get_incoming_relationships(tx_node_id, RelationshipType.SOURCE_LOCATION_SUPPORTS_FACT)
        for lr in direct_loc_rels:
            loc_node = self.get_node(lr.source_id)
            if loc_node:
                chain.source_locations.append(loc_node.properties)
                doc_rels = self.get_incoming_relationships(loc_node.node_id, RelationshipType.DOCUMENT_CONTAINS_SOURCE_LOCATION)
                for dr in doc_rels:
                    if dr.source_id not in chain.document_ids:
                        chain.document_ids.append(dr.source_id)

        # 2. Indirect location -> fact -> transaction link
        fact_rels = self.get_incoming_relationships(tx_node_id, RelationshipType.FACT_RELATES_TO_TRANSACTION)
        for fr in fact_rels:
            loc_rels = self.get_incoming_relationships(fr.source_id, RelationshipType.SOURCE_LOCATION_SUPPORTS_FACT)
            for lr in loc_rels:
                loc_node = self.get_node(lr.source_id)
                if loc_node:
                    chain.source_locations.append(loc_node.properties)
                    # Document containing source location
                    doc_rels = self.get_incoming_relationships(loc_node.node_id, RelationshipType.DOCUMENT_CONTAINS_SOURCE_LOCATION)
                    for dr in doc_rels:
                        if dr.source_id not in chain.document_ids:
                            chain.document_ids.append(dr.source_id)

    def get_audit_graph_summary(self, audit_id: str) -> Dict[str, Any]:
        """Provides node and relationship count statistics partitioned by audit_id."""
        with self._lock:
            c1 = self._conn.execute("""
            SELECT node_type, COUNT(*) FROM graph_nodes
            WHERE audit_id = ? GROUP BY node_type;
            """, (audit_id,))
            nodes_by_type = {r[0]: r[1] for r in c1.fetchall()}

            c2 = self._conn.execute("""
            SELECT rel_type, COUNT(*) FROM graph_relationships
            WHERE audit_id = ? GROUP BY rel_type;
            """, (audit_id,))
            rels_by_type = {r[0]: r[1] for r in c2.fetchall()}

            return {
                "audit_id": audit_id,
                "total_nodes": sum(nodes_by_type.values()),
                "total_relationships": sum(rels_by_type.values()),
                "nodes_by_type": nodes_by_type,
                "relationships_by_type": rels_by_type,
            }

    def delete_audit_graph(self, audit_id: str) -> int:
        """Deletes all nodes and cascades relationships for an audit."""
        with self._lock, self._conn:
            cursor = self._conn.execute("DELETE FROM graph_nodes WHERE audit_id = ?;", (audit_id,))
            return cursor.rowcount

    def close(self):
        """Closes the underlying SQLite connection."""
        with self._lock:
            if self._conn:
                self._conn.close()
