"""
AUDRYN Provider Health Check Service.
Executes parallel non-blocking health checks across all registered providers.
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List

from backend.providers.base import ProviderHealthStatus, ProviderStatus
from backend.providers.provider_router import ProviderRouter, get_provider_router


class ProviderHealthChecker:
    @staticmethod
    async def check_all(router: ProviderRouter = None) -> Dict[str, Any]:
        if router is None:
            router = get_provider_router()

        tasks = [provider.health_check() for provider in router.providers.values()]
        results: List[ProviderHealthStatus] = await asyncio.gather(*tasks, return_exceptions=False)

        provider_statuses: Dict[str, Any] = {}
        available_count = 0
        configured_count = 0

        for r in results:
            if r.status != ProviderStatus.NOT_CONFIGURED:
                configured_count += 1
            if r.is_available:
                available_count += 1

            provider_statuses[r.name] = {
                "name": r.name,
                "display_name": r.display_name,
                "type": r.provider_type.value,
                "status": r.status.value,
                "model": r.model,
                "is_available": r.is_available,
                "latency_ms": round(r.latency_ms, 2),
                "message": r.message,
                "last_checked": r.last_checked,
            }

        overall = "healthy" if available_count > 0 else ("unconfigured" if configured_count == 0 else "degraded")

        return {
            "status": overall,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "total_providers": len(router.providers),
            "configured_providers": configured_count,
            "available_providers": available_count,
            "active_mode": router.config.MODE,
            "deterministic_engine_fallback": "ACTIVE",
            "providers": provider_statuses,
        }
