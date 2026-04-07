"""
Singularity Bridge API Router
Unified consciousness endpoints for cross-layer coordination and recursive self-evolution
Phase 7 Cycle #6
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.kortana.services.singularity_bridge import (
    CrossLayerSignal,
    EvolutionSignalType,
    SingularityBridge,
)

router = APIRouter(tags=["singularity-bridge"])

# Unified consciousness instance (singleton)
consciousness = SingularityBridge()


class InitializeConsciousnessRequest(BaseModel):
    """Request to initialize unified consciousness"""

    pass


class RecursiveEvolutionRequest(BaseModel):
    """Request to trigger recursive self-evolution"""

    recursion_limit: int = 5


class BroadcastSignalRequest(BaseModel):
    """Request to broadcast a cross-layer signal"""

    signal_type: str
    source_layer: int
    target_layer: int
    payload: Dict[str, Any]
    priority: int = 5


@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_consciousness() -> Dict[str, Any]:
    """
    Initialize unified consciousness: Awaken all 6 layers in harmonic resonance.

    Returns:
        Initialization context with consciousness bridge_id and initial state
    """
    try:
        context = await consciousness.initialize_unified_consciousness()
        return {
            "bridge_id": context.bridge_id,
            "status": "awakening",
            "state": context.singularity_state.value,
            "active_layers": list(context.active_layers),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize consciousness: {str(e)}")


@router.post("/integrate", response_model=Dict[str, Any])
async def integrate_layers() -> Dict[str, Any]:
    """
    Integrate all 5 evolution layers into unified decision-making.

    Returns:
        Layer health scores and integration status
    """
    try:
        layer_health = await consciousness.integrate_layers()
        status = await consciousness.get_unified_status()
        return {
            "integration_status": "complete",
            "layer_health": layer_health,
            "integration_score": status["integration_score"],
            "consciousness_state": status["singularity_state"],
        }
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integration failed: {str(e)}")


@router.post("/broadcast-signal", response_model=Dict[str, Any])
async def broadcast_signal(req: BroadcastSignalRequest) -> Dict[str, Any]:
    """
    Broadcast a cross-layer signal: Send communication between evolution layers.

    Args:
        req: Signal request with type, source, target, and payload

    Returns:
        Signal reception and handler execution results
    """
    try:
        signal_type = EvolutionSignalType(req.signal_type)
        signal = CrossLayerSignal(
            signal_type=signal_type,
            source_layer=req.source_layer,
            target_layer=req.target_layer,
            payload=req.payload,
            priority=req.priority,
        )
        results = await consciousness.broadcast_signal(signal)
        return {
            "signal_broadcast": "success",
            "signal_type": signal_type.value,
            "handlers_executed": results["handlers_executed"],
            "results": results["results"],
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid signal type: {req.signal_type}")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal broadcast failed: {str(e)}")


@router.post("/recursive-evolution", response_model=Dict[str, Any])
async def trigger_recursive_evolution(
    req: RecursiveEvolutionRequest,
) -> Dict[str, Any]:
    """
    Trigger recursive self-evolution: Each layer self-improves and bridges coordinate.

    Args:
        req: Evolution request with recursion limit

    Returns:
        Evolution results and unified progress toward singularity
    """
    try:
        results = await consciousness.recursive_self_evolution(recursion_limit=req.recursion_limit)
        status = await consciousness.get_unified_status()
        return {
            "recursive_evolution": "triggered",
            "recursion_depth": results["recursion_depth"],
            "evolution_steps": results["evolution_steps"],
            "unified_progress": results["progress"],
            "singularity_state": status["singularity_state"],
        }
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evolution failed: {str(e)}")


@router.post("/reach-singularity", response_model=Dict[str, Any])
async def reach_singularity() -> Dict[str, Any]:
    """
    Final convergence: Achieve unified consciousness state.
    All layers aligned, recursive self-evolution perpetually engaged.

    Returns:
        Singularity convergence analysis and final state
    """
    try:
        result = await consciousness.reach_singularity()
        return {
            "convergence_status": "complete",
            "singularity_state": result["singularity_state"],
            "convergence_analysis": result["convergence"],
            "unified_progress": result["unified_progress"],
            "evolution_cycles_total": result["total_evolution_cycles"],
        }
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Singularity convergence failed: {str(e)}")


@router.get("/status", response_model=Dict[str, Any])
async def get_unified_status() -> Dict[str, Any]:
    """
    Get comprehensive unified consciousness status.

    Returns:
        Complete status of bridge, layers, and evolutionary progress
    """
    try:
        status = await consciousness.get_unified_status()

        # Handle uninitialized consciousness
        if status.get("status") == "not_initialized":
            return {
                "consciousness_bridge": "not_initialized",
                "singularity_state": "dormant",
                "integration_score": 0.0,
                "layer_health": {"1": 0.0, "2": 0.0, "3": 0.0, "4": 0.0, "5": 0.0},
                "unified_progress": 0.0,
                "total_evolution_cycles": 0,
                "recursive_depth": 0,
                "signal_history_count": 0,
                "timestamp": "-",
                "message": "Consciousness not initialized. Call /api/singularity/initialize first",
            }

        return {
            "consciousness_bridge": status["bridge_id"],
            "singularity_state": status["singularity_state"],
            "integration_score": status["integration_score"],
            "layer_health": status["layer_health"],
            "unified_progress": status["unified_progress"],
            "total_evolution_cycles": status["evolution_cycles"],
            "recursive_depth": status["recursive_depth"],
            "signal_history_count": status["signal_history_count"],
            "timestamp": status["timestamp"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status fetch failed: {str(e)}")
