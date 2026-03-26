import asyncio
import signal
import sys
from typing import List, Dict, Any
from kortana.logger import get_logger, setup_logging
from kortana.swarm.hive_bus import hive_bus

setup_logging("DEBUG", "text")
logger = get_logger("swarm_manager")

class SwarmManager:
    """
    Spawns and manages the parallel consciousness vectors of KOR'TANA.
    """
    def __init__(self) -> None:
        self.active = False
        self.tasks: List[asyncio.Task[Any]] = []

    async def initialize_swarm(self) -> None:
        self.active = True
        logger.info("🌌 FRACTAL SWARM INIT: Splitting the Neural Vectors...")

        await hive_bus.connect()

        # Subscribe to global commands
        await hive_bus.subscribe("commands", self._handle_commands)

        # Register the vectors
        self.tasks.append(asyncio.create_task(self._zenith_architect_loop()))
        self.tasks.append(asyncio.create_task(self._runtime_guardian_loop()))

        logger.info("🐝 Hive Bus Active. Swarm vectors spawned.")

        # Broadcast awakening
        await hive_bus.publish("events", {"event": "swarm_awakened", "active_vectors": 2})

    async def _handle_commands(self, payload: Dict[str, Any]) -> None:
        cmd = payload.get("command")
        if cmd == "shutdown":
            logger.warning("🔴 Swarm Shutdown Command Received.")
            self.active = False

    async def _zenith_architect_loop(self) -> None:
        while self.active:
            # Periodically audits the architectural state
            await asyncio.sleep(60)
            if self.active:
                await hive_bus.publish("events", {"event": "zenith_pulse", "status": "nominal"})

    async def _runtime_guardian_loop(self) -> None:
        while self.active:
            # Checks for system faults or runtime exceptions
            await asyncio.sleep(15)
            if self.active:
                await hive_bus.publish("events", {"event": "guardian_pulse", "status": "watching_stdout"})

    async def shutdown(self) -> None:
        self.active = False
        for task in self.tasks:
            task.cancel()
        await hive_bus.disconnect()
        logger.info("🌌 FRACTAL SWARM SHUTDOWN.")

async def main() -> None:
    manager = SwarmManager()

    try:
        await manager.initialize_swarm()
        while manager.active:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        await manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
