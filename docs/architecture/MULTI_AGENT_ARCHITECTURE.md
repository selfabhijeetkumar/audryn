# AUDRYN — Multi-Agent Architecture

> **Document ID:** AUDRYN-ARCH-002  
> **Status:** APPROVED  
> **Phase:** 3 — Multi-Agent Audit Core  

---

## 1. Overview & Architectural Principles

AUDRYN employs a multi-tiered, heterogeneous agent architecture designed specifically for high-assurance statutory financial auditing. The architecture divides responsibilities across three discrete framework layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        LangGraph Supervisor                            │
│           (StateGraph Orchestration, Checkpoints, Interrupts)           │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│     CrewAI Investigation Team        │  │ MS Agent Framework Review    │
│  (Specialist Audit Collaboration)    │  │    (Independent Challenge)   │
│                                      │  │                              │
│ • Corporate Tax Audit Specialist     │  │ • Counter-Evidence Challenger│
│ • General Ledger Investigator        │  │ • Blind-Spot Spotter         │
│ • Evidence Matching Specialist       │  │ • Independent Finding        │
│ • Forensic Investigator              │  │   Reviewer                   │
└──────────────────┬───────────────────┘  └──────────────┬───────────────┘
                   │                                     │
                   └──────────────────┬──────────────────┘
                                      ▼
             ┌─────────────────────────────────────────────────┐
             │       Deterministic Financial Engine (Decimal)   │
             │       + Cryptographic Evidence Vault (SHA-256)  │
             └─────────────────────────────────────────────────┘
```

---

## 2. Framework Roles & Boundaries

### 2.1 LangGraph (Primary Orchestrator)
- **Responsibility:** Stateful audit lifecycle management, conditional branch routing, checkpoint persistence via SQLite/MemorySaver, execution error recovery, human-in-the-loop interruption, and final completeness gating.
- **State Model:** `AuditGraphState` typed Pydantic/TypedDict channels.
- **Boundary:** Sub-agents never modify the supervisor graph directly. They communicate exclusively through structured input/output envelopes.

### 2.2 CrewAI (Investigation Team)
- **Responsibility:** Collaborative deep investigation of anomalies detected during deterministic reconciliation and document ingestion.
- **Operating Model:** Sequential/hierarchical process using local Ollama (`qwen3:4b`, temperature 0.0).
- **Specialist Roster:**
  1. **Corporate Tax Audit Specialist:** Inspects tax schedules, tests depreciation compliance against demonstration rules, and flags statutory classification discrepancies.
  2. **General Ledger Investigator:** Traces journal entries, verifies debit/credit integrity, tests roll-forwards, and detects unusual transaction velocity.
  3. **Evidence Matching Specialist:** Cross-references invoices, contracts, and bank records against ledger postings, tracking exact page and row coordinates.
  4. **Forensic Investigator:** Hunts duplicate invoices, split payments, round-sum vouchers, and abnormal vendor transactions.
- **Rule:** Specialists **never** perform mathematical calculations themselves. All calculations are executed through deterministic Python tools (`verify_trial_balance`, `verify_depreciation`, `compute_variance`, `detect_duplicate_reference`).

### 2.3 Microsoft Agent Framework (Independent Review Team)
- **Responsibility:** Independent challenge, adversarial counter-evidence retrieval, blind-spot spotting, and objective finding verdict formulation.
- **Isolation:** Runs in an isolated execution context completely separate from the investigation crew. It begins from original source documents and deterministic outputs, not from CrewAI's conclusions.
- **Specialist Roster:**
  1. **Counter-Evidence Challenger:** Searches for reversals, credit notes, timing cut-off differences, and legitimate commercial explanations.
  2. **Blind-Spot Spotter:** Evaluates procedure coverage, untested statutory areas, and gaps in evidence chains.
  3. **Independent Finding Reviewer:** Reviews deterministic arithmetic proofs and assigns independent verdicts (`SUPPORTED`, `CONTRADICTED`, `PARTIALLY_SUPPORTED`, `UNRESOLVED`, `INSUFFICIENT_EVIDENCE`).

---

## 3. Strict Prohibitions
1. **Zero LLM Arithmetic:** No language model is ever permitted to compute, estimate, or extrapolate financial totals or variances.
2. **No Autonomous Fraud Labeling:** Discrepancies and variances must never be automatically branded as fraud; they require counter-evidence analysis and human escalation.
3. **No Automatic Completion:** A run with missing mandatory documents or unresolved critical findings cannot finalize.
