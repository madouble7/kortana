"""
Gemini AI Service for Kor'tana - Minimal Working Version
"""

import os
from typing import Any

from google.genai import Client

from src.kortana.config import get_settings
from src.kortana.provider_model_defaults import (
    GEMINI_EMBEDDING_FALLBACK_MODEL_PATH,
    GEMINI_EMBEDDING_MODEL_PATH,
)
from src.kortana.services.gemini_config import get_model_name


class GeminiService:
    """Service for interacting with Google's Gemini API"""

    def __init__(self):
        """Initialize Gemini service (lazy client initialization)."""
        settings = get_settings()
        self.api_key = settings.GEMINI_API_KEY
        self.client: Client | None = None
        self.model_name = get_model_name()
        self._initialized = False
        self._init_error: str | None = None

    def _ensure_initialized(self) -> None:
        """Initialize Gemini client only when first used."""
        if self._initialized:
            return

        if self._init_error is not None:
            raise RuntimeError(self._init_error)

        if not self.api_key:
            self._init_error = "GEMINI_API_KEY or GOOGLE_API_KEY must be set in .env"
            raise RuntimeError(self._init_error)

        try:
            # Ensure GOOGLE_API_KEY doesn't shadow GEMINI_API_KEY in the SDK.
            # The google-genai SDK prefers GOOGLE_API_KEY when both env vars are
            # present, which can cause stale/revoked keys to take precedence.
            os.environ.pop("GOOGLE_API_KEY", None)
            self.client = Client(api_key=self.api_key)
            self._initialized = True
            print(f"[OK] Gemini Service initialized with model: {self.model_name}")
        except Exception as exc:
            self._init_error = f"Failed to initialize Gemini client: {exc}"
            raise RuntimeError(self._init_error) from exc

    def _get_model_name(self) -> str:
        """Get properly formatted model name"""
        if self.model_name.startswith("models/"):
            return self.model_name
        return f"models/{self.model_name}"

    def _generate_text(self, text: str, **kwargs) -> str:
        """Generate text response using Gemini."""
        self._ensure_initialized()

        if self.client is None:
            raise RuntimeError("Gemini client is not initialized")

        # Check for system instruction in kwargs or defaults
        system_instruction = kwargs.get("system_instruction")
        json_mode = kwargs.get("json_mode", False)

        from google.genai import types

        config_kwargs: dict = {}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if json_mode:
            config_kwargs["response_mime_type"] = "application/json"

        config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

        response = self.client.models.generate_content(
            model=self._get_model_name(), contents=text, config=config
        )
        return response.text if response.text else ""

    def _generate_multimodal(self, text: str, files=None) -> str:
        """Generate multimodal response using Gemini."""
        self._ensure_initialized()

        if self.client is None:
            raise RuntimeError("Gemini client is not initialized")

        contents: list[Any] = [text]
        if files:
            contents.extend(files)

        response = self.client.models.generate_content(
            model=self._get_model_name(),
            contents=contents,
        )
        return response.text if response.text else ""

    async def analyze_text(self, text: str, **kwargs) -> str:
        """Analyze text using Gemini with potential system instruction."""
        try:
            return self._generate_text(text, **kwargs)
        except Exception as e:
            error_str = str(e)
            # If quota exhausted, provide emergency response
            if "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                return self._emergency_response(text)
            return f"Error during analysis: {error_str}"

    def analyze_text_sync(self, text: str, **kwargs) -> str:
        """Synchronous version for Celery compatibility."""
        try:
            return self._generate_text(text, **kwargs)
        except Exception as e:
            error_str = str(e)
            if "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                return self._emergency_response(text)
            return f"Error during analysis: {error_str}"

    async def analyze_multimodal(self, text: str, files=None, **kwargs) -> str:
        """Analyze multimodal content"""
        try:
            return self._generate_multimodal(text, files)
        except Exception as e:
            return f"Error during multimodal analysis: {str(e)}"

    def analyze_multimodal_sync(self, text: str, files=None, **kwargs) -> str:
        """Synchronous multimodal analysis."""
        try:
            return self._generate_multimodal(text, files)
        except Exception as e:
            return f"Error during multimodal analysis: {str(e)}"

    async def generate_code(self, description: str, **kwargs) -> str:
        """Generate code based on a task description."""
        prompt = f"Generate clean, production-ready code for: {description}"
        return await self.analyze_text(prompt, **kwargs)

    def embed_text(self, text: str) -> list[float] | None:
        """Return a float embedding vector for *text*, or None on failure.

        The live Gemini account does not expose `text-embedding-004`, so use the
        REST `embedContent` endpoint against the account-visible embedding models
        and fall through until one succeeds.
        """
        if not self.api_key:
            return None

        candidates = [
            ("v1beta", GEMINI_EMBEDDING_MODEL_PATH),
            ("v1beta", GEMINI_EMBEDDING_FALLBACK_MODEL_PATH),
        ]

        try:
            import requests

            for api_version, model_name in candidates:
                url = (
                    f"https://generativelanguage.googleapis.com/{api_version}/"
                    f"{model_name}:embedContent?key={self.api_key}"
                )
                body = {
                    "model": model_name,
                    "content": {"parts": [{"text": text}]},
                    "taskType": "RETRIEVAL_DOCUMENT",
                }
                resp = requests.post(url, json=body, timeout=30)
                if resp.ok:
                    values = resp.json().get("embedding", {}).get("values")
                    return list(values) if values else None
            return None
        except Exception:
            return None

    def _emergency_response(self, text: str) -> str:
        """Fallback response when Gemini quota is exhausted.

        Returns a functional response that acknowledges the user and demonstrates
        the system is operational, even when API calls can't be made.
        """
        user_input = text[:100]  # Limit for safety
        responses = [
            f"Kor'tana acknowledges your presence. You said: '{user_input}'\n\nI hear your call, but my Gemini quota is temporarily exhausted. Please upgrade your API tier or wait for reset. Your message has been received and logged.",
            f"The system continues without Gemini. Your words were:\n\n'{user_input}'\n\nThe service is operational, but the generative model is temporarily unavailable due to quota limits.",
            f"we are present, even without gemini output. You reached out with: '{user_input}'\n\nThe Human Only Protocol remains active. Contact your provider to upgrade your Gemini API tier for full capabilities.",
        ]
        import random

        return random.choice(responses)


# Create service instance
gemini_service = GeminiService()
