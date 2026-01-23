"""
Emotional Intelligence Module for Kor'tana
Provides sentiment analysis and emotion-aware responses
"""

from .emotion_detector import EmotionDetector
from .sentiment_analyzer import SentimentAnalyzer

__all__ = ["SentimentAnalyzer", "EmotionDetector"]
