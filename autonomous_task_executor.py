"""
Autonomous Task Executor - Scheduled Development & Improvement Tasks
=====================================================================

This service manages:
- Scheduled autonomous development tasks
- Code review cycles
- Refactoring initiatives
- Testing and validation runs
- Performance optimization tasks
- Goal processing and autonomous intelligence updates

Tasks are queued and executed based on system resources and priorities.
"""

import asyncio
import json
import logging
import os
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import sqlite3
from enum import Enum
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('state/autonomous_tasks.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Path('state').mkdir(exist_ok=True)


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AutonomousTask:
    """Represents an autonomous task."""
    task_id: str
    name: str
    description: str
    task_type: str  # 'code_review', 'refactor', 'test', 'optimize', 'goal_process'
    command: Optional[str] = None
    function: Optional[Callable] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    scheduled_time: Optional[datetime] = None
    interval_minutes: Optional[int] = None  # For recurring tasks
    status: TaskStatus = TaskStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    estimated_duration_minutes: int = 5
    retries: int = 0
    max_retries: int = 3


class AutonomousTaskExecutor:
    """Executes scheduled autonomous development tasks."""
    
    def __init__(self):
        self.db_path = 'state/autonomous_tasks.db'
        self.task_queue: List[AutonomousTask] = []
        self.executed_tasks = {}
        self.is_running = False
        self.executor_thread: Optional[threading.Thread] = None
        self.check_interval = 5  # seconds between task checks
        
        self._initialize_database()
        self._register_default_tasks()
        logger.info("🟢 Autonomous Task Executor initialized")
    
    def _initialize_database(self):
        """Initialize database for task tracking."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    task_type TEXT,
                    priority INTEGER,
                    status TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_run DATETIME,
                    next_run DATETIME,
                    execution_count INTEGER DEFAULT 0,
                    total_duration_ms INTEGER DEFAULT 0,
                    last_result TEXT,
                    details JSON
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    duration_ms INTEGER,
                    result TEXT,
                    error_message TEXT,
                    details JSON,
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✓ Task executor database initialized")
        except Exception as e:
            logger.error(f"✗ Database initialization failed: {e}")
    
    def _register_default_tasks(self):
        """Register default autonomous tasks."""
        tasks = [
            AutonomousTask(
                task_id="daily_code_review",
                name="Daily Code Review",
                description="Perform comprehensive code review cycle",
                task_type="code_review",
                command="python -m pytest tests/ -v --tb=short",
                priority=TaskPriority.HIGH,
                interval_minutes=1440,  # Daily
                estimated_duration_minutes=15
            ),
            AutonomousTask(
                task_id="hourly_health_check",
                name="Hourly System Health Check",
                description="Check system health and generate report",
                task_type="health_check",
                command="python autonomous_monitor_daemon.py",
                priority=TaskPriority.HIGH,
                interval_minutes=60,  # Hourly
                estimated_duration_minutes=2
            ),
            AutonomousTask(
                task_id="development_analysis",
                name="Development Activity Analysis",
                description="Analyze development activity and changes",
                task_type="analysis",
                command="python development_activity_tracker.py",
                priority=TaskPriority.MEDIUM,
                interval_minutes=120,  # Every 2 hours
                estimated_duration_minutes=5
            ),
            AutonomousTask(
                task_id="weekly_refactor",
                name="Weekly Code Refactoring",
                description="Execute code refactoring and cleanup",
                task_type="refactor",
                priority=TaskPriority.MEDIUM,
                interval_minutes=10080,  # Weekly
                estimated_duration_minutes=30
            ),
            AutonomousTask(
                task_id="continuous_testing",
                name="Continuous Integration Tests",
                description="Run continuous integration test suite",
                task_type="test",
                command="python -m pytest tests/ -x",
                priority=TaskPriority.HIGH,
                interval_minutes=30,  # Every 30 minutes
                estimated_duration_minutes=10
            ),
            AutonomousTask(
                task_id="goal_processing_cycle",
                name="Autonomous Goal Processing",
                description="Process queued goals and autonomous development requests",
                task_type="goal_process",
                priority=TaskPriority.HIGH,
                interval_minutes=15,  # Every 15 minutes
                estimated_duration_minutes=5
            ),
            AutonomousTask(
                task_id="intelligence_update",
                name="Intelligence Update Cycle",
                description="Update autonomous intelligence metrics and learning",
                task_type="intelligence_update",
                priority=TaskPriority.MEDIUM,
                interval_minutes=30,  # Every 30 minutes
                estimated_duration_minutes=3
            ),
        ]
        
        for task in tasks:
            self.add_task(task)
        
        logger.info(f"📋 Registered {len(tasks)} default tasks")
    
    def add_task(self, task: AutonomousTask):
        """Add a task to the queue."""
        task.next_run = datetime.now()
        self.task_queue.append(task)
        
        # Persist to database
        self._save_task(task)
        logger.info(f"➕ Task added: {task.name}")
    
    def _save_task(self, task: AutonomousTask):
        """Save task to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO tasks
                (task_id, name, description, task_type, priority, status,
                 last_run, next_run, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.task_id,
                task.name,
                task.description,
                task.task_type,
                task.priority.value,
                task.status.value,
                task.last_run.isoformat() if task.last_run else None,
                task.next_run.isoformat() if task.next_run else None,
                json.dumps({
                    'interval_minutes': task.interval_minutes,
                    'estimated_duration_minutes': task.estimated_duration_minutes,
                    'command': task.command
                })
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"✗ Failed to save task: {e}")
    
    def get_ready_tasks(self) -> List[AutonomousTask]:
        """Get all tasks that are ready to execute."""
        ready = []
        now = datetime.now()
        
        for task in self.task_queue:
            if task.status == TaskStatus.PENDING or task.status == TaskStatus.COMPLETED:
                if task.next_run and task.next_run <= now:
                    # Check if enough time has passed for the task to complete
                    if task.last_run is None or \
                       (now - task.last_run).total_seconds() >= (task.estimated_duration_minutes * 60 * 2):
                        ready.append(task)
        
        # Sort by priority
        ready.sort(key=lambda t: t.priority.value)
        return ready
    
    async def execute_task(self, task: AutonomousTask) -> bool:
        """Execute a single task."""
        task_start = time.time()
        task.status = TaskStatus.RUNNING
        
        logger.info(f"🚀 Executing task: {task.name} [{task.task_id}]")
        logger.info(f"   Type: {task.task_type}")
        logger.info(f"   Priority: {task.priority.name}")
        
        try:
            if task.command:
                # Execute command
                result = subprocess.run(
                    task.command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=task.estimated_duration_minutes * 60
                )
                
                success = result.returncode == 0
                output = result.stdout + result.stderr
            elif task.function:
                # Execute function
                result = await task.function() if asyncio.iscoroutinefunction(task.function) else task.function()
                success = result is not None
                output = str(result)
            else:
                # No command or function
                success = True
                output = "Task executed (no command/function defined)"
            
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.last_run = datetime.now()
            task.retries = 0
            
            # Schedule next execution if recurring
            if task.interval_minutes:
                task.next_run = datetime.now() + timedelta(minutes=task.interval_minutes)
            else:
                task.status = TaskStatus.COMPLETED
            
            duration_ms = int((time.time() - task_start) * 1000)
            
            logger.info(f"✅ Task completed: {task.name} ({duration_ms}ms)")
            
            # Record execution
            self._record_execution(task.task_id, task.status, duration_ms, output)
            self._save_task(task)
            
            return success
        
        except subprocess.TimeoutExpired:
            logger.error(f"⏱️  Task timeout: {task.name}")
            task.status = TaskStatus.FAILED
            task.retries += 1
            if task.retries < task.max_retries:
                task.next_run = datetime.now() + timedelta(minutes=5)  # Retry in 5 minutes
            return False
        
        except Exception as e:
            logger.error(f"✗ Task failed: {task.name} - {e}")
            task.status = TaskStatus.FAILED
            task.retries += 1
            if task.retries < task.max_retries:
                task.next_run = datetime.now() + timedelta(minutes=10)  # Retry in 10 minutes
            
            duration_ms = int((time.time() - task_start) * 1000)
            self._record_execution(task.task_id, TaskStatus.FAILED, duration_ms, str(e))
            self._save_task(task)
            
            return False
    
    def _record_execution(self, task_id: str, status: TaskStatus,
                         duration_ms: int, result: str):
        """Record task execution in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO task_executions
                (task_id, status, duration_ms, result)
                VALUES (?, ?, ?, ?)
            ''', (task_id, status.value, duration_ms, result[:500]))  # Limit result size
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to record execution: {e}")
    
    def execution_cycle(self):
        """Execute a single executor cycle."""
        try:
            ready_tasks = self.get_ready_tasks()
            
            if ready_tasks:
                logger.info(f"📋 {len(ready_tasks)} tasks ready for execution")
                
                # Execute up to 3 tasks concurrently
                for task in ready_tasks[:3]:
                    try:
                        asyncio.run(self.execute_task(task))
                    except Exception as e:
                        logger.error(f"✗ Failed to execute task {task.task_id}: {e}")
            
            # Log task queue status
            pending_count = sum(1 for t in self.task_queue if t.status == TaskStatus.PENDING)
            running_count = sum(1 for t in self.task_queue if t.status == TaskStatus.RUNNING)
            
            if running_count > 0:
                logger.debug(f"📊 Queue status: {pending_count} pending, {running_count} running")
        
        except Exception as e:
            logger.error(f"✗ Execution cycle failed: {e}")
    
    def get_task_status(self) -> Dict[str, Any]:
        """Get current task status."""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_tasks': len(self.task_queue),
            'pending': sum(1 for t in self.task_queue if t.status == TaskStatus.PENDING),
            'running': sum(1 for t in self.task_queue if t.status == TaskStatus.RUNNING),
            'completed': sum(1 for t in self.task_queue if t.status == TaskStatus.COMPLETED),
            'failed': sum(1 for t in self.task_queue if t.status == TaskStatus.FAILED),
            'next_tasks': [
                {
                    'name': t.name,
                    'type': t.task_type,
                    'next_run': t.next_run.isoformat() if t.next_run else None
                }
                for t in sorted(self.task_queue, key=lambda x: x.next_run or datetime.max)[:5]
            ]
        }
    
    def run(self):
        """Start the task executor."""
        self.is_running = True
        logger.info("🚀 Starting Autonomous Task Executor")
        logger.info(f"⏱️  Check interval: {self.check_interval} seconds")
        logger.info(f"📋 Registered tasks: {len(self.task_queue)}")
        
        try:
            while self.is_running:
                self.execution_cycle()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("⏹️  Executor interrupted by user")
        except Exception as e:
            logger.error(f"✗ Executor error: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown executor gracefully."""
        self.is_running = False
        status = self.get_task_status()
        logger.info("🛑 Autonomous Task Executor shutdown")
        logger.info(f"📊 Final status: {json.dumps(status, indent=2)}")


def main():
    """Main entry point."""
    executor = AutonomousTaskExecutor()
    executor.run()


if __name__ == '__main__':
    main()
