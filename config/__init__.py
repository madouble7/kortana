"""
Configuration Module

This module provides functions for loading and managing the application configuration.
"""

import os
from pathlib import Path

import yaml

from .schema import KortanaConfig


def load_config() -> KortanaConfig:
    """
    Load configuration from YAML files and environment variables.

    Returns:
        The application configuration.
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config"

    # Default configuration file
    default_yaml = config_dir / "default.yaml"

    # Load default configuration
    with open(default_yaml, "r") as f:
        config_dict = yaml.safe_load(f)

    # Check for environment-specific configuration
    env = os.getenv("KORTANA_ENV", "development")
    env_yaml = config_dir / f"{env}.yaml"

    if env_yaml.exists():
        print(f"Loading environment configuration: {env_yaml}")
        with open(env_yaml, "r") as f:
            env_dict = yaml.safe_load(f)
            # Update configuration with environment-specific values
            _update_dict(config_dict, env_dict)

    # Override with environment variables
    _apply_env_overrides(config_dict)

    # Create Pydantic model
    config = KortanaConfig(**config_dict)

    return config


def _update_dict(base_dict, update_dict):
    """
    Update a nested dictionary with values from another dictionary.

    Args:
        base_dict: The dictionary to update.
        update_dict: The dictionary with new values.
    """
    for key, value in update_dict.items():
        if (
            isinstance(value, dict)
            and key in base_dict
            and isinstance(base_dict[key], dict)
        ):
            _update_dict(base_dict[key], value)
        else:
            base_dict[key] = value


def _apply_env_overrides(config_dict):
    """
    Apply environment variable overrides to the configuration.

    Args:
        config_dict: The configuration dictionary to update.
    """
    # Example: KORTANA_API_HOST -> config_dict["api"]["host"]
    for env_key, env_value in os.environ.items():
        if env_key.startswith("KORTANA_"):
            # Remove prefix and convert to lowercase
            key_path = env_key[8:].lower()

            # If a path is provided, use it
            if key_path == "config_dir":
                continue

            # Split by underscore to get nested keys
            keys = key_path.split("_")

            # Navigate to the correct nested dictionary
            current = config_dict
            for key in keys[:-1]:
                if key not in current or not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]

            # Set the value
            try:
                # Try to convert to appropriate type
                if env_value.lower() in ["true", "yes", "1"]:
                    current[keys[-1]] = True
                elif env_value.lower() in ["false", "no", "0"]:
                    current[keys[-1]] = False
                elif env_value.isdigit():
                    current[keys[-1]] = int(env_value)
                elif (
                    env_value.replace(".", "", 1).isdigit()
                    and env_value.count(".") == 1
                ):
                    current[keys[-1]] = float(env_value)
                else:
                    current[keys[-1]] = env_value
            except Exception:
                # Default to string if conversion fails
                current[keys[-1]] = env_value
