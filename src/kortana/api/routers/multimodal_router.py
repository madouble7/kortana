"""
Multimodal API router for Kor'tana.

This module provides API endpoints for multimodal prompt generation and processing,
supporting text, voice, video, image, and simulation-based queries.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.kortana.core.multimodal import (
    ContentType,
    MultimodalPromptGenerator,
    SimulationQuery,
)
from src.kortana.services.database import get_db_sync
from src.kortana.services.multimodal_service import MultimodalService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/multimodal",
    tags=["Multimodal AI"],
)


# Request/Response Models
class TextPromptRequest(BaseModel):
    """Request model for text-based prompts."""

    text: str = Field(..., description="Text content for the prompt")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional context information"
    )


class VoicePromptRequest(BaseModel):
    """Request model for voice-based prompts."""

    audio_url: Optional[str] = Field(default=None, description="URL to audio file")
    transcription: Optional[str] = Field(
        default=None, description="Optional transcription of the audio"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional context information"
    )


class ImagePromptRequest(BaseModel):
    """Request model for image-based prompts."""

    image_url: str = Field(..., description="URL to image file")
    caption: Optional[str] = Field(
        default=None, description="Optional caption for the image"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional context information"
    )


class VideoPromptRequest(BaseModel):
    """Request model for video-based prompts."""

    video_url: str = Field(..., description="URL to video file")
    description: Optional[str] = Field(
        default=None, description="Optional description of the video"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional context information"
    )


class SimulationPromptRequest(BaseModel):
    """Request model for simulation-based prompts."""

    scenario: str = Field(..., description="Scenario to simulate")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Simulation parameters"
    )
    expected_outcomes: Optional[List[str]] = Field(
        default=None, description="Expected outcomes"
    )
    duration: Optional[str] = Field(default=None, description="Simulation duration")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional context information"
    )


class MixedPromptRequest(BaseModel):
    """Request model for mixed multimodal prompts."""

    contents: List[Dict[str, Any]] = Field(
        ..., description="List of content pieces with type and data"
    )
    primary_type: str = Field(default="text", description="Primary content type")
    instruction: Optional[str] = Field(
        default=None, description="Optional instruction for processing"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional context information"
    )


class MultimodalResponse(BaseModel):
    """Response model for multimodal queries."""

    success: bool = Field(..., description="Whether the request was successful")
    response_id: str = Field(..., description="Unique response identifier")
    prompt_id: str = Field(..., description="Prompt identifier")
    content: str = Field(..., description="Response content")
    content_type: str = Field(default="text", description="Type of response content")
    processing_info: Dict[str, Any] = Field(
        default_factory=dict, description="Processing information"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )


# API Endpoints
@router.post("/text", response_model=MultimodalResponse)
async def process_text_prompt(
    request: TextPromptRequest, db: Session = Depends(get_db_sync)
):
    """
    Process a text-based prompt.

    Args:
        request: Text prompt request
        db: Database session

    Returns:
        Multimodal response
    """
    try:
        # Create text prompt
        generator = MultimodalPromptGenerator()
        prompt = generator.create_text_prompt(request.text, request.context)

        # Process with multimodal service
        service = MultimodalService(db)
        response = await service.process_prompt(prompt)

        return MultimodalResponse(
            success=response.success,
            response_id=response.response_id,
            prompt_id=response.prompt_id,
            content=response.content if isinstance(response.content, str) else str(response.content),
            content_type=response.content_type.value,
            processing_info=response.processing_info,
            error_message=response.error_message,
        )
    except Exception as e:
        logger.error(f"Error processing text prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice", response_model=MultimodalResponse)
async def process_voice_prompt(
    request: VoicePromptRequest, db: Session = Depends(get_db_sync)
):
    """
    Process a voice/audio-based prompt.

    Args:
        request: Voice prompt request
        db: Database session

    Returns:
        Multimodal response
    """
    try:
        if not request.audio_url and not request.transcription:
            raise HTTPException(
                status_code=400,
                detail="Either audio_url or transcription must be provided",
            )

        # Create voice prompt
        generator = MultimodalPromptGenerator()
        audio_data = request.audio_url or ""
        prompt = generator.create_voice_prompt(
            audio_data=audio_data,
            encoding="url" if request.audio_url else "text",
            transcription=request.transcription,
            context=request.context,
        )

        # Process with multimodal service
        service = MultimodalService(db)
        response = await service.process_prompt(prompt)

        return MultimodalResponse(
            success=response.success,
            response_id=response.response_id,
            prompt_id=response.prompt_id,
            content=response.content if isinstance(response.content, str) else str(response.content),
            content_type=response.content_type.value,
            processing_info=response.processing_info,
            error_message=response.error_message,
        )
    except Exception as e:
        logger.error(f"Error processing voice prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image", response_model=MultimodalResponse)
async def process_image_prompt(
    request: ImagePromptRequest, db: Session = Depends(get_db_sync)
):
    """
    Process an image-based prompt.

    Args:
        request: Image prompt request
        db: Database session

    Returns:
        Multimodal response
    """
    try:
        # Create image prompt
        generator = MultimodalPromptGenerator()
        prompt = generator.create_image_prompt(
            image_data=request.image_url,
            encoding="url",
            caption=request.caption,
            context=request.context,
        )

        # Process with multimodal service
        service = MultimodalService(db)
        response = await service.process_prompt(prompt)

        return MultimodalResponse(
            success=response.success,
            response_id=response.response_id,
            prompt_id=response.prompt_id,
            content=response.content if isinstance(response.content, str) else str(response.content),
            content_type=response.content_type.value,
            processing_info=response.processing_info,
            error_message=response.error_message,
        )
    except Exception as e:
        logger.error(f"Error processing image prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/video", response_model=MultimodalResponse)
async def process_video_prompt(
    request: VideoPromptRequest, db: Session = Depends(get_db_sync)
):
    """
    Process a video-based prompt.

    Args:
        request: Video prompt request
        db: Database session

    Returns:
        Multimodal response
    """
    try:
        # Create video prompt
        generator = MultimodalPromptGenerator()
        prompt = generator.create_video_prompt(
            video_data=request.video_url,
            encoding="url",
            description=request.description,
            context=request.context,
        )

        # Process with multimodal service
        service = MultimodalService(db)
        response = await service.process_prompt(prompt)

        return MultimodalResponse(
            success=response.success,
            response_id=response.response_id,
            prompt_id=response.prompt_id,
            content=response.content if isinstance(response.content, str) else str(response.content),
            content_type=response.content_type.value,
            processing_info=response.processing_info,
            error_message=response.error_message,
        )
    except Exception as e:
        logger.error(f"Error processing video prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulation", response_model=MultimodalResponse)
async def process_simulation_prompt(
    request: SimulationPromptRequest, db: Session = Depends(get_db_sync)
):
    """
    Process a simulation-based prompt.

    Args:
        request: Simulation prompt request
        db: Database session

    Returns:
        Multimodal response
    """
    try:
        # Create simulation query
        simulation_query = SimulationQuery(
            scenario=request.scenario,
            parameters=request.parameters,
            expected_outcomes=request.expected_outcomes,
            duration=request.duration,
            context=str(request.context) if request.context else None,
        )

        # Create simulation prompt
        generator = MultimodalPromptGenerator()
        prompt = generator.create_simulation_prompt(simulation_query, request.context)

        # Process with multimodal service
        service = MultimodalService(db)
        response = await service.process_prompt(prompt)

        return MultimodalResponse(
            success=response.success,
            response_id=response.response_id,
            prompt_id=response.prompt_id,
            content=response.content if isinstance(response.content, str) else str(response.content),
            content_type=response.content_type.value,
            processing_info=response.processing_info,
            error_message=response.error_message,
        )
    except Exception as e:
        logger.error(f"Error processing simulation prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mixed", response_model=MultimodalResponse)
async def process_mixed_prompt(
    request: MixedPromptRequest, db: Session = Depends(get_db_sync)
):
    """
    Process a mixed multimodal prompt with multiple content types.

    Args:
        request: Mixed prompt request
        db: Database session

    Returns:
        Multimodal response
    """
    try:
        # Create mixed prompt
        generator = MultimodalPromptGenerator()
        prompt = generator.create_mixed_prompt(
            contents=request.contents,
            primary_type=ContentType(request.primary_type),
            instruction=request.instruction,
            context=request.context,
        )

        # Process with multimodal service
        service = MultimodalService(db)
        response = await service.process_prompt(prompt)

        return MultimodalResponse(
            success=response.success,
            response_id=response.response_id,
            prompt_id=response.prompt_id,
            content=response.content if isinstance(response.content, str) else str(response.content),
            content_type=response.content_type.value,
            processing_info=response.processing_info,
            error_message=response.error_message,
        )
    except Exception as e:
        logger.error(f"Error processing mixed prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=Dict[str, Any])
async def upload_media(
    file: UploadFile = File(...),
    content_type: str = Form(...),
    caption: Optional[str] = Form(None),
):
    """
    Upload media file for multimodal processing.

    Args:
        file: Media file to upload
        content_type: Type of content (image, audio, video)
        caption: Optional caption or description

    Returns:
        Upload confirmation with file info
    """
    try:
        # Read file content
        content = await file.read()

        # Here you would typically:
        # 1. Validate file type and size
        # 2. Store file in cloud storage or local storage
        # 3. Return URL or identifier for later use

        return {
            "success": True,
            "filename": file.filename,
            "content_type": content_type,
            "size": len(content),
            "caption": caption,
            "message": "File uploaded successfully",
        }
    except Exception as e:
        logger.error(f"Error uploading media: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_multimodal_capabilities():
    """
    Get information about available multimodal capabilities.

    Returns:
        Dictionary of supported features and content types
    """
    return {
        "supported_content_types": [
            "text",
            "voice",
            "audio",
            "image",
            "video",
            "simulation",
            "mixed",
        ],
        "features": {
            "text_processing": True,
            "voice_transcription": True,
            "image_analysis": True,
            "video_processing": True,
            "simulation_generation": True,
            "mixed_content": True,
        },
        "endpoints": {
            "text": "/multimodal/text",
            "voice": "/multimodal/voice",
            "image": "/multimodal/image",
            "video": "/multimodal/video",
            "simulation": "/multimodal/simulation",
            "mixed": "/multimodal/mixed",
            "upload": "/multimodal/upload",
        },
    }
