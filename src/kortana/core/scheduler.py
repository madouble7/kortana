"""
Kor'tana's Autonomous Task Scheduler
Handles self-directed, scheduled operations that enable true autonomy
"""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytz import UTC

from kortana.core.autonomous_tasks import run_performance_analysis_task
from kortana.core.covenant import CovenantEnforcer
from kortana.core.environmental_scanner import run_environmental_scan_cycle
from kortana.core.goal_manager import (
    GoalManager as CoreGoalManager,  # Alias to avoid confusion
)
from kortana.core.memory import MemoryManager

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


def start_scheduler():
    """
    Initializes and starts Kor'tana's autonomous agent scheduler.
    Now runs the full GoalEngine cycle and our specific EnvironmentalScanner.
    """
    logger.info(
        "🚀 Starting Kor'tana's autonomous agent scheduler (GoalEngine + Core EnvironmentalScanner mode)..."
    )

    # Define project root for the core environmental scanner
    project_root_for_core_scanner = "c:\\project-kortana"

    # Initialize dependencies
    memory_manager = MemoryManager()
    covenant_enforcer = CovenantEnforcer()
    core_goal_manager = CoreGoalManager(memory_manager, covenant_enforcer)

    # Wrapper for the core environmental scan cycle, passing necessary dependencies
    async def async_run_core_environmental_scan_wrapper():
        logger.info("[Scheduler] Triggering core environmental scan cycle.")
        try:
            await run_environmental_scan_cycle(
                core_goal_manager, project_root_for_core_scanner
            )
        except Exception as e:
            logger.error(
                f"[Scheduler] Error during core environmental scan cycle: {e}",
                exc_info=True,
            )

    # Add dynamic task prioritization logic
    async def prioritize_tasks():
        logger.info("[Scheduler] Prioritizing tasks based on urgency and context.")
        try:
            # Fetch active goals from GoalManager
            goals = core_goal_manager.get_active_goals()

            # Calculate dynamic priorities based on urgency and context
            for goal in goals:
                urgency_bonus = 0
                if goal.target_completion:
                    time_remaining = (
                        goal.target_completion - datetime.now(UTC)
                    ).total_seconds()
                    urgency_bonus = max(
                        0, 10 - time_remaining / 3600
                    )  # Higher bonus for closer deadlines

                goal.dynamic_priority = goal.priority + urgency_bonus

            # Sort goals by dynamic priority
            prioritized_goals = sorted(
                goals, key=lambda g: g.dynamic_priority, reverse=True
            )

            # Log prioritized goals
            logger.info(
                f"[Scheduler] Prioritized goals: {[g.title for g in prioritized_goals]}"
            )

            # Execute the highest-priority task
            if prioritized_goals:
                highest_priority_goal = prioritized_goals[0]
                logger.info(
                    f"[Scheduler] Executing highest-priority goal: {highest_priority_goal.title}"
                )
                success = core_goal_manager.activate_goal(highest_priority_goal.goal_id)
                if success:
                    logger.info(
                        f"[Scheduler] Successfully activated goal: {highest_priority_goal.title}"
                    )
                else:
                    logger.warning(
                        f"[Scheduler] Failed to activate goal: {highest_priority_goal.title}"
                    )

        except Exception as e:
            logger.error(
                f"[Scheduler] Error during task prioritization: {e}", exc_info=True
            )

    # Schedule periodic self-reflection (learning loop)
    async def async_run_performance_analysis_wrapper():
        logger.info("[Scheduler] Triggering performance analysis (learning loop).")
        from kortana.services.database import get_db_sync

        db = next(get_db_sync())
        try:
            await run_performance_analysis_task(db)
        except Exception as e:
            logger.error(
                f"[Scheduler] Error during performance analysis: {e}", exc_info=True
            )
        finally:
            db.close()

    scheduler.add_job(
        async_run_core_environmental_scan_wrapper,
        trigger=IntervalTrigger(seconds=60),
        id="core_environmental_scan_cycle",
        name="Periodic Core Environmental Scan Cycle",
        replace_existing=True,
        max_instances=1,
    )

    # Schedule task prioritization
    scheduler.add_job(
        prioritize_tasks,
        trigger=IntervalTrigger(seconds=120),
        id="task_prioritization_cycle",
        name="Periodic Task Prioritization Cycle",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.add_job(
        async_run_performance_analysis_wrapper,
        trigger=IntervalTrigger(hours=1),
        id="performance_analysis_cycle",
        name="Periodic Performance Analysis (Learning Loop)",
        replace_existing=True,
        max_instances=1,
    )  # Create a wrapper for performance analysis that handles DB dependency

    def run_performance_analysis_wrapper():
        """Wrapper to handle database dependency for performance analysis."""
        try:
            from src.kortana.services.database import get_db_sync

            db_gen = get_db_sync()
            db = next(db_gen)  # Get the actual session from the generator
            try:
                # Import here to avoid circular dependencies
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(run_performance_analysis_task(db))
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Performance analysis task failed: {e}")

    scheduler.add_job(
        run_performance_analysis_wrapper,
        trigger=IntervalTrigger(hours=1),
        id="performance_analysis_task",
        name="Periodic Self-Reflection and Learning",
        replace_existing=True,
    )

    # 🚀 BATCH 10: Add proactive code review task
    def run_proactive_code_review_wrapper():
        """Wrapper to handle database dependency for proactive code review."""
        try:
            from src.kortana.core.autonomous_tasks import run_proactive_code_review_task
            from src.kortana.services.database import get_db_sync

            db_gen = get_db_sync()
            db = next(db_gen)  # Get the actual session from the generator
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(run_proactive_code_review_task(db))
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Proactive code review task failed: {e}")

    scheduler.add_job(
        run_proactive_code_review_wrapper,
        trigger=IntervalTrigger(hours=2),  # Run every 2 hours
        id="proactive_code_review_task",
        name="Proactive Code Quality Review",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info(
        "✅ Kor'tana's autonomous scheduler started with Core Environmental Scanner."
    )
    logger.info("🔄 Core Environmental scan cycle will run every 60 seconds")
    logger.info("🔄 Task prioritization cycle will run every 120 seconds")
    logger.info("🔄 Performance analysis cycle will run every hour")


def stop_scheduler():
    """
    Gracefully stops Kor'tana's autonomous agent scheduler.
    """
    if scheduler.running:
        logger.info("🛑 Stopping Kor'tana's autonomous agent scheduler...")
        scheduler.shutdown(wait=True)
        logger.info("✅ Autonomous scheduler stopped")


def get_scheduler_status():
    """
    Returns the current status of the autonomous scheduler.
    """
    return {
        "running": scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat()
                if job.next_run_time
                else None,
                "trigger": str(job.trigger),
            }
            for job in scheduler.get_jobs()
        ],
    }
