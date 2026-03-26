import os
import json
import asyncio
from typing import Callable, Dict, Any, Optional
import redis.asyncio as redis
from kortana.logger import get_logger

logger = get_logger("hive_bus")

class HiveBus:
    """
    The central nervous system of Phase 9's Fractal Swarm.
    Uses Redis Pub/Sub for decentralized agent-to-agent communication.
    """
    def __init__(self, url: Optional[str] = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis: Optional[redis.Redis[str]] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self._callbacks: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self._listen_task: Optional[asyncio.Task[None]] = None

    async def connect(self) -> None:
        if not self.redis:
            self.redis = redis.from_url(self.url, decode_responses=True)
            self.pubsub = self.redis.pubsub()
            logger.info("🐝 HiveBus connected to Redis.")

    async def disconnect(self) -> None:
        if self._listen_task:
            self._listen_task.cancel()
        if self.pubsub:
            await self.pubsub.close() # type: ignore
        if self.redis:
            await self.redis.aclose() # type: ignore
            logger.info("🐝 HiveBus disconnected from Redis.")

    async def publish(self, channel: str, message: Dict[str, Any]) -> None:
        if not self.redis:
            await self.connect()
        assert self.redis is not None
        payload = json.dumps(message)
        await self.redis.publish(f"kortana:hive:{channel}", payload)
        logger.debug(f"🐝 Published to {channel}: {payload[:100]}...")

    async def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        if not self.redis or not self.pubsub:
            await self.connect()

        assert self.pubsub is not None
        full_channel = f"kortana:hive:{channel}"
        await self.pubsub.subscribe(full_channel)
        self._callbacks[full_channel] = callback
        logger.info(f"🐝 HiveBus subscribed to {full_channel}")

        if not self._listen_task:
            self._listen_task = asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        assert self.pubsub is not None
        try:
            async for message in self.pubsub.listen(): # type: ignore
                if message["type"] == "message":
                    channel = message["channel"]
                    data_str = message["data"]
                    try:
                        data = json.loads(data_str)
                        if channel in self._callbacks:
                            # We could await the callback if it's async, but
                            # we'll keep it simple: spawn a task or call directly.
                            callback = self._callbacks[channel]
                            if asyncio.iscoroutinefunction(callback):
                                asyncio.create_task(callback(data)) # type: ignore
                            else:
                                callback(data)
                    except json.JSONDecodeError:
                        logger.error(f"🐝 Failed to decode message on {channel}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"🐝 HiveBus listen loop crashed: {e}")

hive_bus = HiveBus()
