"""
AUDRYN Base AI Provider Interfaces and Types.
Defines contracts for local and cloud LLM providers with deterministic protection.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional


class ProviderStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    AUTH_ERROR = "AUTH_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"


class ProviderType(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"


@dataclass
class ProviderResponse:
    text: str = ""
    structured_data: Optional[Dict[str, Any]] = None
    raw_response: Any = None
    provider_name: str = ""
    model_name: str = ""
    latency_ms: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    retry_count: int = 0
    failover_occurred: bool = False
    failover_history: List[str] = field(default_factory=list)


@dataclass
class ProviderHealthStatus:
    name: str
    display_name: str
    provider_type: ProviderType
    status: ProviderStatus
    model: str
    is_available: bool = False
    latency_ms: float = 0.0
    message: str = ""
    last_checked: str = ""
    rate_limit_reset: Optional[str] = None


class BaseAIProvider(ABC):
    """Abstract base class for all AUDRYN AI providers."""

    def __init__(
        self,
        name: str,
        display_name: str,
        provider_type: ProviderType,
        model: str,
        priority: int = 10,
    ):
        self.name = name
        self.display_name = display_name
        self.provider_type = provider_type
        self.model = model
        self.priority = priority
        self.last_status: ProviderStatus = ProviderStatus.NOT_CONFIGURED
        self.last_error: Optional[str] = None

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if required API keys, base URLs, or runtime requirements are set."""
        pass

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        response_format: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Execute text completion / inference."""
        pass

    @abstractmethod
    async def health_check(self) -> ProviderHealthStatus:
        """Evaluate provider connectivity, authentication and readiness."""
        pass

    def validate_response(self, response: ProviderResponse) -> bool:
        """Validate response structure. Can be overridden for strict schema checks."""
        return response.success and bool(response.text.strip() or response.structured_data)
