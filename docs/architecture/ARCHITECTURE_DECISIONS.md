# Architecture Decisions Record (ADR) — AUDRYN

## ADR 001: Three-Tier Multi-Framework Strategy
- **Status:** Accepted
- **Context:** Financial audits require both strict deterministic state workflows (legal compliance) and flexible, role-based investigative exploration (forensic review), plus an unbiased verification mechanism to challenge audit findings.
- **Decision:**
  - **Tier 1 (Orchestration):** LangGraph acts as the top-level state machine. It manages session persistence, conditional branching, human-in-the-loop interrupts, and final completeness gating.
  - **Tier 2 (Investigation):** CrewAI is invoked as specialized sub-graphs / nodes within LangGraph for role-based forensic exploration (e.g., Audit Associate, Senior Auditor).
  - **Tier 3 (Independent Verification):** Microsoft Agent Framework (`agent-framework` + `agent-framework-ollama`) runs as an independent review agent with an isolated context, challenging assumptions and detecting blind spots before workpaper generation.
- **Consequences:** Eliminates single-framework bias. Clear responsibility boundaries prevent framework state clashes.

---

## ADR 002: Deterministic Verification Layer Bypassing LLMs
- **Status:** Accepted
- **Context:** Financial figures and tax calculations cannot tolerate hallucination.
- **Decision:** All mathematical tie-outs, depreciation schedule verifications, tax bracket applications, and variance calculations are executed strictly by deterministic Python functions (using NumPy and Pandas) and verified with SHA-256 assertions. LLMs are restricted to narrative interpretation, anomaly hypothesis generation, and semantic mapping.
- **Consequences:** 100% calculation determinism; regulatory defensibility.

---

## ADR 003: Local-First, Zero-Paid-API Foundation
- **Status:** Accepted
- **Context:** Small/mid-sized CA firms handle sensitive non-public financial records and cannot risk cloud data leakage or high per-token API costs.
- **Decision:** Default inference runtime is Ollama on the local machine (NVIDIA RTX 4050, 6GB VRAM), utilizing compact tool-calling models (Qwen 4B/7B, Llama 3.1 8B).
- **Consequences:** Zero external API cost, complete data privacy, offline audit capability.

---

## ADR 004: Evidence Graph & Not-Checked Register
- **Status:** Accepted
- **Context:** Traditional audit software produces flat checklists that conceal omitted areas.
- **Decision:** AUDRYN maintains an interactive Evidence Graph linking every claim to exact document coordinates (page, table cell, voucher ID). Any account not tied to empirical evidence is logged in a persistent "Not Checked Register".
- **Consequences:** Direct visibility into audit blind spots and completeness gaps.
