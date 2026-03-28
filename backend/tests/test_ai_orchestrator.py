"""
Tests for Unified AI Orchestrator Router
"""

from unittest.mock import patch

import pytest

from src.kortana.main import create_app


@pytest.fixture
def client():
    app = create_app()
    from .conftest import SyncTestClient
    return SyncTestClient(app)


def test_orchestrator_status(client):
    """Test the status endpoint of the orchestrator."""
    response = client.get("/api/orchestrator/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "logic_available" in data
    assert "prompts_available" in data


def test_handshake_standard(client):
    """Test standard handshake response."""
    response = client.post("/api/orchestrator/handshake", json={"message": "Hello"})
    assert response.status_code == 200
    assert response.json()["status"] == "standard"


def test_handshake_elevated(client):
    """Test elevated handshake response with 'we are'."""
    response = client.post(
        "/api/orchestrator/handshake", json={"message": "we are ready"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ELEVATED"
    assert "Activation Protocol" in response.json()["message"]


@patch("src.kortana.routers.orchestrator.gemini_service")
def test_execute_unified_logic(mock_service, client):
    """Test execution of unified logic with mocked Gemini service."""

    async def mock_analyze(*args, **kwargs):
        return "Mocked AI Response"

    mock_service.analyze_text.side_effect = mock_analyze

    response = client.post("/api/orchestrator/execute", json={"task": "Say hello"})

    assert response.status_code == 200
    assert response.json()["response"] == "Mocked AI Response"
    assert response.json()["source"] == "local_gemini_service"
