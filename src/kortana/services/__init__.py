"""
Database services for Kortana.
"""

# Import specific service functions from the main services module
from ..core.services import (
    get_ade_llm_client,
    get_chat_engine,
    get_covenant_enforcer,
    get_default_llm_client,
    get_enhanced_model_router,
    get_execution_engine,
    get_llm_client_factory,
    get_llm_service,
    get_memory_core_service,
    get_memory_manager,
    get_model_router,
    get_planning_engine,
    get_sacred_model_router,
    get_scheduler,
    get_service,
    get_service_status,
    initialize_core_services,
    initialize_services,
    reset_services,
)
from .database import get_db, get_db_sync

# Explicitly define what's exported
__all__ = [
    # Core services
    "initialize_services",
    "initialize_core_services",
    "get_service",
    "reset_services",
    "get_service_status",
    # LLM services
    "get_llm_client_factory",
    "get_default_llm_client",
    "get_ade_llm_client",
    "get_llm_service",
    # Model routing
    "get_enhanced_model_router",
    "get_model_router",
    "get_sacred_model_router",
    # Core engines
    "get_planning_engine",
    "get_execution_engine",
    "get_covenant_enforcer",
    "get_scheduler",
    # Memory services
    "get_memory_core_service",
    "get_memory_manager",
    # Chat engine
    "get_chat_engine",
    # Database
    "get_db",
    "get_db_sync",
]
