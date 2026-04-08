"""Security-focused regression tests for configuration handling."""

from __future__ import annotations

import importlib
import sys

import pytest

MODULE_NAME = "src.kortana.config"
ENV_KEYS = [
    "KORTANA_SKIP_DOTENV",
    "ENVIRONMENT",
    "SECRET_KEY",
    "DATABASE_URL",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GITHUB_TOKEN",
    "DISCORD_BOT_TOKEN",
    "OPENAI_API_KEY",
    "RATE_LIMIT_PROXY_MODE",
    "RATE_LIMIT_TRUSTED_PROXIES",
    "KORTANA_MODEL_USAGE_LANE",
    "KORTANA_CORE_MODELS",
    "KORTANA_EXPERIMENTAL_MODELS",
    "KORTANA_QUARANTINE_MODELS",
    "GMAIL_SCOPES",
]


def reload_config_module(monkeypatch: pytest.MonkeyPatch, **overrides: str):
    """Reload the config module with a controlled environment."""
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("KORTANA_SKIP_DOTENV", "true")
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)

    module = importlib.import_module(MODULE_NAME)
    module = importlib.reload(module)
    module.get_settings.cache_clear()
    return module


def test_find_env_file_searches_parent_directories(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The config loader should discover backend/.env when repo-root .env is absent."""
    config_module = reload_config_module(monkeypatch)
    package_dir = tmp_path / "backend" / "src" / "kortana"
    package_dir.mkdir(parents=True)
    env_file = tmp_path / "backend" / ".env"
    env_file.write_text("SECRET_KEY=test\n", encoding="utf-8")

    assert config_module._find_env_file(package_dir) == env_file


def test_find_env_file_falls_back_to_repo_root_env(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The config loader should discover a repo-root .env when present."""
    config_module = reload_config_module(monkeypatch)
    package_dir = tmp_path / "backend" / "src" / "kortana"
    package_dir.mkdir(parents=True)
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET_KEY=test\n", encoding="utf-8")

    assert config_module._find_env_file(package_dir) == env_file


def test_find_env_file_prefers_repo_root_over_backend_env(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Local dev should not let backend/.env shadow the repo-root environment."""
    config_module = reload_config_module(monkeypatch)
    package_dir = tmp_path / "backend" / "src" / "kortana"
    package_dir.mkdir(parents=True)
    backend_env = tmp_path / "backend" / ".env"
    backend_env.write_text("OPENAI_API_KEY=placeholder\n", encoding="utf-8")
    root_env = tmp_path / ".env"
    root_env.write_text("GEMINI_API_KEY=realish\n", encoding="utf-8")

    assert config_module._find_env_file(package_dir) == root_env


def test_get_env_prefers_real_dotenv_value_over_placeholder_process_env(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stale placeholder process env should not shadow a real repo-root secret."""
    config_module = reload_config_module(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=sk-real-dotenv-key\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "<your-api-key-here>")

    config_module._LOADED_ENV_FILE = env_file
    config_module._DOTENV_VALUES = {"OPENAI_API_KEY": "sk-real-dotenv-key"}

    assert config_module._get_env("OPENAI_API_KEY") == "sk-real-dotenv-key"


def test_config_import_tolerates_missing_python_dotenv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Runtime config should still import when python-dotenv is unavailable."""
    original_dotenv = sys.modules.pop("dotenv", None)
    monkeypatch.setitem(sys.modules, "dotenv", None)
    try:
        config_module = reload_config_module(
            monkeypatch,
            OPENAI_API_KEY="openai-test-key",
            GEMINI_API_KEY="gemini-test-key",
        )
        settings = config_module.get_settings()
        assert settings.OPENAI_API_KEY == "openai-test-key"
        assert settings.GEMINI_API_KEY == "gemini-test-key"
    finally:
        sys.modules.pop("dotenv", None)
        if original_dotenv is not None:
            sys.modules["dotenv"] = original_dotenv


def test_secret_key_is_generated_for_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Development mode should avoid a static fallback secret."""
    config_module = reload_config_module(monkeypatch, ENVIRONMENT="development")

    settings = config_module.get_settings()
    assert settings.SECRET_KEY
    assert settings.SECRET_KEY != "change-me-in-production"


def test_database_url_falls_back_to_sqlite_in_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Development mode should default to a local SQLite database when DB creds are absent."""
    config_module = reload_config_module(monkeypatch, ENVIRONMENT="development")

    settings = config_module.get_settings()
    assert settings.DATABASE_URL == "sqlite+aiosqlite:///./kortana.db"


def test_validate_rejects_placeholder_secret_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production mode must fail fast when a placeholder secret key is used."""
    config_module = reload_config_module(
        monkeypatch,
        ENVIRONMENT="production",
        SECRET_KEY="change-me-in-production",
        DATABASE_URL="sqlite+aiosqlite:///./test.db",
        GEMINI_API_KEY="gemini-test-key",
        GITHUB_TOKEN="github-test-token",
        DISCORD_BOT_TOKEN="discord-test-token",
        OPENAI_API_KEY="openai-test-key",
    )

    with pytest.raises(ValueError, match="SECRET_KEY"):
        config_module.Settings.validate()


def test_rate_limit_proxy_settings_parse_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Proxy mode and trusted proxies should parse cleanly from env."""
    config_module = reload_config_module(
        monkeypatch,
        RATE_LIMIT_PROXY_MODE="true",
        RATE_LIMIT_TRUSTED_PROXIES="127.0.0.1,10.0.0.0/8 , 192.168.1.10",
    )

    settings = config_module.get_settings()
    assert settings.RATE_LIMIT_PROXY_MODE is True
    assert settings.RATE_LIMIT_TRUSTED_PROXIES == [
        "127.0.0.1",
        "10.0.0.0/8",
        "192.168.1.10",
    ]


def test_model_lane_settings_parse_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Model lane controls should parse cleanly from env."""
    config_module = reload_config_module(
        monkeypatch,
        KORTANA_MODEL_USAGE_LANE="experimental",
        KORTANA_CORE_MODELS="gpt-4o, gemini-2.0-flash",
        KORTANA_EXPERIMENTAL_MODELS="gpt-5-future-preview",
        KORTANA_QUARANTINE_MODELS="ft:gpt-4o-mini-2024-07-18:personal::rogue",
    )

    settings = config_module.get_settings()
    assert settings.KORTANA_MODEL_USAGE_LANE == "experimental"
    assert settings.KORTANA_CORE_MODELS == ["gpt-4o", "gemini-2.0-flash"]
    assert settings.KORTANA_EXPERIMENTAL_MODELS == ["gpt-5-future-preview"]
    assert settings.KORTANA_QUARANTINE_MODELS == [
        "ft:gpt-4o-mini-2024-07-18:personal::rogue"
    ]


def test_gmail_scopes_parse_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gmail scopes should parse cleanly from env for OAuth bootstrap/runtime parity."""
    config_module = reload_config_module(
        monkeypatch,
        GMAIL_SCOPES=(
            "https://www.googleapis.com/auth/gmail.modify,"
            "https://www.googleapis.com/auth/gmail.send"
        ),
    )

    settings = config_module.get_settings()
    assert settings.GMAIL_SCOPES == [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.send",
    ]
