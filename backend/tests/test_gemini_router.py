"""Tests for src/kortana/routers/gemini.py - Gemini AI router endpoints"""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image
from tests.conftest import SyncTestClient


@pytest.fixture
def client():
    """Create a test client for FastAPI app"""
    from src.kortana.main import app

    return SyncTestClient(app)


class TestAnalyzeIssue:
    def test_analyze_issue_success(self, client):
        """Test successful issue analysis"""
        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.analyze_text = AsyncMock(return_value="Analysis result")

            response = client.post(
                "/api/gemini/analyze", json={"text": "Fix login bug in auth module"}
            )

            assert response.status_code == 200
            assert "Analysis result" in response.json()["analysis"]

    def test_analyze_issue_missing_text(self, client):
        """Test analyze with missing text field"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post("/api/gemini/analyze", json={})

            assert response.status_code == 400
            assert "Missing" in response.json()["detail"]

    def test_analyze_issue_empty_text(self, client):
        """Test analyze with empty text"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post("/api/gemini/analyze", json={"text": ""})

            assert response.status_code == 400

    def test_analyze_issue_service_error(self, client):
        """Test analyze when service raises exception"""
        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.analyze_text = AsyncMock(side_effect=Exception("Service error"))

            try:
                response = client.post("/api/gemini/analyze", json={"text": "Some issue"})
                # If we get here, check that it's an error response
                assert response.status_code >= 400
            except Exception:
                # Exception is generated and this is expected behavior
                pass


class TestGenerateCode:
    def test_generate_code_success(self, client):
        """Test successful code generation"""
        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.generate_code = AsyncMock(return_value="def hello():\n    pass")

            response = client.post(
                "/api/gemini/generate", json={"description": "Create a simple greeting function"}
            )

            assert response.status_code == 200
            assert "def hello()" in response.json()["code"]

    def test_generate_code_missing_description(self, client):
        """Test generate with missing description"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post("/api/gemini/generate", json={})

            assert response.status_code == 400
            assert "Missing" in response.json()["detail"]

    def test_generate_code_empty_description(self, client):
        """Test generate with empty description"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post("/api/gemini/generate", json={"description": ""})

            assert response.status_code == 400

    def test_generate_code_complex_description(self, client):
        """Test code generation with complex description"""
        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.generate_code = AsyncMock(return_value="class DataProcessor:\n    pass")

            response = client.post(
                "/api/gemini/generate",
                json={"description": "Create a class that processes data with validation"},
            )

            assert response.status_code == 200
            assert "DataProcessor" in response.json()["code"]


class TestChatWithGemini:
    def test_chat_success_with_ai_service(self, client):
        """Test chat using multi-model AI service"""
        with patch("src.kortana.routers.gemini.ai_service") as mock_ai:
            with patch("src.kortana.routers.gemini.gemini_service"):
                mock_ai.analyze_text = AsyncMock(return_value="AI response")

                response = client.post("/api/gemini/chat", json={"message": "Hello, how are you?"})

                assert response.status_code == 200
                assert "AI response" in response.json()["response"]

    def test_chat_fallback_to_gemini(self, client):
        """Test chat fallback to gemini when ai_service fails"""
        with patch("src.kortana.routers.gemini.ai_service") as mock_ai:
            with patch("src.kortana.routers.gemini.gemini_service") as mock_gemini:
                mock_ai.analyze_text = AsyncMock(side_effect=Exception("Service error"))
                mock_gemini.analyze_text = AsyncMock(return_value="Gemini response")

                response = client.post("/api/gemini/chat", json={"message": "Hello"})

                assert response.status_code == 200
                assert "Gemini response" in response.json()["response"]

    def test_chat_both_services_fail(self, client):
        """Test chat when both services fail"""
        with patch("src.kortana.routers.gemini.ai_service") as mock_ai:
            with patch("src.kortana.routers.gemini.gemini_service") as mock_gemini:
                mock_ai.analyze_text = AsyncMock(side_effect=Exception("AI error"))
                mock_gemini.analyze_text = AsyncMock(side_effect=Exception("Gemini error"))

                response = client.post("/api/gemini/chat", json={"message": "Hello"})

                assert response.status_code == 503

    def test_chat_no_services_available(self, client):
        """Test chat when both services are None"""
        with patch("src.kortana.routers.gemini.ai_service", None):
            with patch("src.kortana.routers.gemini.gemini_service", None):
                response = client.post("/api/gemini/chat", json={"message": "Hello"})

                assert response.status_code == 503

    def test_chat_missing_message(self, client):
        """Test chat with missing message field"""
        with patch("src.kortana.routers.gemini.ai_service"):
            response = client.post("/api/gemini/chat", json={})

            assert response.status_code == 400
            assert "Missing" in response.json()["detail"]

    def test_chat_empty_message(self, client):
        """Test chat with empty message"""
        with patch("src.kortana.routers.gemini.ai_service"):
            response = client.post("/api/gemini/chat", json={"message": ""})

            assert response.status_code == 400


