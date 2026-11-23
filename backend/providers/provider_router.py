"""
AUDRYN AI Provider Router and Automatic Failover Orchestrator.
Orchestrates multi-provider resilience across Ollama, Gemini, Groq, and NVIDIA NIM.
Strictly safeguards confidential financial data and arithmetic integrity.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional

from backend.providers.base import (
    BaseAIProvider,
    ProviderResponse,
    ProviderHealthStatus,
    ProviderStatus,
    ProviderType,
)
from backend.providers.config import ProviderConfig
from backend.providers.quota_manager import QuotaManager
from backend.providers.failover_manager import FailoverManager
from backend.providers.ollama_provider import OllamaProvider
from backend.providers.gemini_provider import GeminiProvider
from backend.providers.groq_provider import GroqProvider
from backend.providers.nvidia_nim_provider import NvidiaNimProvider

logger = logging.getLogger("audryn.providers")


class ProviderRouter:
    def __init__(self):
        self.config = ProviderConfig
        self.quota_manager = QuotaManager(
            failure_threshold=ProviderConfig.CIRCUIT_BREAKER_FAIL_THRESHOLD,
            cooldown_seconds=ProviderConfig.CIRCUIT_BREAKER_COOLDOWN_SECONDS,
        )
        self.failover_manager = FailoverManager()

        # Initialize concrete providers
        self.providers: Dict[str, BaseAIProvider] = {
            "ollama": OllamaProvider(
                base_url=ProviderConfig.OLLAMA_BASE_URL,
                model=ProviderConfig.OLLAMA_MODEL,
                priority=1,
            ),
            "gemini": GeminiProvider(
                api_key=ProviderConfig.GEMINI_API_KEY,
                model=ProviderConfig.GEMINI_MODEL,
                priority=2,
            ),
            "groq": GroqProvider(
                api_key=ProviderConfig.GROQ_API_KEY,
                model=ProviderConfig.GROQ_MODEL,
                priority=3,
            ),
            "nvidia_nim": NvidiaNimProvider(
                api_key=ProviderConfig.NVIDIA_NIM_API_KEY,
                model=ProviderConfig.NVIDIA_NIM_MODEL,
                priority=4,
            ),
        }

    def register_provider(self, name: str, provider: BaseAIProvider):
        """Allows registering custom mock or specialized providers for testing."""
        self.providers[name] = provider

    def get_priority_chain(self) -> List[str]:
        configured_chain = ProviderConfig.get_priority_chain()
        # Filter only existing registered providers
        return [p for p in configured_chain if p in self.providers]

    async def execute_with_failover(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        response_format: Optional[str] = None,
        confidential: bool = False,
        **kwargs,
    ) -> ProviderResponse:
        """
        Executes inference request traversing the prioritized provider chain on retryable failure.
        Enforces data governance: Never sends confidential data to cloud if disallowed.
        """
        priority_chain = self.get_priority_chain()
        failover_history: List[str] = []
        last_error_msg = ""

        # Confidentiality safeguard
        if confidential and not ProviderConfig.ALLOW_CONFIDENTIAL_EXTERNAL_DATA:
            # Strictly restrict to local providers that are configured
            priority_chain = [
                p for p in priority_chain
                if self.providers[p].provider_type == ProviderType.LOCAL
            ]
            has_configured_local = any(self.providers[p].is_configured() for p in priority_chain)
            if not priority_chain or not has_configured_local:
                return ProviderResponse(
                    success=False,
                    error_message=(
                        "DATA GOVERNANCE GUARD: Confidential financial evidence cannot be sent to cloud providers. "
                        "No local provider is configured or available and AI_ALLOW_CONFIDENTIAL_EXTERNAL_DATA is false."
                    ),
                    failover_occurred=True,
                    failover_history=["DATA_GOVERNANCE: CLOUD_BLOCKED"],
                )

        total_providers = len(priority_chain)
        for idx, provider_name in enumerate(priority_chain):
            provider = self.providers[provider_name]

            # 1. Check configuration
            if not provider.is_configured():
                reason = f"{provider.display_name} not configured"
                next_provider = priority_chain[idx + 1] if idx + 1 < total_providers else "NONE"
                self.failover_manager.record_failover(
                    from_provider=provider_name,
                    to_provider=next_provider,
                    reason=reason,
                    status=ProviderStatus.NOT_CONFIGURED,
                )
                failover_history.append(f"{provider_name}: NOT_CONFIGURED")
                continue

            # 2. Check circuit breaker / quota
            can_exec, block_reason = self.quota_manager.can_execute(provider_name)
            if not can_exec:
                next_provider = priority_chain[idx + 1] if idx + 1 < total_providers else "NONE"
                self.failover_manager.record_failover(
                    from_provider=provider_name,
                    to_provider=next_provider,
                    reason=block_reason or "Circuit open",
                    status=ProviderStatus.CIRCUIT_OPEN,
                )
                failover_history.append(f"{provider_name}: CIRCUIT_OPEN ({block_reason})")
                continue

            # 3. Attempt execution
            try:
                response = await provider.complete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    tools=tools,
                    temperature=temperature,
                    response_format=response_format,
                    **kwargs,
                )

                if response.success and provider.validate_response(response):
                    self.quota_manager.record_success(provider_name)
                    response.failover_occurred = len(failover_history) > 0
                    response.failover_history = failover_history
                    return response

                # Non-success response
                last_error_msg = response.error_message or "Unknown provider failure"
                self.quota_manager.record_failure(
                    provider_name=provider_name,
                    status=provider.last_status,
                    error_message=last_error_msg,
                )
                next_provider = priority_chain[idx + 1] if idx + 1 < total_providers else "NONE"
                self.failover_manager.record_failover(
                    from_provider=provider_name,
                    to_provider=next_provider,
                    reason=last_error_msg,
                    status=provider.last_status,
                    latency_ms=response.latency_ms,
                )
                failover_history.append(f"{provider_name}: FAILED ({last_error_msg})")

            except Exception as e:
                err_str = str(e)
                last_error_msg = err_str
                self.quota_manager.record_failure(
                    provider_name=provider_name,
                    status=ProviderStatus.ERROR,
                    error_message=err_str,
                )
                next_provider = priority_chain[idx + 1] if idx + 1 < total_providers else "NONE"
                self.failover_manager.record_failover(
                    from_provider=provider_name,
                    to_provider=next_provider,
                    reason=err_str,
                    status=ProviderStatus.ERROR,
                )
                failover_history.append(f"{provider_name}: EXCEPTION ({err_str})")

        return ProviderResponse(
            success=False,
            error_message=f"All configured providers exhausted. Last error: {last_error_msg}",
            failover_occurred=len(failover_history) > 0,
            failover_history=failover_history,
        )

    def get_status_summary(self) -> Dict[str, Any]:
        """Provides status payload for administration dashboards and system health reporting."""
        priority_chain = self.get_priority_chain()
        active_provider_name = priority_chain[0] if priority_chain else "none"

        providers_info = {}
        for name, p in self.providers.items():
            circuit_info = self.quota_manager.get_status_info(name)
            providers_info[name] = {
                "name": name,
                "display_name": p.display_name,
                "type": p.provider_type.value,
                "model": p.model,
                "configured": p.is_configured(),
                "last_status": p.last_status.value if hasattr(p.last_status, "value") else str(p.last_status),
                "circuit_state": circuit_info["circuit_state"],
                "consecutive_failures": circuit_info["consecutive_failures"],
                "blocked_seconds_remaining": circuit_info["blocked_seconds_remaining"],
                "priority": p.priority,
            }

        return {
            "mode": ProviderConfig.MODE,
            "confidentiality_mode": "STRICT_LOCAL_ONLY" if not ProviderConfig.ALLOW_CONFIDENTIAL_EXTERNAL_DATA else "ALLOW_CLOUD_ENCRYPTED",
            "priority_chain": priority_chain,
            "active_primary_provider": active_provider_name,
            "providers": providers_info,
            "recent_failovers": self.failover_manager.get_recent_events(limit=10),
        }


# Singleton router instance
_router_instance: Optional[ProviderRouter] = None


def get_provider_router() -> ProviderRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = ProviderRouter()
    return _router_instance
