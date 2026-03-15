"""
Test script for Kor'tana autonomous scheduler and goal processing.
Creates a test goal, runs one scheduler cycle, and logs results.
"""

import os
import sys

# Add project root to sys.path to allow for src.kortana imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import asyncio
import logging

from src.kortana.core.autonomous_tasks import autonomous_goal_processing_cycle
from src.kortana.core.covenant import CovenantEnforcer
from src.kortana.core.goal_manager import GoalManager
from src.kortana.core.memory import MemoryManager
from src.kortana.core.models import GoalType
from src.kortana.services.database import get_db_sync

# Setup logging to a test log file
logging.basicConfig(
    filename="data/autonomous_activity_test.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logger = logging.getLogger(__name__)


async def create_test_goal():
    try:
        covenant_enforcer = CovenantEnforcer()
        logger.info("CovenantEnforcer instantiated.")
    except Exception as e:
        logger.error(f"Failed to instantiate CovenantEnforcer: {e}")
        covenant_enforcer = CovenantEnforcer()

    memory_manager = MemoryManager()
    logger.info("Dummy MemoryManager instantiated.")

    with get_db_sync() as db:
        manager = GoalManager(
            memory_manager=memory_manager,
            covenant_enforcer=covenant_enforcer,
            db_session=db,
        )
        logger.info(
            "GoalManager instantiated with dummy MemoryManager and CovenantEnforcer."
        )

        goal = await manager.create_goal(
            type=GoalType.MAINTENANCE,
            description="Test autonomous task: Log system status",
            priority=3,
        )
        logger.info(f"Created test goal with id: {goal.id}")
        print(f"Created test goal with id: {goal.id}")
        return goal.id


async def run_scheduler_cycle():
    logger.info("Running one autonomous goal processing cycle...")
    print("Running one autonomous goal processing cycle...")
    await autonomous_goal_processing_cycle()
    logger.info("Cycle complete. Check data/autonomous_activity_test.log for results.")
    print("Cycle complete. Check data/autonomous_activity_test.log for results.")


async def main():
    await create_test_goal()
    await run_scheduler_cycle()


if __name__ == "__main__":
    asyncio.run(main())
