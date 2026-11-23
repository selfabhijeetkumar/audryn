"""
AUDRYN AI Provider Failover and Resilience QA Test Matrix.
22 comprehensive test cases covering automatic failover, circuit breaker trips,
rate-limit recovery, data governance confidentiality, response normalization,
and health telemetry.
"""
import asyncio
import time
from typing import Dict, Any, List, Optional
import pytest

from backend.providers.base import (
    BaseAIProvider,
    ProviderResponse,
    ProviderHealthStatus,
    ProviderStatus,
    ProviderType,
)
from backend.providers.config import ProviderConfig
from backend.providers.quota_manager import QuotaManager, CircuitState
from backend.providers.failover_manager import FailoverManager
from backend.providers.provider_router import ProviderRouter
from backend.providers.provider_health import ProviderHealthChecker
from backend.providers.response_normalizer import ResponseNormalizer


class MockAIProvider(BaseAIProvider):
    """Deterministic mock provider for unit testing failover transitions."""

    def __init__(
        self,
        name: str,
        display_name: str,
        provider_type: ProviderType,
        model: str = "mock-v1",
        priority: int = 10,
        configured: bool = True,
        fail_with_status: Optional[ProviderStatus] = None,
        fail_error_message: str = "Mock simulated failure",
        delay_seconds: float = 0.0,
        response_text: str = "Mock successful completion",
    ):
        super().__init__(name, display_name, provider_type, model, priority)
        self._is_configured = configured
        self.fail_with_status = fail_with_status
        self.fail_error_message = fail_error_message
        self.delay_seconds = delay_seconds
        self.response_text = response_text
        self.call_count = 0

    def is_configured(self) -> bool:
        return self._is_configured

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        response_format: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        self.call_count += 1
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.fail_with_status:
            self.last_status = self.fail_with_status
            return ProviderResponse(
                success=False,
                provider_name=self.name,
                model_name=self.model,
                error_message=self.fail_error_message,
                latency_ms=self.delay_seconds * 1000.0,
            )

        self.last_status = ProviderStatus.AVAILABLE
        structured = ResponseNormalizer.extract_json(self.response_text)
        return ProviderResponse(
            text=self.response_text,
            structured_data=structured,
            provider_name=self.name,
            model_name=self.model,
            latency_ms=self.delay_seconds * 1000.0,
            token_usage={"total_tokens": 42},
            success=True,
        )

    async def health_check(self) -> ProviderHealthStatus:
        if not self._is_configured:
            return ProviderHealthStatus(
                name=self.name,
                display_name=self.display_name,
                provider_type=self.provider_type,
                status=ProviderStatus.NOT_CONFIGURED,
                model=self.model,
                is_available=False,
            )
        if self.fail_with_status:
            return ProviderHealthStatus(
                name=self.name,
                display_name=self.display_name,
                provider_type=self.provider_type,
                status=self.fail_with_status,
                model=self.model,
                is_available=False,
                message=self.fail_error_message,
            )
        return ProviderHealthStatus(
            name=self.name,
            display_name=self.display_name,
            provider_type=self.provider_type,
            status=ProviderStatus.AVAILABLE,
            model=self.model,
            is_available=True,
            message="Mock healthy",
        )


# ─── 22-CASE QA TEST MATRIX ──────────────────────────────────────────────────

def test_case_01_normal_operation_primary():
    async def _run():
        router = ProviderRouter()
        p1 = MockAIProvider("ollama", "Ollama", ProviderType.LOCAL, response_text='{"status": "ok"}')
        router.register_provider("ollama", p1)

        res = await router.execute_with_failover("Analyze trial balance")
        assert res.success is True
        assert res.provider_name == "ollama"
        assert res.failover_occurred is False
        assert p1.call_count == 1
    asyncio.run(_run())


def test_case_02_primary_timeout_failover_to_gemini():
    async def _run():
        router = ProviderRouter()
        p1 = MockAIProvider("ollama", "Ollama", ProviderType.LOCAL, fail_with_status=ProviderStatus.TIMEOUT, fail_error_message="Socket timeout")
        p2 = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, response_text='{"verdict": "verified"}')
        router.register_provider("ollama", p1)
        router.register_provider("gemini", p2)

        res = await router.execute_with_failover("Analyze trial balance")
        assert res.success is True
        assert res.provider_name == "gemini"
        assert res.failover_occurred is True
        assert "ollama: FAILED" in res.failover_history[0]
    asyncio.run(_run())


