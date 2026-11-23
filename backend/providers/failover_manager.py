"""
AUDRYN Failover Manager.
Tracks failover transitions, reasons, and maintains an audit event trail.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.providers.base import ProviderStatus


@dataclass
class FailoverEvent:
    timestamp: str
    from_provider: str
    to_provider: str
    reason: str
    status: str
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "from_provider": self.from_provider,
            "to_provider": self.to_provider,
            "reason": self.reason,
            "status": self.status,
            "latency_ms": self.latency_ms,
        }


class FailoverManager:
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self._events: List[FailoverEvent] = []

    def record_failover(
        self,
        from_provider: str,
        to_provider: str,
        reason: str,
        status: ProviderStatus,
        latency_ms: float = 0.0,
    ) -> FailoverEvent:
        event = FailoverEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            from_provider=from_provider,
            to_provider=to_provider,
            reason=reason,
            status=status.value if hasattr(status, "value") else str(status),
            latency_ms=latency_ms,
        )
        self._events.append(event)
        if len(self._events) > self.max_history:
            self._events = self._events[-self.max_history:]
        return event

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in reversed(self._events[-limit:])]

    @staticmethod
    def is_retryable(status: ProviderStatus) -> bool:
        """Determines if the failure warrants automatic failover to the next provider."""
        return status in (
            ProviderStatus.RATE_LIMITED,
            ProviderStatus.TIMEOUT,
            ProviderStatus.CIRCUIT_OPEN,
            ProviderStatus.AUTH_ERROR,
            ProviderStatus.DEGRADED,
            ProviderStatus.ERROR,
            ProviderStatus.NOT_CONFIGURED,
        )
