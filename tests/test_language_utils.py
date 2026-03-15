"""
Unit tests for language utilities.
"""

from src.kortana.utils.language_utils import (
    SUPPORTED_LANGUAGES,
    detect_language,
    get_language_name,
    get_system_prompt_for_language,
    validate_language_code,
)


class TestLanguageDetection:
    """Test language detection functionality."""

    def test_detect_english_default(self):
        """Test that English text is detected correctly."""
        text = "Hello, how are you?"
        assert detect_language(text) == "en"

    def test_detect_chinese(self):
        """Test that Chinese text is detected correctly."""
        text = "你好世界"
        assert detect_language(text) == "zh"

    def test_detect_japanese(self):
        """Test that Japanese text is detected correctly."""
        text = "こんにちは"
        assert detect_language(text) == "ja"

    def test_detect_korean(self):
        """Test that Korean text is detected correctly."""
        text = "안녕하세요"
        assert detect_language(text) == "ko"

    def test_detect_russian(self):
        """Test that Russian text is detected correctly."""
        text = "Привет мир"
        assert detect_language(text) == "ru"


class TestLanguageValidation:
    """Test language code validation."""

    def test_validate_valid_code(self):
        """Test that valid language codes are accepted."""
        assert validate_language_code("en") == "en"
        assert validate_language_code("es") == "es"
        assert validate_language_code("fr") == "fr"

    def test_validate_uppercase_code(self):
        """Test that uppercase codes are normalized."""
        assert validate_language_code("EN") == "en"
        assert validate_language_code("ES") == "es"

    def test_validate_invalid_code(self):
        """Test that invalid codes default to English."""
        assert validate_language_code("xx") == "en"
        assert validate_language_code("invalid") == "en"

    def test_validate_none(self):
        """Test that None defaults to English."""
        assert validate_language_code(None) == "en"

    def test_validate_with_whitespace(self):
        """Test that codes with whitespace are handled."""
        assert validate_language_code("  en  ") == "en"


class TestLanguageName:
    """Test language name retrieval."""

    def test_get_language_name(self):
        """Test that language names are returned correctly."""
        assert get_language_name("en") == "English"
        assert get_language_name("es") == "Spanish"
        assert get_language_name("fr") == "French"
        assert get_language_name("de") == "German"

    def test_get_unknown_language_name(self):
        """Test that unknown codes return 'Unknown'."""
        assert get_language_name("xx") == "Unknown"


class TestSystemPrompts:
    """Test system prompt generation for languages."""

    def test_english_system_prompt(self):
        """Test that English has no special instruction."""
        prompt = get_system_prompt_for_language("en")
        assert prompt == ""

    def test_spanish_system_prompt(self):
        """Test that Spanish has proper instruction."""
        prompt = get_system_prompt_for_language("es")
        assert "Spanish" in prompt
        assert "respond" in prompt.lower()

    def test_french_system_prompt(self):
        """Test that French has proper instruction."""
        prompt = get_system_prompt_for_language("fr")
        assert "French" in prompt
        assert "respond" in prompt.lower()


class TestSupportedLanguages:
    """Test supported languages list."""

    def test_supported_languages_exist(self):
        """Test that we have a non-empty list of supported languages."""
        assert len(SUPPORTED_LANGUAGES) > 0

    def test_english_is_supported(self):
        """Test that English is in the supported languages."""
        assert "en" in SUPPORTED_LANGUAGES
        assert SUPPORTED_LANGUAGES["en"] == "English"

    def test_all_codes_are_two_chars(self):
        """Test that all language codes are 2 characters."""
        for code in SUPPORTED_LANGUAGES.keys():
            assert len(code) == 2
