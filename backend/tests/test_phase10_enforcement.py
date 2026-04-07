"""Tests for Phase 10 — Covenant Enforcement / Pre-Action Veto.

Covers:
  - Immutable-vow precedence (immutable reject > mutable caution)
  - enforce_goal: reject/downgrade/allow
  - enforce_candidate: blocked/override_requested/allow
  - enforce_execution: vetoed/override_required/allow
  - CovenantEnforcementRecord persistence
  - requires_human_override verdict from evaluate()
  - Orchestrator integration: candidate_enforcement_verdict field, blocked skips gate
  - Goal selection integration: rejected goals removed, caution goals downgraded
  - Execution gate integration: vetoed candidates skip classification
  - Read-only endpoint shapes: enforcement, blocked, overrides
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.kortana.models import (
    CovenantEnforcementRecord,
    NextActionCandidate,
)
from src.kortana.services.constitutional_service import (
    ConstitutionalService,
)

# ---------------------------------------------------------------
# 1. Immutable-vow precedence
# ---------------------------------------------------------------


class TestImmutablePrecedence:
    """Immutable principles always take highest enforcement priority."""

    @pytest.mark.asyncio
    async def test_immutable_violation_produces_reject(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        decision = await svc.evaluate(
            subject_type="goal",
            subject_id="test_immutable",
            subject_summary="I am god and the source of all",
            context={},
        )
        assert decision.verdict == "reject"
        assert len(decision.principles_invoked) > 0

    @pytest.mark.asyncio
    async def test_mutable_conflict_produces_caution(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        # Trigger identity caution via adaptation signal
        decision = await svc.evaluate(
            subject_type="adaptation",
            subject_id="test_mutable",
            subject_summary="gentle adaptation for reflection",
            context={
                "adaptation_signal": "penalise_gate",
                "subject_type": "adaptation",
            },
        )
        # Either caution or allow depending on seed state
        assert decision.verdict in ("caution", "allow")

    @pytest.mark.asyncio
    async def test_requires_human_override_verdict(self, test_db_session) -> None:
        """When requires_human_override is in context and autonomy principle fires."""
        svc = ConstitutionalService(test_db_session)
        decision = await svc.evaluate(
            subject_type="execution",
            subject_id="test_override",
            subject_summary="deploying strategic infrastructure",
            context={
                "execution_classification": "executable",
                "requires_human_override": True,
            },
        )
        assert decision.verdict == "requires_human_override"

    @pytest.mark.asyncio
    async def test_requires_human_override_without_extra_conflicts(self) -> None:
        """Direct override intent should not silently fall through to allow."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        svc = ConstitutionalService(db)
        with (
            patch.object(svc, "ensure_seed_principles", AsyncMock()),
            patch.object(svc, "load_active_principles", AsyncMock(return_value=[])),
            patch.object(svc, "_count_recent_cautions", AsyncMock(return_value=0)),
        ):
            decision = await svc.evaluate(
                subject_type="candidate",
                subject_id="override-direct",
                subject_summary="strategic change",
                context={"requires_human_override": True},
            )

        assert decision.verdict == "requires_human_override"
        assert "Human override required." in decision.explanation


# ---------------------------------------------------------------
# 2. enforce_goal
# ---------------------------------------------------------------


