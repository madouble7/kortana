"""
KOR'TANA Enhanced Health Checks
Multi-tier health monitoring for dependencies and services
"""

import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse


class HealthStatus(str, Enum):
    """Health check status values"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    """Component types for health checks"""

    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    DISK = "disk"
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"
    CELERY = "celery"


@dataclass
class ComponentHealth:
    """Health status for a single component"""

    name: str
    component_type: ComponentType
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0
    details: Dict[str, Any] = field(default_factory=dict)
    last_checked: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.component_type.value,
            "status": self.status.value,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "details": self.details,
            "last_checked": self.last_checked,
        }


class HealthChecker:
    """Comprehensive health check manager"""

    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {}
        self._check_interval: int = 30  # seconds
        self._last_full_check: Optional[datetime] = None
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: int = 10  # seconds

    def register_component(
        self,
        name: str,
        component_type: ComponentType,
        check_func,
    ) -> None:
        """Register a component for health checking"""
        self.components[name] = ComponentHealth(
            name=name,
            component_type=component_type,
            status=HealthStatus.UNKNOWN,
            message="Not checked yet",
        )

    async def check_database(
        self,
        host: str = "localhost",
        port: int = 5432,
        dbname: str = "kortana",
        user: str = None,
        password: str = None,
        timeout: int = 5,
    ) -> ComponentHealth:
        """Check database connectivity"""
        start = time.perf_counter()
        try:
            # Try to connect to PostgreSQL
            import asyncpg

            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host=host,
                    port=port,
                    database=dbname,
                    user=user,
                    password=password,
                ),
                timeout=timeout,
            )
            await conn.fetchval("SELECT 1")
            await conn.close()

            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="postgresql",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                latency_ms=latency,
                details={
                    "host": host,
                    "port": port,
                    "database": dbname,
                },
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="postgresql",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                latency_ms=latency,
                details={"error": str(e)},
            )

    async def check_redis(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        timeout: int = 5,
    ) -> ComponentHealth:
        """Check Redis connectivity"""
        start = time.perf_counter()
        try:
            import redis.asyncio as redis

            client = redis.Redis(
                host=host,
                port=port,
                password=password,
                socket_timeout=timeout,
                socket_connect_timeout=timeout,
            )
            await client.ping()
            await client.close()

            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="redis",
                component_type=ComponentType.CACHE,
                status=HealthStatus.HEALTHY,
                message="Redis connection successful",
                latency_ms=latency,
                details={"host": host, "port": port},
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="redis",
                component_type=ComponentType.CACHE,
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}",
                latency_ms=latency,
                details={"error": str(e)},
            )

    async def check_celery(
        self,
        broker_url: str = "redis://localhost:6379/0",
        timeout: int = 10,
    ) -> ComponentHealth:
        """Check Celery task queue status"""
        start = time.perf_counter()
        try:
            from celery import Celery

            # Create a minimal Celery app for health check
            app = Celery("health_check", broker=broker_url)

            # Try to inspect active workers
            inspect = app.control.inspect()

            # Check for active workers
            active_workers = inspect.active() or {}
            stats = inspect.stats() or {}

            latency = (time.perf_counter() - start) * 1000

            worker_count = len(active_workers)
            if worker_count > 0:
                status = HealthStatus.HEALTHY
                message = f"Celery healthy with {worker_count} active worker(s)"
            else:
                status = HealthStatus.DEGRADED
                message = "Celery broker accessible but no active workers"

            return ComponentHealth(
                name="celery",
                component_type=ComponentType.CELERY,
                status=status,
                message=message,
                latency_ms=latency,
                details={
                    "broker_url": broker_url,
                    "active_workers": worker_count,
                    "worker_stats": bool(stats),
                },
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="celery",
                component_type=ComponentType.CELERY,
                status=HealthStatus.UNHEALTHY,
                message=f"Celery check failed: {str(e)}",
                latency_ms=latency,
                details={"error": str(e), "broker_url": broker_url},
            )

    def check_system_resources(self) -> List[ComponentHealth]:
        """Check system resource usage"""
        components = []

        # Memory check
        memory = psutil.virtual_memory()
        memory_status = HealthStatus.HEALTHY
        if memory.percent > 90:
            memory_status = HealthStatus.UNHEALTHY
        elif memory.percent > 75:
            memory_status = HealthStatus.DEGRADED

        components.append(
            ComponentHealth(
                name="memory",
                component_type=ComponentType.MEMORY,
                status=memory_status,
                message=f"Memory usage: {memory.percent}%",
                details={
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent,
                },
            )
        )

        # CPU check (non-blocking - instant snapshot without interval sleep)
        cpu_percent = psutil.cpu_percent(interval=0)  # interval=0 returns instant value
        cpu_status = HealthStatus.HEALTHY
        if cpu_percent > 90:
            cpu_status = HealthStatus.UNHEALTHY
        elif cpu_percent > 75:
            cpu_status = HealthStatus.DEGRADED

        components.append(
            ComponentHealth(
                name="cpu",
                component_type=ComponentType.CPU,
                status=cpu_status,
                message=f"CPU usage: {cpu_percent}%",
                details={
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                },
            )
        )

        # Disk check
        disk = psutil.disk_usage("/")
        disk_percent = disk.percent
        disk_status = HealthStatus.HEALTHY
        if disk_percent > 90:
            disk_status = HealthStatus.UNHEALTHY
        elif disk_percent > 75:
            disk_status = HealthStatus.DEGRADED

        components.append(
            ComponentHealth(
                name="disk",
                component_type=ComponentType.DISK,
                status=disk_status,
                message=f"Disk usage: {disk_percent}%",
                details={
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "percent": disk_percent,
                },
            )
        )

        return components

    async def check_external_api(
        self,
        name: str,
        url: str,
        expected_status: int = 200,
        timeout: int = 10,
    ) -> ComponentHealth:
        """Check external API connectivity"""
        start = time.perf_counter()
        try:
            import httpx

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, follow_redirects=True)
                latency = (time.perf_counter() - start) * 1000

                if response.status_code == expected_status:
                    return ComponentHealth(
                        name=name,
                        component_type=ComponentType.EXTERNAL_API,
                        status=HealthStatus.HEALTHY,
                        message=f"API responded with {response.status_code}",
                        latency_ms=latency,
                        details={
                            "url": url,
                            "status": response.status_code,
                        },
                    )
                else:
                    return ComponentHealth(
                        name=name,
                        component_type=ComponentType.EXTERNAL_API,
                        status=HealthStatus.DEGRADED,
                        message=f"API returned {response.status_code}, expected {expected_status}",
                        latency_ms=latency,
                        details={
                            "url": url,
                            "status": response.status_code,
                            "expected": expected_status,
                        },
                    )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name=name,
                component_type=ComponentType.EXTERNAL_API,
                status=HealthStatus.UNHEALTHY,
                message=f"API check failed: {str(e)}",
                latency_ms=latency,
                details={"url": url, "error": str(e)},
            )

    async def run_full_check(
        self,
        check_db: bool = True,
        check_redis: bool = True,
        check_celery: bool = True,
        check_external: bool = True,
    ) -> Dict[str, Any]:
        """Run comprehensive health check"""
        results = []
        overall_status = HealthStatus.HEALTHY

        # Check system resources
        results.extend(self.check_system_resources())

        # Check database if requested
        if check_db:
            db_health = await self.check_database()
            results.append(db_health)

        # Check Redis if requested
        if check_redis:
            redis_health = await self.check_redis()
            results.append(redis_health)

        # Check Celery if requested
        if check_celery:
            celery_health = await self.check_celery()
            results.append(celery_health)

        # Check external APIs if requested
        if check_external:
            # GitHub API
            github_health = await self.check_external_api(
                name="github_api",
                url="https://api.github.com",
                expected_status=200,
                timeout=10,
            )
            results.append(github_health)

            # Gemini API (Google AI Platform)
            gemini_health = await self.check_external_api(
                name="gemini_api",
                url="https://generativelanguage.googleapis.com",
                expected_status=200,
                timeout=10,
            )
            results.append(gemini_health)

            # Stripe API
            stripe_health = await self.check_external_api(
                name="stripe_api",
                url="https://api.stripe.com",
                expected_status=200,
                timeout=10,
            )
            results.append(stripe_health)

        # Determine overall status
        for result in results:
            if result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
                break
            elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED

        self._last_full_check = datetime.now()

        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "components": [r.to_dict() for r in results],
            "summary": {
                "total": len(results),
                "healthy": len([r for r in results if r.status == HealthStatus.HEALTHY]),
                "degraded": len([r for r in results if r.status == HealthStatus.DEGRADED]),
                "unhealthy": len([r for r in results if r.status == HealthStatus.UNHEALTHY]),
            },
        }

    def get_cached_check(self, max_age_seconds: int = 10) -> Optional[Dict[str, Any]]:
        """Get cached health check result"""
        if not self._cache:
            return None

        cached_time = self._cache.get("timestamp")
        if not cached_time:
            return None

        cached_datetime = datetime.fromisoformat(cached_time)
        if datetime.now() - cached_datetime > timedelta(seconds=max_age_seconds):
            return None

        return self._cache

    def set_cached_check(self, result: Dict[str, Any]) -> None:
        """Cache health check result"""
        self._cache = result


# Global health checker
health_checker = HealthChecker()

# Create router
router = APIRouter(tags=["health"])


@router.get("/")
async def basic_health():
    """Basic health check - always returns 200"""
    return {
        "status": "alive",
        "message": "Kor'tana backend is breathing",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/detailed")
async def detailed_health():
    """Detailed health check with all components"""
    # Check cache first
    cached = health_checker.get_cached_check()
    if cached:
        return JSONResponse(content=cached)

    # Run full check
    result = await health_checker.run_full_check()
    health_checker.set_cached_check(result)

    return JSONResponse(content=result)


@router.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness probe"""
    result = await health_checker.run_full_check()

    if result["status"] == "unhealthy":
        raise HTTPException(
            status_code=503,
            detail=result,
        )

    return result


@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/metrics")
async def health_metrics():
    """Health check metrics for monitoring"""
    result = await health_checker.run_full_check()

    return {
        "timestamp": datetime.now().isoformat(),
        "status": result["status"],
        "component_count": result["summary"]["total"],
        "healthy_components": result["summary"]["healthy"],
        "degraded_components": result["summary"]["degraded"],
        "unhealthy_components": result["summary"]["unhealthy"],
    }


# System info endpoint
@router.get("/system")
async def system_info():
    """Get system information"""
    return {
        "timestamp": datetime.now().isoformat(),
        "python_version": os.sys.version,
        "platform": os.sys.platform,
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "disk_total_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
        "process_memory_mb": round(psutil.Process().memory_info().rss / (1024**2), 2),
        "process_cpu_percent": psutil.Process().cpu_percent(interval=0),
    }
