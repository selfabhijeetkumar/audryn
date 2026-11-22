# Framework Compatibility Report — AUDRYN
**Date:** 2026-11-22  
**Python Version:** 3.13.15  
**Audit Class:** Inspection-only

---

## Critical Baseline Finding

> [!CAUTION]
> **Python 3.13 Compatibility Risk:** All three selected frameworks (LangGraph, CrewAI, Microsoft Agent Framework) officially support Python 3.10–3.12. Python 3.13 is **not yet validated** by these frameworks as of late 2026. This is the primary technical risk for the entire framework layer. A dedicated Python virtual environment with Python 3.11 or 3.12 is strongly recommended for the AUDRYN agent backend.

**None of the three frameworks are currently installed.** Evidence: `pip show langgraph`, `pip show crewai`, `pip show autogen`, `pip show semantic-kernel` — all returned `WARNING: Package(s) not found`.

---

## LangGraph

### Overview
LangGraph (by LangChain Inc.) is a framework for building stateful, multi-agent applications as directed graphs. It is the natural choice as the AUDRYN orchestration backbone.

### Python Compatibility
| Python Version | LangGraph Support |
|----------------|------------------|
| 3.10 | SUPPORTED (documented) |
| 3.11 | SUPPORTED (documented) |
| 3.12 | SUPPORTED (documented) |
| 3.13 | NOT VERIFIED — not in official compatibility matrix |

**Recommendation:** Use Python 3.11 or 3.12 venv for LangGraph.

### Key Capabilities for AUDRYN
| Capability | LangGraph Feature | AUDRYN Use Case |
|-----------|------------------|----------------|
| Stateful workflows | `StateGraph` with typed state | Audit session persistence |
| Conditional routing | `add_conditional_edges()` | Evidence-based branching |
| Checkpointing | `SqliteSaver`, `PostgresSaver` | Supabase checkpoint storage |
| Human-in-the-loop | `interrupt()` + `Command` | Auditor intervention points |
| Agent orchestration | `create_react_agent()` | Individual audit agents |
| Tool integration | LangChain tool format | PDF, OCR, DB tools |
| Multi-agent | `langgraph.prebuilt`, supervisor patterns | Cross-agent reconciliation |
| Streaming | Built-in event streaming | Real-time audit progress |
| Recovery | Checkpoint restore | Resume after failure |

### Integration with Supabase
- LangGraph supports `PostgresSaver` for checkpointing
- Supabase provides a PostgreSQL-compatible endpoint
- This enables persistent audit state across sessions — directly relevant to AUDRYN

### Dependencies to Install
```
langgraph>=0.2.0
langchain>=0.3.0
langchain-community>=0.3.0
langchain-core>=0.3.0
```

### Status: NOT INSTALLED — REQUIRED

---

## CrewAI

### Overview
CrewAI provides role-based multi-agent collaboration with structured task delegation. Best used as a secondary layer for specialized audit investigation teams rather than the main orchestration engine.

### Python Compatibility
| Python Version | CrewAI Support |
|----------------|---------------|
| 3.10 | SUPPORTED |
| 3.11 | SUPPORTED |
| 3.12 | SUPPORTED |
| 3.13 | NOT VERIFIED |

### Key Capabilities for AUDRYN
| Capability | CrewAI Feature | AUDRYN Use Case |
|-----------|---------------|----------------|
| Role-based agents | `Agent(role=..., goal=...)` | Audit associate, senior auditor personas |
| Task delegation | `Task(description=..., agent=...)` | Specific audit investigation tasks |
| Structured output | Pydantic model outputs | Evidence-linked findings |
| Sequential/Hierarchical | `Process.sequential / hierarchical` | Audit workflow ordering |
| Tool support | Custom tool classes | Financial document tools |
| Memory | Built-in short/long-term memory | Audit context retention |
| Collaboration | Built-in agent communication | Cross-agent reconciliation |

### Integration Boundaries (AUDRYN)
CrewAI should **not** be in the main execution path as an orchestrator. It should be invoked from LangGraph nodes as a "crew dispatcher":

```
LangGraph (main graph)
  → Node: "investigation" 
    → CrewAI Crew (specialized audit team)
      → AuditAssociate, SeniorAuditor, ForensicReviewer agents
    ← Returns structured findings
  → Node: "reconciliation"
```

### Dependencies to Install
```
crewai>=0.80.0
crewai-tools>=0.14.0
```

> [!WARNING]
> CrewAI has significant dependency overlap with LangChain. Verify dependency resolution before installing both. Use a clean virtual environment.

### Status: NOT INSTALLED — REQUIRED (secondary role only)

---

## Microsoft Agent Framework

### Overview
"Microsoft Agent Framework" is an ambiguous designation. The viable Python-compatible options are:

| Option | Package | Python Support | Ollama Compat. |
|--------|---------|----------------|----------------|
| **AutoGen** | `pyautogen` / `autogen-agentchat` | 3.10–3.12 | YES (via LiteLLM) |
| **Semantic Kernel** | `semantic-kernel` | 3.10–3.12 | YES (via connectors) |
| **Azure AI Agent Service** | `azure-ai-projects` | 3.8+ | NO (cloud-only) |

> [!IMPORTANT]
> The user has specified **"Do not substitute AutoGen for Microsoft Agent Framework."** However, the Microsoft AI ecosystem for Python multi-agent orchestration *is* AutoGen (maintained by Microsoft Research) or Semantic Kernel (maintained by Microsoft). There is no separate "Microsoft Agent Framework" Python package distinct from these. This requires clarification before the framework layer design is finalized.

