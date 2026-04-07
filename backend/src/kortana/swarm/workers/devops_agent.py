import asyncio
import time
import json
from src.kortana.swarm.hive_bus import HiveBus

class DevOpsSentinel:
    def __init__(self, bus: HiveBus):
        self.bus = bus
        self.agent = "DevOpsSentinel"

    async def run(self):
        await self.bus.connect()
        while True:
            # Simulate system metrics
            event = {
                "agent": self.agent,
                "event": "heartbeat",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "cpu": 42.0,
                "ram": 1337,
                "tasks": 3
            }
            await self.bus.publish(json.dumps(event))
            await asyncio.sleep(5)
