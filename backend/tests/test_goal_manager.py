"""Tests for DB-backed GoalManager persistence."""

from __future__ import annotations

import pytest
from sqlalchemy import delete

from src.kortana.database import get_db_manager
from src.kortana.models import AutonomyGoal
from src.kortana.services.goal_manager import (
    GoalManager,
    GoalTier,
    get_goal_manager,
    reset_goal_manager_for_testing,
)


async def _ensure_db_and_clear_goals() -> None:
    db = get_db_manager()
    await db.initialize()
    async with db.session_scope() as session:
        await session.execute(delete(AutonomyGoal))


@pytest.fixture(autouse=True)
def _reset_goal_singleton():
    reset_goal_manager_for_testing()
    yield
    reset_goal_manager_for_testing()


@pytest.mark.asyncio
async def test_load_from_db_bootstraps_defaults_when_empty() -> None:
    await _ensure_db_and_clear_goals()
    gm = get_goal_manager()
    await gm.load_from_db()
    st = gm.get_status()
    assert st["total_goals"] >= 3
    assert any(t["tier"] == "strategic" for t in st["top_3"])


@pytest.mark.asyncio
async def test_goals_survive_restart_singleton() -> None:
    await _ensure_db_and_clear_goals()
    gm = get_goal_manager()
    await gm.load_from_db()
    n0 = gm.get_status()["total_goals"]
    titles0 = sorted(g.title for g in gm.all())

    reset_goal_manager_for_testing()
    gm2 = get_goal_manager()
    await gm2.load_from_db()
    assert gm2.get_status()["total_goals"] == n0
    assert sorted(g.title for g in gm2.all()) == titles0


@pytest.mark.asyncio
async def test_persist_and_reload_custom_goal() -> None:
    await _ensure_db_and_clear_goals()
    gm = get_goal_manager()
    await gm.load_from_db()
    g = gm.create(
        title="Custom persistence test goal",
        tier=GoalTier.IMMEDIATE,
        description="verify sqlite roundtrip",
        priority=42,
    )
    await gm.persist_goal(g)

    reset_goal_manager_for_testing()
    gm2 = get_goal_manager()
    await gm2.load_from_db()
    found = gm2.get(g.id)
    assert found is not None
    assert found.title == "Custom persistence test goal"
    assert found.priority == 42


@pytest.mark.asyncio
async def test_normalize_goal_kwargs_accepts_string_enums() -> None:
    mgr = GoalManager()
    g = mgr.create(tier="tactical", status="active", title="enum strings")
    assert g.tier == GoalTier.TACTICAL
    assert g.status.value == "active"
