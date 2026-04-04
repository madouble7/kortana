import platform
from dataclasses import asdict
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]
from fastapi import APIRouter, HTTPException

router = APIRouter()


def _build_model_entry(model_name: str) -> dict[str, Any]:
    """Return lane-aware metadata for a chat-capable model."""
    from src.kortana.model_lane_policy import describe_model_lane, model_allowed

    return {
        "model": model_name,
        "lane": describe_model_lane(model_name),
        "allowed": model_allowed(model_name),
    }


def _build_provider_defaults_catalog(defaults: Any) -> dict[str, dict[str, Any]]:
    """Serialize provider defaults into lane-aware catalog entries."""
    return {
        provider_name: _build_model_entry(model_name)
        for provider_name, model_name in asdict(defaults).items()
        if model_name
    }


@router.get("/logs")
async def get_logs(lines: int = 100) -> dict[str, Any]:
    """Get the last N lines of the autonomy log."""
    # Assuming log is in project root
    log_path = Path("AUTONOMY_EXECUTION.log")
    if not log_path.exists():
        # Try backend folder
        log_path = Path("backend/AUTONOMY_EXECUTION.log")

    if not log_path.exists():
        return {"logs": [], "message": "Log file not found"}

    try:
        with log_path.open("r", encoding="utf-8", errors="replace") as f:
            content = f.readlines()
            return {"logs": content[-lines:]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_system_info() -> dict[str, Any]:
    """Get basic system usage info."""
    return {
        "os": platform.system(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "python_version": platform.python_version(),
    }


@router.get("/settings")
async def get_settings_info() -> dict[str, Any]:
    """Get non-sensitive settings."""
    from src.kortana.config import get_settings

    settings = get_settings()
    return {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "version": "3.0.0-ecosystem",
    }


@router.get("/model-lanes")
async def get_model_lane_summary() -> dict[str, Any]:
    """Return a compact summary of model lane posture across active subsystems."""
    from src.kortana.cost_optimized_model_router import CostOptimizedModelRouter
    from src.kortana.llm_router import get_llm_router
    from src.kortana.model_lane_policy import describe_model_lane, get_active_model_lane
    from src.kortana.model_usage_telemetry import get_model_usage_telemetry
    from src.kortana.provider_model_defaults import (
        AI_CONSENSUS_DEFAULTS,
        API_INTEGRATION_FALLBACK_DEFAULTS,
        COST_ROUTER_DEFAULTS,
        DEFAULT_CORE_MODEL_CATALOG,
        GEMINI_DISCOVERY_FALLBACK_MODELS,
        GEMINI_EMBEDDING_FALLBACK_MODEL_PATH,
        GEMINI_EMBEDDING_MODEL_NAME,
        GEMINI_EMBEDDING_MODEL_PATH,
        LLM_ROUTER_DEFAULTS,
        MEMORY_ENGINE_EMBEDDING_MODEL,
        MULTI_MODEL_DEFAULTS,
    )
    from src.kortana.services.ai_consensus import get_consensus_engine
    from src.kortana.services.gemini import gemini_service

    llm_router = get_llm_router()
    consensus_status = get_consensus_engine().get_status()
    cost_router = CostOptimizedModelRouter()
    runtime_usage = get_model_usage_telemetry().get_summary()
    active_lane = get_active_model_lane().value
    catalogs = {
        "chat_models": {
            "known_core_catalog": [
                _build_model_entry(model_name)
                for model_name in sorted(DEFAULT_CORE_MODEL_CATALOG)
            ],
            "gemini_discovery_fallbacks": [
                _build_model_entry(model_name)
                for model_name in GEMINI_DISCOVERY_FALLBACK_MODELS
            ],
            "subsystem_defaults": {
                "llm_router": _build_provider_defaults_catalog(LLM_ROUTER_DEFAULTS),
                "ai_consensus": _build_provider_defaults_catalog(
                    AI_CONSENSUS_DEFAULTS
                ),
                "multi_model": _build_provider_defaults_catalog(MULTI_MODEL_DEFAULTS),
                "cost_router": _build_provider_defaults_catalog(COST_ROUTER_DEFAULTS),
                "api_integration": _build_provider_defaults_catalog(
                    API_INTEGRATION_FALLBACK_DEFAULTS
                ),
                "gemini_service": _build_model_entry(gemini_service.model_name),
            },
        },
        "embedding_models": {
            "memory_engine": {
                "model": MEMORY_ENGINE_EMBEDDING_MODEL,
                "lane_controlled": False,
            },
            "gemini_service": {
                "primary_model": GEMINI_EMBEDDING_MODEL_NAME,
                "primary_path": GEMINI_EMBEDDING_MODEL_PATH,
                "fallback_path": GEMINI_EMBEDDING_FALLBACK_MODEL_PATH,
                "lane_controlled": False,
            },
        },
    }

    return {
        "active_lane": active_lane,
        "gemini_service": {
            "model": gemini_service.model_name,
            "lane": describe_model_lane(gemini_service.model_name),
        },
        "catalogs": catalogs,
        "runtime_usage": runtime_usage,
        "llm_router": llm_router.get_model_info(),
        "consensus": {
            "model_usage_lane": consensus_status.get("model_usage_lane"),
            "providers": consensus_status.get("providers", {}),
            "ranking": consensus_status.get("ranking", []),
            "total_providers": consensus_status.get("total_providers", 0),
        },
        "cost_router": {
            "routing": cost_router.get_routing_strategy(),
            "cost": cost_router.get_cost_report(),
        },
    }
