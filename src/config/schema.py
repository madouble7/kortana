"""
Kortana Configuration Schema

This module defines the Pydantic models for Kortana's configuration system.
Provides type-safe configuration management with validation.
"""

import os

from pydantic import BaseModel, Field, field_validator


class AgentTypeConfig(BaseModel):
    """Configuration for a specific agent type."""

    # Changed from 'model_mapping' to 'agent_model_mapping' to avoid Pydantic protected namespace
    agent_model_mapping: dict[str, str] = Field(
        default_factory=dict, description="Model mapping for this agent type"
    )
    enabled: bool = Field(
        default=True, description="Whether this agent type is enabled"
    )
    max_concurrent: int = Field(default=1, description="Maximum concurrent instances")
    timeout_seconds: int = Field(
        default=300, description="Timeout for agent operations"
    )
    llm_model: str | None = Field(
        default=None, description="Default LLM model for this agent"
    )

    class Config:
        extra = "allow"  # Allow additional fields for flexibility


class AgentsConfig(BaseModel):
    """Configuration for autonomous agents."""

    default_llm_id: str = Field(
        default="gpt-4.1-nano", description="Default LLM for agents"
    )
    max_concurrent_agents: int = Field(
        default=5, description="Maximum concurrent agents"
    )

    # Agent type configurations
    types: dict[str, AgentTypeConfig] = Field(
        default_factory=dict, description="Agent type configurations"
    )

    class Config:
        extra = "allow"


class MemoryConfig(BaseModel):
    """Configuration for memory systems."""

    # Pinecone settings
    pinecone_api_key: str | None = Field(default=None, description="Pinecone API key")
    pinecone_environment: str | None = Field(
        default=None, description="Pinecone environment"
    )
    pinecone_index_name: str = Field(
        default="kortana-memory", description="Pinecone index name"
    )

    # Local memory settings
    local_memory_path: str = Field(
        default="data/project_memory.jsonl", description="Local memory file path"
    )
    max_memory_entries: int = Field(default=10000, description="Maximum memory entries")
    memory_cleanup_interval: int = Field(
        default=3600, description="Memory cleanup interval in seconds"
    )

    class Config:
        extra = "allow"


class PersonaConfig(BaseModel):
    """Configuration for Kortana's persona."""

    name: str = Field(default="Kor'tana", description="Persona name")
    voice_style: str = Field(default="presence", description="Default voice style")
    temperature: float = Field(
        default=0.7, description="Default temperature for responses"
    )
    max_tokens: int = Field(default=4000, description="Maximum tokens per response")

    # Sacred Trinity principles
    wisdom_weight: float = Field(
        default=0.33, description="Weight for wisdom principle"
    )
    compassion_weight: float = Field(
        default=0.33, description="Weight for compassion principle"
    )
    truth_weight: float = Field(default=0.34, description="Weight for truth principle")

    class Config:
        extra = "allow"


class LLMConfig(BaseModel):
    """Configuration for LLM clients."""

    default_model: str = Field(default="gpt-4.1-nano", description="Default model ID")
    fallback_model: str = Field(
        default="gpt-4o-mini", description="Fallback model if default fails"
    )

    # Rate limiting
    requests_per_minute: int = Field(
        default=60, description="Requests per minute limit"
    )
    tokens_per_minute: int = Field(default=40000, description="Tokens per minute limit")

    # Timeout settings
    request_timeout: int = Field(default=60, description="Request timeout in seconds")
    connection_timeout: int = Field(
        default=30, description="Connection timeout in seconds"
    )

    class Config:
        extra = "allow"


class CovenantConfig(BaseModel):
    """Configuration for covenant enforcement."""

    enabled: bool = Field(
        default=True, description="Whether covenant enforcement is enabled"
    )
    strict_mode: bool = Field(
        default=False, description="Strict covenant enforcement mode"
    )
    violation_threshold: float = Field(
        default=0.8, description="Threshold for covenant violations"
    )

    # Sacred principles
    sacred_principles: list[str] = Field(
        default=["wisdom", "compassion", "truth"], description="Core sacred principles"
    )

    class Config:
        extra = "allow"


class PathsConfig(BaseModel):
    """Configuration for file system paths."""

    # Core configuration files
    persona_file_path: str = Field(
        default="config/persona.json", description="Path to persona configuration file"
    )
    identity_file_path: str = Field(
        default="config/identity.json",
        description="Path to identity configuration file",
    )
    covenant_file_path: str = Field(
        default="covenant.yaml",
        description="Path to covenant configuration file",
    )

    # Memory system paths with user templating
    memory_journal_path: str = Field(
        default="data/memory/{user}/memory_journal.jsonl",
        description="Path to memory journal file. {user} will be replaced with username",
    )
    heart_log_path: str = Field(
        default="data/memory/{user}/heart_log.jsonl",
        description="Path to heart memory log. {user} will be replaced with username",
    )
    soul_index_path: str = Field(
        default="data/memory/{user}/soul_index.jsonl",
        description="Path to soul index file. {user} will be replaced with username",
    )
    lit_log_path: str = Field(
        default="data/memory/{user}/lit_log.jsonl",
        description="Path to lit log file. {user} will be replaced with username",
    )
    project_memory_file_path: str = Field(
        default="data/memory/{user}/project_memory.jsonl",
        description="Path to project memory file. {user} will be replaced with username",
    )

    # Directory paths
    config: str = Field(default="config", description="Configuration directory")
    data: str = Field(default="data", description="Data directory")
    logs: str = Field(default="logs", description="Logs directory")
    models: str = Field(default="models", description="Models directory")

    def get_user_paths(self, user_name: str) -> dict[str, str]:
        """Get all memory paths with user name substituted.

        Args:
            user_name: The username to substitute into path templates.

        Returns:
            Dictionary of path names to concrete paths with username substituted.
        """
        memory_paths = {
            "memory_journal_path": self.memory_journal_path,
            "heart_log_path": self.heart_log_path,
            "soul_index_path": self.soul_index_path,
            "lit_log_path": self.lit_log_path,
            "project_memory_file_path": self.project_memory_file_path,
        }
        return {k: v.format(user=user_name) for k, v in memory_paths.items()}


