# AUDRYN — Functional and Technical Specification

> **Status:** FINALIZED  
> **Product:** AUDRYN — Evidence-First Multi-Agent Financial Audit Intelligence System  
> **Case Study Focus:** Case Study 2 — Optimizing the Tax Audit Agent  
> **Target Users:** Audit Associates, Senior Auditors, Audit Managers, Small and Mid-Sized CA/Accounting Firms

---

## A. Problem Statement
Tax and statutory financial audits require analyzing hundreds of pages across heterogeneous formats (PDF balance sheets, Excel schedules, scanned invoices, regulatory filings, trial balances). Auditors face manual reconciliation overhead, high risk of undetected multi-period discrepancies, lack of verifiable evidence chains, and blind spots created by sample-based or generic check models. Existing generic LLM tools hallucinate financial figures, lack deterministic reconciliation mechanisms, and do not provide defensible audit trails or human-in-the-loop control gates.

## B. Actual User Problems
1. **Manual Cross-Year Inconsistencies:** Comparing Prior-Year (PY) and Current-Year (CY) schedules takes days; subtle reclassifications and timing differences are missed.
2. **Hallucination in Financial Calculations:** LLMs cannot be trusted with statutory tax math; financial proofs must be mathematically deterministic.
3. **Black-Box AI Decisions:** Auditors cannot submit reports to regulatory bodies without an ironclad, interactive evidence trail linking every finding to exact line items.
4. **Audit Blind Spots:** Auditors often fail to verify areas where documentation was quietly omitted by clients.
5. **Tax Law & Rule Drift:** Tax regulations change annually with specific effective dates; agents using static prompts evaluate prior years against incorrect legislation.

## C. Target Users
- **Audit Associates:** Ingest documents, extract line items, flag initial variances, run standard checks.
- **Senior Auditors:** Deep-dive into anomaly investigations, review counter-evidence, validate cross-year ties.
- **Audit Managers / Partners:** Review Audit Completeness Gates, inspect executive summaries, approve workpapers, export defensible audit packs.
- **Small and Mid-Sized CA/Accounting Firms:** Require enterprise-grade audit intelligence without enterprise SaaS subscriptions or third-party cloud data exposure.

## D. Functional Requirements
1. **Multi-Format Ingestion:** Ingest PDF (text & tabular), Excel (.xlsx/.xls), and CSV files.
2. **Deterministic Arithmetic Engine:** Zero LLM computation for totals, tax brackets, depreciation, or variance percentages. All math computed via Python/NumPy/Pandas.
3. **Evidence Graph:** Graph representation mapping (Entity) -> (Account) -> (Line Item) -> (Voucher/Source) -> (Audit Assertion).
4. **Stateful Multi-Agent Orchestration:** Deterministic workflow execution, interruptible human checkpoints, step replay.
5. **Local-First Zero-Cost Execution:** Fully functional using local Ollama models (e.g., Qwen 4B/7B, Llama 3.1 8B) without mandatory paid API calls.

## E. Non-Functional Requirements
1. **Privacy & Data Isolation:** All financial documents processed locally or in dedicated local SQLite; no client financial data sent to third-party endpoints.
2. **Determinism & Reproducibility:** Every audit run is assignable a deterministic run seed, replayable with identical findings.
3. **Performance:** Under 6 GB VRAM consumption on an NVIDIA RTX 4050 laptop GPU.
4. **Auditability:** Every assertion includes document name, page number, bounding box/table cell reference, and computation formula.
5. **Design Aesthetics:** Obsidian Assembly / UNESCO editorial clarity. No purple gradients, no generic AI SaaS templates, no fake counters or charts.

## F. Selected Architecture
- **Primary Orchestrator:** LangGraph — Stateful graph, conditional edges, checkpointing, recovery, and human-in-the-loop interruptions.
- **Specialized Multi-Agent Investigation:** CrewAI — Role-based investigation crew (Tax Specialist, Forensic Auditor, Compliance Reviewer).
- **Independent Verification & Review:** Microsoft Agent Framework (`agent-framework` + `agent-framework-ollama`) — Unbiased challenger, completeness checker, counter-evidence validator.
- **Local Inference:** Ollama via local OpenAI-compatible endpoint.

