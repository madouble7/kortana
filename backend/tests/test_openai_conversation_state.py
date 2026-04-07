from __future__ import annotations

from unittest.mock import patch

import pytest


class _ExplodingScope:
    async def __aenter__(self):
        raise RuntimeError("db unavailable")

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _ExplodingDbManager:
    def session_scope(self):
        return _ExplodingScope()


@pytest.mark.asyncio
async def test_get_previous_response_id_returns_none_when_db_unavailable() -> None:
    from src.kortana.openai_conversation_state import get_previous_response_id

    with patch(
        "src.kortana.openai_conversation_state.get_db_manager",
        return_value=_ExplodingDbManager(),
    ):
        assert await get_previous_response_id("sess_live") is None


@pytest.mark.asyncio
async def test_store_response_id_is_best_effort_when_db_unavailable() -> None:
    from src.kortana.openai_conversation_state import store_response_id

    with patch(
        "src.kortana.openai_conversation_state.get_db_manager",
        return_value=_ExplodingDbManager(),
    ):
        await store_response_id(
            "sess_live",
            "resp_123",
            model_name="gpt-5.4-mini",
            route="test_route",
        )


@pytest.mark.asyncio
async def test_clear_response_id_is_best_effort_when_db_unavailable() -> None:
    from src.kortana.openai_conversation_state import clear_response_id

    with patch(
        "src.kortana.openai_conversation_state.get_db_manager",
        return_value=_ExplodingDbManager(),
    ):
        await clear_response_id(
            "sess_live",
            route="test_route",
            reason="test_reason",
        )
