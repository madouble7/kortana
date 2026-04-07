"""
Configuration management for Kor'tana Backend
Handles environment-specific settings and validation
Loads secrets from .env file and environment variables
"""

import os
from functools import lru_cache
from os import PathLike
from pathlib import Path
from secrets import token_urlsafe
from typing import IO, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dotenv import dotenv_values, load_dotenv
else:
    try:
        from dotenv import dotenv_values, load_dotenv
    except ModuleNotFoundError:  # pragma: no cover - exercised in packaging/runtime smoke tests
        def load_dotenv(
            dotenv_path: str | PathLike[str] | None = None,
            stream: IO[str] | None = None,
            verbose: bool = False,
            override: bool = False,
            interpolate: bool = True,
            encoding: str | None = "utf-8",
        ) -> bool:
            """No-op fallback when python-dotenv is unavailable at runtime."""
            del dotenv_path, stream, verbose, override, interpolate, encoding
            return False

        def dotenv_values(
            dotenv_path: str | PathLike[str] | None = None,
            stream: IO[str] | None = None,
            verbose: bool = False,
            interpolate: bool = True,
            encoding: str | None = "utf-8",
        ) -> dict[str, str | None]:
            """Return no .env values when python-dotenv is unavailable."""
            del dotenv_path, stream, verbose, interpolate, encoding
            return {}

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
    return (
        normalized is None
        or normalized in _PLACEHOLDER_VALUES
        or (
            normalized.startswith("<")
            and normalized.endswith(">")
            and "your-" in normalized.lower()
        )
    )


def _get_env(name: str, default: str | None = None) -> str | None:
    """Read an environment variable with placeholder-aware .env fallback."""
    env_value = _normalize_env_value(os.getenv(name))
    dotenv_value = _normalize_env_value(_DOTENV_VALUES.get(name))

    if env_value and not _is_placeholder(env_value):
        return env_value
    if dotenv_value and not _is_placeholder(dotenv_value):
        return dotenv_value
    if env_value is not None:
        return env_value
    if dotenv_value is not None:
        return dotenv_value
    return default


def _split_csv_env(name: str, default: str = "") -> list[str]:
    """Parse a comma-separated environment variable into a trimmed string list."""
    raw_value = _get_env(name, default) or ""
    return [entry.strip() for entry in raw_value.split(",") if entry.strip()]


def _get_bool_env(name: str, default: str = "false") -> bool:
    """Parse a boolean environment variable using true/false semantics."""
    return (str(_get_env(name, default) or default)).lower() == "true"


def _get_int_env(name: str, default: str) -> int:
    """Parse an integer environment variable with a required string default."""
    return int(_get_env(name, default) or default)


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
    """Locate the preferred .env file, favouring the repo root over backend/.env."""
    current = (start_path or Path(__file__).resolve().parent).resolve()
    for directory in (current, *current.parents):
        if directory.name == "backend":
            for filename in _ENV_FILENAMES:
                repo_candidate = directory.parent / filename
                if repo_candidate.is_file():
                    return repo_candidate
            for filename in _ENV_FILENAMES:
                backend_candidate = directory / filename
                if backend_candidate.is_file():
                    return backend_candidate
            break
        for filename in _ENV_FILENAMES:
            candidate = directory / filename
            if candidate.is_file():
                return candidate
    return None


_LOADED_ENV_FILE: Path | None = None
_DOTENV_VALUES: dict[str, str | None] = {}
if (_get_env("KORTANA_SKIP_DOTENV") or "false").lower() != "true":
    _LOADED_ENV_FILE = _find_env_file()
    if _LOADED_ENV_FILE is not None:
        _DOTENV_VALUES = {
            key: _normalize_env_value(value)
            for key, value in dotenv_values(_LOADED_ENV_FILE).items()
        }
        load_dotenv(_LOADED_ENV_FILE, override=False)


