# Technical Stack Specification — AUDRYN

## Core Runtimes
- **Python:** 3.13.15 (64-bit AMD64)
- **Node.js:** v26.13.1 (for frontend & design tools)
- **Package Manager:** pip 26.3 inside isolated `.venv`

## Multi-Agent Architecture
- **Primary Orchestrator:** LangGraph 1.2.x (StateGraph, checkpointing, interrupt)
- **Investigation Framework:** CrewAI 1.15.x (Hierarchical & sequential role execution)
- **Review Framework:** Microsoft Agent Framework (`agent-framework` 1.26.x + `agent-framework-ollama` 1.0.0b)

## Local Inference & AI
- **Engine:** Ollama 0.40.17
- **Hardware Acceleration:** CUDA 13.3 on NVIDIA GeForce RTX 4050 (6GB VRAM)
- **Target Local Models:** Qwen 4B / Qwen 7B / Llama 3.1 8B (Q4 Quantized)

## Data & Processing Engine
- **Data Manipulation:** Pandas 2.3.x, NumPy 2.3.x
- **Document Extraction:** PyPDF, OpenPyXL, Python-multipart
- **Database:** Local SQLite (`audryn_local.db`) for initial prototype
- **API Backend:** FastAPI 0.135.x + Uvicorn 0.42.x
- **Config & Validation:** Pydantic 2.12.x, Pydantic-Settings 2.15.x

## Quality & Governance
- **Reviewer:** CodeRabbit CLI & skills
- **Optimization:** Ponytail governance
- **Security:** Pip-Audit, Python-dotenv, PyJWT, Cryptography
