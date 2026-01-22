"""
Integration tests for CopilotKit adapter.
"""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.kortana.main import app
from src.kortana.modules.memory_core import models as memory_models
from src.kortana.services.database import Base, get_db_sync

# Use a separate in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///./test_kortana_copilotkit.db"
engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function")
def override_get_db_sync_test():
    """Provide a test database session."""
    db = None
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        if db:
            db.close()


@pytest.fixture(scope="function")
def client(override_get_db_sync_test):
    """Create a test client with test database."""
    app.dependency_overrides[get_db_sync] = lambda: override_get_db_sync_test
    Base.metadata.create_all(bind=engine_test)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine_test)
    # Ensure the override is removed after the test
    if get_db_sync in app.dependency_overrides:
        del app.dependency_overrides[get_db_sync]


@pytest.mark.asyncio
@patch(
    "src.kortana.core.orchestrator.KorOrchestrator.process_query",
    new_callable=AsyncMock,
)
async def test_copilotkit_endpoint_success(mock_process_query, client: TestClient):
    """Test the /copilotkit endpoint with a successful mocked orchestrator response."""
    # Arrange: Set up the mock to return a simulated response
    mock_process_query.return_value = {
        "final_response": "Hello! I'm Kor'tana, how can I help you?",
        "model_used": "gpt-4",
        "memory_context": [],
        "ethical_evaluation": {},
    }

    # Act: Make a request to the CopilotKit endpoint
    request_payload = {
        "messages": [
            {"role": "user", "content": "Hello, Kor'tana!"},
        ],
    }
    response = client.post("/copilotkit", json=request_payload)

    # Assert: Check the response
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["role"] == "assistant"
    assert data["content"] == "Hello! I'm Kor'tana, how can I help you?"
    assert "metadata" in data
    assert data["metadata"]["model_used"] == "gpt-4"


@pytest.mark.asyncio
@patch(
    "src.kortana.core.orchestrator.KorOrchestrator.process_query",
    new_callable=AsyncMock,
)
async def test_copilotkit_endpoint_with_multiple_messages(
    mock_process_query, client: TestClient
):
    """Test the /copilotkit endpoint with multiple messages in the conversation."""
    # Arrange
    mock_process_query.return_value = {
        "final_response": "The weather is sunny today.",
        "model_used": "gpt-4",
        "memory_context": [],
        "ethical_evaluation": {},
    }

    # Act
    request_payload = {
        "messages": [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "What's the weather?"},
        ],
    }
    response = client.post("/copilotkit", json=request_payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "The weather is sunny today."
    # Verify that the orchestrator was called with the last user message
    mock_process_query.assert_called_once()


@pytest.mark.asyncio
async def test_copilotkit_endpoint_no_user_message(client: TestClient):
    """Test the /copilotkit endpoint with no user messages."""
    # Act
    request_payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
        ],
    }
    response = client.post("/copilotkit", json=request_payload)

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "No user message found" in data["detail"]


@pytest.mark.asyncio
@patch(
    "src.kortana.core.orchestrator.KorOrchestrator.process_query",
    new_callable=AsyncMock,
)
async def test_copilotkit_endpoint_error_handling(
    mock_process_query, client: TestClient
):
    """Test the /copilotkit endpoint handles orchestrator errors gracefully."""
    # Arrange: Make the orchestrator raise an exception
    mock_process_query.side_effect = Exception("Internal processing error")

    # Act
    request_payload = {
        "messages": [
            {"role": "user", "content": "Hello!"},
        ],
    }
    response = client.post("/copilotkit", json=request_payload)

    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "error processing your message" in data["detail"].lower()


def test_copilotkit_health_endpoint(client: TestClient):
    """Test the /copilotkit/health endpoint."""
    # Act
    response = client.get("/copilotkit/health")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Kor'tana CopilotKit Adapter"
    assert "version" in data
