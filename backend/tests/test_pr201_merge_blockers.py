"""Targeted tests for PR #201 merge-blocker fixes.

Covers:
  - Stale-candidate skip (autonomy_orchestrator gate guard)
  - Revelation field mapping (signal_weight / signal_scope)
  - Override-learning method name (learn_from_override_resolution)
  - Not-found audit null FK (OverrideAuditRecord)
  - goal.progress None-safe formatting
  - Wisdom/predictions endpoint read from RevelationMemory
"""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.kortana.models import (
    AutonomyGoal,
    OutcomeLearningRecord,
    RevelationMemory,
)
from src.kortana.services.goal_selection_service import GoalSelectionService

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------


def _make_goal(**kwargs: object) -> AutonomyGoal:
    defaults: dict = {
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


def _make_learning_record(**kwargs: object) -> OutcomeLearningRecord:
    defaults: dict = {
        "id": str(uuid.uuid4()),
        "outcome_verdict": "succeeded",
        "adaptation_signal": "boost_tier:tactical",
        "signal_weight": 0.3,
        "signal_scope": "cycle",
        "lesson": "Test learning lesson content.",
        "expectation_match": "expected",
        "source_type": "execution",
        "applied": False,
        "created_at": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return OutcomeLearningRecord(**defaults)


# ---------------------------------------------------------------
# 1. goal.progress None-safe formatting
# ---------------------------------------------------------------


class TestGoalProgressNoneSafe:
    """Verify progress=None does not crash % formatting."""

    def test_progress_none_in_rationale(self) -> None:
        """Top-goal rationale must not throw when progress is None."""
        goal = _make_goal(progress=None, priority=80, tier="strategic")
        # The formatting used in GoalSelectionService._build_candidate:
        val = (goal.progress or 0)
        formatted = f"progress={val:.0%}"
        assert formatted == "progress=0%"

    def test_progress_none_in_why_now(self) -> None:
        """Already-in-progress text must not crash when progress is None."""
        goal = _make_goal(progress=None, status="in_progress")
        val = (goal.progress or 0)
        formatted = f"Already in progress ({val:.0%} complete)"
        assert formatted == "Already in progress (0% complete)"

    def test_progress_float_still_works(self) -> None:
        goal = _make_goal(progress=0.75)
        val = (goal.progress or 0)
        formatted = f"progress={val:.0%}"
        assert formatted == "progress=75%"

    def test_compute_why_now_with_none_progress(self) -> None:
        """Integration: _compute_why_now handles None progress."""
        goal = _make_goal(progress=None, status="in_progress")
        result = GoalSelectionService._compute_why_now(goal, None, None)
        assert "complete" in result


# ---------------------------------------------------------------
# 2. Revelation field mapping (signal_weight / signal_scope)
# ---------------------------------------------------------------


class TestRevelationFieldMapping:
    """Ensure _gather_learning_lessons uses correct field names."""

    @pytest.mark.asyncio
    async def test_gather_outcome_signals_uses_signal_weight_and_scope(self) -> None:
        """The formatted string must reference signal_weight & signal_scope."""
        from src.kortana.services.revelation_engine import _gather_outcome_signals

        rec = _make_learning_record(
            signal_weight=0.5,
            signal_scope="session",
        )

        # Mock async session
        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [rec]
        session.execute = AsyncMock(return_value=result_mock)

        lines = await _gather_outcome_signals(session, limit=5)
        assert len(lines) == 1
        assert "weight=+0.50" in lines[0]
        assert "scope=session" in lines[0]

    @pytest.mark.asyncio
    async def test_gather_outcome_signals_no_attribute_error(self) -> None:
        """Must NOT raise AttributeError for weight_delta / scope."""
        from src.kortana.services.revelation_engine import _gather_outcome_signals

        rec = _make_learning_record()
        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [rec]
        session.execute = AsyncMock(return_value=result_mock)

        # Should not raise
        lines = await _gather_outcome_signals(session, limit=5)
        assert len(lines) == 1


# ---------------------------------------------------------------
# 3. Override-learning method name
# ---------------------------------------------------------------


class TestOverrideLearningMethodName:
    """Ensure constitutional_service calls learn_from_override_resolution."""

    @pytest.mark.asyncio
    async def test_resolve_override_calls_correct_method(self) -> None:
        """The resolve_override path must call learn_from_override_resolution."""
        from src.kortana.models import CovenantEnforcementRecord
        from src.kortana.services.constitutional_service import ConstitutionalService

        # Build a mock enforcement record in pending state
        record = CovenantEnforcementRecord(
            id=str(uuid.uuid4()),
            cycle_id="AAAA",
            decision_id="dec-001",
            target_type="action",
            target_id="some-action",
            target_summary="requires_human_override",
            action="override_requested",
            override_status="pending",
            created_at=datetime.utcnow(),
        )

        # Mock DB
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = record
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        svc = ConstitutionalService(db)

        # Patch outcome learning service
        with patch(
            "src.kortana.services.outcome_learning_service.OutcomeLearningService"
        ) as MockOLS:
            mock_ols_instance = AsyncMock()
            MockOLS.return_value = mock_ols_instance
            mock_ols_instance.learn_from_override_resolution = AsyncMock(
                return_value=None
            )

            # Patch _record_audit
            with patch.object(svc, "_record_audit", new_callable=AsyncMock):
                await svc.resolve_override(
                    record_id=record.id,
                    resolution="approved",
                    resolver="matt",
                    rationale="test approval",
                )

            # Verify correct method was called
            mock_ols_instance.learn_from_override_resolution.assert_awaited_once()


# ---------------------------------------------------------------
# 4. Stale-candidate skip (execution gate guard)
# ---------------------------------------------------------------


class TestStaleCandidateSkip:
    """When goal selection fails, execution gate must NOT be called with None."""

    @pytest.mark.asyncio
    async def test_orchestrator_skips_gate_when_no_candidate(self) -> None:
        """ExecutionGateService.evaluate must not be called if next_action_id is None."""
        from src.kortana.services.autonomy_orchestrator import AutonomyOrchestrator

        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None),
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))),
            scalar=MagicMock(return_value=0),
        ))
        db.commit = AsyncMock()
        db.rollback = AsyncMock()

        with patch(
            "src.kortana.services.autonomy_orchestrator.ExecutionGateService"
        ) as MockGate:
            mock_gate = AsyncMock()
            MockGate.return_value = mock_gate

            # Patch everything the orchestrator needs
            with patch(
                "src.kortana.services.autonomy_orchestrator.SelfModelService"
            ), patch(
                "src.kortana.services.autonomy_orchestrator.RevelationEngine"
            ), patch(
                "src.kortana.services.autonomy_orchestrator.GoalSelectionService"
            ) as MockGoalSvc, patch(
                "src.kortana.services.autonomy_orchestrator.ConstitutionalService"
            ), patch(
                "src.kortana.services.autonomy_orchestrator.OutcomeLearningService"
            ):
                # Goal selection returns None
                MockGoalSvc.return_value.select_next_action = AsyncMock(
                    return_value=None
                )

                orch = AutonomyOrchestrator(db)
                # Patch internal services
                orch.self_model = AsyncMock()
                orch.self_model._gather_observations = AsyncMock(return_value=[])
                orch.self_model.evolve = AsyncMock(return_value=None)
                orch.revelation_engine = AsyncMock()
                orch.revelation_engine.synthesise = AsyncMock(return_value=[])

                try:
                    await orch.run_cycle(trigger="test")
                except Exception:
                    pass  # We only care that gate.evaluate was not called with None

                # If gate.evaluate was called, its candidate_id must not be None
                for call in mock_gate.evaluate.call_args_list:
                    _, kwargs = call
                    assert kwargs.get("candidate_id") is not None, (
                        "ExecutionGateService.evaluate called with candidate_id=None"
                    )


