"""
AUDRYN Quota and Circuit Breaker Manager.
Tracks rate limits, HTTP 429 status codes, and applies cooldowns.
"""
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Tuple, Optional
from backend.providers.base import ProviderStatus


class CircuitState(str, Enum):
    CLOSED = "CLOSED"       # Normal operation
    OPEN = "OPEN"           # In cooldown, requests blocked
    HALF_OPEN = "HALF_OPEN" # Testing recovery


class QuotaManager:
    def __init__(
        self,
        failure_threshold: int = 3,
        cooldown_seconds: float = 60.0,
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        # provider -> failure count
        self._consecutive_failures: Dict[str, int] = {}
        # provider -> cooldown expiration timestamp (float)
        self._cooldown_until: Dict[str, float] = {}
        # provider -> rate limit reset timestamp
        self._rate_limit_reset: Dict[str, float] = {}
        # provider -> last error message
        self._last_error: Dict[str, str] = {}

    def get_circuit_state(self, provider_name: str) -> CircuitState:
        now = time.time()
        cooldown_expiry = self._cooldown_until.get(provider_name, 0.0)
        rate_limit_expiry = self._rate_limit_reset.get(provider_name, 0.0)

        active_block = max(cooldown_expiry, rate_limit_expiry)
        if now < active_block:
            return CircuitState.OPEN

        if active_block > 0 and self._consecutive_failures.get(provider_name, 0) >= self.failure_threshold:
            return CircuitState.HALF_OPEN

        return CircuitState.CLOSED

    def can_execute(self, provider_name: str) -> Tuple[bool, Optional[str]]:
        """Check if provider is permitted to execute or currently blocked by circuit/rate limits."""
        state = self.get_circuit_state(provider_name)
        now = time.time()

        if state == CircuitState.OPEN:
            cooldown_expiry = self._cooldown_until.get(provider_name, 0.0)
            rate_limit_expiry = self._rate_limit_reset.get(provider_name, 0.0)
            remaining = int(max(cooldown_expiry, rate_limit_expiry) - now)
            reason = self._last_error.get(provider_name, "Circuit breaker open")
            return False, f"Provider '{provider_name}' blocked ({reason}). Retry in {remaining}s."

        return True, None

    def record_success(self, provider_name: str):
        """Reset consecutive failures on successful execution."""
        self._consecutive_failures[provider_name] = 0
        self._cooldown_until.pop(provider_name, None)
        self._rate_limit_reset.pop(provider_name, None)
        self._last_error.pop(provider_name, None)

    def record_failure(
        self,
        provider_name: str,
        status: ProviderStatus,
        error_message: str,
        retry_after: Optional[float] = None,
    ):
        """Record a failure and potentially trip the circuit breaker or apply rate limit delay."""
        now = time.time()
        failures = self._consecutive_failures.get(provider_name, 0) + 1
        self._consecutive_failures[provider_name] = failures
        self._last_error[provider_name] = error_message

        if status == ProviderStatus.RATE_LIMITED:
            delay = retry_after if retry_after and retry_after > 0 else self.cooldown_seconds
            self._rate_limit_reset[provider_name] = now + delay
        elif failures >= self.failure_threshold:
            self._cooldown_until[provider_name] = now + self.cooldown_seconds

    def get_status_info(self, provider_name: str) -> Dict[str, Any]:
        state = self.get_circuit_state(provider_name)
        now = time.time()
        cooldown_expiry = self._cooldown_until.get(provider_name, 0.0)
        rate_expiry = self._rate_limit_reset.get(provider_name, 0.0)
        block_until = max(cooldown_expiry, rate_expiry)
        remaining = max(0, int(block_until - now)) if block_until > now else 0

        return {
            "circuit_state": state.value,
            "consecutive_failures": self._consecutive_failures.get(provider_name, 0),
            "blocked_seconds_remaining": remaining,
            "last_error": self._last_error.get(provider_name),
        }
