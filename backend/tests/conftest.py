"""
Pytest configuration and fixtures for Kor'tana Backend tests
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kortana.auth import create_access_token
from src.kortana.config import Settings
from src.kortana.database import get_db
from src.kortana.main import app
from src.kortana.schemas import Agent, Task, User


@pytest.fixture
def app_fixture(db):
    """Provide the FastAPI app with mocked database"""
    app.dependency_overrides[get_db] = lambda: db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """Provide test settings"""
    settings = Settings()
    settings.ENVIRONMENT = "testing"
    settings.DEBUG = True
    return settings


@pytest.fixture
def client(app_fixture):
    """Provide FastAPI test client"""
    return TestClient(app_fixture)


@pytest.fixture
def test_user():
    """Provide a test user"""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        created_at="2026-01-14T00:00:00",
    )


@pytest.fixture
def test_token(test_user):
    """Provide a valid test JWT token"""
    return create_access_token(
        data={"sub": test_user.username, "scopes": ["read", "write"]}
    )


@pytest.fixture
def authenticated_client(client, test_token):
    """Provide authenticated test client"""
    client.headers = {"Authorization": f"Bearer {test_token}"}
    return client


@pytest.fixture
def test_agent():
    """Provide a test agent"""
    return Agent(
        id=1,
        name="Test Agent",
        description="A test agent",
        owner_id=1,
        model="gpt-4",
        temperature=0.7,
        status="idle",
        enabled=True,
        created_at="2026-01-14T00:00:00",
    )


@pytest.fixture
def test_task():
    """Provide a test task"""
    return Task(
        id=1,
        title="Test Task",
        description="A test task",
        agent_id=1,
        priority=1,
        status="pending",
        created_at="2026-01-14T00:00:00",
    )


@pytest.fixture
def test_database():
    """Provide a test database connection"""

    # This would connect to a test database
    # For now, just a placeholder
    class TestDB:
        async def connect(self):
            pass

        async def disconnect(self):
            pass

    return TestDB()


@pytest.fixture
def db():
    """Provide database session for tests"""
    # Returns a mock session for testing
    from unittest.mock import AsyncMock, MagicMock

    mock_db = MagicMock()
    # Mock traditional query method for backward compatibility
    mock_db.query = MagicMock()
    # Mock new async execute method
    mock_db.execute = AsyncMock()

    # Configure return value for execute to be a mock result that can be iterated or awaited
    mock_result = MagicMock()
    mock_db.execute.return_value = mock_result

    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.close = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.scalar = AsyncMock()
    mock_db.scalars = AsyncMock()
    return mock_db


# Markers for organizing tests
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "async: mark test as async")
    config.addinivalue_line("markers", "slow: mark test as slow")


# Helper functions for testing
def create_test_auth_header(token: str) -> dict:
    """Create authorization header for tests"""
    return {"Authorization": f"Bearer {token}"}


def assert_response_structure(response, expected_keys: list):
    """Assert response has expected keys"""
    data = response.json()
    for key in expected_keys:
        assert key in data, f"Missing key '{key}' in response"
    return data


def assert_error_response(response, expected_error: str, expected_status: int = None):
    """Assert error response structure"""
    assert response.status_code == expected_status or response.status_code >= 400
    data = response.json()
    assert "error" in data
    assert data["error"] == expected_error
    assert "message" in data
    return data


@pytest.fixture(autouse=True)
def reset_db():
    """Reset database state between tests"""
    # This would reset test database
    yield
    # Cleanup after test


@pytest.fixture
def mock_external_api(monkeypatch):
    """Mock external API calls"""

    class MockAPI:
        @staticmethod
        def success(data=None):
            return {"status": "success", "data": data or {}}

        @staticmethod
        def error(message: str, code: str = "ERROR"):
            return {"status": "error", "code": code, "message": message}

    return MockAPI()
