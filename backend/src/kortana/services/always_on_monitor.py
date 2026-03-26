"""
Always-On Autonomous Development Monitor
Continuous monitoring and processing system for GitHub-driven autonomous development
Phase 7 Cycle #3: Intelligent task filtering and multi-source context injection
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
from src.kortana.services.task_filtering_service import TaskFilteringService

logger = get_logger(__name__)
settings = get_settings()


class AlwaysOnMonitor:
    """Always-on monitoring system for autonomous development."""

    def __init__(self):
        self.db_manager = get_db_manager()
        self.github_service = None
        self.hop_service = None
        self.task_filter = TaskFilteringService()
        self.is_running = False
        self.last_check = None
        self.check_interval = int(os.getenv("MONITOR_CHECK_INTERVAL", "60"))
        self.max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
        self.monitoring_enabled = (
            os.getenv("ALWAYS_ON_MONITORING", "true").lower() == "true"
        )

        self.stats = {
            "issues_fetched": 0,
            "tasks_created": 0,
            "tasks_processed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "human_interventions": 0,
            "last_run": None,
            "filtered_tasks_analyzed": 0,
            "high_impact_tasks_selected": 0,
        }

    def _db_session_scope(self):
        """Support both the real DB manager context API and older mocked tests."""
        session_scope_defined = "session_scope" in getattr(self.db_manager, "__dict__", {})
        session_scope_defined = session_scope_defined or hasattr(
            type(self.db_manager), "session_scope"
        )
        if session_scope_defined:
            session_scope = self.db_manager.session_scope
            return session_scope()
        return self.db_manager.get_session()

    async def start_monitoring(self):
        """Start the always-on monitoring loop."""
        if not self.monitoring_enabled:
            logger.info("Always-on monitoring disabled via environment variable")
            return

        if self.is_running:
            logger.warning("Monitor already running")
            return

        self.is_running = True
        logger.info("Starting Always-On Autonomous Development Monitor")
        logger.info(f"Check interval: {self.check_interval}s")
        logger.info(f"Max concurrent tasks: {self.max_concurrent_tasks}")
        logger.info(f"Monitoring enabled: {self.monitoring_enabled}")

        try:
            while self.is_running:
                await self._monitoring_cycle()
                await asyncio.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
        except Exception as e:
            logger.error(f"Monitor error: {str(e)}")
            raise
        finally:
            self.stop_monitoring()

    async def _monitoring_cycle(self):
        """Execute one monitoring cycle with error recovery."""
        cycle_start = time.time()
        self.last_check = datetime.utcnow().isoformat()
        logger.info("Starting monitoring cycle")

        errors_encountered = []
        partial_success = False

        try:
            try:
                new_tasks = await self._fetch_new_issues()
                self.stats["issues_fetched"] += len(new_tasks)
                self.stats["tasks_created"] += len(new_tasks)
                partial_success = True
            except Exception as e:
                error_msg = f"Failed to fetch issues: {str(e)}"
                logger.error(error_msg)
                errors_encountered.append(error_msg)
                new_tasks = []

            try:
                await self._process_task_pipeline()
                partial_success = True
            except Exception as e:
                error_msg = f"Failed to process task pipeline: {str(e)}"
                logger.error(error_msg)
                errors_encountered.append(error_msg)

            try:
                await self._run_hop_cycle()
                partial_success = True
            except Exception as e:
                error_msg = f"Failed to run HOP cycle: {str(e)}"
                logger.error(error_msg)
                errors_encountered.append(error_msg)

            self.stats["last_run"] = datetime.utcnow().isoformat()
            cycle_duration = time.time() - cycle_start

            if errors_encountered:
                logger.warning(
                    f"Cycle completed with {len(errors_encountered)} errors in "
                    f"{cycle_duration:.2f}s"
                )
                for error in errors_encountered:
                    logger.warning(error)
            else:
                logger.info(f"Cycle completed successfully in {cycle_duration:.2f}s")

            logger.info(
                f"Cycle stats: {len(new_tasks)} new, {self.stats['tasks_processed']} processed"
            )

            if not partial_success and not new_tasks:
                raise Exception(f"Complete cycle failure: {', '.join(errors_encountered)}")

        except Exception as e:
            logger.error(f"Cycle failed completely: {str(e)}")
            self.stats["errors_encountered"] = errors_encountered

    async def _fetch_new_issues(self) -> List[GitHubTask]:
        """Fetch new GitHub issues and queue them as tasks."""
        try:
            logger.info("Fetching new GitHub issues")
            async with self._db_session_scope() as db:
                try:
                    self.github_service = GitHubAutonomyService(db)
                    new_tasks = await self.github_service.fetch_and_queue_issues()

                    if new_tasks:
                        logger.info(f"Found {len(new_tasks)} new issues to process")
                        self.stats["filtered_tasks_analyzed"] += len(new_tasks)

                        ranked_tasks = await self.task_filter.filter_and_rank_tasks(
                            new_tasks
                        )
                        for task, context in ranked_tasks[:3]:
                            logger.info(
                                f"Task #{task.github_issue_number}: {task.title} "
                                f"(impact={context.impact_level.value}, "
                                f"score={context.impact_score:.2f})"
                            )
                            self.stats["high_impact_tasks_selected"] += 1
                    else:
                        logger.info("No new issues found")

                    return new_tasks
                except Exception as e:
                    logger.error(f"Failed in fetch cycle: {str(e)}")
                    return []

        except Exception as e:
            logger.error(f"Failed to fetch issues: {str(e)}")
            return []

    async def _process_task_pipeline(self):
        """Process tasks through the autonomous development pipeline."""
        try:
            logger.info("Processing task pipeline")

            from sqlalchemy import select

            async with self._db_session_scope() as db:
                stmt = (
                    select(GitHubTask)
                    .filter(
                        GitHubTask.status.in_(
                            ("pending", "analyzed", "planning_complete")
                        )
                    )
                    .limit(self.max_concurrent_tasks * 2)
                )
                result = await db.execute(stmt)
                all_pending_tasks = result.scalars().all()

                if not all_pending_tasks:
                    logger.info("No queued tasks to process")
                    return

                ranked_tasks = await self.task_filter.filter_and_rank_tasks(
                    all_pending_tasks,
                    limit=self.max_concurrent_tasks,
                )

                if not ranked_tasks:
                    logger.warning("No tasks selected after intelligent filtering")
                    return

                pending_tasks = [task for task, _ in ranked_tasks]
                self.hop_service = HOPAutonomyService(db)

                for task in pending_tasks:
                    try:
                        await self._process_single_task(task, db)
                        self.stats["tasks_processed"] += 1
                    except Exception as e:
                        logger.error(f"Task {task.id} failed: {str(e)}")
                        self.stats["tasks_failed"] += 1

                        try:
                            task.status = "failed"
                            task.error_message = str(e)
                            task.error_count = (task.error_count or 0) + 1
                            if task.error_count >= 3:
                                task.status = "needs_human_review"
                                logger.warning(
                                    f"Task {task.id} marked for human review after "
                                    f"{task.error_count} failures"
                                )
                            await db.commit()
                        except Exception as db_exc:
                            logger.error(
                                f"Failed to update task {task.id} status: {str(db_exc)}"
                            )

        except Exception as e:
            logger.error(f"Pipeline processing failed: {str(e)}")
            raise

    async def _process_single_task(self, task: GitHubTask, db: AsyncSession):
        """Process a single task through the full pipeline."""
        logger.info(f"Processing task #{task.github_issue_number}: {task.title}")

        if task.status == "pending":
            logger.info(f"Analyzing task {task.id}")
            self.github_service = GitHubAutonomyService(db)
            await self.github_service.analyze_task(task)
            logger.info(f"Analysis complete for task {task.id}")

        if task.status == "analyzed":
            logger.info(f"Planning task {task.id}")
            self.github_service = GitHubAutonomyService(db)
            await self.github_service.plan_task(task)
            logger.info(f"Planning complete for task {task.id}")

        if task.status == "planning_complete":
            self.hop_service = HOPAutonomyService()
            requires_human = await self.hop_service.should_require_human(task)

            if requires_human:
                logger.info(f"Task {task.id} requires human oversight")
                await self.hop_service.generate_ho_scaffold(task)
                self.stats["human_interventions"] += 1
                logger.info(f"HO scaffold generated for task {task.id}")
            else:
                logger.info(f"Executing task {task.id} autonomously")
                self.github_service = GitHubAutonomyService(db)
                await self.github_service.execute_task(task, dry_run=False)
                logger.info(f"Task {task.id} executed successfully")
                self.stats["tasks_completed"] += 1

    async def _run_hop_cycle(self):
        """Run HOP autonomy cycle for task classification."""
        try:
            logger.info("Running HOP autonomy cycle")
            self.hop_service = HOPAutonomyService()
            result = await self.hop_service.run_hop_cycle()
            logger.info(f"HOP cycle completed: {result.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"HOP cycle failed: {str(e)}")

    def stop_monitoring(self):
        """Stop the monitoring system."""
        self.is_running = False
        logger.info("Always-On Monitor stopped")
        if self.github_service:
            self.github_service.close()
        if self.hop_service:
            self.hop_service.close()

    def get_status(self) -> Dict[str, Any]:
        """Get current monitor status and statistics."""
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
        """Get current task status across all stages."""
        try:
            from sqlalchemy import func, select

            async with self._db_session_scope() as db:
                async def count_filtered(filter_expr=None):
                    stmt = select(func.count()).select_from(GitHubTask)
                    if filter_expr is not None:
                        stmt = stmt.where(filter_expr)
                    result = await db.execute(stmt)
                    return result.scalar_one()

                total_tasks = await count_filtered()
                pending = await count_filtered(GitHubTask.status == "pending")
                analyzing = await count_filtered(GitHubTask.status == "analyzing")
                planning = await count_filtered(GitHubTask.status == "planning")
                planning_complete = await count_filtered(
                    GitHubTask.status == "planning_complete"
                )
                executing = await count_filtered(GitHubTask.status == "executing")
                completed = await count_filtered(GitHubTask.status == "completed")
                failed = await count_filtered(GitHubTask.status == "failed")
                waiting_ho = await count_filtered(GitHubTask.status == "waiting_for_ho")

                auto_tasks = await count_filtered(GitHubTask.classification == "auto")
                ho_tasks = await count_filtered(GitHubTask.classification == "ho")
                approval_tasks = await count_filtered(
                    GitHubTask.classification == "approval"
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
            logger.error(f"Failed to get task status: {str(e)}")
            return {"error": str(e)}

    async def force_check(self) -> Dict[str, Any]:
        """Force an immediate monitoring cycle."""
        if not self.is_running:
            logger.warning("Monitor not running, starting temporarily")
            self.is_running = True
            try:
                await self._monitoring_cycle()
            finally:
                self.is_running = False
        else:
            await self._monitoring_cycle()

        return self.get_status()


_monitor = None


def get_always_on_monitor() -> AlwaysOnMonitor:
    """Get or create the always-on monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = AlwaysOnMonitor()
    return _monitor


async def start_always_on_monitor():
    """Start the always-on monitor for startup scripts and API triggers."""
    monitor = get_always_on_monitor()
    await monitor.start_monitoring()


def stop_always_on_monitor():
    """Stop the always-on monitor for shutdown handlers."""
    global _monitor
    if _monitor:
        _monitor.stop_monitoring()
        _monitor = None
