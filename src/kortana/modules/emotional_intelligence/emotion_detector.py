"""
Emotion Detector for Kor'tana
Detects emotions in text
"""

from enum import StrEnum


class Emotion(StrEnum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    NEUTRAL = "neutral"


class EmotionDetector:
    """Service for detecting emotions in text"""

    def __init__(self):
        self.emotion_keywords = {
            Emotion.JOY: ["happy", "joy", "excited", "pleased", "delighted", "cheerful"],
            Emotion.SADNESS: ["sad", "unhappy", "depressed", "miserable", "sorrowful"],
            Emotion.ANGER: [
                "angry",
                "furious",
                "mad",
                "irritated",
                "frustrated",
                "annoyed",
            ],
            Emotion.FEAR: ["afraid", "scared", "worried", "anxious", "nervous", "fear"],
            Emotion.SURPRISE: [
                "surprised",
                "amazed",
                "astonished",
                "shocked",
                "unexpected",
            ],
        }

    def detect(self, text: str) -> tuple[Emotion, float]:
        """
        Detect primary emotion in text

        Args:
            text: Text to analyze

        Returns:
            Tuple of (emotion, confidence_score)
        """
        if not text or len(text.strip()) == 0:
            return Emotion.NEUTRAL, 0.5

        text_lower = text.lower()

        # Count keywords for each emotion
        emotion_scores = {}
        for emotion, keywords in self.emotion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            emotion_scores[emotion] = count

        # Find dominant emotion
        max_score = max(emotion_scores.values())
        if max_score == 0:
            return Emotion.NEUTRAL, 0.5

        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        confidence = min(0.95, 0.6 + max_score * 0.15)

        return dominant_emotion, confidence

    def detect_all(self, text: str) -> dict[Emotion, float]:
        """
        Detect all emotions with confidence scores

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping emotions to confidence scores
        """
        if not text or len(text.strip()) == 0:
            return {Emotion.NEUTRAL: 1.0}

        text_lower = text.lower()

        # Calculate scores for all emotions
        results = {}
        total_keywords = 0

        for emotion, keywords in self.emotion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            results[emotion] = count
            total_keywords += count

        # Normalize scores
        if total_keywords > 0:
            return {
                emotion: count / total_keywords
                for emotion, count in results.items()
                if count > 0
            }
        else:
            return {Emotion.NEUTRAL: 1.0}
