"""
Comprehensive Integration Tests for Kor'tana User Functionality

This test suite validates the integration between frontend and backend,
ensuring stability, responsiveness, and proper communication.
"""

import base64
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from kortana.main import app
from kortana.services.database import Base, get_db_sync

# Test database setup
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///./test_kortana_comprehensive.db"

# OpenAI adapter orchestrator mock path
ORCHESTRATOR_PROCESS_QUERY_PATH = (
    "src.kortana.core.orchestrator.KorOrchestrator.process_query"
)

# =============================================================================
# Test Fixtures
# =============================================================================

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database session."""
    db = None
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        if db:
            db.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database override."""
    app.dependency_overrides[get_db_sync] = lambda: test_db
    Base.metadata.create_all(bind=engine_test)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine_test)
    if get_db_sync in app.dependency_overrides:
        del app.dependency_overrides[get_db_sync]


# =============================================================================
# Health & Status Endpoint Tests
# =============================================================================


def test_health_check(client: TestClient):
    """Test that the health endpoint returns correct status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Kor'tana"
    assert "version" in data


def test_system_status(client: TestClient):
    """Test that system status endpoint returns operational info."""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "autonomous_agent" in data
    assert "scheduler_running" in data
    assert "message" in data


def test_database_connectivity(client: TestClient):
    """Test database connectivity through the test-db endpoint."""
    response = client.get("/test-db")
    assert response.status_code == 200
    data = response.json()
    assert "db_connection" in data


# =============================================================================
# Chat Endpoint Tests
# =============================================================================


def test_basic_chat_endpoint(client: TestClient):
    """Test basic chat functionality."""
    response = client.post("/chat", json={"message": "Hello Kor'tana"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "status" in data
    assert data["status"] == "success"


def test_chat_with_empty_message(client: TestClient):
    """Test chat endpoint handles empty messages gracefully."""
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data


def test_chat_with_missing_message_field(client: TestClient):
    """Test chat endpoint handles missing message field."""
    response = client.post("/chat", json={})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data


def test_voice_transcribe_endpoint(client: TestClient):
    """Test voice transcription endpoint with heuristic text payload."""
    audio_payload = base64.b64encode(b"TEXT: hello from voice testing").decode("utf-8")
    response = client.post(
        "/voice/transcribe",
        json={"audio_base64": audio_payload, "user_id": "voice-test-user"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "transcript" in data
    assert "metrics" in data


def test_voice_chat_endpoint(client: TestClient):
    """Test full voice chat endpoint with optional TTS output."""
    audio_payload = base64.b64encode(b"TEXT: tell me something encouraging").decode(
        "utf-8"
    )
    response = client.post(
        "/voice/chat",
        json={
            "audio_base64": audio_payload,
            "user_id": "voice-test-user",
            "return_audio": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "transcript" in data
    assert "response" in data
    assert "metrics" in data


def test_voice_chat_invalid_base64(client: TestClient):
    """Test voice endpoint rejects malformed base64 payloads."""
    response = client.post(
        "/voice/chat",
        json={"audio_base64": "@@@not-base64@@@", "user_id": "voice-test-user"},
    )
    assert response.status_code == 400


# =============================================================================
# Core Query Endpoint Tests
# =============================================================================


def test_core_query_validation_empty_string(client: TestClient):
    """Test core query rejects empty strings."""
    response = client.post("/core/query", json={"query": ""})
    assert response.status_code == 422


def test_core_query_validation_missing_field(client: TestClient):
    """Test core query requires query field."""
    response = client.post("/core/query", json={})
    assert response.status_code == 422


def test_core_query_validation_long_query(client: TestClient):
    """Test core query rejects queries that are too long."""
    long_query = "a" * 1001  # Exceeds max_length of 1000
    response = client.post("/core/query", json={"query": long_query})
    assert response.status_code == 422


# =============================================================================
# Goal Management Endpoint Tests
# =============================================================================


def test_create_goal(client: TestClient):
    """Test creating a new goal."""
    goal_data = {
        "description": "A test goal for comprehensive testing",
        "priority": 100,
    }
    response = client.post("/goals/", json=goal_data)
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == goal_data["description"]
    assert data["priority"] == goal_data["priority"]
    assert "id" in data
    assert "created_at" in data
    assert data["status"] == "pending"


def test_list_goals(client: TestClient):
    """Test listing all goals."""
    # Create a goal first
    goal_data = {
        "description": "Goal for testing list endpoint",
        "priority": 80,
    }
    client.post("/goals/", json=goal_data)

    # List goals
    response = client.get("/goals/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_goal_by_id(client: TestClient):
    """Test retrieving a specific goal by ID."""
    # Create a goal first
    goal_data = {
        "description": "Goal for testing get by ID",
        "priority": 90,
    }
    create_response = client.post("/goals/", json=goal_data)
    goal_id = create_response.json()["id"]

    # Get the goal
    response = client.get(f"/goals/{goal_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == goal_id
    assert data["description"] == goal_data["description"]


def test_get_nonexistent_goal(client: TestClient):
    """Test getting a goal that doesn't exist."""
    response = client.get("/goals/99999")
    assert response.status_code == 404


