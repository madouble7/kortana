"""
Unit tests for task management functionality
Tests Celery tasks and TaskQueueService
"""

from unittest.mock import MagicMock, patch

import pytest



@pytest.fixture
def mock_db():
    """Mock database session"""
    db = MagicMock()
    return db


class TestCeleryTasks:
    """Tests for Celery task functions"""

    @patch("src.kortana.tasks.gemini_service")
    def test_process_chat_success(self, mock_gemini):
        """Test chat processing task"""
        from src.kortana.tasks import process_chat

        mock_gemini.analyze_text_sync.return_value = "AI response"

        result = process_chat("Hello", "conv-123")
        assert result["response"] == "AI response"
        assert result["conversation_id"] == "conv-123"
        assert result["status"] == "completed"

    @patch("src.kortana.tasks.gemini_service")
    def test_process_chat_failure(self, mock_gemini):
        """Test chat processing task failure"""
        from src.kortana.tasks import process_chat

        mock_gemini.analyze_text_sync.side_effect = Exception("API error")

        # Mock the task instance for retry
        mock_task = MagicMock()
        mock_task.retry = MagicMock(side_effect=Exception("Retry"))

        # Call with mock self
        with pytest.raises(Exception):
            process_chat(mock_task, "Hello")



    @patch("src.kortana.tasks.SessionLocal")
    def test_run_github_autonomy_cycle_success(self, mock_session):
        """Test GitHub autonomy cycle"""
        from src.kortana.tasks import run_github_autonomy_cycle

        # Mock database session and service
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        with patch("src.kortana.tasks.GitHubAutonomyService") as mock_service_class, \
             patch("asyncio.get_event_loop") as mock_loop:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            mock_loop_instance = MagicMock()
            mock_loop.return_value = mock_loop_instance

            # Mock async calls
            mock_loop_instance.run_until_complete.side_effect = [
                [MagicMock()],  # fetch_and_queue_issues
                None  # process_next_tasks
            ]

            result = run_github_autonomy_cycle()
            assert result["status"] == "completed"

    @patch("src.kortana.tasks.gemini_service")
    def test_classify_task_auto(self, mock_gemini):
        """Test task classification as auto"""
        from src.kortana.tasks import _classify_task

        mock_task = MagicMock()
        mock_task.title = "Test Task"
        mock_task.description = "Test description"

        mock_gemini.analyze_text_sync.return_value = "auto"

        result = _classify_task(mock_task)
        assert result == "auto"

    @patch("src.kortana.tasks.gemini_service")
    def test_classify_task_invalid_defaults_to_ho(self, mock_gemini):
        """Test task classification with invalid response defaults to ho"""
        from src.kortana.tasks import _classify_task

        mock_task = MagicMock()
        mock_task.title = "Test Task"
        mock_task.description = "Test description"

        mock_gemini.analyze_text_sync.return_value = "invalid"

        result = _classify_task(mock_task)
        assert result == "ho"

    @patch("src.kortana.tasks.gemini_service")
    def test_execute_task_success(self, mock_gemini):
        """Test task execution"""
        from src.kortana.tasks import _execute_task

        mock_task = MagicMock()
        mock_task.title = "Test Task"
        mock_task.description = "Test description"
        mock_task.command = "test command"

        mock_gemini.analyze_text_sync.return_value = "Execution result"

        result = _execute_task(mock_task)
        assert result == "Execution result"

    @patch("src.kortana.tasks.gemini_service")
    def test_generate_scaffold_success(self, mock_gemini):
        """Test scaffold generation"""
        from src.kortana.tasks import _generate_scaffold

        mock_task = MagicMock()
        mock_task.title = "Test Task"
        mock_task.description = "Test description"

        mock_gemini.analyze_text_sync.return_value = "Scaffold content"

        result = _generate_scaffold(mock_task)
        assert result == "Scaffold content"


