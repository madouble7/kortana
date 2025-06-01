"""
Configuration loading utility for Project Kor'tana
Centralized configuration management with environment-based overrides
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Union
from functools import lru_cache

from .schema import KortanaConfig


def _load_yaml_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML configuration file"""
    path = Path(file_path)
    if not path.exists():
        return {}

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f) or {}
        return content
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {file_path}: {e}")
    except Exception as e:
        raise ValueError(f"Cannot read config file {file_path}: {e}")


def _merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two configuration dictionaries"""
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def _resolve_extends(config: Dict[str, Any], config_dir: Path) -> Dict[str, Any]:
    """Resolve 'extends' directive in configuration"""
    if 'extends' not in config:
        return config

    extends_file = config.pop('extends')
    base_config = _load_yaml_file(config_dir / extends_file)

    # Recursively resolve extends in base config
    base_config = _resolve_extends(base_config, config_dir)

    # Merge current config over base config
    return _merge_configs(base_config, config)


@lru_cache(maxsize=1)
def load_config(
    config_name: Optional[str] = None,
    config_dir: Optional[Union[str, Path]] = None,
    env_override: bool = True
) -> KortanaConfig:
    """
    Load and validate configuration for Project Kor'tana

    Args:
        config_name: Name of config file (without .yaml extension).
                    Defaults to environment-specific config or 'default'
        config_dir: Directory containing config files. Defaults to './config'
        env_override: Whether to allow environment variable overrides

    Returns:
        Validated KortanaConfig instance

    Environment Variables:
        KORTANA_CONFIG: Override config file name
        KORTANA_CONFIG_DIR: Override config directory
        KORTANA_ENV: Set environment (development/staging/production)
    """

    # Determine config directory
    if config_dir is None:
        config_dir = Path(os.getenv('KORTANA_CONFIG_DIR', 'config'))
    else:
        config_dir = Path(config_dir)

    if not config_dir.exists():
        raise ValueError(f"Config directory does not exist: {config_dir}")

    # Determine config file name
    if config_name is None:
        config_name = os.getenv('KORTANA_CONFIG')

    if config_name is None:
        # Use environment-specific config if available
        env = os.getenv('KORTANA_ENV', 'development')
        env_config_file = config_dir / f"{env}.yaml"
        if env_config_file.exists():
            config_name = env
        else:
            config_name = 'default'

    config_file = config_dir / f"{config_name}.yaml"

    # Load base configuration
    config_data = _load_yaml_file(config_file)

    # Resolve extends directive
    config_data = _resolve_extends(config_data, config_dir)

    # Apply environment variable overrides if enabled
    if env_override:
        # Override environment if KORTANA_ENV is set
        kortana_env = os.getenv('KORTANA_ENV')
        if kortana_env:
            if 'app' not in config_data:
                config_data['app'] = {}
            config_data['app']['environment'] = kortana_env

    # Validate and create config object
    try:
        return KortanaConfig(**config_data)
    except Exception as e:
        raise ValueError(f"Invalid configuration in {config_file}: {e}")


def get_config() -> KortanaConfig:
    """Get the current configuration instance (cached)"""
    return load_config()


def reload_config() -> KortanaConfig:
    """Reload configuration (clears cache)"""
    load_config.cache_clear()
    return load_config()


def create_config_file(
    config_name: str,
    config_data: Dict[str, Any],
    config_dir: Optional[Union[str, Path]] = None,
    overwrite: bool = False
) -> Path:
    """
    Create a new configuration file

    Args:
        config_name: Name of config file (without .yaml extension)
        config_data: Configuration data to write
        config_dir: Directory to write config file. Defaults to './config'
        overwrite: Whether to overwrite existing file

    Returns:
        Path to created config file
    """
    if config_dir is None:
        config_dir = Path('config')
    else:
        config_dir = Path(config_dir)

    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / f"{config_name}.yaml"

    if config_file.exists() and not overwrite:
        raise ValueError(f"Config file already exists: {config_file}")

    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f, default_flow_style=False, indent=2)
    except Exception as e:
        raise ValueError(f"Cannot write config file {config_file}: {e}")

    return config_file


# Convenience functions for common operations
def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a specific provider"""
    config = get_config()
    return config.get_api_key(provider)


def is_production() -> bool:
    """Check if running in production environment"""
    config = get_config()
    return config.is_production()


def is_development() -> bool:
    """Check if running in development environment"""
    config = get_config()
    return config.is_development()


def get_database_url() -> str:
    """Get database connection URL"""
    config = get_config()
    db = config.database

    if db.type == "sqlite":
        return f"sqlite:///{db.name}"
    elif db.type == "postgresql":
        return f"postgresql://{db.user}:{db.password}@{db.host}:{db.port}/{db.name}"
    elif db.type == "mysql":
        return f"mysql://{db.user}:{db.password}@{db.host}:{db.port}/{db.name}"
    else:
        raise ValueError(f"Unsupported database type: {db.type}")