class ApiKeysConfig(BaseModel):
    """Configuration for API keys."""

    openai: str | None = Field(default=None, description="OpenAI API key")
    # Add other API keys as needed

    class Config:
        extra = "allow"


class KortanaConfig(BaseModel):
    """Main Kortana configuration model."""  # Core settings

    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(
        default="development", description="Environment (development/production)"
    )
    default_llm_id: str = Field(
        default="gpt-4.1-nano", description="Default LLM model ID"
    )  # Component configurations
    agents: AgentsConfig = Field(
        default_factory=AgentsConfig, description="Agents configuration"
    )
    memory: MemoryConfig = Field(
        default_factory=MemoryConfig, description="Memory configuration"
    )
    persona: PersonaConfig = Field(
        default_factory=PersonaConfig, description="Persona configuration"
    )
    paths: PathsConfig = Field(
        default_factory=PathsConfig, description="File system paths configuration"
    )
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM configuration")
    covenant: CovenantConfig = Field(
        default_factory=CovenantConfig, description="Covenant configuration"
    )
    api_keys: ApiKeysConfig = Field(
        default_factory=ApiKeysConfig, description="API keys configuration"
    ) # Added api_keys

    # API settings
    api_host: str = Field(default="localhost", description="API host")
    api_port: int = Field(default=8000, description="API port")  # File paths
    config_dir: str = Field(default="config", description="Configuration directory")
    data_dir: str = Field(default="data", description="Data directory")
    logs_dir: str = Field(default="logs", description="Logs directory")

    def get_api_key(self, provider: str) -> str | None:
        """Get API key for a specific provider."""
        if hasattr(self.api_keys, provider):
            return getattr(self.api_keys, provider)
        return None

    @field_validator("log_level", mode="after")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper() @ field_validator("environment", mode="after")

    @classmethod
    def validate_environment(cls, v):
        valid_environments = ["development", "testing", "production"]
        if v.lower() not in valid_environments:
            raise ValueError(f"environment must be one of {valid_environments}")
        return v.lower()

    class Config:
        extra = "allow"  # Allow additional fields for flexibility
        validate_assignment = True


def load_config_from_env() -> KortanaConfig:
    """Load configuration with environment variable overrides."""
    # Start with default configuration
    config = KortanaConfig()

    # Override with environment variables
    debug_env = os.getenv("KORTANA_DEBUG")
    if debug_env is not None:
        config.debug = debug_env.lower() == "true"

    log_level_env = os.getenv("KORTANA_LOG_LEVEL")
    if log_level_env is not None:
        config.log_level = log_level_env

    environment_env = os.getenv("KORTANA_ENVIRONMENT")
    if environment_env is not None:
        config.environment = environment_env

    # Memory configuration from environment
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")

    if pinecone_api_key is not None or pinecone_environment is not None:
        # Update memory config
        memory_updates: dict[str, Any] = {}
        if pinecone_api_key is not None:
            memory_updates["pinecone_api_key"] = pinecone_api_key
        if pinecone_environment is not None:
            memory_updates["pinecone_environment"] = pinecone_environment

        # Create new memory config with updates
        # Use model_dump() for Pydantic v2, or dict() for Pydantic v1
        try:
            # Attempt Pydantic v2 model_dump()
            current_memory_data = config.memory.model_dump()
        except AttributeError:
            # Fallback to Pydantic v1 dict()
            current_memory_data = config.memory.dict()

        config.memory = MemoryConfig(**{**current_memory_data, **memory_updates})

    # Add overrides for other configs as needed
    # Example for LLMConfig:
    default_llm_model_env = os.getenv("KORTANA_DEFAULT_LLM_MODEL")
    if default_llm_model_env is not None:
         try:
            current_llm_data = config.llm.model_dump()
         except AttributeError:
            current_llm_data = config.llm.dict()
         config.llm = LLMConfig(**{**current_llm_data, "default_model": default_llm_model_env})


    return config


def create_default_config() -> KortanaConfig:
    """Create a default configuration instance."""
    return KortanaConfig()


# Export for convenience
__all__ = [
    "KortanaConfig",
    "AgentsConfig",
    "AgentTypeConfig",
    "MemoryConfig",
    "PersonaConfig",
    "LLMConfig",
    "CovenantConfig",
    "PathsConfig", # Added PathsConfig to __all__
    "ApiKeysConfig", # Added ApiKeysConfig to __all__
    "load_config_from_env",
    "create_default_config",
]
