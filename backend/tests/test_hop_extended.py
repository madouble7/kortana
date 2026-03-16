"""
Extended tests for HumanOnlyProtocol async engine methods and router endpoints.
Covers the uncovered lines from human_only_protocol.py.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.human_only_protocol import (
    HumanOnlyProtocol,
    TaskClassification,
    TaskStatus,
)


def make_mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    db.rollback = AsyncMock()
    return db


def make_task_mock(
    task_id="task-001",
    title="Test Task",
    classification="auto",
    status="pending",
    command="python -m pytest",
    ho_scaffold=None,
    completed_at=None,
):
    t = MagicMock()
    t.id = task_id
    t.title = title
    t.classification = classification
    t.status = status
    t.command = command
    t.ho_scaffold = ho_scaffold
    t.completed_at = completed_at
    t.started_at = None
    t.result = None
    t.error = None
    return t


class TestHOPGetStatus:
    """Tests for HumanOnlyProtocol.get_status()"""

    def test_get_status_empty_db(self):
        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()
        # synchronize_tasks finds all tasks "already exist" in DB (non-null return)
        existing = MagicMock()
        existing.scalar_one_or_none.return_value = MagicMock()  # Simulate existing task
        all_tasks = MagicMock()
        all_tasks.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[existing] * 20 + [all_tasks])
        mock_db.commit = AsyncMock()

        async def run():
            return await hop.get_status(mock_db)

        result = asyncio.run(run())
        assert "status" in result
        assert "tasks" in result
        assert "autonomy_progress" in result

    def test_get_status_with_tasks(self):
        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()

        auto_task = make_task_mock(
            "t1", "Run Tests", classification="auto", status="completed"
        )
        ho_task = make_task_mock(
            "t2", "Config DB", classification="ho", status="pending", command=None
        )
        approval_task = make_task_mock(
            "t3", "Deploy", classification="approval", status="pending"
        )

        existing = MagicMock()
        existing.scalar_one_or_none.return_value = MagicMock()
        all_tasks = MagicMock()
        all_tasks.scalars.return_value.all.return_value = [
            auto_task,
            ho_task,
            approval_task,
        ]
        mock_db.execute = AsyncMock(side_effect=[existing] * 20 + [all_tasks])
        mock_db.commit = AsyncMock()

        async def run():
            return await hop.get_status(mock_db)

        result = asyncio.run(run())
        assert result["autonomy_progress"]["auto_complete"] == 1
        assert result["autonomy_progress"]["ho_total"] == 1


class TestHOPGetNextHOTask:
    """Tests for HumanOnlyProtocol.get_next_ho_task()"""

    def test_get_next_ho_task_when_none(self):
        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()

        existing = MagicMock()
        existing.scalar_one_or_none.return_value = MagicMock()
        all_tasks = MagicMock()
        all_tasks.scalars.return_value.all.return_value = []  # No tasks
        mock_db.execute = AsyncMock(side_effect=[existing] * 20 + [all_tasks])
        mock_db.commit = AsyncMock()

        async def run():
            return await hop.get_next_ho_task(mock_db)

        result = asyncio.run(run())
        assert result is None

    def test_get_next_ho_task_returns_first_pending(self):
        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()

        ho_completed = make_task_mock(
            "t2", "Old Task", classification="ho", status="completed"
        )
        ho_pending = make_task_mock(
            "t3", "New Task", classification="ho", status="pending"
        )

        existing = MagicMock()
        existing.scalar_one_or_none.return_value = MagicMock()
        all_tasks = MagicMock()
        all_tasks.scalars.return_value.all.return_value = [ho_completed, ho_pending]
        mock_db.execute = AsyncMock(side_effect=[existing] * 20 + [all_tasks])
        mock_db.commit = AsyncMock()

        async def run():
            return await hop.get_next_ho_task(mock_db)

        result = asyncio.run(run())
        assert result is not None
        assert result.id == "t3"


class TestHOPCompleteHOTask:
    """Tests for HumanOnlyProtocol.complete_ho_task()"""

    def test_complete_ho_task_not_found(self):
        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result_mock)

        from fastapi import HTTPException

        async def run():
            return await hop.complete_ho_task("nonexistent_id", mock_db)

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(run())
        assert exc_info.value.status_code == 404

    def test_complete_ho_task_success(self):
        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()
        mock_task = make_task_mock(
            "t1", "Token Setup", classification="ho", status="pending"
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_task
        mock_db.execute = AsyncMock(return_value=result_mock)
        mock_db.commit = AsyncMock()

        async def run():
            return await hop.complete_ho_task("t1", mock_db)

        result = asyncio.run(run())
        assert result["status"] == "completed"
        assert mock_task.status == TaskStatus.COMPLETED.value


class TestHOPExecuteAutoTask:
    """Tests for edge cases in execute_auto_task"""

    def test_execute_auto_task_wrong_classification(self):
        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()
        mock_task = make_task_mock(
            "t1", "HO Task", classification="ho", status="pending"
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_task
        mock_db.execute = AsyncMock(return_value=result_mock)

        from fastapi import HTTPException

        async def run():
            return await hop.execute_auto_task("t1", mock_db)

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(run())
        assert exc_info.value.status_code == 400

    def test_execute_auto_task_no_command(self):
        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()
        mock_task = make_task_mock(
            "t1", "Task", classification="auto", status="pending", command=None
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_task
        mock_db.execute = AsyncMock(return_value=result_mock)
        mock_db.commit = AsyncMock()

        async def run():
            return await hop.execute_auto_task("t1", mock_db)

        result = asyncio.run(run())
        assert result["status"] == "completed"
        assert result["message"] == "No command needed"

    def test_execute_auto_task_unsafe_command_blocked(self):
        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()
        mock_task = make_task_mock(
            "t1",
            "Dangerous",
            classification="auto",
            status="pending",
            command="rm -rf /",  # Not in safe_commands list
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_task
        mock_db.execute = AsyncMock(return_value=result_mock)
        mock_db.commit = AsyncMock()

        async def run():
            return await hop.execute_auto_task("t1", mock_db)

        result = asyncio.run(run())
        assert result["status"] == "failed"
        assert "Unauthorized" in result["error"]

    def test_execute_auto_task_subprocess_success(self):
        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()
        # Use a task with a command from the safe list
        safe_task = list(hop._definitions.values())[0]  # First task definition
        if not safe_task.command:
            # Pick one that has a command
            for td in hop._definitions.values():
                if td.command:
                    safe_task = td
                    break

        mock_task = make_task_mock(
            safe_task.id,
            safe_task.name,
            classification="auto",
            status="pending",
            command=safe_task.command,
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_task
        mock_db.execute = AsyncMock(return_value=result_mock)
        mock_db.commit = AsyncMock()

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Tests passed"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc):

            async def run():
                return await hop.execute_auto_task(safe_task.id, mock_db)

            result = asyncio.run(run())
        assert result["status"] == "completed"
        assert "Tests passed" in result["output"]

    def test_execute_auto_task_subprocess_failure(self):
        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()

        # Use task with known safe command
        for task_id, task_def in hop._definitions.items():
            if task_def.command and task_def.classification == TaskClassification.AUTO:
                break

        mock_task = make_task_mock(
            task_id,
            task_def.name,
            classification="auto",
            status="pending",
            command=task_def.command,
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_task
        mock_db.execute = AsyncMock(return_value=result_mock)
        mock_db.commit = AsyncMock()

        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "Error occurred"

        with patch("subprocess.run", return_value=mock_proc):

            async def run():
                return await hop.execute_auto_task(task_id, mock_db)

            result = asyncio.run(run())
        assert result["status"] == "failed"

    def test_execute_auto_task_subprocess_timeout(self):
        import subprocess

        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()

        for task_id, task_def in hop._definitions.items():
            if task_def.command and task_def.classification == TaskClassification.AUTO:
                break

        mock_task = make_task_mock(
            task_id,
            task_def.name,
            classification="auto",
            status="pending",
            command=task_def.command,
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_task
        mock_db.execute = AsyncMock(return_value=result_mock)
        mock_db.commit = AsyncMock()

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 300)):

            async def run():
                return await hop.execute_auto_task(task_id, mock_db)

            result = asyncio.run(run())
        assert result["status"] == "failed"
        assert "Timeout" in result["error"]


class TestHOPRunAutonomousCycle:
    """Tests for run_autonomous_cycle"""

    def test_run_autonomous_cycle_no_auto_tasks(self):
        hop = HumanOnlyProtocol()
        mock_db = make_mock_db()

        ho_task = make_task_mock("t1", "HO Task", classification="ho", status="pending")

        existing = MagicMock()
        existing.scalar_one_or_none.return_value = MagicMock()
        all_tasks = MagicMock()
        all_tasks.scalars.return_value.all.return_value = [ho_task]
        mock_db.execute = AsyncMock(side_effect=[existing] * 20 + [all_tasks] * 5)
        mock_db.commit = AsyncMock()

        async def run():
            return await hop.run_autonomous_cycle(mock_db)

        result = asyncio.run(run())
        assert result["executed"] == []
        assert "pending_ho" in result


class TestHOPRouterEndpoints:
    """Tests for the FastAPI router endpoints"""

    @pytest.fixture
    def client(self):
        from src.kortana.main import app
        from tests.conftest import SyncTestClient

        return SyncTestClient(app)

    def test_protocol_health_endpoint(self, client):
        resp = client.get("/api/protocol/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "human_only_protocol"

    def test_protocol_status_endpoint(self, client):
        resp = client.get("/api/protocol/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data

    def test_get_auto_tasks_endpoint(self, client):
        resp = client.get("/api/protocol/auto/tasks")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_execute_nonexistent_auto_task(self, client):
        resp = client.post("/api/protocol/auto/execute/nonexistent-task-xyz")
        assert resp.status_code in (404, 422, 500)

    def test_run_autonomous_cycle_endpoint(self, client):
        resp = client.post("/api/protocol/auto/cycle")
        assert resp.status_code == 200
        data = resp.json()
        assert "executed" in data

    def test_get_next_ho_task_endpoint(self, client):
        resp = client.get("/api/protocol/ho/next")
        assert resp.status_code == 200
        data = resp.json()
        assert "task" in data or "message" in data

    def test_get_all_ho_tasks_endpoint(self, client):
        resp = client.get("/api/protocol/ho/all")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_complete_nonexistent_ho_task(self, client):
        resp = client.post("/api/protocol/ho/complete/nonexistent-ho-task-xyz")
        assert resp.status_code in (404, 422, 500)
