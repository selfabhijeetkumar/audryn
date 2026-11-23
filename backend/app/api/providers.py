"""
AUDRYN AI Provider Administration and Observability API.
Exposes multi-provider health, real-time circuit-breaker states, and failover telemetry.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.app.auth import get_current_user, require_permission, verify_csrf
from backend.app.rbac import Permission
from backend.providers.provider_router import get_provider_router
from backend.providers.provider_health import ProviderHealthChecker
from backend.providers.base import ProviderStatus

router = APIRouter(prefix="/providers", tags=["AI Providers & Failover"])


class TestFailoverRequest(BaseModel):
    from_provider: str = "ollama"
    to_provider: str = "gemini"
    reason: str = "Simulated manual failover test"


@router.get("/status")
def get_providers_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Returns high-level status of all inference providers,
    active primary model, rate-limit cooldowns, and failover event trail.
    """
    router_instance = get_provider_router()
    return router_instance.get_status_summary()


@router.get("/health")
async def get_providers_health(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Executes live parallel health checks across all registered providers
    and returns latency metrics and readiness status.
    """
    router_instance = get_provider_router()
    return await ProviderHealthChecker.check_all(router_instance)


@router.post("/failover/test", dependencies=[Depends(verify_csrf)])
def trigger_test_failover(
    req: TestFailoverRequest,
    current_user: Dict[str, Any] = Depends(require_permission(Permission.CONFIGURE_SETTINGS)),
):
    """
    Test endpoint for Partner / Senior Auditor to verify failover logging and state tracking.
    """
    router_instance = get_provider_router()
    event = router_instance.failover_manager.record_failover(
        from_provider=req.from_provider,
        to_provider=req.to_provider,
        reason=req.reason,
        status=ProviderStatus.RATE_LIMITED,
        latency_ms=12.5,
    )
    return {
        "message": "Test failover logged successfully",
        "event": event.to_dict(),
        "summary": router_instance.get_status_summary(),
    }
