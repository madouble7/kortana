"""
Distributed Task Locking for Horizontal Scaling
Ensures only one instance executes critical autonomous cycles
Uses Redis for distributed mutual exclusion (mutex)
"""

import time
import uuid

from redis import Redis
from redis.exceptions import RedisError

from src.kortana.logger import get_logger

logger = get_logger(__name__)


class DistributedLock:
    """
    Redis-based distributed mutual exclusion lock
    Prevents multiple workers from executing same critical task
    """

    def __init__(
        self,
        redis_client: Redis,
        lock_name: str,
        timeout: int = 300,  # 5 minutes
        auto_renewal: bool = False,
    ):
        """
        Initialize distributed lock

        Args:
            redis_client: Redis connection
            lock_name: Unique name for this lock
            timeout: Lock TTL in seconds
            auto_renewal: Auto-renew lock while held
        """
        self.redis = redis_client
        self.lock_name = lock_name
        self.timeout = timeout
        self.auto_renewal = auto_renewal
        self.lock_id = str(uuid.uuid4())  # Unique identifier for this lock holder
        self.acquired = False
        self.prefix = "lock:"

    def _get_lock_key(self) -> str:
        """Get Redis key for lock"""
        return f"{self.prefix}{self.lock_name}"

    def acquire(self, blocking: bool = True, wait_time: int = 30) -> bool:
        """
        Acquire the lock

        Args:
            blocking: Wait for lock if busy
            wait_time: Max seconds to wait if blocking

        Returns:
            True if lock acquired, False otherwise
        """
        start_time = time.time()
        key = self._get_lock_key()

        while True:
            try:
                # Try to acquire lock (SET NX = set if not exists)
                acquired = self.redis.set(
                    key,
                    self.lock_id,
                    ex=self.timeout,
                    nx=True,
                )

                if acquired:
                    self.acquired = True
                    logger.debug(f"Lock acquired: {self.lock_name}")
                    return True

                if not blocking:
                    logger.debug(f"Lock not available (non-blocking): {self.lock_name}")
                    return False

                # Check timeout
                if time.time() - start_time > wait_time:
                    logger.warning(
                        f"Lock acquisition timeout: {self.lock_name} (waited {wait_time}s)"
                    )
                    return False

                # Wait before retrying
                time.sleep(0.1)

            except RedisError as e:
                logger.warning(
                    "Redis unavailable for lock '%s'; proceeding without lock: %s",
                    self.lock_name,
                    e,
                )
                return True

    def release(self) -> bool:
        """
        Release the lock

        Returns:
            True if lock released, False if not held
        """
        if not self.acquired:
            return False

        try:
            key = self._get_lock_key()

            # Only release if we still own it (compare lock_id)
            current_holder = self.redis.get(key)
            if current_holder and current_holder.decode() == self.lock_id:
                self.redis.delete(key)
                self.acquired = False
                logger.debug(f"Lock released: {self.lock_name}")
                return True

            logger.warning(
                f"Lock already released or taken by another: {self.lock_name}"
            )
            return False

        except RedisError as e:
            logger.error(f"Redis error during lock release: {e}")
            return False

    def renew(self) -> bool:
        """
        Renew lock TTL (extend timeout)
        Useful for long-running tasks

        Returns:
            True if renewed, False if not held
        """
        if not self.acquired:
            return False

        try:
            key = self._get_lock_key()

            # Verify we still own the lock
            current_holder = self.redis.get(key)
            if current_holder and current_holder.decode() == self.lock_id:
                self.redis.expire(key, self.timeout)
                logger.debug(f"Lock renewed: {self.lock_name}")
                return True

            logger.warning(f"Cannot renew: lock lost or expired: {self.lock_name}")
            self.acquired = False
            return False

        except RedisError as e:
            logger.error(f"Redis error during lock renewal: {e}")
            return False

    def is_held_by_me(self) -> bool:
        """Check if this instance still holds the lock"""
        if not self.acquired:
            return False

        try:
            key = self._get_lock_key()
            current_holder = self.redis.get(key)
            if current_holder and current_holder.decode() == self.lock_id:
                return True
            self.acquired = False
            return False
        except RedisError as e:
            logger.error(f"Redis error checking lock: {e}")
            return False

    def __enter__(self):
        """Context manager support"""
        self.acquire(blocking=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.release()


class TaskLockManager:
    """
    Manages multiple locks for different autonomous tasks
    Ensures critical operations don't run concurrently across instances
    """

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.locks: dict[str, DistributedLock] = {}

    def get_lock(
        self,
        task_name: str,
        timeout: int = 300,
    ) -> DistributedLock:
        """Get or create lock for task"""
        if task_name not in self.locks:
            self.locks[task_name] = DistributedLock(
                self.redis,
                task_name,
                timeout=timeout,
            )
        return self.locks[task_name]

    def acquire_for_task(
        self,
        task_name: str,
        blocking: bool = True,
        wait_time: int = 30,
    ) -> bool:
        """Try to acquire lock for task"""
        lock = self.get_lock(task_name)
        return lock.acquire(blocking=blocking, wait_time=wait_time)

    def release_for_task(self, task_name: str) -> bool:
        """Release lock for task"""
        if task_name in self.locks:
            return self.locks[task_name].release()
        return False

    def is_locked(self, task_name: str) -> bool:
        """Check if task is currently locked"""
        try:
            key = f"lock:{task_name}"
            return self.redis.exists(key) > 0
        except RedisError:
            return False

    def get_all_locks(self) -> dict[str, dict]:
        """Get status of all managed locks"""
        statuses = {}
        try:
            # Find all lock keys
            pattern = "lock:*"
            for key in self.redis.scan_iter(match=pattern):
                task_name = key.decode().replace("lock:", "")
                lock_holder = self.redis.get(key)
                statuses[task_name] = {
                    "held_by": lock_holder.decode() if lock_holder else None,
                    "held_locally": (
                        lock_holder.decode()
                        == self.locks.get(
                            task_name, DistributedLock(self.redis, task_name)
                        ).lock_id
                        if task_name in self.locks
                        else False
                    ),
                }
        except RedisError as e:
            logger.error(f"Error getting lock status: {e}")

        return statuses

    def release_all(self) -> None:
        """Release all locks held by this instance"""
        for lock in self.locks.values():
            lock.release()


def create_task_lock_manager(redis_url: str) -> TaskLockManager:
    """Factory function"""
    import os

    redis_client = Redis.from_url(
        redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    return TaskLockManager(redis_client)
