"""
Pytest configuration and fixtures for Kor'tana Backend tests
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import patch, MagicMock

# Set test environment variables before any imports
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_kortana.db"
os.environ["GEMINI_API_KEY"] = "test_gemini_key"
os.environ["GITHUB_TOKEN"] = "test_github_token"
os.environ["DISCORD_BOT_TOKEN"] = "test_discord_token"
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["ANTHROPIC_API_KEY"] = "test_anthropic_key"
os.environ["GOOGLE_API_KEY"] = "test_google_key"
os.environ["OPENROUTER_API_KEY"] = "test_openrouter_key"
os.environ["GROQ_API_KEY"] = "test_groq_key"
os.environ["PINECONE_API_KEY"] = "test_pinecone_key"
os.environ["TWILIO_ACCOUNT_SID"] = "test_twilio_sid"
os.environ["TWILIO_AUTH_TOKEN"] = "test_twilio_token"
os.environ["STRIPE_SECRET_KEY"] = "test_stripe_key"
os.environ["STRIPE_PUBLISHABLE_KEY"] = "test_stripe_publishable"
os.environ["STRIPE_WEBHOOK_SECRET"] = "test_stripe_webhook"
os.environ["AWS_ACCESS_KEY_ID"] = "test_aws_key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test_aws_secret"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing"
os.environ["SESSION_SALT"] = "test_session_salt"
os.environ["HEARTBEAT_TOKEN"] = "test_heartbeat_token"

# Patch print function to handle emojis before any imports
_original_print = print
def safe_print(*args, **kwargs):
    # Filter out strings containing emojis
    filtered_args = []
    for arg in args:
        if isinstance(arg, str):
            # Remove common emojis that cause issues
            arg = arg.replace("✅", "[OK]").replace("❌", "[ERROR]").replace("⚠️", "[WARN]").replace("❌", "[FAIL]").replace("❌", "[FAIL]")
        filtered_args.append(arg)
    return _original_print(*filtered_args, **kwargs)
print = safe_print

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kortana.config import Settings
from src.kortana.database import DatabaseManager


class SyncTestClient:
    """A synchronous test client that wraps httpx.AsyncClient for ASGI apps."""

    def __init__(self, app):
        self.app = app
        self.base_url = "http://testserver"
        self._loop = None
        self._client = None

    def _get_loop(self):
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    def _run_async(self, coro):
        loop = self._get_loop()
        return loop.run_until_complete(coro)

    async def _get_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(
                transport=httpx.ASGITransport(app=self.app),
                base_url=self.base_url
            )
        return self._client

    def get(self, url, **kwargs):
        return self._run_async(self._aget(url, **kwargs))

    def post(self, url, **kwargs):
        return self._run_async(self._apost(url, **kwargs))

    def put(self, url, **kwargs):
        return self._run_async(self._aput(url, **kwargs))

    def delete(self, url, **kwargs):
        return self._run_async(self._adelete(url, **kwargs))

    def patch(self, url, **kwargs):
        return self._run_async(self._apatch(url, **kwargs))

    async def _aget(self, url, **kwargs):
        client = await self._get_client()
        return await client.get(url, **kwargs)

    async def _apost(self, url, **kwargs):
        client = await self._get_client()
        return await client.post(url, **kwargs)

    async def _aput(self, url, **kwargs):
        client = await self._get_client()
        return await client.put(url, **kwargs)

    async def _adelete(self, url, **kwargs):
        client = await self._get_client()
        return await client.delete(url, **kwargs)

    async def _apatch(self, url, **kwargs):
        client = await self._get_client()
        return await client.patch(url, **kwargs)

    def close(self):
        if self._client and self._loop:
            self._loop.run_until_complete(self._client.aclose())
        if self._loop:
            self._loop.close()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import these inside fixtures to avoid early initialization issues
# from src.kortana.auth import create_access_token
# from src.kortana.config import Settings
# from src.kortana.database import get_db
# from src.kortana.main import app
# from src.kortana.schemas import Agent, Task, User


@pytest.fixture(scope="session")
def test_db_url():
    """Provide test database URL using SQLite"""
    return "sqlite+aiosqlite:///./test_kortana.db"


@pytest.fixture(scope="session")
async def test_engine(test_db_url):
    """Create test database engine"""
    engine = create_async_engine(test_db_url, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def setup_test_db(test_db_url, test_engine):
    """Set up test database schema using alembic migrations"""
    import subprocess
    import os
    from pathlib import Path

    # Set DATABASE_URL for alembic
    env = os.environ.copy()
    env["DATABASE_URL"] = test_db_url.replace("aiosqlite", "sqlite")

    # Run alembic upgrade to head
    backend_dir = Path(__file__).parent.parent
    alembic_dir = backend_dir / "alembic"
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        # If alembic fails, fall back to creating tables directly
        from src.kortana.models import Base
        from sqlalchemy import create_engine

        sync_url = test_db_url.replace("aiosqlite", "sqlite")
        engine = create_engine(sync_url)
        Base.metadata.create_all(engine)
        engine.dispose()

    yield

    # Clean up test database file after tests
    db_file = test_db_url.replace("sqlite+aiosqlite:///", "")
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture
async def test_db_session(test_engine, setup_test_db):
    """Provide test database session"""
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture
def mock_settings(test_db_url):
    """Mock settings for tests with test database and mock API keys"""
    # Mock environment variables for settings
    mock_env = {
        "ENVIRONMENT": "testing",
        "DATABASE_URL": test_db_url,
        "GEMINI_API_KEY": "test_gemini_key",
        "GITHUB_TOKEN": "test_github_token",
        "DISCORD_BOT_TOKEN": "test_discord_token",
        "OPENAI_API_KEY": "test_openai_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "GOOGLE_API_KEY": "test_google_key",
        "OPENROUTER_API_KEY": "test_openrouter_key",
        "GROQ_API_KEY": "test_groq_key",
        "PINECONE_API_KEY": "test_pinecone_key",
        "TWILIO_ACCOUNT_SID": "test_twilio_sid",
        "TWILIO_AUTH_TOKEN": "test_twilio_token",
        "STRIPE_SECRET_KEY": "test_stripe_key",
        "STRIPE_PUBLISHABLE_KEY": "test_stripe_publishable",
        "STRIPE_WEBHOOK_SECRET": "test_stripe_webhook",
        "AWS_ACCESS_KEY_ID": "test_aws_key",
        "AWS_SECRET_ACCESS_KEY": "test_aws_secret",
        "SECRET_KEY": "test_secret_key_for_testing",
        "SESSION_SALT": "test_session_salt",
        "HEARTBEAT_TOKEN": "test_heartbeat_token",
    }

    with patch.dict(os.environ, mock_env):
        settings = Settings()
        yield settings


@pytest.fixture
def app_fixture(db, mock_settings):
    """Provide the FastAPI app with mocked database and settings"""
    from src.kortana.main import app
    from src.kortana.database import get_db
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
    return SyncTestClient(app_fixture)


@pytest.fixture
def test_user():
    """Provide a test user"""
    from src.kortana.schemas import User
    return User(
        id="1",
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        created_at="2026-01-14T00:00:00",
    )


@pytest.fixture
def test_token(test_user):
    """Provide a valid test JWT token"""
    from src.kortana.auth import create_access_token
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
    from src.kortana.schemas import Agent
    return Agent(
        id="1",
        name="Test Agent",
        description="A test agent",
        owner_id="1",
        model="gpt-4",
        temperature=0.7,
        status="idle",
        enabled=True,
        created_at="2026-01-14T00:00:00",
    )


@pytest.fixture
def test_task():
    """Provide a test task"""
    from src.kortana.schemas import Task
    return Task(
        id="1",
        title="Test Task",
        description="A test task",
        agent_id="1",
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
def db(test_db_session):
    """Provide database session for tests"""
    return test_db_session


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


# GitHub API calls are mocked via httpx in mock_httpx_requests fixture


@pytest.fixture(autouse=True)
def mock_gemini_api():
    """Mock Gemini API calls"""
    with patch("google.genai.Client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Mock the models.generate_content method
        mock_response = MagicMock()
        mock_response.text = "Mocked Gemini response"
        mock_instance.models.generate_content.return_value = mock_response

        yield mock_instance


@pytest.fixture(autouse=True)
def mock_discord_api():
    """Mock Discord API calls"""
    with patch("discord.Client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture(autouse=True)
def mock_openai_api():
    """Mock OpenAI API calls"""
    with patch("openai.OpenAI") as mock_openai:
        mock_instance = MagicMock()
        mock_client = MagicMock()
        mock_instance.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Mocked OpenAI response"))]
        )
        yield mock_client


@pytest.fixture(autouse=True)
def mock_anthropic_api():
    """Mock Anthropic API calls"""
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_instance = MagicMock()
        mock_client = MagicMock()
        mock_instance.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text="Mocked Anthropic response")])
        yield mock_client


@pytest.fixture(autouse=True)
def mock_httpx_requests():
    """Mock all httpx requests for external APIs"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.get.return_value = MagicMock(status_code=200, json=lambda: {"mock": "response"})
        mock_instance.post.return_value = MagicMock(status_code=200, json=lambda: {"mock": "response"})
        mock_instance.put.return_value = MagicMock(status_code=200, json=lambda: {"mock": "response"})
        mock_instance.delete.return_value = MagicMock(status_code=200, json=lambda: {"mock": "response"})
        yield mock_instance


@pytest.fixture(autouse=True, scope="session")
def suppress_emoji_prints():
    """Suppress emoji prints that cause encoding issues on Windows"""
    def safe_print(*args, **kwargs):
        # Filter out strings containing emojis
        filtered_args = []
        for arg in args:
            if isinstance(arg, str):
                # Remove common emojis that cause issues
                arg = arg.replace("✅", "[OK]").replace("❌", "[ERROR]").replace("⚠️", "[WARN]").replace("❌", "[FAIL]")
            filtered_args.append(arg)
        return print(*filtered_args, **kwargs)

    with patch("builtins.print", side_effect=safe_print):
        yield
