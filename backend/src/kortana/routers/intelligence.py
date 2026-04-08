"""
KOR'TANA Intelligence Router

Exposes Self-Awareness, Adaptive Learning, and Goal Management via HTTP.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from src.kortana.auth import TokenData, get_current_active_user
from src.kortana.services.adaptive_learner import get_adaptive_learner
from src.kortana.services.autonomy_controller import get_autonomy_controller
from src.kortana.services.gmail_service import (
    GmailAPIError,
    GmailConfigurationError,
    get_gmail_service,
)
from src.kortana.services.goal_manager import GoalTier, get_goal_manager
from src.kortana.services.self_awareness import get_self_awareness

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


class GmailSendRequest(BaseModel):
    """Request body for outbound Gmail messages."""

    to: EmailStr
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)
    cc: list[EmailStr] = Field(default_factory=list)
    bcc: list[EmailStr] = Field(default_factory=list)
    thread_id: str | None = None
    in_reply_to: str | None = None


def _raise_gmail_http_error(exc: Exception) -> None:
    """Convert Gmail integration errors into FastAPI HTTP responses."""
    if isinstance(exc, GmailConfigurationError):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if isinstance(exc, GmailAPIError):
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    raise exc


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


@router.get("/self-model")
async def self_model() -> dict[str, Any]:
    """Return the latest operational self-model, reflecting if needed."""
    controller = get_autonomy_controller()
    status = controller.get_status()
    if status["last_reflection"] is None:
        return await controller.reflect()
    return status["last_reflection"]


@router.get("/controller/status")
async def controller_status() -> dict[str, Any]:
    """Current closed-loop autonomy controller status."""
    return get_autonomy_controller().get_status()


@router.post("/controller/reflect")
async def controller_reflect() -> dict[str, Any]:
    """Force a fresh reflection and control recommendation."""
    return await get_autonomy_controller().reflect()


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
    mgr = get_goal_manager()
    await mgr.ensure_loaded()
    return mgr.get_status()


@router.get("/goals/active")
async def goals_active(tier: str | None = None) -> dict[str, Any]:
    """List active goals, optionally filtered by tier."""
    mgr = get_goal_manager()
    await mgr.ensure_loaded()
    t = GoalTier(tier) if tier else None
    from dataclasses import asdict

    goals = mgr.active(tier=t)
    return {"count": len(goals), "goals": [asdict(g) for g in goals]}


@router.get("/goals/next")
async def goals_next() -> dict[str, Any]:
    """Highest-priority unblocked goal."""
    from dataclasses import asdict

    mgr = get_goal_manager()
    await mgr.ensure_loaded()
    goal = mgr.next_goal()
    return {"goal": asdict(goal) if goal else None}


@router.post("/goals")
async def create_goal(body: dict[str, Any]) -> dict[str, Any]:
    """Create a new goal."""
    from dataclasses import asdict

    mgr = get_goal_manager()
    await mgr.ensure_loaded()
    goal = mgr.create(**body)
    await mgr.persist_goal(goal)
    return {"created": asdict(goal)}


@router.post("/goals/{goal_id}/complete")
async def complete_goal(goal_id: str) -> dict[str, Any]:
    """Mark a goal completed."""
    from dataclasses import asdict

    mgr = get_goal_manager()
    await mgr.ensure_loaded()
    goal = mgr.complete(goal_id)
    if not goal:
        return {"error": "Goal not found"}
    # complete() may cascade to parent goals — persist the full graph
    await mgr.persist_all_goals()
    return {"completed": asdict(goal)}


# ---------------------------------------------------------------------------
# Gmail autonomy
# ---------------------------------------------------------------------------


@router.get("/email/status")
async def gmail_status(
    _current_user: TokenData = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Return Gmail integration readiness and live profile status."""
    del _current_user
    return await get_gmail_service().get_status()


@router.get("/email/messages")
async def gmail_messages(
    limit: int = Query(default=10, ge=1, le=25),
    query: str = Query(default="in:inbox"),
    _current_user: TokenData = Depends(get_current_active_user),
) -> dict[str, Any]:
    """List recent Gmail messages for autonomous triage."""
    del _current_user
    try:
        return await get_gmail_service().list_messages(limit=limit, query=query)
    except Exception as exc:
        _raise_gmail_http_error(exc)


@router.get("/email/messages/{message_id}")
async def gmail_message_detail(
    message_id: str,
    _current_user: TokenData = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Fetch a full Gmail message body and metadata."""
    del _current_user
    try:
        return await get_gmail_service().get_message(message_id)
    except Exception as exc:
        _raise_gmail_http_error(exc)


@router.post("/email/messages/{message_id}/archive")
async def gmail_archive_message(
    message_id: str,
    _current_user: TokenData = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Archive a Gmail message by removing it from the inbox."""
    del _current_user
    try:
        return await get_gmail_service().archive_message(message_id)
    except Exception as exc:
        _raise_gmail_http_error(exc)


@router.post("/email/messages/{message_id}/read")
async def gmail_mark_read(
    message_id: str,
    _current_user: TokenData = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Mark a Gmail message as read."""
    del _current_user
    try:
        return await get_gmail_service().mark_message_read(message_id)
    except Exception as exc:
        _raise_gmail_http_error(exc)


@router.post("/email/send")
async def gmail_send(
    body: GmailSendRequest,
    _current_user: TokenData = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Send an outbound Gmail message from the connected account."""
    del _current_user
    try:
        return await get_gmail_service().send_message(
            to=str(body.to),
            subject=body.subject,
            body=body.body,
            cc=[str(item) for item in body.cc],
            bcc=[str(item) for item in body.bcc],
            thread_id=body.thread_id,
            in_reply_to=body.in_reply_to,
        )
    except Exception as exc:
        _raise_gmail_http_error(exc)
