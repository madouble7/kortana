"""
Unit tests for multimodal processors.
"""

import pytest

from src.kortana.core.multimodal.models import ContentType, MultimodalContent, MultimodalPrompt
from src.kortana.core.multimodal.processors import (
    ImageProcessor,
    MultimodalProcessor,
    SimulationProcessor,
    TextProcessor,
    VideoProcessor,
    VoiceProcessor,
)


class TestTextProcessor:
    """Tests for TextProcessor."""

    def test_process_text_content(self):
        """Test processing text content."""
        content = MultimodalContent(
            content_type=ContentType.TEXT,
            data="Hello, world!",
        )
        processor = TextProcessor()
        result = processor.process(content)

        assert result["type"] == "text"
        assert result["text"] == "Hello, world!"

    def test_process_text_with_metadata(self):
        """Test processing text content with metadata."""
        content = MultimodalContent(
            content_type=ContentType.TEXT,
            data="Test text",
            metadata={"source": "user_input"},
        )
        processor = TextProcessor()
        result = processor.process(content)

        assert result["metadata"]["source"] == "user_input"


class TestVoiceProcessor:
    """Tests for VoiceProcessor."""

    def test_process_voice_url(self):
        """Test processing voice content with URL."""
        content = MultimodalContent(
            content_type=ContentType.AUDIO,
            data="https://example.com/audio.mp3",
            encoding="url",
        )
        processor = VoiceProcessor()
        result = processor.process(content)

        assert result["type"] == "audio"
        assert result["audio_url"] == "https://example.com/audio.mp3"
        assert result["format"] == "url"

    def test_process_voice_base64(self):
        """Test processing voice content with base64."""
        content = MultimodalContent(
            content_type=ContentType.AUDIO,
            data="base64encodedaudio",
            encoding="base64",
        )
        processor = VoiceProcessor()
        result = processor.process(content)

        assert result["type"] == "audio"
        assert result["audio_data"] == "base64encodedaudio"
        assert result["format"] == "base64"

    def test_process_voice_bytes(self):
        """Test processing voice content from bytes."""
        content = MultimodalContent(
            content_type=ContentType.AUDIO,
            data=b"audio bytes",
        )
        processor = VoiceProcessor()
        result = processor.process(content)

        assert result["type"] == "audio"
        assert "audio_data" in result
        assert result["format"] == "base64"


class TestImageProcessor:
    """Tests for ImageProcessor."""

    def test_process_image_url(self):
        """Test processing image content with URL."""
        content = MultimodalContent(
            content_type=ContentType.IMAGE,
            data="https://example.com/image.jpg",
            encoding="url",
        )
        processor = ImageProcessor()
        result = processor.process(content)

        assert result["type"] == "image"
        assert result["image_url"] == "https://example.com/image.jpg"
        assert result["format"] == "url"

    def test_process_image_base64(self):
        """Test processing image content with base64."""
        content = MultimodalContent(
            content_type=ContentType.IMAGE,
            data="base64imagedata",
        )
        processor = ImageProcessor()
        result = processor.process(content)

        assert result["type"] == "image"
        assert result["image_data"] == "base64imagedata"


class TestVideoProcessor:
    """Tests for VideoProcessor."""

    def test_process_video_url(self):
        """Test processing video content with URL."""
        content = MultimodalContent(
            content_type=ContentType.VIDEO,
            data="https://example.com/video.mp4",
            encoding="url",
        )
        processor = VideoProcessor()
        result = processor.process(content)

        assert result["type"] == "video"
        assert result["video_url"] == "https://example.com/video.mp4"
        assert result["format"] == "url"


class TestSimulationProcessor:
    """Tests for SimulationProcessor."""

    def test_process_simulation_content(self):
        """Test processing simulation content."""
        content = MultimodalContent(
            content_type=ContentType.SIMULATION,
            data={
                "scenario": "Test scenario",
                "parameters": {"param1": "value1"},
                "expected_outcomes": ["outcome1"],
            },
        )
        processor = SimulationProcessor()
        result = processor.process(content)

        assert result["type"] == "simulation"
        assert result["scenario"] == "Test scenario"
        assert result["parameters"]["param1"] == "value1"
        assert "outcome1" in result["expected_outcomes"]

    def test_process_simulation_requires_dict(self):
        """Test that simulation processor requires dict data."""
        content = MultimodalContent(
            content_type=ContentType.SIMULATION,
            data="not a dict",
        )
        processor = SimulationProcessor()

        with pytest.raises(ValueError):
            processor.process(content)


class TestMultimodalProcessor:
    """Tests for MultimodalProcessor."""

    def test_processor_initialization(self):
        """Test multimodal processor initialization."""
        processor = MultimodalProcessor()
        assert ContentType.TEXT in processor.processors
        assert ContentType.AUDIO in processor.processors
        assert ContentType.IMAGE in processor.processors
        assert ContentType.VIDEO in processor.processors
        assert ContentType.SIMULATION in processor.processors

    def test_process_multimodal_prompt(self):
        """Test processing a complete multimodal prompt."""
        prompt = MultimodalPrompt(
            contents=[
                MultimodalContent(content_type=ContentType.TEXT, data="Text content"),
                MultimodalContent(
                    content_type=ContentType.IMAGE,
                    data="https://example.com/image.jpg",
                    encoding="url",
                ),
            ],
            primary_content_type=ContentType.TEXT,
        )

        processor = MultimodalProcessor()
        result = processor.process_prompt(prompt)

        assert result["prompt_id"] == prompt.prompt_id
        assert result["primary_content_type"] == "text"
        assert len(result["contents"]) == 2

    def test_validate_content_success(self):
        """Test validating valid content."""
        content = MultimodalContent(
            content_type=ContentType.TEXT,
            data="Valid text",
        )
        processor = MultimodalProcessor()

        assert processor.validate_content(content) is True

    def test_validate_content_failure(self):
        """Test validating invalid content."""
        # Create content with unsupported type
        content = MultimodalContent(
            content_type=ContentType.TEXT,
            data=123,  # Invalid for text
        )
        processor = MultimodalProcessor()

        # Should catch the validation error
        assert processor.validate_content(content) is False
