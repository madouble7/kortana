"""Tests for DB-backed GoalManager persistence."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import delete

from src.kortana.database import get_db_manager
from src.kortana.models import AutonomyCycleMemory, AutonomyGoal, GitHubTask
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
        await session.execute(delete(AutonomyCycleMemory))
        await session.execute(delete(GitHubTask))
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
async def test_bootstrap_from_db_loads_defaults_on_cold_start() -> None:
    await _ensure_db_and_clear_goals()
    gm = get_goal_manager()

    await gm.bootstrap_from_db()

    status = gm.get_status()
    assert status["total_goals"] >= 3
    assert status["active"] >= 1


@pytest.mark.asyncio
async def test_bootstrap_from_db_persists_progress_and_metadata() -> None:
    await _ensure_db_and_clear_goals()
    db = get_db_manager()
    now = datetime.utcnow()

    async with db.session_scope() as session:
        for idx in range(12):
            session.add(
                AutonomyCycleMemory(
                    id=f"cycle-{idx}",
                    cycle_id=f"cycle-{idx}",
                    start_time=now - timedelta(minutes=idx + 1),
                    end_time=now - timedelta(minutes=idx),
                    tasks_processed=0,
                    approvals_processed=0,
                    errors_encountered=0,
                    metrics=None,
                )
            )

        for issue_number in range(1, 21):
            status = "completed" if issue_number <= 19 else "failed"
            session.add(
                GitHubTask(
                    id=f"task-{issue_number}",
                    github_issue_number=issue_number,
                    github_repo="matt/kortana",
                    title=f"Task {issue_number}",
                    description="seeded for goal bootstrap",
                    status=status,
                    created_at=now,
                    updated_at=now,
                )
            )

    gm = get_goal_manager()
    await gm.bootstrap_from_db()

    autonomous_goal = next(
        goal for goal in gm.all() if "autonomous operation" in goal.title.lower()
    )
    success_goal = next(
        goal for goal in gm.all() if "success rate" in goal.title.lower()
    )

    assert autonomous_goal.progress == 0.4
    assert autonomous_goal.metadata["clean_cycles"] == 12
    assert success_goal.progress == 0.95
    assert success_goal.metadata["total_tasks"] == 20

    reset_goal_manager_for_testing()
    gm_reloaded = get_goal_manager()
    await gm_reloaded.load_from_db()

    reloaded_autonomous_goal = gm_reloaded.get(autonomous_goal.id)
    reloaded_success_goal = gm_reloaded.get(success_goal.id)
    assert reloaded_autonomous_goal is not None
    assert reloaded_success_goal is not None
    assert reloaded_autonomous_goal.progress == 0.4
    assert reloaded_autonomous_goal.metadata["clean_cycles"] == 12
    assert reloaded_success_goal.progress == 0.95
    assert reloaded_success_goal.metadata["total_tasks"] == 20


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
