"""
Configuration Schema for Project Kor'tana
Pydantic-based configuration validation and management
"""

from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator
import os


class AppConfig(BaseModel):
    """Application-level configuration"""
    name: str = "Project Kor'tana"
    version: str = "1.0.0"
    environment: str = Field(default="development", regex="^(development|staging|production)$")
    debug: bool = True


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    console_enabled: bool = True
    max_file_size: str = "10MB"
    backup_count: int = Field(default=5, ge=1, le=20)


class APIConfig(BaseModel):
    """API server configuration"""
    host: str = "localhost"
    port: int = Field(default=8000, ge=1024, le=65535)
    timeout: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    rate_limit: int = Field(default=100, ge=1)


class ModelProviderConfig(BaseModel):
    """Individual model provider configuration"""
    model: str
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    cost_per_1k_input: float = Field(default=0.0, ge=0.0)
    cost_per_1k_output: float = Field(default=0.0, ge=0.0)


class ModelsConfig(BaseModel):
    """Model configuration"""
    default_provider: str = "openai"
    cost_optimization: bool = True
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    providers: Dict[str, ModelProviderConfig] = {}


class MemoryConfig(BaseModel):
    """Memory management configuration"""
    max_entries: int = Field(default=10000, ge=100)
    cleanup_interval: int = Field(default=3600, ge=60)
    compression_enabled: bool = True
    backup_enabled: bool = True


class AgentTypeConfig(BaseModel):
    """Individual agent type configuration"""
    enabled: bool = True
    max_tasks: int = Field(default=10, ge=1, le=100)


class AgentsConfig(BaseModel):
    """Agent system configuration"""
    max_concurrent: int = Field(default=5, ge=1, le=20)
    default_timeout: int = Field(default=300, ge=30, le=3600)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    types: Dict[str, AgentTypeConfig] = {}


class DevelopmentConfig(BaseModel):
    """Development settings"""
    auto_reload: bool = True
    debug_mode: bool = True
    test_mode: bool = False
    mock_apis: bool = False


class SecurityConfig(BaseModel):
    """Security configuration"""
    token_expiry: int = Field(default=3600, ge=300, le=86400)
    max_login_attempts: int = Field(default=5, ge=1, le=20)
    session_timeout: int = Field(default=1800, ge=300, le=86400)


class DatabaseConfig(BaseModel):
    """Database configuration"""
    type: str = Field(default="sqlite", regex="^(sqlite|postgresql|mysql)$")
    name: str = "kortana.db"
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    backup_enabled: bool = True
    backup_interval: int = Field(default=86400, ge=3600)


class MonitoringConfig(BaseModel):
    """Monitoring configuration"""
    enabled: bool = True
    metrics_interval: int = Field(default=60, ge=10, le=3600)
    health_check_interval: int = Field(default=30, ge=5, le=300)
    external_service: bool = False
    metrics_endpoint: Optional[str] = None


class PathsConfig(BaseModel):
    """File paths configuration"""
    data_dir: str = "data"
    logs_dir: str = "logs"
    models_dir: str = "models"
    config_dir: str = "config"
    temp_dir: str = "tmp"


class APIKeysConfig(BaseModel):
    """API keys configuration (for production)"""
    openai: Optional[str] = None
    google: Optional[str] = None
    openrouter: Optional[str] = None
    xai: Optional[str] = None
    anthropic: Optional[str] = None
    pinecone: Optional[str] = None


class KortanaConfig(BaseModel):
    """Main configuration schema for Project Kor'tana"""

    app: AppConfig = AppConfig()
    logging: LoggingConfig = LoggingConfig()
    api: APIConfig = APIConfig()
    models: ModelsConfig = ModelsConfig()
    memory: MemoryConfig = MemoryConfig()
    agents: AgentsConfig = AgentsConfig()
    development: DevelopmentConfig = DevelopmentConfig()
    security: SecurityConfig = SecurityConfig()
    database: DatabaseConfig = DatabaseConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    paths: PathsConfig = PathsConfig()
    api_keys: Optional[APIKeysConfig] = None

    # Allow additional configuration sections
    class Config:
        extra = "allow"

    @validator('paths')
    def validate_paths(cls, v):
        """Ensure all paths exist or can be created"""
        paths = v if isinstance(v, PathsConfig) else PathsConfig(**v)
        for path_name, path_value in paths.dict().items():
            path = Path(path_value)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise ValueError(f"Cannot create path {path_value} for {path_name}: {e}")
        return paths

    @validator('api_keys', pre=True, always=True)
    def resolve_environment_variables(cls, v):
        """Resolve environment variables in API keys"""
        if not v:
            return v

        if isinstance(v, dict):
            resolved = {}
            for key, value in v.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    resolved[key] = os.getenv(env_var)
                else:
                    resolved[key] = value
            return APIKeysConfig(**resolved)
        return v

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider"""
        if not self.api_keys:
            return None
        return getattr(self.api_keys, provider, None)

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.app.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.app.environment == "development"
