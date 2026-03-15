"""
Integration tests for multimodal API endpoints.
"""

import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.kortana.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


class TestMultimodalAPIEndpoints:
    """Integration tests for multimodal API endpoints."""

    def test_health_check(self, client):
        """Test that the health check endpoint works."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_multimodal_capabilities_endpoint(self, client):
        """Test the multimodal capabilities endpoint."""
        response = client.get("/multimodal/capabilities")
        assert response.status_code == 200

        data = response.json()
        assert "supported_content_types" in data
        assert "text" in data["supported_content_types"]
        assert "image" in data["supported_content_types"]
        assert "video" in data["supported_content_types"]
        assert "simulation" in data["supported_content_types"]

    @patch("src.kortana.services.multimodal_service.MultimodalService.process_prompt")
    def test_text_prompt_endpoint(self, mock_process, client):
        """Test the text prompt endpoint."""
        from src.kortana.core.multimodal.models import ContentType, MultimodalResponse

        # Mock the response
        mock_response = MultimodalResponse(
            prompt_id="test123",
            content="Test response",
            content_type=ContentType.TEXT,
            success=True,
        )
        mock_process.return_value = mock_response

        response = client.post(
            "/multimodal/text",
            json={"text": "Hello, world!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "response_id" in data
        assert "prompt_id" in data

    @patch("src.kortana.services.multimodal_service.MultimodalService.process_prompt")
    def test_image_prompt_endpoint(self, mock_process, client):
        """Test the image prompt endpoint."""
        from src.kortana.core.multimodal.models import ContentType, MultimodalResponse

        # Mock the response
        mock_response = MultimodalResponse(
            prompt_id="test123",
            content="Image analysis result",
            content_type=ContentType.TEXT,
            success=True,
        )
        mock_process.return_value = mock_response

        response = client.post(
            "/multimodal/image",
            json={
                "image_url": "https://example.com/image.jpg",
                "caption": "A test image",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("src.kortana.services.multimodal_service.MultimodalService.process_prompt")
    def test_voice_prompt_endpoint_with_url(self, mock_process, client):
        """Test the voice prompt endpoint with audio URL."""
        from src.kortana.core.multimodal.models import ContentType, MultimodalResponse

        # Mock the response
        mock_response = MultimodalResponse(
            prompt_id="test123",
            content="Voice processing result",
            content_type=ContentType.TEXT,
            success=True,
        )
        mock_process.return_value = mock_response

        response = client.post(
            "/multimodal/voice",
            json={"audio_url": "https://example.com/audio.mp3"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_voice_prompt_endpoint_missing_data(self, client):
        """Test voice endpoint returns error when no audio data provided."""
        response = client.post("/multimodal/voice", json={})

        assert response.status_code == 400

    @patch("src.kortana.services.multimodal_service.MultimodalService.process_prompt")
    def test_video_prompt_endpoint(self, mock_process, client):
        """Test the video prompt endpoint."""
        from src.kortana.core.multimodal.models import ContentType, MultimodalResponse

        # Mock the response
        mock_response = MultimodalResponse(
            prompt_id="test123",
            content="Video analysis result",
            content_type=ContentType.TEXT,
            success=True,
        )
        mock_process.return_value = mock_response

        response = client.post(
            "/multimodal/video",
            json={
                "video_url": "https://example.com/video.mp4",
                "description": "A test video",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("src.kortana.services.multimodal_service.MultimodalService.process_prompt")
    def test_simulation_prompt_endpoint(self, mock_process, client):
        """Test the simulation prompt endpoint."""
        from src.kortana.core.multimodal.models import ContentType, MultimodalResponse

        # Mock the response
        mock_response = MultimodalResponse(
            prompt_id="test123",
            content="Simulation result",
            content_type=ContentType.TEXT,
            success=True,
        )
        mock_process.return_value = mock_response

        response = client.post(
            "/multimodal/simulation",
            json={
                "scenario": "Test scenario",
                "parameters": {"param1": "value1"},
                "expected_outcomes": ["outcome1", "outcome2"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("src.kortana.services.multimodal_service.MultimodalService.process_prompt")
    def test_mixed_prompt_endpoint(self, mock_process, client):
        """Test the mixed multimodal prompt endpoint."""
        from src.kortana.core.multimodal.models import ContentType, MultimodalResponse

        # Mock the response
        mock_response = MultimodalResponse(
            prompt_id="test123",
            content="Mixed content result",
            content_type=ContentType.TEXT,
            success=True,
        )
        mock_process.return_value = mock_response

        response = client.post(
            "/multimodal/mixed",
            json={
                "contents": [
                    {"type": "text", "data": "Text content"},
                    {"type": "image", "data": "https://example.com/image.jpg", "encoding": "url"},
                ],
                "primary_type": "text",
                "instruction": "Analyze this content",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestMultimodalAPIErrorHandling:
    """Tests for error handling in multimodal API."""

    def test_invalid_json_returns_422(self, client):
        """Test that invalid JSON returns 422 status code."""
        response = client.post(
            "/multimodal/text",
            data="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @patch("src.kortana.services.multimodal_service.MultimodalService.process_prompt")
    def test_service_error_returns_500(self, mock_process, client):
        """Test that service errors return 500 status code."""
        mock_process.side_effect = Exception("Service error")

        response = client.post(
            "/multimodal/text",
            json={"text": "Test"},
        )

        assert response.status_code == 500
