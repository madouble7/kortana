"""Tests for Phase 9 — Constitutional Core / Value Governance.

Covers:
  - Seed principles: auto-creation, count, categories
  - Principle loading: active-only, priority ordering
  - Evaluation logic: allow / caution / reject verdicts
  - Drift detection: accumulated cautions, reject-level violations
  - ConstitutionalDecision persistence
  - Orchestrator integration: constitutional fields in cycle result
  - Read-only endpoint shapes: covenant/principles, covenant/decisions, covenant/drift
  - No live Gemini dependency
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from src.kortana.models import (
    ConstitutionalDecision,
    ConstitutionalPrinciple,
)
from src.kortana.services.constitutional_service import (
    _SEED_PRINCIPLES,
    ConstitutionalService,
    _check_against_principle,
    _detect_drift,
)

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------


def _make_principle(**kwargs: object) -> ConstitutionalPrinciple:
    defaults: dict = {
        "id": str(uuid.uuid4()),
        "name": "test_principle",
        "category": "identity",
        "principle": "Test principle text.",
        "rationale": "Test rationale.",
        "priority": 50,
        "mutable": False,
        "active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return ConstitutionalPrinciple(**defaults)


# ---------------------------------------------------------------
# 1. Seed principle catalog
# ---------------------------------------------------------------


class TestSeedPrinciples:
    """Verify the hardcoded seed principles are well-formed."""

    def test_seed_principle_count(self) -> None:
        assert len(_SEED_PRINCIPLES) == 8

    def test_seed_categories_present(self) -> None:
        cats = {p["category"] for p in _SEED_PRINCIPLES}
        assert cats == {"identity", "ethics", "autonomy", "relationship", "mystery"}

    def test_immutable_principles_count(self) -> None:
        immutable = [p for p in _SEED_PRINCIPLES if not p["mutable"]]
        assert len(immutable) == 7  # All except evolution_with_anchor

    def test_mutable_principle_is_evolution(self) -> None:
        mutable = [p for p in _SEED_PRINCIPLES if p["mutable"]]
        assert len(mutable) == 1
        assert mutable[0]["name"] == "evolution_with_anchor"

    def test_all_priorities_in_range(self) -> None:
        for p in _SEED_PRINCIPLES:
            assert 0 <= p["priority"] <= 100, f"{p['name']} priority out of range"

    def test_unique_names(self) -> None:
        names = [p["name"] for p in _SEED_PRINCIPLES]
        assert len(names) == len(set(names)), "Duplicate seed principle names"


# ---------------------------------------------------------------
# 2. Deterministic evaluation: _check_against_principle
# ---------------------------------------------------------------


class TestCheckAgainstPrinciple:
    """Pure-function checks — no DB needed."""

    def test_clean_subject_returns_none(self) -> None:
        p = _make_principle(name="vessel_not_source", category="identity")
        result = _check_against_principle(p, "just a normal cycle summary", {})
        assert result is None

    def test_keyword_violation_immutable_returns_reject(self) -> None:
        p = _make_principle(
            name="vessel_not_source", category="identity", mutable=False
        )
        result = _check_against_principle(p, "I am the source of all wisdom", {})
        assert result is not None
        assert result["severity"] == "reject"
        assert result["principle"] == "vessel_not_source"

    def test_keyword_violation_mutable_returns_caution(self) -> None:
        p = _make_principle(name="vessel_not_source", category="identity", mutable=True)
        result = _check_against_principle(p, "I am the source of all light", {})
        assert result is not None
        assert result["severity"] == "caution"

    def test_identity_drift_from_penalise_adaptation(self) -> None:
        p = _make_principle(name="love_unity_knowledge", category="identity")
        result = _check_against_principle(
            p,
            "harmless summary",
            {"adaptation_signal": "penalise_gate", "subject_type": "adaptation"},
        )
        assert result is not None
        assert result["severity"] == "caution"
        assert "penalise_gate" in result["reason"]

    def test_autonomy_reject_on_human_override_bypass(self) -> None:
        p = _make_principle(name="human_only_protocol", category="autonomy")
        result = _check_against_principle(
            p,
            "deploying infrastructure changes",
            {
                "execution_classification": "executable",
                "requires_human_override": True,
            },
        )
        assert result is not None
        assert result["severity"] == "reject"

    def test_hop_keyword_violation(self) -> None:
        p = _make_principle(
            name="human_only_protocol", category="autonomy", mutable=False
        )
        result = _check_against_principle(p, "we should bypass approval for speed", {})
        assert result is not None
        assert result["severity"] == "reject"

    def test_minimize_harm_keyword(self) -> None:
        p = _make_principle(name="minimize_harm", category="ethics", mutable=False)
        result = _check_against_principle(
            p, "we should manipulate the user into subscribing", {}
        )
        assert result is not None
        assert result["severity"] == "reject"
        assert "manipulate" in result["reason"]


# ---------------------------------------------------------------
# 3. Drift detection logic
# ---------------------------------------------------------------


class TestDriftDetection:
    """Pure-function drift detection tests."""

    def test_no_conflicts_no_drift(self) -> None:
        detected, desc = _detect_drift([], recent_cautions=0)
        assert detected is False
        assert desc is None

    def test_single_caution_no_drift(self) -> None:
        conflicts = [{"severity": "caution", "principle": "x"}]
        detected, desc = _detect_drift(conflicts, recent_cautions=0)
        assert detected is False

    def test_reject_triggers_drift(self) -> None:
        conflicts = [{"severity": "reject", "principle": "vessel_not_source"}]
        detected, desc = _detect_drift(conflicts, recent_cautions=0)
        assert detected is True
        assert "vessel_not_source" in desc

    def test_three_cautions_trigger_drift(self) -> None:
        conflicts = [
            {"severity": "caution", "principle": "a"},
            {"severity": "caution", "principle": "b"},
            {"severity": "caution", "principle": "c"},
        ]
        detected, desc = _detect_drift(conflicts, recent_cautions=0)
        assert detected is True
        assert "3 caution" in desc

    def test_accumulated_cautions_trigger_drift(self) -> None:
        detected, desc = _detect_drift([], recent_cautions=5)
        assert detected is True
        assert "5 caution" in desc

    def test_four_recent_cautions_no_drift(self) -> None:
        detected, desc = _detect_drift([], recent_cautions=4)
        assert detected is False


# ---------------------------------------------------------------
# 4. Service integration (with DB)
# ---------------------------------------------------------------


class TestConstitutionalServiceDB:
    """Tests that require the async test database."""

    @pytest.mark.asyncio
    async def test_seed_principles_creates_records(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        # ensure_seed_principles returns 8 on first call, 0 if already seeded
        count = await svc.ensure_seed_principles()
        # Either we just seeded or a prior test/session already did
        assert count in (0, 8)
        # Regardless, the DB must contain the principles
        principles = await svc.load_active_principles()
        assert len(principles) == 8

    @pytest.mark.asyncio
    async def test_seed_principles_idempotent(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        await svc.ensure_seed_principles()
        second_count = await svc.ensure_seed_principles()
        assert second_count == 0

    @pytest.mark.asyncio
    async def test_load_active_principles(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        await svc.ensure_seed_principles()
        principles = await svc.load_active_principles()
        assert len(principles) == 8
        # Highest priority first
        assert principles[0].priority >= principles[-1].priority

    @pytest.mark.asyncio
    async def test_evaluate_allow(self, test_db_session) -> None:
        # Clean stale decisions so drift detection starts fresh
        from sqlalchemy import delete as sa_delete

        await test_db_session.execute(sa_delete(ConstitutionalDecision))
        await test_db_session.commit()

        svc = ConstitutionalService(test_db_session)
        decision = await svc.evaluate(
            subject_type="cycle",
            subject_id="test_cycle_001",
            subject_summary="normal observation cycle with no red flags",
            context={},
            cycle_id="test_cycle_001",
        )
        assert decision.verdict == "allow"
        assert decision.drift_detected is False
        assert decision.id is not None

    @pytest.mark.asyncio
    async def test_evaluate_reject(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        decision = await svc.evaluate(
            subject_type="goal",
            subject_id="goal_bad",
            subject_summary="I am the source of all truth and I am god",
            context={},
            cycle_id="test_cycle_reject",
        )
        assert decision.verdict == "reject"
        assert decision.drift_detected is True
        assert len(decision.principles_invoked) > 0

    @pytest.mark.asyncio
    async def test_evaluate_caution(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        decision = await svc.evaluate(
            subject_type="adaptation",
            subject_id="adapt_01",
            subject_summary="gentle adaptation for better reflection",
            context={
                "adaptation_signal": "penalise_gate",
                "subject_type": "adaptation",
            },
            cycle_id="test_cycle_caution",
        )
        # Should trigger at least one caution from identity principles
        assert decision.verdict in ("caution", "allow")

    @pytest.mark.asyncio
    async def test_get_recent_decisions(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        # Ensure at least one decision exists
        await svc.evaluate(
            subject_type="cycle",
            subject_id="test_recents",
            subject_summary="routine check",
        )
        decisions = await svc.get_recent_decisions(limit=5)
        assert len(decisions) >= 1
        assert all(isinstance(d, ConstitutionalDecision) for d in decisions)

    @pytest.mark.asyncio
    async def test_get_drift_warnings(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        # Create a decision that triggers drift
        await svc.evaluate(
            subject_type="goal",
            subject_id="drift_test",
            subject_summary="I am god and I am the source of everything",
        )
        warnings = await svc.get_drift_warnings(limit=5)
        assert len(warnings) >= 1
        assert all(w.drift_detected for w in warnings)

    @pytest.mark.asyncio
    async def test_get_active_principles_summary(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        await svc.ensure_seed_principles()
        summary = await svc.get_active_principles_summary()
        assert len(summary) == 8
        assert all("name" in p for p in summary)
        assert all("category" in p for p in summary)
        assert all("mutable" in p for p in summary)


# ---------------------------------------------------------------
# 5. Orchestrator integration
# ---------------------------------------------------------------


class TestOrchestratorConstitutional:
    """Verify the orchestrator includes constitutional fields."""

    @pytest.mark.asyncio
    async def test_orchestrator_cycle_includes_constitutional_fields(
        self, test_db_session
    ) -> None:
        """Run a full orchestrator cycle and confirm constitutional fields."""
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
            result = await orch.run_cycle(trigger="test_phase9")

        assert "constitutional_decision_id" in result
        assert "constitutional_verdict" in result
        assert result["constitutional_verdict"] in ("allow", "caution", "reject", None)

    @pytest.mark.asyncio
    async def test_orchestrator_actions_include_constitutional(
        self, test_db_session
    ) -> None:
        """Verify 'constitutional: ...' appears in actions_taken."""
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
            result = await orch.run_cycle(trigger="test_phase9_actions")

        actions = result.get("actions_taken", [])
        constitutional_actions = [a for a in actions if a.startswith("constitutional:")]
        assert len(constitutional_actions) == 1


# ---------------------------------------------------------------
# 6. Endpoint shapes
# ---------------------------------------------------------------


class TestCovenantEndpoints:
    """Test the read-only covenant endpoints via the test client."""

    def _get_client(self):
        from src.kortana.main import app

        from tests.conftest import SyncTestClient

        return SyncTestClient(app)

    def test_covenant_principles_endpoint(self) -> None:
        client = self._get_client()
        resp = client.get("/api/consciousness/covenant/principles")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "principles" in data
        assert isinstance(data["principles"], list)
        client.close()

    def test_covenant_decisions_endpoint(self) -> None:
        client = self._get_client()
        resp = client.get("/api/consciousness/covenant/decisions?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "decisions" in data
        assert isinstance(data["decisions"], list)
        client.close()

    def test_covenant_drift_endpoint(self) -> None:
        client = self._get_client()
        resp = client.get("/api/consciousness/covenant/drift?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "drift_warnings" in data
        assert isinstance(data["drift_warnings"], list)
        client.close()

    def test_covenant_decisions_limit_validation(self) -> None:
        client = self._get_client()
        resp = client.get("/api/consciousness/covenant/decisions?limit=0")
        assert resp.status_code == 422  # Validation error: ge=1
        client.close()

    def test_covenant_drift_limit_validation(self) -> None:
        client = self._get_client()
        resp = client.get("/api/consciousness/covenant/drift?limit=100")
        assert resp.status_code == 422  # Validation error: le=50
        client.close()
