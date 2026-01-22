"""
Language Detection for Kor'tana
Detects the language of input text
"""


class LanguageDetector:
    """Service for detecting language of text"""

    def detect(self, text: str) -> str:
        """
        Detect the language of the given text

        Args:
            text: Text to analyze

        Returns:
            Detected language code (e.g., 'en', 'es', 'fr')
        """
        # Simple heuristic-based detection
        # Can be extended with proper language detection library
        if not text or len(text.strip()) == 0:
            return "en"

        # Check for common non-English characters
        if any(char in text for char in "áéíóúñ¿¡"):
            return "es"
        elif any(char in text for char in "àâæçéèêëïîôùûü"):
            return "fr"
        elif any(char in text for char in "äöüß"):
            return "de"
        elif any("\u4e00" <= char <= "\u9fff" for char in text):
            return "zh"
        elif any("\u3040" <= char <= "\u309f" for char in text) or any(
            "\u30a0" <= char <= "\u30ff" for char in text
        ):
            return "ja"
        elif any("\uac00" <= char <= "\ud7af" for char in text):
            return "ko"
        elif any("\u0600" <= char <= "\u06ff" for char in text):
            return "ar"
        elif any("\u0400" <= char <= "\u04ff" for char in text):
            return "ru"

        return "en"

    def detect_with_confidence(self, text: str) -> tuple[str, float]:
        """
        Detect language with confidence score

        Args:
            text: Text to analyze

        Returns:
            Tuple of (language_code, confidence_score)
        """
        lang = self.detect(text)
        # Simple confidence based on text length and character matches
        confidence = min(0.9, 0.5 + (len(text) / 200))
        return lang, confidence
