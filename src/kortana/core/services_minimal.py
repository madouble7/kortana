"""
Minimal centralized service instances for breaking circular dependencies.
This version only includes the most essential services.
"""

import logging

# Only import what we absolutely need
from kortana.config.schema import KortanaConfig

# Placeholder for service instances
_config: KortanaConfig | None = None

logger = logging.getLogger(__name__)


def initialize_core_services(config: KortanaConfig):
    """Initialize minimal core services."""
    global _config
    _config = config
    logger.info("Minimal core services initialized.")


def get_config() -> KortanaConfig:
    """Get the initialized config."""
    if _config is None:
        raise RuntimeError(
            "Core services not initialized. Call initialize_core_services first."
        )
    return _config


# For now, let's use simple placeholder classes to avoid import issues
class PlaceholderChatEngine:
    def __init__(self, config):
        self.config = config
        print("Placeholder ChatEngine initialized.")


class PlaceholderCovenantEnforcer:
    def __init__(self, config):
        self.config = config
        print("Placeholder CovenantEnforcer initialized.")


def get_chat_engine() -> PlaceholderChatEngine:
    """Get a placeholder chat engine."""
    if _config is None:
        raise RuntimeError("Core services not initialized.")
    return PlaceholderChatEngine(_config)


def get_covenant_enforcer() -> PlaceholderCovenantEnforcer:
    """Get a placeholder covenant enforcer."""
    if _config is None:
        raise RuntimeError("Core services not initialized.")
    return PlaceholderCovenantEnforcer(_config)
