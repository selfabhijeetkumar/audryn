# AUDRYN — AI Provider Setup and API Key Configuration Guide

This guide details how to configure inference providers for AUDRYN, including local private inference (Ollama) and high-resilience cloud reasoning (Google Gemini, Groq, and NVIDIA NIM).

---

## 1. Multi-Provider Architecture Overview

AUDRYN employs a stateful multi-tier inference architecture with automatic circuit-breaker failover:

```
[ Ingestion & Evidence Vault ]
             │
             ▼
[ Deterministic Python Decimal Engine ]  <-- Strictly computes ALL arithmetic
             │
             ▼
      [ Provider Router ]
             │
   ┌─────────┴─────────┐
   │                   │
   ▼ (Local Mode)      ▼ (Cloud Mode)
1. Ollama (Private) 1. Google Gemini 2.0 Flash
2. Gemini 2.0 Flash 2. Groq LPU (Llama 3.3 70B)
3. Groq LPU         3. NVIDIA NIM (Nemotron 70B)
4. NVIDIA NIM
```

### Deterministic Financial Safety Guarantee
**Language models in AUDRYN NEVER compute financial numbers.**
All sums, subtractions, variances, depreciation schedules, and tax formulas are calculated by Python's `Decimal` arithmetic engine (`ROUND_HALF_UP` to two decimal places). AI models only interpret, explain, and cross-reference structured outputs against statutory text.

---

## 2. Supported Providers & Key Procurement

### Provider 1: Ollama (Local Private On-Premise)
- **Role:** Primary Local Provider (100% Data Sovereignty)
- **Model:** `qwen3:4b` (or `qwen2.5:3b`)
- **Cost:** Free / Zero external network calls
- **Installation:**
  1. Download and install Ollama from [https://ollama.com](https://ollama.com).
  2. Pull the model:
     ```bash
     ollama pull qwen3:4b
     ```
  3. Ensure Ollama is running on `http://127.0.0.1:11434`.

### Provider 2: Google Gemini (Primary Cloud Reasoning)
- **Role:** Primary Cloud Reasoning Model (1M Token Context)
- **Model:** `gemini-2.0-flash` (or `gemini-1.5-pro`)
- **Key Procurement:**
  1. Go to [Google AI Studio](https://aistudio.google.com/).
  2. Click **Create API Key**.
  3. Copy your key and add it to `.env`:
     ```bash
     GEMINI_API_KEY=AIzaSy...
     GEMINI_MODEL=gemini-2.0-flash
     ```

### Provider 3: Groq (Ultra-Low Latency Inference)
- **Role:** High-Speed Secondary Cloud Failover
- **Model:** `llama-3.3-70b-versatile`
- **Key Procurement:**
  1. Go to [Groq Console](https://console.groq.com/).
  2. Navigate to **API Keys** and generate a new key.
  3. Copy your key and add it to `.env`:
     ```bash
     GROQ_API_KEY=gsk_...
     GROQ_MODEL=llama-3.3-70b-versatile
     ```

### Provider 4: NVIDIA NIM (Enterprise Reasoning)
- **Role:** Enterprise Compliance and Tertiary Cloud Failover
- **Model:** `nvidia/llama-3.1-nemotron-70b-instruct`
- **Key Procurement:**
  1. Go to [NVIDIA Build Console](https://build.nvidia.com/).
  2. Select `nvidia/llama-3.1-nemotron-70b-instruct`.
  3. Click **Get API Key**.
  4. Copy your key and add it to `.env`:
     ```bash
     NVIDIA_NIM_API_KEY=nvapi-...
     NVIDIA_NIM_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
     ```

---

## 3. Data Governance & Privacy Enforcement

AUDRYN enforces a strict boundary between confidential client data and external cloud inference:

```bash
# Set to 'false' to guarantee client records are NEVER sent to cloud providers
AI_ALLOW_CONFIDENTIAL_EXTERNAL_DATA=false
```

When set to `false`, any request flagged as confidential is restricted exclusively to local Ollama. If local Ollama is not running, AUDRYN triggers a `DATA GOVERNANCE GUARD` block, protecting confidential ledgers and vouchers from leaving your secure network.

---

## 4. Automatic Failover & Circuit Breaker Mechanics

The system monitors every inference request:
1. **Timeout Threshold:** 15.0 seconds (customizable via `AI_TIMEOUT_SECONDS`).
2. **Circuit Breaker:** After 3 consecutive timeouts or HTTP 5xx errors, the provider circuit moves to `OPEN`.
3. **Cooldown Window:** Blocked for 60 seconds before testing recovery in `HALF_OPEN` state.
4. **Rate Limit 429:** Respects provider `Retry-After` headers automatically.

Admins can inspect live circuit breaker states and failover event trails in **Workspace 10 (Settings & Roles)** or via the REST API at `GET /api/v1/providers/status`.
