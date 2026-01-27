"""
Centralized service instances for Kortana core modules.

This module provides singleton instances of core services like LLM clients,
memory managers, planning engine, and execution engine to break circular
dependencies.
"""

import logging
from pathlib import Path
from typing import Any

# Import necessary service classes
from apscheduler.schedulers.background import BackgroundScheduler

from kortana.config.schema import KortanaConfig
from kortana.core.brain import ChatEngine
from kortana.core.covenant_enforcer import CovenantEnforcer
from kortana.core.enhanced_model_router import EnhancedModelRouter
from kortana.core.execution_engine import ExecutionEngine
from kortana.core.planning_engine import PlanningEngine
from kortana.llm_clients.factory import LLMClientFactory
from kortana.modules.memory_core.services import MemoryCoreService

# Assuming SacredModelRouter path is correct, adjust if needed
try:
    from model_router import SacredModelRouter
except ImportError:
    # Provide a stub or handle the missing import appropriately
    class SacredModelRouter:
        def __init__(self, settings):
            logging.warning("SacredModelRouter not found, using stub.")
            self.settings = settings

# Placeholder for service instances
_llm_client_factory: LLMClientFactory | None = None
_default_llm_client: Any | None = None # Use Any for now, specific type can be refined
_ade_llm_client: Any | None = None # Use Any for now
_memory_core_service: MemoryCoreService | None = None
_planning_engine: PlanningEngine | None = None
_execution_engine: ExecutionEngine | None = None
_scheduler: BackgroundScheduler | None = None
_sacred_model_router: SacredModelRouter | None = None
_enhanced_model_router: EnhancedModelRouter | None = None
_covenant_enforcer: CovenantEnforcer | None = None
_chat_engine: ChatEngine | None = None

logger = logging.getLogger(__name__)

def initialize_core_services(config: KortanaConfig):
    """Initializes all core singleton services."""
    global _llm_client_factory, _default_llm_client, _ade_llm_client, \
           _memory_core_service, _planning_engine, _execution_engine, \
           _scheduler, _sacred_model_router, _enhanced_model_router, _covenant_enforcer, _chat_engine

    logger.info("Initializing core services...")

    # Initialize LLM clients
    _llm_client_factory = LLMClientFactory(settings=config)
    LLMClientFactory.validate_configuration(config)
    _default_llm_client = _llm_client_factory.get_client(config.default_llm_id)
    _ade_llm_client = _llm_client_factory.get_client(config.agents.default_llm_id)
    logger.info("LLM clients initialized.")

    # Initialize Routers and Enforcer first as they might be dependencies
    try:
        _sacred_model_router = SacredModelRouter(settings=config) # Assuming settings is needed
        logger.info("SacredModelRouter initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize SacredModelRouter: {e}")
        _sacred_model_router = None

    try:
        _enhanced_model_router = EnhancedModelRouter(settings=config) # Assuming settings is needed
        logger.info("EnhancedModelRouter initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize EnhancedModelRouter: {e}")
        _enhanced_model_router = None

    try:
        _covenant_enforcer = CovenantEnforcer(settings=config) # Assuming settings is needed
        logger.info("CovenantEnforcer initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize CovenantEnforcer: {e}")
        _covenant_enforcer = None

    # Initialize memory service (assuming MemoryCoreService is the main one)
    # Note: MemoryCoreService might need a database session or other dependencies    # This initialization might need adjustment based on its actual constructor
    try:
        # MemoryCoreService requires a database session, placeholder for now
        _memory_core_service = None  # Placeholder until database is properly initialized
        logger.info("MemoryCoreService placeholder set (needs database session).")
    except Exception as e:
        logger.error(f"Failed to initialize MemoryCoreService: {e}")
        _memory_core_service = None

    # Initialize Planning Engine (no parameters required)
    try:
        _planning_engine = PlanningEngine()
        logger.info("PlanningEngine initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize PlanningEngine: {e}")
        _planning_engine = None

    # Initialize Execution Engine (needs allowed_dirs and blocked_commands)
    try:
        # Get security settings from config or use defaults
        allowed_dirs = getattr(config, 'allowed_dirs', [str(Path.cwd())])
        blocked_commands = getattr(config, 'blocked_commands', ['rm', 'del', 'format', 'sudo'])
        _execution_engine = ExecutionEngine(allowed_dirs=allowed_dirs, blocked_commands=blocked_commands)
        logger.info("ExecutionEngine initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize ExecutionEngine: {e}")
        _execution_engine = None

    # Initialize ChatEngine
    try:
        _chat_engine = ChatEngine(config)
        logger.info("ChatEngine initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize ChatEngine: {e}")
        _chat_engine = None

    # Initialize Scheduler
    _scheduler = BackgroundScheduler()
    logger.info("Scheduler initialized.")

    logger.info("Core services initialization complete.")

def get_llm_client_factory() -> LLMClientFactory:
    """Gets the initialized LLM client factory."""
    if _llm_client_factory is None:
        raise RuntimeError("Core services not initialized. Call initialize_core_services first.")
    return _llm_client_factory

def get_default_llm_client() -> Any:
    """Gets the default LLM client instance."""
    if _default_llm_client is None:
        raise RuntimeError("Core services not initialized. Call initialize_core_services first.")
    return _default_llm_client

def get_ade_llm_client() -> Any:
    """Gets the ADE LLM client instance."""
    if _ade_llm_client is None:
        raise RuntimeError("Core services not initialized. Call initialize_core_services first.")
    return _ade_llm_client

def get_memory_core_service() -> MemoryCoreService:
    """Gets the MemoryCoreService instance."""
    if _memory_core_service is None:
        # Depending on whether MemoryCoreService is essential, you might raise an error
        # or return None and handle it in the caller.
        # For now, let's raise an error if it failed to initialize.
         raise RuntimeError("MemoryCoreService not initialized.")
    return _memory_core_service

def get_planning_engine() -> PlanningEngine:
    """Gets the PlanningEngine instance."""
    if _planning_engine is None:
         raise RuntimeError("PlanningEngine not initialized.")
    return _planning_engine

def get_execution_engine() -> ExecutionEngine:
    """Gets the ExecutionEngine instance."""
    if _execution_engine is None:
         raise RuntimeError("ExecutionEngine not initialized.")
    return _execution_engine

def get_scheduler() -> BackgroundScheduler:
    """Gets the BackgroundScheduler instance."""
    if _scheduler is None:
         raise RuntimeError("Scheduler not initialized.")
    return _scheduler

def get_sacred_model_router() -> SacredModelRouter:
    """Gets the SacredModelRouter instance."""
    if _sacred_model_router is None:
         raise RuntimeError("SacredModelRouter not initialized.")
    return _sacred_model_router

def get_enhanced_model_router() -> EnhancedModelRouter:
    """Gets the EnhancedModelRouter instance."""
    if _enhanced_model_router is None:
         raise RuntimeError("EnhancedModelRouter not initialized.")
    return _enhanced_model_router

def get_covenant_enforcer() -> CovenantEnforcer:
    """Gets the CovenantEnforcer instance.""" # Added missing getter
    if _covenant_enforcer is None:
         raise RuntimeError("CovenantEnforcer not initialized.")
    return _covenant_enforcer

def get_chat_engine() -> ChatEngine:
    """Gets the ChatEngine instance."""
    if _chat_engine is None:
        raise RuntimeError("ChatEngine not initialized.")
    return _chat_engine
