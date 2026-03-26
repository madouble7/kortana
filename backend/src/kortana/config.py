"""
Configuration management for Kor'tana Backend
Handles environment-specific settings and validation
Loads secrets from .env file and environment variables
"""

import os
from functools import lru_cache
from pathlib import Path
from secrets import token_urlsafe
from typing import Any

from dotenv import load_dotenv

_ENV_FILENAMES = (".env",)
_PLACEHOLDER_VALUES = {
    "change-me-in-production",
    "your-secret-key-change-in-production",
    "your-secret-key-here",
    "your-heartbeat-token",
    "your-session-salt",
    "your-secure-password",
    "sk-...",
    "github_pat_...",
    "gsk_...",
    "pcsk_...",
}
_DEV_SECRET_KEY = token_urlsafe(48)


def _normalize_env_value(value: str | None) -> str | None:
    """Normalize empty environment values to None."""
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def _is_placeholder(value: str | None) -> bool:
    """Return True when a value is blank or matches a known placeholder."""
    normalized = _normalize_env_value(value)
    return normalized is None or normalized in _PLACEHOLDER_VALUES


def _get_env(name: str, default: str | None = None) -> str | None:
    """Read an environment variable, treating blank strings as unset."""
    return _normalize_env_value(os.getenv(name)) or default


def _normalize_database_url(url: str) -> str:
    """Normalize PostgreSQL URLs to the asyncpg dialect while preserving params."""
    normalized = url.strip()
    if normalized.startswith("postgresql+asyncpg://"):
        return normalized
    if normalized.startswith("postgres://"):
        return "postgresql+asyncpg://" + normalized[len("postgres://") :]
    if normalized.startswith("postgresql://"):
        return "postgresql+asyncpg://" + normalized[len("postgresql://") :]
    if normalized.startswith("postgresql+") and "://" in normalized:
        return "postgresql+asyncpg://" + normalized.split("://", 1)[1]
    return normalized


def _find_env_file(start_path: Path | None = None) -> Path | None:
    """Locate the nearest backend .env file by walking up parent directories."""
    current = (start_path or Path(__file__).resolve().parent).resolve()
    for directory in (current, *current.parents):
        for filename in _ENV_FILENAMES:
            candidate = directory / filename
            if candidate.is_file():
                return candidate
        if directory.name == "backend":
            break
    return None


_LOADED_ENV_FILE: Path | None = None
if (_get_env("KORTANA_SKIP_DOTENV") or "false").lower() != "true":
    _LOADED_ENV_FILE = _find_env_file()
    if _LOADED_ENV_FILE is not None:
        load_dotenv(_LOADED_ENV_FILE, override=False)


