"""Tests for routers/task_queue.py - Task queue management"""
import pytest

from src.kortana.routers.task_queue import (
    Task,
    parse_covenant_tasks,
    slugify,
    task_queue,
)


@pytest.fixture(autouse=True)
def reset_task_queue():
    """Clear task queue before each test"""
    task_queue.clear()
    yield
    task_queue.clear()


@pytest.fixture
def client():
    from src.kortana.main import app
    from tests.conftest import SyncTestClient

    return SyncTestClient(app)


class TestSlugify:
    def test_lowercase(self):
        assert slugify("Hello World") == "hello-world"

    def test_replaces_special_chars(self):
        assert slugify("Fix: Bug #123!") == "fix-bug-123"

    def test_strips_leading_trailing_dashes(self):
        assert slugify("  test  ") == "test"

    def test_consecutive_special_chars(self):
        assert slugify("a  b") == "a-b"

    def test_simple_slug(self):
        assert slugify("add-feature") == "add-feature"

    def test_numbers_preserved(self):
        result = slugify("task 42 done")
        assert "42" in result


class TestParseCovenantTasks:
    def test_returns_empty_when_file_missing(self):
        tasks = parse_covenant_tasks()
        assert isinstance(tasks, list)
        # Either empty (no file) or list of Task objects
        for t in tasks:
            assert isinstance(t, Task)

    def test_returns_empty_list_on_error(self, tmp_path, monkeypatch):
        from src.kortana.config import get_settings

        settings = get_settings()
        monkeypatch.setattr(settings, "REPO_ROOT", str(tmp_path))
        tasks = parse_covenant_tasks()
        assert tasks == []

    def test_parses_yaml_frontmatter(self, tmp_path, monkeypatch):
        from src.kortana.config import get_settings

        settings = get_settings()
        monkeypatch.setattr(settings, "REPO_ROOT", str(tmp_path))

        covenant_file = tmp_path / "COVENANT_INDEX.md"
        covenant_file.write_text(
            """---
tasks:
  - id: task-001
    name: Fix Login Bug
    description: Fix the authentication issue
    status: pending
  - id: task-002
    name: Add Tests
    status: completed
---
# Covenant Index
"""
        )

        tasks = parse_covenant_tasks()
        assert len(tasks) == 2
        assert tasks[0].id == "task-001"
        assert tasks[0].name == "Fix Login Bug"
        assert tasks[1].status == "completed"

    def test_parses_file_without_tasks_key(self, tmp_path, monkeypatch):
        from src.kortana.config import get_settings

        settings = get_settings()
        monkeypatch.setattr(settings, "REPO_ROOT", str(tmp_path))

        covenant_file = tmp_path / "COVENANT_INDEX.md"
        covenant_file.write_text(
            """---
version: 1.0
---
# No tasks here
"""
        )
        tasks = parse_covenant_tasks()
        assert tasks == []


class TestTaskQueueRouterListTasks:
    def test_list_empty_queue(self, client):
        resp = client.get("/api/task-queue/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["tasks"] == []

    def test_list_with_tasks(self, client):
        task_queue["t1"] = Task(id="t1", name="Task One")
        resp = client.get("/api/task-queue/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1


class TestTaskQueueRouterAddTask:
    def test_add_task_via_post(self, client):
        resp = client.post("/api/task-queue/", json={"name": "My Task"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "My Task"
        assert data["status"] == "pending"
        assert "created_at" in data

    def test_add_task_missing_name_returns_400(self, client):
        resp = client.post("/api/task-queue/", json={})
        assert resp.status_code == 400

    def test_add_task_with_description(self, client):
        resp = client.post(
            "/api/task-queue/",
            json={
                "name": "Refactor Code",
                "description": "Clean up the auth module",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "Clean up the auth module"


class TestTaskQueueRouterQueueEndpoint:
    def test_queue_task_via_queue_endpoint(self, client):
        resp = client.post(
            "/api/task-queue/queue",
            json={
                "id": "t42",
                "name": "Queued Task",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert data["task"]["id"] == "t42"

    def test_queue_duplicate_task_returns_400(self, client):
        task_queue["t42"] = Task(id="t42", name="Existing")
        resp = client.post(
            "/api/task-queue/queue", json={"id": "t42", "name": "Duplicate"}
        )
        assert resp.status_code == 400


class TestTaskQueueRouterGetTask:
    def test_get_existing_task(self, client):
        task_queue["t5"] = Task(id="t5", name="Task Five")
        resp = client.get("/api/task-queue/t5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "t5"

    def test_get_nonexistent_task_returns_404(self, client):
        resp = client.get("/api/task-queue/nonexistent-999")
        assert resp.status_code == 404


class TestTaskQueueRouterDeleteTask:
    def test_delete_existing_task(self, client):
        task_queue["del1"] = Task(id="del1", name="To Delete")
        resp = client.delete("/api/task-queue/del1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "deleted"
        assert "del1" not in task_queue

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/api/task-queue/doesnotexist")
        assert resp.status_code == 404


class TestTaskQueueRouterUpdateStatus:
    def test_update_to_valid_status(self, client):
        task_queue["t7"] = Task(id="t7", name="Task Seven")
        resp = client.post("/api/task-queue/t7/status", json={"status": "completed"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"

    def test_update_to_invalid_status_returns_400(self, client):
        task_queue["t8"] = Task(id="t8", name="Task Eight")
        resp = client.post(
            "/api/task-queue/t8/status", json={"status": "invalid_status"}
        )
        assert resp.status_code == 400

    def test_update_nonexistent_task_returns_404(self, client):
        resp = client.post(
            "/api/task-queue/nonexistent/status", json={"status": "completed"}
        )
        assert resp.status_code == 404

    def test_all_valid_statuses(self, client):
        for status in ["pending", "in_progress", "completed", "failed"]:
            task_queue["ts"] = Task(id="ts", name="Test")
            resp = client.post("/api/task-queue/ts/status", json={"status": status})
            assert resp.status_code == 200
            assert task_queue["ts"].status == status


class TestTaskQueueRouterSyncCovenant:
    def test_sync_covenant_returns_status(self, client, monkeypatch):
        from unittest.mock import patch

        with patch(
            "src.kortana.routers.task_queue.parse_covenant_tasks", return_value=[]
        ):
            resp = client.post("/api/task-queue/sync-covenant")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "synced"

    def test_sync_covenant_queues_tasks(self, client):
        from unittest.mock import patch

        mock_tasks = [
            Task(id="cov1", name="Covenant Task 1"),
            Task(id="cov2", name="Covenant Task 2"),
        ]
        with patch(
            "src.kortana.routers.task_queue.parse_covenant_tasks",
            return_value=mock_tasks,
        ):
            resp = client.post("/api/task-queue/sync-covenant")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2

    def test_sync_covenant_skips_existing_tasks(self, client):
        from unittest.mock import patch

        task_queue["cov1"] = Task(id="cov1", name="Already exists")
        mock_tasks = [Task(id="cov1", name="Covenant Task 1")]
        with patch(
            "src.kortana.routers.task_queue.parse_covenant_tasks",
            return_value=mock_tasks,
        ):
            client.post("/api/task-queue/sync-covenant")
        assert len(task_queue) == 1  # Not duplicated
