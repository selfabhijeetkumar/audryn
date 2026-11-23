"""
AUDRYN NVIDIA NIM Provider.
Enterprise AI inference adapter for NVIDIA Nemotron models hosted on NVIDIA NIM.
"""
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx

from backend.providers.base import (
    BaseAIProvider,
    ProviderResponse,
    ProviderHealthStatus,
    ProviderStatus,
    ProviderType,
)
from backend.providers.config import ProviderConfig
from backend.providers.response_normalizer import ResponseNormalizer


class NvidiaNimProvider(BaseAIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        priority: int = 4,
    ):
        model_name = model or ProviderConfig.NVIDIA_NIM_MODEL
        super().__init__(
            name="nvidia_nim",
            display_name="NVIDIA NIM (Nemotron Reasoning)",
            provider_type=ProviderType.CLOUD,
            model=model_name,
            priority=priority,
        )
        self.api_key = (api_key or ProviderConfig.NVIDIA_NIM_API_KEY).strip()
        self.base_url = (base_url or ProviderConfig.NVIDIA_NIM_BASE_URL).rstrip("/")
        self.timeout = ProviderConfig.REQUEST_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        response_format: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        start_time = time.time()
        if not self.is_configured():
            return ProviderResponse(
                success=False,
                provider_name=self.name,
                model_name=self.model,
                error_message="NVIDIA_NIM_API_KEY is not configured.",
                latency_ms=0.0,
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                elapsed = (time.time() - start_time) * 1000.0

                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    content = choices[0].get("message", {}).get("content", "") if choices else ""
                    structured = ResponseNormalizer.extract_json(content)
                    usage = data.get("usage", {})

                    self.last_status = ProviderStatus.AVAILABLE
                    return ProviderResponse(
                        text=content,
                        structured_data=structured,
                        raw_response=data,
                        provider_name=self.name,
                        model_name=self.model,
                        latency_ms=elapsed,
                        token_usage={
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "total_tokens": usage.get("total_tokens", 0),
                        },
                        success=True,
                    )
                elif res.status_code in (401, 403):
                    self.last_status = ProviderStatus.AUTH_ERROR
                    return ProviderResponse(
                        success=False,
                        provider_name=self.name,
                        model_name=self.model,
                        error_message=f"NVIDIA NIM auth error (HTTP {res.status_code})",
                        latency_ms=elapsed,
                    )
                elif res.status_code == 429:
                    self.last_status = ProviderStatus.RATE_LIMITED
                    return ProviderResponse(
                        success=False,
                        provider_name=self.name,
                        model_name=self.model,
                        error_message="NVIDIA NIM rate limit exceeded (HTTP 429)",
                        latency_ms=elapsed,
                    )
                else:
                    self.last_status = ProviderStatus.ERROR
                    return ProviderResponse(
                        success=False,
                        provider_name=self.name,
                        model_name=self.model,
                        error_message=f"NVIDIA NIM error HTTP {res.status_code}: {res.text[:200]}",
                        latency_ms=elapsed,
                    )
        except httpx.TimeoutException:
            self.last_status = ProviderStatus.TIMEOUT
            return ProviderResponse(
                success=False,
                provider_name=self.name,
                model_name=self.model,
                error_message=f"NVIDIA NIM request timed out after {self.timeout}s",
                latency_ms=(time.time() - start_time) * 1000.0,
            )
        except Exception as e:
            self.last_status = ProviderStatus.ERROR
            return ProviderResponse(
                success=False,
                provider_name=self.name,
                model_name=self.model,
                error_message=f"NVIDIA NIM request error: {str(e)}",
                latency_ms=(time.time() - start_time) * 1000.0,
            )

    async def health_check(self) -> ProviderHealthStatus:
        now_iso = datetime.now(timezone.utc).isoformat()
        start = time.time()

        if not self.is_configured():
            return ProviderHealthStatus(
                name=self.name,
                display_name=self.display_name,
                provider_type=self.provider_type,
                status=ProviderStatus.NOT_CONFIGURED,
                model=self.model,
                is_available=False,
                latency_ms=0.0,
                message="NVIDIA_NIM_API_KEY is not configured.",
                last_checked=now_iso,
            )

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/models", headers=headers)
                elapsed = (time.time() - start) * 1000.0
                if res.status_code == 200:
                    self.last_status = ProviderStatus.AVAILABLE
                    return ProviderHealthStatus(
                        name=self.name,
                        display_name=self.display_name,
                        provider_type=self.provider_type,
                        status=ProviderStatus.AVAILABLE,
                        model=self.model,
                        is_available=True,
                        latency_ms=elapsed,
                        message="NVIDIA NIM active.",
                        last_checked=now_iso,
                    )
                elif res.status_code in (401, 403):
                    self.last_status = ProviderStatus.AUTH_ERROR
                    return ProviderHealthStatus(
                        name=self.name,
                        display_name=self.display_name,
                        provider_type=self.provider_type,
                        status=ProviderStatus.AUTH_ERROR,
                        model=self.model,
                        is_available=False,
                        latency_ms=elapsed,
                        message=f"Invalid NVIDIA NIM API key (HTTP {res.status_code}).",
                        last_checked=now_iso,
                    )
                else:
                    self.last_status = ProviderStatus.DEGRADED
                    return ProviderHealthStatus(
                        name=self.name,
                        display_name=self.display_name,
                        provider_type=self.provider_type,
                        status=ProviderStatus.DEGRADED,
                        model=self.model,
                        is_available=False,
                        latency_ms=elapsed,
                        message=f"NVIDIA NIM returned HTTP {res.status_code}",
                        last_checked=now_iso,
                    )
        except Exception as e:
            self.last_status = ProviderStatus.ERROR
            return ProviderHealthStatus(
                name=self.name,
                display_name=self.display_name,
                provider_type=self.provider_type,
                status=ProviderStatus.ERROR,
                model=self.model,
                is_available=False,
                latency_ms=(time.time() - start) * 1000.0,
                message=f"NVIDIA NIM connection error: {str(e)}",
                last_checked=now_iso,
            )
