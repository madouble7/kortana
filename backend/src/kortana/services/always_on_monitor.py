"""
Always-On Autonomous Development Monitor
Continuous monitoring and processing system for GitHub-driven autonomous development
"""

import asyncio
import os
import time
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession
from src.kortana.config import get_settings
from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask
from src.kortana.services.github_autonomy_service import GitHubAutonomyService
from src.kortana.services.hop_autonomy_service import HOPAutonomyService

logger = get_logger(__name__)
settings = get_settings()


class AlwaysOnMonitor:
    """Always-on monitoring system for autonomous development"""

    def __init__(self):
        self.db_manager = get_db_manager()
        self.github_service = None
        self.hop_service = None
        self.is_running = False
        self.last_check = None
        self.check_interval = int(os.getenv("MONITOR_CHECK_INTERVAL", "60"))  # seconds
        self.max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
        self.monitoring_enabled = os.getenv("ALWAYS_ON_MONITORING", "true").lower() == "true"

        # Statistics tracking
        self.stats = {
            "issues_fetched": 0,
            "tasks_created": 0,
            "tasks_processed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "human_interventions": 0,
            "last_run": None,
        }

    async def start_monitoring(self):
        """Start the always-on monitoring loop"""
        if not self.monitoring_enabled:
            logger.info("Always-on monitoring disabled via environment variable")
            return

        if self.is_running:
            logger.warning("Monitor already running")
            return

        self.is_running = True
        logger.info("🚀 Starting Always-On Autonomous Development Monitor")
        logger.info(f"📋 Check interval: {self.check_interval}s")
        logger.info(f"📊 Max concurrent tasks: {self.max_concurrent_tasks}")
        logger.info(f"🔧 Monitoring enabled: {self.monitoring_enabled}")

        try:
            while self.is_running:
                await self._monitoring_cycle()
                await asyncio.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("🛑 Monitor stopped by user")
        except Exception as e:
            logger.error(f"❌ Monitor error: {str(e)}")
            raise
        finally:
            self.stop_monitoring()

    async def _monitoring_cycle(self):
        """Execute one monitoring cycle"""
        cycle_start = time.time()
        logger.info("🔄 Starting monitoring cycle...")

        try:
            # 1. Fetch new GitHub issues
            new_tasks = await self._fetch_new_issues()
            self.stats["issues_fetched"] += len(new_tasks)
            self.stats["tasks_created"] += len(new_tasks)

            # 2. Process existing tasks through pipeline
            await self._process_task_pipeline()

            # 3. Run HOP autonomy cycle for classification
            await self._run_hop_cycle()

            # 4. Update statistics
            self.stats["last_run"] = datetime.utcnow().isoformat()
            cycle_duration = time.time() - cycle_start

            logger.info(f"✅ Cycle completed in {cycle_duration:.2f}s")
            logger.info(f"📊 Stats: {len(new_tasks)} new, {self.stats['tasks_processed']} processed")

        except Exception as e:
            logger.error(f"❌ Cycle failed: {str(e)}")
            raise

    async def _fetch_new_issues(self) -> List[GitHubTask]:
        """Fetch new GitHub issues and queue them as tasks"""
        try:
            logger.info("📥 Fetching new GitHub issues...")
            db = await self.db_manager.get_session()
            try:
                self.github_service = GitHubAutonomyService(db)
                new_tasks = await self.github_service.fetch_and_queue_issues()

                if new_tasks:
                    logger.info(f"✅ Found {len(new_tasks)} new issues to process")
                    for task in new_tasks:
                        logger.info(f"   📋 Task: #{task.github_issue_number} - {task.title}")
                else:
                    logger.info("📭 No new issues found")

                return new_tasks
            finally:
                await db.close()

        except Exception as e:
            logger.error(f"❌ Failed to fetch issues: {str(e)}")
            return []

    async def _process_task_pipeline(self):
        """Process tasks through the autonomous development pipeline"""
        try:
            logger.info("⚙️ Processing task pipeline...")

            db = await self.db_manager.get_session()
            try:
                # Get pending tasks (limit based on concurrency setting)
                pending_tasks = (
                    db.query(GitHubTask)
                    .filter(GitHubTask.status == "pending")
                    .limit(self.max_concurrent_tasks)
                    .all()
                )

                if not pending_tasks:
                    logger.info("📭 No pending tasks to process")
                    return

                logger.info(f"🚀 Processing {len(pending_tasks)} pending tasks")

                # Process each task through the pipeline
                for task in pending_tasks:
                    try:
                        await self._process_single_task(task, db)
                        self.stats["tasks_processed"] += 1
                    except Exception as e:
                        logger.error(f"❌ Task {task.id} failed: {str(e)}")
                        self.stats["tasks_failed"] += 1
                        continue
            finally:
                await db.close()

        except Exception as e:
            logger.error(f"❌ Pipeline processing failed: {str(e)}")
            raise

    async def _process_single_task(self, task: GitHubTask, db: AsyncSession):
        """Process a single task through the full pipeline"""
        logger.info(f"🎯 Processing task #{task.github_issue_number}: {task.title}")

        # 1. Analyze task
        if task.status == "pending":
            logger.info(f"🔍 Analyzing task {task.id}")
            self.github_service = GitHubAutonomyService(db)
            await self.github_service.analyze_task(task)
            logger.info(f"✅ Analysis complete for task {task.id}")

        # 2. Plan task
        if task.status == "analyzed":
            logger.info(f"📝 Planning task {task.id}")
            self.github_service = GitHubAutonomyService(db)
            await self.github_service.plan_task(task)
            logger.info(f"✅ Planning complete for task {task.id}")

        # 3. Execute task (if autonomous mode enabled)
        if task.status == "planning_complete":
            # Check if task requires human oversight
            self.hop_service = HOPAutonomyService()
            requires_human = await self.hop_service.should_require_human(task)

            if requires_human:
                logger.info(f"👤 Task {task.id} requires human oversight")
                scaffold = await self.hop_service.generate_ho_scaffold(task)
                self.stats["human_interventions"] += 1
                logger.info(f"📋 HO scaffold generated for task {task.id}")
            else:
                logger.info(f"🤖 Executing task {task.id} autonomously")
                self.github_service = GitHubAutonomyService(db)
                await self.github_service.execute_task(task, dry_run=False)
                logger.info(f"✅ Task {task.id} executed successfully")
                self.stats["tasks_completed"] += 1

    async def _run_hop_cycle(self):
        """Run HOP autonomy cycle for task classification"""
        try:
            logger.info("🧠 Running HOP autonomy cycle...")
            self.hop_service = HOPAutonomyService()
            result = await self.hop_service.run_hop_cycle()
            logger.info(f"✅ HOP cycle completed: {result.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ HOP cycle failed: {str(e)}")
            # Don't raise - HOP cycle failure shouldn't stop monitoring

    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.is_running = False
        logger.info("🛑 Always-On Monitor stopped")
        if self.github_service:
            self.github_service.close()
        if self.hop_service:
            self.hop_service.close()

    def get_status(self) -> Dict[str, Any]:
        """Get current monitor status and statistics"""
        return {
            "monitoring_enabled": self.monitoring_enabled,
            "is_running": self.is_running,
            "last_check": self.last_check,
            "check_interval": self.check_interval,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "statistics": self.stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_task_status(self) -> Dict[str, Any]:
        """Get current task status across all stages"""
        try:
            async with self.db_manager.get_session() as db:
                # Count tasks by status
                total_tasks = db.query(GitHubTask).count()
                pending = db.query(GitHubTask).filter(GitHubTask.status == "pending").count()
                analyzing = db.query(GitHubTask).filter(GitHubTask.status == "analyzing").count()
                planning = db.query(GitHubTask).filter(GitHubTask.status == "planning").count()
                planning_complete = (
                    db.query(GitHubTask).filter(GitHubTask.status == "planning_complete").count()
                )
                executing = db.query(GitHubTask).filter(GitHubTask.status == "executing").count()
                completed = db.query(GitHubTask).filter(GitHubTask.status == "completed").count()
                failed = db.query(GitHubTask).filter(GitHubTask.status == "failed").count()
                waiting_ho = (
                    db.query(GitHubTask).filter(GitHubTask.status == "waiting_for_ho").count()
                )

                # Count by classification
                auto_tasks = (
                    db.query(GitHubTask).filter(GitHubTask.classification == "auto").count()
                )
                ho_tasks = db.query(GitHubTask).filter(GitHubTask.classification == "ho").count()
                approval_tasks = (
                    db.query(GitHubTask).filter(GitHubTask.classification == "approval").count()
                )

                return {
                    "total_tasks": total_tasks,
                    "by_status": {
                        "pending": pending,
                        "analyzing": analyzing,
                        "planning": planning,
                        "planning_complete": planning_complete,
                        "executing": executing,
                        "completed": completed,
                        "failed": failed,
                        "waiting_for_ho": waiting_ho,
                    },
                    "by_classification": {
                        "auto": auto_tasks,
                        "ho": ho_tasks,
                        "approval": approval_tasks,
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"❌ Failed to get task status: {str(e)}")
            return {"error": str(e)}

    async def force_check(self) -> Dict[str, Any]:
        """Force an immediate monitoring cycle"""
        if not self.is_running:
            logger.warning("Monitor not running, starting temporarily")
            # Start temporarily for this check
            self.is_running = True
            try:
                await self._monitoring_cycle()
            finally:
                self.is_running = False
        else:
            await self._monitoring_cycle()

        return self.get_status()


# Global monitor instance
_monitor = None


def get_always_on_monitor() -> AlwaysOnMonitor:
    """Get or create the always-on monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = AlwaysOnMonitor()
    return _monitor


async def start_always_on_monitor():
    """Start the always-on monitor (for use in main.py or startup scripts)"""
    monitor = get_always_on_monitor()
    await monitor.start_monitoring()


def stop_always_on_monitor():
    """Stop the always-on monitor (for use in shutdown handlers)"""
    global _monitor
    if _monitor:
        _monitor.stop_monitoring()
        _monitor = None
