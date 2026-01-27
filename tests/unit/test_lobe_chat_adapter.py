"""
Unit tests for the LobeChat adapter.
"""

import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Set test API key environment variable
os.environ["KORTANA_API_KEY"] = "test-api-key"

from kortana.adapters.lobe_chat_adapter import verify_api_key
from kortana.main import app


def test_verify_api_key_valid():
    """Test that verify_api_key accepts a valid API key."""
    # Valid API key
    result = verify_api_key(authorization="Bearer test-api-key")
    assert result is True


def test_verify_api_key_missing():
    """Test that verify_api_key rejects a missing API key."""
    # Missing API key
    with pytest.raises(HTTPException) as excinfo:
        verify_api_key(authorization=None)
    assert excinfo.value.status_code == 401
    assert "Missing API key" in excinfo.value.detail


def test_verify_api_key_invalid_format():
    """Test that verify_api_key rejects an invalidly formatted API key."""
    # Invalid format
    with pytest.raises(HTTPException) as excinfo:
        verify_api_key(authorization="test-api-key")
    assert excinfo.value.status_code == 401
    assert "Invalid API key format" in excinfo.value.detail


def test_verify_api_key_wrong_key():
    """Test that verify_api_key rejects an incorrect API key."""
    # Wrong API key
    with pytest.raises(HTTPException) as excinfo:
        verify_api_key(authorization="Bearer wrong-api-key")
    assert excinfo.value.status_code == 401
    assert "Invalid API key" in excinfo.value.detail


@patch("src.kortana.adapters.lobe_chat_adapter.KorOrchestrator")
def test_process_lobe_chat(mock_orchestrator):
    """Test the process_lobe_chat endpoint."""
    # Configure mock
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator.return_value = mock_orchestrator_instance
    mock_orchestrator_instance.process_query.return_value = {
        "final_response": "This is a test response from Kor'tana."
    }

    # Create test client with authentication
    client = TestClient(app)

    # Test request
    test_conversation_id = str(uuid.uuid4())
    response = client.post(
        "/api/lobe/chat",
        json={"content": "Hello, Kor'tana!", "conversation_id": test_conversation_id},
        headers={"Authorization": "Bearer test-api-key"},
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "This is a test response from Kor'tana."
    assert data["conversation_id"] == test_conversation_id
    assert "id" in data
    assert "created_at" in data

    # Verify orchestrator was called correctly
    mock_orchestrator_instance.process_query.assert_called_once_with(
        query="Hello, Kor'tana!"
    )


@patch("src.kortana.adapters.lobe_chat_adapter.KorOrchestrator")
def test_process_lobe_chat_error(mock_orchestrator):
    """Test error handling in the process_lobe_chat endpoint."""
    # Configure mock to raise an exception
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator.return_value = mock_orchestrator_instance
    mock_orchestrator_instance.process_query.side_effect = Exception("Test error")

    # Create test client with authentication
    client = TestClient(app)

    # Test request
    response = client.post(
        "/api/lobe/chat",
        json={
            "content": "This will cause an error",
            "conversation_id": "test-conversation",
        },
        headers={"Authorization": "Bearer test-api-key"},
    )
    # Verify response
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"].lower()
