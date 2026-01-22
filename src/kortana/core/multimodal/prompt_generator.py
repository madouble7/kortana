"""
Multimodal prompt generator for creating advanced AI prompts.

This module provides tools for generating prompts from various content types
and combining them into coherent multimodal prompts for AI processing.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from .models import (
    ContentType,
    MultimodalContent,
    MultimodalPrompt,
    SimulationQuery,
)
from .processors import MultimodalProcessor

logger = logging.getLogger(__name__)


class MultimodalPromptGenerator:
    """
    Generator for creating multimodal prompts from various input types.

    This class provides methods for building prompts that can include
    text, voice, video, images, and simulation-based queries.
    """

    def __init__(self):
        """Initialize the prompt generator."""
        self.processor = MultimodalProcessor()

    def create_text_prompt(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> MultimodalPrompt:
        """
        Create a simple text-based prompt.

        Args:
            text: The text content
            context: Optional context information

        Returns:
            A multimodal prompt with text content
        """
        content = MultimodalContent(content_type=ContentType.TEXT, data=text)

        prompt = MultimodalPrompt(
            contents=[content],
            primary_content_type=ContentType.TEXT,
            context=context or {},
        )

        return prompt

    def create_voice_prompt(
        self,
        audio_data: Union[str, bytes],
        encoding: str = "base64",
        transcription: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> MultimodalPrompt:
        """
        Create a voice/audio-based prompt.

        Args:
            audio_data: Audio data (base64 string, bytes, or URL)
            encoding: Encoding format ("base64", "url", or "raw")
            transcription: Optional text transcription of the audio
            context: Optional context information

        Returns:
            A multimodal prompt with voice content
        """
        contents = []

        # Add audio content
        audio_content = MultimodalContent(
            content_type=ContentType.AUDIO,
            data=audio_data,
            encoding=encoding,
            metadata={"has_transcription": transcription is not None},
        )
        contents.append(audio_content)

        # Add transcription if available
        if transcription:
            text_content = MultimodalContent(
                content_type=ContentType.TEXT,
                data=transcription,
                metadata={"source": "voice_transcription"},
            )
            contents.append(text_content)

        prompt = MultimodalPrompt(
            contents=contents,
            primary_content_type=ContentType.AUDIO,
            context=context or {},
        )

        return prompt

    def create_video_prompt(
        self,
        video_data: Union[str, bytes],
        encoding: str = "url",
        description: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> MultimodalPrompt:
        """
        Create a video-based prompt.

        Args:
            video_data: Video data (URL, base64 string, or bytes)
            encoding: Encoding format ("url", "base64", or "raw")
            description: Optional text description of the video
            context: Optional context information

        Returns:
            A multimodal prompt with video content
        """
        contents = []

        # Add video content
        video_content = MultimodalContent(
            content_type=ContentType.VIDEO,
            data=video_data,
            encoding=encoding,
            metadata={"has_description": description is not None},
        )
        contents.append(video_content)

        # Add description if available
        if description:
            text_content = MultimodalContent(
                content_type=ContentType.TEXT,
                data=description,
                metadata={"source": "video_description"},
            )
            contents.append(text_content)

        prompt = MultimodalPrompt(
            contents=contents,
            primary_content_type=ContentType.VIDEO,
            context=context or {},
        )

        return prompt

    def create_image_prompt(
        self,
        image_data: Union[str, bytes],
        encoding: str = "url",
        caption: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> MultimodalPrompt:
        """
        Create an image-based prompt.

        Args:
            image_data: Image data (URL, base64 string, or bytes)
            encoding: Encoding format ("url", "base64", or "raw")
            caption: Optional text caption for the image
            context: Optional context information

        Returns:
            A multimodal prompt with image content
        """
        contents = []

        # Add image content
        image_content = MultimodalContent(
            content_type=ContentType.IMAGE,
            data=image_data,
            encoding=encoding,
            metadata={"has_caption": caption is not None},
        )
        contents.append(image_content)

        # Add caption if available
        if caption:
            text_content = MultimodalContent(
                content_type=ContentType.TEXT,
                data=caption,
                metadata={"source": "image_caption"},
            )
            contents.append(text_content)

        prompt = MultimodalPrompt(
            contents=contents,
            primary_content_type=ContentType.IMAGE,
            context=context or {},
        )

        return prompt

    def create_simulation_prompt(
        self, simulation_query: SimulationQuery, context: Optional[Dict[str, Any]] = None
    ) -> MultimodalPrompt:
        """
        Create a simulation-based prompt.

        Args:
            simulation_query: The simulation query specification
            context: Optional context information

        Returns:
            A multimodal prompt with simulation content
        """
        # Convert simulation query to dict
        simulation_data = simulation_query.dict()

        simulation_content = MultimodalContent(
            content_type=ContentType.SIMULATION,
            data=simulation_data,
            metadata={"query_type": "simulation"},
        )

        prompt = MultimodalPrompt(
            contents=[simulation_content],
            primary_content_type=ContentType.SIMULATION,
            context=context or {},
        )

        return prompt

    def create_mixed_prompt(
        self,
        contents: List[Dict[str, Any]],
        primary_type: ContentType = ContentType.TEXT,
        instruction: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> MultimodalPrompt:
        """
        Create a mixed multimodal prompt with multiple content types.

        Args:
            contents: List of content dictionaries with 'type', 'data', and optional 'encoding'
            primary_type: The primary content type
            instruction: Optional instruction for processing the prompt
            context: Optional context information

        Returns:
            A multimodal prompt with mixed content
        """
        multimodal_contents = []

        for content_spec in contents:
            content_type = ContentType(content_spec["type"])
            data = content_spec["data"]
            encoding = content_spec.get("encoding")
            metadata = content_spec.get("metadata", {})

            content = MultimodalContent(
                content_type=content_type,
                data=data,
                encoding=encoding,
                metadata=metadata,
            )
            multimodal_contents.append(content)

        prompt = MultimodalPrompt(
            contents=multimodal_contents,
            primary_content_type=primary_type,
            instruction=instruction,
            context=context or {},
        )

        return prompt

    def enhance_prompt_with_context(
        self, prompt: MultimodalPrompt, memory_context: Optional[List[Any]] = None
    ) -> MultimodalPrompt:
        """
        Enhance a prompt with additional context from memory or other sources.

        Args:
            prompt: The original prompt
            memory_context: Optional memory context to add

        Returns:
            Enhanced prompt with additional context
        """
        if memory_context:
            # Add memory context to the prompt's context
            prompt.context["memory"] = memory_context

        return prompt

    def validate_prompt(self, prompt: MultimodalPrompt) -> bool:
        """
        Validate a multimodal prompt.

        Args:
            prompt: The prompt to validate

        Returns:
            True if valid, False otherwise
        """
        if not prompt.contents:
            logger.error("Prompt has no contents")
            return False

        # Validate each content piece
        for content in prompt.contents:
            if not self.processor.validate_content(content):
                logger.error(f"Invalid content: {content.content_type}")
                return False

        return True

    def to_llm_format(self, prompt: MultimodalPrompt) -> Dict[str, Any]:
        """
        Convert a multimodal prompt to a format suitable for LLM processing.

        Args:
            prompt: The prompt to convert

        Returns:
            Dictionary formatted for LLM consumption
        """
        return self.processor.process_prompt(prompt)
