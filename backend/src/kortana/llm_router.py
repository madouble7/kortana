"""
LLM Provider Router - Multi-model fallback strategy
Handles Gemini, OpenAI, Anthropic, Groq with intelligent routing and fallbacks
"""

import asyncio
import time
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel

from src.kortana.config import get_settings
from src.kortana.logger import log_error, log_request
from src.kortana.model_lane_policy import (
    describe_model_lane,
    get_active_model_lane,
    model_allowed,
)
from src.kortana.model_usage_telemetry import get_model_usage_telemetry
from src.kortana.provider_model_defaults import (
    LLM_ROUTER_DEFAULTS,
    LLM_ROUTER_FALLBACK_ORDER,
)


class ModelProvider(str, Enum):
    """Supported LLM providers"""

    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OPENROUTER = "openrouter"


class ModelConfig(BaseModel):
    """Configuration for a language model"""

    provider: ModelProvider
    model_name: str
    api_key: Optional[str]
    base_url: Optional[str] = None
    timeout: int = 30
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    enabled: bool = True
    lane: str = "core"


class LLMResponse(BaseModel):
    """Standardized LLM response"""

    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    latency_ms: int = 0
    temperature: float


class LLMRouter:
    """Intelligent routing across multiple LLM providers with fallbacks"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_usage_lane = get_active_model_lane(self.settings)
        self.models: dict[str, ModelConfig] = self._initialize_models()
        self.primary_model: Optional[ModelConfig] = self._get_primary_model()
        self.fallback_models: list[ModelConfig] = self._get_fallback_models()

    def _initialize_models(self) -> dict[str, ModelConfig]:
        """Initialize available models from settings"""
        models: dict[str, ModelConfig] = {}

        # Gemini (primary)
        if self.settings.GEMINI_API_KEY:
            self._register_model(
                models,
                LLM_ROUTER_DEFAULTS.gemini,
                ModelConfig(
                    provider=ModelProvider.GEMINI,
                    model_name=LLM_ROUTER_DEFAULTS.gemini,
                    api_key=self.settings.GEMINI_API_KEY,
                    max_tokens=8000,
                    temperature=0.7,
                ),
            )

        # OpenAI
        if self.settings.OPENAI_API_KEY:
            self._register_model(
                models,
                LLM_ROUTER_DEFAULTS.openai,
                ModelConfig(
                    provider=ModelProvider.OPENAI,
                    model_name=LLM_ROUTER_DEFAULTS.openai,
                    api_key=self.settings.OPENAI_API_KEY,
                    max_tokens=4096,
                    temperature=0.7,
                ),
            )

        # Groq (fast, low-cost)
        if self.settings.GROQ_API_KEY:
            self._register_model(
                models,
                LLM_ROUTER_DEFAULTS.groq,
                ModelConfig(
                    provider=ModelProvider.GROQ,
                    model_name=LLM_ROUTER_DEFAULTS.groq,
                    api_key=self.settings.GROQ_API_KEY,
                    timeout=15,
                    max_tokens=2048,
                    temperature=0.7,
                ),
            )

        # Anthropic
        if self.settings.ANTHROPIC_API_KEY:
            self._register_model(
                models,
                LLM_ROUTER_DEFAULTS.anthropic,
                ModelConfig(
                    provider=ModelProvider.ANTHROPIC,
                    model_name=LLM_ROUTER_DEFAULTS.anthropic,
                    api_key=self.settings.ANTHROPIC_API_KEY,
                    max_tokens=4096,
                    temperature=0.7,
                ),
            )

        return models

    def _register_model(
        self, models: dict[str, ModelConfig], model_name: str, config: ModelConfig
    ) -> None:
        """Register a model when it is allowed in the active lane."""
        if not model_allowed(
            model_name,
            active_lane=self.model_usage_lane,
            settings=self.settings,
        ):
            return

        config.lane = describe_model_lane(model_name, self.settings)
        models[model_name] = config

    def _get_primary_model(self) -> Optional[ModelConfig]:
        """Get primary model (Gemini preferred)"""
        return self.models.get(LLM_ROUTER_DEFAULTS.gemini)

    def _get_fallback_models(self) -> list[ModelConfig]:
        """Get fallback models in order"""
        return [
            self.models[name]
            for name in LLM_ROUTER_FALLBACK_ORDER
            if name in self.models and self.models[name].enabled
        ]

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate text with fallback strategy"""

        # Use specified model or primary model
        config = None
        if model:
            if model not in self.models:
                raise ValueError(
                    f"Requested model '{model}' is unavailable under the "
                    f"'{self.model_usage_lane.value}' model lane"
                )
            config = self.models[model]
        elif self.primary_model:
            config = self.primary_model
        else:
            raise ValueError("No LLM models available")

        start_time = time.time()
        last_error = None

        # Try primary model first
        try:
            response = await self._call_model(
                config,
                prompt,
                temperature or config.temperature,
                max_tokens or config.max_tokens,
            )
            latency_ms = int((time.time() - start_time) * 1000)
            log_request(
                "llm",
                f"Generated response from {config.provider} ({config.model_name})",
                details={"latency_ms": latency_ms, "model": config.model_name},
            )
            response.latency_ms = latency_ms
            get_model_usage_telemetry().record_generation(
                subsystem="llm_router",
                provider=config.provider.value,
                model=config.model_name,
                catalog="llm_router_defaults"
                if model is None
                else "requested_model",
                selection="primary_default" if model is None else "requested_model",
                runtime_lane=self.model_usage_lane.value,
                tokens_used=response.tokens_used,
            )
            return response
        except Exception as e:
            last_error = e
            log_error(
                "llm_primary_failed",
                f"Primary model {config.model_name} failed: {str(e)}",
            )

        # Try fallback models
        for fallback_config in self.fallback_models:
            if fallback_config.model_name == config.model_name:
                continue  # Skip already-tried model

            try:
                log_request(
                    "llm",
                    f"Falling back to {fallback_config.provider} ({fallback_config.model_name})",
                )
                response = await self._call_model(
                    fallback_config,
                    prompt,
                    temperature or fallback_config.temperature,
                    max_tokens or fallback_config.max_tokens,
                )
                latency_ms = int((time.time() - start_time) * 1000)
                response.latency_ms = latency_ms
                get_model_usage_telemetry().record_generation(
                    subsystem="llm_router",
                    provider=fallback_config.provider.value,
                    model=fallback_config.model_name,
                    catalog="llm_router_defaults",
                    selection="fallback_default",
                    runtime_lane=self.model_usage_lane.value,
                    tokens_used=response.tokens_used,
                )
                return response
            except Exception as e:
                log_error(
                    "llm_fallback_failed",
                    f"Fallback model {fallback_config.model_name} failed: {str(e)}",
                )
                last_error = e
                continue

        # All models failed
        raise RuntimeError(f"All LLM models exhausted. Last error: {str(last_error)}")

    async def _call_model(
        self,
        config: ModelConfig,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Call specific LLM provider"""

        if config.provider == ModelProvider.GEMINI:
            return await self._call_gemini(config, prompt, temperature, max_tokens)
        elif config.provider == ModelProvider.OPENAI:
            return await self._call_openai(config, prompt, temperature, max_tokens)
        elif config.provider == ModelProvider.GROQ:
            return await self._call_groq(config, prompt, temperature, max_tokens)
        elif config.provider == ModelProvider.ANTHROPIC:
            return await self._call_anthropic(config, prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

    async def _call_gemini(
        self, config: ModelConfig, prompt: str, temperature: float, max_tokens: int
    ) -> LLMResponse:
        """Call Google Gemini API"""
        try:
            import google.generativeai as genai

            genai.configure(api_key=config.api_key)
            model = genai.GenerativeModel(config.model_name)

            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    top_p=0.9,
                    max_output_tokens=max_tokens,
                ),
            )

            return LLMResponse(
                content=response.text,
                model=config.model_name,
                provider=config.provider.value,
                tokens_used=None,  # Gemini doesn't expose token count in free tier
                temperature=temperature,
            )
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")

    async def _call_openai(
        self, config: ModelConfig, prompt: str, temperature: float, max_tokens: int
    ) -> LLMResponse:
        """Call OpenAI API"""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=config.api_key)

            response = await client.chat.completions.create(
                model=config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=config.timeout,
            )

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=config.model_name,
                provider=config.provider.value,
                tokens_used=response.usage.total_tokens
                if response.usage is not None
                else None,
                temperature=temperature,
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    async def _call_groq(
        self, config: ModelConfig, prompt: str, temperature: float, max_tokens: int
    ) -> LLMResponse:
        """Call Groq API"""
        try:
            from groq import AsyncGroq

            client = AsyncGroq(api_key=config.api_key)

            response = await client.chat.completions.create(
                model=config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=config.timeout,
            )

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=config.model_name,
                provider=config.provider.value,
                tokens_used=response.usage.total_tokens
                if response.usage is not None
                else None,
                temperature=temperature,
            )
        except Exception as e:
            raise RuntimeError(f"Groq API error: {str(e)}")

    async def _call_anthropic(
        self, config: ModelConfig, prompt: str, temperature: float, max_tokens: int
    ) -> LLMResponse:
        """Call Anthropic Claude API"""
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=config.api_key)

            response = await client.messages.create(
                model=config.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            return LLMResponse(
                content=getattr(response.content[0], "text", "")
                if response.content
                else "",
                model=config.model_name,
                provider=config.provider.value,
                tokens_used=(
                    response.usage.input_tokens + response.usage.output_tokens
                    if response.usage is not None
                    else None
                ),
                temperature=temperature,
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")

    def available_models(self) -> list[str]:
        """Get list of available models"""
        return [
            name
            for name, config in self.models.items()
            if config.enabled and config.api_key
        ]

    def get_model_info(self) -> dict[str, Any]:
        """Get information about available models"""
        return {
            "primary": self.primary_model.model_name if self.primary_model else None,
            "model_usage_lane": self.model_usage_lane.value,
            "available_models": self.available_models(),
            "fallback_order": [m.model_name for m in self.fallback_models],
            "model_lanes": {
                name: config.lane
                for name, config in self.models.items()
                if config.enabled and config.api_key
            },
        }


# Global router instance
_llm_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get or create LLM router singleton"""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router
