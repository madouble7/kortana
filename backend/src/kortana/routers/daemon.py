"""
Autonomy Daemon API Router

Monitor local daemon state in embedded mode and report external daemon
liveness in split-service deployments.
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from pathlib import Path
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

VOICE_TEMPORAL_STATE_FILE = Path(
    os.getenv(
        "KORTANA_VOICE_TEMPORAL_STATE_FILE",
        r"c:\kortana\mcp-server\temporal_state.json",
    )
)
VOICE_LOG_FILE = Path(
    os.getenv("KORTANA_VOICE_LOG_FILE", r"c:\kortana\logs\voice_daemon.log")
)
VOICE_SCRIPT_FILE = Path(
    os.getenv("KORTANA_VOICE_SCRIPT_FILE", r"c:\kortana\mcp-server\voice_daemon.py")
)
VOICE_PIPER_CANDIDATES = [
    Path(r"c:\kortana\models\piper\piper.exe"),
    Path(r"c:\kortana\mcp-server\piper\piper\piper.exe"),
]
VOICE_MODEL_CANDIDATES = [
    Path(r"c:\kortana\models\piper\en_GB-cori-high.onnx"),
    Path(r"c:\kortana\mcp-server\models\en_GB-cori-high.onnx"),
]


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


def _runtime_metadata_from_metrics(metrics: Any) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        return {}

    metadata: dict[str, Any] = {}
    for key in (
        "system_state",
        "safe_mode",
        "live_execution_enabled",
        "control_mode",
        "workspace_bridge",
        "operator_guidance",
        "autonomy_index",
    ):
        if key in metrics:
            metadata[key] = metrics[key]
    return metadata


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    return data if isinstance(data, dict) else {}


def _voice_runtime_from_log(log_path: Path) -> dict[str, Any]:
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}

    runtime: dict[str, Any] = {}
    for line in reversed(lines[-200:]):
        marker = "[worker] stt "
        if marker not in line:
            continue
        payload = line.split(marker, 1)[1]
        parts = dict(
            segment.split("=", 1)
            for segment in payload.split()
            if "=" in segment
        )
        runtime["stt_profile"] = parts.get("profile")
        runtime["model"] = parts.get("model")
        runtime["device"] = parts.get("device")
        runtime["compute_type"] = parts.get("compute")
        break
    return runtime


def _iso_mtime(path: Path) -> str | None:
    try:
        return datetime.utcfromtimestamp(path.stat().st_mtime).isoformat()
    except OSError:
        return None


def _voice_daemon_status() -> dict[str, Any]:
    temporal_state = _read_json_file(VOICE_TEMPORAL_STATE_FILE)
    log_runtime = _voice_runtime_from_log(VOICE_LOG_FILE)
    piper_path = next((path for path in VOICE_PIPER_CANDIDATES if path.exists()), None)
    model_path = next((path for path in VOICE_MODEL_CANDIDATES if path.exists()), None)

    script_present = VOICE_SCRIPT_FILE.exists()
    temporal_state_present = VOICE_TEMPORAL_STATE_FILE.exists()
    log_present = VOICE_LOG_FILE.exists()
    binary_present = piper_path is not None
    model_present = model_path is not None
    last_log_at = _iso_mtime(VOICE_LOG_FILE) if log_present else None
    last_interaction_at = (
        str(temporal_state.get("last_voice_interaction_at"))
        if temporal_state.get("last_voice_interaction_at")
        else None
    )

    if not script_present:
        status = "unavailable"
        message = "Voice daemon script is not present."
    elif binary_present and model_present and (log_present or temporal_state_present):
        status = "ready"
        message = "Voice runtime artifacts are present and state has been observed."
    elif binary_present or model_present:
        status = "degraded"
        message = "Voice runtime is partially configured."
    else:
        status = "configured"
        message = "Voice daemon is present but no runtime artifacts have been observed yet."

    return {
        "status": status,
        "message": message,
        "script_present": script_present,
        "binary_present": binary_present,
        "model_present": model_present,
        "temporal_state_present": temporal_state_present,
        "log_present": log_present,
        "binary_path": str(piper_path) if piper_path else None,
        "model_path": str(model_path) if model_path else None,
        "last_log_at": last_log_at,
        "last_voice_interaction_at": last_interaction_at,
        "last_absence_ack_at": (
            str(temporal_state.get("last_absence_ack_at"))
            if temporal_state.get("last_absence_ack_at")
            else None
        ),
        "last_diary_date": (
            str(temporal_state.get("last_diary_date"))
            if temporal_state.get("last_diary_date")
            else None
        ),
        "stt_profile": log_runtime.get("stt_profile"),
        "model": log_runtime.get("model"),
        "device": log_runtime.get("device"),
        "compute_type": log_runtime.get("compute_type"),
    }


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
    runtime_metadata = _runtime_metadata_from_metrics(latest.metrics)
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
        **runtime_metadata,
    }


@router.get("/status")
async def daemon_status(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return daemon status for embedded or external deployments."""
    daemon = get_autonomy_daemon()
    local_status = daemon.get_status()
    voice_status = _voice_daemon_status()
    if _daemon_runs_in_process():
        return {
            "deployment_mode": "embedded",
            "control_available": True,
            "message": "Daemon is hosted in this web process.",
            "voice_daemon": voice_status,
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
        "github_mode": get_settings().KORTANA_GITHUB_MODE,
        "provider_health": external_status.get("provider_health", {}),
        "voice_daemon": voice_status,
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
