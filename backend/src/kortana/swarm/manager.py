import asyncio
import logging
from .hive_bus import HiveBus
from .workers.architect_agent import ArchitectAgent
from .workers.devops_agent import DevOpsSentinel
from .workers.oracle_agent import OracleAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

class SwarmManager:
    """
    Bootstraps the Multi-Agent Hive.
    """
    def __init__(self):
        self.logger = logging.getLogger("SwarmManager")
        self.bus = HiveBus()
        self.workers = []

    async def boot(self):
        self.logger.info("Initializing SwarmManager... Awakening Vanguard Phase 10")
        await self.bus.connect()

        # Instantiate specialized agents
        architect = ArchitectAgent(self.bus)
        devops = DevOpsSentinel(self.bus)
        oracle = OracleAgent(self.bus)

        self.workers = [
            asyncio.create_task(architect.run()),
            asyncio.create_task(devops.run()),
            asyncio.create_task(oracle.run())
        ]

        self.logger.info("Swarm fully online. All layers synchronized.")

        # Keep process alive
        await asyncio.gather(*self.workers)

if __name__ == "__main__":
    manager = SwarmManager()
    try:
        asyncio.run(manager.boot())
    except KeyboardInterrupt:
        print("Swarm daemon shutting down gracefully.")
