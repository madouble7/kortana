from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GITHUB_PAT: str
    GITHUB_REQUIRED_SCOPES: list[str] = ["repo", "workflow"]
    ALWAYS_ON_ENABLED: bool = True

settings = Settings()