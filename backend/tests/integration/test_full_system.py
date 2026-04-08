"""Integration smoke tests for core backend readiness."""

from pathlib import Path

import pytest

from tests.conftest import SyncTestClient


def test_configuration():
    """Core settings should load and expose required local integrations."""
    from src.kortana.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    settings.validate()

    assert settings.GEMINI_API_KEY
    assert settings.GITHUB_TOKEN
    assert settings.DISCORD_BOT_TOKEN
    assert settings.PINECONE_API_KEY
    assert settings.STRIPE_SECRET_KEY
    assert settings.DATABASE_URL


def test_application_startup():
    """The FastAPI app should boot and serve a health response."""
    from src.kortana.main import app

    client = SyncTestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert app.title
    assert len(app.routes) > 0


def test_provider_connectivity():
    """Local provider clients should instantiate without network calls."""
    import anthropic
    import openai

    pytest.importorskip("pinecone")
    from pinecone import Pinecone

    from src.kortana.config import get_settings

    settings = get_settings()

    openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    Pinecone(api_key=settings.PINECONE_API_KEY)


def test_database_readiness():
    """Database and Alembic assets should be wired for the current environment."""
    from src.kortana.config import get_settings

    settings = get_settings()
    backend_dir = Path(__file__).resolve().parents[2]
    alembic_ini = backend_dir / "alembic.ini"
    versions_dir = backend_dir / "alembic" / "versions"

    assert settings.DATABASE_URL
    assert alembic_ini.exists()
    assert versions_dir.exists()
    assert any(path.suffix == ".py" for path in versions_dir.iterdir())

    if settings.DATABASE_URL.startswith("sqlite"):
        assert "test_kortana" in settings.DATABASE_URL
