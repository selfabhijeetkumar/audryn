# AUDRYN — Project Roadmap

> **Methodology:** GSD (Get Shit Done)  
> **Status:** ACTIVE  
> **Current Phase:** Phase 7 — Frontend & Design Implementation (Obsidian Assembly)  

---

## Phase Overview

```
Phase 1: Project Foundation & Framework Setup (COMPLETED)
    ├── Task 1.1: Root verification, Git & .gitignore isolation (DONE)
    ├── Task 1.2: Python 3.13 venv & core framework dependencies (DONE)
    ├── Task 1.3: Ollama local model setup & benchmark (DONE)
    ├── Task 1.4: Framework smoke tests (LangGraph, CrewAI, MS Agent Framework) (DONE)
    └── Task 1.5: Security baseline & GSD state synchronization (DONE)

Phase 2: Data Ingestion & Deterministic Math Engine (COMPLETED)
    ├── Task 2.1: Multi-format parser (PDF, Excel, CSV) & Evidence Vault (DONE)
    ├── Task 2.2: Deterministic verification & tie-out engine (Decimal only) (DONE)
    ├── Task 2.3: Synthetic tax audit dataset generator (10 Planted Anomalies) (DONE)
    ├── Task 2.4: Audit Completeness Gate & Not-Checked Register (DONE)
    └── Task 2.5: Full test suite verification & implementation report (DONE)

Phase 3: Multi-Agent Audit Core (LangGraph + CrewAI + MS Agent Framework) (COMPLETED)
    ├── Task 3.1: LangGraph 13-node state machine & checkpointing (DONE)
    ├── Task 3.2: CrewAI specialized audit investigation crew (DONE)
    ├── Task 3.3: Cross-year reconciliation workflow (DONE)
    ├── Task 3.4: Counter-Evidence Intelligence Engine (DONE)
    ├── Task 3.5: GAP RADAR blind-spot discovery service (DONE)
    ├── Task 3.6: Human-in-the-loop interrupt nodes & persistent ledger (DONE)
    └── Task 3.7: Security isolation & 95-test suite validation (DONE)

Phase 4: India-Ready Intelligence & Reliability Hardening (COMPLETED)
    ├── Task 4.1: INR demonstration dataset migration & Indian number formatting (DONE)
    ├── Task 4.2: Versioned Indian Tax Rulebook (Section 115BAA, Section 32, Form 3CD) (DONE)
    ├── Task 4.3: Durable SQLite checkpoint persistence with WAL mode & mutex (DONE)
    ├── Task 4.4: Adversarial evaluation lab (25 cases) & prompt injection defense (DONE)
    ├── Task 4.5: Empirical metrics & calibration evaluation (Brier, ECE, latency) (DONE)
    └── Task 4.6: Pytest warning remediation & 127-test regression suite (DONE)

Phase 5: Evidence Graph & Report Generation (COMPLETED)
    ├── Task 5.1: Evidence Graph Engine (14 nodes, 19 rels, SQLite WAL, traversal) (DONE)
    ├── Task 5.2: Deterministic Financial Linkage Service (invoices, GL, bank, tax) (DONE)
    ├── Task 5.3: Statutory Report Generation Engine (12 sections, zero LLM math) (DONE)
    ├── Task 5.4: Release Gate Service (DRAFT/BLOCKED/REVIEW_READY/FINALIZED) (DONE)
    ├── Task 5.5: ReportLab PDF report generator with tamper detection hashes (DONE)
    └── Task 5.6: Full 159-test regression suite & Phase 5 reports (DONE)

Phase 6: Adversarial Challenge Lab & Evaluation Engine (COMPLETED)
    ├── Task 6.1: Decoupled evaluation harness & ground-truth isolation (DONE)
    ├── Task 6.2: Scalable synthetic dataset generator across 3 scale tiers (DONE)
    ├── Task 6.3: Benchmark V1 (25 cases) & Benchmark V2 (60 cases across 8 categories) (DONE)
    ├── Task 6.4: Formal metric engine (Precision, Recall, F1, Brier, 10-bin ECE, 95% CIs) (DONE)
    ├── Task 6.5: Metamorphic & property-based testing (row-order, idempotency, tamper) (DONE)
    └── Task 6.6: Full 168-test regression suite & Phase 6 reports (DONE)

Phase 7: Frontend & Design Implementation (Obsidian Assembly — NEXT SPRINT)
    ├── Task 7.1: Design review & Stitch MCP system generation
    ├── Task 7.2: Custom editorial financial dashboard with INR formatting
    └── Task 7.3: Interactive Evidence Graph visualization & source coordinate explorer
```

---

## Completed Sprints

### Phase 1: Foundation & Framework Setup
| Task | Description | Status | Verification Proof |
|------|-------------|--------|-------------------|
| **1.1** | Project Root, Git Init & .gitignore | DONE | `git status`, `.gitignore` verification |
| **1.2** | Python 3.13 venv & Framework Installation | DONE | `pip check`, dry-run, installation |
| **1.3** | Ollama local model setup (Qwen) | DONE | `ollama run`, tool-calling test |
| **1.4** | Smoke tests for LangGraph, CrewAI, MS Agent Framework | DONE | Deterministic test scripts |
| **1.5** | Security baseline, pip-audit & Phase 1 report | DONE | `docs/audit/PHASE1_SETUP_REPORT.md` |