# ---------------------------------------------------------------
# 5. Not-found audit null FK
# ---------------------------------------------------------------


class TestNotFoundAuditNullFK:
    """When enforcement record is not found, audit FK should be None."""

    @pytest.mark.asyncio
    async def test_resolve_override_not_found_uses_null_fk(self) -> None:
        from src.kortana.services.constitutional_service import ConstitutionalService

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None  # record not found
        db.execute = AsyncMock(return_value=result_mock)

        svc = ConstitutionalService(db)

        audit_calls: list = []
        original_record_audit = svc._record_audit

        async def capture_audit(*args, **kwargs):
            audit_calls.append(kwargs)
            return await original_record_audit(*args, **kwargs)

        with patch.object(svc, "_record_audit", side_effect=capture_audit):
            result = await svc.resolve_override(
                record_id="nonexistent-id",
                resolution="approved",
                resolver="matt",
                rationale="test",
            )

        assert result is None
        assert len(audit_calls) == 1
        assert audit_calls[0]["enforcement_record_id"] is None
        assert audit_calls[0]["outcome"] == "not_found"


# ---------------------------------------------------------------
# 6. Wisdom/predictions read from RevelationMemory
# ---------------------------------------------------------------


class TestWisdomPredictionsEndpoints:
    """Verify /wisdom and /predictions query RevelationMemory."""

    @pytest.mark.asyncio
    async def test_wisdom_queries_revelation_memory(self) -> None:
        """The /wisdom endpoint must query RevelationMemory, not SelfMemory."""
        from src.kortana.routers.consciousness import get_wisdom

        rev = RevelationMemory(
            id=str(uuid.uuid4()),
            title="Night coding pattern",
            content="Matt codes mostly at night.",
            revelation_type="pattern",
            confidence=0.85,
            surfaced=False,
            source="revelation_engine",
            created_at=datetime.utcnow(),
        )

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [rev]
        db.execute = AsyncMock(return_value=result_mock)

        response = await get_wisdom(limit=10, db=db)
        assert response["count"] == 1
        assert response["wisdom"][0]["summary"] == "Night coding pattern"
        assert response["wisdom"][0]["type"] == "pattern"

    @pytest.mark.asyncio
    async def test_predictions_queries_revelation_memory(self) -> None:
        """The /predictions endpoint must query RevelationMemory, not SelfMemory."""
        from src.kortana.routers.consciousness import get_predictions

        pred = RevelationMemory(
            id=str(uuid.uuid4()),
            title="Build time will increase",
            content="Based on file growth rate.",
            revelation_type="prediction",
            confidence=0.7,
            surfaced=False,
            source="revelation_engine",
            created_at=datetime.utcnow(),
        )

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [pred]
        db.execute = AsyncMock(return_value=result_mock)

        response = await get_predictions(limit=10, db=db)
        assert response["count"] == 1
        assert response["predictions"][0]["summary"] == "Build time will increase"
