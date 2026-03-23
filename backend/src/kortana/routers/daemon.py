"""
Autonomy Daemon API Router

Monitor and control the self-sustaining autonomy daemon.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.kortana.services.autonomy_daemon import get_autonomy_daemon

router = APIRouter(prefix="/api/daemon", tags=["daemon"])


@router.get("/status")
async def daemon_status() -> dict:
    """Return autonomy daemon status and metrics."""
    daemon = get_autonomy_daemon()
    return daemon.get_status()


@router.post("/start")
async def daemon_start() -> dict:
    """Start the autonomy daemon if not already running."""
    daemon = get_autonomy_daemon()
    await daemon.start()
    return {"status": "started", **daemon.get_status()}


@router.post("/stop")
async def daemon_stop() -> dict:
    """Gracefully stop the autonomy daemon."""
    daemon = get_autonomy_daemon()
    await daemon.stop()
    return {"status": "stopped", **daemon.get_status()}
