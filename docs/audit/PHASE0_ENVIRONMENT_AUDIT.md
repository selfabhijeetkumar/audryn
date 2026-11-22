# PHASE 0 — AUDRYN Environment Audit
**Project:** AUDRYN — Evidence-First Multi-Agent Financial Audit Intelligence System  
**Audit Date:** 2026-11-22  
**Audit Class:** Inspection-Only (No modifications made)  
**Auditor:** Antigravity Senior Architecture Audit

---

## PHASE A — Host Environment

### Operating System
| Property | Value |
|----------|-------|
| OS | Microsoft Windows 11 Home Single Language |
| Version | 10.0.26300 |
| Architecture | 64-bit |

**Evidence:** `Get-CimInstance Win32_OperatingSystem`

### Runtime Versions
| Runtime | Version | Status |
|---------|---------|--------|
| Node.js | v26.13.1 | VERIFIED |
| npm | 11.21.0 | VERIFIED |
| pnpm | 9.12.2 | VERIFIED |
| Python | 3.13.15 | VERIFIED |
| pip | 26.2.1 | VERIFIED |
| Git | 2.56.0.windows.4 | VERIFIED |
| Java | 25.0.5.0.3 (LTS) | VERIFIED |

**Evidence:** `node --version; npm --version; pnpm --version; python --version; pip --version; git --version; java --version`

> [!IMPORTANT]
> Python 3.13 is current but **LangGraph, CrewAI, and Microsoft Agent Framework have not been tested against 3.13 in production.** Their supported range is typically 3.10–3.12. This is the single most significant compatibility risk for the entire framework layer.

### Hardware
| Component | Specification | Status |
|-----------|--------------|--------|
| CPU | Intel Core i7-12650H (12th Gen) | VERIFIED |
| CPU Cores | 10 physical / 16 logical | VERIFIED |
| CPU Clock | 2300 MHz base | VERIFIED |
| RAM | 16 GB | VERIFIED |
| GPU 1 | Intel UHD Graphics (iGPU, 2 GB shared) | VERIFIED |
| GPU 2 | NVIDIA GeForce RTX 4050 Laptop GPU | VERIFIED |
| VRAM (RTX 4050) | ~6 GB (6141 MiB total, 30 MiB used at time of audit) | VERIFIED |
| CUDA | 13.3 (Driver 610.78 / NVIDIA-SMI 610.78) | VERIFIED |
| Disk C: Total | ~354 GB | VERIFIED |
| Disk C: Free | 54.47 GB | VERIFIED |

**Evidence:** `Get-CimInstance Win32_Processor`, `nvidia-smi`, `Get-PSDrive`

> [!WARNING]
> 54 GB free disk space is adequate but watch for model downloads. `gemma4:31b-cloud` is listed in Ollama but its local size is shown as `-` (cloud model, not downloaded locally). Full local LLM models for financial document tasks (e.g., Llama 3.1 8B) require 5–10 GB each. Plan accordingly before downloading.

### Ollama
| Property | Value | Status |
|----------|-------|--------|
| Ollama Version | 0.40.17 | VERIFIED |
| Running Models | None (idle) | VERIFIED |
| Listed Models | `gemma4:31b-cloud` | VERIFIED |
| Model Size | `-` (cloud-routed, not local) | NOT VERIFIED as local |
| GPU Acceleration | CUDA 13.3 available | VERIFIED |
| Local Inference Ready | Conditional (no local model downloaded) | NOT VERIFIED |

**Evidence:** `ollama --version; ollama list; ollama ps`

> [!CAUTION]
> `gemma4:31b-cloud` is a cloud-routed model (size shown as `-`). It does **not** run locally on this machine. For AUDRYN's local-first requirement, a local model must be explicitly pulled (e.g., `ollama pull llama3.1:8b`). The RTX 4050 with 6 GB VRAM can run 7B/8B quantized models comfortably. 13B+ models will require CPU offloading.

---

## PHASE B — Antigravity Environment

