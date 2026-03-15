"""
Unit tests for multimodal prompt generator.
"""

import pytest

from src.kortana.core.multimodal.models import ContentType, SimulationQuery
from src.kortana.core.multimodal.prompt_generator import MultimodalPromptGenerator


class TestMultimodalPromptGenerator:
    """Tests for MultimodalPromptGenerator."""

    def test_initialization(self):
        """Test generator initialization."""
        generator = MultimodalPromptGenerator()
        assert generator.processor is not None

    def test_create_text_prompt(self):
        """Test creating a text prompt."""
        generator = MultimodalPromptGenerator()
        prompt = generator.create_text_prompt("Hello, world!")

        assert len(prompt.contents) == 1
        assert prompt.primary_content_type == ContentType.TEXT
        assert prompt.contents[0].data == "Hello, world!"

    def test_create_text_prompt_with_context(self):
        """Test creating a text prompt with context."""
        generator = MultimodalPromptGenerator()
        context = {"user": "test_user", "session": "123"}
        prompt = generator.create_text_prompt("Hello", context=context)

        assert prompt.context["user"] == "test_user"
        assert prompt.context["session"] == "123"

    def test_create_voice_prompt(self):
        """Test creating a voice prompt."""
        generator = MultimodalPromptGenerator()
        prompt = generator.create_voice_prompt(
            audio_data="https://example.com/audio.mp3",
            encoding="url",
        )

        assert prompt.primary_content_type == ContentType.AUDIO
        assert len(prompt.contents) == 1

    def test_create_voice_prompt_with_transcription(self):
        """Test creating a voice prompt with transcription."""
        generator = MultimodalPromptGenerator()
        prompt = generator.create_voice_prompt(
            audio_data="https://example.com/audio.mp3",
            encoding="url",
            transcription="This is the transcribed text",
        )

        assert len(prompt.contents) == 2  # Audio + text
        text_contents = prompt.get_contents_by_type(ContentType.TEXT)
        assert len(text_contents) == 1
        assert text_contents[0].data == "This is the transcribed text"

    def test_create_video_prompt(self):
        """Test creating a video prompt."""
        generator = MultimodalPromptGenerator()
        prompt = generator.create_video_prompt(
            video_data="https://example.com/video.mp4",
            encoding="url",
        )

        assert prompt.primary_content_type == ContentType.VIDEO
        assert len(prompt.contents) == 1

    def test_create_video_prompt_with_description(self):
        """Test creating a video prompt with description."""
        generator = MultimodalPromptGenerator()
        prompt = generator.create_video_prompt(
            video_data="https://example.com/video.mp4",
            encoding="url",
            description="A video showing...",
        )

        assert len(prompt.contents) == 2  # Video + text
        text_contents = prompt.get_contents_by_type(ContentType.TEXT)
        assert len(text_contents) == 1

    def test_create_image_prompt(self):
        """Test creating an image prompt."""
        generator = MultimodalPromptGenerator()
        prompt = generator.create_image_prompt(
            image_data="https://example.com/image.jpg",
            encoding="url",
        )

        assert prompt.primary_content_type == ContentType.IMAGE
        assert len(prompt.contents) == 1

    def test_create_image_prompt_with_caption(self):
        """Test creating an image prompt with caption."""
        generator = MultimodalPromptGenerator()
        prompt = generator.create_image_prompt(
            image_data="https://example.com/image.jpg",
            encoding="url",
            caption="A beautiful sunset",
        )

        assert len(prompt.contents) == 2  # Image + text
        text_contents = prompt.get_contents_by_type(ContentType.TEXT)
        assert text_contents[0].data == "A beautiful sunset"

    def test_create_simulation_prompt(self):
        """Test creating a simulation prompt."""
        generator = MultimodalPromptGenerator()
        simulation_query = SimulationQuery(
            scenario="Test scenario",
            parameters={"param1": "value1"},
        )
        prompt = generator.create_simulation_prompt(simulation_query)

        assert prompt.primary_content_type == ContentType.SIMULATION
        assert len(prompt.contents) == 1

    def test_create_mixed_prompt(self):
        """Test creating a mixed multimodal prompt."""
        generator = MultimodalPromptGenerator()
        contents = [
            {"type": "text", "data": "Text content"},
            {"type": "image", "data": "https://example.com/image.jpg", "encoding": "url"},
            {"type": "audio", "data": "https://example.com/audio.mp3", "encoding": "url"},
        ]
        prompt = generator.create_mixed_prompt(contents, primary_type=ContentType.TEXT)

        assert len(prompt.contents) == 3
        assert prompt.primary_content_type == ContentType.TEXT
        assert prompt.has_content_type(ContentType.TEXT)
        assert prompt.has_content_type(ContentType.IMAGE)
        assert prompt.has_content_type(ContentType.AUDIO)

    def test_create_mixed_prompt_with_instruction(self):
        """Test creating a mixed prompt with instruction."""
        generator = MultimodalPromptGenerator()
        contents = [{"type": "text", "data": "Content"}]
        instruction = "Please analyze this content"
        prompt = generator.create_mixed_prompt(
            contents, primary_type=ContentType.TEXT, instruction=instruction
        )

        assert prompt.instruction == instruction

    def test_enhance_prompt_with_context(self):
        """Test enhancing prompt with memory context."""
        generator = MultimodalPromptGenerator()
        prompt = generator.create_text_prompt("Original text")

        memory_context = [
            {"memory": "Previous conversation 1"},
            {"memory": "Previous conversation 2"},
        ]
        enhanced_prompt = generator.enhance_prompt_with_context(prompt, memory_context)

        assert "memory" in enhanced_prompt.context
        assert len(enhanced_prompt.context["memory"]) == 2

    def test_validate_valid_prompt(self):
        """Test validating a valid prompt."""
        generator = MultimodalPromptGenerator()
        prompt = generator.create_text_prompt("Valid text")

        assert generator.validate_prompt(prompt) is True

    def test_to_llm_format(self):
        """Test converting prompt to LLM format."""
        generator = MultimodalPromptGenerator()
        prompt = generator.create_text_prompt("Test text")

        llm_format = generator.to_llm_format(prompt)

        assert "prompt_id" in llm_format
        assert "contents" in llm_format
        assert "primary_content_type" in llm_format
        assert llm_format["primary_content_type"] == "text"
