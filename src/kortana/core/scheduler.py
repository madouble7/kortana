"""
Kor'tana's Autonomous Task Scheduler
Handles self-directed, scheduled operations that enable true autonomy
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

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

    scheduler.add_job(
        async_run_core_environmental_scan_wrapper,
        trigger=IntervalTrigger(seconds=60),
        id="core_environmental_scan_cycle",
        name="Periodic Core Environmental Scan Cycle",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info(
        "✅ Kor'tana's autonomous scheduler started with Core Environmental Scanner."
    )
    logger.info("🔄 Core Environmental scan cycle will run every 60 seconds")


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
