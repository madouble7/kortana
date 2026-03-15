"""
Unit tests for the AutoGen adapter.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.kortana.adapters.autogen_adapter import AutoGenAdapter
from src.kortana.main import app


@pytest.fixture
def autogen_adapter():
    """Create an AutoGen adapter instance for testing."""
    return AutoGenAdapter()


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MagicMock()


@patch("src.kortana.adapters.autogen_adapter.KorOrchestrator")
def test_handle_autogen_request_success(mock_orchestrator, autogen_adapter, mock_db_session):
    """Test successful handling of an AutoGen request."""
    # Configure mock
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator.return_value = mock_orchestrator_instance
    mock_orchestrator_instance.process_query.return_value = {
        "final_kortana_response": "This is a test response from Kor'tana."
    }

    # Test request
    request_data = {
        "messages": [{"role": "user", "content": "Hello, AutoGen!"}],
        "conversation_id": "test-conv-1",
    }

    # Call the adapter
    import asyncio
    response = asyncio.run(
        autogen_adapter.handle_autogen_request(request_data, mock_db_session)
    )

    # Verify response
    assert response["status"] == "success"
    assert response["conversation_id"] == "test-conv-1"
    assert len(response["agent_responses"]) == 1
    assert response["agent_responses"][0]["agent"] == "kortana_assistant"
    assert "This is a test response" in response["agent_responses"][0]["content"]


@patch("src.kortana.adapters.autogen_adapter.KorOrchestrator")
def test_handle_autogen_request_missing_messages(mock_orchestrator, autogen_adapter, mock_db_session):
    """Test handling of request with missing messages."""
    # Test request with empty messages
    request_data = {
        "messages": [],
        "conversation_id": "test-conv-1",
    }

    # Call the adapter and expect an error
    with pytest.raises(HTTPException) as excinfo:
        import asyncio
        asyncio.run(
            autogen_adapter.handle_autogen_request(request_data, mock_db_session)
        )
    
    assert excinfo.value.status_code == 400
    assert "No user message found" in excinfo.value.detail


@patch("src.kortana.adapters.autogen_adapter.KorOrchestrator")
def test_handle_autogen_request_orchestrator_error(mock_orchestrator, autogen_adapter, mock_db_session):
    """Test handling of orchestrator error."""
    # Configure mock to raise an error
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator.return_value = mock_orchestrator_instance
    mock_orchestrator_instance.process_query.side_effect = Exception("Orchestrator error")

    # Test request
    request_data = {
        "messages": [{"role": "user", "content": "Hello!"}],
        "conversation_id": "test-conv-1",
    }

    # Call the adapter
    import asyncio
    response = asyncio.run(
        autogen_adapter.handle_autogen_request(request_data, mock_db_session)
    )

    # Verify error response
    assert response["status"] == "error"
    assert response["agent_responses"][0]["content"] == "I encountered an internal processing error. Please try again."


@patch("src.kortana.adapters.autogen_adapter.KorOrchestrator")
def test_handle_multi_agent_collaboration_success(mock_orchestrator, autogen_adapter, mock_db_session):
    """Test successful multi-agent collaboration."""
    # Configure mock
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator.return_value = mock_orchestrator_instance
    mock_orchestrator_instance.process_query.return_value = {
        "final_kortana_response": "Task completed successfully."
    }

    # Test request
    request_data = {
        "task": "Analyze this code and suggest improvements",
    }

    # Call the adapter
    import asyncio
    response = asyncio.run(
        autogen_adapter.handle_multi_agent_collaboration(request_data, mock_db_session)
    )

    # Verify response
    assert response["status"] == "completed"
    assert response["task"] == request_data["task"]
    assert "kortana_orchestrator" in response["agents_involved"]
    assert len(response["agent_contributions"]) == 1
    assert response["agent_contributions"][0]["agent"] == "kortana_orchestrator"
    assert "multi_agent_simulation" in response["debug_info"]


@patch("src.kortana.adapters.autogen_adapter.KorOrchestrator")
def test_handle_multi_agent_collaboration_missing_task(mock_orchestrator, autogen_adapter, mock_db_session):
    """Test handling of collaboration request with missing task."""
    # Test request with missing task
    request_data = {}

    # Call the adapter and expect an error
    with pytest.raises(HTTPException) as excinfo:
        import asyncio
        asyncio.run(
            autogen_adapter.handle_multi_agent_collaboration(request_data, mock_db_session)
        )
    
    assert excinfo.value.status_code == 400
    assert "Missing 'task'" in excinfo.value.detail


def test_get_agent_status(autogen_adapter):
    """Test getting agent status."""
    status = autogen_adapter.get_agent_status()
    
    assert status["framework"] == "Microsoft AutoGen"
    assert status["status"] == "operational"
    assert "available_agents" in status
    assert len(status["available_agents"]) > 0
    assert "agent_details" in status


@patch("src.kortana.adapters.autogen_router.autogen_adapter")
def test_chat_endpoint(mock_adapter):
    """Test the /adapters/autogen/chat endpoint."""
    # Configure mock
    mock_adapter.handle_autogen_request.return_value = {
        "agent_responses": [
            {
                "agent": "kortana_assistant",
                "role": "assistant",
                "content": "Test response",
                "metadata": {"agent_type": "kortana_orchestrator"},
            }
        ],
        "conversation_id": "test-conv-1",
        "status": "success",
        "debug_info": {},
    }

    # Create test client
    client = TestClient(app)

    # Test request
    response = client.post(
        "/adapters/autogen/chat",
        json={
            "messages": [{"role": "user", "content": "Hello!"}],
            "conversation_id": "test-conv-1",
        },
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["conversation_id"] == "test-conv-1"


@patch("src.kortana.adapters.autogen_router.autogen_adapter")
def test_collaborate_endpoint(mock_adapter):
    """Test the /adapters/autogen/collaborate endpoint."""
    # Configure mock
    mock_adapter.handle_multi_agent_collaboration.return_value = {
        "collaboration_result": "Task completed",
        "agents_involved": ["kortana_orchestrator"],
        "task": "Test task",
        "status": "completed",
        "agent_contributions": [
            {"agent": "kortana_orchestrator", "contribution": "Processed task"}
        ],
        "debug_info": {},
    }

    # Create test client
    client = TestClient(app)

    # Test request
    response = client.post(
        "/adapters/autogen/collaborate",
        json={"task": "Test task"},
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["task"] == "Test task"


def test_status_endpoint():
    """Test the /adapters/autogen/status endpoint."""
    # Create test client
    client = TestClient(app)

    # Test request
    response = client.get("/adapters/autogen/status")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "Microsoft AutoGen"
    assert data["status"] == "operational"
    assert "available_agents" in data


def test_health_endpoint():
    """Test the /adapters/autogen/health endpoint."""
    # Create test client
    client = TestClient(app)

    # Test request
    response = client.get("/adapters/autogen/health")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["adapter"] == "AutoGen"
