# AUDRYN — Evidence Graph Architecture

> **Document Type:** System Architecture Specification  
> **Component:** Evidence Graph Engine  
> **Module:** `backend/services/evidence_graph_service.py` & `backend/models/evidence_graph.py`  
> **Status:** ACTIVE & PRODUCTION-GRADE  
> **Persistence:** Dedicated ACID SQLite Database in WAL Mode (Zero External Graph DB Dependencies)

---

## 1. Architectural Motivation & Principles

In high-stakes statutory financial auditing, audit conclusions cannot exist in isolation. Every material observation, adjusting entry, or risk flag must be deterministically linked back to its root evidence: the original uploaded PDF page, spreadsheet row, general ledger voucher, or bank transaction.

The AUDRYN **Evidence Graph** is not a decorative visual graph. It is an operational, relational, and auditable network of typed nodes and directed relationships that establishes verifiable provenance from source records to final audit report sections.

### Core Architectural Guarantees:
1. **Evidence Before Conclusions:** A finding without verifiable source links is automatically marked unverified.
2. **Deterministic Traversal:** Lineage queries follow typed relationships with strict referential integrity.
3. **Audit Isolation:** Nodes and relationships are partitioned strictly by `audit_id`. Attempting to link records across separate audits raises an immediate `ValueError`.
4. **Relational ACID Storage:** Uses standard library `sqlite3` in WAL mode with reentrant thread mutex locking (`threading.Lock()`), eliminating heavy external dependencies like Neo4j while ensuring 100% compliance with Windows Application Control.
5. **Zero LLM Guesswork:** Graph edges are created exclusively through deterministic tie-outs, voucher matches, or explicit auditor decisions—never through probabilistic LLM hallucination.

---

## 2. Node Model (14 Typed Nodes)

Every entity, document, and artifact in an audit is represented as a typed `GraphNode`:

| Node Type | Purpose & Scope | Example Properties |
|---|---|---|
| **AUDIT** | Root engagement node for a specific company and audit cycle. | `{"entity": "Apex Industrial Dynamics", "year": "FY2024-25"}` |
| **ENTITY** | Company, vendor, customer, bank branch, or related party. | `{"name": "Steel Works Ltd", "gstin": "27AAACS1234A1Z5"}` |
| **EVIDENCE_DOCUMENT** | Uploaded file registered in the SHA-256 Evidence Vault. | `{"sha256": "f834ae98...", "filename": "TB_FY24.pdf"}` |
| **SOURCE_LOCATION** | Exact physical/logical coordinates in the source document. | `{"page": 1, "row": 12, "col": "Debit", "cell": "C12"}` |
| **EXTRACTED_FACT** | Structured data element extracted from a source location. | `{"field": "gross_revenue", "extracted_val": "₹ 14.25 Cr"}` |
| **FINANCIAL_TRANSACTION** | Ledger journal, invoice, bank movement, or credit note. | `{"voucher_id": "JV-9001", "amount": "500000.00", "currency": "INR"}` |
| **FINANCIAL_CALCULATION** | Deterministic math result (variance, tie-out, depreciation).| `{"variance": "1500000.00", "status": "UNBALANCED"}` |
| **TAX_RULE** | Versioned rule from Income-tax Act, 1961 (e.g. 115BAA, Sec 32).| `{"section": "Section 115BAA", "rate": "25.168%"}` |
| **AUDIT_FINDING** | Structured audit observation or anomaly. | `{"finding_id": "FIND-TB-01", "severity": "HIGH"}` |
| **COUNTER_EVIDENCE** | Independent review challenge evaluating the finding. | `{"challenge_id": "CHG-01", "verdict": "CONTRADICTED"}` |
| **GAP** | Audit coverage blind spot identified by GAP RADAR. | `{"gap_id": "GAP-01", "severity": "CRITICAL"}` |
| **REVIEW_DECISION** | Human auditor sign-off, rejection, or escalation. | `{"decision": "APPROVED", "reviewer": "CA R. Sharma"}` |
| **REPORT** | Top-level audit report version container. | `{"report_id": "RPT-001", "version": 1, "status": "FINALIZED"}`|
| **REPORT_SECTION** | Discrete section within the generated report. | `{"section_type": "AUDIT_FINDINGS", "title": "Findings"}` |

---

## 3. Relationship Model (19 Typed Edges)

Relationships in the Evidence Graph are directed, typed, and timestamped:

