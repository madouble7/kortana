"""
Translation Service for Kor'tana
Provides real-time translation capabilities
"""

from typing import Optional


class TranslationService:
    """Service for translating text between languages"""

    def __init__(self):
        self.supported_languages = [
            "en",
            "es",
            "fr",
            "de",
            "ja",
            "zh",
            "ko",
            "ar",
            "ru",
            "pt",
        ]

    def translate(
        self, text: str, source_lang: str = "auto", target_lang: str = "en"
    ) -> str:
        """
        Translate text from source language to target language

        Args:
            text: Text to translate
            source_lang: Source language code (default: auto-detect)
            target_lang: Target language code (default: en)

        Returns:
            Translated text
        """
        # Simple passthrough for now - can be extended with actual translation API
        if source_lang == target_lang or source_lang == "auto":
            return text
        return f"[{target_lang}] {text}"

    def is_supported(self, language_code: str) -> bool:
        """Check if a language is supported"""
        return language_code in self.supported_languages

    def get_supported_languages(self) -> list[str]:
        """Get list of supported language codes"""
        return self.supported_languages.copy()
