from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "kortana"
    LOG_LEVEL: str = "INFO"
    MEMORY_DB_URL: str = Field(
        "sqlite:///./kortana_memory_dev.db", validation_alias="MEMORY_DB_URL"
    )
    OPENAI_API_KEY: str | None = Field(None, validation_alias="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = Field(None, validation_alias="ANTHROPIC_API_KEY")
    DEFAULT_GREETING: str = "hello from kor'tana"

    # Execution Engine Permissions for Autonomous Operations
    EXECUTION_ALLOWED_DIRS: list[str] = [
        r"c:\project-kortana\src",
        r"c:\project-kortana\tests",
        r"c:\project-kortana\docs",
        r"c:\project-kortana\data",
        r"c:\project-kortana",
    ]
    EXECUTION_BLOCKED_COMMANDS: list[str] = [
        "rm",
        "del",
        "rmdir",
        "rd",  # File deletion
        "sudo",
        "runas",  # Privilege escalation
        "format",
        "fdisk",  # Disk operations
        "net",
        "netsh",  # Network changes
        "reg",
        "regedit",  # Registry changes
        "shutdown",
        "restart",  # System control
        "taskkill",  # Process killing
        "git push",
        "git pull",  # Version control (for safety)
    ]

    @property
    def ALEMBIC_DATABASE_URL(self) -> str:
        # Alembic needs a plain URL, handle potential async prefix if MEMORY_DB_URL might have it
        # For now, assuming MEMORY_DB_URL is sync. If it can be async, more logic is needed here.
        # Example: return self.MEMORY_DB_URL.replace("postgresql+asyncpg", "postgresql")
        return self.MEMORY_DB_URL


settings = AppSettings()

# For testing purposes, you can add this:
if __name__ == "__main__":
    print("--- Loaded AppSettings ---")
    print(f"App Name: {settings.APP_NAME}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print(f"Memory DB URL: {settings.MEMORY_DB_URL}")
    print(f"Alembic DB URL: {settings.ALEMBIC_DATABASE_URL}")
    print(f"OpenAI API Key: {'Set' if settings.OPENAI_API_KEY else 'Not Set'}")
    print(f"Anthropic API Key: {'Set' if settings.ANTHROPIC_API_KEY else 'Not Set'}")
    print(f"Default Greeting: {settings.DEFAULT_GREETING}")
    print("--------------------------")
