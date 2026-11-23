"""
AUDRYN Model Capabilities and Metadata.
Tracks model constraints, context limits, and audit compliance characteristics.
"""
from typing import Dict, Any


MODEL_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "ollama/qwen3:4b": {
        "provider": "ollama",
        "display_name": "Qwen 3 4B (Local)",
        "context_window": 8192,
        "structured_output": True,
        "tool_calling": True,
        "data_confidentiality": "STRICT_LOCAL",
        "description": "Local on-premise inference ensuring 100% data sovereignty on private hardware.",
    },
    "gemini-2.0-flash": {
        "provider": "gemini",
        "display_name": "Google Gemini 2.0 Flash",
        "context_window": 1048576,
        "structured_output": True,
        "tool_calling": True,
        "data_confidentiality": "EXTERNAL_ENCRYPTED_TRANSIT",
        "description": "High-throughput primary cloud reasoning model with 1M context window.",
    },
    "gemini-1.5-pro": {
        "provider": "gemini",
        "display_name": "Google Gemini 1.5 Pro",
        "context_window": 2097152,
        "structured_output": True,
        "tool_calling": True,
        "data_confidentiality": "EXTERNAL_ENCRYPTED_TRANSIT",
        "description": "Deep audit cross-document analysis model with 2M token context window.",
    },
    "llama-3.3-70b-versatile": {
        "provider": "groq",
        "display_name": "Groq Llama 3.3 70B",
        "context_window": 131072,
        "structured_output": True,
        "tool_calling": True,
        "data_confidentiality": "EXTERNAL_ENCRYPTED_TRANSIT",
        "description": "Ultra-low latency cloud inference on custom LPU silicon for fast audit verification.",
    },
    "nvidia/llama-3.1-nemotron-70b-instruct": {
        "provider": "nvidia_nim",
        "display_name": "NVIDIA Llama 3.1 Nemotron 70B",
        "context_window": 131072,
        "structured_output": True,
        "tool_calling": True,
        "data_confidentiality": "EXTERNAL_ENCRYPTED_TRANSIT",
        "description": "Enterprise-grade high-accuracy reasoning model hosted on NVIDIA NIM.",
    },
}


def get_model_capability(model_name: str) -> Dict[str, Any]:
    return MODEL_CAPABILITIES.get(
        model_name,
        {
            "provider": "unknown",
            "display_name": model_name,
            "context_window": 8192,
            "structured_output": True,
            "tool_calling": False,
            "data_confidentiality": "UNKNOWN",
            "description": "Standard language model endpoint.",
        },
    )
