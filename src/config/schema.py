"""
Kortana Configuration Schema

This module defines the Pydantic models for Kortana's configuration system.
Provides type-safe configuration management with validation.
"""

import os
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class AgentTypeConfig(BaseModel):
    """Configuration for a specific agent type."""

    # Changed from 'model_mapping' to 'agent_model_mapping' to avoid Pydantic protected namespace
    agent_model_mapping: Dict[str, str] = Field(
        default_factory=dict, description="Model mapping for this agent type"
    )
    enabled: bool = Field(
        default=True, description="Whether this agent type is enabled"
    )
    max_concurrent: int = Field(default=1, description="Maximum concurrent instances")
    timeout_seconds: int = Field(
        default=300, description="Timeout for agent operations"
    )
    llm_model: Optional[str] = Field(
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
    types: Dict[str, AgentTypeConfig] = Field(
        default_factory=dict, description="Agent type configurations"
    )

    class Config:
        extra = "allow"


class MemoryConfig(BaseModel):
    """Configuration for memory systems."""

    # Pinecone settings
    pinecone_api_key: Optional[str] = Field(
        default=None, description="Pinecone API key"
    )
    pinecone_environment: Optional[str] = Field(
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
    sacred_principles: List[str] = Field(
        default=["wisdom", "compassion", "truth"], description="Core sacred principles"
    )

    class Config:
        extra = "allow"


class KortanaConfig(BaseModel):
    """Main Kortana configuration model."""

    # Core settings
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(
        default="development", description="Environment (development/production)"
    )

    # Component configurations
    agents: AgentsConfig = Field(
        default_factory=AgentsConfig, description="Agents configuration"
    )
    memory: MemoryConfig = Field(
        default_factory=MemoryConfig, description="Memory configuration"
    )
    persona: PersonaConfig = Field(
        default_factory=PersonaConfig, description="Persona configuration"
    )
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM configuration")
    covenant: CovenantConfig = Field(
        default_factory=CovenantConfig, description="Covenant configuration"
    )

    # API settings
    api_host: str = Field(default="localhost", description="API host")
    api_port: int = Field(default=8000, description="API port")

    # File paths
    config_dir: str = Field(default="config", description="Configuration directory")
    data_dir: str = Field(default="data", description="Data directory")
    logs_dir: str = Field(default="logs", description="Logs directory")

    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @validator("environment")
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

    # Start with defaults
    config_data = {}

    # Override with environment variables
    if os.getenv("KORTANA_DEBUG"):
        config_data["debug"] = os.getenv("KORTANA_DEBUG").lower() == "true"

    if os.getenv("KORTANA_LOG_LEVEL"):
        config_data["log_level"] = os.getenv("KORTANA_LOG_LEVEL")

    if os.getenv("KORTANA_ENVIRONMENT"):
        config_data["environment"] = os.getenv("KORTANA_ENVIRONMENT")

    # Memory configuration from environment
    memory_config = {}
    if os.getenv("PINECONE_API_KEY"):
        memory_config["pinecone_api_key"] = os.getenv("PINECONE_API_KEY")
    if os.getenv("PINECONE_ENVIRONMENT"):
        memory_config["pinecone_environment"] = os.getenv("PINECONE_ENVIRONMENT")

    if memory_config:
        config_data["memory"] = memory_config

    return KortanaConfig(**config_data)


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
    "load_config_from_env",
    "create_default_config",
]
