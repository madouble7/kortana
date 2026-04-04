"""Persist lightweight OpenAI conversation state across chat turns."""

from __future__ import annotations

from sqlalchemy import select

from src.kortana.database import get_db_manager
from src.kortana.models import AuditLog

_OPENAI_RESPONSE_STATE_ACTION = "openai_response_state"
_RESOURCE_TYPE = "conversation_session"
_MAX_LOOKBACK = 20


async def get_previous_response_id(session_id: str) -> str | None:
    """Return the most recent persisted OpenAI response id for a session."""
    if not session_id.strip():
        return None

    async with get_db_manager().session_scope() as session:
        result = await session.execute(
            select(AuditLog)
            .where(AuditLog.action == _OPENAI_RESPONSE_STATE_ACTION)
            .where(AuditLog.resource_type == _RESOURCE_TYPE)
            .where(AuditLog.resource_id == session_id)
            .order_by(AuditLog.created_at.desc())
            .limit(_MAX_LOOKBACK)
        )
        logs = list(result.scalars().all())

    for log in logs:
        raw_details = log.details
        details: dict[str, object] = raw_details if isinstance(raw_details, dict) else {}
        if details.get("provider") != "openai":
            continue
        response_id = details.get("response_id")
        if response_id:
            return str(response_id)
        return None

    return None


async def store_response_id(
    session_id: str,
    response_id: str,
    *,
    model_name: str,
    route: str,
) -> None:
    """Persist the latest OpenAI response id for a chat session."""
    if not session_id.strip() or not response_id.strip():
        return

    async with get_db_manager().session_scope() as session:
        session.add(
            AuditLog(
                action=_OPENAI_RESPONSE_STATE_ACTION,
                resource_type=_RESOURCE_TYPE,
                resource_id=session_id,
                details={
                    "provider": "openai",
                    "response_id": response_id,
                    "model": model_name,
                    "route": route,
                },
            )
        )


async def clear_response_id(
    session_id: str,
    *,
    route: str,
    reason: str,
) -> None:
    """Explicitly clear any persisted OpenAI response id for a chat session."""
    if not session_id.strip():
        return

    async with get_db_manager().session_scope() as session:
        session.add(
            AuditLog(
                action=_OPENAI_RESPONSE_STATE_ACTION,
                resource_type=_RESOURCE_TYPE,
                resource_id=session_id,
                details={
                    "provider": "openai",
                    "response_id": None,
                    "route": route,
                    "reason": reason,
                    "cleared": True,
                },
            )
        )
