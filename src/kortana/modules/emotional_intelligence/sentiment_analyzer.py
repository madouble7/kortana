"""
Sentiment Analyzer for Kor'tana
Analyzes sentiment of text input
"""

from enum import Enum


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class SentimentAnalyzer:
    """Service for analyzing sentiment in text"""

    def __init__(self):
        self.positive_keywords = [
            "happy",
            "joy",
            "love",
            "excellent",
            "great",
            "wonderful",
            "amazing",
            "good",
            "nice",
            "fantastic",
        ]
        self.negative_keywords = [
            "sad",
            "angry",
            "hate",
            "terrible",
            "awful",
            "bad",
            "horrible",
            "poor",
            "disappointing",
            "frustrating",
        ]

    def analyze(self, text: str) -> tuple[Sentiment, float]:
        """
        Analyze sentiment of text

        Args:
            text: Text to analyze

        Returns:
            Tuple of (sentiment, confidence_score)
        """
        if not text or len(text.strip()) == 0:
            return Sentiment.NEUTRAL, 0.5

        text_lower = text.lower()

        # Count positive and negative keywords
        positive_count = sum(
            1 for keyword in self.positive_keywords if keyword in text_lower
        )
        negative_count = sum(
            1 for keyword in self.negative_keywords if keyword in text_lower
        )

        # Determine sentiment
        if positive_count > negative_count:
            sentiment = Sentiment.POSITIVE
            confidence = min(0.95, 0.6 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            sentiment = Sentiment.NEGATIVE
            confidence = min(0.95, 0.6 + (negative_count - positive_count) * 0.1)
        else:
            sentiment = Sentiment.NEUTRAL
            confidence = 0.5

        return sentiment, confidence

    def get_sentiment_score(self, text: str) -> float:
        """
        Get sentiment score from -1.0 (very negative) to 1.0 (very positive)

        Args:
            text: Text to analyze

        Returns:
            Float score between -1.0 and 1.0
        """
        sentiment, confidence = self.analyze(text)

        if sentiment == Sentiment.POSITIVE:
            return confidence
        elif sentiment == Sentiment.NEGATIVE:
            return -confidence
        else:
            return 0.0
