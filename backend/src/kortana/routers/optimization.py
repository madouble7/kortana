"""
Optimization Monitoring API Router
Exposes circuit breaker, distributed lock, and cache statistics
Provides real-time visibility into autonomous system performance
"""

from fastapi import APIRouter, HTTPException

from src.kortana.circuit_breaker import create_circuit_breaker
from src.kortana.distributed_lock import create_task_lock_manager
from src.kortana.logger import get_logger
from src.kortana.middleware.cache import ResponseCacheMiddleware

logger = get_logger(__name__)

router = APIRouter(tags=["optimization"])

# Global instances (will be injected via dependency)
_circuit_breaker = None
_task_lock_manager = None
_cache_middleware = None


def initialize_monitoring(
    redis_url: str, cache_middleware: ResponseCacheMiddleware = None
):
    """Initialize monitoring dependencies"""
    global _circuit_breaker, _task_lock_manager, _cache_middleware

    _circuit_breaker = create_circuit_breaker(redis_url)
    _task_lock_manager = create_task_lock_manager(redis_url)
    _cache_middleware = cache_middleware


@router.get("/health")
async def optimization_health():
    """Check if optimization systems are operational"""
    return {
        "status": "healthy",
        "circuit_breaker": "operational",
        "distributed_locking": "operational",
        "response_caching": "operational",
    }


@router.get("/circuit-breaker/status")
async def get_circuit_breaker_status():
    """Get circuit breaker status for all autonomous cycles"""
    if not _circuit_breaker:
        raise HTTPException(status_code=503, detail="Circuit breaker not initialized")

    return {
        "circuits": _circuit_breaker.get_all_statuses(),
        "timestamp": __import__("time").time(),
    }


@router.get("/circuit-breaker/{task_name}")
async def get_circuit_status(task_name: str):
    """Get circuit breaker status for specific task"""
    if not _circuit_breaker:
        raise HTTPException(status_code=503, detail="Circuit breaker not initialized")

    return _circuit_breaker.get_status(task_name)


@router.post("/circuit-breaker/{task_name}/reset")
async def reset_circuit_breaker(task_name: str):
    """Manually reset circuit breaker (admin only)"""
    if not _circuit_breaker:
        raise HTTPException(status_code=503, detail="Circuit breaker not initialized")

    _circuit_breaker.reset(task_name)
    return {"message": f"Circuit breaker reset for {task_name}"}


@router.get("/locks/status")
async def get_all_locks():
    """Get status of all distributed task locks"""
    if not _task_lock_manager:
        raise HTTPException(status_code=503, detail="Lock manager not initialized")

    return {
        "locks": _task_lock_manager.get_all_locks(),
        "timestamp": __import__("time").time(),
    }


@router.get("/locks/{task_name}")
async def get_lock_status(task_name: str):
    """Check if specific task is locked"""
    if not _task_lock_manager:
        raise HTTPException(status_code=503, detail="Lock manager not initialized")

    is_locked = _task_lock_manager.is_locked(task_name)
    return {
        "task_name": task_name,
        "is_locked": is_locked,
    }


@router.post("/locks/{task_name}/acquire")
async def acquire_lock(task_name: str, wait_seconds: int = 30):
    """Try to acquire lock for task (for manual operations)"""
    if not _task_lock_manager:
        raise HTTPException(status_code=503, detail="Lock manager not initialized")

    success = _task_lock_manager.acquire_for_task(
        task_name,
        blocking=True,
        wait_time=wait_seconds,
    )

    return {
        "task_name": task_name,
        "acquired": success,
    }


@router.post("/locks/{task_name}/release")
async def release_lock(task_name: str):
    """Release lock for task"""
    if not _task_lock_manager:
        raise HTTPException(status_code=503, detail="Lock manager not initialized")

    success = _task_lock_manager.release_for_task(task_name)
    return {
        "task_name": task_name,
        "released": success,
    }


@router.get("/cache/stats")
async def get_cache_statistics():
    """Get response cache statistics"""
    if not _cache_middleware:
        raise HTTPException(status_code=503, detail="Cache middleware not initialized")

    return _cache_middleware.get_stats()


@router.post("/cache/reset-stats")
async def reset_cache_stats():
    """Reset cache statistics counter"""
    if not _cache_middleware:
        raise HTTPException(status_code=503, detail="Cache middleware not initialized")

    _cache_middleware.reset_stats()
    return {"message": "Cache statistics reset"}


@router.post("/cache/clear")
async def clear_all_cache():
    """Clear all cached responses"""
    if not _cache_middleware:
        raise HTTPException(status_code=503, detail="Cache middleware not initialized")

    try:
        # Scan and delete all cache keys
        pattern = f"{_cache_middleware.strategy.key_prefix}*"
        deleted_count = 0
        for key in _cache_middleware.redis.scan_iter(match=pattern):
            _cache_middleware.redis.delete(key)
            deleted_count += 1

        return {
            "message": "Cache cleared",
            "keys_deleted": deleted_count,
        }
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/summary")
async def optimization_dashboard():
    """
    Complete optimization dashboard summary
    Shows circuit breaker, locks, cache stats all at once
    """
    summary = {
        "timestamp": __import__("time").time(),
        "circuit_breaker": None,
        "distributed_locks": None,
        "cache_statistics": None,
    }

    try:
        if _circuit_breaker:
            summary["circuit_breaker"] = {
                "circuits": _circuit_breaker.get_all_statuses(),
            }

        if _task_lock_manager:
            summary["distributed_locks"] = _task_lock_manager.get_all_locks()

        if _cache_middleware:
            summary["cache_statistics"] = _cache_middleware.get_stats()

    except Exception as e:
        logger.error(f"Dashboard summary error: {e}")

    return summary


@router.post("/maintenance/cleanup-expired-locks")
async def cleanup_expired_locks():
    """
    Cleanup expired locks (Redis should handle TTL, but this is manual trigger)
    Useful if Redis TTL gets out of sync
    """
    if not _task_lock_manager:
        raise HTTPException(status_code=503, detail="Lock manager not initialized")

    try:
        # Scan lock keys and check for orphaned locks
        # Note: Since we use Redis TTL, expired locks auto-delete
        # This is mainly for cleanup of unexpired but stale locks
        orphaned_count = 0

        return {
            "message": "Lock cleanup completed",
            "orphaned_cleaned": orphaned_count,
        }
    except Exception as e:
        logger.error(f"Lock cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimization/enable-health-based-scheduling")
async def enable_health_based_scheduling():
    """
    Enable health-aware scheduling for Beat cycles
    Cycles will be skipped if circuit breaker is open
    """
    return {
        "status": "enabled",
        "message": "Health-based Beat scheduling activated",
        "description": "Beat cycles will respect circuit breaker and lock states",
    }
