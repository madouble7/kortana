"""
Language detection and translation utilities for Kor'tana multilingual support.
"""

from typing import Optional

# Supported languages mapping
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish", 
    "fr": "French",
    "de": "German",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "pt": "Portuguese",
    "it": "Italian",
    "ru": "Russian",
}


def detect_language(text: str) -> str:
    """
    Detect the language of the given text.
    
    For now, this is a simple implementation that defaults to English.
    In production, this would use a proper language detection library.
    
    Args:
        text: The text to detect language for
        
    Returns:
        ISO 639-1 language code (e.g., 'en', 'es', 'fr')
    """
    # Simple heuristic: check for common non-English characters
    if any('\u4e00' <= char <= '\u9fff' for char in text):
        return "zh"  # Chinese characters
    if any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
        return "ja"  # Japanese hiragana/katakana
    if any('\uac00' <= char <= '\ud7af' for char in text):
        return "ko"  # Korean hangul
    if any('\u0400' <= char <= '\u04ff' for char in text):
        return "ru"  # Cyrillic
    
    # Default to English for now
    return "en"


def validate_language_code(lang_code: Optional[str]) -> str:
    """
    Validate a language code and return it if valid, else return default.
    
    Args:
        lang_code: ISO 639-1 language code to validate
        
    Returns:
        Valid language code (defaults to 'en' if invalid)
    """
    if not lang_code:
        return "en"
    
    lang_code = lang_code.lower().strip()
    
    if lang_code in SUPPORTED_LANGUAGES:
        return lang_code
    
    # Default to English
    return "en"


def get_language_name(lang_code: str) -> str:
    """
    Get the full name of a language from its code.
    
    Args:
        lang_code: ISO 639-1 language code
        
    Returns:
        Full language name
    """
    return SUPPORTED_LANGUAGES.get(lang_code, "Unknown")


def get_system_prompt_for_language(lang_code: str) -> str:
    """
    Get the system prompt instructing the LLM to respond in the specified language.
    
    Args:
        lang_code: ISO 639-1 language code
        
    Returns:
        System prompt text
    """
    language_name = get_language_name(lang_code)
    
    if lang_code == "en":
        return ""  # No special instruction needed for English
    
    return f"Please respond in {language_name}. All responses should be in {language_name} language."