class Settings:
    """Application settings loaded from environment variables"""

    # Environment
    ENVIRONMENT: str = _get_env("ENVIRONMENT", "development") or "development"
    DEBUG: bool = ENVIRONMENT == "development"
    ENV_FILE: str | None = str(_LOADED_ENV_FILE) if _LOADED_ENV_FILE else None

    # Server
    HOST: str = _get_env("HOST", "0.0.0.0") or "0.0.0.0"
    PORT: int = int(_get_env("PORT", "8000") or "8000")

    # API Configuration
    API_TITLE: str = "Kor'tana Backend"
    API_VERSION: str = "0.1.0"
    API_DESCRIPTION: str = "Autonomous AI constellation API"

    # CORS Configuration
    CORS_ORIGINS: list[str] = (
        _get_env(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8080,http://localhost:5173,https://kortana.vercel.app,https://*.vercel.app",
        )
        or ""
    ).split(",")
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: list[str] = ["*"]

    # AI & LLM Providers
    OPENAI_API_KEY: str | None = _get_env("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = _get_env("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: str | None = _get_env("GOOGLE_API_KEY")
    GOOGLE_PROJECT_ID: str = _get_env("GOOGLE_PROJECT_ID", "") or ""
    OPENROUTER_API_KEY: str | None = _get_env("OPENROUTER_API_KEY")
    GROQ_API_KEY: str | None = _get_env("GROQ_API_KEY")
    # Gemini uses GEMINI_API_KEY or falls back to GOOGLE_API_KEY
    GEMINI_API_KEY: str = _get_env("GEMINI_API_KEY") or _get_env("GOOGLE_API_KEY") or ""

    # Vector Database
    PINECONE_API_KEY: str | None = _get_env("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: str = (
        _get_env("PINECONE_ENVIRONMENT", "us-east-1") or "us-east-1"
    )

    # Google Integration
    GOOGLE_DRIVE_API_KEY: str = _get_env("GOOGLE_DRIVE_API_KEY", "") or ""
    GOOGLE_CLIENT_ID: str | None = _get_env("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str | None = _get_env("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = (
        _get_env("GOOGLE_REDIRECT_URI", "http://localhost:3000/oauth/callback")
        or "http://localhost:3000/oauth/callback"
    )
    GOOGLE_REFRESH_TOKEN: str | None = _get_env("GOOGLE_REFRESH_TOKEN")
    GOOGLE_APPLICATION_CREDENTIALS: str | None = _get_env(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )

    # GitHub Integration
    GITHUB_TOKEN: str | None = _get_env("GITHUB_TOKEN")
    GITHUB_OWNER: str = _get_env("GITHUB_OWNER", "madouble7") or "madouble7"
    GITHUB_REPO: str = _get_env("GITHUB_REPO", "kortana") or "kortana"

    # Discord Integration
    DISCORD_BOT_TOKEN: str | None = _get_env("DISCORD_BOT_TOKEN")
    DISCORD_CLIENT_ID: str | None = _get_env("CLIENT_ID")

    # Twilio Integration
    TWILIO_ACCOUNT_SID: str | None = _get_env("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str | None = _get_env("TWILIO_AUTH_TOKEN")

    # Stripe Payment
    STRIPE_SECRET_KEY: str | None = _get_env("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: str | None = _get_env("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: str | None = _get_env("STRIPE_WEBHOOK_SECRET")

    # AWS Integration
    AWS_ACCESS_KEY_ID: str | None = _get_env("AWS_BACKUP_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str | None = _get_env("AWS_BACKUP_SECRET_ACCESS_KEY")

    # Database
    DB_HOST: str = _get_env("DB_HOST", "localhost") or "localhost"
    DB_PORT: int = int(_get_env("DB_PORT", "5432") or "5432")
    DB_NAME: str = _get_env("DB_NAME", "kortana") or "kortana"
    DB_USER: str = _get_env("DB_USER", "postgres") or "postgres"
    DB_PASSWORD: str = _get_env("DB_PASSWORD", "") or ""
    # Security
    SESSION_SALT: str | None = _get_env("SESSION_SALT")
    HEARTBEAT_TOKEN: str | None = _get_env("HEARTBEAT_TOKEN")

    @property
    def DATABASE_URL(self) -> str:
        """Constructs the async database URL from settings."""
        env_url = _get_env("DATABASE_URL")
        if env_url:
            return _normalize_database_url(env_url)

        if self.DB_PASSWORD:
            return (
                f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )

        if self.ENVIRONMENT == "production":
            print(
                "[!] WARNING: No DATABASE_URL in production "
                "— falling back to SQLite (ephemeral on most hosts)"
            )

        return "sqlite+aiosqlite:///./kortana.db"

    # Logging
    LOG_LEVEL: str = _get_env("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG") or (
        "INFO" if not DEBUG else "DEBUG"
    )
    LOG_FORMAT: str = _get_env("LOG_FORMAT", "json") or "json"

    # Security
    ALLOWED_HOSTS: list[str] = (
        _get_env("ALLOWED_HOSTS", "localhost,127.0.0.1") or ""
    ).split(",")
    SECRET_KEY: str = _get_env("SECRET_KEY") or (
        _DEV_SECRET_KEY if ENVIRONMENT != "production" else ""
    )

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = (
        _get_env("RATE_LIMIT_ENABLED", "true") or "true"
    ).lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(_get_env("RATE_LIMIT_REQUESTS", "100") or "100")
    RATE_LIMIT_PERIOD: int = int(_get_env("RATE_LIMIT_PERIOD", "60") or "60")

    # Redis Config
    REDIS_URL: str | None = _get_env("REDIS_URL")
    REDIS_HOST: str = _get_env("REDIS_HOST", "localhost") or "localhost"
    REDIS_PORT: int = int(_get_env("REDIS_PORT", "6379") or "6379")

    # Internal Settings
    @property
    def INTERNAL_REDIS_URL(self) -> str:
        """Constructs the Redis URL from settings."""
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # Timeouts
    REQUEST_TIMEOUT: int = int(_get_env("REQUEST_TIMEOUT", "30") or "30")
    API_TIMEOUT: int = int(_get_env("API_TIMEOUT", "15") or "15")

    # Autonomous Task Configuration
    TASK_MAX_RETRIES: int = int(_get_env("TASK_MAX_RETRIES", "3") or "3")
    TASK_RETRY_DELAY: int = int(_get_env("TASK_RETRY_DELAY", "300") or "300")
    REPO_ROOT: str = _get_env("REPO_ROOT", ".") or "."
    KORTANA_BACKEND_URL: str = (
        _get_env("KORTANA_BACKEND_URL", "http://localhost:8000")
        or "http://localhost:8000"
    )

    # Autonomy Configuration
    AUTONOMOUS_MODE: bool = (
        _get_env("KORTANA_AUTONOMOUS_MODE", "false") or "false"
    ).lower() == "true"
    AUTONOMY_CYCLE_INTERVAL: int = int(
        _get_env("AUTONOMY_CYCLE_INTERVAL", "600") or "600"
    )

    @classmethod
    def validate(cls) -> None:
        """Validate required settings on startup"""
        if _LOADED_ENV_FILE is not None:
            load_dotenv(_LOADED_ENV_FILE, override=False)
        else:
            print("[!] Warning: No .env file found; relying on process environment")

        settings = cls()

        # Core secrets that should always be present
        # Note: Some keys have fallbacks (e.g., GEMINI uses GOOGLE_API_KEY)
        critical_keys = [
            (
                "GEMINI_API_KEY",
                ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
                "Gemini/Google API",
            ),
            ("GITHUB_TOKEN", ["GITHUB_TOKEN"], "GitHub Token"),
            ("DISCORD_BOT_TOKEN", ["DISCORD_BOT_TOKEN"], "Discord Bot Token"),
            ("OPENAI_API_KEY", ["OPENAI_API_KEY"], "OpenAI API Key"),
        ]

        missing = []
        for key, fallbacks, desc in critical_keys:
            # Check if any of the fallback keys are available
            value = None
            for fb_key in fallbacks:
                value = os.getenv(fb_key)
                if value and value.strip() != "":
                    break

            if not value:
                missing.append(f"{key} ({desc})")

        if missing:
            print("[#] Warning: Missing API keys (some features will be disabled):")
            for item in missing:
                print(f"   - {item}")
        else:
            print("[+] All critical API keys validated and loaded")

        if _is_placeholder(settings.SECRET_KEY):
            raise ValueError("SECRET_KEY must be configured before startup")

        if (
            settings.ENVIRONMENT != "production"
            and settings.SECRET_KEY == _DEV_SECRET_KEY
        ):
            print(
                "[!] Warning: SECRET_KEY not set; using an ephemeral development secret"
            )

        # Validate database connection string
        try:
            db_url = settings.DATABASE_URL
            if settings.DB_PASSWORD and settings.DB_PASSWORD.lower() in {
                "supersecretpassword",
                "password",
                "changeme",
            }:
                message = "Database password is using an insecure default value"
                if settings.ENVIRONMENT == "production":
                    raise ValueError(message)
                print(f"[!] Warning: {message}")
            elif not _get_env("DATABASE_URL") and not settings.DB_PASSWORD:
                print(
                    "[!] Warning: DATABASE_URL not set; falling back to local SQLite database"
                )
            if settings.ENVIRONMENT == "production" and db_url.startswith("sqlite"):
                print(
                    "[!] Warning: Production is configured to use SQLite; verify deployment settings"
                )
        except Exception as e:
            if settings.ENVIRONMENT == "production":
                raise
            print(f"[!] Warning: Database configuration issue: {e}")

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary (excluding sensitive values)"""
        sensitive_keys = {
            "GEMINI_API_KEY",
            "GITHUB_TOKEN",
            "SECRET_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY",
            "DISCORD_BOT_TOKEN",
            "TWILIO_AUTH_TOKEN",
            "STRIPE_SECRET_KEY",
            "AWS_SECRET_ACCESS_KEY",
            "DB_PASSWORD",
            "OPENROUTER_API_KEY",
            "GROQ_API_KEY",
            "PINECONE_API_KEY",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REFRESH_TOKEN",
            "STRIPE_WEBHOOK_SECRET",
            "SESSION_SALT",
            "HEARTBEAT_TOKEN",
        }
        return {
            key: (value if key not in sensitive_keys else "***REDACTED***")
            for key, value in self.__class__.__dict__.items()
            if not key.startswith("_") and not callable(value)
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get settings singleton instance with .env already loaded"""
    return Settings()
