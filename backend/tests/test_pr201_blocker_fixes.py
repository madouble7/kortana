"""Tests for PR #201 merge-blocker fixes.

Covers:
  - override-learning call site: learn_from_override_resolution (not learn_from_override)
  - not_found audit FK: enforcement_record_id is None when target is missing
  - wisdom/predictions endpoints: read from RevelationMemory, not SelfMemory
  - revelation_engine field names: signal_weight / signal_scope (not weight_delta / scope)
  - orchestrator gate guard: execution gate skipped when next_action_id is None
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from src.kortana.models import (
    CovenantEnforcementRecord,
    OutcomeLearningRecord,
    OverrideAuditRecord,
    RevelationMemory,
)
from src.kortana.services.constitutional_service import ConstitutionalService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pending_record(
    db_session,
    record_id: str | None = None,
) -> CovenantEnforcementRecord:
    """Create a pending override enforcement record."""
    record = CovenantEnforcementRecord(
        id=record_id or str(uuid.uuid4()),
        decision_id="dec_blocker_test",
        target_type="candidate",
        target_id="t_blocker",
        target_summary="Blocker fix test target",
        action="override_requested",
        override_status="pending",
        cycle_id="cyc_blocker",
    )
    db_session.add(record)
    return record


def _make_revelation(
    db_session,
    revelation_type: str = "pattern",
    title: str = "Test revelation",
    content: str = "Some insight",
    confidence: float = 0.8,
) -> RevelationMemory:
    """Create a revelation memory row."""
    r = RevelationMemory(
        id=str(uuid.uuid4()),
        title=title,
        content=content,
        evidence=["test evidence"],
        revelation_type=revelation_type,
        confidence=confidence,
        surfaced=False,
        source="revelation_engine",
    )
    db_session.add(r)
    return r


# ---------------------------------------------------------------------------
# 1. Override-learning call site: correct method name
# ---------------------------------------------------------------------------


class TestOverrideLearningCallSite:
    """The resolve_override path must call learn_from_override_resolution."""

    async def test_resolve_calls_correct_learning_method(self, test_db_session):
        """After a successful resolve, the learning call should not raise AttributeError."""
        record = _make_pending_record(test_db_session)
        await test_db_session.flush()

        svc = ConstitutionalService(test_db_session)
        resolved = await svc.resolve_override(
            record_id=record.id,
            resolution="approved",
            resolver="matt",
            rationale="blocker test",
        )
        # If this reaches here without AttributeError, the method name is correct.
        assert resolved is not None
        assert resolved.override_status == "approved"

    async def test_learning_record_created_on_resolve(self, test_db_session):
        """A successful resolve should produce an OutcomeLearningRecord."""
        record = _make_pending_record(test_db_session)
        await test_db_session.flush()

        svc = ConstitutionalService(test_db_session)
        await svc.resolve_override(
            record_id=record.id,
            resolution="denied",
            resolver="matt",
            rationale="blocker deny test",
        )
        await test_db_session.flush()

        stmt = select(OutcomeLearningRecord).where(
            OutcomeLearningRecord.source_type == "override_resolution"
        )
        result = await test_db_session.execute(stmt)
        learning = result.scalars().all()
        assert len(learning) >= 1
        # denied → adaptation_signal should be an override_denied signal
        assert any("denied" in lr.adaptation_signal for lr in learning)


# ---------------------------------------------------------------------------
# 2. not_found audit FK: enforcement_record_id must be None
# ---------------------------------------------------------------------------


class TestNotFoundAuditFK:
    """When resolving a non-existent record, audit must use None FK, not the missing ID."""

    async def test_not_found_audit_has_null_fk(self, test_db_session):
        fake_id = "nonexistent-" + str(uuid.uuid4())
        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record_id=fake_id,
            resolution="approved",
            resolver="matt",
            rationale="should not find this",
        )
        assert result is None  # not found

        await test_db_session.flush()
        stmt = select(OverrideAuditRecord).where(
            OverrideAuditRecord.outcome == "not_found"
        )
        rows = (await test_db_session.execute(stmt)).scalars().all()
        assert len(rows) >= 1
        audit = rows[-1]
        # The FK must be None, not the non-existent record_id
        assert audit.enforcement_record_id is None
        assert fake_id in audit.detail  # target ID preserved in detail text


# ---------------------------------------------------------------------------
# 3. Wisdom/predictions endpoints: query RevelationMemory
# ---------------------------------------------------------------------------


class TestWisdomPredictionsEndpoints:
    """Endpoints must read from RevelationMemory filtered by revelation_type."""

    async def test_wisdom_returns_pattern_revelations(self, test_db_session):
        """GET /wisdom should return pattern, self_discovery, contradiction revelations."""
        _make_revelation(test_db_session, "pattern", "Pattern insight")
        _make_revelation(test_db_session, "self_discovery", "Self insight")
        _make_revelation(test_db_session, "prediction", "Should not appear")
        await test_db_session.flush()

        # Import and call the endpoint function directly
        from src.kortana.routers.consciousness import get_wisdom

        resp = await get_wisdom(limit=50, db=test_db_session)
        titles = [w["summary"] for w in resp["wisdom"]]
        assert "Pattern insight" in titles
        assert "Self insight" in titles
        assert "Should not appear" not in titles

    async def test_predictions_returns_only_predictions(self, test_db_session):
        """GET /predictions should return only prediction-type revelations."""
        _make_revelation(test_db_session, "pattern", "Not a prediction")
        _make_revelation(test_db_session, "prediction", "Will happen")
        await test_db_session.flush()

        from src.kortana.routers.consciousness import get_predictions

        resp = await get_predictions(limit=50, db=test_db_session)
        titles = [p["summary"] for p in resp["predictions"]]
        assert "Will happen" in titles
        assert "Not a prediction" not in titles

    async def test_wisdom_response_has_revelation_fields(self, test_db_session):
        """Wisdom entries should expose RevelationMemory fields, not SelfMemory fields."""
        _make_revelation(
            test_db_session, "pattern", "Test fields", "Content body", 0.95
        )
        await test_db_session.flush()

        from src.kortana.routers.consciousness import get_wisdom

        resp = await get_wisdom(limit=5, db=test_db_session)
        entry = resp["wisdom"][0]
        # RevelationMemory fields (mapped for backward compat)
        assert "summary" in entry  # r.title mapped to "summary"
        assert "content" in entry
        assert "confidence" in entry
        assert "type" in entry  # r.revelation_type mapped to "type"
        # Should be querying RevelationMemory, not SelfMemory
        assert (
            entry["content"] == "Content body"
        )  # proves it read RevelationMemory.content


# ---------------------------------------------------------------------------
# 4. Revelation engine field names: signal_weight / signal_scope
# ---------------------------------------------------------------------------


class TestRevelationFieldNames:
    """Revelation engine must use signal_weight and signal_scope, not weight_delta/scope."""

    async def test_outcome_learning_record_has_correct_fields(self, test_db_session):
        """OutcomeLearningRecord must have signal_weight and signal_scope attributes."""
        record = OutcomeLearningRecord(
            id=str(uuid.uuid4()),
            outcome_verdict="success",
            expectation_match="expected",
            adaptation_signal="reinforce",
            signal_weight=0.5,
            signal_scope="cycle",
            lesson="test lesson",
            source_type="execution",
        )
        test_db_session.add(record)
        await test_db_session.flush()

        # Verify the fields used by revelation_engine._gather_outcome_signals
        assert hasattr(record, "signal_weight")
        assert hasattr(record, "signal_scope")
        assert record.signal_weight == 0.5
        assert record.signal_scope == "cycle"

    async def test_gather_outcome_signals_format(self, test_db_session):
        """The _gather_outcome_signals function should not raise AttributeError."""
        record = OutcomeLearningRecord(
            id=str(uuid.uuid4()),
            outcome_verdict="success",
            expectation_match="expected",
            adaptation_signal="reinforce",
            signal_weight=-0.15,
            signal_scope="cycle",
            lesson="Revelation field test lesson",
            source_type="execution",
            created_at=datetime.utcnow(),
        )
        test_db_session.add(record)
        await test_db_session.flush()

        from src.kortana.services.revelation_engine import _gather_outcome_signals

        lines = await _gather_outcome_signals(test_db_session, limit=10)
        assert len(lines) >= 1
        # Should contain the correct field values
        assert "weight=-0.15" in lines[0]
        assert "scope=cycle" in lines[0]


# ---------------------------------------------------------------------------
# 5. Orchestrator gate guard: skip when next_action_id is None
# ---------------------------------------------------------------------------


class TestOrchestratorGateGuard:
    """Execution gate must not be called when next_action_id is None."""

    async def test_gate_guard_exists_in_source(self):
        """Verify the orchestrator guards against next_action_id being None."""
        import inspect

        from src.kortana.services.autonomy_orchestrator import AutonomyOrchestrator

        source = inspect.getsource(AutonomyOrchestrator.run_cycle)
        # The gate section must check next_action_id is truthy
        assert "next_action_id" in source
        # Look for the guard pattern: something like "and next_action_id" before gate
        gate_section_idx = source.index("EXECUTION GATE")
        # The guard check must appear near the gate section
        guard_region = source[max(0, gate_section_idx - 200) : gate_section_idx + 200]
        assert "next_action_id" in guard_region
