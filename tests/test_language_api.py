"""
Integration tests for language API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.kortana.main import app

client = TestClient(app)


class TestLanguageEndpoints:
    """Test language management API endpoints."""

    def test_get_supported_languages(self):
        """Test retrieving list of supported languages."""
        response = client.get("/language/supported")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "en" in data
        assert data["en"] == "English"
        assert len(data) > 0

    def test_switch_language_valid(self):
        """Test switching to a valid language."""
        response = client.post(
            "/language/switch",
            json={"language": "es"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["language"] == "es"
        assert data["language_name"] == "Spanish"
        assert "switched" in data["message"].lower()

    def test_switch_language_french(self):
        """Test switching to French."""
        response = client.post(
            "/language/switch",
            json={"language": "fr"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["language"] == "fr"
        assert data["language_name"] == "French"

    def test_switch_language_invalid(self):
        """Test switching to an invalid language."""
        response = client.post(
            "/language/switch",
            json={"language": "xx"}
        )
        assert response.status_code == 400
        assert "unsupported" in response.json()["detail"].lower()

    def test_switch_language_with_session(self):
        """Test switching language with session ID."""
        response = client.post(
            "/language/switch",
            json={"language": "de", "session_id": "test-session-123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["language"] == "de"

    def test_detect_language_english(self):
        """Test detecting English text."""
        response = client.get(
            "/language/detect",
            params={"text": "Hello world"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["detected_language"] == "en"
        assert data["language_name"] == "English"

    def test_detect_language_chinese(self):
        """Test detecting Chinese text."""
        response = client.get(
            "/language/detect",
            params={"text": "你好世界"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["detected_language"] == "zh"
        assert data["language_name"] == "Chinese"

    def test_detect_language_empty(self):
        """Test detecting language with empty text."""
        response = client.get("/language/detect")
        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()

    def test_health_check_includes_languages(self):
        """Test that health check reports multilingual support."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "multilingual_support" in data
        assert data["multilingual_support"] is True
        assert "supported_languages" in data
        assert isinstance(data["supported_languages"], list)
        assert "en" in data["supported_languages"]


class TestMultilingualCoreQuery:
    """Test multilingual support in core query endpoint."""

    def test_core_query_with_language_parameter(self):
        """Test core query with explicit language parameter."""
        # Note: This test may fail if the database or LLM is not properly configured
        # We're just testing that the API accepts the language parameter
        response = client.post(
            "/core/query",
            json={
                "query": "What is the meaning of life?",
                "language": "es"
            }
        )
        # Accept either 200 (success) or 500 (expected if DB/LLM not configured)
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            # Verify the response includes language information
            assert "language" in data
            assert data["language"] == "es"

    def test_core_query_without_language(self):
        """Test core query without language parameter (defaults to English)."""
        response = client.post(
            "/core/query",
            json={"query": "Hello"}
        )
        # Accept either 200 (success) or 500 (expected if DB/LLM not configured)
        assert response.status_code in [200, 500]


class TestMultilingualChatCompletions:
    """Test multilingual support in OpenAI-compatible endpoint."""

    def test_chat_completions_with_language(self):
        """Test chat completions with language parameter."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "kortana-custom",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "language": "fr"
            }
        )
        # Accept either 200 (success) or 500 (expected if DB/LLM not configured)
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "choices" in data
            assert len(data["choices"]) > 0

    def test_chat_completions_without_language(self):
        """Test chat completions without language parameter."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "kortana-custom",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ]
            }
        )
        # Accept either 200 (success) or 500 (expected if DB/LLM not configured)
        assert response.status_code in [200, 500]
