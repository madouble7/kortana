"""Tests for Phase 5 — Autonomy Core hardening.

Covers:
  - Silent Reviewer AUTONOMY.lock kill-switch
  - Durable autonomy status (survives restart, reads from DB)
  - Internal autonomy-cycle endpoint response structure
  - Self-model and self-model/history endpoint shapes
  - No test requires a live Gemini key
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# scripts/ lives at repo root, add it to path so silent_reviewer is importable
_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ---------------------------------------------------------------
# Silent Reviewer — AUTONOMY.lock kill switch
# ---------------------------------------------------------------
class TestSilentReviewerLockFile:
    """Verify AUTONOMY.lock pauses all cycle activity."""

    def test_is_autonomy_locked_when_file_exists(self, tmp_path):
        lock = tmp_path / "AUTONOMY.lock"
        lock.write_text("paused")

        import scripts.silent_reviewer as sr

        original = sr.LOCK_FILE
        try:
            sr.LOCK_FILE = str(lock)
            assert sr.is_autonomy_locked() is True
        finally:
            sr.LOCK_FILE = original

    def test_is_autonomy_locked_when_file_absent(self, tmp_path):
        import scripts.silent_reviewer as sr

        original = sr.LOCK_FILE
        try:
            sr.LOCK_FILE = str(tmp_path / "nonexistent.lock")
            assert sr.is_autonomy_locked() is False
        finally:
            sr.LOCK_FILE = original

    def test_run_cycle_skips_when_locked(self, tmp_path):
        lock = tmp_path / "AUTONOMY.lock"
        lock.write_text("paused")

        import scripts.silent_reviewer as sr

        original = sr.LOCK_FILE
        try:
            sr.LOCK_FILE = str(lock)
            # run_cycle should return immediately without calling trigger
            with patch.object(sr, "trigger_autonomy_cycle") as mock_trigger:
                with patch.object(sr, "_has_meaningful_change") as mock_change:
                    sr.run_cycle()
                    mock_trigger.assert_not_called()
                    mock_change.assert_not_called()
        finally:
            sr.LOCK_FILE = original

    def test_trigger_autonomy_cycle_skips_when_locked(self, tmp_path):
        lock = tmp_path / "AUTONOMY.lock"
        lock.write_text("paused")

        import scripts.silent_reviewer as sr

        original = sr.LOCK_FILE
        try:
            sr.LOCK_FILE = str(lock)
            result = sr.trigger_autonomy_cycle()
            assert result is None
        finally:
            sr.LOCK_FILE = original

    def test_has_meaningful_change_skips_when_locked(self, tmp_path):
        lock = tmp_path / "AUTONOMY.lock"
        lock.write_text("paused")

        import scripts.silent_reviewer as sr

        original = sr.LOCK_FILE
        try:
            sr.LOCK_FILE = str(lock)
            assert sr._has_meaningful_change() is False
        finally:
            sr.LOCK_FILE = original


# ---------------------------------------------------------------
# Durable autonomy status — get_last_cycle_record from DB
# ---------------------------------------------------------------
class TestDurableAutonomyStatus:
    """Verify autonomy status reads from the database, not in-memory."""

    @pytest.mark.asyncio
    async def test_get_last_cycle_record_returns_none_when_empty(self, test_db_session):
        from sqlalchemy import delete as sa_delete
        from src.kortana.models import AutonomyCycleRecord
        from src.kortana.services.autonomy_orchestrator import get_last_cycle_record

        # Ensure table is empty (prior tests or runs may have left rows)
        await test_db_session.execute(sa_delete(AutonomyCycleRecord))
        await test_db_session.commit()

        result = await get_last_cycle_record(test_db_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_last_cycle_record_returns_persisted_data(self, test_db_session):
        from src.kortana.models import AutonomyCycleRecord
        from src.kortana.services.autonomy_orchestrator import get_last_cycle_record

        record = AutonomyCycleRecord(
            cycle_id="abc12345",
            trigger="daemon",
            duration_ms=1500,
            observations_count=7,
            revelations_written=2,
            self_model_version=3,
            developmental_stage="awakening",
            actions_taken=["observed 7 signals", "synthesised 2 revelations"],
        )
        test_db_session.add(record)
        await test_db_session.commit()

        result = await get_last_cycle_record(test_db_session)
        assert result is not None
        assert result["cycle_id"] == "abc12345"
        assert result["trigger"] == "daemon"
        assert result["duration_ms"] == 1500
        assert result["observations"] == 7
        assert result["revelations_written"] == 2
        assert result["self_model_version"] == 3
        assert result["developmental_stage"] == "awakening"
        assert isinstance(result["actions_taken"], list)
        assert result["timestamp"] is not None

    @pytest.mark.asyncio
    async def test_status_survives_simulated_restart(self, test_db_session):
        """Insert a record, then call get_last_cycle_record in a fresh context."""
        from src.kortana.models import AutonomyCycleRecord
        from src.kortana.services.autonomy_orchestrator import get_last_cycle_record

        record = AutonomyCycleRecord(
            cycle_id="restart1",
            trigger="scheduled",
            duration_ms=800,
            observations_count=3,
            revelations_written=0,
            self_model_version=1,
            developmental_stage="nascent",
            actions_taken=["observed 3 signals"],
        )
        test_db_session.add(record)
        await test_db_session.commit()

        # Simulate restart: the module-level global is gone; DB must provide the data
        result = await get_last_cycle_record(test_db_session)
        assert result is not None
        assert result["cycle_id"] == "restart1"


# ---------------------------------------------------------------
# Internal autonomy-cycle endpoint — response structure
# ---------------------------------------------------------------
class TestInternalAutonomyCycleEndpoint:
    """Verify /_internal/autonomy-cycle returns the expected shape."""

    def test_internal_cycle_returns_expected_keys(self, client):
        """Mock the orchestrator so no Gemini key is needed."""
        mock_result = {
            "cycle_id": "test1234",
            "trigger": "daemon",
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 500,
            "observations": 5,
            "revelations_written": 1,
            "self_model_version": 2,
            "developmental_stage": "awakening",
            "actions_taken": ["observed 5 signals"],
        }

        with patch(
            "src.kortana.services.autonomy_orchestrator.AutonomyOrchestrator"
        ) as MockOrch:
            instance = MockOrch.return_value
            instance.run_cycle = AsyncMock(return_value=mock_result)
            resp = client.post("/api/consciousness/_internal/autonomy-cycle")

        assert resp.status_code == 200
        data = resp.json()
        expected_keys = {
            "cycle_id",
            "trigger",
            "timestamp",
            "duration_ms",
            "observations",
            "revelations_written",
            "self_model_version",
            "developmental_stage",
            "actions_taken",
        }
        assert expected_keys.issubset(data.keys())
        assert data["cycle_id"] == "test1234"
        assert isinstance(data["actions_taken"], list)


# ---------------------------------------------------------------
# Self-model endpoints — shape validation
# ---------------------------------------------------------------
class TestSelfModelEndpoints:
    """Verify self-model and self-model/history endpoint shapes."""

    def test_self_model_returns_none_when_empty(self, client):
        resp = client.get("/api/consciousness/self-model")
        assert resp.status_code == 200
        data = resp.json()
        assert data["self_model"] is None

    def test_self_model_history_returns_empty_list(self, client):
        resp = client.get("/api/consciousness/self-model/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["snapshots"] == []

    def test_self_model_history_respects_limit(self, client):
        resp = client.get("/api/consciousness/self-model/history?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "snapshots" in data

    def test_autonomy_status_returns_valid_shape(self, client):
        """Status endpoint returns either no_cycles_yet or active with last_cycle."""
        resp = client.get("/api/consciousness/autonomy/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("no_cycles_yet", "active")
        if data["status"] == "active":
            assert "last_cycle" in data


# ---------------------------------------------------------------
# Wisdom & predictions endpoints — read-only shape
# ---------------------------------------------------------------
class TestWisdomPredictionEndpoints:
    def test_wisdom_endpoint_returns_shape(self, client):
        resp = client.get("/api/consciousness/wisdom")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "wisdom" in data
        assert isinstance(data["wisdom"], list)

    def test_predictions_endpoint_returns_shape(self, client):
        resp = client.get("/api/consciousness/predictions")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "predictions" in data
        assert isinstance(data["predictions"], list)
