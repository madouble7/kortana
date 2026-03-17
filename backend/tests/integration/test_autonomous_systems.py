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

    @patch("src.kortana.routers.autonomous_systems.review_code_task_celery")
    def test_code_review_endpoint(self, mock_task, client):
        """Test code review endpoint"""
        mock_task.delay.return_value = MagicMock(id="task-789")

        code = "def hello(): pass"
        response = client.post(
            "/api/autonomous/review?code=def+hello%28%29:+pass&file_path=main.py"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"

    @patch("src.kortana.routers.autonomous_systems.execute_agent_task_celery")
    def test_execute_agent_endpoint(self, mock_task, client):
        """Test agent execution endpoint"""
        mock_task.delay.return_value = MagicMock(id="task-999")

        response = client.post(
            '/api/autonomous/agent/execute/agent-1?task=Implement+feature+X&context={"priority":"high"}'
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"


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

        # Check that Phase 5 tasks have routes
        assert "src.kortana.tasks.run_always_on_monitor" in task_routes
        assert "src.kortana.tasks.create_pr_for_task" in task_routes
        assert "src.kortana.tasks.review_code" in task_routes
        assert "src.kortana.tasks.execute_agent" in task_routes

    def test_celery_always_on_monitor_interval(self):
        """Test Always-On Monitor is scheduled every 5 minutes"""
        from src.kortana.celery_app import app

        beat_schedule = app.conf.beat_schedule
        monitor_config = beat_schedule.get("always-on-monitor-every-5-minutes")

        assert monitor_config is not None
        assert monitor_config["schedule"] == 300.0  # 5 minutes


class TestServiceIntegration:
    """Test Phase 5 services can be imported and instantiated"""

    def test_always_on_monitor_service_import(self):
        """Test AlwaysOnMonitor service can be imported"""
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        assert AlwaysOnMonitor is not None

    def test_pr_creation_service_import(self):
        """Test PRCreationService can be imported"""
        from src.kortana.services.pr_creation_service import PRCreationService

        assert PRCreationService is not None

    def test_code_review_service_import(self):
        """Test CodeReviewService can be imported"""
        from src.kortana.services.code_review_service import CodeReviewService

        assert CodeReviewService is not None

    def test_agent_orchestration_service_import(self):
        """Test AgentOrchestrationService can be imported"""
        from src.kortana.services.agent_orchestration_service import (
            AgentOrchestrationService,
        )

        assert AgentOrchestrationService is not None

    def test_code_review_service_security_patterns(self):
        """Test code review service has security patterns"""
        from src.kortana.services.code_review_service import CodeReviewService

        service = CodeReviewService()
        patterns = service.SECURITY_PATTERNS

        assert "sql_injection" in patterns
        assert len(patterns) > 5  # Should have multiple security patterns

    def test_pinecone_knowledge_base_import(self):
        """Test Pinecone knowledge base can be imported"""
        from src.kortana.services.pinecone_knowledge_base import (
            PineconeKnowledgeBase,
        )

        # Should not raise even if Pinecone is not available
        kb = PineconeKnowledgeBase()
        assert kb is not None


class TestErrorHandling:
    """Test error handling in autonomous systems"""

    @patch("src.kortana.routers.autonomous_systems.run_always_on_monitor_task")
    def test_monitor_trigger_error_handling(self, mock_task, client):
        """Test error handling when triggering monitor"""
        mock_task.delay.side_effect = Exception("Redis connection failed")

        response = client.post("/api/autonomous/monitor/trigger")

        assert response.status_code == 500

    @patch("src.kortana.routers.autonomous_systems.review_code_task_celery")
    def test_code_review_empty_code_error(self, mock_task, client):
        """Test code review with empty code"""
        response = client.post("/api/autonomous/review?code=&file_path=main.py")

        assert response.status_code == 500

    @patch("src.kortana.routers.autonomous_systems.execute_agent_task_celery")
    def test_execute_agent_missing_task_error(self, mock_task, client):
        """Test agent execution with missing task"""
        response = client.post("/api/autonomous/agent/execute/agent-1?task=&context={}")

        assert response.status_code == 500


def test_autonomous_systems_router_registered():
    """Test that autonomous systems router is registered"""
    openapi = app.openapi()
    paths = openapi.get("paths", {})

    assert any("/autonomous" in path for path in paths)


def test_all_phase_5_services_exist():
    """Test that all Phase 5 services are available"""
    from src.kortana.services.agent_orchestration_service import (
        AgentOrchestrationService,
    )
    from src.kortana.services.always_on_monitor import AlwaysOnMonitor
    from src.kortana.services.code_review_service import CodeReviewService
    from src.kortana.services.pr_creation_service import PRCreationService

    # Verify all services can be imported
    assert AlwaysOnMonitor is not None
    assert PRCreationService is not None
    assert CodeReviewService is not None
    assert AgentOrchestrationService is not None
