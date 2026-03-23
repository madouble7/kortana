"""
KOR'TANA Intelligence Router

Exposes Self-Awareness, Adaptive Learning, and Goal Management via HTTP.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.kortana.services.adaptive_learner import get_adaptive_learner
from src.kortana.services.goal_manager import GoalTier, get_goal_manager
from src.kortana.services.self_awareness import get_self_awareness

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


# ---------------------------------------------------------------------------
# Self-Awareness
# ---------------------------------------------------------------------------


@router.get("/self-awareness/status")
async def sa_status() -> dict[str, Any]:
    """Current self-awareness engine status (lightweight)."""
    return get_self_awareness().get_status()


@router.get("/self-awareness/assess")
async def sa_assess() -> dict[str, Any]:
    """Full system assessment — snapshot, drift, corrections, capabilities."""
    return await get_self_awareness().assess()


@router.post("/self-awareness/confidence")
async def sa_confidence(decision: dict[str, Any]) -> dict[str, Any]:
    """Score confidence for an autonomous decision."""
    score = await get_self_awareness().confidence(decision)
    return {"confidence": score, "decision": decision}


# ---------------------------------------------------------------------------
# Adaptive Learner
# ---------------------------------------------------------------------------


@router.get("/learner/status")
async def learner_status() -> dict[str, Any]:
    """Current adaptive learner status — scores, insights."""
    learner = await get_adaptive_learner()
    return learner.get_status()


@router.get("/learner/insights")
async def learner_insights() -> dict[str, Any]:
    """Actionable insights derived from learning data."""
    learner = await get_adaptive_learner()
    from dataclasses import asdict

    return {"insights": [asdict(i) for i in learner.generate_insights()]}


@router.get("/learner/best-provider/{task_type}")
async def best_provider(task_type: str) -> dict[str, Any]:
    """Best AI provider for a given task type."""
    learner = await get_adaptive_learner()
    provider = learner.best_provider(task_type)
    return {"task_type": task_type, "best_provider": provider}


# ---------------------------------------------------------------------------
# Goal Manager
# ---------------------------------------------------------------------------


@router.get("/goals/status")
async def goals_status() -> dict[str, Any]:
    """Goal manager overview."""
    return get_goal_manager().get_status()


@router.get("/goals/active")
async def goals_active(tier: str | None = None) -> dict[str, Any]:
    """List active goals, optionally filtered by tier."""
    mgr = get_goal_manager()
    t = GoalTier(tier) if tier else None
    from dataclasses import asdict

    goals = mgr.active(tier=t)
    return {"count": len(goals), "goals": [asdict(g) for g in goals]}


@router.get("/goals/next")
async def goals_next() -> dict[str, Any]:
    """Highest-priority unblocked goal."""
    from dataclasses import asdict

    goal = get_goal_manager().next_goal()
    return {"goal": asdict(goal) if goal else None}


@router.post("/goals")
async def create_goal(body: dict[str, Any]) -> dict[str, Any]:
    """Create a new goal."""
    from dataclasses import asdict

    goal = get_goal_manager().create(**body)
    return {"created": asdict(goal)}


@router.post("/goals/{goal_id}/complete")
async def complete_goal(goal_id: str) -> dict[str, Any]:
    """Mark a goal completed."""
    from dataclasses import asdict

    goal = get_goal_manager().complete(goal_id)
    if not goal:
        return {"error": "Goal not found"}
    return {"completed": asdict(goal)}
