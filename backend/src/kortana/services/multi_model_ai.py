"""
Kor'tana Multi-Model AI Service
Supports: Gemini, OpenAI, Claude, OpenRouter, Groq with automatic fallback
"""

import os
from typing import Any, Optional

import httpx

from src.kortana.model_lane_policy import (
    describe_model_lane,
    get_active_model_lane,
    model_allowed,
)
from src.kortana.model_usage_telemetry import get_model_usage_telemetry
from src.kortana.openai_responses import sync_generate_text
from src.kortana.provider_model_defaults import MULTI_MODEL_DEFAULTS
from src.kortana.services.gemini_config import get_model_name


class MultiModelAIService:
    """Service that intelligently selects from multiple AI providers"""

    def __init__(self) -> None:
        """Initialize service container (providers are loaded lazily on first use)."""
        self.providers: dict[str, dict[str, Any]] = {}
        self.primary_provider: Optional[str] = None
        self._initialized = False
        self.model_usage_lane = get_active_model_lane()

    def _model_allowed(self, provider_name: str, model_name: str) -> bool:
        """Return True when a provider model is allowed in the active lane."""
        if model_allowed(model_name, active_lane=self.model_usage_lane):
            return True

        print(
            f"[INFO] Skipping {provider_name} model {model_name} "
            f"({describe_model_lane(model_name)} lane) under "
            f"{self.model_usage_lane.value} runtime"
        )
        return False

    def _ensure_initialized(self) -> None:
        """Initialize providers only when first requested."""
        if self._initialized:
            return

        self._init_gemini()
        self._init_openai()
        self._init_anthropic()
        self._init_groq()
        self._init_openrouter()

        if self.providers:
            self.primary_provider = list(self.providers.keys())[0]
            print("[OK] Multi-Model Service initialized")
            print(f"[INFO] Available providers: {', '.join(self.providers.keys())}")
            print(f"[INFO] Primary provider: {self.primary_provider}")
        else:
            print("[WARN] No AI providers configured")

        self._initialized = True

    def _init_gemini(self) -> None:
        """Initialize Google Gemini"""
        try:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return

            from google.genai import Client

            client = Client(api_key=api_key)
            model_name = get_model_name()
            if not self._model_allowed("gemini", model_name):
                return
            self.providers["gemini"] = {
                "client": client,
                "model": model_name,
                "type": "google",
            }
            print("[OK] Gemini provider initialized")
        except Exception as e:
            print(f"[WARN] Gemini initialization failed: {e}")

    def _init_openai(self) -> None:
        """Initialize OpenAI"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return

            import openai

            if not self._model_allowed("openai", MULTI_MODEL_DEFAULTS.openai):
                return
            self.providers["openai"] = {
                "client": openai.OpenAI(
                    api_key=api_key,
                    http_client=httpx.Client(timeout=30.0),
                ),
                "model": MULTI_MODEL_DEFAULTS.openai,
                "type": "openai",
            }
            print("[OK] OpenAI provider initialized")
        except Exception as e:
            print(f"[WARN] OpenAI initialization failed: {e}")

    def _init_anthropic(self) -> None:
        """Initialize Anthropic Claude"""
        try:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return

            import anthropic

            if not self._model_allowed(
                "anthropic", MULTI_MODEL_DEFAULTS.anthropic
            ):
                return
            self.providers["anthropic"] = {
                "client": anthropic.Anthropic(api_key=api_key),
                "model": MULTI_MODEL_DEFAULTS.anthropic,
                "type": "anthropic",
            }
            print("[OK] Anthropic Claude provider initialized")
        except Exception as e:
            print(f"[WARN] Anthropic initialization failed: {e}")

    def _init_groq(self) -> None:
        """Initialize Groq (fast inference)"""
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                return

            import groq

            if not self._model_allowed("groq", MULTI_MODEL_DEFAULTS.groq):
                return
            self.providers["groq"] = {
                "client": groq.Groq(api_key=api_key),
                "model": MULTI_MODEL_DEFAULTS.groq,
                "type": "groq",
            }
            print("[OK] Groq provider initialized")
        except Exception as e:
            print(f"[WARN] Groq initialization failed: {e}")

    def _init_openrouter(self) -> None:
        """Initialize OpenRouter (multi-model aggregator)"""
        try:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                return

            import openai as openai_module

            if not self._model_allowed(
                "openrouter", MULTI_MODEL_DEFAULTS.openrouter
            ):
                return
            self.providers["openrouter"] = {
                "client": openai_module.OpenAI(
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1",
                    http_client=httpx.Client(timeout=30.0),
                ),
                "model": MULTI_MODEL_DEFAULTS.openrouter,
                "type": "openrouter",
            }
            print("[OK] OpenRouter provider initialized")
        except Exception as e:
            print(f"[WARN] OpenRouter initialization failed: {e}")

    async def analyze_text(self, text: str, **kwargs: object) -> str:
        """Analyze text using best available provider with fallback"""
        self._ensure_initialized()

        if not self.providers:
            return "[ERROR] No AI providers available"

        # Try each provider in order
        for provider_name in self.providers.keys():
            try:
                response = await self._call_provider(provider_name, text)
                if response:
                    return f"[{provider_name.upper()}] {response}"
            except Exception as e:
                print(f"[WARN] {provider_name} failed: {e}; trying next provider")
                continue

        return "[ERROR] All providers failed"

    async def _call_provider(self, provider_name: str, text: str) -> Optional[str]:
        """Call a specific provider"""
        provider = self.providers.get(provider_name)
        if not provider:
            return None

        try:
            # Gemini
            if provider_name == "gemini":
                response = provider["client"].models.generate_content(
                    model=f"models/{provider['model']}",
                    contents=text,
                )
                text_out = response.text if response else None
                if text_out:
                    get_model_usage_telemetry().record_generation(
                        subsystem="multi_model_ai",
                        provider=provider_name,
                        model=str(provider["model"]),
                        catalog="multi_model_defaults",
                        selection="ordered_provider",
                        runtime_lane=self.model_usage_lane.value,
                    )
                return text_out

            # OpenAI
            elif provider_name == "openai":
                text_out, _, _ = sync_generate_text(
                    provider["client"],
                    model_name=str(provider["model"]),
                    prompt=text,
                    max_output_tokens=500,
                )
                if text_out:
                    get_model_usage_telemetry().record_generation(
                        subsystem="multi_model_ai",
                        provider=provider_name,
                        model=str(provider["model"]),
                        catalog="multi_model_defaults",
                        selection="ordered_provider",
                        runtime_lane=self.model_usage_lane.value,
                    )
                return text_out

            # Anthropic Claude
            elif provider_name == "anthropic":
                response = provider["client"].messages.create(
                    model=provider["model"],
                    max_tokens=500,
                    messages=[{"role": "user", "content": text}],
                )
                text_out = response.content[0].text if response.content else None
                if text_out:
                    get_model_usage_telemetry().record_generation(
                        subsystem="multi_model_ai",
                        provider=provider_name,
                        model=str(provider["model"]),
                        catalog="multi_model_defaults",
                        selection="ordered_provider",
                        runtime_lane=self.model_usage_lane.value,
                    )
                return text_out

            # Groq
            elif provider_name == "groq":
                response = provider["client"].chat.completions.create(
                    model=provider["model"],
                    messages=[{"role": "user", "content": text}],
                    max_tokens=500,
                )
                text_out = (
                    response.choices[0].message.content if response.choices else None
                )
                if text_out:
                    get_model_usage_telemetry().record_generation(
                        subsystem="multi_model_ai",
                        provider=provider_name,
                        model=str(provider["model"]),
                        catalog="multi_model_defaults",
                        selection="ordered_provider",
                        runtime_lane=self.model_usage_lane.value,
                    )
                return text_out

            # OpenRouter
            elif provider_name == "openrouter":
                response = provider["client"].chat.completions.create(
                    model=provider["model"],
                    messages=[{"role": "user", "content": text}],
                    max_tokens=500,
                )
                text_out = (
                    response.choices[0].message.content if response.choices else None
                )
                if text_out:
                    get_model_usage_telemetry().record_generation(
                        subsystem="multi_model_ai",
                        provider=provider_name,
                        model=str(provider["model"]),
                        catalog="multi_model_defaults",
                        selection="ordered_provider",
                        runtime_lane=self.model_usage_lane.value,
                    )
                return text_out

        except Exception as e:
            print(f"[WARN] Error calling {provider_name}: {e}")
            return None

        return None

    async def generate_code(self, description: str, **kwargs: object) -> str:
        """Generate code using best available provider"""
        prompt = f"Generate clean, production-ready code for: {description}"
        return await self.analyze_text(prompt, **kwargs)

    async def analyze_multimodal(
        self, text: str, files: object = None, **kwargs: object
    ) -> str:
        """Analyze multimodal content"""
        return await self.analyze_text(text, **kwargs)


# Create global instance
ai_service = MultiModelAIService()