def test_case_03_primary_429_rate_limited_failover():
    async def _run():
        router = ProviderRouter()
        p1 = MockAIProvider("ollama", "Ollama", ProviderType.LOCAL, fail_with_status=ProviderStatus.RATE_LIMITED, fail_error_message="Rate limit 429")
        p2 = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, response_text="Success from gemini")
        router.register_provider("ollama", p1)
        router.register_provider("gemini", p2)

        res = await router.execute_with_failover("Compute variance")
        assert res.success is True
        assert res.provider_name == "gemini"
        assert res.failover_occurred is True
    asyncio.run(_run())


def test_case_04_primary_http_500_failover():
    async def _run():
        router = ProviderRouter()
        p1 = MockAIProvider("ollama", "Ollama", ProviderType.LOCAL, fail_with_status=ProviderStatus.ERROR, fail_error_message="HTTP 500 Internal Error")
        p2 = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, response_text="Gemini fallback response")
        router.register_provider("ollama", p1)
        router.register_provider("gemini", p2)

        res = await router.execute_with_failover("Audit finding summary")
        assert res.success is True
        assert res.provider_name == "gemini"
    asyncio.run(_run())


def test_case_05_circuit_breaker_open_skips_primary():
    async def _run():
        router = ProviderRouter()
        p1 = MockAIProvider("ollama", "Ollama", ProviderType.LOCAL, fail_with_status=ProviderStatus.TIMEOUT)
        p2 = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, response_text="Gemini ok")
        router.register_provider("ollama", p1)
        router.register_provider("gemini", p2)

        # Trip the circuit breaker for ollama with 3 consecutive failures
        router.quota_manager.record_failure("ollama", ProviderStatus.TIMEOUT, "Trip 1")
        router.quota_manager.record_failure("ollama", ProviderStatus.TIMEOUT, "Trip 2")
        router.quota_manager.record_failure("ollama", ProviderStatus.TIMEOUT, "Trip 3")

        state = router.quota_manager.get_circuit_state("ollama")
        assert state == CircuitState.OPEN

        # Execution should skip calling p1 completely
        p1_calls_before = p1.call_count
        res = await router.execute_with_failover("Fast query")
        assert res.success is True
        assert res.provider_name == "gemini"
        assert p1.call_count == p1_calls_before  # Not called because circuit is OPEN
    asyncio.run(_run())


def test_case_06_cloud_mode_gemini_429_failover_to_groq(monkeypatch):
    async def _run():
        monkeypatch.setattr(ProviderConfig, "MODE", "cloud")
        router = ProviderRouter()
        p_gemini = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, fail_with_status=ProviderStatus.RATE_LIMITED, fail_error_message="Gemini quota exhausted 429")
        p_groq = MockAIProvider("groq", "Groq", ProviderType.CLOUD, response_text="Groq fast response")
        router.register_provider("gemini", p_gemini)
        router.register_provider("groq", p_groq)

        res = await router.execute_with_failover("Analyze tax rate")
        assert res.success is True
        assert res.provider_name == "groq"
        assert res.failover_occurred is True
    asyncio.run(_run())


def test_case_07_cloud_mode_gemini_timeout_failover_to_groq(monkeypatch):
    async def _run():
        monkeypatch.setattr(ProviderConfig, "MODE", "cloud")
        router = ProviderRouter()
        p_gemini = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, fail_with_status=ProviderStatus.TIMEOUT)
        p_groq = MockAIProvider("groq", "Groq", ProviderType.CLOUD, response_text="Groq ok")
        router.register_provider("gemini", p_gemini)
        router.register_provider("groq", p_groq)

        res = await router.execute_with_failover("Analyze cross-year journals")
        assert res.success is True
        assert res.provider_name == "groq"
    asyncio.run(_run())


def test_case_08_cloud_mode_groq_timeout_failover_to_nvidia(monkeypatch):
    async def _run():
        monkeypatch.setattr(ProviderConfig, "MODE", "cloud")
        router = ProviderRouter()
        p_gemini = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, fail_with_status=ProviderStatus.TIMEOUT)
        p_groq = MockAIProvider("groq", "Groq", ProviderType.CLOUD, fail_with_status=ProviderStatus.TIMEOUT)
        p_nvidia = MockAIProvider("nvidia_nim", "Nvidia NIM", ProviderType.CLOUD, response_text="Nemotron 70B conclusion")
        router.register_provider("gemini", p_gemini)
        router.register_provider("groq", p_groq)
        router.register_provider("nvidia_nim", p_nvidia)

        res = await router.execute_with_failover("Deep audit investigation")
        assert res.success is True
        assert res.provider_name == "nvidia_nim"
        assert len(res.failover_history) >= 2
    asyncio.run(_run())


