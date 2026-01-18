"""
Task Queue Service for Kor'tana
Manages task creation, enqueueing, and status tracking
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from celery.result import AsyncResult
from database import SessionLocal
from models import Task
from tasks import execute_hop_task, process_chat, analyze_image
from logger import log_request, log_error


class TaskQueueService:
    """Service for managing task queue operations"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    async def enqueue_task(self, task_data: dict[str, Any]) -> Task:
        """
        Create and enqueue a task
        
        Args:
            task_data: Dictionary containing task information
                - title: str
                - description: str (optional)
                - priority: int (1-10, default 5)
                - command: str (optional)
                - classification: str (default "auto")
        
        Returns:
            Created Task object
        """
        try:
            # Create task in database
            task = Task(
                id=str(uuid4()),
                title=task_data.get("title"),
                description=task_data.get("description"),
                priority=task_data.get("priority", 5),
                command=task_data.get("command"),
                classification=task_data.get("classification", "auto"),
                status="pending",
                created_at=datetime.utcnow()
            )
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            log_request("task_queue", f"Task created: {task.id} - {task.title}")
            
            return task
            
        except Exception as e:
            self.db.rollback()
            log_error("task_queue", f"Failed to create task: {str(e)}")
            raise
    
    async def execute_task(self, task_id: str) -> dict[str, Any]:
        """
        Execute a task immediately via Celery
        
        Args:
            task_id: UUID of task to execute
            
        Returns:
            dict with celery task info
        """
        try:
            # Get task from database
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Enqueue to Celery
            celery_task = execute_hop_task.delay(task_id)
            
            log_request("task_queue", f"Task enqueued to Celery: {task_id}")
            
            return {
                "task_id": task_id,
                "celery_task_id": celery_task.id,
                "status": "enqueued"
            }
            
        except Exception as e:
            log_error("task_queue", f"Failed to execute task {task_id}: {str(e)}")
            raise
    
    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        Get current status of a task
        
        Args:
            task_id: UUID of task
            
        Returns:
            dict with task status information
        """
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            return {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "classification": task.classification,
                "priority": task.priority,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "result": task.result,
                "error": task.error
            }
            
        except Exception as e:
            log_error("task_queue", f"Failed to get task status {task_id}: {str(e)}")
            raise
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending task
        
        Args:
            task_id: UUID of task to cancel
            
        Returns:
            bool indicating success
        """
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return False
            
            if task.status in ["completed", "failed"]:
                return False  # Cannot cancel completed/failed tasks
            
            task.status = "cancelled"
            task.updated_at = datetime.utcnow()
            self.db.commit()
            
            log_request("task_queue", f"Task cancelled: {task_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            log_error("task_queue", f"Failed to cancel task {task_id}: {str(e)}")
            raise
    
    async def list_tasks(
        self, 
        status: str | None = None, 
        limit: int = 100,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        List tasks with optional filtering
        
        Args:
            status: Filter by status (optional)
            limit: Max number of tasks to return
            offset: Pagination offset
            
        Returns:
            List of task dictionaries
        """
        try:
            query = self.db.query(Task)
            
            if status:
                query = query.filter(Task.status == status)
            
            tasks = query.order_by(Task.created_at.desc()).limit(limit).offset(offset).all()
            
            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "classification": t.classification,
                    "priority": t.priority,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in tasks
            ]
            
        except Exception as e:
            log_error("task_queue", f"Failed to list tasks: {str(e)}")
            raise
    
    async def enqueue_chat(self, message: str, conversation_id: str | None = None) -> dict[str, Any]:
        """
        Enqueue a chat message for processing
        
        Args:
            message: User message text
            conversation_id: Optional conversation ID
            
        Returns:
            dict with celery task info
        """
        try:
            celery_task = process_chat.delay(message, conversation_id)
            
            log_request("task_queue", f"Chat enqueued: {celery_task.id}")
            
            return {
                "celery_task_id": celery_task.id,
                "status": "enqueued",
                "message": message[:100]
            }
            
        except Exception as e:
            log_error("task_queue", f"Failed to enqueue chat: {str(e)}")
            raise
    
    async def enqueue_image_analysis(self, image_url: str, prompt: str) -> dict[str, Any]:
        """
        Enqueue an image for analysis
        
        Args:
            image_url: URL to image
            prompt: Analysis prompt
            
        Returns:
            dict with celery task info
        """
        try:
            celery_task = analyze_image.delay(image_url, prompt)
            
            log_request("task_queue", f"Image analysis enqueued: {celery_task.id}")
            
            return {
                "celery_task_id": celery_task.id,
                "status": "enqueued",
                "image_url": image_url
            }
            
        except Exception as e:
            log_error("task_queue", f"Failed to enqueue image analysis: {str(e)}")
            raise
    
    async def get_celery_result(self, celery_task_id: str) -> dict[str, Any]:
        """
        Get result of a Celery task
        
        Args:
            celery_task_id: Celery task ID
            
        Returns:
            dict with task result and status
        """
        try:
            result = AsyncResult(celery_task_id)
            
            return {
                "celery_task_id": celery_task_id,
                "status": result.status,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "result": result.result if result.ready() else None
            }
            
        except Exception as e:
            log_error("task_queue", f"Failed to get Celery result {celery_task_id}: {str(e)}")
            raise
    
    def close(self):
        """Close database session"""
        self.db.close()


# Singleton instance
_task_queue_service = None

def get_task_queue_service() -> TaskQueueService:
    """Get or create task queue service instance"""
    global _task_queue_service
    if _task_queue_service is None:
        _task_queue_service = TaskQueueService()
    return _task_queue_service
