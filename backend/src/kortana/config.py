from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GITHUB_PAT: str
    GITHUB_REQUIRED_SCOPES: list[str] = ["repo", "workflow", "write:packages"]
    DEBUG: bool = False

settings = Settings()