def test_case_09_all_providers_fail_clean_error():
    async def _run():
        router = ProviderRouter()
        p1 = MockAIProvider("ollama", "Ollama", ProviderType.LOCAL, fail_with_status=ProviderStatus.TIMEOUT)
        p2 = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, fail_with_status=ProviderStatus.ERROR)
        p3 = MockAIProvider("groq", "Groq", ProviderType.CLOUD, fail_with_status=ProviderStatus.RATE_LIMITED)
        p4 = MockAIProvider("nvidia_nim", "Nvidia", ProviderType.CLOUD, fail_with_status=ProviderStatus.AUTH_ERROR)
        router.register_provider("ollama", p1)
        router.register_provider("gemini", p2)
        router.register_provider("groq", p3)
        router.register_provider("nvidia_nim", p4)

        res = await router.execute_with_failover("Exhaustion test")
        assert res.success is False
        assert "All configured providers exhausted" in res.error_message
        assert res.failover_occurred is True
    asyncio.run(_run())


def test_case_10_data_governance_confidential_blocks_cloud(monkeypatch):
    async def _run():
        monkeypatch.setattr(ProviderConfig, "ALLOW_CONFIDENTIAL_EXTERNAL_DATA", False)
        router = ProviderRouter()
        # Unconfigured local provider + configured cloud providers
        p_local = MockAIProvider("ollama", "Ollama", ProviderType.LOCAL, configured=False)
        p_cloud = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, response_text="Leaked confidential data")
        router.register_provider("ollama", p_local)
        router.register_provider("gemini", p_cloud)

        res = await router.execute_with_failover("Top secret payroll vouchers", confidential=True)
        assert res.success is False
        assert "DATA GOVERNANCE GUARD" in res.error_message
        assert p_cloud.call_count == 0  # Cloud was strictly protected from confidential data
    asyncio.run(_run())


def test_case_11_data_governance_confidential_allowed_when_flag_true(monkeypatch):
    async def _run():
        monkeypatch.setattr(ProviderConfig, "ALLOW_CONFIDENTIAL_EXTERNAL_DATA", True)
        router = ProviderRouter()
        p_local = MockAIProvider("ollama", "Ollama", ProviderType.LOCAL, configured=False)
        p_cloud = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, response_text="Allowed with explicit config")
        router.register_provider("ollama", p_local)
        router.register_provider("gemini", p_cloud)

        res = await router.execute_with_failover("Ledger analysis", confidential=True)
        assert res.success is True
        assert res.provider_name == "gemini"
    asyncio.run(_run())


def test_case_12_circuit_breaker_half_open_state():
    qm = QuotaManager(failure_threshold=2, cooldown_seconds=0.1)
    qm.record_failure("test_p", ProviderStatus.ERROR, "Fail 1")
    qm.record_failure("test_p", ProviderStatus.ERROR, "Fail 2")
    assert qm.get_circuit_state("test_p") == CircuitState.OPEN

    # Sleep past cooldown
    time.sleep(0.12)
    assert qm.get_circuit_state("test_p") == CircuitState.HALF_OPEN


def test_case_13_circuit_breaker_resets_on_success():
    qm = QuotaManager(failure_threshold=3, cooldown_seconds=60.0)
    qm.record_failure("test_p", ProviderStatus.TIMEOUT, "Timeout 1")
    qm.record_failure("test_p", ProviderStatus.TIMEOUT, "Timeout 2")
    assert qm.get_status_info("test_p")["consecutive_failures"] == 2

    qm.record_success("test_p")
    assert qm.get_status_info("test_p")["consecutive_failures"] == 0
    assert qm.get_circuit_state("test_p") == CircuitState.CLOSED


