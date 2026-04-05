"""
Autonomy Daemon API Router

Monitor local daemon state in embedded mode and report external daemon
liveness in split-service deployments.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.config import get_settings
from src.kortana.database import get_db
from src.kortana.models import AutonomyCycleMemory
from src.kortana.services.autonomy_daemon import get_autonomy_daemon

router = APIRouter(prefix="/api/daemon", tags=["daemon"])


def _daemon_runs_in_process() -> bool:
    return os.getenv("KORTANA_DAEMON_IN_PROCESS", "false").lower() == "true"


def _stale_after_seconds() -> int:
    return max(get_settings().AUTONOMY_CYCLE_INTERVAL * 3, 300)


def _provider_health_from_metrics(metrics: Any) -> dict[str, str]:
    if isinstance(metrics, dict):
        provider_health = metrics.get("provider_health")
        if isinstance(provider_health, dict):
            return {
                str(provider): str(status)
                for provider, status in provider_health.items()
            }
    return {}


async def _external_daemon_status(db: AsyncSession) -> dict[str, Any]:
    stale_after = _stale_after_seconds()
    try:
        result = await db.execute(
            select(AutonomyCycleMemory)
            .order_by(AutonomyCycleMemory.end_time.desc())
            .limit(1)
        )
    except SQLAlchemyError as exc:
        return {
            "alive": False,
            "state": "unknown",
            "message": f"Unable to read daemon cycle memory: {exc}",
            "stale_after_seconds": stale_after,
        }

    latest = result.scalar_one_or_none()
    if latest is None or latest.end_time is None:
        return {
            "alive": False,
            "state": "unknown",
            "message": "No recorded daemon cycles yet",
            "stale_after_seconds": stale_after,
        }

    seconds_since_last_cycle = max(
        0,
        int((datetime.utcnow() - latest.end_time).total_seconds()),
    )
    alive = seconds_since_last_cycle <= stale_after
    provider_health = _provider_health_from_metrics(latest.metrics)
    return {
        "alive": alive,
        "state": "alive" if alive else "stale",
        "message": (
            "External daemon cycle memory is fresh"
            if alive
            else "External daemon cycle memory is stale"
        ),
        "last_cycle_id": latest.cycle_id,
        "last_cycle_completed_at": latest.end_time.isoformat(),
        "seconds_since_last_cycle": seconds_since_last_cycle,
        "stale_after_seconds": stale_after,
        "tasks_processed": latest.tasks_processed,
        "errors_encountered": latest.errors_encountered,
        "provider_health": provider_health,
    }


@router.get("/status")
async def daemon_status(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return daemon status for embedded or external deployments."""
    daemon = get_autonomy_daemon()
    local_status = daemon.get_status()
    if _daemon_runs_in_process():
        return {
            "deployment_mode": "embedded",
            "control_available": True,
            "message": "Daemon is hosted in this web process.",
            **local_status,
        }

    external_status = await _external_daemon_status(db)
    return {
        "deployment_mode": "external",
        "control_available": False,
        "message": (
            "Daemon is managed by a dedicated worker process; "
            "web start/stop controls are disabled."
        ),
        "local_process": {
            "running": local_status["running"],
            "enabled": local_status["enabled"],
        },
        "provider_health": external_status.get("provider_health", {}),
        "external_daemon": external_status,
    }


@router.post("/start")
async def daemon_start() -> dict[str, Any]:
    """Start the autonomy daemon if this process is the embedded host."""
    if not _daemon_runs_in_process():
        raise HTTPException(
            status_code=409,
            detail=(
                "Daemon is deployed as a dedicated worker process. "
                "Set KORTANA_DAEMON_IN_PROCESS=true only for embedded deployments."
            ),
        )

    daemon = get_autonomy_daemon()
    if not daemon.enabled:
        return {"status": "disabled", **daemon.get_status()}
    await daemon.start()
    return {
        "status": "running" if daemon._running else "stopped",
        **daemon.get_status(),
    }


@router.post("/stop")
async def daemon_stop() -> dict[str, Any]:
    """Stop the autonomy daemon if this process is the embedded host."""
    if not _daemon_runs_in_process():
        raise HTTPException(
            status_code=409,
            detail=(
                "Daemon is deployed as a dedicated worker process. "
                "Set KORTANA_DAEMON_IN_PROCESS=true only for embedded deployments."
            ),
        )

    daemon = get_autonomy_daemon()
    await daemon.stop()
    return {
        "status": "stopped" if not daemon._running else "running",
        **daemon.get_status(),
    }


@router.get("/cycles")
async def daemon_cycles(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return recent autonomy cycle history, newest first."""
    try:
        result = await db.execute(
            select(AutonomyCycleMemory)
            .order_by(AutonomyCycleMemory.end_time.desc())
            .limit(limit)
        )
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    cycles = result.scalars().all()
    return [
        {
            "cycle_id": c.cycle_id,
            "start_time": c.start_time.isoformat() if c.start_time else None,
            "end_time": c.end_time.isoformat() if c.end_time else None,
            "tasks_processed": c.tasks_processed,
            "approvals_processed": c.approvals_processed,
            "errors_encountered": c.errors_encountered,
            "metrics": c.metrics,
        }
        for c in cycles
    ]
