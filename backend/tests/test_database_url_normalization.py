def _clear_settings_caches() -> None:
    from config import get_settings as get_root_settings
    from src.kortana.config import get_settings as get_src_settings

    get_root_settings.cache_clear()
    get_src_settings.cache_clear()


def test_root_settings_normalize_postgres_url(monkeypatch):
    raw_url = "postgresql://user:pass@host:5432/dbname?sslmode=require"
    expected_url = "postgresql+asyncpg://user:pass@host:5432/dbname?sslmode=require"

    monkeypatch.setenv("DATABASE_URL", raw_url)
    _clear_settings_caches()

    from config import get_settings

    assert get_settings().DATABASE_URL == expected_url

    _clear_settings_caches()


def test_root_database_config_preserves_neon_query_params(monkeypatch):
    raw_url = (
        "postgresql://user:pass@host:5432/dbname"
        "?sslmode=require&channel_binding=require"
    )
    async_url = (
        "postgresql+asyncpg://user:pass@host:5432/dbname"
        "?sslmode=require&channel_binding=require"
    )

    monkeypatch.setenv("DATABASE_URL", raw_url)
    _clear_settings_caches()

    from database import DatabaseConfig

    config = DatabaseConfig()

    assert config.get_url() == async_url
    assert config.get_sync_url() == raw_url

    _clear_settings_caches()


def test_src_database_config_normalizes_postgres_scheme(monkeypatch):
    raw_url = "postgres://user:pass@host:5432/dbname?sslmode=require"
    sync_url = "postgresql://user:pass@host:5432/dbname?sslmode=require"
    async_url = "postgresql+asyncpg://user:pass@host:5432/dbname?sslmode=require"

    monkeypatch.setenv("DATABASE_URL", raw_url)
    _clear_settings_caches()

    from src.kortana.database import DatabaseConfig

    config = DatabaseConfig()

    assert config.get_url() == async_url
    assert config.get_sync_url() == sync_url

    _clear_settings_caches()


def test_database_url_normalization_does_not_touch_sqlite(monkeypatch):
    sqlite_url = "sqlite+aiosqlite:///./test_kortana.db"

    monkeypatch.setenv("DATABASE_URL", sqlite_url)
    _clear_settings_caches()

    from config import get_settings as get_root_settings
    from src.kortana.config import get_settings as get_src_settings

    assert get_root_settings().DATABASE_URL == sqlite_url
    assert get_src_settings().DATABASE_URL == sqlite_url

    _clear_settings_caches()
