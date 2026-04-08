from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from src.kortana.autonomous_monitor import AutonomousSystemMonitor


class _DummySessionScope:
    def __init__(self, session: Any) -> None:
        self._session = session

    async def __aenter__(self) -> Any:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _RecordingPatcher:
    calls: list[dict[str, Any]] = []

    def __init__(self, db: Any) -> None:
        self.db = db

    async def attempt_auto_fix(
        self,
        *,
        error_type: str,
        error_message: str,
        target_file: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        self.__class__.calls.append(
            {
                "db": self.db,
                "error_type": error_type,
                "error_message": error_message,
                "target_file": target_file,
                "context": context or {},
            }
        )
        return True


def _make_monitor() -> AutonomousSystemMonitor:
    _RecordingPatcher.calls = []
    return AutonomousSystemMonitor(
        db_session_factory=lambda: _DummySessionScope(SimpleNamespace(name="db")),
        patcher_cls=_RecordingPatcher,
    )


def test_normalize_patch_target_file_accepts_backend_and_src_paths() -> None:
    assert (
        AutonomousSystemMonitor._normalize_patch_target_file("src/kortana/main.py")
        == "backend/src/kortana/main.py"
    )
    assert (
        AutonomousSystemMonitor._normalize_patch_target_file(
            r"C:\kortana\backend\src\kortana\services\demo.py"
        )
        == "backend/src/kortana/services/demo.py"
    )
    assert (
        AutonomousSystemMonitor._normalize_patch_target_file("frontend/app.tsx")
        is None
    )


@pytest.mark.asyncio
async def test_identify_improvements_marks_patchable_recurring_errors() -> None:
    monitor = _make_monitor()
    monitor.metrics["errors_encountered"] = [
        {
            "type": "AssertionError",
            "message": "expected 'new' but got 'old'",
            "target_file": "src/kortana/services/sample.py",
        }
        for _ in range(6)
    ]

    improvements = await monitor.identify_improvements()

    top_issue = improvements[0]
    assert top_issue["type"] == "error_reduction"
    assert top_issue["impact"] == "high"
    assert top_issue["patchable"] is True
    assert top_issue["target_file"] == "backend/src/kortana/services/sample.py"
    assert "expected 'new'" in top_issue["sample_error_message"]


@pytest.mark.asyncio
async def test_initiate_self_optimization_queues_patch_for_actionable_error() -> None:
    monitor = _make_monitor()
    monitor.metrics["errors_encountered"] = [
        {
            "type": "AssertionError",
            "message": "expected 'new' but got 'old'",
            "target_file": "backend/src/kortana/services/sample.py",
        }
        for _ in range(6)
    ]

    result = await monitor.initiate_self_optimization()
    pending = tuple(monitor._background_patch_tasks)
    if pending:
        await asyncio.gather(*pending)

    assert result["patch_candidate_queued"] is True
    assert len(_RecordingPatcher.calls) == 1
    assert _RecordingPatcher.calls[0]["error_type"] == "AssertionError"
    assert _RecordingPatcher.calls[0]["target_file"] == (
        "backend/src/kortana/services/sample.py"
    )
    assert _RecordingPatcher.calls[0]["context"]["source"] == "autonomous_monitor"


@pytest.mark.asyncio
async def test_initiate_self_optimization_skips_error_without_target_file() -> None:
    monitor = _make_monitor()
    monitor.metrics["errors_encountered"] = [
        {"type": "AssertionError", "message": "expected 'new' but got 'old'"}
        for _ in range(6)
    ]

    result = await monitor.initiate_self_optimization()

    assert result["patch_candidate_queued"] is False
    assert _RecordingPatcher.calls == []
