"""
Kortana Configuration Module
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from config file.

    Args:
        config_path: Optional path to config file. If None, uses default config.yaml

    Returns:
        Dict containing configuration
    """
    if config_path is None:
        config_path = os.path.join(get_project_root(), "config.yaml")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        return {}


def get_config(key: str = None, config_path: Optional[str] = None) -> Any:
    """
    Get a specific configuration value or the entire config.

    Args:
        key: Config key to retrieve. If None, returns entire config
        config_path: Optional path to config file

    Returns:
        Configuration value or entire config dict
    """
    config = load_config(config_path)

    if key is None:
        return config

    return config.get(key, None)


def get_api_key(provider: str = "openai") -> str:
    """
    Get API key for specified provider.

    Args:
        provider: Service provider name (openai, google, etc.)

    Returns:
        API key as string
    """
    # First check environment variables
    env_var_name = f"{provider.upper()}_API_KEY"
    api_key = os.environ.get(env_var_name)

    # If not in environment, check config file
    if not api_key:
        config = load_config()
        api_keys = config.get("api_keys", {})
        api_key = api_keys.get(provider)

    return api_key
