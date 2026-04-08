"""
Tests for HumanOnlyProtocol enums, data classes, and the engine class.
"""

from datetime import datetime

import pytest

from src.kortana.human_only_protocol import (
    DeploymentTask,
    HumanOnlyProtocol,
    TaskClassification,
    TaskStatus,
)


class TestTaskClassification:
    def test_values_exist(self):
        assert TaskClassification.AUTO.value == "auto"
        assert TaskClassification.HO.value == "ho"
        assert TaskClassification.APPROVAL.value == "approval"

    def test_enum_members(self):
        members = list(TaskClassification)
        assert len(members) == 4
        assert TaskClassification.SELF_CORRECTION in members


class TestTaskStatus:
    def test_values_exist(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.WAITING_FOR_HO.value == "waiting_for_ho"
        assert TaskStatus.BLOCKED.value == "blocked"

    def test_enum_members(self):
        members = list(TaskStatus)
        assert len(members) == 6


class TestDeploymentTask:
    def test_basic_creation(self):
        task = DeploymentTask(
            id="test1",
            name="Test Task",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
        )
        assert task.id == "test1"
        assert task.name == "Test Task"
        assert task.classification == TaskClassification.AUTO
        assert task.status == TaskStatus.PENDING
        assert task.command is None
        assert task.description == ""
        assert task.prerequisites == []
        assert task.ho_scaffold is None
        assert task.result is None
        assert task.error is None
        assert isinstance(task.created_at, datetime)
        assert task.completed_at is None

    def test_full_creation(self):
        task = DeploymentTask(
            id="hop_task",
            name="Setup DB",
            classification=TaskClassification.HO,
            status=TaskStatus.WAITING_FOR_HO,
            command="alembic upgrade head",
            description="Run migrations",
            prerequisites=["create_env"],
            ho_scaffold="### Step 1: Do this...",
        )
        assert task.prerequisites == ["create_env"]
        assert task.ho_scaffold == "### Step 1: Do this..."

    def test_defaults_are_independent_between_instances(self):
        t1 = DeploymentTask(
            id="a",
            name="A",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
        )
        t2 = DeploymentTask(
            id="b",
            name="B",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
        )
        t1.prerequisites.append("dep1")
        assert "dep1" not in t2.prerequisites


class TestHumanOnlyProtocolEngine:
    def test_instantiation(self):
        hop = HumanOnlyProtocol()
        assert hop is not None
        assert hop._definitions is not None

    def test_deployment_tasks_defined(self):
        hop = HumanOnlyProtocol()
        assert len(hop._definitions) > 0

    def test_auto_tasks_present(self):
        hop = HumanOnlyProtocol()
        auto_tasks = [
            t for t in hop._definitions.values() if t.classification == TaskClassification.AUTO
        ]
        assert len(auto_tasks) > 0

    def test_ho_tasks_present(self):
        hop = HumanOnlyProtocol()
        ho_tasks = [
            t for t in hop._definitions.values() if t.classification == TaskClassification.HO
        ]
        assert len(ho_tasks) > 0

    def test_approval_tasks_present(self):
        hop = HumanOnlyProtocol()
        approval_tasks = [
            t for t in hop._definitions.values() if t.classification == TaskClassification.APPROVAL
        ]
        assert len(approval_tasks) > 0

    def test_all_tasks_have_id_and_name(self):
        hop = HumanOnlyProtocol()
        for task_key, task in hop._definitions.items():
            assert task.id, f"Task {task_key} missing id"
            assert task.name, f"Task {task_key} missing name"

    def test_known_tasks_exist(self):
        hop = HumanOnlyProtocol()
        assert "run_tests" in hop._definitions
        assert "github_token" in hop._definitions
        assert "start_server" in hop._definitions

    def test_ho_tasks_have_scaffold(self):
        hop = HumanOnlyProtocol()
        ho_tasks = [
            t for t in hop._definitions.values() if t.classification == TaskClassification.HO
        ]
        for t in ho_tasks:
            assert t.ho_scaffold is not None, f"HO task {t.id} missing scaffold"

    def test_auto_tasks_have_commands(self):
        hop = HumanOnlyProtocol()
        auto_tasks_with_commands = [
            t
            for t in hop._definitions.values()
            if t.classification == TaskClassification.AUTO and t.command is not None
        ]
        assert len(auto_tasks_with_commands) > 0

    def test_execute_auto_task_raises_for_unknown(self):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock

        hop = HumanOnlyProtocol()
        mock_db = MagicMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result_mock)

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(hop.execute_auto_task("nonexistent_task_id", mock_db))
        assert exc_info.value.status_code == 404

    def test_get_all_tasks_returns_list(self):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock

        hop = HumanOnlyProtocol()
        mock_db = MagicMock()

        # synchronize_tasks will try to execute + commit, get_all_tasks does two db calls
        empty_result = MagicMock()
        empty_result.scalar_one_or_none.return_value = None
        tasks_result = MagicMock()
        tasks_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[empty_result] * 20 + [tasks_result])
        mock_db.commit = AsyncMock(return_value=None)
        mock_db.add = MagicMock()

        async def run():
            return await hop.get_all_tasks(mock_db)

        tasks = asyncio.run(run())
        assert isinstance(tasks, list)
