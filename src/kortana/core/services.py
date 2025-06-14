"""
Kortana Core Services - Dependency Inverted Architecture

This module provides a clean service locator pattern to break circular dependencies.
It contains ZERO imports from high-level modules like brain.py or goal_engine.py.

All services are lazily initialized to avoid import-time circular dependencies.
"""

import logging
from pathlib import Path
from typing import Any

# Import only LOW-LEVEL dependencies (no brain.py, goal_engine.py, etc.)
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

# Global service registry
_services: dict[str, Any] = {}
_config: Any | None = None


def initialize_services(config) -> None:
    """
    Initialize the service registry with configuration.

    Args:
        config: Application configuration object
    """
    global _config
    _config = config
    logger.info("Service registry initialized with configuration")


def get_service(service_name: str, factory_func=None, *args, **kwargs) -> Any:
    """
    Generic service getter with lazy initialization.

    Args:
        service_name: Name of the service to retrieve
        factory_func: Function to create the service if not exists
        *args, **kwargs: Arguments for factory function

    Returns:
        The requested service instance
    """
    if service_name not in _services:
        if factory_func is None:
            raise RuntimeError(
                f"Service '{service_name}' not initialized and no factory provided"
            )

        logger.info(f"Lazy initializing service: {service_name}")
        try:
            _services[service_name] = factory_func(*args, **kwargs)
            logger.info(f"Service '{service_name}' initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize service '{service_name}': {e}")
            raise RuntimeError(f"Service initialization failed: {service_name}") from e

    return _services[service_name]


def _create_llm_client_factory():
    """Factory function for LLM client factory."""
    from src.kortana.llm_clients.factory import LLMClientFactory

    if _config is None:
        raise RuntimeError("Services not initialized with configuration")

    factory = LLMClientFactory(settings=_config)
    LLMClientFactory.validate_configuration(_config)
    return factory


def _create_enhanced_model_router():
    """Factory function for Enhanced Model Router."""
    from src.kortana.core.enhanced_model_router import EnhancedModelRouter

    if _config is None:
        raise RuntimeError("Services not initialized with configuration")

    return EnhancedModelRouter(settings=_config)


def _create_planning_engine():
    """Factory function for Planning Engine."""
    from src.kortana.core.planning_engine import PlanningEngine

    return PlanningEngine()


def _create_execution_engine():
    """Factory function for Execution Engine."""
    from src.kortana.core.execution_engine import ExecutionEngine

    if _config is None:
        raise RuntimeError("Services not initialized with configuration")

    # Get security settings from config or use defaults
    allowed_dirs = getattr(_config, "allowed_dirs", [str(Path.cwd())])
    blocked_commands = getattr(
        _config, "blocked_commands", ["rm", "del", "format", "sudo"]
    )

    return ExecutionEngine(allowed_dirs=allowed_dirs, blocked_commands=blocked_commands)


def _create_covenant_enforcer():
    """Factory function for Covenant Enforcer."""
    from src.kortana.core.covenant_enforcer import CovenantEnforcer

    if _config is None:
        raise RuntimeError("Services not initialized with configuration")

    return CovenantEnforcer(settings=_config)


def _create_scheduler():
    """Factory function for Background Scheduler."""
    return BackgroundScheduler()


def _create_memory_core_service():
    """Factory function for Memory Core Service."""

    # TODO: This needs proper database session initialization
    # For now, return None as placeholder
    logger.warning(
        "MemoryCoreService factory not fully implemented - needs database session"
    )
    return None


def _create_sacred_model_router():
    """Factory function for Sacred Model Router."""
    try:
        from model_router import SacredModelRouter

        if _config is None:
            raise RuntimeError("Services not initialized with configuration")

        return SacredModelRouter(settings=_config)
    except ImportError:
        logger.warning("SacredModelRouter not found, using stub")

        class SacredModelRouterStub:
            def __init__(self, settings):
                self.settings = settings

        return SacredModelRouterStub(settings=_config)


def _create_chat_engine():
    """Factory function for Chat Engine."""
    try:
        from src.kortana.modules.chat.chat_engine import ChatEngine

        if _config is None:
            raise RuntimeError("Services not initialized with configuration")

        return ChatEngine(settings=_config)
    except ImportError as e:
        logger.warning(f"ChatEngine not found: {e}, using stub")

        class ChatEngineStub:
            def __init__(self, settings):
                self.settings = settings

            def process_message(self, message):
                return "Chat engine not available"

        return ChatEngineStub(settings=_config)


# Service getters with lazy initialization
def get_llm_client_factory():
    """Get the LLM client factory instance."""
    return get_service("llm_client_factory", _create_llm_client_factory)


def get_default_llm_client():
    """Get the default LLM client instance."""
    factory = get_llm_client_factory()
    if _config is None:
        raise RuntimeError("Services not initialized with configuration")
    return factory.get_client(_config.default_llm_id)


def get_ade_llm_client():
    """Get the ADE LLM client instance."""
    factory = get_llm_client_factory()
    if _config is None:
        raise RuntimeError("Services not initialized with configuration")
    return factory.get_client(_config.agents.default_llm_id)


def get_enhanced_model_router():
    """Get the Enhanced Model Router instance."""
    return get_service("enhanced_model_router", _create_enhanced_model_router)


def get_planning_engine():
    """Get the Planning Engine instance."""
    return get_service("planning_engine", _create_planning_engine)


def get_execution_engine():
    """Get the Execution Engine instance."""
    return get_service("execution_engine", _create_execution_engine)


def get_covenant_enforcer():
    """Get the Covenant Enforcer instance."""
    return get_service("covenant_enforcer", _create_covenant_enforcer)


def get_scheduler():
    """Get the Background Scheduler instance."""
    return get_service("scheduler", _create_scheduler)


def get_memory_core_service():
    """Get the Memory Core Service instance."""
    return get_service("memory_core_service", _create_memory_core_service)


def get_sacred_model_router():
    """Get the Sacred Model Router instance."""
    return get_service("sacred_model_router", _create_sacred_model_router)


def get_llm_service():
    """Get the default LLM service/client instance."""
    return get_default_llm_client()


def get_model_router():
    """Get the model router instance (alias for enhanced model router)."""
    return get_enhanced_model_router()


def get_chat_engine():
    """Get the chat engine instance."""
    return get_service("chat_engine", _create_chat_engine)


def reset_services():
    """Reset all services - useful for testing."""
    global _services, _config
    _services.clear()
    _config = None
    logger.info("All services reset")


def get_service_status() -> dict[str, bool]:
    """Get the initialization status of all services."""
    return {
        "llm_client_factory": "llm_client_factory" in _services,
        "enhanced_model_router": "enhanced_model_router" in _services,
        "planning_engine": "planning_engine" in _services,
        "execution_engine": "execution_engine" in _services,
        "covenant_enforcer": "covenant_enforcer" in _services,
        "scheduler": "scheduler" in _services,
        "memory_core_service": "memory_core_service" in _services,
        "sacred_model_router": "sacred_model_router" in _services,
        "chat_engine": "chat_engine" in _services,
        "config_initialized": _config is not None,
    }


def initialize_core_services(config):
    """Initialize core services (alias for initialize_services)."""
    return initialize_services(config)