## G. Mandatory Differentiating Features (P0, P1, P2)

### P0 (Core Foundation & Evidence Verification)
1. **Document Intelligence:** Extract text, tables, and key financial metadata from PDFs and Excels.
2. **Cross-Year Reconciliation:** Automated PY vs CY tie-out with variance analysis and reconciliation statements.
3. **Deterministic Financial Verification:** Formula-based math verification layer bypassing LLM arithmetic.
4. **Interactive Evidence Graph:** Traceable node-link structure connecting claims to exact source evidence.
5. **Audit Completeness Gate:** Hard checkpoint blocking report generation if high-risk assertions remain unverified.
6. **Not Checked Register:** Explicit registry of all accounts and line items that were excluded or lacked documentation.
7. **Evidence-Linked Audit Reports:** Exportable markdown and PDF workpapers linking every finding to source coordinates.

### P1 (Advanced Multi-Agent & Investigation)
8. **Anomaly Investigator:** CrewAI specialized crew flagging anomalous journal entries and tax disallowances.
9. **Counter-Evidence Intelligence:** Agent specifically tasked with searching for conflicting documents or disproving evidence.
10. **GAP RADAR & Blind-Spot Discovery:** Automated detection of missing disclosure notes, missing statutory registers, and reconciliation omissions.
11. **Effective-Dated Rulebook:** Time-aware statutory tax rule engine validating entries against the legal tax code active in that fiscal year.
12. **Human-in-the-Loop Review:** LangGraph interrupt points allowing auditors to annotate, override, or accept flagged issues.
13. **Conflict Resolution:** Protocol arbitrating contradictory assessments between the primary crew and the independent reviewer.

### P2 (Governance, Evaluation & Lab)
14. **Adversarial Challenge Lab:** Simulation environment injecting synthetic errors (tampered totals, omitted entries) to evaluate agent precision.
15. **Run Replay:** Checkpoint-based execution replay allowing step-by-step audit inspection and audit log reconstruction.
16. **Evaluation Engine:** Metric dashboard measuring agent recall, false discovery rate, and citation precision.
17. **Cinematic Technical UI:** Bespoke 3D/editorial interface adhering to Obsidian Assembly and UNESCO guidelines.

## H. Risks & Failure Scenarios
1. **Model Context Overflow:** Complex multi-page filings exceed token budgets. *Mitigation:* Chunking with semantic table extraction and Targeted Read discipline.
2. **Local Model Incoherence:** Smaller local models hallucinating tool arguments. *Mitigation:* Strict Pydantic JSON schemas, constrained generation, fallback to rule-based parser.
3. **Framework Clashes:** LangGraph and CrewAI sharing globals. *Mitigation:* Strict boundary: LangGraph acts as the top-level supervisor; CrewAI runs encapsulated in LangGraph worker nodes.

## I. Security Requirements
- All private uploaded documents stored in gitignored local directories (`uploads/private/`, `data/private/`).
- No hardcoded keys; all settings via `.env` with validation through `pydantic-settings`.
- Strict file magic byte validation preventing malicious script uploads disguised as spreadsheets or PDFs.

## J. Evaluation Requirements
- **Citation Precision:** 100% of reported anomalies must point to a valid document coordinate.
- **Arithmetic Accuracy:** 100% on deterministic tie-out computations.
- **Adversarial Catch Rate:** >90% detection of injected synthetic accounting anomalies in Challenge Lab.

## K. Acceptance Criteria
1. Full Phase 1 framework setup: LangGraph, CrewAI, and Microsoft Agent Framework verified in Python 3.13 venv.
2. Working local Ollama model running inference with tool-calling and structured JSON output.
3. Smoke tests passing independently for all three agent frameworks.
4. Baseline directory structure, Git configuration, and GSD documentation verified.

## L. Project Constraints
- Zero mandatory cloud API dependencies.
- Maximum 6 GB VRAM consumption on RTX 4050.
- Clean isolation of framework responsibilities.