def test_case_14_response_normalizer_json_extraction():
    # Case A: Plain JSON
    a = ResponseNormalizer.extract_json('{"key": "value", "amount": 1000}')
    assert a == {"key": "value", "amount": 1000}

    # Case B: Markdown code fence ```json ... ```
    b = ResponseNormalizer.extract_json('Here is the finding:\n```json\n{"anomaly": "ITC_MISMATCH", "val": 500}\n```\nDone.')
    assert b == {"anomaly": "ITC_MISMATCH", "val": 500}

    # Case C: Embedded brackets in messy text
    c = ResponseNormalizer.extract_json('Noise {"inner": true} trailing noise')
    assert c == {"inner": True}

    # Case D: Malformed text returns None without crashing
    d = ResponseNormalizer.extract_json('Just plain English without JSON.')
    assert d is None


def test_case_15_quota_manager_retry_after():
    qm = QuotaManager(failure_threshold=3, cooldown_seconds=60.0)
    qm.record_failure("p_rate", ProviderStatus.RATE_LIMITED, "Rate limit", retry_after=30.0)
    can_exec, msg = qm.can_execute("p_rate")
    assert can_exec is False
    assert "Retry in" in msg


def test_case_16_non_retryable_validation_check():
    p = MockAIProvider("mock", "Mock", ProviderType.LOCAL)
    valid_resp = ProviderResponse(text="Valid text", success=True)
    invalid_resp = ProviderResponse(text="   ", success=True)
    failed_resp = ProviderResponse(text="Error", success=False)

    assert p.validate_response(valid_resp) is True
    assert p.validate_response(invalid_resp) is False
    assert p.validate_response(failed_resp) is False


def test_case_17_health_check_reports_accurate_status():
    async def _run():
        router = ProviderRouter()
        p1 = MockAIProvider("ollama", "Ollama", ProviderType.LOCAL)
        p2 = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, configured=False)
        router.register_provider("ollama", p1)
        router.register_provider("gemini", p2)

        health = await ProviderHealthChecker.check_all(router)
        assert "providers" in health
        assert health["providers"]["ollama"]["status"] == "AVAILABLE"
        assert health["providers"]["gemini"]["status"] == "NOT_CONFIGURED"
    asyncio.run(_run())


def test_case_18_health_check_status_healthy_with_one_available():
    async def _run():
        router = ProviderRouter()
        p1 = MockAIProvider("ollama", "Ollama", ProviderType.LOCAL)
        p2 = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, fail_with_status=ProviderStatus.AUTH_ERROR)
        router.register_provider("ollama", p1)
        router.register_provider("gemini", p2)

        health = await ProviderHealthChecker.check_all(router)
        assert health["status"] == "healthy"
        assert health["available_providers"] == 1
    asyncio.run(_run())


def test_case_19_health_check_status_unconfigured():
    async def _run():
        router = ProviderRouter()
        p1 = MockAIProvider("ollama", "Ollama", ProviderType.LOCAL, configured=False)
        p2 = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, configured=False)
        router.register_provider("ollama", p1)
        router.register_provider("gemini", p2)

        health = await ProviderHealthChecker.check_all(router)
        assert health["status"] == "unconfigured"
        assert health["configured_providers"] == 0
    asyncio.run(_run())


def test_case_20_health_decouples_ollama_from_core_readiness():
    from backend.app.api.health import get_health
    # get_health should execute cleanly and report status
    res = get_health()
    assert "status" in res
    assert "inference" in res
    assert res["inference"]["cloud_failover_enabled"] is True
    assert res["inference"]["deterministic_arithmetic_engine"] == "READY"


def test_case_21_multiprovider_preserves_query_context():
    async def _run():
        router = ProviderRouter()
        query = "Audit Section 115BAA corporate tax verification for ₹5,00,00,000"
        p = MockAIProvider("gemini", "Gemini", ProviderType.CLOUD, response_text=f"Processed: {query}")
        router.register_provider("gemini", p)

        res = await router.execute_with_failover(query)
        assert query in res.text
    asyncio.run(_run())


def test_case_22_admin_summary_reflects_circuit_and_failover_trail():
    router = ProviderRouter()
    router.failover_manager.record_failover(
        from_provider="ollama",
        to_provider="gemini",
        reason="Socket timeout test",
        status=ProviderStatus.TIMEOUT,
        latency_ms=15.2,
    )
    summary = router.get_status_summary()
    assert "mode" in summary
    assert "providers" in summary
    assert "recent_failovers" in summary
    assert len(summary["recent_failovers"]) >= 1
    assert summary["recent_failovers"][0]["from_provider"] == "ollama"
    assert summary["recent_failovers"][0]["to_provider"] == "gemini"
