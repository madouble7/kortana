import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    REQUIRED_SCOPES: list[str] = ["repo", "workflow"]

    def validate_github_environment(self):
        if not self.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN not configured.")

settings = Settings()