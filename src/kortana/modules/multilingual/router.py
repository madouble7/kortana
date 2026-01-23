"""
Multilingual API Router for Kor'tana
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .language_detector import LanguageDetector
from .translation_service import TranslationService

router = APIRouter(prefix="/api/multilingual", tags=["multilingual"])

translation_service = TranslationService()
language_detector = LanguageDetector()


class TranslationRequest(BaseModel):
    text: str
    target_language: str = "en"
    source_language: str = "auto"


class LanguageDetectionRequest(BaseModel):
    text: str


@router.post("/translate")
async def translate_text(request: TranslationRequest):
    """Translate text to target language"""
    try:
        if not translation_service.is_supported(request.target_language):
            raise HTTPException(
                status_code=400,
                detail=f"Target language {request.target_language} not supported",
            )

        translated = translation_service.translate(
            request.text, request.source_language, request.target_language
        )
        return {
            "original": request.text,
            "translated": translated,
            "source_language": request.source_language,
            "target_language": request.target_language,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect")
async def detect_language(request: LanguageDetectionRequest):
    """Detect the language of text"""
    try:
        lang, confidence = language_detector.detect_with_confidence(request.text)
        return {"language": lang, "confidence": confidence, "text": request.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {"languages": translation_service.get_supported_languages()}
