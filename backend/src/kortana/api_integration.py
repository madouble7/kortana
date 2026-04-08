"""
KOR'TANA API Integration Layer

Bridges the cost-optimized model router to actual API providers.
Handles real API calls with fallback chains and cost tracking.
"""

from __future__ import annotations

import asyncio
from typing import Protocol

import aiohttp
import httpx

from src.kortana.adaptive_retry_engine import get_adaptive_retry_engine
from src.kortana.cost_optimized_model_router import (
    ModelProvider,
    TaskType,
    get_cost_optimized_model_router,
)
from src.kortana.logger import get_logger
from src.kortana.model_lane_policy import (
    describe_model_lane,
    get_active_model_lane,
    model_allowed,
)
from src.kortana.model_usage_telemetry import get_model_usage_telemetry
from src.kortana.openai_responses import async_generate_text
from src.kortana.provider_model_defaults import API_INTEGRATION_FALLBACK_DEFAULTS
from src.kortana.services.gemini_config import (
    get_model_name,
    get_preferred_model_name,
)

logger = get_logger(__name__)


class ProviderRateLimitError(Exception):
    """Raised when an upstream provider reports a rate limit or quota exhaustion."""

    def __init__(
        self,
        provider: ModelProvider | str,
        message: str,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = (
            provider if isinstance(provider, str) else provider.value
        )
        self.retry_after_seconds = retry_after_seconds


def _parse_retry_after_seconds(value: str | None) -> int | None:
    """Return integer Retry-After seconds when present and valid."""
    if not value:
        return None

    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return None

    return seconds if seconds >= 0 else None


def _resolve_allowed_model_name(
    requested_model_name: str | None,
    *,
    default_model_name: str,
    provider_name: str,
) -> str:
    candidate = (requested_model_name or default_model_name).strip()
    if model_allowed(candidate):
        return candidate

    logger.warning(
        "Requested %s model '%s' is unavailable under the %s runtime lane; "
        "falling back to '%s' (%s lane)",
        provider_name,
        candidate,
        get_active_model_lane().value,
        default_model_name,
        describe_model_lane(default_model_name),
    )
    return default_model_name


class SupportsGenerationClient(Protocol):
    """Client contract for provider-specific generation adapters."""

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> tuple[str, int, int]: ...


class GroqAPIClient:
    """Groq API client (free, unlimited, fast)"""

    def __init__(self, api_key: str, model_name: str | None = None):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = _resolve_allowed_model_name(
            model_name,
            default_model_name=API_INTEGRATION_FALLBACK_DEFAULTS.groq,
            provider_name="groq",
        )

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> tuple[str, int, int]:
        """
        Generate text using Groq API.

        Returns: (text, input_tokens, output_tokens)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        usage = data["usage"]
                        return (
                            content,
                            usage["prompt_tokens"],
                            usage["completion_tokens"],
                        )
                    error_text = await response.text()
                    if response.status == 429:
                        raise ProviderRateLimitError(
                            ModelProvider.GROQ,
                            f"Groq API rate limit: {error_text}",
                            retry_after_seconds=_parse_retry_after_seconds(
                                response.headers.get("Retry-After")
                            ),
                        )
                    raise Exception(f"Groq API error {response.status}: {error_text}")
        except asyncio.TimeoutError:
            raise Exception("Groq API request timeout")
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise


class GeminiAPIClient:
    """Gemini API client (free, quota-limited)"""

    def __init__(self, api_key: str, model_name: str | None = None):
        self.api_key = api_key
        self.model = (
            get_preferred_model_name(model_name)
            if model_name is not None
            else get_model_name()
        )

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> tuple[str, int, int]:
        """
        Generate text using Gemini API.

        Returns: (text, input_tokens, output_tokens)
        """
        try:
            # Use Google's generative AI client
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
                stream=False,
            )

            content = response.text
            # Estimate tokens (Gemini doesn't always return exact counts)
            input_tokens = len(prompt.split()) * 1.3
            output_tokens = len(content.split()) * 1.3

            return content, int(input_tokens), int(output_tokens)

        except Exception as e:
            message = str(e).lower()
            if "429" in message or "quota" in message or "rate limit" in message:
                raise ProviderRateLimitError(
                    ModelProvider.GEMINI,
                    f"Gemini API rate limit: {e}",
                ) from e
            logger.error(f"Gemini API error: {e}")
            raise


class ClaudeAPIClient:
    """Claude API client (premium, for critical decisions)"""

    def __init__(self, api_key: str, model_name: str | None = None):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.model = _resolve_allowed_model_name(
            model_name,
            default_model_name=API_INTEGRATION_FALLBACK_DEFAULTS.anthropic,
            provider_name="anthropic",
        )

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> tuple[str, int, int]:
        """
        Generate text using Claude API.

        Returns: (text, input_tokens, output_tokens)
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["content"][0]["text"]
                        usage = data["usage"]
                        return (
                            content,
                            usage["input_tokens"],
                            usage["output_tokens"],
                        )
                    error_text = await response.text()
                    if response.status == 429:
                        raise ProviderRateLimitError(
                            ModelProvider.CLAUDE,
                            f"Claude API rate limit: {error_text}",
                            retry_after_seconds=_parse_retry_after_seconds(
                                response.headers.get("Retry-After")
                            ),
                        )
                    raise Exception(f"Claude API error {response.status}: {error_text}")
        except asyncio.TimeoutError:
            raise Exception("Claude API request timeout")
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise


class OpenAIAPIClient:
    """OpenAI API client (expensive, fallback)"""

    def __init__(self, api_key: str, model_name: str | None = None):
        self.api_key = api_key
        self.model = _resolve_allowed_model_name(
            model_name,
            default_model_name=API_INTEGRATION_FALLBACK_DEFAULTS.openai,
            provider_name="openai",
        )

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> tuple[str, int, int]:
        """
        Generate text using OpenAI API.

        Returns: (text, input_tokens, output_tokens)
        """
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=self.api_key,
                http_client=httpx.AsyncClient(timeout=30.0),
            )

            try:
                content, input_tokens, output_tokens = await async_generate_text(
                    client,
                    model_name=self.model,
                    prompt=prompt,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    timeout=30.0,
                )
            finally:
                await client.close()

            return (
                content,
                input_tokens or 0,
                output_tokens or 0,
            )

        except Exception as e:
            status_code = getattr(e, "status_code", None)
            if status_code == 429:
                retry_after = None
                response = getattr(e, "response", None)
                if response is not None:
                    retry_after = _parse_retry_after_seconds(
                        response.headers.get("retry-after")
                    )
                raise ProviderRateLimitError(
                    ModelProvider.OPENAI,
                    f"OpenAI API rate limit: {e}",
                    retry_after_seconds=retry_after,
                ) from e
            logger.error(f"OpenAI API error: {e}")
            raise


