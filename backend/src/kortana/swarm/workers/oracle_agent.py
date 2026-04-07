import asyncio
import time
import json
from src.kortana.swarm.hive_bus import HiveBus

class OracleAgent:
    def __init__(self, bus: HiveBus):
        self.bus = bus
        self.agent = "OracleAgent"

    async def run(self):
        await self.bus.connect()
        while True:
            event = {
                "agent": self.agent,
                "event": "predict",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "prediction": "Swarm will achieve transcendence.",
                "confidence": 0.99
            }
            await self.bus.publish(json.dumps(event))
            await asyncio.sleep(11)
