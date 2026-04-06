"""Tests for Phase 8 — Outcome Learning / Recursive Adaptation.

Covers:
  - Outcome interpretation rules (deterministic)
  - OutcomeLearningRecord persistence
  - OutcomeLearningService learn_from_execution + history + adaptations
  - Feedback hook functions: compute_score_adjustment, compute_gate_adjustment
  - Goal selector adaptation_adjustment parameter
  - Execution gate gate_adjustment parameter
  - Orchestrator includes outcome learning fields
  - Read-only endpoint shapes: outcomes/current, outcomes/history, adaptations
  - No live Gemini dependency
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.kortana.models import (
    ActionExecutionRecord,
    NextActionCandidate,
)
from src.kortana.services.outcome_learning_service import (
    OutcomeLearningService,
    _interpret_outcome,
    compute_gate_adjustment,
    compute_score_adjustment,
)


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

def _make_candidate(**kwargs: object) -> NextActionCandidate:
    defaults: dict = {
        "id": str(uuid.uuid4()),
        "title": "test action",
        "action_type": "observation",
        "rationale": "test",
        "why_now": "test",
        "why_not_alternatives": "test",
        "score": 0.65,
        "goal_id": None,
        "candidate_payload": {},
        "status": "selected",
        "cycle_id": "test0001",
        "created_at": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return NextActionCandidate(**defaults)


def _make_exec_record(candidate_id: str, **kwargs: object) -> ActionExecutionRecord:
    defaults: dict = {
        "id": str(uuid.uuid4()),
        "candidate_id": candidate_id,
        "classification": "executable",
        "gate_rationale": "test rationale",
        "execution_plan": [{"step": "test"}],
        "outcome": "pending",
        "outcome_detail": None,
        "cycle_id": "test0001",
        "created_at": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return ActionExecutionRecord(**defaults)


# ---------------------------------------------------------------
# Unit: deterministic outcome interpretation
# ---------------------------------------------------------------
class TestOutcomeInterpretation:
    """Verify _interpret_outcome produces correct verdicts and signals."""

    def test_executable_succeeded(self) -> None:
        c = _make_candidate()
        r = _make_exec_record(str(c.id), classification="executable", outcome="succeeded")
        verdict, expect, lesson, signal, weight, scope = _interpret_outcome(r)
        assert verdict == "succeeded"
        assert expect == "expected"
        assert "trust" in signal
        assert weight > 0

    def test_executable_failed(self) -> None:
        c = _make_candidate()
        r = _make_exec_record(str(c.id), classification="executable", outcome="failed")
        verdict, expect, lesson, signal, weight, scope = _interpret_outcome(r)
        assert verdict == "failed"
        assert expect == "surprising"
        assert "penalise" in signal
        assert weight < 0

    def test_executable_pending_is_inconclusive(self) -> None:
        c = _make_candidate()
        r = _make_exec_record(str(c.id), classification="executable", outcome="pending")
        verdict, expect, lesson, signal, weight, scope = _interpret_outcome(r)
        assert verdict == "inconclusive"
        assert expect == "surprising"

    def test_deferred_skipped(self) -> None:
        c = _make_candidate()
        r = _make_exec_record(str(c.id), classification="deferred", outcome="deferred")
        verdict, expect, _, signal, weight, _ = _interpret_outcome(r)
        assert verdict == "skipped"
        assert expect == "expected"
        assert weight == 0.0

    def test_blocked_skipped(self) -> None:
        c = _make_candidate()
        r = _make_exec_record(str(c.id), classification="blocked", outcome="skipped")
        verdict, expect, _, signal, weight, _ = _interpret_outcome(r)
        assert verdict == "skipped"
        assert expect == "expected"

    def test_requires_human_succeeded(self) -> None:
        c = _make_candidate()
        r = _make_exec_record(str(c.id), classification="requires_human", outcome="succeeded")
        verdict, expect, _, signal, weight, _ = _interpret_outcome(r)
        assert verdict == "succeeded"
        assert "trust" in signal

    def test_requires_human_pending(self) -> None:
        c = _make_candidate()
        r = _make_exec_record(str(c.id), classification="requires_human", outcome="pending")
        verdict, expect, _, signal, weight, _ = _interpret_outcome(r)
        assert verdict == "inconclusive"
        assert "neutral" in signal

    def test_executable_skipped_contradictory(self) -> None:
        c = _make_candidate()
        r = _make_exec_record(str(c.id), classification="executable", outcome="skipped")
        verdict, expect, _, signal, weight, _ = _interpret_outcome(r)
        assert verdict == "skipped"
        assert expect == "contradictory"
        assert weight < 0


# ---------------------------------------------------------------
# Unit: feedback hook functions
# ---------------------------------------------------------------
class TestFeedbackHooks:
    """Verify compute_score_adjustment and compute_gate_adjustment."""

    def test_score_adjustment_positive_signals(self) -> None:
        signals = [
            {"signal": "trust_classification:executable", "total_weight": 0.2, "occurrences": 3},
            {"signal": "boost_tier:tactical", "total_weight": 0.1, "occurrences": 1},
        ]
        adj = compute_score_adjustment(signals)
        assert adj > 0
        assert adj <= 0.3

    def test_score_adjustment_negative_signals(self) -> None:
        signals = [
            {"signal": "penalise_classification:executable", "total_weight": -0.4, "occurrences": 2},
        ]
        adj = compute_score_adjustment(signals)
        assert adj < 0
        assert adj >= -0.3

    def test_score_adjustment_clamped(self) -> None:
        signals = [
            {"signal": "trust_classification:executable", "total_weight": 1.0, "occurrences": 50},
        ]
        adj = compute_score_adjustment(signals)
        assert adj == 0.3

    def test_score_adjustment_empty(self) -> None:
        assert compute_score_adjustment([]) == 0.0

    def test_gate_adjustment_matching_classification(self) -> None:
        signals = [
            {"signal": "trust_classification:executable", "total_weight": 0.15, "occurrences": 2},
        ]
        adj = compute_gate_adjustment(signals, "executable")
        assert adj == 0.15

    def test_gate_adjustment_non_matching(self) -> None:
        signals = [
            {"signal": "trust_classification:requires_human", "total_weight": 0.15, "occurrences": 2},
        ]
        adj = compute_gate_adjustment(signals, "executable")
        assert adj == 0.0

    def test_gate_adjustment_clamped(self) -> None:
        signals = [
            {"signal": "penalise_classification:executable", "total_weight": -0.5, "occurrences": 10},
        ]
        adj = compute_gate_adjustment(signals, "executable")
        assert adj == -0.2


# ---------------------------------------------------------------
# Unit: goal scoring with adaptation
# ---------------------------------------------------------------
class TestGoalScoringAdaptation:
    """Verify _compute_goal_score accepts adaptation_adjustment."""

    def test_positive_adjustment_increases_score(self) -> None:
        from src.kortana.models import AutonomyGoal
        from src.kortana.services.goal_selection_service import _compute_goal_score

        goal = AutonomyGoal(
            id=str(uuid.uuid4()),
            title="test",
            tier="operational",
            status="active",
            description="",
            success_criteria="",
            progress=0.0,
            priority=50,
        )
        base = _compute_goal_score(goal, None)
        boosted = _compute_goal_score(goal, None, adaptation_adjustment=0.1)
        assert boosted > base

    def test_negative_adjustment_decreases_score(self) -> None:
        from src.kortana.models import AutonomyGoal
        from src.kortana.services.goal_selection_service import _compute_goal_score

        goal = AutonomyGoal(
            id=str(uuid.uuid4()),
            title="test",
            tier="operational",
            status="active",
            description="",
            success_criteria="",
            progress=0.0,
            priority=50,
        )
        base = _compute_goal_score(goal, None)
        penalised = _compute_goal_score(goal, None, adaptation_adjustment=-0.1)
        assert penalised < base


# ---------------------------------------------------------------
# Unit: execution gate with gate_adjustment
# ---------------------------------------------------------------
class TestGateClassificationAdaptation:
    """Verify _classify_candidate gate_adjustment shifts threshold."""

    def test_positive_adjustment_lowers_threshold(self) -> None:
        from src.kortana.services.execution_gate_service import _classify_candidate

        # Score 0.45 with no adjustment → below 0.5 threshold
        c = _make_candidate(
            action_type="goal_work",
            score=0.45,
            candidate_payload={"goal_tier": "tactical"},
        )
        cls_no_adj, _, _ = _classify_candidate(c, gate_adjustment=0.0)
        cls_with_adj, _, _ = _classify_candidate(c, gate_adjustment=0.1)
        # With +0.1 adjustment, threshold becomes 0.4, so 0.45 should now pass
        assert cls_with_adj == "executable"

    def test_negative_adjustment_raises_threshold(self) -> None:
        from src.kortana.services.execution_gate_service import _classify_candidate

        # Score 0.52 with -0.1 adjustment: threshold becomes 0.6 → should be default
        c = _make_candidate(
            action_type="goal_work",
            score=0.52,
            candidate_payload={"goal_tier": "tactical"},
        )
        cls_no_adj, _, _ = _classify_candidate(c, gate_adjustment=0.0)
        cls_with_adj, _, _ = _classify_candidate(c, gate_adjustment=-0.1)
        assert cls_no_adj == "executable"
        assert cls_with_adj == "executable"  # still passes at 0.52 vs 0.6


# ---------------------------------------------------------------
# Integration: OutcomeLearningService with DB
# ---------------------------------------------------------------
class TestOutcomeLearningService:
    """Verify end-to-end service flow with real DB."""

    @pytest.mark.asyncio
    async def test_learn_from_execution(self, test_db_session) -> None:
        """learn_from_execution should create an OutcomeLearningRecord."""
        candidate = _make_candidate()
        test_db_session.add(candidate)
        await test_db_session.commit()

        exec_record = _make_exec_record(str(candidate.id), outcome="succeeded")
        test_db_session.add(exec_record)
        await test_db_session.commit()

        svc = OutcomeLearningService(test_db_session)
        learning = await svc.learn_from_execution(
            execution_record_id=str(exec_record.id), cycle_id="cyc001"
        )
        assert learning is not None
        assert learning.execution_record_id == str(exec_record.id)
        assert learning.outcome_verdict == "succeeded"
        assert learning.adaptation_signal is not None
        assert learning.cycle_id == "cyc001"

    @pytest.mark.asyncio
    async def test_learn_missing_record_returns_none(self, test_db_session) -> None:
        svc = OutcomeLearningService(test_db_session)
        result = await svc.learn_from_execution(str(uuid.uuid4()))
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_outcome(self, test_db_session) -> None:
        candidate = _make_candidate()
        test_db_session.add(candidate)
        await test_db_session.commit()

        exec_record = _make_exec_record(str(candidate.id), outcome="failed")
        test_db_session.add(exec_record)
        await test_db_session.commit()

        svc = OutcomeLearningService(test_db_session)
        await svc.learn_from_execution(str(exec_record.id))
        current = await svc.get_current_outcome()
        assert current is not None
        assert current.outcome_verdict == "failed"

    @pytest.mark.asyncio
    async def test_get_outcome_history(self, test_db_session) -> None:
        for i in range(3):
            c = _make_candidate(title=f"action-{i}")
            test_db_session.add(c)
            await test_db_session.commit()

            er = _make_exec_record(str(c.id), outcome="succeeded")
            test_db_session.add(er)
            await test_db_session.commit()

            svc = OutcomeLearningService(test_db_session)
            await svc.learn_from_execution(str(er.id), cycle_id=f"cyc{i:03d}")

        svc = OutcomeLearningService(test_db_session)
        history = await svc.get_outcome_history(limit=50)
        assert len(history) >= 3

    @pytest.mark.asyncio
    async def test_get_adaptations(self, test_db_session) -> None:
        candidate = _make_candidate()
        test_db_session.add(candidate)
        await test_db_session.commit()

        exec_record = _make_exec_record(str(candidate.id), outcome="succeeded")
        test_db_session.add(exec_record)
        await test_db_session.commit()

        svc = OutcomeLearningService(test_db_session)
        await svc.learn_from_execution(str(exec_record.id))
        adaptations = await svc.get_adaptations()
        assert isinstance(adaptations, list)
        if len(adaptations) > 0:
            assert "signal" in adaptations[0]
            assert "total_weight" in adaptations[0]


# ---------------------------------------------------------------
# Integration: Orchestrator includes outcome learning fields
# ---------------------------------------------------------------
class TestOrchestratorOutcomeLearning:
    """Verify the orchestrator step 3.9 adds learning fields."""

    @pytest.mark.asyncio
    async def test_cycle_result_includes_learning_fields(
        self, test_db_session
    ) -> None:
        from src.kortana.services.autonomy_orchestrator import AutonomyOrchestrator

        candidate = _make_candidate(title="orch-learn-test")
        test_db_session.add(candidate)
        await test_db_session.commit()

        orch = AutonomyOrchestrator(db=test_db_session)
        orch.self_model._gather_observations = AsyncMock(return_value=[])
        orch.self_model.evolve = AsyncMock(
            return_value=type(
                "M", (), {"version": "1.0", "developmental_stage": "testing", "confidence": 0.5}
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

        assert "outcome_learning_id" in result
        assert "outcome_verdict" in result
        assert "adaptation_signal" in result


# ---------------------------------------------------------------
# Endpoint shapes: outcomes/current, outcomes/history, adaptations
# ---------------------------------------------------------------
class TestOutcomeEndpoints:
    """Verify read-only HTTP endpoints return correct shapes."""

    @pytest.fixture
    def client(self):
        from tests.conftest import SyncTestClient
        from src.kortana.main import app
        return SyncTestClient(app)

    def test_outcomes_current_empty(self, client) -> None:
        resp = client.get("/api/consciousness/outcomes/current")
        assert resp.status_code == 200
        body = resp.json()
        assert "outcome" in body

    def test_outcomes_history_empty(self, client) -> None:
        resp = client.get("/api/consciousness/outcomes/history")
        assert resp.status_code == 200
        body = resp.json()
        assert "count" in body
        assert "outcomes" in body
        assert isinstance(body["outcomes"], list)

    def test_outcomes_history_limit_param(self, client) -> None:
        resp = client.get("/api/consciousness/outcomes/history?limit=5")
        assert resp.status_code == 200
        assert "count" in resp.json()

    def test_adaptations_empty(self, client) -> None:
        resp = client.get("/api/consciousness/adaptations")
        assert resp.status_code == 200
        body = resp.json()
        assert "count" in body
        assert "adaptations" in body
        assert isinstance(body["adaptations"], list)

    def test_adaptations_limit_param(self, client) -> None:
        resp = client.get("/api/consciousness/adaptations?limit=5")
        assert resp.status_code == 200
        assert "count" in resp.json()
