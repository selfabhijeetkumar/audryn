"""
AUDRYN AI Provider Configuration.
Centralized settings for local and cloud inference failover.
"""
import os
from typing import List


class ProviderConfig:
    # Mode: 'local' (Ollama -> Gemini -> Groq -> NVIDIA NIM) or 'cloud' (Gemini -> Groq -> NVIDIA NIM)
    is_cloud_env = bool(
        os.environ.get("RENDER")
        or os.environ.get("VERCEL")
        or os.environ.get("ENV") == "production"
    )

    MODE = os.environ.get(
        "AI_PROVIDER_MODE",
        "cloud" if is_cloud_env else "local",
    ).lower()

    # Data governance: Never send raw financial records or confidential client documents to cloud
    ALLOW_CONFIDENTIAL_EXTERNAL_DATA = (
        os.environ.get("AI_ALLOW_CONFIDENTIAL_EXTERNAL_DATA", "false").lower() == "true"
    )

    # Provider priorities
    LOCAL_PRIORITY: List[str] = ["ollama", "gemini", "groq", "nvidia_nim"]
    CLOUD_PRIORITY: List[str] = ["gemini", "groq", "nvidia_nim"]

    # Ollama settings
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b")

    # Gemini settings
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    # Groq settings
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    # NVIDIA NIM settings
    NVIDIA_NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "").strip()
    NVIDIA_NIM_MODEL = os.environ.get("NVIDIA_NIM_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")
    NVIDIA_NIM_BASE_URL = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    # Timeouts & Circuit Breaker thresholds
    REQUEST_TIMEOUT_SECONDS = float(os.environ.get("AI_TIMEOUT_SECONDS", "15.0"))
    CIRCUIT_BREAKER_FAIL_THRESHOLD = int(os.environ.get("AI_CIRCUIT_FAIL_THRESHOLD", "3"))
    CIRCUIT_BREAKER_COOLDOWN_SECONDS = float(os.environ.get("AI_CIRCUIT_COOLDOWN_SECONDS", "60.0"))

    @classmethod
    def get_priority_chain(cls) -> List[str]:
        if cls.MODE == "cloud":
            return list(cls.CLOUD_PRIORITY)
        return list(cls.LOCAL_PRIORITY)