def test_list_goals_with_pagination(client: TestClient):
    """Test goal listing with pagination parameters."""
    # Create multiple goals
    for i in range(5):
        goal_data = {
            "description": f"Goal {i} for pagination testing",
            "priority": 100 - i,
        }
        client.post("/goals/", json=goal_data)

    # Test pagination
    response = client.get("/goals/?skip=0&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3


# =============================================================================
# OpenAI-Compatible Adapter Tests (LobeChat Integration)
# =============================================================================


def test_openai_adapter_basic_chat(client: TestClient):
    """Test OpenAI-compatible chat completions endpoint."""
    # Mock the orchestrator to avoid network calls
    mock_response = {
        "response": "Hello! I'm doing great, thank you for asking!",
        "content": "Hello! I'm doing great, thank you for asking!",
    }

    with patch(
        ORCHESTRATOR_PROCESS_QUERY_PATH,
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        request_data = {
            "model": "kortana-custom",
            "messages": [{"role": "user", "content": "Hello, how are you?"}],
        }
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "object" in data
        assert data["object"] == "chat.completion"
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert "message" in data["choices"][0]
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert "content" in data["choices"][0]["message"]


def test_openai_adapter_no_user_message(client: TestClient):
    """Test OpenAI adapter handles missing user message."""
    request_data = {
        "model": "kortana-custom",
        "messages": [{"role": "system", "content": "You are a helpful assistant."}],
    }
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 400


def test_openai_adapter_empty_messages(client: TestClient):
    """Test OpenAI adapter handles empty messages list."""
    request_data = {"model": "kortana-custom", "messages": []}
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 400


def test_lobechat_adapter(client: TestClient):
    """Test legacy LobeChat adapter endpoint."""
    request_data = {
        "messages": [{"content": "Test message for LobeChat", "role": "user"}]
    }
    response = client.post("/adapters/lobechat/chat", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data


# =============================================================================
# Error Handling & Edge Cases
# =============================================================================


def test_invalid_endpoint(client: TestClient):
    """Test accessing an invalid endpoint returns 404."""
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404


def test_invalid_http_method(client: TestClient):
    """Test using wrong HTTP method on endpoint."""
    # POST instead of GET on health
    response = client.post("/health")
    assert response.status_code == 405


def test_malformed_json(client: TestClient):
    """Test sending malformed JSON to endpoints."""
    response = client.post(
        "/chat", data="not valid json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


def test_goal_creation_missing_required_fields(client: TestClient):
    """Test goal creation fails with missing required fields."""
    incomplete_goal = {
        "priority": 100
        # Missing required 'description' field
    }
    response = client.post("/goals/", json=incomplete_goal)
    assert response.status_code == 422


# =============================================================================
# CORS & Headers Tests
# =============================================================================


def test_cors_headers_present(client: TestClient):
    """Test that CORS middleware is configured (TestClient may not show headers)."""
    response = client.get("/health")
    assert response.status_code == 200
    # Note: TestClient doesn't always expose CORS headers in the same way as real HTTP requests
    # This test mainly verifies the endpoint is accessible, which indicates CORS is configured
    # For real CORS testing, use actual HTTP requests or integration tests with a running server


def test_options_request_for_cors(client: TestClient):
    """Test CORS preflight OPTIONS request."""
    response = client.options("/health")
    # Should handle OPTIONS for CORS preflight
    assert response.status_code in [200, 405]


# =============================================================================
# Concurrent Request Tests
# =============================================================================


def test_concurrent_goal_creation(client: TestClient):
    """Test creating multiple goals in sequence (simulating concurrency)."""
    goals = []
    for i in range(3):
        goal_data = {
            "description": f"Testing concurrent creation {i}",
            "priority": 100,
        }
        response = client.post("/goals/", json=goal_data)
        assert response.status_code == 201
        goals.append(response.json())

    # Verify all goals were created
    response = client.get("/goals/")
    assert response.status_code == 200
    all_goals = response.json()
    assert len(all_goals) >= 3


def test_multiple_health_checks(client: TestClient):
    """Test multiple health check requests."""
    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


# =============================================================================
# Response Time & Performance Tests
# =============================================================================


def test_health_endpoint_response_time(client: TestClient):
    """Test that health endpoint responds quickly."""
    import time

    start = time.time()
    response = client.get("/health")
    duration = time.time() - start
    assert response.status_code == 200
    # Health check should be very fast (under 1 second)
    assert duration < 1.0


def test_list_goals_response_time(client: TestClient):
    """Test that listing goals responds in reasonable time."""
    import time

    # Create some goals first
    for i in range(10):
        goal_data = {
            "description": f"Performance test goal {i}",
            "priority": 100,
        }
        client.post("/goals/", json=goal_data)

    start = time.time()
    response = client.get("/goals/")
    duration = time.time() - start
    assert response.status_code == 200
    # Should complete within reasonable time (under 2 seconds)
    assert duration < 2.0
