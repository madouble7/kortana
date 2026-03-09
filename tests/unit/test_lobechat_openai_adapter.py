"""
Unit tests for the OpenAI-compatible LobeChat adapter.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

# Set test environment variables BEFORE importing the adapter
os.environ["KORTANA_API_KEY"] = "test-api-key-12345"
os.environ["ENV"] = "development"

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.kortana.adapters.lobechat_openai_adapter import (
    ChatCompletionRequest,
    Message,
    verify_api_key,
)
from src.kortana.main import app

client = TestClient(app)


class TestVerifyApiKey:
    """Tests for API key verification."""

    def test_verify_api_key_valid(self):
        """Test that verify_api_key accepts a valid API key."""
        result = verify_api_key(authorization="Bearer test-api-key-12345")
        assert result is True

    def test_verify_api_key_missing_in_dev(self):
        """Test that verify_api_key allows access in dev mode when key is missing."""
        with patch.dict(os.environ, {"ENV": "development"}, clear=False):
            with patch.dict(os.environ, {"KORTANA_API_KEY": ""}, clear=False):
                # Remove the key
                if "KORTANA_API_KEY" in os.environ:
                    del os.environ["KORTANA_API_KEY"]
                
                result = verify_api_key(authorization=None)
                assert result is True

    def test_verify_api_key_missing_in_production(self):
        """Test that verify_api_key fails in production when key is missing."""
        with patch.dict(os.environ, {"ENV": "production"}, clear=False):
            with patch.dict(os.environ, {}, clear=True):
                # Remove the key
                if "KORTANA_API_KEY" in os.environ:
                    del os.environ["KORTANA_API_KEY"]
                
                with pytest.raises(HTTPException) as excinfo:
                    verify_api_key(authorization=None)
                assert excinfo.value.status_code == 500
                assert "misconfiguration" in excinfo.value.detail.lower()

    def test_verify_api_key_invalid(self):
        """Test that verify_api_key rejects an incorrect API key."""
        with pytest.raises(HTTPException) as excinfo:
            verify_api_key(authorization="Bearer wrong-api-key")
        assert excinfo.value.status_code == 401
        assert "Invalid or missing" in excinfo.value.detail

    def test_verify_api_key_invalid_format(self):
        """Test that verify_api_key rejects an invalidly formatted API key."""
        with pytest.raises(HTTPException) as excinfo:
            verify_api_key(authorization="test-api-key-12345")  # Missing "Bearer"
        assert excinfo.value.status_code == 401


class TestModelsEndpoint:
    """Tests for /v1/models endpoint."""

    def test_list_models_success(self):
        """Test that /v1/models returns the list of models."""
        response = client.get(
            "/v1/models",
            headers={"Authorization": "Bearer test-api-key-12345"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 3
        model_ids = [model["id"] for model in data["data"]]
        assert "kortana-default" in model_ids
        assert "gpt-4o-mini-openai" in model_ids
        assert "gemini-2.0-flash-lite" in model_ids

    def test_list_models_unauthorized(self):
        """Test that /v1/models requires authentication."""
        response = client.get("/v1/models")
        assert response.status_code == 401


class TestChatCompletionsEndpoint:
    """Tests for /v1/chat/completions endpoint."""

    @patch("src.kortana.adapters.lobechat_openai_adapter.KorOrchestrator")
    @patch("src.kortana.adapters.lobechat_openai_adapter.get_db_sync")
    def test_chat_completion_success(self, mock_get_db, mock_orchestrator):
        """Test successful chat completion."""
        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock orchestrator
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_orchestrator_instance.process_query = AsyncMock(
            return_value={"final_response": "Test response from Kor'tana"}
        )
        
        response = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer test-api-key-12345"},
            json={
                "model": "kortana-default",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "chat.completion"
        assert data["model"] == "kortana-default"
        assert len(data["choices"]) == 1
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert data["choices"][0]["message"]["content"] == "Test response from Kor'tana"

    def test_chat_completion_unauthorized(self):
        """Test that chat completions require authentication."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "kortana-default",
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )
        assert response.status_code == 401

    def test_chat_completion_unsupported_model(self):
        """Test that unsupported models are rejected."""
        response = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer test-api-key-12345"},
            json={
                "model": "unsupported-model",
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]

    def test_chat_completion_streaming_rejected(self):
        """Test that streaming requests are rejected."""
        response = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer test-api-key-12345"},
            json={
                "model": "kortana-default",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True
            }
        )
        assert response.status_code == 400
        assert "streaming" in response.json()["detail"].lower()

    def test_chat_completion_no_messages(self):
        """Test that empty messages are rejected."""
        response = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer test-api-key-12345"},
            json={
                "model": "kortana-default",
                "messages": []
            }
        )
        assert response.status_code == 400
        assert "No messages" in response.json()["detail"]

    def test_chat_completion_no_user_messages(self):
        """Test that requests without user messages are rejected."""
        response = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer test-api-key-12345"},
            json={
                "model": "kortana-default",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant"}
                ]
            }
        )
        assert response.status_code == 400
        assert "No user messages" in response.json()["detail"]


class TestHealthEndpoint:
    """Tests for /v1/health endpoint."""

    def test_health_check(self):
        """Test that /v1/health returns OK."""
        response = client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
