"""Tests for Phase 6 — Agency Core / Goal Selection Foundation.

Covers:
  - Goal scoring deterministic logic
  - GoalSelectionService ranking and selection
  - NextActionCandidate persistence
  - Orchestrator includes next_action in cycle result
  - Read-only endpoint shapes: goals/active, goals/next-action, goals/next-action/history
  - No live Gemini dependency
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import delete as sa_delete
from src.kortana.models import AutonomyGoal, NextActionCandidate
from src.kortana.services.goal_selection_service import (
    GoalSelectionService,
    _build_idle_candidate,
    _compute_goal_score,
    _rank_goals,
)


# ---------------------------------------------------------------
# Unit: deterministic goal scoring
# ---------------------------------------------------------------
class TestGoalScoring:
    """Verify _compute_goal_score produces correct deterministic scores."""

    def _make_goal(self, **kwargs: object) -> AutonomyGoal:
        defaults = {
            "id": str(uuid.uuid4()),
            "title": "test goal",
            "tier": "operational",
            "status": "active",
            "description": "",
            "success_criteria": "",
            "progress": 0.0,
            "priority": 50,
        }
        defaults.update(kwargs)
        return AutonomyGoal(**defaults)

    def test_higher_priority_scores_higher(self) -> None:
        low = self._make_goal(priority=20)
        high = self._make_goal(priority=90)
        assert _compute_goal_score(high, None) > _compute_goal_score(low, None)

    def test_mission_tier_outscores_maintenance(self) -> None:
        mission = self._make_goal(tier="mission", priority=50)
        maint = self._make_goal(tier="maintenance", priority=50)
        assert _compute_goal_score(mission, None) > _compute_goal_score(maint, None)

    def test_in_progress_gets_momentum_boost(self) -> None:
        active = self._make_goal(status="active", priority=50, tier="operational")
        in_prog = self._make_goal(status="in_progress", priority=50, tier="operational")
        assert _compute_goal_score(in_prog, None) > _compute_goal_score(active, None)

    def test_near_complete_gets_progress_boost(self) -> None:
        early = self._make_goal(progress=0.2, priority=50)
        almost = self._make_goal(progress=0.8, priority=50)
        assert _compute_goal_score(almost, None) > _compute_goal_score(early, None)

    def test_stage_alignment_nascent_favours_tactical(self) -> None:
        # Use equal tier weights (both operational=0.6) so alignment bonus is decisive
        tactical = self._make_goal(tier="tactical", priority=50)
        operational = self._make_goal(tier="operational", priority=50)
        # In nascent stage, tactical gets +0.15 alignment bonus
        t_score = _compute_goal_score(tactical, "nascent")
        o_score = _compute_goal_score(operational, "nascent")
        assert t_score > o_score

    def test_stage_alignment_autonomous_favours_mission(self) -> None:
        mission = self._make_goal(tier="mission", priority=50)
        tactical = self._make_goal(tier="tactical", priority=50)
        m_score = _compute_goal_score(mission, "autonomous")
        t_score = _compute_goal_score(tactical, "autonomous")
        assert m_score > t_score


class TestGoalRanking:
    """Verify _rank_goals produces sorted output."""

    def _make_goal(self, **kwargs: object) -> AutonomyGoal:
        defaults = {
            "id": str(uuid.uuid4()),
            "title": "test goal",
            "tier": "operational",
            "status": "active",
            "description": "",
            "success_criteria": "",
            "progress": 0.0,
            "priority": 50,
        }
        defaults.update(kwargs)
        return AutonomyGoal(**defaults)

    def test_ranking_returns_sorted_descending(self) -> None:
        goals = [
            self._make_goal(title="low", priority=10, tier="maintenance"),
            self._make_goal(title="high", priority=90, tier="mission"),
            self._make_goal(title="mid", priority=50, tier="operational"),
        ]
        ranked = _rank_goals(goals, None)
        assert ranked[0]["goal"].title == "high"
        assert ranked[-1]["goal"].title == "low"
        assert all("score" in r for r in ranked)

    def test_ranking_with_empty_list(self) -> None:
        assert _rank_goals([], None) == []


class TestBuildIdleCandidate:
    def test_idle_candidate_fields(self) -> None:
        c = _build_idle_candidate("abc123")
        assert c.action_type == "idle"
        assert c.score == 0.0
        assert c.cycle_id == "abc123"
        assert c.goal_id is None
        assert c.status == "proposed"


# ---------------------------------------------------------------
# Integration: GoalSelectionService with DB
# ---------------------------------------------------------------
class TestGoalSelectionService:
    """Verify selection service reads from DB and persists candidates."""

    @pytest.mark.asyncio
    async def test_select_next_action_no_goals_returns_idle(
        self, test_db_session
    ) -> None:
        # Ensure no goals exist
        await test_db_session.execute(sa_delete(AutonomyGoal))
        await test_db_session.execute(sa_delete(NextActionCandidate))
        await test_db_session.commit()

        svc = GoalSelectionService(test_db_session)
        candidate = await svc.select_next_action(cycle_id="idle01")
        assert candidate.action_type == "idle"
        assert candidate.cycle_id == "idle01"
        assert candidate.id is not None  # was persisted

    @pytest.mark.asyncio
    async def test_select_next_action_picks_highest_scoring(
        self, test_db_session
    ) -> None:
        # Clean slate
        await test_db_session.execute(sa_delete(NextActionCandidate))
        await test_db_session.execute(sa_delete(AutonomyGoal))
        await test_db_session.commit()

        # Insert two goals: one high-priority mission, one low-priority maintenance
        g_high = AutonomyGoal(
            id=str(uuid.uuid4()),
            title="Deploy core module",
            tier="mission",
            status="active",
            priority=90,
            progress=0.3,
        )
        g_low = AutonomyGoal(
            id=str(uuid.uuid4()),
            title="Clean temp files",
            tier="maintenance",
            status="active",
            priority=20,
            progress=0.0,
        )
        test_db_session.add_all([g_high, g_low])
        await test_db_session.commit()

        svc = GoalSelectionService(test_db_session)
        candidate = await svc.select_next_action(cycle_id="sel01")

        assert candidate.action_type != "idle"
        assert candidate.goal_id == g_high.id
        assert candidate.score > 0
        assert "Deploy core module" in candidate.title
        assert candidate.why_not_alternatives  # should mention alternatives
        assert candidate.why_now  # should have reasoning

    @pytest.mark.asyncio
    async def test_candidate_payload_has_expected_keys(self, test_db_session) -> None:
        # Reuse existing goals from prior test (or insert one)
        await test_db_session.execute(sa_delete(NextActionCandidate))
        await test_db_session.execute(sa_delete(AutonomyGoal))
        await test_db_session.commit()

        g = AutonomyGoal(
            id=str(uuid.uuid4()),
            title="Build API",
            tier="strategic",
            status="in_progress",
            priority=70,
            progress=0.5,
        )
        test_db_session.add(g)
        await test_db_session.commit()

        svc = GoalSelectionService(test_db_session)
        candidate = await svc.select_next_action(cycle_id="pay01")

        assert candidate.candidate_payload is not None
        payload = candidate.candidate_payload
        assert "goal_tier" in payload
        assert "goal_status" in payload
        assert "ranked_count" in payload

    @pytest.mark.asyncio
    async def test_get_current_next_action_returns_latest(
        self, test_db_session
    ) -> None:
        await test_db_session.execute(sa_delete(NextActionCandidate))
        await test_db_session.commit()

        # Insert two candidates manually
        c1 = NextActionCandidate(
            title="first",
            action_type="goal_work",
            rationale="r",
            why_now="w",
            why_not_alternatives="n",
            score=0.5,
            status="proposed",
            cycle_id="h01",
            created_at=datetime(2026, 1, 1),
        )
        c2 = NextActionCandidate(
            title="second",
            action_type="maintenance",
            rationale="r",
            why_now="w",
            why_not_alternatives="n",
            score=0.8,
            status="proposed",
            cycle_id="h02",
            created_at=datetime(2026, 4, 1),
        )
        test_db_session.add_all([c1, c2])
        await test_db_session.commit()

        svc = GoalSelectionService(test_db_session)
        latest = await svc.get_current_next_action()
        assert latest is not None
        assert latest.title == "second"

    @pytest.mark.asyncio
    async def test_get_next_action_history_respects_limit(
        self, test_db_session
    ) -> None:
        svc = GoalSelectionService(test_db_session)
        history = await svc.get_next_action_history(limit=1)
        assert len(history) <= 1


# ---------------------------------------------------------------
# Integration: Orchestrator includes next_action in cycle result
# ---------------------------------------------------------------
class TestOrchestratorGoalSelection:
    """Verify autonomy orchestrator cycle result includes next_action fields."""

    def test_cycle_result_contains_next_action_keys(self, authenticated_client) -> None:
        mock_result = {
            "cycle_id": "orch01",
            "trigger": "daemon",
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 300,
            "observations": 3,
            "revelations_written": 0,
            "self_model_version": 1,
            "developmental_stage": "nascent",
            "next_action_candidate_id": "fake-id-123",
            "next_action_title": "Work on: Deploy core module",
            "actions_taken": ["observed 3 signals", "next-action: Deploy core module"],
        }

        with patch(
            "src.kortana.services.autonomy_orchestrator.AutonomyOrchestrator"
        ) as MockOrch:
            instance = MockOrch.return_value
            instance.run_cycle = AsyncMock(return_value=mock_result)
            resp = authenticated_client.post(
                "/api/consciousness/_internal/autonomy-cycle"
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "next_action_candidate_id" in data
        assert "next_action_title" in data
        assert data["next_action_candidate_id"] == "fake-id-123"


# ---------------------------------------------------------------
# Read-only endpoint shapes
# ---------------------------------------------------------------
class TestGoalEndpoints:
    """Verify goals/active, goals/next-action, goals/next-action/history shapes."""

    def test_goals_active_returns_list_shape(self, client) -> None:
        resp = client.get("/api/consciousness/goals/active")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "goals" in data
        assert isinstance(data["goals"], list)

    def test_goals_next_action_returns_shape(self, client) -> None:
        resp = client.get("/api/consciousness/goals/next-action")
        assert resp.status_code == 200
        data = resp.json()
        # Either null or full candidate
        if data.get("next_action") is not None:
            na = data["next_action"]
            assert "title" in na
            assert "action_type" in na
            assert "rationale" in na
            assert "why_now" in na
            assert "why_not_alternatives" in na
            assert "score" in na
        else:
            assert "message" in data

    def test_goals_next_action_history_returns_shape(self, client) -> None:
        resp = client.get("/api/consciousness/goals/next-action/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "candidates" in data
        assert isinstance(data["candidates"], list)

    def test_goals_next_action_history_respects_limit(self, client) -> None:
        resp = client.get("/api/consciousness/goals/next-action/history?limit=3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] <= 3
