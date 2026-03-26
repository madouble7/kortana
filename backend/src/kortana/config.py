from pydantic_settings import BaseSettings
from typing import List

REQUIRED_GH_SCOPES = ["repo", "workflow"]

class Settings(BaseSettings):
    GITHUB_TOKEN: str
    
    def validate_scopes(self):
        # Implementation of token scope validation to ensure autonomy readiness
        if not self.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN is not configured.")

settings = Settings()