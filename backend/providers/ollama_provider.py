"""
AUDRYN Ollama Provider.
Local on-premise inference adapter for qwen3:4b with loopback safety in cloud environments.
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


class OllamaProvider(BaseAIProvider):
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        priority: int = 1,
    ):
        model_name = model or ProviderConfig.OLLAMA_MODEL
        super().__init__(
            name="ollama",
            display_name="Ollama (Local Private Inference)",
            provider_type=ProviderType.LOCAL,
            model=model_name,
            priority=priority,
        )
        self.base_url = (base_url or ProviderConfig.OLLAMA_BASE_URL).rstrip("/")
        self.timeout = ProviderConfig.REQUEST_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        # In cloud environments (Render, Vercel), local loopback is suppressed for safety
        if ProviderConfig.is_cloud_env and ("127.0.0.1" in self.base_url or "localhost" in self.base_url):
            return False
        return bool(self.base_url)

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
                error_message="Ollama loopback disabled in cloud deployment or unconfigured.",
                latency_ms=0.0,
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model.replace("ollama/", ""),
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if response_format == "json":
            payload["format"] = "json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                elapsed = (time.time() - start_time) * 1000.0

                if res.status_code == 200:
                    data = res.json()
                    content = data.get("message", {}).get("content", "")
                    structured = ResponseNormalizer.extract_json(content)
                    self.last_status = ProviderStatus.AVAILABLE
                    return ProviderResponse(
                        text=content,
                        structured_data=structured,
                        raw_response=data,
                        provider_name=self.name,
                        model_name=self.model,
                        latency_ms=elapsed,
                        token_usage={
                            "prompt_tokens": data.get("prompt_eval_count", 0),
                            "completion_tokens": data.get("eval_count", 0),
                        },
                        success=True,
                    )
                else:
                    self.last_status = ProviderStatus.ERROR
                    return ProviderResponse(
                        success=False,
                        provider_name=self.name,
                        model_name=self.model,
                        error_message=f"Ollama returned HTTP {res.status_code}: {res.text}",
                        latency_ms=elapsed,
                    )
        except httpx.TimeoutException:
            self.last_status = ProviderStatus.TIMEOUT
            return ProviderResponse(
                success=False,
                provider_name=self.name,
                model_name=self.model,
                error_message=f"Ollama connection timed out after {self.timeout}s",
                latency_ms=(time.time() - start_time) * 1000.0,
            )
        except Exception as e:
            self.last_status = ProviderStatus.ERROR
            return ProviderResponse(
                success=False,
                provider_name=self.name,
                model_name=self.model,
                error_message=f"Ollama connection error: {str(e)}",
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
                message="Localhost inference suppressed in cloud environment or unconfigured.",
                last_checked=now_iso,
            )

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                elapsed = (time.time() - start) * 1000.0
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    self.last_status = ProviderStatus.AVAILABLE
                    return ProviderHealthStatus(
                        name=self.name,
                        display_name=self.display_name,
                        provider_type=self.provider_type,
                        status=ProviderStatus.AVAILABLE,
                        model=self.model,
                        is_available=True,
                        latency_ms=elapsed,
                        message=f"Ollama active ({len(models)} models installed).",
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
                        message=f"Ollama HTTP {res.status_code}",
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
                message=f"Cannot connect to Ollama at {self.base_url}: {str(e)}",
                last_checked=now_iso,
            )
