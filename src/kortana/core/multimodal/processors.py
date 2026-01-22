"""
Multimodal content processors for handling different content types.

This module provides processors for text, voice, video, and simulation-based content,
ensuring each type is properly validated and prepared for AI processing.
"""

import base64
import logging
from typing import Any, Dict, Optional, Union

from .models import ContentType, MultimodalContent, MultimodalPrompt

logger = logging.getLogger(__name__)


class ContentProcessor:
    """Base class for content processors."""

    def process(self, content: MultimodalContent) -> Dict[str, Any]:
        """
        Process a piece of multimodal content.

        Args:
            content: The content to process

        Returns:
            Processed content as a dictionary
        """
        raise NotImplementedError


class TextProcessor(ContentProcessor):
    """Processor for text content."""

    def process(self, content: MultimodalContent) -> Dict[str, Any]:
        """Process text content."""
        if not isinstance(content.data, str):
            raise ValueError("Text content must be a string")

        return {
            "type": "text",
            "text": content.data,
            "metadata": content.metadata,
        }


class VoiceProcessor(ContentProcessor):
    """Processor for voice/audio content."""

    def process(self, content: MultimodalContent) -> Dict[str, Any]:
        """
        Process voice/audio content.

        Handles both base64-encoded audio and URLs to audio files.
        """
        processed = {
            "type": "audio",
            "metadata": content.metadata,
        }

        if isinstance(content.data, str):
            if content.encoding == "base64":
                processed["audio_data"] = content.data
                processed["format"] = "base64"
            elif content.encoding == "url":
                processed["audio_url"] = content.data
                processed["format"] = "url"
            else:
                # Assume raw base64 or URL
                if content.data.startswith("http"):
                    processed["audio_url"] = content.data
                    processed["format"] = "url"
                else:
                    processed["audio_data"] = content.data
                    processed["format"] = "base64"
        elif isinstance(content.data, bytes):
            # Convert bytes to base64
            processed["audio_data"] = base64.b64encode(content.data).decode("utf-8")
            processed["format"] = "base64"

        return processed


class VideoProcessor(ContentProcessor):
    """Processor for video content."""

    def process(self, content: MultimodalContent) -> Dict[str, Any]:
        """
        Process video content.

        Handles both video data and URLs to video files.
        """
        processed = {
            "type": "video",
            "metadata": content.metadata,
        }

        if isinstance(content.data, str):
            if content.encoding == "url":
                processed["video_url"] = content.data
                processed["format"] = "url"
            else:
                # Assume base64 or URL
                if content.data.startswith("http"):
                    processed["video_url"] = content.data
                    processed["format"] = "url"
                else:
                    processed["video_data"] = content.data
                    processed["format"] = "base64"
        elif isinstance(content.data, bytes):
            # Convert bytes to base64
            processed["video_data"] = base64.b64encode(content.data).decode("utf-8")
            processed["format"] = "base64"

        return processed


class ImageProcessor(ContentProcessor):
    """Processor for image content."""

    def process(self, content: MultimodalContent) -> Dict[str, Any]:
        """
        Process image content.

        Handles both image data and URLs to image files.
        """
        processed = {
            "type": "image",
            "metadata": content.metadata,
        }

        if isinstance(content.data, str):
            if content.encoding == "url":
                processed["image_url"] = content.data
                processed["format"] = "url"
            else:
                # Assume base64 or URL
                if content.data.startswith("http"):
                    processed["image_url"] = content.data
                    processed["format"] = "url"
                else:
                    processed["image_data"] = content.data
                    processed["format"] = "base64"
        elif isinstance(content.data, bytes):
            # Convert bytes to base64
            processed["image_data"] = base64.b64encode(content.data).decode("utf-8")
            processed["format"] = "base64"

        return processed


class SimulationProcessor(ContentProcessor):
    """Processor for simulation-based queries."""

    def process(self, content: MultimodalContent) -> Dict[str, Any]:
        """
        Process simulation content.

        Converts simulation queries into structured format for AI processing.
        """
        if not isinstance(content.data, dict):
            raise ValueError("Simulation content must be a dictionary")

        simulation_data = content.data
        processed = {
            "type": "simulation",
            "scenario": simulation_data.get("scenario", ""),
            "parameters": simulation_data.get("parameters", {}),
            "expected_outcomes": simulation_data.get("expected_outcomes", []),
            "context": simulation_data.get("context", ""),
            "duration": simulation_data.get("duration", ""),
            "metadata": content.metadata,
        }

        return processed


class MultimodalProcessor:
    """
    Main processor for handling multimodal prompts.

    This processor coordinates the processing of different content types
    and prepares them for AI model consumption.
    """

    def __init__(self):
        """Initialize the multimodal processor with specific content processors."""
        self.processors = {
            ContentType.TEXT: TextProcessor(),
            ContentType.VOICE: VoiceProcessor(),
            ContentType.AUDIO: VoiceProcessor(),  # Voice and audio use same processor
            ContentType.VIDEO: VideoProcessor(),
            ContentType.IMAGE: ImageProcessor(),
            ContentType.SIMULATION: SimulationProcessor(),
        }

    def process_prompt(self, prompt: MultimodalPrompt) -> Dict[str, Any]:
        """
        Process a complete multimodal prompt.

        Args:
            prompt: The multimodal prompt to process

        Returns:
            Processed prompt data ready for AI consumption
        """
        processed_contents = []

        for content in prompt.contents:
            processor = self.processors.get(content.content_type)
            if not processor:
                logger.warning(f"No processor for content type: {content.content_type}")
                continue

            try:
                processed = processor.process(content)
                processed_contents.append(processed)
            except Exception as e:
                logger.error(
                    f"Error processing content type {content.content_type}: {str(e)}"
                )
                continue

        return {
            "prompt_id": prompt.prompt_id,
            "contents": processed_contents,
            "primary_content_type": prompt.primary_content_type.value,
            "instruction": prompt.instruction,
            "context": prompt.context,
            "metadata": prompt.metadata,
        }

    def validate_content(self, content: MultimodalContent) -> bool:
        """
        Validate a piece of multimodal content.

        Args:
            content: The content to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            processor = self.processors.get(content.content_type)
            if not processor:
                return False
            processor.process(content)
            return True
        except Exception as e:
            logger.error(f"Content validation failed: {str(e)}")
            return False
