from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_database_manager_falls_back_to_sqlite_in_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/kortana")
    monkeypatch.setenv("KORTANA_DEV_DB_FALLBACK", "true")

    from src.kortana.config import get_settings

    get_settings.cache_clear()

    from src.kortana.database import DatabaseConfig, DatabaseManager

    manager = DatabaseManager(DatabaseConfig())
    attempted_urls: list[str] = []

    async def fake_initialize_current_config(self: DatabaseManager) -> None:
        attempted_urls.append(self.config.get_url())
        if len(attempted_urls) == 1:
            raise OSError("connection refused")
        self.engine = object()  # type: ignore[assignment]
        self.session_factory = object()  # type: ignore[assignment]
        self._connected = True

    async def fake_reset_engine_state(self: DatabaseManager) -> None:
        self.engine = None
        self.session_factory = None
        self._connected = False

    with (
        patch.object(
            DatabaseManager,
            "_initialize_current_config",
            fake_initialize_current_config,
        ),
        patch.object(DatabaseManager, "_reset_engine_state", fake_reset_engine_state),
    ):
        await manager.initialize()

    assert len(attempted_urls) == 2
    assert attempted_urls[0].startswith("postgresql+asyncpg://")
    assert attempted_urls[1].startswith("sqlite+aiosqlite:///")
    assert manager.config.is_sqlite is True
    assert manager._connected is True


@pytest.mark.asyncio
async def test_database_manager_does_not_fallback_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/kortana")
    monkeypatch.setenv("KORTANA_DEV_DB_FALLBACK", "true")

    from src.kortana.config import get_settings

    get_settings.cache_clear()

    from src.kortana.database import DatabaseConfig, DatabaseManager

    manager = DatabaseManager(DatabaseConfig())
    attempted_urls: list[str] = []

    async def fake_initialize_current_config(self: DatabaseManager) -> None:
        attempted_urls.append(self.config.get_url())
        raise OSError("connection refused")

    async def fake_reset_engine_state(self: DatabaseManager) -> None:
        self.engine = None
        self.session_factory = None
        self._connected = False

    with (
        patch.object(
            DatabaseManager,
            "_initialize_current_config",
            fake_initialize_current_config,
        ),
        patch.object(DatabaseManager, "_reset_engine_state", fake_reset_engine_state),
    ):
        with pytest.raises(OSError, match="connection refused"):
            await manager.initialize()

    assert attempted_urls == ["postgresql+asyncpg://user:pass@localhost:5432/kortana"]
    assert manager.config.is_sqlite is False