class TestTaskQueueService:
    """Tests for TaskQueueService"""

    @pytest.fixture
    def service(self, mock_db):
        """Create TaskQueueService instance"""
        from src.kortana.services.task_queue_service import TaskQueueService
        service = TaskQueueService()
        service.db = mock_db
        return service

    @pytest.mark.asyncio
    async def test_enqueue_task_success(self, service, mock_db):
        """Test task enqueuing"""
        task_data = {
            "title": "Test Task",
            "description": "Test description",
            "priority": 5,
            "command": "test command",
            "classification": "auto"
        }

        mock_task = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = await service.enqueue_task(task_data)
        assert result.title == "Test Task"
        assert result.description == "Test description"

    @pytest.mark.asyncio
    async def test_execute_task_success(self, service, mock_db):
        """Test task execution via Celery"""
        mock_task = MagicMock()
        mock_task.id = "task-1"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        with patch("src.kortana.services.task_queue_service.execute_hop_task.delay") as mock_delay:
            mock_celery_task = MagicMock()
            mock_celery_task.id = "celery-1"
            mock_delay.return_value = mock_celery_task

            result = await service.execute_task("task-1")
            assert result["task_id"] == "task-1"
            assert result["celery_task_id"] == "celery-1"

    @pytest.mark.asyncio
    async def test_get_task_status_success(self, service, mock_db):
        """Test getting task status"""
        mock_task = MagicMock()
        mock_task.id = "task-1"
        mock_task.title = "Test Task"
        mock_task.status = "completed"
        mock_task.classification = "auto"
        mock_task.priority = 5
        mock_task.created_at = None
        mock_task.started_at = None
        mock_task.completed_at = None
        mock_task.result = "Success"
        mock_task.error = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        result = await service.get_task_status("task-1")
        assert result["id"] == "task-1"
        assert result["title"] == "Test Task"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_cancel_task_success(self, service, mock_db):
        """Test task cancellation"""
        mock_task = MagicMock()
        mock_task.id = "task-1"
        mock_task.status = "pending"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_task
        mock_db.commit = MagicMock()

        result = await service.cancel_task("task-1")
        assert result is True
        assert mock_task.status == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_task_completed(self, service, mock_db):
        """Test cancelling already completed task"""
        mock_task = MagicMock()
        mock_task.id = "task-1"
        mock_task.status = "completed"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        result = await service.cancel_task("task-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_tasks_success(self, service, mock_db):
        """Test listing tasks"""
        mock_task = MagicMock()
        mock_task.id = "task-1"
        mock_task.title = "Test Task"
        mock_task.description = "Test description"
        mock_task.status = "pending"
        mock_task.classification = "auto"
        mock_task.priority = 5
        mock_task.created_at = None

        mock_query = MagicMock()
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [mock_task]
        mock_db.query.return_value = mock_query

        result = await service.list_tasks()
        assert len(result) == 1
        assert result[0]["id"] == "task-1"
        assert result[0]["title"] == "Test Task"

    @pytest.mark.asyncio
    async def test_enqueue_chat_success(self, service):
        """Test chat enqueuing"""
        with patch("src.kortana.services.task_queue_service.process_chat.delay") as mock_delay:
            mock_celery_task = MagicMock()
            mock_celery_task.id = "celery-1"
            mock_delay.return_value = mock_celery_task

            result = await service.enqueue_chat("Hello world", "conv-123")
            assert result["celery_task_id"] == "celery-1"
            assert result["status"] == "enqueued"

    @pytest.mark.asyncio
    async def test_enqueue_image_analysis_success(self, service):
        """Test image analysis enqueuing"""
        with patch("src.kortana.services.task_queue_service.analyze_image.delay") as mock_delay:
            mock_celery_task = MagicMock()
            mock_celery_task.id = "celery-1"
            mock_delay.return_value = mock_celery_task

            result = await service.enqueue_image_analysis("http://example.com/image.jpg", "Analyze this")
            assert result["celery_task_id"] == "celery-1"
            assert result["status"] == "enqueued"

    @pytest.mark.asyncio
    async def test_get_celery_result_success(self, service):
        """Test getting Celery task result"""
        from celery.result import AsyncResult

        mock_result = MagicMock(spec=AsyncResult)
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = "Task result"

        with patch("src.kortana.services.task_queue_service.AsyncResult", return_value=mock_result):
            result = await service.get_celery_result("celery-1")
            assert result["celery_task_id"] == "celery-1"
            assert result["status"] == "SUCCESS"
            assert result["ready"] is True
            assert result["successful"] is True
            assert result["result"] == "Task result"