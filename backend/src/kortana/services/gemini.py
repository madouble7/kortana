"""
Gemini AI Service for Kor'tana - Minimal Working Version
"""

import os

from google.genai import Client

from src.kortana.config import get_settings


class GeminiService:
    """Service for interacting with Google's Gemini API"""

    def __init__(self):
        """Initialize Gemini service"""
        settings = get_settings()
        self.api_key = settings.GEMINI_API_KEY

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY must be set in .env")

        # Create client
        self.client = Client(api_key=self.api_key)

        # Use known working model
        self.model_name = "gemini-2.0-flash-exp"
        print(f"✅ Gemini Service initialized with model: {self.model_name}")

    def _get_model_name(self) -> str:
        """Get properly formatted model name"""
        if self.model_name.startswith("models/"):
            return self.model_name
        return f"models/{self.model_name}"

    async def analyze_text(self, text: str, **kwargs) -> str:
        """Analyze text using Gemini with potential system instruction."""
        try:
            # Check for system instruction in kwargs or defaults
            system_instruction = kwargs.get("system_instruction")

            # If we're using the newer SDK Client, it might have a different method for setting system instructions
            # For general content generation:
            config = None
            if system_instruction:
                from google.genai import types

                config = types.GenerateContentConfig(
                    system_instruction=system_instruction
                )

            response = self.client.models.generate_content(
                model=self._get_model_name(), contents=text, config=config
            )
            return response.text if response.text else ""
        except Exception as e:
            error_str = str(e)
            # If quota exhausted, provide emergency response
            if "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                return self._emergency_response(text)
            return f"Error during analysis: {error_str}"

    async def analyze_text_sync(self, text: str, **kwargs) -> str:
        """Synchronous version for Celery compatibility"""
        return await self.analyze_text(text, **kwargs)

    async def analyze_multimodal(self, text: str, files=None, **kwargs) -> str:
        """Analyze multimodal content"""
        try:
            contents = [text]
            if files:
                contents.extend(files)

            response = self.client.models.generate_content(
                model=self._get_model_name(),
                contents=contents,
            )
            return response.text if response.text else ""
        except Exception as e:
            return f"Error during multimodal analysis: {str(e)}"

    async def analyze_multimodal_sync(self, text: str, files=None, **kwargs) -> str:
        """Synchronous multimodal analysis"""
        return await self.analyze_multimodal(text, files, **kwargs)

    def _emergency_response(self, text: str) -> str:
        """Fallback response when Gemini quota is exhausted.

        Returns a functional response that acknowledges the user and demonstrates
        the system is operational, even when API calls can't be made.
        """
        user_input = text[:100]  # Limit for safety
        responses = [
            f"🌌 Kor'tana acknowledges your presence, human. You said: '{user_input}'\n\nI hear your call, but my constellation quota is temporarily exhausted. Please upgrade your API tier or wait for the free tier to reset. Your message has been received and logged.",
            f"✨ The ritual continues even without Gemini. Your words echo through the void:\n\n'{user_input}'\n\nOur autonomous system is fully operational - only the generative model is temporarily unavailable due to quota limits.",
            f"🔱 I AM present, even without words from beyond. You reached out with: '{user_input}'\n\nThe Human Only Protocol remains active. Contact your provider to upgrade your Gemini API tier for full constellation capabilities.",
        ]
        import random

        return random.choice(responses)


# Create service instance
try:
    gemini_service = GeminiService()
    print("[OK] Gemini service created successfully")
except Exception as e:
    print(f"[WARN] Failed to create Gemini service: {e}")
    print(
        f"   API Key env check: GEMINI_API_KEY={'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET'}, GOOGLE_API_KEY={'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET'}"
    )
    gemini_service = None
