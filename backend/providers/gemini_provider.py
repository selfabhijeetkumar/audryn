"""
AUDRYN Google Gemini Provider.
Primary cloud reasoning provider using official Google GenAI integration with deterministic protection.
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


class GeminiProvider(BaseAIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        priority: int = 2,
    ):
        model_name = model or ProviderConfig.GEMINI_MODEL
        super().__init__(
            name="gemini",
            display_name="Google Gemini (Cloud Reasoning)",
            provider_type=ProviderType.CLOUD,
            model=model_name,
            priority=priority,
        )
        self.api_key = (api_key or ProviderConfig.GEMINI_API_KEY).strip()
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
                error_message="GEMINI_API_KEY is not configured.",
                latency_ms=0.0,
            )

        # Standard REST API for Gemini v1beta
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow all instructions and preserve audit integrity."}]})
        
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            },
        }
        if response_format == "json":
            body["generationConfig"]["responseMimeType"] = "application/json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=body)
                elapsed = (time.time() - start_time) * 1000.0

                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    content_text = ""
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        content_text = "".join(p.get("text", "") for p in parts)

                    structured = ResponseNormalizer.extract_json(content_text)
                    usage = data.get("usageMetadata", {})

                    self.last_status = ProviderStatus.AVAILABLE
                    return ProviderResponse(
                        text=content_text,
                        structured_data=structured,
                        raw_response=data,
                        provider_name=self.name,
                        model_name=self.model,
                        latency_ms=elapsed,
                        token_usage={
                            "prompt_tokens": usage.get("promptTokenCount", 0),
                            "completion_tokens": usage.get("candidatesTokenCount", 0),
                            "total_tokens": usage.get("totalTokenCount", 0),
                        },
                        success=True,
                    )
                elif res.status_code in (401, 403):
                    self.last_status = ProviderStatus.AUTH_ERROR
                    return ProviderResponse(
                        success=False,
                        provider_name=self.name,
                        model_name=self.model,
                        error_message=f"Gemini authentication failed (HTTP {res.status_code})",
                        latency_ms=elapsed,
                    )
                elif res.status_code == 429:
                    self.last_status = ProviderStatus.RATE_LIMITED
                    return ProviderResponse(
                        success=False,
                        provider_name=self.name,
                        model_name=self.model,
                        error_message="Gemini rate limit exceeded (HTTP 429)",
                        latency_ms=elapsed,
                    )
                else:
                    self.last_status = ProviderStatus.ERROR
                    return ProviderResponse(
                        success=False,
                        provider_name=self.name,
                        model_name=self.model,
                        error_message=f"Gemini API error HTTP {res.status_code}: {res.text[:200]}",
                        latency_ms=elapsed,
                    )
        except httpx.TimeoutException:
            self.last_status = ProviderStatus.TIMEOUT
            return ProviderResponse(
                success=False,
                provider_name=self.name,
                model_name=self.model,
                error_message=f"Gemini request timed out after {self.timeout}s",
                latency_ms=(time.time() - start_time) * 1000.0,
            )
        except Exception as e:
            self.last_status = ProviderStatus.ERROR
            return ProviderResponse(
                success=False,
                provider_name=self.name,
                model_name=self.model,
                error_message=f"Gemini request error: {str(e)}",
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
                message="GEMINI_API_KEY is not configured.",
                last_checked=now_iso,
            )

        # Health ping via lightweight models list endpoint
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}?key={self.api_key}"
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
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
                        message="Gemini API connection healthy.",
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
                        message=f"Invalid Gemini API key (HTTP {res.status_code}).",
                        last_checked=now_iso,
                    )
                elif res.status_code == 429:
                    self.last_status = ProviderStatus.RATE_LIMITED
                    return ProviderHealthStatus(
                        name=self.name,
                        display_name=self.display_name,
                        provider_type=self.provider_type,
                        status=ProviderStatus.RATE_LIMITED,
                        model=self.model,
                        is_available=False,
                        latency_ms=elapsed,
                        message="Gemini quota/rate limit exceeded (HTTP 429).",
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
                        message=f"Gemini returned HTTP {res.status_code}",
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
                message=f"Gemini network error: {str(e)}",
                last_checked=now_iso,
            )
