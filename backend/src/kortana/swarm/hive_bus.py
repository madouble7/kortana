import redis.asyncio as redis
import os
import json
import logging

class HiveBus:
    """
    Redis Pub/Sub Matrix for the Fractal Swarm.
    """
    def __init__(self, redis_url=None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.channel = "kortana:hive:bus"
        self._redis = None
        self._pubsub = None

    async def connect(self):
        if not self._redis:
            self._redis = redis.from_url(self.redis_url)
            self._pubsub = self._redis.pubsub()
            await self._pubsub.subscribe(self.channel)

    async def publish(self, message: str):
        if not self._redis:
            await self.connect()
        await self._redis.publish(self.channel, message)

    async def subscribe(self):
        if not self._pubsub:
            await self.connect()
        async for message in self._pubsub.listen():
            if message["type"] == "message":
                yield message["data"].decode("utf-8")

    async def get_history(self, limit=100):
        # Optional method for UI - requires a Redis list to persist history
        pass