```
[AUDIT] ──AUDIT_CONTAINS_DOCUMENT──► [EVIDENCE_DOCUMENT]
                                             │
                       DOCUMENT_CONTAINS_SOURCE_LOCATION
                                             ▼
                                     [SOURCE_LOCATION]
                                             │
                               SOURCE_LOCATION_SUPPORTS_FACT
                                             ▼
                                      [EXTRACTED_FACT]
                                             │
                                FACT_RELATES_TO_TRANSACTION
                                             ▼
                                  [FINANCIAL_TRANSACTION]
                                             │
                               TRANSACTION_SUPPORTS_CALCULATION
                                             ▼
                                  [FINANCIAL_CALCULATION] ──CALCULATION_USES_RULE──► [TAX_RULE]
                                             │
                               CALCULATION_SUPPORTS_FINDING
                                             ▼
                                      [AUDIT_FINDING]
                                       │     │     │
               FINDING_HAS_COUNTER_EVIDENCE  │    FINDING_HAS_REVIEW_DECISION
                       │                     │                 │
                       ▼                     │                 ▼
              [COUNTER_EVIDENCE]             │         [REVIEW_DECISION]
                                             ▼
                                      FINDING_HAS_GAP ──► [GAP]
```

### Supported Relationships:
1. `AUDIT_CONTAINS_DOCUMENT`
2. `DOCUMENT_CONTAINS_SOURCE_LOCATION`
3. `SOURCE_LOCATION_SUPPORTS_FACT`
4. `FACT_RELATES_TO_TRANSACTION`
5. `TRANSACTION_BELONGS_TO_ENTITY`
6. `TRANSACTION_MATCHES_TRANSACTION` (Exact tie-outs, credit note reversals)
7. `TRANSACTION_CONTRADICTS_TRANSACTION` (Variance or unrecorded liability flags)
8. `TRANSACTION_SUPPORTS_CALCULATION`
9. `CALCULATION_USES_RULE` (Direct link to statutory tax rule)
10. `CALCULATION_SUPPORTS_FINDING`
11. `DOCUMENT_SUPPORTS_FINDING`
12. `DOCUMENT_CONTRADICTS_FINDING`
13. `FINDING_HAS_COUNTER_EVIDENCE`
14. `FINDING_HAS_GAP`
15. `FINDING_REQUIRES_REVIEW`
16. `FINDING_HAS_REVIEW_DECISION`
17. `REPORT_CONTAINS_SECTION`
18. `REPORT_SECTION_REFERENCES_FINDING`
19. `REPORT_SECTION_CITES_EVIDENCE`

---

## 4. Relational Storage Schema & Concurrency

The Evidence Graph resides in `data/evidence_graph/audryn_evidence_graph.db` using two normalized tables:

```sql
CREATE TABLE IF NOT EXISTS graph_nodes (
    node_id TEXT PRIMARY KEY,
    audit_id TEXT NOT NULL,
    node_type TEXT NOT NULL,
    label TEXT NOT NULL,
    properties_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

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

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_nodes_audit ON graph_nodes(audit_id, node_type);
CREATE INDEX IF NOT EXISTS idx_rel_audit ON graph_relationships(audit_id, rel_type);
CREATE INDEX IF NOT EXISTS idx_rel_source ON graph_relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON graph_relationships(target_id);
```

### Mutex Synchronization & WAL Mode
- `PRAGMA journal_mode = WAL;` enables non-blocking read queries concurrent with write transactions.
- A `threading.Lock()` mutex in `EvidenceGraphService` guarantees thread-safety when multiple worker agents execute queries simultaneously.
- Foreign keys (`PRAGMA foreign_keys = ON;`) prevent orphan relationships and ensure cascade deletion if an audit is pruned.

---

## 5. Lineage Traversal (`trace_finding_to_source`)

The `trace_finding_to_source(finding_id: str)` method reconstructs the entire backward lineage chain:
1. Reaches upstream calculations supporting the finding (`CALCULATION_SUPPORTS_FINDING`).
2. Reaches upstream transactions supporting the calculation (`TRANSACTION_SUPPORTS_CALCULATION`).
3. Reaches source locations and coordinates (`SOURCE_LOCATION_SUPPORTS_FACT` or direct).
4. Reaches original document IDs and SHA-256 hashes (`DOCUMENT_CONTAINS_SOURCE_LOCATION`).
5. Reaches independent counter-evidence challenges (`FINDING_HAS_COUNTER_EVIDENCE`).
6. Reaches human auditor sign-offs (`FINDING_HAS_REVIEW_DECISION`).

The result is returned as a validated `TraceabilityChain` object. If any link is missing, `unresolved_links` explicitly documents the gap.

---

## 6. Audit Isolation & Security Boundaries

- **Strict Multi-Tenancy:** Nodes belonging to `AUDIT-CORP-A` cannot be connected to `AUDIT-CORP-B`.
- **Validation Check:** `add_relationship()` verifies that `source_node.audit_id == rel.audit_id == target_node.audit_id`. Any mismatch raises an immediate `ValueError: Audit Isolation Violation`.
- **Self-Loop Prohibition:** `source_id == target_id` is forbidden to prevent cyclic loops.
