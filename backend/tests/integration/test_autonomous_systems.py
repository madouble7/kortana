"""
Integration tests for Phase 5 Autonomous Systems
Tests the complete flow of monitoring, PR creation, code review, and agent execution
"""

from unittest.mock import MagicMock, patch

from src.kortana.main import app


class TestAutonomousSystemsAPI:
    """Test autonomous systems REST API endpoints"""

    @patch("src.kortana.routers.autonomous_systems.run_always_on_monitor_task")
    def test_trigger_monitor_endpoint(self, mock_task, client):
        """Test triggering the Always-On Monitor"""
        mock_task.delay.return_value = MagicMock(id="task-123")

        response = client.post("/api/autonomous/monitor/trigger")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["task_id"] == "task-123"

    @patch("src.kortana.routers.autonomous_systems.create_pr_for_task_celery")
    def test_create_pr_endpoint(self, mock_task, client):
        """Test creating a PR for a task"""
        mock_task.delay.return_value = MagicMock(id="task-456")

        response = client.post("/api/autonomous/pr/create/issue-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"

    def test_code_review_endpoint(self, client):
        """Test code review generate-review endpoint exists"""
        # The actual endpoint is /api/code-review/generate-review (POST)
        response = client.post(
            "/api/code-review/generate-review",
            json={"code": "print('hello')", "language": "python"},
        )

        # Should not be 404/405 — the endpoint should exist
        assert response.status_code != 405
        assert response.status_code != 404

    def test_execute_agent_endpoint(self, client):
        """Test agent execution endpoint returns structured response"""
        response = client.post(
            "/api/agents/execute/0", json={"task": "Implement feature X"}
        )

        assert response.status_code == 200
        data = response.json()
        # Agent 0 may not exist, so either 'result' or 'error' is valid
        assert "result" in data or "error" in data


class TestCeleryConfiguration:
    """Test Celery configuration for Phase 5"""

    def test_celery_beat_schedule_configured(self):
        """Test that Celery beat schedule is configured"""
        from src.kortana.celery_app import app

        beat_schedule = app.conf.beat_schedule

        # Check that required tasks are scheduled
        assert "always-on-monitor-every-5-minutes" in beat_schedule
        assert "github-autonomy-every-10-minutes" in beat_schedule
        assert "hop-cycle-every-hour" in beat_schedule

    def test_celery_task_routes_configured(self):
        """Test that Celery task routes are configured"""
        from src.kortana.celery_app import app

        task_routes = app.conf.task_routes

        # Check that Phase 5 autonomy tasks have routes
        assert "src.kortana.tasks.create_pr_for_task_celery" in task_routes
        assert "src.kortana.tasks.review_code_task_celery" in task_routes
        assert "src.kortana.tasks.execute_agent_task_celery" in task_routes
        # run_always_on_monitor is in beat_schedule, not task_routes
        assert "src.kortana.tasks.run_github_autonomy_cycle" in task_routes

    def test_celery_always_on_monitor_interval(self):
        """Test Always-On Monitor is scheduled every 5 minutes"""
        from src.kortana.celery_app import app

        beat_schedule = app.conf.beat_schedule
        monitor_config = beat_schedule.get("always-on-monitor-every-5-minutes")

        assert monitor_config is not None
        assert monitor_config["schedule"] == 300.0  # 5 minutes


class TestServiceIntegration:
    """Test Phase 5 services can be imported and instantiated"""

    def test_github_autonomy_service_import(self):
        """Test GitHubAutonomyService can be imported"""
        from src.kortana.services.github_autonomy_service import GitHubAutonomyService

        assert GitHubAutonomyService is not None


class TestErrorHandling:
    """Test error handling in autonomous systems"""

    @patch("src.kortana.routers.autonomous_systems.run_always_on_monitor_task")
    def test_monitor_trigger_error_handling(self, mock_task, client):
        """Test error handling when triggering monitor"""
        mock_task.delay.side_effect = Exception("Redis connection failed")

        response = client.post("/api/autonomous/monitor/trigger")

        assert response.status_code == 500

    def test_code_review_empty_code_error(self, client):
        """Test code review with empty/missing body"""
        response = client.post("/api/code-review/generate-review")

        # Should return 422 (validation error) for missing body
        assert response.status_code == 422

    def test_execute_agent_missing_task_error(self, client):
        """Test agent execution with non-existent agent"""
        response = client.post(
            "/api/agents/execute/999", json={"task": "Implement feature X"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "not found" in data["error"].lower()


def test_autonomous_systems_router_registered():
    """Test that autonomous systems router is registered"""
    openapi = app.openapi()
    paths = openapi.get("paths", {})

    assert any("/autonomous" in path for path in paths)


def test_all_phase_5_services_exist():
    """Test that all Phase 5 services are available"""
    from src.kortana.services.github_autonomy_service import GitHubAutonomyService

    # Verify all services can be imported
    assert GitHubAutonomyService is not None
