"""
Emotional Intelligence API Router for Kor'tana
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .emotion_detector import EmotionDetector
from .sentiment_analyzer import SentimentAnalyzer

router = APIRouter(prefix="/api/emotional-intelligence", tags=["emotional-intelligence"])

sentiment_analyzer = SentimentAnalyzer()
emotion_detector = EmotionDetector()


class TextAnalysisRequest(BaseModel):
    text: str


@router.post("/sentiment")
async def analyze_sentiment(request: TextAnalysisRequest):
    """Analyze sentiment of text"""
    try:
        sentiment, confidence = sentiment_analyzer.analyze(request.text)
        score = sentiment_analyzer.get_sentiment_score(request.text)
        return {
            "text": request.text,
            "sentiment": sentiment,
            "confidence": confidence,
            "score": score,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emotion")
async def detect_emotion(request: TextAnalysisRequest):
    """Detect emotion in text"""
    try:
        emotion, confidence = emotion_detector.detect(request.text)
        all_emotions = emotion_detector.detect_all(request.text)
        return {
            "text": request.text,
            "primary_emotion": emotion,
            "confidence": confidence,
            "all_emotions": all_emotions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_full(request: TextAnalysisRequest):
    """Perform full emotional analysis (sentiment + emotion)"""
    try:
        sentiment, sent_confidence = sentiment_analyzer.analyze(request.text)
        emotion, emot_confidence = emotion_detector.detect(request.text)
        score = sentiment_analyzer.get_sentiment_score(request.text)

        return {
            "text": request.text,
            "sentiment": {
                "value": sentiment,
                "confidence": sent_confidence,
                "score": score,
            },
            "emotion": {"value": emotion, "confidence": emot_confidence},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
