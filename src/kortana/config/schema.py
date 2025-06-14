"""
Kortana Configuration Schema

This module defines the Pydantic models for Kortana's configuration system.
Provides type-safe configuration management with validation.
"""

from pydantic import BaseModel, Field


class AgentTypeConfig(BaseModel):
    """Configuration for a specific agent type."""

    enabled: bool = Field(
        default=True, description="Whether this agent type is enabled"
    )
    llm_id: str | None = Field(
        default=None, description="Override LLM ID for this agent type"
    )


class AgentsConfig(BaseModel):
    """Configuration for autonomous agents."""

    default_llm_id: str = Field(
        default="gpt-4.1-nano", description="Default LLM for agents"
    )
    max_concurrent_agents: int = Field(
        default=5, description="Maximum concurrent agents"
    )
    types: dict[str, AgentTypeConfig] = Field(
        default_factory=dict, description="Agent type configurations"
    )


class MemoryConfig(BaseModel):
    """Configuration for memory systems."""

    pinecone_api_key: str | None = Field(default=None, description="Pinecone API key")
    pinecone_environment: str | None = Field(
        default=None, description="Pinecone environment"
    )
    pinecone_index_name: str = Field(
        default="kortana-memory", description="Pinecone index name"
    )
    pinecone_namespace: str = Field(
        default="{user}",
        description="Pinecone namespace template. {user} will be replaced with username",
    )
    local_memory_path: str = Field(
        default="data/project_memory.jsonl", description="Local memory file path"
    )
    max_memory_entries: int = Field(default=10000, description="Maximum memory entries")
    memory_cleanup_interval: int = Field(
        default=3600, description="Memory cleanup interval in seconds"
    )


class PersonaConfig(BaseModel):
    """Configuration for Kortana's persona."""

    name: str = Field(default="Kor'tana", description="Persona name")
    voice_style: str = Field(default="presence", description="Default voice style")
    temperature: float = Field(
        default=0.7, description="Default temperature for responses"
    )
    max_tokens: int = Field(default=4000, description="Maximum tokens per response")
    wisdom_weight: float = Field(
        default=0.33, description="Weight for wisdom principle"
    )
    compassion_weight: float = Field(
        default=0.33, description="Weight for compassion principle"
    )
    truth_weight: float = Field(default=0.34, description="Weight for truth principle")


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
    models_config_file_path: str = Field(
        default="config/models_config.json",
        description="Path to LLM models configuration file",
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


class KortanaConfig(BaseModel):
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    persona: PersonaConfig = Field(default_factory=PersonaConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    default_llm_id: str = Field(
        default="openai/gpt-4.1-nano", description="Default LLM model ID"
    )
    models: dict = Field(default_factory=dict, description="LLM models config")
