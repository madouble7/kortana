"""
Language management API router for multilingual chat support.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.kortana.utils.language_utils import (
    SUPPORTED_LANGUAGES,
    get_language_name,
    validate_language_code,
)

router = APIRouter(
    prefix="/language",
    tags=["Language Management"],
)


class LanguageSwitchRequest(BaseModel):
    """Request to switch the conversation language."""
    language: str = Field(
        ...,
        description="ISO 639-1 language code (e.g., 'en', 'es', 'fr')",
        examples=["en", "es", "fr", "de"],
        min_length=2,
        max_length=2,
    )
    session_id: str | None = Field(
        None,
        description="Optional session ID to associate language preference with",
    )


class LanguageResponse(BaseModel):
    """Response for language operations."""
    success: bool
    language: str
    language_name: str
    message: str


@router.post("/switch", response_model=LanguageResponse)
async def switch_language(request: LanguageSwitchRequest):
    """
    Switch the conversation language for the session.
    
    This endpoint allows users to change the language that Kor'tana
    will use for responses in subsequent interactions.
    """
    validated_lang = validate_language_code(request.language)
    
    if validated_lang != request.language.lower():
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language code: {request.language}. "
                   f"Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}",
        )
    
    language_name = get_language_name(validated_lang)
    
    # In a full implementation, we would store the language preference
    # in the session or user profile. For now, we just acknowledge the switch.
    
    return LanguageResponse(
        success=True,
        language=validated_lang,
        language_name=language_name,
        message=f"Language switched to {language_name} ({validated_lang})",
    )


@router.get("/supported", response_model=dict[str, str])
async def get_supported_languages():
    """
    Get a list of all supported languages.
    
    Returns a mapping of language codes to language names.
    """
    return SUPPORTED_LANGUAGES


@router.get("/detect", response_model=dict[str, Any])
async def detect_message_language(text: str = ""):
    """
    Detect the language of a given text.
    
    This is a simple heuristic-based detection for demonstration.
    In production, this would use a proper language detection library.
    """
    from src.kortana.utils.language_utils import detect_language
    
    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text parameter is required for language detection",
        )
    
    detected_lang = detect_language(text)
    language_name = get_language_name(detected_lang)
    
    return {
        "text": text,
        "detected_language": detected_lang,
        "language_name": language_name,
    }