### Semantic Kernel (Most Viable Option)
| Capability | Semantic Kernel Feature | AUDRYN Use Case |
|-----------|------------------------|----------------|
| Plugin system | `KernelPlugin` / `KernelFunction` | Audit capability plugins |
| Planner | `FunctionChoiceBehavior` | Agent planning |
| Memory | Semantic memory / vector stores | Evidence retrieval |
| Structured output | Pydantic + OpenAI format | Audit findings |
| Ollama support | `OllamaChatCompletion` connector | Local model inference |
| LangGraph interop | Manual integration required | Verification workflows |

### Ollama Compatibility (All Options)
All Microsoft AI Python SDKs support Ollama via OpenAI-compatible endpoint (`http://localhost:11434/v1`). LiteLLM bridge is the cleanest path.

### Recommended Role in AUDRYN
Microsoft AI SDK should handle **independent review workflows** only — not share the main execution graph with LangGraph:

```
LangGraph Graph
  → Node: "independent-verification"
    → Semantic Kernel / AutoGen agent (independent review)
    ← Returns verification judgment
  → Continue main graph
```

This keeps the frameworks from sharing state directly and isolates failures.

### Status: NOT INSTALLED — CLARIFICATION REQUIRED before installation

---

## Ollama Integration Assessment

### Current State
| Property | Value |
|----------|-------|
| Ollama Version | 0.40.17 |
| Local Models | NONE (gemma4:31b-cloud is cloud-routed) |
| GPU | RTX 4050 / 6 GB VRAM |
| CUDA | 13.3 |

### Model Recommendations for AUDRYN
| Model | Size | VRAM Need | Tool Calling | JSON Output | Recommendation |
|-------|------|-----------|-------------|-------------|----------------|
| `llama3.1:8b` | ~5 GB | ~5 GB | YES | YES | RECOMMENDED — fits in 6 GB |
| `mistral:7b` | ~4 GB | ~4 GB | YES | YES | RECOMMENDED — fast inference |
| `llama3.2:3b` | ~2 GB | ~2 GB | YES | YES | RECOMMENDED — testing/dev |
| `qwen2.5:7b` | ~5 GB | ~5 GB | YES | YES | RECOMMENDED — strong reasoning |
| `gemma2:9b` | ~6 GB | ~6.5 GB | LIMITED | YES | RISKY — may exceed VRAM |
| `llama3.1:70b` | ~40 GB | Exceeds | YES | YES | NOT FEASIBLE (CPU only, too slow) |

> [!NOTE]
> For AUDRYN's financial audit context, `llama3.1:8b` or `qwen2.5:7b` are the best local options. Both support structured JSON output and tool calling via Ollama. Neither requires paid API access.

---

## Framework Conflict Analysis

### Dependency Overlap Risk
| Conflict Area | LangGraph | CrewAI | SK/AutoGen | Risk Level |
|--------------|-----------|--------|-----------|-----------|
| LangChain dependency | REQUIRED | OPTIONAL | NONE | MEDIUM |
| Pydantic version | v2 required | v2 required | v2 required | LOW |
| OpenAI SDK | v1+ | v1+ | v1+ | LOW |
| httpx version | Shared | Shared | Shared | LOW |
| Python version | 3.10-3.12 | 3.10-3.12 | 3.10-3.12 | HIGH (we have 3.13) |

### Recommended Integration Architecture

```
AUDRYN Agent Architecture
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LAYER 1: ORCHESTRATION (LangGraph)
  ┌─────────────────────────────────────────────────┐
  │  Main Audit Graph (StateGraph)                  │
  │  - Document ingestion state                     │
  │  - Audit session checkpointing (Supabase)       │
  │  - Conditional routing (evidence-based)         │
  │  - Human-in-the-loop interrupt nodes            │
  └──────────────┬──────────────┬───────────────────┘
                 │              │
LAYER 2a:        │   LAYER 2b:  │
CREW DISPATCH    │   INDEP.     │
(CrewAI)         │   REVIEW     │
                 │   (SK)       │
  ┌──────────────▼──┐  ┌────────▼──────────────────┐
  │ Audit Crew      │  │ Independent Verification   │
  │ - Associate     │  │ - Counter-evidence agent   │
  │ - Senior        │  │ - Adversarial challenger   │
  │ - Forensic      │  │ - Completeness gate        │
  └─────────────────┘  └───────────────────────────┘
                 │              │
LAYER 3: LOCAL INFERENCE (Ollama)
  ┌─────────────────────────────────────────────────┐
  │  llama3.1:8b or qwen2.5:7b (local, no API key) │
  │  OpenAI-compatible endpoint: localhost:11434/v1  │
  └─────────────────────────────────────────────────┘
```

### Minimal Viable Integration Boundaries
1. **LangGraph controls all state** — no other framework writes to audit state directly
2. **CrewAI is stateless from LangGraph's perspective** — returns structured Pydantic objects
3. **Microsoft AI SDK runs in isolated subgraph** — no shared tool registry with LangGraph
4. **All frameworks talk to Ollama via OpenAI-compatible API** — single inference endpoint
5. **Supabase is the only persistent store** — no framework-native DBs (no SQLite in production)

---

## Missing Packages Summary

### Critical (must install before any agent work)
- `langgraph` + `langchain` + `langchain-community`
- `pypdf` or `pdfplumber` (PDF document ingestion)
- `openpyxl` (Excel ingestion)

### High Priority
- `crewai` + `crewai-tools`
- `pytesseract` (OCR)
- `plotly` (interactive evidence graphs)

### Conditional (after framework clarification)
- `semantic-kernel` or `pyautogen`
- `tabula-py` or `camelot-py` (PDF table extraction)

### Not Required
- Paid API SDKs (Anthropic, OpenAI direct) — Ollama covers local inference
- AutoGen (pending Microsoft framework clarification)

---

*Report generated: 2026-11-22 | Inspection-only | No packages installed*
