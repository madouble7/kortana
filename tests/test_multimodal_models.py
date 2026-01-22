"""
Unit tests for multimodal models and schemas.
"""

import pytest
from datetime import datetime

from src.kortana.core.multimodal.models import (
    ContentType,
    MultimodalContent,
    MultimodalPrompt,
    MultimodalResponse,
    SimulationQuery,
)


class TestContentType:
    """Tests for ContentType enum."""

    def test_content_types_exist(self):
        """Test that all expected content types exist."""
        assert ContentType.TEXT == "text"
        assert ContentType.VOICE == "voice"
        assert ContentType.AUDIO == "audio"
        assert ContentType.VIDEO == "video"
        assert ContentType.IMAGE == "image"
        assert ContentType.SIMULATION == "simulation"
        assert ContentType.MIXED == "mixed"


class TestMultimodalContent:
    """Tests for MultimodalContent model."""

    def test_create_text_content(self):
        """Test creating text content."""
        content = MultimodalContent(
            content_type=ContentType.TEXT,
            data="Hello, world!",
        )
        assert content.content_type == ContentType.TEXT
        assert content.data == "Hello, world!"
        assert isinstance(content.timestamp, datetime)

    def test_create_image_content_with_url(self):
        """Test creating image content with URL."""
        content = MultimodalContent(
            content_type=ContentType.IMAGE,
            data="https://example.com/image.jpg",
            encoding="url",
        )
        assert content.content_type == ContentType.IMAGE
        assert content.data == "https://example.com/image.jpg"
        assert content.encoding == "url"

    def test_create_audio_content_with_metadata(self):
        """Test creating audio content with metadata."""
        content = MultimodalContent(
            content_type=ContentType.AUDIO,
            data="base64encodedaudio",
            encoding="base64",
            metadata={"duration": 120, "format": "mp3"},
        )
        assert content.content_type == ContentType.AUDIO
        assert content.metadata["duration"] == 120
        assert content.metadata["format"] == "mp3"

    def test_invalid_text_content_raises_error(self):
        """Test that non-string text content raises validation error."""
        with pytest.raises(ValueError):
            MultimodalContent(
                content_type=ContentType.TEXT,
                data=123,  # Should be string
            )


class TestSimulationQuery:
    """Tests for SimulationQuery model."""

    def test_create_basic_simulation_query(self):
        """Test creating a basic simulation query."""
        query = SimulationQuery(
            scenario="Test scenario",
            parameters={"param1": "value1"},
        )
        assert query.scenario == "Test scenario"
        assert query.parameters == {"param1": "value1"}

    def test_create_full_simulation_query(self):
        """Test creating a simulation query with all fields."""
        query = SimulationQuery(
            scenario="Complex scenario",
            parameters={"param1": "value1", "param2": 42},
            expected_outcomes=["outcome1", "outcome2"],
            context="Additional context",
            duration="1 hour",
        )
        assert query.scenario == "Complex scenario"
        assert len(query.expected_outcomes) == 2
        assert query.duration == "1 hour"


class TestMultimodalPrompt:
    """Tests for MultimodalPrompt model."""

    def test_create_simple_prompt(self):
        """Test creating a simple prompt with one content piece."""
        content = MultimodalContent(
            content_type=ContentType.TEXT,
            data="Test prompt",
        )
        prompt = MultimodalPrompt(
            contents=[content],
            primary_content_type=ContentType.TEXT,
        )
        assert len(prompt.contents) == 1
        assert prompt.primary_content_type == ContentType.TEXT

    def test_add_content_to_prompt(self):
        """Test adding content to an existing prompt."""
        content = MultimodalContent(
            content_type=ContentType.TEXT,
            data="Initial content",
        )
        prompt = MultimodalPrompt(
            contents=[content],
            primary_content_type=ContentType.TEXT,
        )

        prompt.add_content(
            content_type=ContentType.IMAGE,
            data="https://example.com/image.jpg",
            encoding="url",
        )

        assert len(prompt.contents) == 2
        assert prompt.contents[1].content_type == ContentType.IMAGE

    def test_get_contents_by_type(self):
        """Test filtering contents by type."""
        prompt = MultimodalPrompt(
            contents=[
                MultimodalContent(content_type=ContentType.TEXT, data="Text 1"),
                MultimodalContent(content_type=ContentType.IMAGE, data="img1.jpg"),
                MultimodalContent(content_type=ContentType.TEXT, data="Text 2"),
            ],
            primary_content_type=ContentType.TEXT,
        )

        text_contents = prompt.get_contents_by_type(ContentType.TEXT)
        assert len(text_contents) == 2

        image_contents = prompt.get_contents_by_type(ContentType.IMAGE)
        assert len(image_contents) == 1

    def test_has_content_type(self):
        """Test checking if prompt has specific content type."""
        prompt = MultimodalPrompt(
            contents=[
                MultimodalContent(content_type=ContentType.TEXT, data="Text"),
                MultimodalContent(content_type=ContentType.IMAGE, data="img.jpg"),
            ],
            primary_content_type=ContentType.TEXT,
        )

        assert prompt.has_content_type(ContentType.TEXT)
        assert prompt.has_content_type(ContentType.IMAGE)
        assert not prompt.has_content_type(ContentType.VIDEO)

    def test_prompt_requires_contents(self):
        """Test that prompt requires at least one content piece."""
        with pytest.raises(ValueError):
            MultimodalPrompt(
                contents=[],
                primary_content_type=ContentType.TEXT,
            )


class TestMultimodalResponse:
    """Tests for MultimodalResponse model."""

    def test_create_successful_response(self):
        """Test creating a successful response."""
        response = MultimodalResponse(
            prompt_id="prompt123",
            content="Response content",
            success=True,
        )
        assert response.success
        assert response.content == "Response content"
        assert response.error_message is None

    def test_create_error_response(self):
        """Test creating an error response."""
        response = MultimodalResponse(
            prompt_id="prompt123",
            content="Error occurred",
            success=False,
            error_message="Something went wrong",
        )
        assert not response.success
        assert response.error_message == "Something went wrong"

    def test_response_with_processing_info(self):
        """Test response with processing information."""
        response = MultimodalResponse(
            prompt_id="prompt123",
            content="Response",
            processing_info={
                "model": "gpt-4-vision",
                "tokens": 150,
            },
        )
        assert response.processing_info["model"] == "gpt-4-vision"
        assert response.processing_info["tokens"] == 150
