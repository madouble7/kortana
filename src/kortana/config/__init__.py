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
    KortanaConfig,  # Ensure KortanaConfig is imported
    MemoryConfig,
    PathsConfig,
    PersonaConfig,
)


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent.parent


def load_config(config_path: str | None = None) -> KortanaConfig:  # Changed return type
    """
    Load configuration from config file and parse into KortanaConfig object.

    Args:
        config_path: Optional path to config file. If None, uses default config.yaml

    Returns:
        KortanaConfig object
    """
    if config_path is None:
        # Assuming get_project_root() correctly points to c:\\project-kortana
        config_path_obj = get_project_root() / "config.yaml"
        config_path = str(config_path_obj)

    config_data = {}
    try:
        if os.path.exists(config_path):
            with open(config_path, encoding="utf-8") as f:
                loaded_yaml = yaml.safe_load(f)
                if loaded_yaml is not None:
                    config_data = loaded_yaml
                else:
                    print(
                        f"Warning: Config file at {config_path} is empty or invalid YAML. Using defaults."
                    )
        else:
            print(
                f"Config file not found at {config_path}, using default KortanaConfig values."
            )

        # Parse the dictionary into KortanaConfig object
        # If config_data is empty, this will use default_factory for nested models
        return KortanaConfig(**config_data)

    except yaml.YAMLError as e:
        print(f"Error parsing YAML from {config_path}: {e}")
        print("Using default KortanaConfig due to YAML parsing error.")
        return KortanaConfig()  # Return default config on YAML error
    except Exception as e:
        print(f"Error loading or parsing config from {config_path}: {e}")
        print("Using default KortanaConfig due to an unexpected error.")
        return KortanaConfig()  # Return default config on other errors


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