### Phase 2: Data Ingestion & Deterministic Math Engine
| Task | Description | Status | Verification Proof |
|------|-------------|--------|-------------------|
| **2.1** | Multi-format parser (PDF, Excel, CSV) & Vault | DONE | `tests/unit/test_pdf_service.py`, `tests/unit/test_spreadsheet_service.py` |
| **2.2** | Deterministic verification & tie-out engine | DONE | `tests/unit/test_financial_engine.py` (8 test suites) |
| **2.3** | Synthetic tax audit dataset generator | DONE | `data/synthetic/` (10 planted anomalies) |
| **2.4** | Completeness Gate & Not-Checked Register | DONE | `tests/unit/test_completeness_gate.py`, `tests/unit/test_not_checked_register.py` |
| **2.5** | End-to-end integration & Phase 2 report | DONE | `tests/integration/test_phase2_integration.py`, `docs/audit/PHASE2_IMPLEMENTATION_REPORT.md` |

### Phase 3: Multi-Agent Audit Core
| Task | Description | Status | Verification Proof |
|------|-------------|--------|-------------------|
| **3.1** | LangGraph StateGraph & Checkpointing | DONE | `tests/unit/test_audit_supervisor.py` (8 tests) |
| **3.2** | CrewAI Specialized Investigation Crew | DONE | `tests/unit/test_crewai_execution.py` & tools |
| **3.3** | Cross-Year Reconciliation Workflow | DONE | `tests/unit/test_cross_year.py` (7 tests) |
| **3.4** | Counter-Evidence Intelligence Engine | DONE | `tests/unit/test_counter_evidence.py` (6 tests) |
| **3.5** | GAP RADAR Blind-Spot Detector | DONE | `tests/unit/test_gap_radar.py` (8 tests) |
| **3.6** | Human-in-the-Loop Interrupt & Ledger | DONE | `tests/unit/test_human_review.py` (11 tests) |
| **3.7** | Independent Review & Security Isolation | DONE | `tests/unit/test_review_team.py` (17 tests), `tests/unit/test_security.py` (6 tests), `tests/integration/test_phase3_integration.py` |

### Phase 4: India-Ready Intelligence & Reliability Hardening
| Task | Description | Status | Verification Proof |
|------|-------------|--------|-------------------|
| **4.1** | INR Demonstration Dataset Migration | DONE | `data/synthetic/`, `tests/unit/test_inr_formatting.py` (6 tests) |
| **4.2** | Versioned Indian Tax Rulebook | DONE | `backend/services/indian_tax_rulebook.py`, `tests/unit/test_indian_tax_rulebook.py` (13 tests) |
| **4.3** | Durable SQLite Checkpoint Persistence | DONE | `backend/services/checkpoint_service.py`, `tests/unit/test_sqlite_checkpoint.py` (7 tests) |
| **4.4** | Adversarial Evaluation Lab (25 Cases) | DONE | `backend/tools/adversarial_lab.py`, `tests/unit/test_adversarial_lab.py` (6 tests) |
| **4.5** | Empirical Evaluation Metrics & Calibration | DONE | `backend/services/evaluation_metrics.py`, `docs/audit/EVALUATION_METRICS.md` |
| **4.6** | Regression Testing & Warning Cleanup | DONE | `pytest.ini`, 127/127 tests passing |

### Phase 5: Evidence Graph & Report Generation
| Task | Description | Status | Verification Proof |
|------|-------------|--------|-------------------|
| **5.1** | Evidence Graph Engine | DONE | `backend/services/evidence_graph_service.py`, `tests/unit/test_evidence_graph.py` (6 tests) |
| **5.2** | Deterministic Financial Linkage | DONE | `backend/services/financial_linkage_service.py`, `tests/unit/test_financial_linkage.py` (7 tests) |
| **5.3** | Statutory Report Generation Engine | DONE | `backend/services/report_generation_service.py`, `tests/unit/test_report_generation.py` (14 tests) |
| **5.4** | Release Gate Evaluation Service | DONE | `backend/services/release_gate_service.py`, `tests/unit/test_release_gate.py` (9 tests) |
| **5.5** | Publication-Grade PDF Generator | DONE | `backend/services/pdf_report_service.py`, `tests/integration/test_phase5_integration.py` |
| **5.6** | Security & End-to-End Integration | DONE | `tests/integration/test_phase5_integration.py` (1 test), 159 tests total |

### Phase 6: Adversarial Challenge Lab & Evaluation Engine
| Task | Description | Status | Verification Proof |
|------|-------------|--------|-------------------|
| **6.1** | Decoupled Architecture & Ground-Truth Isolation | DONE | `backend/evaluation/`, `docs/architecture/EVALUATION_ENGINE_ARCHITECTURE.md` |
| **6.2** | Scalable Dataset Generator (Baseline, Medium, Large) | DONE | `backend/evaluation/dataset_generator.py`, `tests/unit/test_evaluation_engine.py` |
| **6.3** | Benchmark V1 (25 cases) & V2 (60 cases across 8 categories) | DONE | `backend/evaluation/benchmark_registry.py`, `docs/audit/ADVERSARIAL_BENCHMARK_SPECIFICATION.md` |
| **6.4** | Formal Metric Engine (Precision, Recall, F1, Brier, ECE, CIs) | DONE | `backend/evaluation/metrics_engine.py`, `tests/unit/test_evaluation_engine.py` |
| **6.5** | Metamorphic & Property Verification | DONE | `backend/evaluation/evaluation_engine.py`, 100% property checks passing |
| **6.6** | Regression & Benchmark Integration | DONE | `tests/integration/test_phase6_benchmark.py`, 168 automated tests passing (0 failures, 0 warnings) |

---

## Active Sprint: Phase 7 Work Breakdown (Obsidian Assembly)

| Task | Description | Status | Verification Target |
|------|-------------|--------|-------------------|
| **7.1** | Design System & Stitch MCP Generation | READY | Stitch project creation & token definition |
| **7.2** | Editorial Financial Dashboard (INR Native) | READY | Lakh/Crore formatted audit console |
| **7.3** | Interactive Evidence Graph Visualizer | READY | Coordinate explorer & lineage inspector |
