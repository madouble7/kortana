"""
Multilingual Support Module for Kor'tana
Provides real-time translation and multilingual memory adaptation
"""

from .language_detector import LanguageDetector
from .translation_service import TranslationService

__all__ = ["TranslationService", "LanguageDetector"]
