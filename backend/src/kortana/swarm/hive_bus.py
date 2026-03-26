"""Redis-backed event bus for the Phase 9 swarm."""

from __future__ import annotations

import asyncio
import inspect
import json
import os
from collections import defaultdict
from typing import Any, Callable

import redis.asyncio as redis

from src.kortana.logger import get_logger

logger = get_logger(__name__)

BusCallback = Callable[[dict[str, Any]], Any]


class HiveBus:
    """Redis Pub/Sub communication backbone for the swarm."""

    prefix = "kortana:hive"

    def __init__(self, url: str | None = None) -> None:
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis: redis.Redis | None = None
        self.pubsub: redis.client.PubSub | None = None
        self._callbacks: dict[str, list[BusCallback]] = defaultdict(list)
        self._listen_task: asyncio.Task[None] | None = None
        self._connected = False
        self._published_count = 0
        self._last_error: str | None = None

    def _full_channel(self, channel: str) -> str:
        return f"{self.prefix}:{channel}"

    async def connect(self) -> bool:
        """Connect to Redis and validate Pub/Sub readiness."""
        if self._connected and self.redis and self.pubsub:
            return True

        try:
            self.redis = redis.from_url(self.url, decode_responses=True)
            await self.redis.ping()
            self.pubsub = self.redis.pubsub()
            self._connected = True
            self._last_error = None
            logger.info(f"HiveBus connected to Redis at {self.url}")
            return True
        except Exception as exc:
            self._connected = False
            self._last_error = str(exc)
            logger.warning(f"HiveBus unavailable: {exc}")
            if self.pubsub is not None:
                try:
                    await self.pubsub.close()
                except Exception:
                    pass
            if self.redis is not None:
                try:
                    await self.redis.aclose()
                except Exception:
                    pass
            self.pubsub = None
            self.redis = None
            return False

    async def disconnect(self) -> None:
        """Close the listener task and Redis connections."""
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        self._listen_task = None
        if self.pubsub is not None:
            await self.pubsub.close()
        if self.redis is not None:
            await self.redis.aclose()
        self.pubsub = None
        self.redis = None
        self._connected = False
        logger.info("HiveBus disconnected")

    async def publish(self, channel: str, message: dict[str, Any]) -> bool:
        """Publish a message. Returns False when Redis is unavailable."""
        if not await self.connect():
            return False
        assert self.redis is not None
        payload = json.dumps(message, default=str)
        await self.redis.publish(self._full_channel(channel), payload)
        self._published_count += 1
        logger.debug(f"HiveBus published to {channel}: {payload[:160]}")
        return True

    async def subscribe(self, channel: str, callback: BusCallback) -> bool:
        """Subscribe a callback to a logical channel."""
        if not await self.connect():
            return False

        assert self.pubsub is not None
        full_channel = self._full_channel(channel)
        callbacks = self._callbacks[full_channel]
        if callback not in callbacks:
            callbacks.append(callback)
        await self.pubsub.subscribe(full_channel)
        logger.info(f"HiveBus subscribed to {full_channel}")

        if self._listen_task is None or self._listen_task.done():
            self._listen_task = asyncio.create_task(self._listen())
        return True

    async def _listen(self) -> None:
        """Listen for Pub/Sub events and dispatch callbacks."""
        assert self.pubsub is not None
        try:
            async for message in self.pubsub.listen():
                if message.get("type") != "message":
                    continue

                channel = message.get("channel")
                data_str = message.get("data")
                if not isinstance(channel, str) or not isinstance(data_str, str):
                    continue

                try:
                    payload = json.loads(data_str)
                except json.JSONDecodeError:
                    logger.error(f"HiveBus failed to decode payload on {channel}")
                    continue

                for callback in self._callbacks.get(channel, []):
                    try:
                        result = callback(payload)
                        if inspect.isawaitable(result):
                            asyncio.create_task(result)
                    except Exception as exc:
                        logger.error(f"HiveBus callback failed on {channel}: {exc}")
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            self._connected = False
            self._last_error = str(exc)
            logger.error(f"HiveBus listen loop crashed: {exc}")

    def get_status(self) -> dict[str, Any]:
        """Return connection and subscription state."""
        return {
            "url": self.url,
            "connected": self._connected,
            "subscriptions": sorted(self._callbacks.keys()),
            "published_count": self._published_count,
            "last_error": self._last_error,
        }


hive_bus = HiveBus()