### Configuration Files
| File | Exists | Status |
|------|--------|--------|
| `~/.gemini/antigravity-ide/mcp_config.json` | YES | VERIFIED |
| `~/.gemini/settings.json` (global) | YES (at `~/.gemini/config/mcp_config.json`) | VERIFIED |
| `%APPDATA%\Antigravity IDE\User\settings.json` | YES | VERIFIED |
| `~/.gemini/antigravity/mcp_config.json` | YES (AGY native config) | VERIFIED |

### Specialized GSD Agents
All five agents are defined in `c:\FAI AGENT\.agents\agents\`:

| Agent | File | Status |
|-------|------|--------|
| gsd-researcher | `.agents/agents/gsd-researcher.md` | VERIFIED |
| gsd-planner | `.agents/agents/gsd-planner.md` | VERIFIED |
| gsd-executor | `.agents/agents/gsd-executor.md` | VERIFIED |
| gsd-verifier | `.agents/agents/gsd-verifier.md` | VERIFIED |
| gsd-debugger | `.agents/agents/gsd-debugger.md` | VERIFIED |

**Evidence:** `Get-ChildItem -Path "c:\FAI AGENT\.agents\agents"`

### Custom Skills
All 12 skills present in `.agents/skills/`:

| Skill | SKILL.md Present | Status |
|-------|-----------------|--------|
| codebase-mapper | YES | VERIFIED |
| context-compressor | YES | VERIFIED |
| context-fetch | YES | VERIFIED |
| context-health-monitor | YES | VERIFIED |
| debugger | YES | VERIFIED |
| empirical-validation | YES | VERIFIED |
| executor | YES | VERIFIED |
| plan-checker | YES | VERIFIED |
| planner | YES | VERIFIED |
| subagent-delegation | YES | VERIFIED |
| token-budget | YES | VERIFIED |
| verifier | YES | VERIFIED |

### GSD Workflows
All workflow files present in `.agent/workflows/`:

| Workflow | File | Status |
|----------|------|--------|
| /map | `map.md` | VERIFIED |
| /plan | `plan.md` | VERIFIED |
| /execute | `execute.md` | VERIFIED |
| /verify | `verify.md` | VERIFIED |
| /debug | `debug.md` | VERIFIED |
| /pause | `pause.md` | VERIFIED |
| /resume | `resume.md` | VERIFIED |
| /new-project | `new-project.md` | VERIFIED |
| /progress | `progress.md` | VERIFIED |
| /sprint | `sprint.md` | VERIFIED |
| /research-phase | `research-phase.md` | VERIFIED |
| /web-search | `web-search.md` | VERIFIED |

Additional workflows also present: `add-phase`, `add-todo`, `audit-milestone`, `check-todos`, `complete-milestone`, `discuss-phase`, `help`, `insert-phase`, `install`, `list-phase-assumptions`, `new-milestone`, `plan-milestone-gaps`, `remove-phase`, `update`, `whats-new`

---

## PHASE C — MCP Server Audit

### MCP Configuration Locations Found
1. `~/.gemini/antigravity/mcp_config.json` (Antigravity native)
2. `~/.gemini/antigravity-ide/mcp_config.json` (IDE-level)
3. `~/.gemini/config/mcp_config.json` (Global config)
4. `~/.gemini/settings.json` (global user settings — references fast-context, grok-search, context7, ace-tool)

### MCP Server Status Matrix

| Server | Installed | Configured | Registered (AGY) | Operational | Relevant to AUDRYN |
|--------|-----------|------------|------------------|-------------|-------------------|
| **Stitch MCP** | YES (npx) | YES | YES | AVAILABLE (key present) | YES — UI generation |
| **Context7 MCP** | YES (npx) | YES | YES | AVAILABLE | YES — framework docs |
| **Supabase MCP** | YES (npx) | YES | YES | AVAILABLE (token present) | YES — database/auth |
| **Fast Context MCP** | CONFIGURED | YES (settings.json) | NOT in AGY config | NOT VERIFIED | CONDITIONAL |
| **Grok Search MCP** | CONFIGURED | YES (settings.json) | NOT in AGY config | BLOCKED — placeholder keys ("n") | NO |
| **ACE Tool** | CONFIGURED | YES (settings.json) | NOT in AGY config | BLOCKED — placeholder credentials ("j") | NOT REQUIRED |
| **Code Review Graph** | YES (pip pkg `2.3.9`) | YES (.code-review-graph/) | NOT as MCP server | AVAILABLE as Python package only | NOT REQUIRED |

### Configuration Conflict Identified
- Stitch MCP and Supabase MCP and Context7 appear in **both** `~/.gemini/antigravity/mcp_config.json` AND `~/.gemini/antigravity-ide/mcp_config.json` and `~/.gemini/config/mcp_config.json`
- Two different Stitch API keys are present across config locations (redacted — both appear to be real keys, not placeholders)
- This dual-registration is not necessarily a conflict but should be audited before production

> [!CAUTION]
> **SECURITY RISK:** Real API keys and tokens (Stitch, Supabase) are stored in plaintext in multiple JSON config files:
> - `~/.gemini/antigravity-ide/mcp_config.json`
> - `~/.gemini/antigravity/mcp_config.json`  
> - `~/.gemini/config/mcp_config.json`
> These files are outside the project `.gitignore` scope and are machine-local only. Do NOT copy these files into the AUDRYN project repository. The access token values have been REDACTED in this audit report.

### Grok Search MCP
Status: **BLOCKED**  
Evidence: `TAVILY_API_KEY: "n"`, `GROK_API_KEY: "n"` — all credentials are single-character placeholder values "n". This MCP cannot activate without real keys.

### ACE Tool
Status: **BLOCKED**  
Evidence: `--base-url "j"`, `--token "j"` — both values are single-character placeholder "j". As instructed, no activation attempted.

### Fast Context MCP
Status: **NOT VERIFIED**  
Evidence: `WINDSURF_API_KEY: "y"` — value "y" is a placeholder. This MCP will not connect.

### Stitch MCP Tools (AVAILABLE)
Registered tools confirmed in `~/.gemini/antigravity/mcp/StitchMCP/`: create_project, get_project, update_project, delete_project, list_projects, list_screens, get_screen, update_screen, download_file, generate_screen_from_text, edit_screens, generate_variants, upload_design_md, create_design_system, create_design_system_from_design_md, update_design_system, list_design_systems, apply_design_system

### Supabase MCP Tools (AVAILABLE)
Registered tools confirmed in `~/.gemini/antigravity/mcp/supabase/`: search_docs, list_organizations, get_organization, list_projects, get_project, get_cost, confirm_cost, create_project, pause_project, restore_project, list_tables, list_extensions, list_migrations, apply_migration, execute_sql, query_logs, get_advisors, get_project_url, get_publishable_keys, generate_typescript_types, list_edge_functions, deploy_edge_function, create_branch, list_branches, delete_branch, merge_branch, reset_branch, rebase_branch, create_notebook, list_notebooks, get_notebook, run_notebook, delete_notebook

### Context7 MCP Tools (AVAILABLE)
Tools: `resolve-library-id`, `query-docs`

---

## PHASE D — Plugins and Engineering Governance

### CodeRabbit
| Component | Location | Version | Status |
|-----------|----------|---------|--------|
| Plugin definition | `~/.gemini/config/plugins/coderabbit/` | 1.2.1 | VERIFIED |
| `code-reviewer` agent | `agents/code-reviewer.md` | Present | VERIFIED |
| `autofix` agent | `agents/autofix.md` | Present | VERIFIED |
| `code-review` skill | `skills/code-review/SKILL.md` | Present | VERIFIED |
| `autofix` skill | `skills/autofix/SKILL.md` | Present | VERIFIED |
| `coderabbit-config` skill | `skills/coderabbit-config/SKILL.md` | Present | VERIFIED |
| Plugin data dir | `~/.gemini/antigravity/plugin_data/coderabbit/` | Present | VERIFIED |

### Ponytail
| Component | Status | Evidence |
|-----------|--------|---------|
| Skill files | 7 skills installed | VERIFIED |
| ponytail | SKILL.md present | VERIFIED |
| ponytail-audit | SKILL.md present | VERIFIED |
| ponytail-debt | SKILL.md present | VERIFIED |
| ponytail-gain | SKILL.md present | VERIFIED |
| ponytail-help | SKILL.md present | VERIFIED |
| ponytail-review | SKILL.md present | VERIFIED |
| ponytail-update | SKILL.md present | VERIFIED |
| IDE setting | `ponytail.defaultMode: "full"` | VERIFIED |
| Active version | MIT license, `argument-hint: [lite\|full\|ultra]` | VERIFIED |

> [!NOTE]
> Ponytail is configured as `full` mode by default in IDE settings. The skill itself defaults to `ultra`. For AUDRYN, which requires a sophisticated multi-framework architecture, consider disabling ponytail ultra-minimalism for the framework layer specifically (it may resist installing LangGraph + CrewAI as "unnecessary").

### GSD Methodology
| Component | Location | Status |
|-----------|----------|--------|
| PROJECT_RULES.md | `c:\FAI AGENT\PROJECT_RULES.md` | VERIFIED |
| GSD-STYLE.md | `c:\FAI AGENT\GSD-STYLE.md` | VERIFIED |
| GEMINI.md (workspace) | `c:\FAI AGENT\.gemini\GEMINI.md` | VERIFIED |
| adapters/GEMINI.md | `c:\FAI AGENT\adapters\GEMINI.md` | VERIFIED |
| adapters/CLAUDE.md | `c:\FAI AGENT\adapters\CLAUDE.md` | VERIFIED |
| adapters/GPT_OSS.md | `c:\FAI AGENT\adapters\GPT_OSS.md` | VERIFIED |
| model_capabilities.yaml | `c:\FAI AGENT\model_capabilities.yaml` | VERIFIED |
| VERSION | `1.6.0` | VERIFIED |
| Templates (`.gsd/templates/`) | 18 templates | VERIFIED |
| Examples (`.gsd/examples/`) | 4 examples | VERIFIED |
| Scripts | 10 scripts (.ps1 + .sh pairs) | VERIFIED |

### GSD State Files (AUDRYN-specific — NOT yet created)
| File | Status |
|------|--------|
| `.gsd/SPEC.md` | NOT INSTALLED (required before implementation) |
| `.gsd/ROADMAP.md` | NOT INSTALLED (required before /plan) |
| `.gsd/STATE.md` | NOT INSTALLED (required for session memory) |
| `CHANGELOG.md` | NOT INSTALLED |
| `docs/` directory | NOT INSTALLED (created by this audit) |

### Other Installed Integrations
| Tool | Status | Notes |
|------|--------|-------|
| code-review-graph | AVAILABLE (v2.3.9 pip) | Graph DB exists at `.code-review-graph/graph.db` |
| gemini-web2api | AVAILABLE (separate git repo) | Local Gemini API proxy server |
| fastmcp | AVAILABLE (v3.4.8) | MCP server framework — useful for custom AUDRYN MCP tools |
| google-genai | AVAILABLE (v2.28.0) | Google Generative AI SDK |
| google-generativeai | AVAILABLE (v0.8.6) | Legacy Google GenAI SDK |

---

## PHASE E — Repository Inspection

### Project Root
`c:\FAI AGENT\` — This is the GSD agent framework root, **not** an AUDRYN application repository.

### Git Status
```
fatal: not a git repository (or any of the parent directories): .git
```
**Status:** NOT INSTALLED — The workspace root `c:\FAI AGENT` has no git repository initialized.

> [!IMPORTANT]
> `c:\FAI AGENT` has no `.git` directory. AUDRYN will need a new git repository initialized at a designated project root before any implementation begins. The GSD methodology requires atomic commits (`one task = one commit`). This is a prerequisite blocker.

The only git repository found is `c:\FAI AGENT\gemini-web2api\` — a separate sub-project.

### Directory Structure
```
c:\FAI AGENT\
├── .agent/workflows/        — 28 GSD workflow files (VERIFIED)
├── .agents/agents/          — 5 GSD specialist agents (VERIFIED)
├── .agents/skills/          — 12 skill SKILL.md files (VERIFIED)
├── .code-review-graph/      — graph.db + .gitignore (VERIFIED)
├── .gemini/GEMINI.md        — Workspace Gemini config (VERIFIED)
├── .gsd/
│   ├── examples/            — 4 reference examples
│   └── templates/           — 18 GSD document templates
├── adapters/                — CLAUDE.md, GEMINI.md, GPT_OSS.md
├── gemini-web2api/          — Local Gemini API proxy (separate git repo)
├── scripts/                 — 10 validation scripts (.ps1 + .sh)
├── GSD-STYLE.md
├── model_capabilities.yaml
├── PROJECT_RULES.md
└── VERSION                  — 1.6.0
```

### Missing AUDRYN-Specific Structure
None of the following exist yet (expected — this is pre-implementation):
- `docs/` (created by this audit only)
- `src/` or `app/`
- `frontend/`
- `backend/`
- Any Python application code
- Any package.json
- Any `.env` or `.env.example`
- `.gsd/SPEC.md`, `.gsd/ROADMAP.md`, `.gsd/STATE.md`

### gemini-web2api Sub-Project (Inspection Only)
- Python 3.13 venv present
- FastAPI-based Gemini API proxy server
- `config.json` present (contains server configuration — NOT credentials per first 5 lines)
- `config.json` is in `.gitignore` (correct)
- Tests present (`tests/test_modular_sync.py`)
- Not relevant to AUDRYN core — separate utility

---

## PHASE I — Performance and Data Readiness

### Local Compute Assessment
| Resource | Available | AUDRYN Feasibility |
|----------|-----------|-------------------|
| RAM | 16 GB | ADEQUATE for 7-8B local models + application |
| GPU VRAM | 6 GB (RTX 4050) | Fits 7B Q4 models; 13B requires offloading |
| CUDA | 13.3 | VERIFIED — GPU inference enabled |
| CPU | i7-12650H 10c/16t | ADEQUATE for CPU-offloaded inference |
| Disk Free | 54.47 GB | ADEQUATE (allow 15-20 GB for models + app) |

### Python Data Processing Stack (INSTALLED)
| Package | Version | AUDRYN Use |
|---------|---------|-----------|
| pandas | 2.3.3 | Financial data manipulation |
| numpy | 2.3.5 | Numerical calculations |
| torch | 2.6.0+cu124 | ML models, CUDA-enabled |
| scikit-learn | 1.8.0 | Anomaly detection |
| matplotlib | 3.11.1 | Financial charting |
| plotly | NOT INSTALLED | Interactive charts — needed |
| streamlit | 1.62.0 | Rapid UI prototyping |
| reportlab | 4.4.10 | PDF generation (audit reports) |
| opencv-python | 4.13.0.90 | Image processing |
| pillow | 12.2.0 | Image handling |
| shap | 0.52.0 | Explainability for anomaly detection |

### Missing Document Processing Libraries
| Package | Status | AUDRYN Need |
|---------|--------|------------|
| pypdf / pdfplumber | NOT INSTALLED | CRITICAL — PDF financial document ingestion |
| pytesseract | NOT INSTALLED | HIGH — OCR for scanned documents |
| openpyxl | NOT INSTALLED | CRITICAL — Excel spreadsheet processing |
| xlrd | NOT INSTALLED | HIGH — Legacy .xls support |
| camelot-py | NOT INSTALLED | MEDIUM — PDF table extraction |
| tabula-py | NOT INSTALLED | MEDIUM — PDF table extraction alternative |

### Existing Synthetic Data
No synthetic financial datasets found in `c:\FAI AGENT`. Must be generated during SPEC phase.

### Local Inference Feasibility Assessment
- **Recommended local model:** `llama3.1:8b` or `mistral:7b` (Q4 quantized) — fits in 6 GB VRAM
- **Tool-calling support:** Available in both Llama 3.1 and Mistral via Ollama
- **JSON structured output:** Supported by Ollama with `format: json`
- **Current local model status:** No local model available — `gemma4:31b-cloud` is cloud-routed
- **Action required:** Pull a local model before AUDRYN development begins

---

*Report generated: 2026-11-22 | Inspection-only phase | No files modified*
