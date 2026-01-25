"""
Configuration management for Kor'tana Backend
Handles environment-specific settings and validation
Loads secrets from .env file and environment variables
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load .env file at module import time
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback to checking parent directory
    parent_env = Path(__file__).parent.parent / ".env"
    if parent_env.exists():
        load_dotenv(parent_env)


class Settings:
    """Application settings loaded from environment variables"""

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))

    # API Configuration
    API_TITLE: str = "Kor'tana Backend"
    API_VERSION: str = "0.1.0"
    API_DESCRIPTION: str = "Autonomous AI constellation API"

    # CORS Configuration
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
    ).split(",")
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: list = ["*"]

    # AI & LLM Providers
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: str | None = os.getenv("GOOGLE_API_KEY")
    GOOGLE_PROJECT_ID: str = os.getenv("GOOGLE_PROJECT_ID", "")
    OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
    # Gemini uses GEMINI_API_KEY or falls back to GOOGLE_API_KEY
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")

    # Vector Database
    PINECONE_API_KEY: str | None = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")

    # Google Integration
    GOOGLE_DRIVE_API_KEY: str = os.getenv("GOOGLE_DRIVE_API_KEY", "")
    GOOGLE_CLIENT_ID: str | None = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str | None = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:3000/oauth/callback"
    )
    GOOGLE_REFRESH_TOKEN: str | None = os.getenv("GOOGLE_REFRESH_TOKEN")
    GOOGLE_APPLICATION_CREDENTIALS: str | None = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # GitHub Integration
    GITHUB_TOKEN: str | None = os.getenv("GITHUB_TOKEN")
    GITHUB_OWNER: str = os.getenv("GITHUB_OWNER", "KOR-TANA")
    GITHUB_REPO: str = os.getenv("GITHUB_REPO", "kortana")

    # Discord Integration
    DISCORD_BOT_TOKEN: str | None = os.getenv("DISCORD_BOT_TOKEN")
    DISCORD_CLIENT_ID: str | None = os.getenv("CLIENT_ID")

    # Twilio Integration
    TWILIO_ACCOUNT_SID: str | None = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str | None = os.getenv("TWILIO_AUTH_TOKEN")

    # Stripe Payment
    STRIPE_SECRET_KEY: str | None = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: str | None = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: str | None = os.getenv("STRIPE_WEBHOOK_SECRET")

    # AWS Integration
    AWS_ACCESS_KEY_ID: str | None = os.getenv("AWS_BACKUP_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str | None = os.getenv("AWS_BACKUP_SECRET_ACCESS_KEY")

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_NAME: str = os.getenv("DB_NAME", "kortana")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "supersecretpassword")
    DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Security
    SESSION_SALT: str | None = os.getenv("SESSION_SALT")
    HEARTBEAT_TOKEN: str | None = os.getenv("HEARTBEAT_TOKEN")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")

    # Security
    ALLOWED_HOSTS: list = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

    # Timeouts
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "15"))

    @classmethod
    def validate(cls) -> None:
        """Validate required settings on startup"""
        # First, ensure .env is loaded
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=False)

        # Core secrets that should always be present
        # Note: Some keys have fallbacks (e.g., GEMINI uses GOOGLE_API_KEY)
        critical_keys = [
            ("GEMINI_API_KEY", ["GEMINI_API_KEY", "GOOGLE_API_KEY"], "Gemini/Google API"),
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
            print("⚠️  Warning: Missing critical API keys:")
            for item in missing:
                print(f"   - {item}")
            if cls.ENVIRONMENT == "production":
                raise ValueError(
                    f"Missing required environment variables in production: {', '.join([m.split()[0] for m in missing])}"
                )
        else:
            print("✅ All critical API keys validated and loaded")

        # Validate database connection string
        try:
            db_url = cls.DATABASE_URL
            if not db_url or "supersecretpassword" in db_url:
                print("⚠️  Warning: Database password is using default value")
        except Exception as e:
            print(f"⚠️  Warning: Database configuration issue: {e}")

    def to_dict(self) -> dict:
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