class Settings:
    """Application settings loaded from environment variables"""
    def __init__(self) -> None:
        # Environment
        self.ENVIRONMENT: str = _get_env("ENVIRONMENT", "development") or "development"
        self.DEBUG: bool = self.ENVIRONMENT == "development"
        self.ENV_FILE: str | None = str(_LOADED_ENV_FILE) if _LOADED_ENV_FILE else None

        # Server
        self.HOST: str = _get_env("HOST", "0.0.0.0") or "0.0.0.0"
        self.PORT: int = _get_int_env("PORT", "8000")

        # API Configuration
        self.API_TITLE: str = "Kor'tana Backend"
        self.API_VERSION: str = "0.1.0"
        self.API_DESCRIPTION: str = "Autonomous AI constellation API"

        # CORS Configuration
        self.CORS_ORIGINS: list[str] = (
            _get_env(
                "CORS_ORIGINS",
                "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8080,http://localhost:5173,http://127.0.0.1:5173,https://kortana.vercel.app,https://*.vercel.app",
            )
            or ""
        ).split(",")
        self.CORS_CREDENTIALS: bool = True
        self.CORS_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.CORS_HEADERS: list[str] = ["*"]

        # AI & LLM Providers
        self.OPENAI_API_KEY: str | None = _get_env("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY: str | None = _get_env("ANTHROPIC_API_KEY")
        self.GOOGLE_API_KEY: str | None = _get_env("GOOGLE_API_KEY")
        self.GOOGLE_PROJECT_ID: str = _get_env("GOOGLE_PROJECT_ID", "") or ""
        self.OPENROUTER_API_KEY: str | None = _get_env("OPENROUTER_API_KEY")
        self.GROQ_API_KEY: str | None = _get_env("GROQ_API_KEY")
        self.GEMINI_API_KEY: str = (
            _get_env("GEMINI_API_KEY") or _get_env("GOOGLE_API_KEY") or ""
        )
        self.KORTANA_MODEL_USAGE_LANE: str = (
            _get_env("KORTANA_MODEL_USAGE_LANE", "core") or "core"
        ).lower()
        self.KORTANA_CORE_MODELS: list[str] = _split_csv_env("KORTANA_CORE_MODELS")
        self.KORTANA_EXPERIMENTAL_MODELS: list[str] = _split_csv_env(
            "KORTANA_EXPERIMENTAL_MODELS"
        )
        self.KORTANA_QUARANTINE_MODELS: list[str] = _split_csv_env(
            "KORTANA_QUARANTINE_MODELS"
        )
        self.KORTANA_OPENAI_STATEFUL_CHAT_ENABLED: bool = _get_bool_env(
            "KORTANA_OPENAI_STATEFUL_CHAT_ENABLED",
            "true",
        )

        # Vector Database
        self.PINECONE_API_KEY: str | None = _get_env("PINECONE_API_KEY")
        self.PINECONE_ENVIRONMENT: str = (
            _get_env("PINECONE_ENVIRONMENT", "us-east-1") or "us-east-1"
        )

        # Google Integration
        self.GOOGLE_DRIVE_API_KEY: str = _get_env("GOOGLE_DRIVE_API_KEY", "") or ""
        self.GOOGLE_CLIENT_ID: str | None = _get_env("GOOGLE_CLIENT_ID")
        self.GOOGLE_CLIENT_SECRET: str | None = _get_env("GOOGLE_CLIENT_SECRET")
        self.GOOGLE_REDIRECT_URI: str = (
            _get_env("GOOGLE_REDIRECT_URI", "http://localhost:3000/oauth/callback")
            or "http://localhost:3000/oauth/callback"
        )
        self.GOOGLE_REFRESH_TOKEN: str | None = _get_env("GOOGLE_REFRESH_TOKEN")
        self.GOOGLE_APPLICATION_CREDENTIALS: str | None = _get_env(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )

        # GitHub Integration
        self.GITHUB_TOKEN: str | None = _get_env("GITHUB_TOKEN")
        self.GITHUB_WEBHOOK_SECRET: str | None = _get_env("GITHUB_WEBHOOK_SECRET")
        self.GITHUB_OWNER: str = _get_env("GITHUB_OWNER", "madouble7") or "madouble7"
        self.GITHUB_REPO: str = _get_env("GITHUB_REPO", "kortana") or "kortana"
        self.KORTANA_GITHUB_MODE: str = (
            _get_env("KORTANA_GITHUB_MODE", "full") or "full"
        ).lower()
        self.KORTANA_LOCAL_BACKLOG_ENABLED: bool = _get_bool_env(
            "KORTANA_LOCAL_BACKLOG_ENABLED",
            "true",
        )

        # Discord Integration
        self.DISCORD_ENABLED: bool = _get_bool_env("DISCORD_ENABLED", "false")
        self.DISCORD_BOT_TOKEN: str | None = _get_env("DISCORD_BOT_TOKEN")
        self.DISCORD_CLIENT_ID: str | None = _get_env("CLIENT_ID")

        # Twilio Integration
        self.TWILIO_ACCOUNT_SID: str | None = _get_env("TWILIO_ACCOUNT_SID")
        self.TWILIO_AUTH_TOKEN: str | None = _get_env("TWILIO_AUTH_TOKEN")

        # Stripe Payment
        self.STRIPE_SECRET_KEY: str | None = _get_env("STRIPE_SECRET_KEY")
        self.STRIPE_PUBLISHABLE_KEY: str | None = _get_env("STRIPE_PUBLISHABLE_KEY")
        self.STRIPE_WEBHOOK_SECRET: str | None = _get_env("STRIPE_WEBHOOK_SECRET")

        # AWS Integration
        self.AWS_ACCESS_KEY_ID: str | None = _get_env("AWS_BACKUP_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY: str | None = _get_env(
            "AWS_BACKUP_SECRET_ACCESS_KEY"
        )

        # Database
        self.DB_HOST: str = _get_env("DB_HOST", "localhost") or "localhost"
        self.DB_PORT: int = _get_int_env("DB_PORT", "5432")
        self.DB_NAME: str = _get_env("DB_NAME", "kortana") or "kortana"
        self.DB_USER: str = _get_env("DB_USER", "postgres") or "postgres"
        self.DB_PASSWORD: str = _get_env("DB_PASSWORD", "") or ""

        # Security
        self.SESSION_SALT: str | None = _get_env("SESSION_SALT")
        self.HEARTBEAT_TOKEN: str | None = _get_env("HEARTBEAT_TOKEN")
        self.ALLOWED_HOSTS: list[str] = (
            _get_env("ALLOWED_HOSTS", "localhost,127.0.0.1") or ""
        ).split(",")
        self.SECRET_KEY: str = _get_env("SECRET_KEY") or (
            _DEV_SECRET_KEY if self.ENVIRONMENT != "production" else ""
        )

        # Autonomy Loop Config
        self.AUTONOMY_LOOP_SHADOW_ENABLED: bool = _get_bool_env(
            "AUTONOMY_LOOP_SHADOW_ENABLED",
            "false",
        )
        self.AUTONOMY_LOOP_SHADOW_TIMEOUT_SECONDS: int = _get_int_env(
            "AUTONOMY_LOOP_SHADOW_TIMEOUT_SECONDS",
            "120",
        )
        self.VECTOR_ALPHA_DRY_RUN: bool = _get_bool_env("VECTOR_ALPHA_DRY_RUN", "true")

        # Logging
        self.LOG_LEVEL: str = _get_env(
            "LOG_LEVEL",
            "INFO" if not self.DEBUG else "DEBUG",
        ) or ("INFO" if not self.DEBUG else "DEBUG")
        self.LOG_FORMAT: str = _get_env("LOG_FORMAT", "json") or "json"

        # Rate Limiting
        self.RATE_LIMIT_ENABLED: bool = _get_bool_env("RATE_LIMIT_ENABLED", "true")
        self.RATE_LIMIT_REQUESTS: int = _get_int_env("RATE_LIMIT_REQUESTS", "100")
        self.RATE_LIMIT_PERIOD: int = _get_int_env("RATE_LIMIT_PERIOD", "60")
        self.RATE_LIMIT_PROXY_MODE: bool = _get_bool_env(
            "RATE_LIMIT_PROXY_MODE",
            "false",
        )
        self.RATE_LIMIT_TRUSTED_PROXIES: list[str] = _split_csv_env(
            "RATE_LIMIT_TRUSTED_PROXIES"
        )

        # Redis Config
        self.REDIS_URL: str | None = _get_env("REDIS_URL")
        self.REDIS_HOST: str = _get_env("REDIS_HOST", "localhost") or "localhost"
        self.REDIS_PORT: int = _get_int_env("REDIS_PORT", "6379")

        # Timeouts
        self.REQUEST_TIMEOUT: int = _get_int_env("REQUEST_TIMEOUT", "30")
        self.API_TIMEOUT: int = _get_int_env("API_TIMEOUT", "15")

        # Autonomous Task Configuration
        self.TASK_MAX_RETRIES: int = _get_int_env("TASK_MAX_RETRIES", "3")
        self.TASK_RETRY_DELAY: int = _get_int_env("TASK_RETRY_DELAY", "300")
        self.REPO_ROOT: str = _get_env("REPO_ROOT", ".") or "."
        self.REFERENCE_REPO_ROOT: str | None = _get_env(
            "KORTANA_REFERENCE_REPO_ROOT",
            "KOR-TANA/kortana",
        )
        self.KORTANA_BACKEND_URL: str = (
            _get_env("KORTANA_BACKEND_URL", "http://localhost:8000")
            or "http://localhost:8000"
        )

        # Frontend Dashboard URL
        self.KORTANA_FRONTEND_URL: str = (
            _get_env("KORTANA_FRONTEND_URL", "http://localhost:5173")
            or "http://localhost:5173"
        )

        # Autonomy Configuration
        self.AUTONOMOUS_MODE: bool = _get_bool_env(
            "KORTANA_AUTONOMOUS_MODE",
            "false",
        )
        self.AUTONOMY_CYCLE_INTERVAL: int = _get_int_env(
            "AUTONOMY_CYCLE_INTERVAL",
            "600",
        )

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

        # Use /app/tmp so the kortana non-root user can always write the file.
        # Falls back to relative path on local dev where the cwd is writable.
        import os as _os

        if _os.path.isdir("/app/tmp"):
            return "sqlite+aiosqlite:////app/tmp/kortana.db"
        return "sqlite+aiosqlite:///./kortana.db"

    # Internal Settings
    @property
    def INTERNAL_REDIS_URL(self) -> str:
        """Constructs the Redis URL from settings."""
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

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
            ("OPENAI_API_KEY", ["OPENAI_API_KEY"], "OpenAI API Key"),
        ]
        if settings.KORTANA_GITHUB_MODE == "full":
            critical_keys.append(("GITHUB_TOKEN", ["GITHUB_TOKEN"], "GitHub Token"))
        elif settings.KORTANA_GITHUB_MODE in {"deferred", "disabled"}:
            print(
                "[i] GitHub is running in "
                f"{settings.KORTANA_GITHUB_MODE} mode; local autonomy is primary"
            )
        if settings.DISCORD_ENABLED:
            critical_keys.append(
                ("DISCORD_BOT_TOKEN", ["DISCORD_BOT_TOKEN"], "Discord Bot Token")
            )

        missing = []
        for key, fallbacks, desc in critical_keys:
            # Check if any of the fallback keys are available
            value = None
            for fb_key in fallbacks:
                value = _get_env(fb_key)
                if value and value.strip() != "" and not _is_placeholder(value):
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
            for key, value in self.__dict__.items()
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get settings singleton instance with .env already loaded"""
    return Settings()