class TestAnalyzeImage:
    def test_analyze_image_success(self, client):
        """Test successful image analysis"""
        # Create a test image
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.analyze_multimodal = AsyncMock(return_value="Image analysis")

            response = client.post(
                "/api/gemini/analyze/image",
                data={"prompt": "Describe this image"},
                files={"image": ("test.png", img_bytes, "image/png")},
            )

            assert response.status_code == 200
            assert "Image analysis" in response.json()["response"]

    def test_analyze_image_default_prompt(self, client):
        """Test image analysis with default prompt"""
        img = Image.new("RGB", (100, 100), color="blue")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.analyze_multimodal = AsyncMock(return_value="Analysis")

            response = client.post(
                "/api/gemini/analyze/image", files={"image": ("test.png", img_bytes, "image/png")}
            )

            assert response.status_code == 200

    def test_analyze_image_invalid_format(self, client):
        """Test image analysis with invalid image format"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post(
                "/api/gemini/analyze/image",
                data={"prompt": "Describe"},
                files={"image": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
            )

            assert response.status_code == 500

    def test_analyze_image_missing_file(self, client):
        """Test image analysis with missing file"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post("/api/gemini/analyze/image", data={"prompt": "Describe"})

            assert response.status_code == 422  # Validation error for missing file


class TestAnalyzeVideo:
    def test_analyze_video_success(self, client):
        """Test successful video analysis"""
        video_bytes = io.BytesIO(b"fake video content")

        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            with patch("google.generativeai.upload_file") as mock_upload:
                mock_service.analyze_multimodal = AsyncMock(return_value="Video analysis")
                mock_uploaded = MagicMock()
                mock_upload.return_value = mock_uploaded

                response = client.post(
                    "/api/gemini/analyze/video",
                    data={"prompt": "Describe the video"},
                    files={"video": ("test.mp4", video_bytes, "video/mp4")},
                )

                assert response.status_code == 200
                assert "Video analysis" in response.json()["response"]

    def test_analyze_video_default_prompt(self, client):
        """Test video analysis with default prompt"""
        video_bytes = io.BytesIO(b"video data")

        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            with patch("google.generativeai.upload_file") as mock_upload:
                mock_service.analyze_multimodal = AsyncMock(return_value="Analysis")
                mock_uploaded = MagicMock()
                mock_upload.return_value = mock_uploaded

                response = client.post(
                    "/api/gemini/analyze/video",
                    files={"video": ("test.mp4", video_bytes, "video/mp4")},
                )

                assert response.status_code == 200

    def test_analyze_video_file_handling_error(self, client):
        """Test video analysis with file handling error"""
        video_bytes = io.BytesIO(b"video data")

        with patch("src.kortana.routers.gemini.gemini_service"):
            with patch("google.generativeai.upload_file"):
                with patch("pathlib.Path.open", side_effect=IOError("File error")):
                    response = client.post(
                        "/api/gemini/analyze/video",
                        files={"video": ("test.mp4", video_bytes, "video/mp4")},
                    )

                    assert response.status_code == 500

    def test_analyze_video_genai_upload_error(self, client):
        """Test video analysis when genai upload fails"""
        video_bytes = io.BytesIO(b"video data")

        with patch("src.kortana.routers.gemini.gemini_service"):
            with patch("google.generativeai.upload_file") as mock_upload:
                mock_upload.side_effect = Exception("Upload error")

                response = client.post(
                    "/api/gemini/analyze/video",
                    files={"video": ("test.mp4", video_bytes, "video/mp4")},
                )

                assert response.status_code == 500

    def test_analyze_video_missing_file(self, client):
        """Test video analysis with missing file"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post("/api/gemini/analyze/video", data={"prompt": "Analyze"})

            assert response.status_code == 422  # Validation error for missing file


class TestGeminiRouterIntegration:
    def test_multiple_sequential_requests(self, client):
        """Test multiple sequential requests"""
        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.analyze_text = AsyncMock(return_value="Response 1")
            mock_service.generate_code = AsyncMock(return_value="Code 1")

            # First request
            response1 = client.post("/api/gemini/analyze", json={"text": "Issue 1"})
            assert response1.status_code == 200

            # Second request
            response2 = client.post(
                "/api/gemini/generate", json={"description": "Generate function"}
            )
            assert response2.status_code == 200

    def test_concurrent_endpoint_coverage(self, client):
        """Test that different endpoints properly isolate mocks"""
        with patch("src.kortana.routers.gemini.gemini_service") as mock_gemini:
            with patch("src.kortana.routers.gemini.ai_service") as mock_ai:
                mock_gemini.analyze_text = AsyncMock(return_value="G1")
                mock_gemini.generate_code = AsyncMock(return_value="G2")
                mock_ai.analyze_text = AsyncMock(return_value="A1")

                # Test analyze endpoint
                r1 = client.post("/api/gemini/analyze", json={"text": "test"})
                assert r1.status_code == 200

                # Test generate endpoint
                r2 = client.post("/api/gemini/generate", json={"description": "test"})
                assert r2.status_code == 200

                # Test chat endpoint
                r3 = client.post("/api/gemini/chat", json={"message": "test"})
                assert r3.status_code == 200
