"""
Meta-Coordination Hub API Router
Exposes meta-coordination service for autonomous decision-making across evolution threads
Phase 7 Cycle #5
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from src.kortana.services.meta_coordination_hub import MetaCoordinationHub

router = APIRouter(prefix="/api/orchestration/meta", tags=["meta-coordination"])

# Service instance (shared across requests)
meta_hub = MetaCoordinationHub()


class InitializeEvolutionRequest(BaseModel):
    """Request to initialize a new evolution cycle"""
    focus_areas: List[str]


class MetaStatusResponse(BaseModel):
    """Response with meta-coordination hub status"""
    coordination_id: str
    evolution_state: str
    global_progress: float
    convergence_rate: float
    thread_count: int


@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_evolution_cycle(req: InitializeEvolutionRequest) -> Dict[str, Any]:
    """
    Initialize a new meta-coordination context for parallel evolution.
    
    Args:
        req: InitializeEvolutionRequest with focus areas
        
    Returns:
        Initialized MetaCoordinationContext details
    """
    try:
        context = await meta_hub.initialize_evolution_cycle(req.focus_areas)
        return {
            "coordination_id": context.coordination_id,
            "status": "initialized",
            "threads": len(context.active_threads),
            "state": context.current_state.value,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize: {str(e)}")


@router.post("/synchronize/{coordination_id}", response_model=Dict[str, Any])
async def synchronize_threads(coordination_id: str) -> Dict[str, Any]:
    """
    Synchronize all parallel evolution threads and update global state.
    
    Args:
        coordination_id: ID of the meta-coordination context
        
    Returns:
        Updated evolutionary state
    """
    try:
        new_state = await meta_hub.synchronize_threads(coordination_id)
        return {
            "coordination_id": coordination_id,
            "new_state": new_state.value,
            "synchronized": True,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synchronization failed: {str(e)}")


@router.get("/conflicts/{coordination_id}", response_model=Dict[str, Any])
async def detect_conflicts(coordination_id: str) -> Dict[str, Any]:
    """
    Detect conflicts between parallel evolution threads.
    
    Args:
        coordination_id: ID of the meta-coordination context
        
    Returns:
        Detected conflicts mapping thread pairs to conflict types
    """
    try:
        conflicts = await meta_hub.detect_cross_thread_conflicts(coordination_id)
        return {
            "coordination_id": coordination_id,
            "conflicts_found": len(conflicts),
            "conflict_details": conflicts,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Conflict detection failed: {str(e)}"
        )


@router.post("/resolve/{coordination_id}", response_model=Dict[str, Any])
async def resolve_conflicts(coordination_id: str) -> Dict[str, Any]:
    """
    Enforce the multi-thread consensus protocol: Detect → Resolve → Synchronize.
    
    Args:
        coordination_id: ID of the meta-coordination context
        
    Returns:
        Resolution results and new evolutionary state
    """
    try:
        new_state = await meta_hub.enforce_consensus_protocol(coordination_id)
        return {
            "coordination_id": coordination_id,
            "protocol_enforced": True,
            "final_state": new_state.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resolution failed: {str(e)}")


@router.get("/status/{coordination_id}", response_model=Dict[str, Any])
async def get_meta_status(coordination_id: str) -> Dict[str, Any]:
    """
    Get comprehensive meta-coordination status.
    
    Args:
        coordination_id: ID of the meta-coordination context
        
    Returns:
        Detailed hub status including all threads and dependencies
    """
    try:
        status = await meta_hub.get_meta_status(coordination_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status fetch failed: {str(e)}")


@router.get("/consensus/{coordination_id}", response_model=Dict[str, Any])
async def get_sacred_consensus(coordination_id: str) -> Dict[str, Any]:
    """
    Get the 'Sacred Consensus' for the next evolutionary step.
    
    Args:
        coordination_id: ID of the meta-coordination context
        
    Returns:
        Consensus determination combining all signals
    """
    try:
        consensus = await meta_hub.get_sacred_consensus(coordination_id)
        return consensus
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Consensus failed: {str(e)}")
