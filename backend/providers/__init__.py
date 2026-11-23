"""
AUDRYN Multi-Provider AI Architecture Package.
"""
from backend.providers.base import (
    BaseAIProvider,
    ProviderResponse,
    ProviderHealthStatus,
    ProviderStatus,
    ProviderType,
)
from backend.providers.config import ProviderConfig
from backend.providers.quota_manager import QuotaManager, CircuitState
from backend.providers.failover_manager import FailoverManager, FailoverEvent
from backend.providers.ollama_provider import OllamaProvider
from backend.providers.gemini_provider import GeminiProvider
from backend.providers.groq_provider import GroqProvider
from backend.providers.nvidia_nim_provider import NvidiaNimProvider
from backend.providers.provider_router import ProviderRouter, get_provider_router
from backend.providers.provider_health import ProviderHealthChecker
from backend.providers.model_capabilities import MODEL_CAPABILITIES, get_model_capability
from backend.providers.response_normalizer import ResponseNormalizer

__all__ = [
    "BaseAIProvider",
    "ProviderResponse",
    "ProviderHealthStatus",
    "ProviderStatus",
    "ProviderType",
    "ProviderConfig",
    "QuotaManager",
    "CircuitState",
    "FailoverManager",
    "FailoverEvent",
    "OllamaProvider",
    "GeminiProvider",
    "GroqProvider",
    "NvidiaNimProvider",
    "ProviderRouter",
    "get_provider_router",
    "ProviderHealthChecker",
    "MODEL_CAPABILITIES",
    "get_model_capability",
    "ResponseNormalizer",
]
