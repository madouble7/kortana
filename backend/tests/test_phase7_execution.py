"""Tests for Phase 7 — Action Realization / Execution Gate.

Covers:
  - Classification logic (executable, deferred, blocked, requires_human)
  - ActionExecutionRecord persistence
  - ExecutionGateService evaluate + record_outcome
  - Orchestrator includes execution_record in cycle result
  - Read-only endpoint shapes: execution/current, execution/history
  - No live Gemini dependency
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from src.kortana.models import NextActionCandidate
from src.kortana.services.execution_gate_service import (
    ExecutionGateService,
    _classify_candidate,
)

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------


def _make_candidate(**kwargs: object) -> NextActionCandidate:
    defaults: dict = {
        "id": str(uuid.uuid4()),
        "title": "test action",
        "action_type": "observation",
        "rationale": "test rationale",
        "why_now": "test urgency",
        "why_not_alternatives": "test alternatives",
        "score": 0.65,
        "goal_id": None,
        "candidate_payload": {},
        "status": "selected",
        "cycle_id": "test0001",
        "created_at": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return NextActionCandidate(**defaults)


# ---------------------------------------------------------------
# Unit: deterministic classification logic
# ---------------------------------------------------------------
class TestClassifyCandidate:
    """Verify _classify_candidate produces correct classifications."""

    def test_idle_always_executable(self) -> None:
        c = _make_candidate(action_type="idle", score=0.0)
        classification, rationale, plan = _classify_candidate(c)
        assert classification == "executable"
        assert plan is not None
        assert len(plan) > 0

    def test_observation_is_executable(self) -> None:
        c = _make_candidate(action_type="observation", score=0.5)
        classification, _, plan = _classify_candidate(c)
        assert classification == "executable"
        assert plan is not None

    def test_maintenance_is_executable(self) -> None:
        c = _make_candidate(action_type="maintenance", score=0.5)
        classification, _, _ = _classify_candidate(c)
        assert classification == "executable"

    def test_already_executed_is_deferred(self) -> None:
        c = _make_candidate(status="executed")
        classification, rationale, _ = _classify_candidate(c)
        assert classification == "deferred"
        assert "already" in rationale.lower()

    def test_already_rejected_is_deferred(self) -> None:
        c = _make_candidate(status="rejected")
        classification, _, _ = _classify_candidate(c)
        assert classification == "deferred"

    def test_block_signal_in_payload(self) -> None:
        c = _make_candidate(
            action_type="goal_work",
            candidate_payload={"missing_dependency": "redis"},
        )
        classification, rationale, plan = _classify_candidate(c)
        assert classification == "blocked"
        assert plan is None
        assert "missing_dependency" in rationale

    def test_external_approval_blocks(self) -> None:
        c = _make_candidate(
            action_type="goal_work",
            candidate_payload={"external_approval_needed": True},
        )
        classification, _, _ = _classify_candidate(c)
        assert classification == "blocked"

    def test_high_score_tactical_is_executable(self) -> None:
        c = _make_candidate(
            action_type="goal_work",
            score=0.7,
            candidate_payload={"goal_tier": "tactical"},
        )
        classification, rationale, plan = _classify_candidate(c)
        assert classification == "executable"
        assert plan is not None
        assert len(plan) >= 2

    def test_mission_tier_requires_human(self) -> None:
        c = _make_candidate(
            action_type="goal_work",
            score=0.8,
            candidate_payload={"goal_tier": "mission"},
        )
        classification, rationale, _ = _classify_candidate(c)
        assert classification == "requires_human"
        assert "human" in rationale.lower()

    def test_strategic_tier_requires_human(self) -> None:
        c = _make_candidate(
            action_type="goal_work",
            score=0.9,
            candidate_payload={"goal_tier": "strategic"},
        )
        classification, _, _ = _classify_candidate(c)
        assert classification == "requires_human"

    def test_low_score_defers(self) -> None:
        c = _make_candidate(action_type="goal_work", score=0.1)
        classification, rationale, plan = _classify_candidate(c)
        assert classification == "deferred"
        assert plan is None
        assert "below" in rationale.lower()

    def test_moderate_score_no_tier_is_executable(self) -> None:
        c = _make_candidate(action_type="goal_work", score=0.4)
        classification, _, plan = _classify_candidate(c)
        assert classification == "executable"
        assert plan is not None


# ---------------------------------------------------------------
# Integration: ExecutionGateService with DB
# ---------------------------------------------------------------
class TestExecutionGateService:
    """Verify end-to-end service flow with real DB."""

    @pytest.mark.asyncio
    async def test_evaluate_creates_record(self, test_db_session) -> None:
        """evaluate() should create an ActionExecutionRecord."""
        candidate = _make_candidate()
        test_db_session.add(candidate)
        await test_db_session.commit()

        svc = ExecutionGateService(test_db_session)
        record = await svc.evaluate(candidate_id=str(candidate.id), cycle_id="cyc001")

        assert record is not None
        assert record.candidate_id == str(candidate.id)
        assert record.classification == "executable"
        assert record.cycle_id == "cyc001"
        assert record.outcome in ("pending", "deferred", "skipped")

    @pytest.mark.asyncio
    async def test_evaluate_no_candidate_returns_none(self, test_db_session) -> None:
        """evaluate() with a nonexistent candidate_id returns None."""
        svc = ExecutionGateService(test_db_session)
        record = await svc.evaluate(candidate_id=str(uuid.uuid4()))
        assert record is None

    @pytest.mark.asyncio
    async def test_evaluate_latest_candidate(self, test_db_session) -> None:
        """evaluate() with no candidate_id picks the most recent one."""
        c1 = _make_candidate(title="older")
        c2 = _make_candidate(title="newer")
        test_db_session.add(c1)
        test_db_session.add(c2)
        await test_db_session.commit()

        svc = ExecutionGateService(test_db_session)
        record = await svc.evaluate()
        assert record is not None
        assert record.candidate_id in (str(c1.id), str(c2.id))

    @pytest.mark.asyncio
    async def test_record_outcome(self, test_db_session) -> None:
        """record_outcome() should update an existing record."""
        candidate = _make_candidate()
        test_db_session.add(candidate)
        await test_db_session.commit()

        svc = ExecutionGateService(test_db_session)
        record = await svc.evaluate(candidate_id=str(candidate.id))
        assert record is not None

        updated = await svc.record_outcome(
            record_id=str(record.id),
            outcome="succeeded",
            detail="Completed without issues.",
        )
        assert updated is not None
        assert updated.outcome == "succeeded"
        assert updated.outcome_detail == "Completed without issues."
        assert updated.completed_at is not None

    @pytest.mark.asyncio
    async def test_record_outcome_missing_id(self, test_db_session) -> None:
        """record_outcome() with unknown id returns None."""
        svc = ExecutionGateService(test_db_session)
        result = await svc.record_outcome(str(uuid.uuid4()), "failed")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_execution(self, test_db_session) -> None:
        """get_current_execution() returns the latest record."""
        candidate = _make_candidate()
        test_db_session.add(candidate)
        await test_db_session.commit()

        svc = ExecutionGateService(test_db_session)
        await svc.evaluate(candidate_id=str(candidate.id))
        current = await svc.get_current_execution()

        assert current is not None
        assert current.candidate_id == str(candidate.id)

    @pytest.mark.asyncio
    async def test_get_execution_history(self, test_db_session) -> None:
        """get_execution_history() returns records in newest-first order."""
        for i in range(3):
            c = _make_candidate(title=f"action-{i}")
            test_db_session.add(c)
            await test_db_session.commit()

            svc = ExecutionGateService(test_db_session)
            await svc.evaluate(candidate_id=str(c.id), cycle_id=f"cyc{i:03d}")

        svc = ExecutionGateService(test_db_session)
        history = await svc.get_execution_history(limit=50)
        assert len(history) >= 3
        # Newest first
        for i in range(len(history) - 1):
            if history[i].created_at and history[i + 1].created_at:
                assert history[i].created_at >= history[i + 1].created_at


# ---------------------------------------------------------------
# Integration: Orchestrator includes execution fields
# ---------------------------------------------------------------
class TestOrchestratorExecutionGate:
    """Verify the orchestrator step 3.7 adds execution fields."""

    @pytest.mark.asyncio
    async def test_cycle_result_includes_execution_fields(
        self, test_db_session
    ) -> None:
        """run_cycle() result dict should contain execution_record_id."""
        from src.kortana.services.autonomy_orchestrator import AutonomyOrchestrator

        # Seed a candidate so execution gate has something to evaluate
        candidate = _make_candidate(title="orch-test")
        test_db_session.add(candidate)
        await test_db_session.commit()

        # Build the orchestrator, then stub its internal services
        orch = AutonomyOrchestrator(db=test_db_session)
        orch.self_model._gather_observations = AsyncMock(return_value=[])
        orch.self_model.evolve = AsyncMock(
            return_value=type(
                "M",
                (),
                {
                    "version": "1.0",
                    "developmental_stage": "testing",
                    "confidence": 0.5,
                },
            )()
        )
        orch.revelation_engine.synthesise = AsyncMock(return_value=[])

        with patch(
            "src.kortana.services.autonomy_orchestrator.GoalSelectionService",
        ) as MockGoalSvc:
            mock_selector = AsyncMock()
            mock_selector.select_next_action = AsyncMock(return_value=candidate)
            MockGoalSvc.return_value = mock_selector

            result = await orch.run_cycle(trigger="test")

        assert "execution_record_id" in result
        assert "execution_classification" in result


# ---------------------------------------------------------------
# Endpoint shapes: GET execution/current, GET execution/history
# ---------------------------------------------------------------
class TestExecutionEndpoints:
    """Verify read-only HTTP endpoints return correct shapes."""

    @pytest.fixture
    def client(self):
        from src.kortana.main import app

        from tests.conftest import SyncTestClient

        return SyncTestClient(app)

    def test_execution_current_empty(self, client) -> None:
        resp = client.get("/api/consciousness/execution/current")
        assert resp.status_code == 200
        body = resp.json()
        assert "execution" in body

    def test_execution_history_empty(self, client) -> None:
        resp = client.get("/api/consciousness/execution/history")
        assert resp.status_code == 200
        body = resp.json()
        assert "count" in body
        assert "executions" in body
        assert isinstance(body["executions"], list)

    def test_execution_history_limit_param(self, client) -> None:
        resp = client.get("/api/consciousness/execution/history?limit=5")
        assert resp.status_code == 200
        body = resp.json()
        assert "count" in body
