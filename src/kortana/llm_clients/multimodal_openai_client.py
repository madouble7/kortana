"""
Multimodal-enhanced OpenAI client for Kor'tana.

This module extends the OpenAI client to support multimodal inputs
including images (GPT-4 Vision) and audio processing capabilities.
"""

import logging
from typing import Any, Dict, List, Optional

from ..core.multimodal.models import ContentType, MultimodalPrompt
from ..core.multimodal.utils import prepare_image_for_llm
from .openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class MultimodalOpenAIClient(OpenAIClient):
    """
    Enhanced OpenAI client with multimodal capabilities.

    Supports:
    - GPT-4 Vision for image understanding
    - Text-to-speech and speech-to-text
    - Combined multimodal prompts
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gpt-4-vision-preview",
        **kwargs,
    ):
        """
        Initialize the multimodal OpenAI client.

        Args:
            api_key: OpenAI API key
            model_name: Model to use (defaults to gpt-4-vision-preview for vision support)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model_name, **kwargs)
        self.vision_enabled = "vision" in model_name.lower() or "gpt-4" in model_name.lower()

    def supports_multimodal(self) -> bool:
        """Check if multimodal inputs are supported."""
        return True

    def supports_vision(self) -> bool:
        """Check if vision/image inputs are supported."""
        return self.vision_enabled

    def supports_audio(self) -> bool:
        """Check if audio inputs are supported."""
        # OpenAI supports audio via Whisper API
        return True

    def get_capabilities(self) -> Dict[str, Any]:
        """Get client capabilities."""
        capabilities = {
            "provider": "openai",
            "model": self.model_name,
            "supports_vision": self.supports_vision(),
            "supports_audio": self.supports_audio(),
            "supports_streaming": True,
            "supports_function_calling": True,
        }
        return capabilities

    def generate_multimodal_response(
        self,
        system_prompt: str,
        messages: list,
        multimodal_content: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate a response with multimodal content.

        Args:
            system_prompt: System instructions
            messages: Conversation messages
            multimodal_content: Multimodal content (processed format)
            **kwargs: Additional parameters

        Returns:
            Response dictionary
        """
        if not multimodal_content:
            return self.generate_response(system_prompt, messages, **kwargs)

        # Convert multimodal content to OpenAI format
        enhanced_messages = self._prepare_multimodal_messages(
            messages, multimodal_content
        )

        # Use the standard generate_response with enhanced messages
        return self.generate_response(system_prompt, enhanced_messages, **kwargs)

    def _prepare_multimodal_messages(
        self, messages: list, multimodal_content: Dict[str, Any]
    ) -> list:
        """
        Prepare messages with multimodal content for OpenAI API.

        Args:
            messages: Original messages
            multimodal_content: Multimodal content to add

        Returns:
            Enhanced messages list
        """
        enhanced_messages = messages.copy()

        # Process contents from multimodal_content
        contents = multimodal_content.get("contents", [])
        multimodal_parts = []

        for content in contents:
            content_type = content.get("type")

            if content_type == "text":
                multimodal_parts.append({"type": "text", "text": content.get("text", "")})

            elif content_type == "image" and self.supports_vision():
                # Prepare image for vision model
                image_data = content.get("image_data") or content.get("image_url")
                if image_data:
                    try:
                        image_part = prepare_image_for_llm(
                            image_data, content.get("format", "url")
                        )
                        multimodal_parts.append(image_part)
                    except Exception as e:
                        logger.error(f"Error preparing image: {e}")

            elif content_type == "audio":
                # For audio, we would typically transcribe first
                # This is a placeholder for audio handling
                if "transcription" in content:
                    multimodal_parts.append(
                        {"type": "text", "text": f"[Audio transcription: {content['transcription']}]"}
                    )
                else:
                    multimodal_parts.append(
                        {"type": "text", "text": "[Audio content provided]"}
                    )

            elif content_type == "video":
                # Video processing would require frame extraction
                # This is a placeholder
                if "description" in content:
                    multimodal_parts.append(
                        {"type": "text", "text": f"[Video description: {content['description']}]"}
                    )
                else:
                    multimodal_parts.append(
                        {"type": "text", "text": "[Video content provided]"}
                    )

        # Add multimodal parts to the last user message or create a new one
        if multimodal_parts:
            if enhanced_messages and enhanced_messages[-1].get("role") == "user":
                # Enhance existing message with multimodal content
                last_message = enhanced_messages[-1]
                if isinstance(last_message.get("content"), str):
                    # Convert simple text to multimodal format
                    enhanced_messages[-1]["content"] = [
                        {"type": "text", "text": last_message["content"]}
                    ] + multimodal_parts
                else:
                    # Already multimodal, append
                    enhanced_messages[-1]["content"].extend(multimodal_parts)
            else:
                # Create new user message with multimodal content
                enhanced_messages.append({"role": "user", "content": multimodal_parts})

        return enhanced_messages

    def process_multimodal_prompt(self, prompt: MultimodalPrompt) -> Dict[str, Any]:
        """
        Process a MultimodalPrompt object and generate a response.

        Args:
            prompt: MultimodalPrompt object

        Returns:
            Response dictionary
        """
        from ..core.multimodal.processors import MultimodalProcessor

        # Process the prompt
        processor = MultimodalProcessor()
        processed_content = processor.process_prompt(prompt)

        # Build messages
        messages = []
        if prompt.instruction:
            messages.append({"role": "system", "content": prompt.instruction})

        # Use generate_multimodal_response
        system_prompt = prompt.instruction or "You are a helpful AI assistant."
        return self.generate_multimodal_response(
            system_prompt=system_prompt,
            messages=messages,
            multimodal_content=processed_content,
        )

    def transcribe_audio(self, audio_file: Any, language: Optional[str] = None) -> str:
        """
        Transcribe audio using OpenAI Whisper.

        Args:
            audio_file: Audio file to transcribe
            language: Optional language code

        Returns:
            Transcribed text
        """
        try:
            params = {}
            if language:
                params["language"] = language

            transcript = self.client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, **params
            )
            return transcript.text
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""

    def generate_speech(
        self, text: str, voice: str = "alloy", model: str = "tts-1"
    ) -> bytes:
        """
        Generate speech from text using OpenAI TTS.

        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            model: TTS model to use

        Returns:
            Audio data as bytes
        """
        try:
            response = self.client.audio.speech.create(
                model=model, voice=voice, input=text
            )
            return response.content
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return b""