class UnifiedAPIClient:
    """
    Unified client that coordinates across all API providers.
    Automatically selects optimal provider and handles fallback chains.
    """

    def __init__(self) -> None:
        self.router = get_cost_optimized_model_router()
        self.retry_engine = get_adaptive_retry_engine()
        self.clients: dict[ModelProvider, SupportsGenerationClient] = {}
        self._init_clients()

    def _init_clients(self) -> None:
        """Initialize all available API clients"""
        for provider, config in self.router.configs.items():
            if provider == ModelProvider.GROQ:
                self.clients[provider] = GroqAPIClient(config.api_key, config.model_name)
            elif provider == ModelProvider.GEMINI:
                self.clients[provider] = GeminiAPIClient(
                    config.api_key, config.model_name
                )
            elif provider == ModelProvider.CLAUDE:
                self.clients[provider] = ClaudeAPIClient(
                    config.api_key, config.model_name
                )
            elif provider == ModelProvider.OPENAI:
                self.clients[provider] = OpenAIAPIClient(
                    config.api_key, config.model_name
                )

    async def generate(
        self,
        prompt: str,
        task_type: TaskType,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        budget_limit: float = 0.01,
    ) -> tuple[str, ModelProvider, float]:
        """
        Generate text with automatic provider selection and fallback.

        Returns: (content, provider_used, cost)
        """
        # Get optimal provider chain
        providers = self.router.select_for_task(task_type, budget_limit)
        failure_reasons: list[str] = []

        for provider in providers:
            client = self.clients.get(provider)
            if not client:
                continue

            attempt_number = 0
            operation_id = f"{provider.value}:{task_type.value}"

            while True:
                try:
                    logger.info(f"Attempting {provider.value} for {task_type.value}")

                    content, input_tokens, output_tokens = await client.generate(
                        prompt, max_tokens, temperature
                    )

                    # Record usage and calculate cost
                    cost = self.router.estimate_cost(
                        provider, task_type, input_tokens, output_tokens
                    )
                    self.router.record_usage(
                        provider, task_type, input_tokens, output_tokens
                    )
                    model_name = getattr(client, "model", None)
                    if not model_name:
                        config = self.router.configs.get(provider)
                        model_name = (
                            config.model_name if config is not None else "unknown"
                        )
                    get_model_usage_telemetry().record_generation(
                        subsystem="api_integration",
                        provider=provider.value,
                        model=model_name,
                        catalog="cost_router_defaults",
                        selection=f"task:{task_type.value}",
                        runtime_lane=self.router.model_usage_lane.value,
                        tokens_used=input_tokens + output_tokens,
                        task_type=task_type.value,
                    )

                    logger.info(
                        f"✅ Success with {provider.value} "
                        f"(${cost:.4f}, {len(content)} chars)"
                    )
                    return content, provider, cost

                except ProviderRateLimitError as e:
                    self.retry_engine.record_retry(
                        operation_id,
                        e,
                        attempt_number,
                        will_retry=False,
                        provider=provider.value,
                        task_type=task_type.value,
                    )
                    self.router.mark_rate_limited(
                        provider,
                        retry_after_seconds=e.retry_after_seconds,
                        reason=str(e),
                    )
                    failure_reasons.append(f"{provider.value}: rate limited")
                    logger.warning(
                        "Provider %s rate limited: %s. Trying next...",
                        provider.value,
                        e,
                    )
                    break
                except Exception as e:
                    status_code = getattr(e, "status_code", None)
                    should_retry = self.retry_engine.should_retry(
                        e,
                        attempt_number,
                        status_code=status_code,
                    )
                    delay_seconds = None
                    if should_retry:
                        delay_seconds = self.retry_engine.get_retry_delay(
                            e,
                            attempt_number,
                            status_code=status_code,
                        )
                    self.retry_engine.record_retry(
                        operation_id,
                        e,
                        attempt_number,
                        will_retry=should_retry,
                        delay_seconds=delay_seconds,
                        provider=provider.value,
                        task_type=task_type.value,
                    )
                    if should_retry and delay_seconds is not None:
                        logger.warning(
                            "Provider %s failed with %s. Retrying in %.2fs...",
                            provider.value,
                            e,
                            delay_seconds,
                        )
                        attempt_number += 1
                        await asyncio.sleep(delay_seconds)
                        continue

                    self.router.record_provider_failure(provider, str(e))
                    failure_reasons.append(f"{provider.value}: {e}")
                    logger.warning(
                        f"Provider {provider.value} failed: {e}. " f"Trying next..."
                    )
                    break

        # All providers failed
        if failure_reasons:
            raise Exception(
                f"All providers exhausted for {task_type.value}: "
                + "; ".join(failure_reasons)
            )
        raise Exception(f"All providers exhausted for {task_type.value}")

    def get_cost_report(self) -> dict[str, object]:
        """Get current cost tracking"""
        return self.router.get_cost_report()

    def get_routing_info(self) -> dict[str, object]:
        """Get routing strategy info"""
        return self.router.get_routing_strategy()
