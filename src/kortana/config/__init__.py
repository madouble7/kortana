"""
Kortana Configuration Package

This package contains configuration schemas and utilities for the Kortana system.
"""

import os
from pathlib import Path
from typing import Any

import yaml

from .schema import (
    AgentsConfig,
    AgentTypeConfig,
    KortanaConfig,
    MemoryConfig,
    PathsConfig,
    PersonaConfig,
)


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent.parent


def load_config(config_path: str | None = None) -> dict:
    """
    Load configuration from config file.

    Args:
        config_path: Optional path to config file. If None, uses default config.yaml

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = os.path.join(get_project_root(), "config.yaml")

    try:
        # First try to load from file
        if os.path.exists(config_path):
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
            return config_data
        else:
            # If no config file, use environment variables and defaults
            print(
                f"Config file not found at {config_path}, using environment variables and defaults"
            )
            return {}
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        print("Using default configuration")
        return {}


def get_config(key: str | None = None, config_path: str | None = None) -> Any:
    """
    Get a specific configuration value or the entire config.

    Args:
        key: Config key to retrieve. If None, returns entire config
        config_path: Optional path to config file

    Returns:
        Configuration value or entire config dictionary
    """
    config = load_config(config_path)

    if key is None:
        return config

    # Access attribute on the configuration dictionary
    return config.get(key, None)


def get_api_key(service: str) -> str | None:
    """
    Get API key for a specific service from environment variables.

    Args:
        service: Service name (e.g., 'openai', 'pinecone')

    Returns:
        API key if found, None otherwise
    """
    key_map = {
        "openai": "OPENAI_API_KEY",
        "pinecone": "PINECONE_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "xai": "XAI_API_KEY",
    }

    env_var = key_map.get(service.lower())
    if env_var:
        return os.getenv(env_var)

    # Try direct lookup
    return os.getenv(f"{service.upper()}_API_KEY")


__all__ = [
    "AgentsConfig",
    "AgentTypeConfig",
    "MemoryConfig",
    "PersonaConfig",
    "PathsConfig",
    "KortanaConfig",
    "get_project_root",
]