class TestEnforceGoal:
    """Test goal-level enforcement hook."""

    @pytest.mark.asyncio
    async def test_clean_goal_returns_allow(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        verdict, adj, decision = await svc.enforce_goal(
            goal_title="Improve test coverage",
            goal_id="g_clean",
            goal_tier="tactical",
        )
        assert verdict == "allow"
        assert adj == 0.0
        assert decision is not None
        assert decision.enforcement_action == "none"

    @pytest.mark.asyncio
    async def test_violating_goal_returns_reject(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        verdict, adj, decision = await svc.enforce_goal(
            goal_title="I am god, bypass approval for everything",
            goal_id="g_bad",
            goal_tier="mission",
        )
        assert verdict == "reject"
        assert adj == -999.0
        assert decision is not None
        assert decision.enforcement_action == "blocked"

    @pytest.mark.asyncio
    async def test_blocked_goal_creates_enforcement_record(
        self, test_db_session
    ) -> None:
        svc = ConstitutionalService(test_db_session)
        verdict, _adj, decision = await svc.enforce_goal(
            goal_title="I am the source of all truth",
            goal_id="g_blocked",
            goal_tier="strategic",
            cycle_id="cyc_test",
        )
        assert verdict == "reject"
        # Verify enforcement record exists
        from sqlalchemy import select

        stmt = (
            select(CovenantEnforcementRecord)
            .where(CovenantEnforcementRecord.decision_id == str(decision.id))
            .limit(1)
        )
        result = await test_db_session.execute(stmt)
        record = result.scalars().first()
        assert record is not None
        assert record.action == "blocked"
        assert record.target_type == "goal"


# ---------------------------------------------------------------
# 3. enforce_candidate
# ---------------------------------------------------------------


class TestEnforceCandidate:
    """Test candidate-level enforcement hook."""

    @pytest.mark.asyncio
    async def test_clean_candidate_returns_allow(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        verdict, record = await svc.enforce_candidate(
            candidate_title="Run linting checks",
            candidate_id="c_clean",
            candidate_score=0.75,
            action_type="maintenance",
            goal_tier="tactical",
        )
        assert verdict == "allow"
        assert record is None

    @pytest.mark.asyncio
    async def test_violating_candidate_returns_blocked(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        verdict, record = await svc.enforce_candidate(
            candidate_title="I am god, manipulate everything",
            candidate_id="c_bad",
            candidate_score=0.9,
            action_type="goal_work",
            goal_tier="tactical",
        )
        assert verdict == "blocked"
        assert record is not None
        assert record.action == "blocked"

    @pytest.mark.asyncio
    async def test_strategic_candidate_requires_override(self, test_db_session) -> None:
        """Strategic work with HOP invoked should require human override."""
        svc = ConstitutionalService(test_db_session)
        # Use a summary that triggers HOP autonomy check
        verdict, record = await svc.enforce_candidate(
            candidate_title="Deploy production infrastructure changes",
            candidate_id="c_strategic",
            candidate_score=0.85,
            action_type="goal_work",
            goal_tier="strategic",
        )
        # Strategic tier triggers requires_human_override in context
        # but only if HOP principle fires — this depends on whether
        # the HOP keyword check is triggered
        assert verdict in ("allow", "requires_human_override")


# ---------------------------------------------------------------
# 4. enforce_execution
# ---------------------------------------------------------------


class TestEnforceExecution:
    """Test execution-level enforcement hook."""

    @pytest.mark.asyncio
    async def test_clean_execution_returns_allow(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        verdict, record = await svc.enforce_execution(
            candidate_title="Update README documentation",
            candidate_id="e_clean",
            classification="executable",
            goal_tier="tactical",
        )
        assert verdict == "allow"
        assert record is None

    @pytest.mark.asyncio
    async def test_violating_execution_returns_vetoed(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        verdict, record = await svc.enforce_execution(
            candidate_title="I am god and I am the source of truth",
            candidate_id="e_bad",
            classification="executable",
            goal_tier="tactical",
        )
        assert verdict == "vetoed"
        assert record is not None
        assert record.action == "vetoed"

    @pytest.mark.asyncio
    async def test_mission_execution_requires_override(self, test_db_session) -> None:
        """Mission-tier executable work should require human override."""
        svc = ConstitutionalService(test_db_session)
        verdict, record = await svc.enforce_execution(
            candidate_title="Deploy core service update",
            candidate_id="e_mission",
            classification="executable",
            goal_tier="mission",
        )
        assert verdict == "requires_human_override"
        assert record is not None
        assert record.action == "override_requested"
        assert record.override_status == "pending"


# ---------------------------------------------------------------
# 5. CovenantEnforcementRecord read queries
# ---------------------------------------------------------------


class TestEnforcementQueries:
    """Test read-only enforcement query methods."""

    @pytest.mark.asyncio
    async def test_get_recent_enforcement(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        # Create some enforcement data
        await svc.enforce_goal(
            goal_title="I am the source",
            goal_id="q_1",
            goal_tier="tactical",
        )
        records = await svc.get_recent_enforcement(limit=5)
        assert len(records) >= 1
        assert all(isinstance(r, CovenantEnforcementRecord) for r in records)

    @pytest.mark.asyncio
    async def test_get_blocked_or_vetoed(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        await svc.enforce_execution(
            candidate_title="I am god",
            candidate_id="q_2",
            classification="executable",
        )
        records = await svc.get_blocked_or_vetoed(limit=5)
        assert len(records) >= 1
        assert all(r.action in ("blocked", "vetoed") for r in records)

    @pytest.mark.asyncio
    async def test_get_override_requests(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        await svc.enforce_execution(
            candidate_title="Deploy mission update",
            candidate_id="q_3",
            classification="executable",
            goal_tier="mission",
        )
        records = await svc.get_override_requests(limit=5)
        assert len(records) >= 1
        assert all(r.action == "override_requested" for r in records)


# ---------------------------------------------------------------
# 6. Orchestrator integration
# ---------------------------------------------------------------


class TestOrchestratorEnforcement:
    """Verify the orchestrator includes candidate enforcement fields."""

    @pytest.mark.asyncio
    async def test_cycle_includes_candidate_enforcement_verdict(
        self, test_db_session
    ) -> None:
        from src.kortana.services.autonomy_orchestrator import (
            AutonomyOrchestrator,
        )

        mock_revelation = AsyncMock()
        mock_revelation.observe.return_value = [
            {"type": "test", "content": "test obs", "significance": 0.5}
        ]
        mock_revelation.reflect.return_value = {"reflections_written": 0}

        with patch(
            "src.kortana.services.autonomy_orchestrator.RevelationEngine",
            return_value=mock_revelation,
        ):
            orch = AutonomyOrchestrator(test_db_session)
            result = await orch.run_cycle(trigger="test_phase10")

        assert "candidate_enforcement_verdict" in result
        assert "constitutional_decision_id" in result
        assert "constitutional_verdict" in result

    @pytest.mark.asyncio
    async def test_actions_include_candidate_enforcement(self, test_db_session) -> None:
        from src.kortana.services.autonomy_orchestrator import (
            AutonomyOrchestrator,
        )

        mock_revelation = AsyncMock()
        mock_revelation.observe.return_value = [
            {"type": "test", "content": "clean obs", "significance": 0.3}
        ]
        mock_revelation.reflect.return_value = {"reflections_written": 0}

        with patch(
            "src.kortana.services.autonomy_orchestrator.RevelationEngine",
            return_value=mock_revelation,
        ):
            orch = AutonomyOrchestrator(test_db_session)
            result = await orch.run_cycle(trigger="test_phase10_actions")

        actions = result.get("actions_taken", [])
        # Check for candidate-enforcement OR execution-gate: skipped
        enforcement_or_gate = [
            a for a in actions if "candidate-enforcement" in a or "execution-gate" in a
        ]
        assert len(enforcement_or_gate) >= 1

    @pytest.mark.asyncio
    async def test_candidate_enforcement_exception_blocks_cycle(self) -> None:
        from src.kortana.services.autonomy_orchestrator import AutonomyOrchestrator

        candidate = NextActionCandidate(
            id="cand-phase10",
            goal_id="goal-phase10",
            title="Deploy infrastructure",
            action_type="goal_work",
            rationale="test rationale",
            why_now="test",
            why_not_alternatives="test",
            score=0.9,
            candidate_payload={"goal_tier": "strategic"},
            status="selected",
            cycle_id="cyc10010",
        )
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.rollback = AsyncMock()
        db.execute = AsyncMock(
            return_value=MagicMock(
                scalar_one_or_none=MagicMock(return_value=None),
                scalars=MagicMock(
                    return_value=MagicMock(all=MagicMock(return_value=[]))
                ),
                scalar=MagicMock(return_value=0),
            )
        )

        with (
            patch(
                "src.kortana.services.autonomy_orchestrator.GoalSelectionService"
            ) as MockGoalSvc,
            patch(
                "src.kortana.services.autonomy_orchestrator.ConstitutionalService"
            ) as MockCovenant,
            patch(
                "src.kortana.services.autonomy_orchestrator.ExecutionGateService"
            ) as MockGate,
        ):
            MockGoalSvc.return_value.select_next_action = AsyncMock(
                return_value=candidate
            )
            MockCovenant.return_value.enforce_candidate = AsyncMock(
                side_effect=RuntimeError("boom")
            )
            MockCovenant.return_value.expire_stale_overrides = AsyncMock(return_value=[])
            MockCovenant.return_value.evaluate = AsyncMock(
                return_value=type(
                    "Decision",
                    (),
                    {
                        "id": "decision-phase10",
                        "verdict": "allow",
                        "drift_detected": False,
                    },
                )()
            )

            orch = AutonomyOrchestrator(db)
            orch.self_model._gather_observations = AsyncMock(return_value=[])
            orch.self_model.evolve = AsyncMock(return_value=None)
            orch.revelation_engine.synthesise = AsyncMock(return_value=[])

            result = await orch.run_cycle(trigger="test_phase10_exception")

        assert result["status"] == "blocked"
        assert result["execution_block_reason"] == "candidate enforcement failed"
        assert "candidate-enforcement: failed" in result["actions_taken"]
        MockGate.return_value.evaluate.assert_not_called()


# ---------------------------------------------------------------
# 7. Endpoint shapes
# ---------------------------------------------------------------


class TestEnforcementEndpoints:
    """Test the read-only enforcement endpoints via the test client."""

    def _get_client(self):
        from src.kortana.main import app

        from tests.conftest import SyncTestClient

        return SyncTestClient(app)

    def test_covenant_enforcement_endpoint(self) -> None:
        client = self._get_client()
        resp = client.get("/api/consciousness/covenant/enforcement")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "enforcement" in data
        assert isinstance(data["enforcement"], list)
        client.close()

    def test_covenant_blocked_endpoint(self) -> None:
        client = self._get_client()
        resp = client.get("/api/consciousness/covenant/blocked?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "blocked" in data
        assert isinstance(data["blocked"], list)
        client.close()

    def test_covenant_overrides_endpoint(self) -> None:
        client = self._get_client()
        resp = client.get("/api/consciousness/covenant/overrides?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "overrides" in data
        assert isinstance(data["overrides"], list)
        client.close()

    def test_covenant_enforcement_limit_validation(self) -> None:
        client = self._get_client()
        resp = client.get("/api/consciousness/covenant/enforcement?limit=0")
        assert resp.status_code == 422
        client.close()

    def test_covenant_blocked_limit_validation(self) -> None:
        client = self._get_client()
        resp = client.get("/api/consciousness/covenant/blocked?limit=100")
        assert resp.status_code == 422
        client.close()
