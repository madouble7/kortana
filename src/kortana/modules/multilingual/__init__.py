"""
Multilingual Support Module for Kor'tana
Provides real-time translation and multilingual memory adaptation
"""

from .translation_service import TranslationService
from .language_detector import LanguageDetector

__all__ = ["TranslationService", "LanguageDetector"]
