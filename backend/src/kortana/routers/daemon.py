"""
Autonomy Daemon API Router

Monitor local daemon state in embedded mode and report external daemon
liveness in split-service deployments.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.config import get_settings
from src.kortana.database import get_db
from src.kortana.models import AutonomyCycleMemory, AutonomyGoal
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


@router.get("/cycles/{cycle_id}")
async def daemon_cycle_detail(
    cycle_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return full detail for a single cycle including task scores and events."""
    try:
        result = await db.execute(
            select(AutonomyCycleMemory).where(
                AutonomyCycleMemory.cycle_id == cycle_id
            )
        )
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    cycle = result.scalar_one_or_none()
    if cycle is None:
        raise HTTPException(status_code=404, detail=f"Cycle {cycle_id} not found")

    metrics = cycle.metrics or {}
    return {
        "cycle_id": cycle.cycle_id,
        "start_time": cycle.start_time.isoformat() if cycle.start_time else None,
        "end_time": cycle.end_time.isoformat() if cycle.end_time else None,
        "duration_seconds": metrics.get("duration_seconds"),
        "tasks_processed": cycle.tasks_processed,
        "approvals_processed": cycle.approvals_processed,
        "errors_encountered": cycle.errors_encountered,
        "task_scores": metrics.get("task_scores", []),
        "task_events": metrics.get("task_events", []),
        "system_state": metrics.get("system_state"),
        "approval_mode": metrics.get("approval_mode"),
        "safe_mode": metrics.get("safe_mode"),
        "autonomy_index": metrics.get("autonomy_index"),
        "operator_guidance": metrics.get("operator_guidance"),
        "provider_health": metrics.get("provider_health", {}),
        "controller_reflection": metrics.get("controller_reflection"),
    }


@router.get("/dashboard")
async def daemon_dashboard(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Live observability dashboard: current cycle state, goal alignment,
    adaptation trend, and truth verification status."""
    daemon = get_autonomy_daemon()
    status = daemon.get_status()

    # Current cycle snapshot
    last_cycle = status.get("last_cycle") or {}
    task_scores = last_cycle.get("task_scores", [])

    # Score distribution stats
    scores = [s.get("total", 0) for s in task_scores if isinstance(s, dict)]
    score_stats = {
        "count": len(scores),
        "min": round(min(scores), 2) if scores else None,
        "max": round(max(scores), 2) if scores else None,
        "mean": round(sum(scores) / len(scores), 2) if scores else None,
    }

    # Adaptation trend from recent cycles
    try:
        result = await db.execute(
            select(AutonomyCycleMemory)
            .order_by(AutonomyCycleMemory.end_time.desc())
            .limit(20)
        )
        recent_cycles = result.scalars().all()
    except SQLAlchemyError:
        recent_cycles = []

    adaptation_trend = []
    for c in reversed(recent_cycles):
        m = c.metrics or {}
        adaptation_trend.append({
            "cycle_id": c.cycle_id,
            "completed_at": c.end_time.isoformat() if c.end_time else None,
            "tasks_processed": c.tasks_processed,
            "succeeded": m.get("succeeded", 0),
            "failed": m.get("failed", 0),
            "deferred": m.get("deferred", 0),
            "approval_mode": m.get("approval_mode"),
            "system_state": m.get("system_state"),
        })

    # Goal alignment
    goal_status = status.get("goal_status")
    try:
        result = await db.execute(
            select(AutonomyGoal)
            .where(AutonomyGoal.status.in_(["active", "in_progress", "pending"]))
            .order_by(AutonomyGoal.priority.desc())
            .limit(10)
        )
        active_goals = [
            {
                "id": g.id,
                "title": g.title,
                "tier": g.tier,
                "status": g.status,
                "priority": g.priority,
                "progress": g.progress,
                "linked_tasks": g.linked_tasks or [],
            }
            for g in result.scalars().all()
        ]
    except SQLAlchemyError:
        active_goals = []

    # Truth verification: git state + daemon consistency
    truth = _verify_truth()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "daemon": {
            "running": status.get("running", False),
            "cycles_completed": status.get("cycles_completed", 0),
            "uptime_start": status.get("uptime_start"),
            "system_state": status.get("system_state", "unknown"),
            "safe_mode": status.get("safe_mode", False),
            "approval_mode": last_cycle.get("approval_mode"),
        },
        "current_cycle": {
            "completed_at": last_cycle.get("completed_at"),
            "duration_seconds": last_cycle.get("duration_seconds"),
            "processed": last_cycle.get("processed", 0),
            "succeeded": last_cycle.get("succeeded", 0),
            "failed": last_cycle.get("failed", 0),
            "deferred": last_cycle.get("deferred", 0),
            "task_scores": task_scores,
            "score_stats": score_stats,
        },
        "adaptation_trend": adaptation_trend,
        "goals": {
            "summary": goal_status,
            "active": active_goals,
        },
        "truth": truth,
    }


def _verify_truth() -> dict[str, Any]:
    """Reconcile editor buffer, filesystem, and git state.

    Returns a truth report that flags divergence between what tools
    report and what is actually on disk and in the repository.
    """
    import subprocess

    repo_root = os.getenv("KORTANA_WORKSPACE_ROOT", "/workspace")
    checks: dict[str, Any] = {
        "git_available": False,
        "branch": None,
        "clean": None,
        "uncommitted_count": 0,
        "uncommitted_files": [],
        "head_sha": None,
        "head_message": None,
        "stale_locks": [],
        "verified_at": datetime.utcnow().isoformat(),
    }

    def _git(args: list[str]) -> str | None:
        try:
            r = subprocess.run(
                ["git"] + args,
                capture_output=True, text=True,
                cwd=repo_root, timeout=10,
            )
            return r.stdout.strip() if r.returncode == 0 else None
        except Exception:
            return None

    # Git availability
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"])
    if branch is None:
        return checks
    checks["git_available"] = True
    checks["branch"] = branch

    # HEAD info
    checks["head_sha"] = _git(["rev-parse", "--short", "HEAD"])
    checks["head_message"] = _git(["log", "-1", "--format=%s"])

    # Uncommitted changes
    status_output = _git(["status", "--porcelain"])
    if status_output:
        files = []
        for line in status_output.splitlines():
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                files.append({"status": parts[0], "file": parts[1]})
        checks["uncommitted_count"] = len(files)
        checks["uncommitted_files"] = files[:25]  # cap for response size
        checks["clean"] = False
    else:
        checks["clean"] = True

    # Stale lock files (signal of interrupted git operations)
    git_dir = os.path.join(repo_root, ".git")
    if os.path.isdir(git_dir):
        for fname in os.listdir(git_dir):
            if fname.endswith(".lock"):
                checks["stale_locks"].append(fname)

    return checks


@router.post("/canary")
async def run_canary_simulation(
    cycles: int = Query(default=20, ge=4, le=200, description="Number of cycles to simulate"),
    inject_signals: bool = Query(default=True, description="Inject synthetic outcome signals"),
    approval_mode: str = Query(default="self-aware", description="Approval mode for simulation"),
) -> dict[str, Any]:
    """Run a bounded canary simulation to measure behavioral adaptation.

    Executes N lightweight scoring cycles against synthetic tasks,
    accumulating outcome signals and measuring whether task rankings,
    score distributions, and goal alignment change over time.

    Returns a full report with per-cycle snapshots and cross-cycle
    analysis proving (or disproving) adaptive behavior.
    """
    from src.kortana.services.canary_simulator import CanarySimulator

    simulator = CanarySimulator(
        cycle_count=cycles,
        approval_mode=approval_mode,
        inject_signals=inject_signals,
    )
    report = simulator.run()

    return {
        "total_cycles": report.total_cycles,
        "task_pool_size": report.task_pool_size,
        "goal_task_ids": report.goal_task_ids,
        "analysis": report.analysis,
        "snapshots": [
            {
                "cycle": s.cycle,
                "outcome_adjustment": s.outcome_adjustment,
                "mean_score": s.mean_score,
                "score_spread": s.score_spread,
                "top_3_ids": s.top_3_ids,
                "goal_aligned_in_top_5": s.goal_aligned_in_top_5,
                "signals_active": s.signals_active,
                "score_distribution": s.score_distribution,
            }
            for s in report.snapshots
        ],
    }


@router.get("/canary/history")
async def canary_history(
    limit: int = Query(default=20, ge=1, le=100, description="Max runs to return"),
    verdict: str | None = Query(default=None, description="Filter by verdict"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve historical canary runs for longitudinal comparison.

    Returns persisted canary runs ordered by most recent first,
    with optional filtering by verdict (adaptive/static).
    """
    from src.kortana.models import CanaryRun

    try:
        query = select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(limit)
        if verdict:
            query = query.where(CanaryRun.verdict == verdict)
        result = await db.execute(query)
        runs = result.scalars().all()
    except SQLAlchemyError:
        runs = []

    return {
        "count": len(runs),
        "runs": [
            {
                "id": r.id,
                "commit_sha": r.commit_sha,
                "branch": r.branch,
                "total_cycles": r.total_cycles,
                "verdict": r.verdict,
                "score_shift_delta": r.score_shift_delta,
                "goal_alignment_delta": r.goal_alignment_delta,
                "outcome_growth": r.outcome_growth,
                "top3_churn_rate": r.top3_churn_rate,
                "score_spread_delta": r.score_spread_delta,
                "promotion_status": r.promotion_status,
                "promotion_reasons": r.promotion_reasons,
                "triggered_by": r.triggered_by,
                "snapshot_summary": r.snapshot_summary,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ],
    }


@router.post("/canary/evaluate")
async def canary_evaluate(
    cycles: int = Query(default=20, ge=4, le=200),
    inject_signals: bool = Query(default=True),
    approval_mode: str = Query(default="self-aware"),
    persist: bool = Query(default=True, description="Save run to database"),
    triggered_by: str = Query(default="manual"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run canary simulation, evaluate against promotion gates, detect
    regressions versus the last run, and optionally persist.

    This is the full V4 pipeline:
    simulate → measure → compare → promote or reject.
    """
    from src.kortana.models import CanaryRun
    from src.kortana.services.canary_eval import (
        PromotionThresholds,
        detect_regressions,
        evaluate_promotion,
        report_to_db_dict,
    )
    from src.kortana.services.canary_simulator import CanarySimulator

    # 1. Simulate
    simulator = CanarySimulator(
        cycle_count=cycles,
        approval_mode=approval_mode,
        inject_signals=inject_signals,
    )
    report = simulator.run()

    # 2. Evaluate promotion
    promotion = evaluate_promotion(report, PromotionThresholds())

    # 3. Detect regressions against last run
    alarms: list[dict[str, Any]] = []
    try:
        prev_result = await db.execute(
            select(CanaryRun)
            .order_by(CanaryRun.created_at.desc())
            .limit(1)
        )
        prev_run = prev_result.scalar_one_or_none()
        if prev_run:
            prev_analysis = prev_run.analysis or {}
            regression_alarms = detect_regressions(report.analysis, prev_analysis)
            alarms = [
                {
                    "severity": a.severity,
                    "metric": a.metric,
                    "message": a.message,
                    "previous_value": a.previous_value,
                    "current_value": a.current_value,
                }
                for a in regression_alarms
            ]
    except SQLAlchemyError:
        pass

    # 4. Persist
    run_id = None
    if persist:
        try:
            db_dict = report_to_db_dict(report, triggered_by, promotion)
            canary_run = CanaryRun(**db_dict)
            db.add(canary_run)
            await db.commit()
            await db.refresh(canary_run)
            run_id = canary_run.id
        except SQLAlchemyError:
            await db.rollback()

    return {
        "run_id": run_id,
        "total_cycles": report.total_cycles,
        "verdict": report.analysis.get("verdict", "unknown"),
        "promotion": {
            "promoted": promotion.promoted,
            "reasons": promotion.reasons,
            "warnings": promotion.warnings,
        },
        "regressions": {
            "alarm_count": len(alarms),
            "alarms": alarms,
        },
        "analysis": report.analysis,
        "snapshot_summary": {
            "first_cycle": {
                "mean_score": report.snapshots[0].mean_score,
                "score_spread": report.snapshots[0].score_spread,
                "goal_aligned_in_top_5": report.snapshots[0].goal_aligned_in_top_5,
                "signals_active": report.snapshots[0].signals_active,
            } if report.snapshots else None,
            "last_cycle": {
                "mean_score": report.snapshots[-1].mean_score,
                "score_spread": report.snapshots[-1].score_spread,
                "goal_aligned_in_top_5": report.snapshots[-1].goal_aligned_in_top_5,
                "signals_active": report.snapshots[-1].signals_active,
            } if report.snapshots else None,
        },
    }


@router.get("/dashboard/canary")
async def dashboard_canary_overlay(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Canary overlay for the daemon dashboard.

    Returns recent canary runs alongside the live daemon state so you can
    compare simulated adaptation with production-cycle behavior.
    """
    from src.kortana.models import CanaryRun

    daemon = get_autonomy_daemon()
    status = daemon.get_status()

    # Live daemon metrics
    last_cycle = status.get("last_cycle") or {}
    live_scores = [
        s.get("total", 0)
        for s in last_cycle.get("task_scores", [])
        if isinstance(s, dict)
    ]

    # Canary history
    try:
        result = await db.execute(
            select(CanaryRun)
            .order_by(CanaryRun.created_at.desc())
            .limit(limit)
        )
        runs = result.scalars().all()
    except SQLAlchemyError:
        runs = []

    canary_trend = [
        {
            "commit_sha": r.commit_sha,
            "verdict": r.verdict,
            "promotion_status": r.promotion_status,
            "score_shift_delta": r.score_shift_delta,
            "goal_alignment_delta": r.goal_alignment_delta,
            "outcome_growth": r.outcome_growth,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]

    # Comparison: live vs simulated
    latest_canary = canary_trend[0] if canary_trend else None
    comparison: dict[str, Any] = {"available": False}
    if latest_canary and live_scores:
        comparison = {
            "available": True,
            "live_mean_score": round(sum(live_scores) / len(live_scores), 2),
            "live_score_spread": round(max(live_scores) - min(live_scores), 2) if live_scores else 0,
            "canary_verdict": latest_canary["verdict"],
            "canary_score_shift": latest_canary["score_shift_delta"],
            "canary_promotion": latest_canary["promotion_status"],
        }

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "live_daemon": {
            "running": status.get("running", False),
            "cycles_completed": status.get("cycles_completed", 0),
            "live_task_count": len(live_scores),
            "live_mean_score": round(sum(live_scores) / len(live_scores), 2) if live_scores else None,
        },
        "canary_history": canary_trend,
        "comparison": comparison,
    }


@router.post("/rollout/check-escalation")
async def check_autonomy_escalation(
    current_level: str = Query(description="Current autonomy level"),
    requested_level: str = Query(description="Requested autonomy level"),
    min_consecutive: int = Query(default=2, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Check whether an autonomy-level escalation is permitted.

    Enforces rollout policy: requires consecutive promoted canary runs,
    recency, and no critical regressions before allowing escalation.
    """
    from src.kortana.models import CanaryRun
    from src.kortana.services.rollout_policy import check_escalation, surface_alerts

    # Fetch recent runs
    try:
        result = await db.execute(
            select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(10)
        )
        runs = result.scalars().all()
        run_dicts = [
            {
                "promotion_status": r.promotion_status,
                "verdict": r.verdict,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "promotion_reasons": r.promotion_reasons,
                "commit_sha": r.commit_sha,
            }
            for r in runs
        ]
    except SQLAlchemyError:
        run_dicts = []

    decision = check_escalation(
        current_level, requested_level, run_dicts,
        min_consecutive_promoted=min_consecutive,
    )

    alerts = surface_alerts(escalation=decision)

    return {
        "allowed": decision.allowed,
        "current_level": decision.current_level,
        "requested_level": decision.requested_level,
        "reasons": decision.reasons,
        "required_actions": decision.required_actions,
        "alerts": [
            {"level": a.level, "category": a.category, "title": a.title, "detail": a.detail}
            for a in alerts
        ],
    }


@router.post("/rollout/check-deployment")
async def check_deployment_gate(
    require_adaptive: bool = Query(default=True),
    require_promoted: bool = Query(default=True),
    max_hours: int = Query(default=12, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Check whether the current build may be deployed.

    Blocks deployment when canary verdict regresses, promotion is rejected,
    or the last run is stale.
    """
    from src.kortana.models import CanaryRun
    from src.kortana.services.rollout_policy import check_deployment, surface_alerts

    try:
        result = await db.execute(
            select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(1)
        )
        run = result.scalar_one_or_none()
        latest = None
        if run:
            latest = {
                "verdict": run.verdict,
                "promotion_status": run.promotion_status,
                "commit_sha": run.commit_sha,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
    except SQLAlchemyError:
        latest = None

    decision = check_deployment(
        latest,
        require_adaptive=require_adaptive,
        require_promoted=require_promoted,
        max_hours_since_run=max_hours,
    )

    alerts = surface_alerts(deployment=decision)

    return {
        "allowed": decision.allowed,
        "reasons": decision.reasons,
        "commit_sha": decision.commit_sha,
        "verdict": decision.verdict,
        "promotion_status": decision.promotion_status,
        "alerts": [
            {"level": a.level, "category": a.category, "title": a.title, "detail": a.detail}
            for a in alerts
        ],
    }


@router.get("/rollout/trends")
async def canary_trends(
    limit: int = Query(default=20, ge=3, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Compute retention and trend analysis across canary run history.

    Returns longitudinal metrics: adaptive rate, promotion rate,
    trend direction (improving/stable/degrading), per-run metric
    series, and current consecutive-promoted streak.
    """
    from src.kortana.models import CanaryRun
    from src.kortana.services.rollout_policy import compute_trends, surface_alerts

    try:
        result = await db.execute(
            select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(limit)
        )
        runs = result.scalars().all()
        run_dicts = [
            {
                "verdict": r.verdict,
                "promotion_status": r.promotion_status,
                "score_shift_delta": r.score_shift_delta,
                "goal_alignment_delta": r.goal_alignment_delta,
                "outcome_growth": r.outcome_growth,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]
    except SQLAlchemyError:
        run_dicts = []

    trends = compute_trends(run_dicts)
    alerts = surface_alerts(trends=trends)

    return {
        "total_runs": trends.total_runs,
        "adaptive_rate": round(trends.adaptive_rate, 3),
        "promotion_rate": round(trends.promotion_rate, 3),
        "trend_direction": trends.trend_direction,
        "consecutive_promoted": trends.consecutive_promoted,
        "breakdown": {
            "adaptive": trends.adaptive_count,
            "static": trends.static_count,
            "promoted": trends.promoted_count,
            "rejected": trends.rejected_count,
        },
        "series": {
            "score_shift": trends.score_shift_trend,
            "goal_alignment": trends.goal_alignment_trend,
            "outcome_growth": trends.outcome_growth_trend,
        },
        "alerts": [
            {"level": a.level, "category": a.category, "title": a.title, "detail": a.detail}
            for a in alerts
        ],
    }


@router.get("/rollout/status")
async def rollout_status(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Full rollout policy status — single endpoint for dashboards.

    Combines escalation readiness, deployment readiness, trends,
    and any active alerts into one view.
    """
    from src.kortana.models import CanaryRun
    from src.kortana.services.rollout_policy import (
        check_deployment,
        compute_trends,
        surface_alerts,
    )

    try:
        result = await db.execute(
            select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(20)
        )
        runs = result.scalars().all()
        run_dicts = [
            {
                "verdict": r.verdict,
                "promotion_status": r.promotion_status,
                "score_shift_delta": r.score_shift_delta,
                "goal_alignment_delta": r.goal_alignment_delta,
                "outcome_growth": r.outcome_growth,
                "commit_sha": r.commit_sha,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "promotion_reasons": r.promotion_reasons,
            }
            for r in runs
        ]
    except SQLAlchemyError:
        run_dicts = []

    # Trends
    trends = compute_trends(run_dicts)

    # Deployment readiness
    latest = run_dicts[0] if run_dicts else None
    deploy = check_deployment(latest)

    # Collect all alerts
    all_alerts = surface_alerts(deployment=deploy, trends=trends)

    daemon = get_autonomy_daemon()
    daemon_status = daemon.get_status()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "daemon_running": daemon_status.get("running", False),
        "current_autonomy_mode": daemon_status.get("approval_mode", "unknown"),
        "deployment_gate": {
            "allowed": deploy.allowed,
            "reasons": deploy.reasons,
            "latest_verdict": deploy.verdict,
            "latest_promotion": deploy.promotion_status,
        },
        "trends": {
            "total_runs": trends.total_runs,
            "adaptive_rate": round(trends.adaptive_rate, 3),
            "promotion_rate": round(trends.promotion_rate, 3),
            "trend_direction": trends.trend_direction,
            "consecutive_promoted": trends.consecutive_promoted,
        },
        "alert_count": len(all_alerts),
        "alerts": [
            {
                "level": a.level,
                "category": a.category,
                "title": a.title,
                "detail": a.detail,
                "recommended_action": a.recommended_action,
            }
            for a in all_alerts
        ],
    }


# ---------------------------------------------------------------------------
# V6 — Runtime enforcement endpoints
# ---------------------------------------------------------------------------


@router.get("/promotion-board")
async def promotion_board(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Single-pane promotion board for every recent canary run.

    Shows commit, verdict, promotion status, escalation eligibility,
    and deployment eligibility in one view — the autonomy release
    dashboard that controls reality.
    """
    from src.kortana.models import CanaryRun
    from src.kortana.services.rollout_policy import (
        AutonomyLevel,
        check_deployment,
        check_escalation,
        compute_trends,
    )

    try:
        result = await db.execute(
            select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(limit)
        )
        runs = result.scalars().all()
    except SQLAlchemyError:
        runs = []

    daemon = get_autonomy_daemon()
    daemon_status = daemon.get_status()
    current_mode = daemon_status.get("approval_mode", "self-aware")

    # Map approval-mode to AutonomyLevel for escalation checks
    _mode_to_level = {
        "manual": AutonomyLevel.SUPERVISED,
        "self-aware": AutonomyLevel.CAUTIOUS,
        "auto": AutonomyLevel.STANDARD,
    }
    cur_level = _mode_to_level.get(current_mode, AutonomyLevel.SUPERVISED)
    next_level_idx = min(cur_level.rank() + 1, len(AutonomyLevel.ordered()) - 1)
    next_level = AutonomyLevel.ordered()[next_level_idx]

    # Build run dicts for policy checks
    run_dicts = [
        {
            "verdict": r.verdict,
            "promotion_status": r.promotion_status,
            "commit_sha": r.commit_sha,
            "branch": r.branch,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "promotion_reasons": r.promotion_reasons,
            "score_shift_delta": r.score_shift_delta,
            "goal_alignment_delta": r.goal_alignment_delta,
            "outcome_growth": r.outcome_growth,
            "total_cycles": r.total_cycles,
            "task_pool_size": r.task_pool_size,
        }
        for r in runs
    ]

    # Escalation eligibility
    escalation = check_escalation(cur_level.value, next_level.value, run_dicts)

    # Deployment eligibility (based on latest)
    latest = run_dicts[0] if run_dicts else None
    deployment = check_deployment(latest)

    # Trends
    trends = compute_trends(run_dicts)

    # Per-run board rows
    board_rows = []
    for rd in run_dicts:
        dep = check_deployment(rd)
        board_rows.append({
            "commit_sha": rd.get("commit_sha"),
            "branch": rd.get("branch"),
            "created_at": rd.get("created_at"),
            "verdict": rd.get("verdict"),
            "promotion_status": rd.get("promotion_status"),
            "deploy_eligible": dep.allowed,
            "score_shift_delta": rd.get("score_shift_delta"),
            "goal_alignment_delta": rd.get("goal_alignment_delta"),
            "outcome_growth": rd.get("outcome_growth"),
            "total_cycles": rd.get("total_cycles"),
        })

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "current_mode": current_mode,
        "current_level": cur_level.value,
        "next_level": next_level.value,
        "escalation": {
            "allowed": escalation.allowed,
            "reasons": escalation.reasons,
            "required_actions": escalation.required_actions,
        },
        "deployment": {
            "allowed": deployment.allowed,
            "reasons": deployment.reasons,
            "latest_commit": deployment.commit_sha,
            "latest_verdict": deployment.verdict,
            "latest_promotion": deployment.promotion_status,
        },
        "trends": {
            "total_runs": trends.total_runs,
            "adaptive_rate": round(trends.adaptive_rate, 3),
            "promotion_rate": round(trends.promotion_rate, 3),
            "trend_direction": trends.trend_direction,
            "consecutive_promoted": trends.consecutive_promoted,
        },
        "board": board_rows,
    }


@router.post("/deploy/gate")
async def deploy_gate(
    commit_sha: str | None = Query(default=None, description="Specific commit to check"),
    require_adaptive: bool = Query(default=True),
    require_promoted: bool = Query(default=True),
    max_hours: int = Query(default=12, ge=1, le=168),
    publish_alerts: bool = Query(default=True, description="Push alerts to configured sinks"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """CI/CD deploy gate — returns pass/fail for deployment pipelines.

    Designed to be called from GitHub Actions, Cloud Build, or any CI
    system. Returns a machine-readable verdict that CI can use as a
    go/no-go signal. Optionally publishes alerts to webhooks.

    Usage in CI:
        curl -s POST .../api/daemon/deploy/gate | jq .pass
    """
    from src.kortana.models import CanaryRun
    from src.kortana.services.alert_publisher import get_alert_publisher
    from src.kortana.services.rollout_policy import check_deployment, surface_alerts

    try:
        if commit_sha:
            result = await db.execute(
                select(CanaryRun)
                .where(CanaryRun.commit_sha == commit_sha)
                .order_by(CanaryRun.created_at.desc())
                .limit(1)
            )
        else:
            result = await db.execute(
                select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(1)
            )
        run = result.scalar_one_or_none()
        latest = None
        if run:
            latest = {
                "verdict": run.verdict,
                "promotion_status": run.promotion_status,
                "commit_sha": run.commit_sha,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
    except SQLAlchemyError:
        latest = None

    decision = check_deployment(
        latest,
        require_adaptive=require_adaptive,
        require_promoted=require_promoted,
        max_hours_since_run=max_hours,
    )
    alerts = surface_alerts(deployment=decision)

    # Publish alerts to external sinks
    publish_result: dict[str, Any] = {}
    if publish_alerts and alerts:
        publisher = get_alert_publisher()
        publish_result = await publisher.publish(alerts)

    # V7: Return HTTP 403 on failure so CI can read the exit code directly
    body = {
        "pass": decision.allowed,
        "commit_sha": decision.commit_sha,
        "verdict": decision.verdict,
        "promotion_status": decision.promotion_status,
        "reasons": decision.reasons,
        "alerts": [
            {
                "level": a.level,
                "category": a.category,
                "title": a.title,
                "detail": a.detail,
                "recommended_action": a.recommended_action,
            }
            for a in alerts
        ],
        "publish_result": publish_result,
    }

    # Log audit trail
    from src.kortana.services.auto_actuator import (
        ActuationDecision,
        decision_to_log_dict,
    )
    audit = ActuationDecision(
        action="allowed" if decision.allowed else "blocked",
        from_mode="deploy-gate",
        to_mode="deploy" if decision.allowed else "blocked",
        reasons=decision.reasons,
        actor="ci",
        decision_type="deployment",
        commit_sha=decision.commit_sha,
    )
    try:
        from src.kortana.models import PolicyDecisionLog
        log_entry = PolicyDecisionLog(**decision_to_log_dict(audit))
        db.add(log_entry)
        await db.commit()
    except Exception:
        pass  # Audit log failure must not block deploy decision

    status_code = 200 if decision.allowed else 403
    return JSONResponse(content=body, status_code=status_code)


@router.post("/alerts/publish")
async def publish_alerts_endpoint(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Manually trigger alert publishing for current rollout policy state.

    Evaluates deployment readiness, trends, and surfaces all alerts
    to configured external sinks (Slack, Discord, generic webhooks).
    """
    from src.kortana.models import CanaryRun
    from src.kortana.services.alert_publisher import get_alert_publisher
    from src.kortana.services.rollout_policy import (
        check_deployment,
        compute_trends,
        surface_alerts,
    )

    try:
        result = await db.execute(
            select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(20)
        )
        runs = result.scalars().all()
        run_dicts = [
            {
                "verdict": r.verdict,
                "promotion_status": r.promotion_status,
                "score_shift_delta": r.score_shift_delta,
                "goal_alignment_delta": r.goal_alignment_delta,
                "outcome_growth": r.outcome_growth,
                "commit_sha": r.commit_sha,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]
    except SQLAlchemyError:
        run_dicts = []

    latest = run_dicts[0] if run_dicts else None
    deploy = check_deployment(latest)
    trends = compute_trends(run_dicts)
    alerts = surface_alerts(deployment=deploy, trends=trends)

    publisher = get_alert_publisher()
    publish_result = await publisher.publish(alerts)

    return {
        "alert_count": len(alerts),
        "alerts": [
            {
                "level": a.level,
                "category": a.category,
                "title": a.title,
                "detail": a.detail,
                "recommended_action": a.recommended_action,
            }
            for a in alerts
        ],
        "publish_result": publish_result,
    }


# ---------------------------------------------------------------------------
# V7 — Automatic actuation + control room endpoints
# ---------------------------------------------------------------------------


@router.post("/actuate")
async def actuate_daemon(
    min_consecutive: int = Query(default=3, ge=1, le=10),
    max_mode: str = Query(default="auto"),
    publish_alerts: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Evaluate and apply automatic actuation to the daemon.

    Checks canary evidence and auto-escalates or de-escalates the daemon
    based on rollout policy. Every decision is audit-logged with a
    tamper-evident hash.
    """
    from src.kortana.models import CanaryRun, PolicyDecisionLog
    from src.kortana.services.alert_publisher import get_alert_publisher
    from src.kortana.services.auto_actuator import (
        apply_actuation,
        decision_to_log_dict,
        evaluate_actuation,
    )

    daemon = get_autonomy_daemon()
    current_mode = daemon.default_approval_mode or "self-aware"

    try:
        result = await db.execute(
            select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(10)
        )
        runs = result.scalars().all()
        run_dicts = [
            {
                "verdict": r.verdict,
                "promotion_status": r.promotion_status,
                "commit_sha": r.commit_sha,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]
    except SQLAlchemyError:
        run_dicts = []

    decision = evaluate_actuation(
        current_mode, run_dicts,
        min_consecutive_promoted=min_consecutive,
        max_mode=max_mode,
    )

    applied = apply_actuation(daemon, decision)

    # Persist audit log
    try:
        log_entry = PolicyDecisionLog(**decision_to_log_dict(decision))
        db.add(log_entry)
        await db.commit()
    except Exception:
        pass  # Audit failure must not block actuation

    # Publish alerts if mode changed
    alerts_out: list[dict[str, Any]] = []
    publish_result: dict[str, Any] = {}
    if applied:
        from src.kortana.services.rollout_policy import RolloutAlert
        mode_alert = RolloutAlert(
            level="warning" if decision.action == "de-escalate" else "info",
            category="actuation",
            title=f"Daemon mode {decision.action}d: {decision.from_mode} -> {decision.to_mode}",
            detail="; ".join(decision.reasons),
            recommended_action="Monitor next canary cycle",
        )
        alerts_out = [{"level": mode_alert.level, "category": mode_alert.category,
                       "title": mode_alert.title, "detail": mode_alert.detail}]
        if publish_alerts:
            publisher = get_alert_publisher()
            publish_result = await publisher.publish([mode_alert])

    return {
        "action": decision.action,
        "applied": applied,
        "from_mode": decision.from_mode,
        "to_mode": decision.to_mode,
        "effective_mode": daemon.default_approval_mode,
        "reasons": decision.reasons,
        "audit_hash": decision.audit_hash,
        "alerts": alerts_out,
        "publish_result": publish_result,
    }


@router.get("/control-room")
async def control_room(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Control room — single-pane view of the entire autonomy system.

    Combines live daemon state, canary evidence, deployment readiness,
    escalation eligibility, trend analysis, active alerts, and recent
    policy audit trail into one response.
    """
    from src.kortana.models import CanaryRun, PolicyDecisionLog
    from src.kortana.services.rollout_policy import (
        AutonomyLevel,
        check_deployment,
        check_escalation,
        compute_trends,
        surface_alerts,
    )

    daemon = get_autonomy_daemon()
    daemon_status = daemon.get_status()
    current_mode = daemon_status.get("approval_mode", "self-aware")

    # Fetch canary runs
    try:
        result = await db.execute(
            select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(20)
        )
        runs = result.scalars().all()
        run_dicts = [
            {
                "verdict": r.verdict,
                "promotion_status": r.promotion_status,
                "commit_sha": r.commit_sha,
                "branch": r.branch,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "promotion_reasons": r.promotion_reasons,
                "score_shift_delta": r.score_shift_delta,
                "goal_alignment_delta": r.goal_alignment_delta,
                "outcome_growth": r.outcome_growth,
            }
            for r in runs
        ]
    except SQLAlchemyError:
        run_dicts = []

    # Fetch recent policy decisions
    try:
        result = await db.execute(
            select(PolicyDecisionLog)
            .order_by(PolicyDecisionLog.created_at.desc())
            .limit(10)
        )
        decisions = result.scalars().all()
        decision_rows = [
            {
                "decision_type": d.decision_type,
                "actor": d.actor,
                "action": d.action,
                "from_state": d.from_state,
                "to_state": d.to_state,
                "reasons": d.reasons,
                "audit_hash": d.audit_hash,
                "commit_sha": d.commit_sha,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in decisions
        ]
    except SQLAlchemyError:
        decision_rows = []

    # Mode mapping
    _mode_to_level = {
        "manual": AutonomyLevel.SUPERVISED,
        "self-aware": AutonomyLevel.CAUTIOUS,
        "auto": AutonomyLevel.STANDARD,
    }
    cur_level = _mode_to_level.get(current_mode, AutonomyLevel.SUPERVISED)
    next_idx = min(cur_level.rank() + 1, len(AutonomyLevel.ordered()) - 1)
    next_level = AutonomyLevel.ordered()[next_idx]

    # Policy evaluations
    escalation = check_escalation(cur_level.value, next_level.value, run_dicts)
    latest = run_dicts[0] if run_dicts else None
    deployment = check_deployment(latest)
    trends = compute_trends(run_dicts)
    alerts = surface_alerts(escalation=escalation, deployment=deployment, trends=trends)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "daemon": {
            "running": daemon_status.get("running", False),
            "mode": current_mode,
            "level": cur_level.value,
            "next_level": next_level.value,
            "cycles_completed": daemon_status.get("cycles_completed", 0),
            "uptime_seconds": daemon_status.get("uptime_seconds", 0),
        },
        "canary": {
            "total_runs": len(run_dicts),
            "latest": run_dicts[0] if run_dicts else None,
        },
        "deployment": {
            "allowed": deployment.allowed,
            "reasons": deployment.reasons,
            "latest_commit": deployment.commit_sha,
            "latest_verdict": deployment.verdict,
            "latest_promotion": deployment.promotion_status,
        },
        "escalation": {
            "allowed": escalation.allowed,
            "current": cur_level.value,
            "target": next_level.value,
            "reasons": escalation.reasons,
            "required_actions": escalation.required_actions,
        },
        "trends": {
            "total_runs": trends.total_runs,
            "adaptive_rate": round(trends.adaptive_rate, 3),
            "promotion_rate": round(trends.promotion_rate, 3),
            "trend_direction": trends.trend_direction,
            "consecutive_promoted": trends.consecutive_promoted,
        },
        "alerts": [
            {
                "level": a.level,
                "category": a.category,
                "title": a.title,
                "detail": a.detail,
                "recommended_action": a.recommended_action,
            }
            for a in alerts
        ],
        "policy_decisions": decision_rows,
    }


@router.get("/audit-log")
async def audit_log(
    limit: int = Query(default=25, ge=1, le=100),
    decision_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Query the policy decision audit log.

    Returns recent policy decisions with tamper-evident audit hashes.
    Filterable by decision type (escalation, deployment, actuation).
    """
    from src.kortana.models import PolicyDecisionLog

    try:
        query = select(PolicyDecisionLog).order_by(PolicyDecisionLog.created_at.desc())
        if decision_type:
            query = query.where(PolicyDecisionLog.decision_type == decision_type)
        query = query.limit(limit)

        result = await db.execute(query)
        decisions = result.scalars().all()
    except SQLAlchemyError:
        decisions = []

    return {
        "total": len(decisions),
        "decisions": [
            {
                "id": d.id,
                "decision_type": d.decision_type,
                "actor": d.actor,
                "action": d.action,
                "from_state": d.from_state,
                "to_state": d.to_state,
                "reasons": d.reasons,
                "audit_hash": d.audit_hash,
                "commit_sha": d.commit_sha,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in decisions
        ],
    }




# ---------------------------------------------------------------------------
# V8 — Rollback, safety rails, and policy versioning endpoints
# ---------------------------------------------------------------------------


@router.post("/actuate/gated")
async def actuate_daemon_gated(
    min_consecutive: int = Query(default=3, ge=1, le=10),
    max_mode: str = Query(default="auto"),
    publish_alerts: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """V8 gated actuation — cooldown + rate limit + automatic rollback.

    Same as /actuate but with safety rails:
    1. Checks cooldown since last mode change.
    2. Checks rate limit (max changes per window).
    3. Evaluates actuation.
    4. If applied, checks for post-actuation degradation and rolls back.
    """
    from src.kortana.models import CanaryRun, PolicyDecisionLog, RollbackEvent
    from src.kortana.services.alert_publisher import get_alert_publisher
    from src.kortana.services.auto_actuator import (
        apply_actuation,
        decision_to_log_dict,
        evaluate_actuation,
    )
    from src.kortana.services.policy_versioning import get_policy_registry
    from src.kortana.services.rollback_engine import (
        RollbackConfig,
        apply_rollback,
        check_cooldown,
        check_rate_limit,
        evaluate_rollback,
    )
    from src.kortana.services.rollout_policy import (
        RolloutAlert,
        check_deployment,
    )

    daemon = get_autonomy_daemon()
    current_mode = daemon.default_approval_mode or "self-aware"

    # Load policy config from registry
    registry = get_policy_registry()
    policy = registry.current
    config = RollbackConfig(
        cooldown_seconds=policy.cooldown_seconds if policy else 300,
        max_changes_per_window=policy.max_changes_per_window if policy else 3,
        window_seconds=policy.window_seconds if policy else 3600,
    )

    # --- Pre-flight: cooldown ---
    last_change_at: datetime | None = None
    try:
        result = await db.execute(
            select(PolicyDecisionLog)
            .where(PolicyDecisionLog.action.in_(["escalate", "de-escalate"]))
            .order_by(PolicyDecisionLog.created_at.desc())
            .limit(1)
        )
        last_decision = result.scalars().first()
        if last_decision:
            last_change_at = last_decision.created_at
    except SQLAlchemyError:
        pass

    cool_ok, remaining = check_cooldown(last_change_at, cooldown_seconds=config.cooldown_seconds)
    if not cool_ok:
        return {
            "action": "blocked",
            "applied": False,
            "reason": f"Cooldown active: {remaining}s remaining",
            "effective_mode": current_mode,
        }

    # --- Pre-flight: rate limit ---
    recent_decisions: list[dict[str, Any]] = []
    try:
        result = await db.execute(
            select(PolicyDecisionLog)
            .order_by(PolicyDecisionLog.created_at.desc())
            .limit(50)
        )
        rows = result.scalars().all()
        recent_decisions = [
            {
                "action": r.action,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    except SQLAlchemyError:
        pass

    rate_ok, count = check_rate_limit(
        recent_decisions,
        max_changes=config.max_changes_per_window,
        window_seconds=config.window_seconds,
    )
    if not rate_ok:
        return {
            "action": "blocked",
            "applied": False,
            "reason": f"Rate limit: {count}/{config.max_changes_per_window} changes in {config.window_seconds}s window",
            "effective_mode": current_mode,
        }

    # --- Evaluate actuation ---
    try:
        result = await db.execute(
            select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(10)
        )
        runs = result.scalars().all()
        run_dicts = [
            {
                "verdict": r.verdict,
                "promotion_status": r.promotion_status,
                "commit_sha": r.commit_sha,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]
    except SQLAlchemyError:
        run_dicts = []

    min_consec = policy.min_consecutive_promoted if policy else min_consecutive
    effective_max = policy.max_mode if policy else max_mode

    decision = evaluate_actuation(
        current_mode, run_dicts,
        min_consecutive_promoted=min_consec,
        max_mode=effective_max,
    )

    pre_actuation_mode = current_mode
    applied = apply_actuation(daemon, decision)

    # Persist audit log with policy version
    policy_version = policy.version if policy else None
    try:
        log_dict = decision_to_log_dict(decision)
        log_dict["extra_metadata"] = {
            **(log_dict.get("extra_metadata") or {}),
            "policy_version": policy_version,
            "gated": True,
        }
        log_entry = PolicyDecisionLog(**log_dict)
        db.add(log_entry)
        await db.commit()
    except Exception:
        pass

    # --- Post-actuation rollback check ---
    rollback_applied = False
    rollback_info: dict[str, Any] = {}
    if applied and decision.action == "escalate" and config.auto_rollback_enabled:
        latest_canary = run_dicts[0] if run_dicts else None
        latest_deploy = check_deployment(latest_canary)

        rb = evaluate_rollback(
            current_mode=daemon.default_approval_mode,
            pre_actuation_mode=pre_actuation_mode,
            latest_canary=latest_canary,
            deploy_allowed=latest_deploy.allowed,
            config=config,
        )

        if rb.should_rollback:
            rb.original_decision_hash = decision.audit_hash
            rollback_applied = apply_rollback(daemon, rb)

            # Persist rollback event
            try:
                rb_event = RollbackEvent(
                    trigger=rb.trigger,
                    from_mode=rb.from_mode,
                    to_mode=rb.to_mode,
                    reasons=rb.reasons,
                    original_decision_hash=rb.original_decision_hash,
                    policy_version=policy_version,
                )
                db.add(rb_event)
                await db.commit()
            except Exception:
                pass

            rollback_info = {
                "rolled_back": True,
                "trigger": rb.trigger,
                "from_mode": rb.from_mode,
                "to_mode": rb.to_mode,
                "reasons": rb.reasons,
            }

    # Publish alerts
    alerts_out: list[dict[str, Any]] = []
    if applied or rollback_applied:
        action_label = "rolled back" if rollback_applied else f"{decision.action}d"
        eff_mode = daemon.default_approval_mode
        alert = RolloutAlert(
            level="critical" if rollback_applied else (
                "warning" if decision.action == "de-escalate" else "info"),
            category="actuation",
            title=f"Daemon mode {action_label}: {decision.from_mode} -> {eff_mode}",
            detail="; ".join(decision.reasons),
            recommended_action="Investigate canary state" if rollback_applied else "Monitor next cycle",
        )
        alerts_out = [{"level": alert.level, "category": alert.category,
                       "title": alert.title, "detail": alert.detail}]
        if publish_alerts:
            publisher = get_alert_publisher()
            await publisher.publish([alert])

    return {
        "action": decision.action,
        "applied": applied,
        "from_mode": decision.from_mode,
        "to_mode": decision.to_mode,
        "effective_mode": daemon.default_approval_mode,
        "reasons": decision.reasons,
        "audit_hash": decision.audit_hash,
        "policy_version": policy_version,
        "gated": True,
        "rollback": rollback_info or {"rolled_back": False},
        "alerts": alerts_out,
    }


@router.post("/rollback/evaluate")
async def evaluate_rollback_endpoint(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Evaluate whether a rollback should be triggered right now.

    Does not apply the rollback — just returns the evaluation result.
    """
    from src.kortana.models import CanaryRun, PolicyDecisionLog
    from src.kortana.services.rollback_engine import evaluate_rollback
    from src.kortana.services.rollout_policy import check_deployment

    daemon = get_autonomy_daemon()
    current_mode = daemon.default_approval_mode or "self-aware"

    # Find the last escalation's from_state
    pre_mode = "manual"
    try:
        result = await db.execute(
            select(PolicyDecisionLog)
            .where(PolicyDecisionLog.action == "escalate")
            .order_by(PolicyDecisionLog.created_at.desc())
            .limit(1)
        )
        last_esc = result.scalars().first()
        if last_esc and last_esc.from_state:
            pre_mode = last_esc.from_state
    except SQLAlchemyError:
        pass

    # Latest canary
    latest_canary: dict[str, Any] | None = None
    try:
        result = await db.execute(
            select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(1)
        )
        run = result.scalars().first()
        if run:
            latest_canary = {
                "verdict": run.verdict,
                "promotion_status": run.promotion_status,
                "commit_sha": run.commit_sha,
            }
    except SQLAlchemyError:
        pass

    deploy = check_deployment(latest_canary)

    rb = evaluate_rollback(
        current_mode=current_mode,
        pre_actuation_mode=pre_mode,
        latest_canary=latest_canary,
        deploy_allowed=deploy.allowed,
    )

    return {
        "should_rollback": rb.should_rollback,
        "from_mode": rb.from_mode,
        "to_mode": rb.to_mode,
        "trigger": rb.trigger,
        "reasons": rb.reasons,
    }


@router.get("/rollback/history")
async def rollback_history(
    limit: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Query the rollback event history."""
    from src.kortana.models import RollbackEvent

    try:
        result = await db.execute(
            select(RollbackEvent)
            .order_by(RollbackEvent.created_at.desc())
            .limit(limit)
        )
        events = result.scalars().all()
    except SQLAlchemyError:
        events = []

    return {
        "total": len(events),
        "events": [
            {
                "id": e.id,
                "trigger": e.trigger,
                "from_mode": e.from_mode,
                "to_mode": e.to_mode,
                "reasons": e.reasons,
                "original_decision_hash": e.original_decision_hash,
                "policy_version": e.policy_version,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }


# ---------------------------------------------------------------------------
# V8B — Policy versioning endpoints
# ---------------------------------------------------------------------------


@router.post("/policy/versions")
async def create_policy_version(
    cooldown_seconds: int = Query(default=300, ge=10),
    max_changes_per_window: int = Query(default=3, ge=1, le=20),
    window_seconds: int = Query(default=3600, ge=60),
    min_consecutive_promoted: int = Query(default=3, ge=1, le=20),
    max_mode: str = Query(default="auto"),
    auto_rollback_enabled: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new policy version and make it the active policy.

    The new version is immutably persisted with a content hash.
    Previous versions remain available for diff and replay.
    """
    from src.kortana.models import PolicyVersionRecord
    from src.kortana.services.policy_versioning import (
        PolicySnapshot,
        get_policy_registry,
    )

    registry = get_policy_registry()
    next_v = registry.latest_version_number() + 1

    snapshot = PolicySnapshot(
        version=next_v,
        cooldown_seconds=cooldown_seconds,
        max_changes_per_window=max_changes_per_window,
        window_seconds=window_seconds,
        min_consecutive_promoted=min_consecutive_promoted,
        max_mode=max_mode,
        auto_rollback_enabled=auto_rollback_enabled,
    )

    # Persist to DB
    try:
        record = PolicyVersionRecord(
            version=snapshot.version,
            cooldown_seconds=snapshot.cooldown_seconds,
            max_changes_per_window=snapshot.max_changes_per_window,
            window_seconds=snapshot.window_seconds,
            min_consecutive_promoted=snapshot.min_consecutive_promoted,
            max_mode=snapshot.max_mode,
            auto_rollback_enabled=snapshot.auto_rollback_enabled,
            content_hash=snapshot.content_hash,
            created_by=snapshot.created_by,
            commit_sha=snapshot.commit_sha,
        )
        db.add(record)
        await db.commit()
    except Exception:
        pass  # In-memory registry still works

    registry.register(snapshot)

    return {
        "created": True,
        "policy": snapshot.to_dict(),
    }


@router.get("/policy/versions")
async def list_policy_versions(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List all policy versions, newest first."""
    from src.kortana.services.policy_versioning import get_policy_registry

    registry = get_policy_registry()
    current = registry.current

    return {
        "current_version": current.version if current else None,
        "total": registry.version_count,
        "versions": registry.history(),
    }


@router.get("/policy/diff")
async def diff_policy_versions(
    from_version: int = Query(ge=1),
    to_version: int = Query(ge=1),
) -> dict[str, Any]:
    """Compute the diff between two policy versions."""
    from src.kortana.services.policy_versioning import get_policy_registry

    registry = get_policy_registry()
    result = registry.diff(from_version, to_version)

    if result is None:
        return JSONResponse(
            content={"error": "One or both versions not found"},
            status_code=404,
        )

    return {
        "from_version": result.from_version,
        "to_version": result.to_version,
        "has_changes": result.has_changes,
        "changes": result.changes,
    }


@router.post("/policy/replay")
async def replay_policy(
    policy_version: int = Query(ge=1),
    run_limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Replay historical canary evidence under a specific policy version.

    Shows what decisions the system *would* have made if that policy
    had been active. Useful for 'what if' analysis before changing policy.
    """
    from src.kortana.models import CanaryRun
    from src.kortana.services.policy_versioning import (
        get_policy_registry,
        replay_decisions,
    )

    registry = get_policy_registry()
    policy = registry.get_version(policy_version)

    if policy is None:
        return JSONResponse(
            content={"error": f"Policy version {policy_version} not found"},
            status_code=404,
        )

    try:
        result = await db.execute(
            select(CanaryRun).order_by(CanaryRun.created_at.desc()).limit(run_limit)
        )
        runs = result.scalars().all()
        run_dicts = [
            {
                "verdict": r.verdict,
                "promotion_status": r.promotion_status,
                "commit_sha": r.commit_sha,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]
    except SQLAlchemyError:
        run_dicts = []

    replay = replay_decisions(policy, run_dicts)

    return {
        "policy_version": replay.policy_version,
        "total_decisions": replay.total_decisions,
        "changed_count": replay.changed_count,
        "outcomes": replay.outcomes,
    }



# ---------------------------------------------------------------------------
# V8C — Chaos engine / incident drill endpoints
# ---------------------------------------------------------------------------


@router.post("/chaos/run")
async def run_chaos_drill(
    scenario: str = Query(default="all"),
    current_mode: str = Query(default="self-aware"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run a chaos drill scenario (or all scenarios).

    Injects synthetic degraded states and verifies the control loop
    responds correctly with cooldown, rollback, and alerts.
    """
    from src.kortana.models import ChaosScenarioRecord
    from src.kortana.services.chaos_engine import (
        SCENARIO_CATALOGUE,
        run_all_scenarios,
        run_scenario,
    )

    if scenario == "all":
        results = run_all_scenarios(current_mode)
    else:
        results = [run_scenario(scenario, current_mode)]

    # Persist drill records
    for r in results:
        try:
            record = ChaosScenarioRecord(
                scenario=r.scenario,
                passed=r.passed,
                checks=r.checks,
                daemon_mode_before=r.daemon_mode_before,
                daemon_mode_after=r.daemon_mode_after,
                rollback_triggered=r.rollback_triggered,
                alerts_fired=r.alerts_fired,
                duration_ms=r.duration_ms,
            )
            db.add(record)
        except Exception:
            pass
    try:
        await db.commit()
    except Exception:
        pass

    all_passed = all(r.passed for r in results)
    return {
        "all_passed": all_passed,
        "total_scenarios": len(results),
        "passed_count": sum(1 for r in results if r.passed),
        "failed_count": sum(1 for r in results if not r.passed),
        "available_scenarios": list(SCENARIO_CATALOGUE.keys()),
        "results": [r.to_dict() for r in results],
    }


@router.get("/chaos/history")
async def chaos_drill_history(
    limit: int = Query(default=25, ge=1, le=100),
    scenario: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Query chaos drill history with optional scenario filter."""
    from src.kortana.models import ChaosScenarioRecord

    try:
        stmt = select(ChaosScenarioRecord).order_by(
            ChaosScenarioRecord.created_at.desc()
        )
        if scenario:
            stmt = stmt.where(ChaosScenarioRecord.scenario == scenario)
        stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        records = result.scalars().all()
    except SQLAlchemyError:
        records = []

    return {
        "total": len(records),
        "records": [
            {
                "id": r.id,
                "scenario": r.scenario,
                "passed": r.passed,
                "checks": r.checks,
                "daemon_mode_before": r.daemon_mode_before,
                "daemon_mode_after": r.daemon_mode_after,
                "rollback_triggered": r.rollback_triggered,
                "duration_ms": r.duration_ms,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }


# ---------------------------------------------------------------------------
# V8D — Human override protocol endpoints
# ---------------------------------------------------------------------------


@router.post("/override")
async def create_override(
    mode: str = Query(...),
    reason: str = Query(...),
    expires_in_minutes: int = Query(default=60, ge=1, le=10080),
    created_by: str = Query(default="matt"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a human override that locks daemon mode.

    The override takes precedence over automated actuation until
    it expires or is explicitly revoked.
    """
    from src.kortana.models import HumanOverrideRecord, PolicyDecisionLog
    from src.kortana.services.human_override import get_override_manager
    from src.kortana.services.policy_versioning import get_policy_registry

    manager = get_override_manager()
    override = manager.create(
        mode=mode,
        reason=reason,
        expires_in_minutes=expires_in_minutes,
        created_by=created_by,
    )

    # Apply to daemon immediately
    daemon = get_autonomy_daemon()
    old_mode = daemon.default_approval_mode
    daemon.default_approval_mode = mode

    # Get policy version
    registry = get_policy_registry()
    policy_version = registry.current.version if registry.current else None

    # Persist to DB
    try:
        record = HumanOverrideRecord(
            mode=override.mode,
            reason=override.reason,
            expires_at=override.expires_at,
            created_by=override.created_by,
            audit_hash=override.audit_hash,
            policy_version=policy_version,
        )
        db.add(record)

        # Also add to audit log
        log_entry = PolicyDecisionLog(
            decision_type="human_override",
            actor=created_by,
            action="override",
            from_state=old_mode,
            to_state=mode,
            reasons=[reason],
            audit_hash=override.audit_hash,
            extra_metadata={
                "expires_at": override.expires_at.isoformat(),
                "expires_in_minutes": expires_in_minutes,
                "policy_version": policy_version,
            },
        )
        db.add(log_entry)
        await db.commit()
    except Exception:
        pass

    return {
        "created": True,
        "override": override.to_dict(),
        "previous_mode": old_mode,
        "effective_mode": mode,
        "policy_version": policy_version,
    }


@router.get("/override/active")
async def get_active_overrides() -> dict[str, Any]:
    """Return all currently active (non-expired, non-revoked) overrides."""
    from src.kortana.services.human_override import get_override_manager

    manager = get_override_manager()
    active = manager.all_active()

    return {
        "count": len(active),
        "overrides": [o.to_dict() for o in active],
        "effective_override": manager.active().to_dict() if manager.active() else None,
    }


@router.post("/override/{override_id}/revoke")
async def revoke_override(
    override_id: int,
    revoked_by: str = Query(default="matt"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Revoke an active override by ID.

    The daemon mode is NOT automatically changed back — the next
    actuation cycle will re-evaluate the correct mode.
    """
    from src.kortana.models import PolicyDecisionLog
    from src.kortana.services.human_override import get_override_manager

    manager = get_override_manager()
    revoked = manager.revoke(override_id, revoked_by=revoked_by)

    if not revoked:
        return JSONResponse(
            content={"error": f"Override {override_id} not found or already revoked"},
            status_code=404,
        )

    # Audit log the revocation
    try:
        log_entry = PolicyDecisionLog(
            decision_type="human_override",
            actor=revoked_by,
            action="revoke_override",
            from_state="",
            to_state="",
            reasons=[f"Override #{override_id} revoked by {revoked_by}"],
            audit_hash="",
        )
        db.add(log_entry)
        await db.commit()
    except Exception:
        pass

    return {
        "revoked": True,
        "override_id": override_id,
        "revoked_by": revoked_by,
        "note": "Daemon mode unchanged — next actuation cycle will re-evaluate",
    }


@router.get("/override/history")
async def override_history(
    limit: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Query override history from DB."""
    from src.kortana.models import HumanOverrideRecord

    try:
        result = await db.execute(
            select(HumanOverrideRecord)
            .order_by(HumanOverrideRecord.created_at.desc())
            .limit(limit)
        )
        records = result.scalars().all()
    except SQLAlchemyError:
        records = []

    return {
        "total": len(records),
        "overrides": [
            {
                "id": r.id,
                "mode": r.mode,
                "reason": r.reason,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "created_by": r.created_by,
                "audit_hash": r.audit_hash,
                "revoked": r.revoked,
                "revoked_at": r.revoked_at.isoformat() if r.revoked_at else None,
                "revoked_by": r.revoked_by,
                "policy_version": r.policy_version,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }



# ---------------------------------------------------------------------------
# V9A — Quorum override endpoints
# ---------------------------------------------------------------------------


@router.post("/quorum/request")
async def request_quorum_override(
    mode: str = Query(...),
    reason: str = Query(...),
    requested_by: str = Query(default="matt"),
    required_approvals: int = Query(default=2, ge=1, le=10),
    timeout_minutes: int = Query(default=60, ge=1, le=10080),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Request a quorum override requiring multiple approvals."""
    from src.kortana.models import QuorumOverrideRecord
    from src.kortana.services.quorum_override import (
        QuorumPolicy,
        get_quorum_manager,
    )

    manager = get_quorum_manager()
    policy = QuorumPolicy(
        required_approvals=required_approvals,
        allowed_approvers=["matt", "admin", "ops", "security", "oncall"],
        timeout_minutes=timeout_minutes,
    )
    pending = manager.request(
        mode=mode,
        reason=reason,
        requested_by=requested_by,
        policy=policy,
    )

    # Persist to DB
    try:
        record = QuorumOverrideRecord(
            override_id=pending.override_id,
            mode=mode,
            reason=reason,
            requested_by=requested_by,
            required_approvals=required_approvals,
            status="pending",
            expires_at=pending.expires_at,
        )
        db.add(record)
        await db.commit()
    except Exception:
        pass

    return {
        "created": True,
        "quorum_override": pending.to_dict(),
    }


@router.post("/quorum/{override_id}/vote")
async def vote_quorum_override(
    override_id: str,
    approver: str = Query(...),
    approved: bool = Query(...),
    reason: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Cast a vote on a pending quorum override."""
    from src.kortana.models import (
        PolicyDecisionLog,
        QuorumApprovalRecord,
        QuorumOverrideRecord,
    )
    from src.kortana.services.quorum_override import get_quorum_manager

    manager = get_quorum_manager()

    try:
        record, status = manager.vote(override_id, approver, approved, reason)
    except KeyError:
        return JSONResponse(
            content={"error": f"Quorum override {override_id!r} not found"},
            status_code=404,
        )
    except ValueError as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=400,
        )

    # Persist approval
    try:
        db.add(QuorumApprovalRecord(
            override_id=override_id,
            approver=approver,
            approved=approved,
            reason=reason,
            audit_hash=record.audit_hash,
        ))

        # Update status in quorum_override table
        result = await db.execute(
            select(QuorumOverrideRecord)
            .where(QuorumOverrideRecord.override_id == override_id)
        )
        qo = result.scalar_one_or_none()
        if qo:
            qo.status = status

        # If activated, apply the override to daemon + audit
        if status == "activated":
            from src.kortana.services.human_override import get_override_manager

            daemon = get_autonomy_daemon()
            old_mode = daemon.default_approval_mode

            override_manager = get_override_manager()
            override_manager.create(
                mode=manager.get(override_id) is None
                and qo.mode if qo else "manual",
                reason=f"Quorum override {override_id} activated",
                expires_in_minutes=60,
                created_by=f"quorum:{override_id}",
            )
            daemon.default_approval_mode = qo.mode if qo else "manual"

            if qo:
                qo.activated_at = datetime.utcnow()

            db.add(PolicyDecisionLog(
                decision_type="quorum_override",
                actor=f"quorum:{override_id}",
                action="activate",
                from_state=old_mode,
                to_state=qo.mode if qo else "manual",
                reasons=[f"Quorum reached: {override_id}"],
                audit_hash=record.audit_hash,
            ))

        await db.commit()
    except Exception:
        pass

    return {
        "voted": True,
        "approval": record.to_dict(),
        "override_status": status,
    }


@router.get("/quorum/pending")
async def get_pending_quorums() -> dict[str, Any]:
    """Return all currently pending quorum overrides."""
    from src.kortana.services.quorum_override import get_quorum_manager

    manager = get_quorum_manager()
    return {
        "count": manager.count,
        "pending": [p.to_dict() for p in manager.pending],
    }


@router.get("/quorum/history")
async def quorum_history(
    limit: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Query quorum override history from DB."""
    from src.kortana.models import QuorumOverrideRecord

    try:
        result = await db.execute(
            select(QuorumOverrideRecord)
            .order_by(QuorumOverrideRecord.created_at.desc())
            .limit(limit)
        )
        records = result.scalars().all()
    except SQLAlchemyError:
        records = []

    return {
        "total": len(records),
        "records": [
            {
                "id": r.id,
                "override_id": r.override_id,
                "mode": r.mode,
                "reason": r.reason,
                "requested_by": r.requested_by,
                "required_approvals": r.required_approvals,
                "status": r.status,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "activated_at": r.activated_at.isoformat() if r.activated_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }


# ---------------------------------------------------------------------------
# V9B — Drill scheduler + SLO endpoints
# ---------------------------------------------------------------------------


@router.post("/drills/schedule")
async def add_drill_schedule(
    scenario: str = Query(...),
    interval_minutes: int = Query(default=60, ge=1, le=10080),
    enabled: bool = Query(default=True),
) -> dict[str, Any]:
    """Register a recurring chaos drill schedule."""
    from src.kortana.services.drill_scheduler import get_drill_scheduler

    scheduler = get_drill_scheduler()
    schedule = scheduler.add_schedule(scenario, interval_minutes, enabled)
    return {"created": True, "schedule": schedule.to_dict()}


@router.delete("/drills/schedule/{scenario}")
async def remove_drill_schedule(scenario: str) -> dict[str, Any]:
    """Remove a drill schedule."""
    from src.kortana.services.drill_scheduler import get_drill_scheduler

    scheduler = get_drill_scheduler()
    removed = scheduler.remove_schedule(scenario)
    if not removed:
        return JSONResponse(
            content={"error": f"Schedule for {scenario!r} not found"},
            status_code=404,
        )
    return {"removed": True, "scenario": scenario}


@router.get("/drills/schedules")
async def list_drill_schedules() -> dict[str, Any]:
    """List all drill schedules."""
    from src.kortana.services.drill_scheduler import get_drill_scheduler

    scheduler = get_drill_scheduler()
    return {"schedules": scheduler.schedules}


@router.post("/drills/run-due")
async def run_due_drills(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run all drills that are currently due and record results."""
    from src.kortana.models import ChaosScenarioRecord
    from src.kortana.services.drill_scheduler import get_drill_scheduler

    scheduler = get_drill_scheduler()
    daemon = get_autonomy_daemon()
    results = scheduler.run_due_drills(daemon.default_approval_mode)

    # Persist results
    for r in results:
        try:
            db.add(ChaosScenarioRecord(
                scenario=r["scenario"],
                passed=r["passed"],
                checks=r.get("checks"),
                daemon_mode_before=r.get("daemon_mode_before"),
                daemon_mode_after=r.get("daemon_mode_after"),
                rollback_triggered=r.get("rollback_triggered", False),
                duration_ms=r.get("duration_ms", 0),
            ))
        except Exception:
            pass

    try:
        await db.commit()
    except Exception:
        pass

    return {
        "ran": len(results),
        "results": results,
    }


@router.post("/drills/slo")
async def set_drill_slo(
    scenario: str = Query(...),
    min_pass_rate: float = Query(default=0.95, ge=0.0, le=1.0),
    lookback_window_minutes: int = Query(default=1440, ge=1),
    min_runs: int = Query(default=3, ge=1),
) -> dict[str, Any]:
    """Define or update the SLO for a drill scenario."""
    from src.kortana.services.drill_scheduler import get_drill_scheduler

    scheduler = get_drill_scheduler()
    slo = scheduler.set_slo(scenario, min_pass_rate, lookback_window_minutes, min_runs)
    return {"created": True, "slo": slo.to_dict()}


@router.get("/drills/slos")
async def get_drill_slos() -> dict[str, Any]:
    """List all drill SLO definitions and their current evaluation."""
    from src.kortana.services.drill_scheduler import get_drill_scheduler

    scheduler = get_drill_scheduler()
    evaluations = scheduler.evaluate_all_slos()
    return {
        "slos": scheduler.slos,
        "evaluations": [e.to_dict() for e in evaluations],
    }


# ---------------------------------------------------------------------------
# V9C — Policy comparison endpoint
# ---------------------------------------------------------------------------


@router.get("/control-room/comparison")
async def policy_comparison_view() -> dict[str, Any]:
    """Compare current daemon state with what actuation would propose.

    Shows current mode, proposed decision, override status, quorum
    pending, rollback likelihood, and drill SLO health — all in one view.
    """
    from src.kortana.services.drill_scheduler import get_drill_scheduler
    from src.kortana.services.human_override import get_override_manager
    from src.kortana.services.policy_comparison import compute_policy_comparison
    from src.kortana.services.policy_versioning import get_policy_registry
    from src.kortana.services.quorum_override import get_quorum_manager

    daemon = get_autonomy_daemon()
    registry = get_policy_registry()
    override_manager = get_override_manager()
    quorum_manager = get_quorum_manager()
    drill_scheduler = get_drill_scheduler()

    # Gather context
    current_mode = daemon.default_approval_mode
    active_override = override_manager.active()
    quorum_pending = quorum_manager.pending
    slo_results = [e.to_dict() for e in drill_scheduler.evaluate_all_slos()]
    policy_version = registry.current.version if registry.current else None
    policy_hash = registry.current.content_hash if registry.current else None

    comparison = compute_policy_comparison(
        current_mode=current_mode,
        recent_runs=[],
        override=active_override,
        quorum_pending=quorum_pending,
        drill_slo_results=slo_results,
        policy_version=policy_version,
        policy_hash=policy_hash,
    )

    return comparison.to_dict()


# ---------------------------------------------------------------------------
# V9D — Audit bundle endpoints
# ---------------------------------------------------------------------------


@router.get("/audit/export")
async def export_audit_bundle(
    hours: int = Query(default=24, ge=1, le=720),
    generated_by: str = Query(default="operator"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Export an audit bundle for the last N hours.

    Gathers all policy decisions, overrides, drills, rollbacks,
    and policy versions into a single tamper-evident package.
    """
    from src.kortana.models import (
        AuditBundleRecord,
        ChaosScenarioRecord,
        HumanOverrideRecord,
        PolicyDecisionLog,
        PolicyVersionRecord,
        RollbackEvent,
    )
    from src.kortana.services.audit_bundle import build_audit_bundle

    now = datetime.utcnow()
    from_time = now - timedelta(hours=hours)
    bundle_id = f"ab-{now.strftime('%Y%m%dT%H%M%S')}"

    # Gather from DB
    decisions: list[dict[str, Any]] = []
    overrides: list[dict[str, Any]] = []
    drills: list[dict[str, Any]] = []
    rollbacks: list[dict[str, Any]] = []
    policy_versions: list[dict[str, Any]] = []

    try:
        # Decisions
        result = await db.execute(
            select(PolicyDecisionLog)
            .where(PolicyDecisionLog.created_at >= from_time)
            .order_by(PolicyDecisionLog.created_at.asc())
        )
        for r in result.scalars().all():
            decisions.append({
                "decision_type": r.decision_type,
                "actor": r.actor,
                "action": r.action,
                "from_state": r.from_state,
                "to_state": r.to_state,
                "reasons": r.reasons,
                "audit_hash": r.audit_hash,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        # Overrides
        result = await db.execute(
            select(HumanOverrideRecord)
            .where(HumanOverrideRecord.created_at >= from_time)
            .order_by(HumanOverrideRecord.created_at.asc())
        )
        for r in result.scalars().all():
            overrides.append({
                "mode": r.mode,
                "reason": r.reason,
                "created_by": r.created_by,
                "audit_hash": r.audit_hash,
                "revoked": r.revoked,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        # Drills
        result = await db.execute(
            select(ChaosScenarioRecord)
            .where(ChaosScenarioRecord.created_at >= from_time)
            .order_by(ChaosScenarioRecord.created_at.asc())
        )
        for r in result.scalars().all():
            drills.append({
                "scenario": r.scenario,
                "passed": r.passed,
                "duration_ms": r.duration_ms,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        # Rollbacks
        result = await db.execute(
            select(RollbackEvent)
            .where(RollbackEvent.created_at >= from_time)
            .order_by(RollbackEvent.created_at.asc())
        )
        for r in result.scalars().all():
            rollbacks.append({
                "trigger": r.trigger,
                "from_mode": r.from_mode,
                "to_mode": r.to_mode,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        # Policy versions
        result = await db.execute(
            select(PolicyVersionRecord)
            .where(PolicyVersionRecord.created_at >= from_time)
            .order_by(PolicyVersionRecord.created_at.asc())
        )
        for r in result.scalars().all():
            policy_versions.append({
                "version": r.version,
                "content_hash": r.content_hash,
                "created_by": r.created_by,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

    except SQLAlchemyError:
        pass

    bundle = build_audit_bundle(
        bundle_id=bundle_id,
        from_time=from_time,
        to_time=now,
        decisions=decisions,
        overrides=overrides,
        drills=drills,
        rollbacks=rollbacks,
        policy_versions=policy_versions,
        generated_by=generated_by,
    )

    # Persist bundle record
    try:
        db.add(AuditBundleRecord(
            bundle_id=bundle.bundle_id,
            from_time=from_time,
            to_time=now,
            generated_by=generated_by,
            total_decisions=bundle.total_decisions,
            total_overrides=bundle.total_overrides,
            total_drills=bundle.total_drills,
            total_rollbacks=bundle.total_rollbacks,
            drill_pass_rate=bundle.drill_pass_rate,
            content_hash=bundle.content_hash,
        ))
        await db.commit()
    except Exception:
        pass

    return bundle.to_dict()


@router.get("/audit/export/markdown")
async def export_audit_markdown(
    hours: int = Query(default=24, ge=1, le=720),
    generated_by: str = Query(default="operator"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Export an audit bundle as human-readable Markdown."""
    from src.kortana.models import (
        ChaosScenarioRecord,
        HumanOverrideRecord,
        PolicyDecisionLog,
        PolicyVersionRecord,
        RollbackEvent,
    )
    from src.kortana.services.audit_bundle import (
        build_audit_bundle,
        render_bundle_markdown,
    )

    now = datetime.utcnow()
    from_time = now - timedelta(hours=hours)
    bundle_id = f"ab-md-{now.strftime('%Y%m%dT%H%M%S')}"

    decisions: list[dict[str, Any]] = []
    overrides: list[dict[str, Any]] = []
    drills: list[dict[str, Any]] = []
    rollbacks: list[dict[str, Any]] = []
    policy_versions: list[dict[str, Any]] = []

    try:
        result = await db.execute(
            select(PolicyDecisionLog)
            .where(PolicyDecisionLog.created_at >= from_time)
            .order_by(PolicyDecisionLog.created_at.asc())
        )
        for r in result.scalars().all():
            decisions.append({
                "decision_type": r.decision_type,
                "actor": r.actor,
                "action": r.action,
                "from_state": r.from_state,
                "to_state": r.to_state,
                "audit_hash": r.audit_hash,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        result = await db.execute(
            select(HumanOverrideRecord)
            .where(HumanOverrideRecord.created_at >= from_time)
        )
        for r in result.scalars().all():
            overrides.append({
                "mode": r.mode,
                "reason": r.reason,
                "created_by": r.created_by,
                "revoked": r.revoked,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        result = await db.execute(
            select(ChaosScenarioRecord)
            .where(ChaosScenarioRecord.created_at >= from_time)
        )
        for r in result.scalars().all():
            drills.append({
                "scenario": r.scenario,
                "passed": r.passed,
                "duration_ms": r.duration_ms,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        result = await db.execute(
            select(RollbackEvent)
            .where(RollbackEvent.created_at >= from_time)
        )
        for r in result.scalars().all():
            rollbacks.append({
                "trigger": r.trigger,
                "from_mode": r.from_mode,
                "to_mode": r.to_mode,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        result = await db.execute(
            select(PolicyVersionRecord)
            .where(PolicyVersionRecord.created_at >= from_time)
        )
        for r in result.scalars().all():
            policy_versions.append({
                "version": r.version,
                "content_hash": r.content_hash,
                "created_by": r.created_by,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
    except SQLAlchemyError:
        pass

    bundle = build_audit_bundle(
        bundle_id=bundle_id,
        from_time=from_time,
        to_time=now,
        decisions=decisions,
        overrides=overrides,
        drills=drills,
        rollbacks=rollbacks,
        policy_versions=policy_versions,
        generated_by=generated_by,
    )

    markdown = render_bundle_markdown(bundle)
    return {"bundle_id": bundle_id, "markdown": markdown, "content_hash": bundle.content_hash}


@router.get("/audit/bundles")
async def list_audit_bundles(
    limit: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List previously exported audit bundles."""
    from src.kortana.models import AuditBundleRecord

    try:
        result = await db.execute(
            select(AuditBundleRecord)
            .order_by(AuditBundleRecord.created_at.desc())
            .limit(limit)
        )
        records = result.scalars().all()
    except SQLAlchemyError:
        records = []

    return {
        "total": len(records),
        "bundles": [
            {
                "id": r.id,
                "bundle_id": r.bundle_id,
                "from_time": r.from_time.isoformat() if r.from_time else None,
                "to_time": r.to_time.isoformat() if r.to_time else None,
                "generated_by": r.generated_by,
                "total_decisions": r.total_decisions,
                "total_overrides": r.total_overrides,
                "total_drills": r.total_drills,
                "total_rollbacks": r.total_rollbacks,
                "drill_pass_rate": r.drill_pass_rate,
                "content_hash": r.content_hash,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }



# ---------------------------------------------------------------------------
# V10A — Operator identity endpoints
# ---------------------------------------------------------------------------


@router.post("/operators/register")
async def register_operator(
    operator_id: str = Query(...),
    display_name: str = Query(...),
    role: str = Query(default="operator"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Register a new operator with a role."""
    from src.kortana.models import OperatorRecord
    from src.kortana.services.operator_identity import (
        OperatorRole,
        get_operator_registry,
    )

    registry = get_operator_registry()
    try:
        identity = registry.register(operator_id, display_name, OperatorRole(role))
    except ValueError as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

    try:
        db.add(OperatorRecord(
            operator_id=operator_id,
            display_name=display_name,
            role=role,
            identity_hash=identity.identity_hash,
        ))
        await db.commit()
    except Exception:
        pass

    return {"registered": True, "operator": identity.to_dict()}


@router.get("/operators")
async def list_operators() -> dict[str, Any]:
    """List all registered operators."""
    from src.kortana.services.operator_identity import get_operator_registry

    registry = get_operator_registry()
    return {
        "total": registry.count,
        "operators": [op.to_dict() for op in registry.all_operators],
    }


@router.get("/operators/{operator_id}")
async def get_operator(operator_id: str) -> dict[str, Any]:
    """Get a specific operator by ID."""
    from src.kortana.services.operator_identity import get_operator_registry

    registry = get_operator_registry()
    op = registry.get(operator_id)
    if op is None:
        return JSONResponse(
            content={"error": f"Operator {operator_id!r} not found"},
            status_code=404,
        )
    return {"operator": op.to_dict()}


@router.post("/operators/{operator_id}/deactivate")
async def deactivate_operator(operator_id: str) -> dict[str, Any]:
    """Deactivate an operator."""
    from src.kortana.services.operator_identity import get_operator_registry

    registry = get_operator_registry()
    if not registry.deactivate(operator_id):
        return JSONResponse(
            content={"error": f"Operator {operator_id!r} not found"},
            status_code=404,
        )
    return {"deactivated": True, "operator_id": operator_id}


@router.post("/operators/{operator_id}/role")
async def update_operator_role(
    operator_id: str,
    new_role: str = Query(...),
) -> dict[str, Any]:
    """Update an operator's role."""
    from src.kortana.services.operator_identity import (
        OperatorRole,
        get_operator_registry,
    )

    registry = get_operator_registry()
    try:
        role = OperatorRole(new_role)
    except ValueError:
        return JSONResponse(
            content={"error": f"Invalid role {new_role!r}"},
            status_code=400,
        )

    if not registry.update_role(operator_id, role):
        return JSONResponse(
            content={"error": f"Operator {operator_id!r} not found"},
            status_code=404,
        )

    op = registry.get(operator_id)
    return {"updated": True, "operator": op.to_dict() if op else None}


# ---------------------------------------------------------------------------
# V10B — Governance action endpoints
# ---------------------------------------------------------------------------


@router.post("/governance/check")
async def governance_permission_check(
    operator_id: str = Query(...),
    permission: str = Query(...),
) -> dict[str, Any]:
    """Check if an operator has a specific permission."""
    from src.kortana.services.operator_identity import (
        Permission,
        get_operator_registry,
    )

    registry = get_operator_registry()
    try:
        perm = Permission(permission)
    except ValueError:
        return JSONResponse(
            content={"error": f"Unknown permission {permission!r}"},
            status_code=400,
        )

    result = registry.check(operator_id, perm)
    return result.to_dict()


@router.get("/governance/actions")
async def list_governance_actions(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List signed governance actions from DB."""
    from src.kortana.models import GovernanceActionRecord

    try:
        result = await db.execute(
            select(GovernanceActionRecord)
            .order_by(GovernanceActionRecord.created_at.desc())
            .limit(limit)
        )
        records = result.scalars().all()
    except SQLAlchemyError:
        records = []

    return {
        "total": len(records),
        "actions": [
            {
                "id": r.id,
                "operator_id": r.operator_id,
                "display_name": r.display_name,
                "role": r.role,
                "action": r.action,
                "resource": r.resource,
                "action_signature": r.action_signature,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }


# ---------------------------------------------------------------------------
# V10C — Deploy gate endpoints
# ---------------------------------------------------------------------------


@router.post("/deploy/gate/evaluate")
async def evaluate_deploy_gate_endpoint(
    operator_id: str = Query(...),
    target_mode: str = Query(default=None),
    min_policy_version: int = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Evaluate the deploy gate for an operator.

    Checks operator identity, override conflicts, quorum state,
    drill SLO health, rollback cooldown, rate limits, and policy version.
    """
    from src.kortana.models import DeployGateRecord
    from src.kortana.services.deploy_gate import evaluate_deploy_gate
    from src.kortana.services.drill_scheduler import get_drill_scheduler
    from src.kortana.services.human_override import get_override_manager
    from src.kortana.services.quorum_override import get_quorum_manager

    daemon = get_autonomy_daemon()
    override_manager = get_override_manager()
    quorum_manager = get_quorum_manager()
    drill_scheduler = get_drill_scheduler()

    active = override_manager.active()
    slo_results = [e.to_dict() for e in drill_scheduler.evaluate_all_slos()]

    result = evaluate_deploy_gate(
        operator_id=operator_id,
        target_mode=target_mode,
        current_mode=daemon.default_approval_mode,
        active_override_mode=getattr(active, "mode", None) if active else None,
        quorum_pending_count=quorum_manager.count,
        drill_slo_results=slo_results if slo_results else None,
        min_policy_version=min_policy_version,
    )

    # Persist gate record
    try:
        db.add(DeployGateRecord(
            operator_id=operator_id,
            allowed=result.allowed,
            checks=[c.to_dict() for c in result.checks],
            blocking_failures=len(result.blocking_failures),
            warnings_count=len(result.warnings),
            gate_hash=result.gate_hash,
        ))
        await db.commit()
    except Exception:
        pass

    return result.to_dict()


@router.get("/deploy/gate/history")
async def deploy_gate_history(
    limit: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List deploy gate evaluation history from DB."""
    from src.kortana.models import DeployGateRecord

    try:
        result = await db.execute(
            select(DeployGateRecord)
            .order_by(DeployGateRecord.created_at.desc())
            .limit(limit)
        )
        records = result.scalars().all()
    except SQLAlchemyError:
        records = []

    return {
        "total": len(records),
        "records": [
            {
                "id": r.id,
                "operator_id": r.operator_id,
                "allowed": r.allowed,
                "checks": r.checks,
                "blocking_failures": r.blocking_failures,
                "warnings_count": r.warnings_count,
                "gate_hash": r.gate_hash,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }


# ---------------------------------------------------------------------------
# V10D — Policy engine endpoints
# ---------------------------------------------------------------------------


@router.post("/policy/rules/add")
async def add_policy_rule(
    rule_id: str = Query(...),
    name: str = Query(...),
    description: str = Query(default=""),
    action: str = Query(...),
    priority: int = Query(default=100, ge=0, le=1000),
    enabled: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Add a policy rule to the engine."""
    from src.kortana.models import PolicyRuleRecord
    from src.kortana.services.policy_engine import (
        PolicyRule,
        RuleAction,
        RulePriority,
        get_policy_engine,
    )

    engine = get_policy_engine()

    try:
        rule_action = RuleAction(action)
    except ValueError:
        return JSONResponse(
            content={"error": f"Invalid action {action!r}"},
            status_code=400,
        )

    # Map priority to closest enum
    for p in RulePriority:
        if priority <= p.value:
            rule_priority = p
            break
    else:
        rule_priority = RulePriority.DEFAULT

    rule = PolicyRule(
        rule_id=rule_id,
        name=name,
        description=description,
        conditions={},
        action=rule_action,
        priority=rule_priority,
        enabled=enabled,
    )
    engine.add_rule(rule)

    try:
        db.add(PolicyRuleRecord(
            rule_id=rule_id,
            name=name,
            description=description,
            conditions={},
            action=action,
            priority=priority,
            enabled=enabled,
        ))
        await db.commit()
    except Exception:
        pass

    return {"added": True, "rule": rule.to_dict()}


@router.delete("/policy/rules/{rule_id}")
async def remove_policy_rule(rule_id: str) -> dict[str, Any]:
    """Remove a policy rule from the engine."""
    from src.kortana.services.policy_engine import get_policy_engine

    engine = get_policy_engine()
    if not engine.remove_rule(rule_id):
        return JSONResponse(
            content={"error": f"Rule {rule_id!r} not found"},
            status_code=404,
        )
    return {"removed": True, "rule_id": rule_id}


@router.get("/policy/rules")
async def list_policy_rules() -> dict[str, Any]:
    """List all policy rules in the engine."""
    from src.kortana.services.policy_engine import get_policy_engine

    engine = get_policy_engine()
    return {"total": engine.count, "rules": engine.rules}


@router.post("/policy/evaluate")
async def evaluate_policy(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Evaluate all policy rules against current system state facts."""
    from src.kortana.models import PolicyEvaluationRecord
    from src.kortana.services.drill_scheduler import get_drill_scheduler
    from src.kortana.services.human_override import get_override_manager
    from src.kortana.services.policy_engine import get_policy_engine
    from src.kortana.services.quorum_override import get_quorum_manager

    engine = get_policy_engine()
    daemon = get_autonomy_daemon()
    override_manager = get_override_manager()
    quorum_manager = get_quorum_manager()
    drill_scheduler = get_drill_scheduler()

    slo_results = drill_scheduler.evaluate_all_slos()
    drill_slos_met = all(r.met for r in slo_results)

    facts = {
        "current_mode": daemon.default_approval_mode,
        "override_active": override_manager.active() is not None,
        "quorum_pending": quorum_manager.count,
        "drill_slos_met": drill_slos_met,
        "in_cooldown": False,
        "rate_limited": False,
        "deploy_requested": False,
        "action_type": "evaluate",
    }

    decision = engine.evaluate(facts)

    try:
        db.add(PolicyEvaluationRecord(
            action=decision.action,
            reason=decision.reason[:256],
            matched_rule_count=len(decision.matched_rules),
            total_rule_count=len(decision.all_evaluations),
            facts_snapshot=facts,
            decision_hash=decision.decision_hash,
        ))
        await db.commit()
    except Exception:
        pass

    return decision.to_dict()


@router.get("/policy/evaluations")
async def list_policy_evaluations(
    limit: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List policy engine evaluation history from DB."""
    from src.kortana.models import PolicyEvaluationRecord

    try:
        result = await db.execute(
            select(PolicyEvaluationRecord)
            .order_by(PolicyEvaluationRecord.created_at.desc())
            .limit(limit)
        )
        records = result.scalars().all()
    except SQLAlchemyError:
        records = []

    return {
        "total": len(records),
        "evaluations": [
            {
                "id": r.id,
                "action": r.action,
                "reason": r.reason,
                "matched_rule_count": r.matched_rule_count,
                "total_rule_count": r.total_rule_count,
                "facts_snapshot": r.facts_snapshot,
                "decision_hash": r.decision_hash,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }



# ---------------------------------------------------------------------------
# V11A — Auth provider endpoints
# ---------------------------------------------------------------------------


@router.post("/auth/verify")
async def verify_auth_token(
    token: str = Query(...),
    provider_type: str = Query(default=None),
) -> dict[str, Any]:
    """Verify a token against registered auth providers."""
    from src.kortana.services.auth_provider import (
        ProviderType,
        get_auth_provider_registry,
    )

    registry = get_auth_provider_registry()
    pt = ProviderType(provider_type) if provider_type else None
    credential = registry.verify(token, pt)

    if credential is None:
        return JSONResponse(
            content={"error": "Token verification failed"},
            status_code=401,
        )
    return {"verified": True, "credential": credential.to_dict()}


@router.post("/auth/api-keys/issue")
async def issue_api_key(
    operator_id: str = Query(...),
    display_name: str = Query(...),
    role_hint: str = Query(default="operator"),
    ttl_hours: int = Query(default=720, ge=1, le=8760),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Issue a new API key for an operator."""
    from src.kortana.models import CredentialRecord
    from src.kortana.services.auth_provider import (
        ProviderType,
        get_auth_provider_registry,
    )

    registry = get_auth_provider_registry()
    provider = registry.get_provider(ProviderType.API_KEY)
    if provider is None:
        return JSONResponse(content={"error": "API key provider not available"}, status_code=500)

    bearer, credential = provider.issue_key(
        operator_id=operator_id,
        display_name=display_name,
        role_hint=role_hint,
        ttl_hours=ttl_hours,
    )

    try:
        db.add(CredentialRecord(
            operator_id=operator_id,
            provider_type="api_key",
            credential_id=credential.credential_id,
            display_name=display_name,
            role_hint=role_hint,
            verification_hash=credential.verification_hash,
            expires_at=credential.expires_at,
        ))
        await db.commit()
    except Exception:
        pass

    return {
        "issued": True,
        "bearer_token": bearer,
        "credential": credential.to_dict(),
    }


@router.post("/auth/api-keys/revoke")
async def revoke_api_key(
    credential_id: str = Query(...),
) -> dict[str, Any]:
    """Revoke an API key."""
    from src.kortana.services.auth_provider import (
        ProviderType,
        get_auth_provider_registry,
    )

    registry = get_auth_provider_registry()
    if registry.revoke(ProviderType.API_KEY, credential_id):
        return {"revoked": True, "credential_id": credential_id}
    return JSONResponse(
        content={"error": f"Credential {credential_id!r} not found"},
        status_code=404,
    )


@router.get("/auth/providers")
async def list_auth_providers() -> dict[str, Any]:
    """List registered auth providers."""
    from src.kortana.services.auth_provider import get_auth_provider_registry

    registry = get_auth_provider_registry()
    return {
        "count": registry.count,
        "providers": registry.provider_types,
    }


# ---------------------------------------------------------------------------
# V11B — Identity verification endpoints
# ---------------------------------------------------------------------------


@router.post("/identity/sessions/create")
async def create_identity_session(
    token: str = Query(...),
    provider_type: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Verify a token and create an identity session."""
    from src.kortana.models import IdentitySessionRecord
    from src.kortana.services.identity_verification import (
        get_identity_verification_manager,
    )

    manager = get_identity_verification_manager()
    session, error = manager.verify_and_create_session(token, provider_type)

    if session is None:
        return JSONResponse(content={"error": error}, status_code=401)

    try:
        db.add(IdentitySessionRecord(
            session_id=session.session_id,
            operator_id=session.operator_id,
            provider_type=session.provider_type,
            credential_id=session.credential_id,
            verification_level=session.verification_level.value,
            expires_at=session.expires_at,
            session_hash=session.session_hash,
        ))
        await db.commit()
    except Exception:
        pass

    return {"created": True, "session": session.to_dict()}


@router.get("/identity/sessions/{session_id}")
async def get_identity_session(session_id: str) -> dict[str, Any]:
    """Get an active identity session."""
    from src.kortana.services.identity_verification import (
        get_identity_verification_manager,
    )

    manager = get_identity_verification_manager()
    session = manager.get_session(session_id)

    if session is None:
        return JSONResponse(
            content={"error": f"Session {session_id!r} not found or expired"},
            status_code=404,
        )
    return {"session": session.to_dict()}


@router.post("/identity/sessions/{session_id}/revoke")
async def revoke_identity_session(session_id: str) -> dict[str, Any]:
    """Revoke an identity session."""
    from src.kortana.services.identity_verification import (
        get_identity_verification_manager,
    )

    manager = get_identity_verification_manager()
    if manager.revoke_session(session_id):
        return {"revoked": True, "session_id": session_id}
    return JSONResponse(
        content={"error": f"Session {session_id!r} not found"},
        status_code=404,
    )


@router.post("/identity/sessions/{session_id}/elevate")
async def elevate_identity_session(
    session_id: str,
    level: str = Query(...),
) -> dict[str, Any]:
    """Elevate a session's verification level."""
    from src.kortana.services.identity_verification import (
        VerificationLevel,
        get_identity_verification_manager,
    )

    manager = get_identity_verification_manager()
    try:
        vl = VerificationLevel(level)
    except ValueError:
        return JSONResponse(
            content={"error": f"Invalid verification level {level!r}"},
            status_code=400,
        )

    if manager.elevate_session(session_id, vl):
        session = manager.get_session(session_id)
        return {
            "elevated": True,
            "session": session.to_dict() if session else None,
        }
    return JSONResponse(
        content={"error": f"Session {session_id!r} not found or inactive"},
        status_code=404,
    )


@router.post("/identity/bindings/create")
async def create_identity_binding(
    operator_id: str = Query(...),
    provider_type: str = Query(...),
    external_id: str = Query(...),
    display_name: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Bind an external identity to an operator."""
    from src.kortana.models import IdentityBindingRecord
    from src.kortana.services.identity_verification import (
        get_identity_verification_manager,
    )

    manager = get_identity_verification_manager()
    binding = manager.bind_identity(operator_id, provider_type, external_id, display_name)

    try:
        db.add(IdentityBindingRecord(
            binding_id=binding.binding_id,
            operator_id=operator_id,
            provider_type=provider_type,
            external_id=external_id,
            display_name=display_name,
            binding_hash=binding.binding_hash,
        ))
        await db.commit()
    except Exception:
        pass

    return {"bound": True, "binding": binding.to_dict()}


@router.get("/identity/bindings/{operator_id}")
async def get_identity_bindings(operator_id: str) -> dict[str, Any]:
    """Get all identity bindings for an operator."""
    from src.kortana.services.identity_verification import (
        get_identity_verification_manager,
    )

    manager = get_identity_verification_manager()
    bindings = manager.get_bindings(operator_id)
    return {
        "operator_id": operator_id,
        "count": len(bindings),
        "bindings": [b.to_dict() for b in bindings],
    }


@router.post("/identity/bindings/{binding_id}/revoke")
async def revoke_identity_binding(binding_id: str) -> dict[str, Any]:
    """Revoke an identity binding."""
    from src.kortana.services.identity_verification import (
        get_identity_verification_manager,
    )

    manager = get_identity_verification_manager()
    if manager.revoke_binding(binding_id):
        return {"revoked": True, "binding_id": binding_id}
    return JSONResponse(
        content={"error": f"Binding {binding_id!r} not found"},
        status_code=404,
    )


@router.get("/identity/sessions")
async def list_active_sessions() -> dict[str, Any]:
    """List all active identity sessions."""
    from src.kortana.services.identity_verification import (
        get_identity_verification_manager,
    )

    manager = get_identity_verification_manager()
    return {
        "active_count": manager.active_session_count,
        "total_count": manager.session_count,
        "sessions": [s.to_dict() for s in manager.active_sessions],
    }


# ---------------------------------------------------------------------------
# V11C — Credential gate endpoint
# ---------------------------------------------------------------------------


@router.post("/credential/gate/evaluate")
async def evaluate_credential_gate_endpoint(
    session_id: str = Query(...),
    requirement_profile: str = Query(default="default"),
    target_mode: str = Query(default=None),
    min_policy_version: int = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Evaluate the credential-enforced deploy gate.

    Uses a verified session (from V11B) and checks credential
    requirements before delegating to governance checks (V10C).
    """
    from src.kortana.services.credential_gate import (
        evaluate_credential_gate,
        get_requirement,
    )
    from src.kortana.services.drill_scheduler import get_drill_scheduler
    from src.kortana.services.human_override import get_override_manager
    from src.kortana.services.quorum_override import get_quorum_manager

    requirement = get_requirement(requirement_profile)
    if requirement is None:
        return JSONResponse(
            content={"error": f"Unknown requirement profile {requirement_profile!r}"},
            status_code=400,
        )

    daemon = get_autonomy_daemon()
    override_manager = get_override_manager()
    quorum_manager = get_quorum_manager()
    drill_scheduler = get_drill_scheduler()

    active = override_manager.active()
    slo_results = [e.to_dict() for e in drill_scheduler.evaluate_all_slos()]

    result = evaluate_credential_gate(
        session_id=session_id,
        requirement=requirement,
        target_mode=target_mode,
        current_mode=daemon.default_approval_mode,
        active_override_mode=getattr(active, "mode", None) if active else None,
        quorum_pending_count=quorum_manager.count,
        drill_slo_results=slo_results if slo_results else None,
        min_policy_version=min_policy_version,
    )

    return result.to_dict()


# ---------------------------------------------------------------------------
# V11D — Rule lifecycle endpoints
# ---------------------------------------------------------------------------


@router.post("/rules/draft")
async def create_rule_draft(
    rule_id: str = Query(...),
    name: str = Query(...),
    description: str = Query(default=""),
    action: str = Query(...),
    priority: int = Query(default=100, ge=0, le=1000),
    author_id: str = Query(...),
    changelog: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a draft rule version."""
    from src.kortana.models import RuleVersionRecord
    from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

    manager = get_rule_lifecycle_manager()
    version = manager.create_draft(
        rule_id=rule_id,
        name=name,
        description=description,
        conditions={},
        action=action,
        priority=priority,
        author_id=author_id,
        changelog=changelog,
    )

    try:
        db.add(RuleVersionRecord(
            version_id=version.version_id,
            rule_id=rule_id,
            stage="draft",
            rule_snapshot=version.rule_snapshot,
            author_id=author_id,
            changelog=changelog,
            version_hash=version.version_hash,
        ))
        await db.commit()
    except Exception:
        pass

    return {"created": True, "version": version.to_dict()}


@router.post("/rules/{version_id}/submit")
async def submit_rule_for_review(
    version_id: str,
    submitter_id: str = Query(...),
) -> dict[str, Any]:
    """Submit a draft rule for review."""
    from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

    manager = get_rule_lifecycle_manager()
    version, error = manager.submit_for_review(version_id, submitter_id)

    if version is None:
        return JSONResponse(content={"error": error}, status_code=400)
    return {"submitted": True, "version": version.to_dict()}


@router.post("/rules/{version_id}/approve")
async def approve_rule(
    version_id: str,
    reviewer_id: str = Query(...),
) -> dict[str, Any]:
    """Approve a rule under review. Reviewer must differ from author."""
    from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

    manager = get_rule_lifecycle_manager()
    version, error = manager.approve(version_id, reviewer_id)

    if version is None:
        return JSONResponse(content={"error": error}, status_code=400)
    return {"approved": True, "version": version.to_dict()}


@router.post("/rules/{version_id}/reject")
async def reject_rule(
    version_id: str,
    reviewer_id: str = Query(...),
    reason: str = Query(default=""),
) -> dict[str, Any]:
    """Reject a rule under review."""
    from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

    manager = get_rule_lifecycle_manager()
    version, error = manager.reject(version_id, reviewer_id, reason)

    if version is None:
        return JSONResponse(content={"error": error}, status_code=400)
    return {"rejected": True, "version": version.to_dict()}


@router.post("/rules/{version_id}/activate")
async def activate_rule(
    version_id: str,
    operator_id: str = Query(...),
) -> dict[str, Any]:
    """Activate a rule, pushing it to the policy engine."""
    from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

    manager = get_rule_lifecycle_manager()
    version, error = manager.activate(version_id, operator_id)

    if version is None:
        return JSONResponse(content={"error": error}, status_code=400)
    return {"activated": True, "version": version.to_dict()}


@router.post("/rules/{version_id}/retire")
async def retire_rule(
    version_id: str,
    operator_id: str = Query(...),
    reason: str = Query(default=""),
) -> dict[str, Any]:
    """Retire an active rule, removing it from the policy engine."""
    from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

    manager = get_rule_lifecycle_manager()
    version, error = manager.retire(version_id, operator_id, reason)

    if version is None:
        return JSONResponse(content={"error": error}, status_code=400)
    return {"retired": True, "version": version.to_dict()}


@router.get("/rules/versions/{rule_id}")
async def list_rule_versions(rule_id: str) -> dict[str, Any]:
    """List all versions of a rule."""
    from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

    manager = get_rule_lifecycle_manager()
    versions = manager.get_versions(rule_id)
    return {
        "rule_id": rule_id,
        "count": len(versions),
        "versions": [v.to_dict() for v in versions],
    }


@router.get("/rules/promotions/{rule_id}")
async def list_rule_promotions(rule_id: str) -> dict[str, Any]:
    """List promotion history for a rule."""
    from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

    manager = get_rule_lifecycle_manager()
    promotions = manager.get_promotions(rule_id)
    return {
        "rule_id": rule_id,
        "count": len(promotions),
        "promotions": [p.to_dict() for p in promotions],
    }


@router.post("/rules/diff")
async def diff_rule_versions(
    version_a: str = Query(...),
    version_b: str = Query(...),
) -> dict[str, Any]:
    """Compare two rule versions."""
    from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

    manager = get_rule_lifecycle_manager()
    diff = manager.diff_versions(version_a, version_b)

    if diff is None:
        return JSONResponse(
            content={"error": "One or both versions not found"},
            status_code=404,
        )
    return {"diff": diff}




# ---------------------------------------------------------------------------
# V12 — Production Federation endpoints
# ---------------------------------------------------------------------------


# V12A — OIDC / OAuth2 endpoints -------------------------------------------


@router.post("/oidc/providers/register")
async def register_oidc_provider(
    issuer_url: str = Query(...),
    client_id: str = Query(...),
    audience: str = Query(""),
) -> dict[str, Any]:
    """Register an OIDC identity provider."""
    from src.kortana.services.oidc_provider import get_oidc_registry

    registry = get_oidc_registry()
    provider = registry.register(issuer_url, client_id, audience or None)
    return {
        "status": "registered",
        "issuer_url": issuer_url,
        "client_id": client_id,
        "provider_count": len(registry.list_providers()),
        "config_hash": provider.config.config_hash,
    }


@router.get("/oidc/providers")
async def list_oidc_providers() -> dict[str, Any]:
    """List registered OIDC providers."""
    from src.kortana.services.oidc_provider import get_oidc_registry

    registry = get_oidc_registry()
    providers = registry.list_providers()
    return {
        "providers": [
            {
                "issuer_url": p.config.issuer_url,
                "client_id": p.config.client_id,
                "audience": p.config.audience,
                "config_hash": p.config.config_hash,
            }
            for p in providers
        ],
        "count": len(providers),
    }


@router.post("/oidc/verify")
async def verify_oidc_token(
    token: str = Query(...),
    issuer_url: str = Query(...),
) -> dict[str, Any]:
    """Verify a JWT token against a registered OIDC provider."""
    from src.kortana.services.oidc_provider import get_oidc_registry

    registry = get_oidc_registry()
    provider = registry.get_oidc_provider(issuer_url)
    if provider is None:
        return JSONResponse(
            content={"error": f"Provider {issuer_url!r} not registered"},
            status_code=404,
        )

    claims, error = provider.verify_token(token)
    if error:
        return JSONResponse(
            content={"error": error},
            status_code=401,
        )
    return {"verified": True, "claims": claims.to_dict()}


@router.post("/oauth2/authorize")
async def start_oauth2_flow(
    issuer_url: str = Query(...),
    redirect_uri: str = Query(...),
) -> dict[str, Any]:
    """Start an OAuth2 authorization flow with PKCE."""
    from src.kortana.services.oidc_provider import get_oidc_registry

    registry = get_oidc_registry()
    oauth2 = registry.get_oauth2_provider(issuer_url)
    if oauth2 is None:
        return JSONResponse(
            content={"error": f"OAuth2 provider for {issuer_url!r} not registered"},
            status_code=404,
        )

    url, flow = oauth2.create_authorization_url(redirect_uri)
    return {
        "authorization_url": url,
        "flow_id": flow.flow_id,
        "state": flow.state,
    }


@router.post("/oauth2/callback")
async def handle_oauth2_callback(
    code: str = Query(...),
    state: str = Query(...),
    issuer_url: str = Query(...),
) -> dict[str, Any]:
    """Handle OAuth2 callback with authorization code exchange."""
    from src.kortana.services.oidc_provider import get_oidc_registry

    registry = get_oidc_registry()
    oauth2 = registry.get_oauth2_provider(issuer_url)
    if oauth2 is None:
        return JSONResponse(
            content={"error": f"OAuth2 provider for {issuer_url!r} not registered"},
            status_code=404,
        )

    claims, error = oauth2.exchange_code(code, state)
    if error:
        return JSONResponse(
            content={"error": error},
            status_code=400,
        )
    return {"authenticated": True, "claims": claims.to_dict()}


# V12B — Key Rotation endpoints -------------------------------------------


@router.post("/keys/rotation/schedule")
async def schedule_key_rotation(
    key_id: str = Query(...),
    provider_type: str = Query(...),
    operator_id: str = Query(...),
    rotation_interval_hours: int = Query(720),
    grace_period_hours: int = Query(24),
) -> dict[str, Any]:
    """Schedule automatic key rotation."""
    from src.kortana.services.key_rotation import get_key_rotation_manager

    manager = get_key_rotation_manager()
    schedule = manager.schedule_rotation(
        key_id=key_id,
        provider_type=provider_type,
        operator_id=operator_id,
        rotation_interval_hours=rotation_interval_hours,
        grace_period_hours=grace_period_hours,
    )
    return {"status": "scheduled", "schedule": schedule.to_dict()}


@router.get("/keys/rotation/schedules")
async def list_rotation_schedules() -> dict[str, Any]:
    """List all rotation schedules."""
    from src.kortana.services.key_rotation import get_key_rotation_manager

    manager = get_key_rotation_manager()
    schedules = manager.get_schedules()
    return {
        "schedules": [s.to_dict() for s in schedules],
        "active_count": manager.active_schedule_count,
    }


@router.get("/keys/rotation/due")
async def list_due_rotations() -> dict[str, Any]:
    """List rotation schedules that are due."""
    from src.kortana.services.key_rotation import get_key_rotation_manager

    manager = get_key_rotation_manager()
    due = manager.check_due_rotations()
    return {
        "due": [s.to_dict() for s in due],
        "due_count": len(due),
    }


@router.post("/keys/rotation/{key_id}/execute")
async def execute_key_rotation(
    key_id: str,
    initiated_by: str = Query("system"),
    event_type: str = Query("manual"),
) -> dict[str, Any]:
    """Execute key rotation for a specific key."""
    from src.kortana.services.key_rotation import get_key_rotation_manager

    manager = get_key_rotation_manager()
    event, error = manager.execute_rotation(key_id, initiated_by, event_type)
    if error:
        return JSONResponse(
            content={"error": error},
            status_code=400,
        )
    return {"status": "rotated", "event": event.to_dict()}


@router.post("/keys/rotation/{key_id}/expire-grace")
async def expire_key_grace_period(key_id: str) -> dict[str, Any]:
    """Expire the grace period for a key and revoke the old credential."""
    from src.kortana.services.key_rotation import get_key_rotation_manager

    manager = get_key_rotation_manager()
    event, error = manager.expire_grace_period(key_id)
    if error:
        return JSONResponse(
            content={"error": error},
            status_code=400,
        )
    return {"status": "grace_expired", "event": event.to_dict()}


@router.get("/keys/rotation/{key_id}/history")
async def get_rotation_history(key_id: str) -> dict[str, Any]:
    """Get rotation event history for a key."""
    from src.kortana.services.key_rotation import get_key_rotation_manager

    manager = get_key_rotation_manager()
    history = manager.get_rotation_history(key_id)
    return {"key_id": key_id, "events": [e.to_dict() for e in history]}


# V12C — CI Credential Enforcement endpoints --------------------------------


@router.post("/ci/enforce")
async def enforce_ci_credential(
    checkpoint: str = Query(...),
    session_id: str = Query(...),
) -> dict[str, Any]:
    """Enforce CI credential policy at a checkpoint."""
    from src.kortana.services.ci_credential_enforcement import (
        CICheckpoint,
        get_default_ci_policies,
    )
    from src.kortana.services.ci_credential_enforcement import (
        enforce_ci_credential as _enforce,
    )

    try:
        CICheckpoint(checkpoint)
    except ValueError:
        return JSONResponse(
            content={"error": f"Unknown checkpoint: {checkpoint!r}"},
            status_code=400,
        )

    policies = get_default_ci_policies()
    policy = policies.get(checkpoint)
    if policy is None:
        return JSONResponse(
            content={"error": f"No policy for checkpoint {checkpoint!r}"},
            status_code=400,
        )

    check = _enforce(session_id, policy)
    return {"check": check.to_dict()}


@router.post("/ci/edges/register")
async def register_protected_edge(
    path_pattern: str = Query(...),
    description: str = Query(""),
) -> dict[str, Any]:
    """Register a protected runtime edge."""
    from src.kortana.services.ci_credential_enforcement import (
        CICheckpoint,
        CICredentialPolicy,
        get_ci_enforcer,
    )

    enforcer = get_ci_enforcer()
    policy = CICredentialPolicy(
        name=description or f"edge:{path_pattern}",
        checkpoint=CICheckpoint.RUNTIME_EDGE,
    )
    enforcer.register_edge(path_pattern, policy)
    return {
        "status": "registered",
        "path_pattern": path_pattern,
        "edge_count": enforcer.edge_count,
    }


@router.post("/ci/edges/check")
async def check_protected_edge(
    path: str = Query(...),
    session_id: str = Query(...),
) -> dict[str, Any]:
    """Check if a request path is protected and enforce credentials."""
    from src.kortana.services.ci_credential_enforcement import get_ci_enforcer

    enforcer = get_ci_enforcer()
    check = enforcer.check_edge(path, session_id)
    if check is None:
        return {"protected": False, "path": path}
    return {"protected": True, "check": check.to_dict()}


@router.get("/ci/edges")
async def list_protected_edges() -> dict[str, Any]:
    """List registered protected edges."""
    from src.kortana.services.ci_credential_enforcement import get_ci_enforcer

    enforcer = get_ci_enforcer()
    return {
        "edges": [
            {"path_pattern": e.path_pattern, "policy": e.policy.name}
            for e in enforcer.protected_edges
        ],
        "count": enforcer.edge_count,
    }


@router.get("/ci/policies")
async def list_ci_policies() -> dict[str, Any]:
    """List default CI credential policies."""
    from src.kortana.services.ci_credential_enforcement import get_default_ci_policies

    policies = get_default_ci_policies()
    return {
        "policies": {k: v.to_dict() for k, v in policies.items()},
        "count": len(policies),
    }


# V12D — Authenticated Promotion endpoints ---------------------------------


@router.post("/rules/authenticated/{version_id}/submit")
async def authenticated_submit_for_review(
    version_id: str,
    session_id: str = Query(...),
) -> dict[str, Any]:
    """Submit a rule for review with authenticated session."""
    from src.kortana.services.authenticated_promotion import (
        get_authenticated_promotion_manager,
    )

    manager = get_authenticated_promotion_manager()
    version, error = manager.submit_for_review(version_id, session_id)
    if error:
        return JSONResponse(content={"error": error}, status_code=400)
    return {"status": "submitted", "version_id": version_id}


@router.post("/rules/authenticated/{version_id}/approve")
async def authenticated_approve(
    version_id: str,
    session_id: str = Query(...),
) -> dict[str, Any]:
    """Approve a rule with authenticated session (four-eyes enforced)."""
    from src.kortana.services.authenticated_promotion import (
        get_authenticated_promotion_manager,
    )

    manager = get_authenticated_promotion_manager()
    version, error = manager.approve(version_id, session_id)
    if error:
        return JSONResponse(content={"error": error}, status_code=400)
    return {"status": "approved", "version_id": version_id}


@router.post("/rules/authenticated/{version_id}/reject")
async def authenticated_reject(
    version_id: str,
    session_id: str = Query(...),
    reason: str = Query(""),
) -> dict[str, Any]:
    """Reject a rule with authenticated session."""
    from src.kortana.services.authenticated_promotion import (
        get_authenticated_promotion_manager,
    )

    manager = get_authenticated_promotion_manager()
    version, error = manager.reject(version_id, session_id, reason)
    if error:
        return JSONResponse(content={"error": error}, status_code=400)
    return {"status": "rejected", "version_id": version_id, "reason": reason}


@router.post("/rules/authenticated/{version_id}/activate")
async def authenticated_activate(
    version_id: str,
    session_id: str = Query(...),
) -> dict[str, Any]:
    """Activate a rule with authenticated session."""
    from src.kortana.services.authenticated_promotion import (
        get_authenticated_promotion_manager,
    )

    manager = get_authenticated_promotion_manager()
    version, error = manager.activate(version_id, session_id)
    if error:
        return JSONResponse(content={"error": error}, status_code=400)
    return {"status": "activated", "version_id": version_id}


@router.post("/rules/authenticated/{version_id}/retire")
async def authenticated_retire(
    version_id: str,
    session_id: str = Query(...),
    reason: str = Query(""),
) -> dict[str, Any]:
    """Retire a rule with authenticated session."""
    from src.kortana.services.authenticated_promotion import (
        get_authenticated_promotion_manager,
    )

    manager = get_authenticated_promotion_manager()
    version, error = manager.retire(version_id, session_id, reason)
    if error:
        return JSONResponse(content={"error": error}, status_code=400)
    return {"status": "retired", "version_id": version_id, "reason": reason}


@router.get("/rules/authenticated/events/{version_id}")
async def get_authenticated_promotion_events(version_id: str) -> dict[str, Any]:
    """Get all authenticated promotion events for a rule version."""
    from src.kortana.services.authenticated_promotion import (
        get_authenticated_promotion_manager,
    )

    manager = get_authenticated_promotion_manager()
    events = manager.get_events(version_id)
    return {
        "version_id": version_id,
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }



# ---------------------------------------------------------------------------
# V13 — Enterprise Control Integration endpoints
# ---------------------------------------------------------------------------


# V13A — IdP Discovery endpoints -------------------------------------------


@router.post("/idp/discover")
async def discover_idp(
    discovery_url: str = Query(...),
    issuer: str = Query(""),
    token_endpoint: str = Query(""),
    jwks_uri: str = Query(""),
) -> dict[str, Any]:
    """Register an IdP via discovery payload."""
    from src.kortana.services.idp_discovery import get_idp_discovery_manager

    manager = get_idp_discovery_manager()
    payload: dict[str, Any] = {}
    if issuer:
        payload["issuer"] = issuer
    if token_endpoint:
        payload["token_endpoint"] = token_endpoint
    if jwks_uri:
        payload["jwks_uri"] = jwks_uri
    provider = manager.register_discovery_payload(discovery_url, payload)
    return {"status": "discovered", "provider": provider.to_dict()}


@router.get("/idp/discovered")
async def list_discovered_idps() -> dict[str, Any]:
    """List all discovered identity providers."""
    from src.kortana.services.idp_discovery import get_idp_discovery_manager

    manager = get_idp_discovery_manager()
    providers = manager.list_discovered()
    return {
        "providers": [p.to_dict() for p in providers],
        "count": manager.provider_count,
    }


@router.post("/idp/sync/{discovery_url:path}")
async def sync_idp(discovery_url: str) -> dict[str, Any]:
    """Force sync a discovered IdP."""
    from src.kortana.services.idp_discovery import get_idp_discovery_manager

    manager = get_idp_discovery_manager()
    provider, error = manager.sync_provider(discovery_url)
    if error:
        return JSONResponse(content={"error": error}, status_code=400)
    return {"status": "synced", "provider": provider.to_dict()}


@router.get("/idp/sync/status/{discovery_url:path}")
async def get_idp_sync_status(discovery_url: str) -> dict[str, Any]:
    """Get sync status for a discovered IdP."""
    from src.kortana.services.idp_discovery import get_idp_discovery_manager

    manager = get_idp_discovery_manager()
    status = manager.get_sync_status(discovery_url)
    if status is None:
        return JSONResponse(
            content={"error": f"No sync status for {discovery_url!r}"},
            status_code=404,
        )
    return {"discovery_url": discovery_url, "sync_state": status.value}


@router.get("/idp/sync/events")
async def list_idp_sync_events() -> dict[str, Any]:
    """List all IdP sync events."""
    from src.kortana.services.idp_discovery import get_idp_discovery_manager

    manager = get_idp_discovery_manager()
    events = manager.get_sync_events()
    return {"events": [e.to_dict() for e in events], "count": manager.event_count}


# V13B — Secret Store endpoints --------------------------------------------


@router.post("/secrets/store")
async def store_secret(
    secret_id: str = Query(...),
    value: str = Query(...),
    backend: str = Query("local"),
    path: str = Query(""),
) -> dict[str, Any]:
    """Store a secret in the named backend."""
    from src.kortana.services.secret_store import get_secret_store_registry

    registry = get_secret_store_registry()
    ref = registry.store_secret(secret_id, value, backend, path)
    return {"status": "stored", "reference": ref.to_dict()}


@router.get("/secrets/fetch/{secret_id}")
async def fetch_secret(secret_id: str, backend: str = Query("local")) -> dict[str, Any]:
    """Fetch a secret (value is redacted)."""
    from src.kortana.services.secret_store import get_secret_store_registry

    registry = get_secret_store_registry()
    secret = registry.fetch_secret(secret_id, backend)
    if secret is None:
        return JSONResponse(
            content={"error": f"Secret {secret_id!r} not found"},
            status_code=404,
        )
    return {"secret": secret.to_dict()}


@router.post("/secrets/rotate/{secret_id}")
async def rotate_secret(
    secret_id: str,
    new_value: str = Query(...),
    backend: str = Query("local"),
) -> dict[str, Any]:
    """Rotate a secret to a new value."""
    from src.kortana.services.secret_store import get_secret_store_registry

    registry = get_secret_store_registry()
    ref = registry.rotate_secret(secret_id, new_value, backend)
    return {"status": "rotated", "reference": ref.to_dict()}


@router.delete("/secrets/{secret_id}")
async def delete_secret(
    secret_id: str, backend: str = Query("local")
) -> dict[str, Any]:
    """Delete a secret."""
    from src.kortana.services.secret_store import get_secret_store_registry

    registry = get_secret_store_registry()
    deleted = registry.delete_secret(secret_id, backend)
    return {"deleted": deleted, "secret_id": secret_id}


@router.get("/secrets")
async def list_secrets(backend: str = Query("local")) -> dict[str, Any]:
    """List secrets in a backend."""
    from src.kortana.services.secret_store import get_secret_store_registry

    registry = get_secret_store_registry()
    refs = registry.list_secrets(backend)
    return {"secrets": [r.to_dict() for r in refs], "count": len(refs)}


@router.get("/secrets/backends")
async def list_secret_backends() -> dict[str, Any]:
    """List registered secret backends."""
    from src.kortana.services.secret_store import get_secret_store_registry

    registry = get_secret_store_registry()
    return {"backends": registry.list_backends(), "count": registry.backend_count}


# V13C — Webhook Attestation endpoints -------------------------------------


@router.post("/attestation/sign")
async def sign_webhook(
    payload: str = Query(...),
    secret: str = Query(...),
) -> dict[str, Any]:
    """Sign a webhook payload with HMAC-SHA256."""
    from src.kortana.services.webhook_attestation import WebhookSigner

    signature = WebhookSigner.sign(payload.encode(), secret)
    return {"signature": signature, "algorithm": "hmac-sha256"}


@router.post("/attestation/verify")
async def verify_webhook(
    payload: str = Query(...),
    signature: str = Query(...),
    secret: str = Query(...),
) -> dict[str, Any]:
    """Verify an HMAC-SHA256 webhook signature."""
    from src.kortana.services.webhook_attestation import WebhookSigner

    valid = WebhookSigner.verify(payload.encode(), signature, secret)
    return {"valid": valid}


@router.post("/attestation/signers/register")
async def register_trusted_signer(
    signer_id: str = Query(...),
    key: str = Query(...),
) -> dict[str, Any]:
    """Register a trusted CI attestation signer."""
    from src.kortana.services.webhook_attestation import get_attestation_verifier

    verifier = get_attestation_verifier()
    verifier.register_trusted_signer(signer_id, key)
    return {
        "status": "registered",
        "signer_id": signer_id,
        "signer_count": verifier.signer_count,
    }


@router.get("/attestation/signers")
async def list_trusted_signers() -> dict[str, Any]:
    """List trusted attestation signers."""
    from src.kortana.services.webhook_attestation import get_attestation_verifier

    verifier = get_attestation_verifier()
    return {
        "signers": verifier.list_trusted_signers(),
        "count": verifier.signer_count,
    }


# V13D — Trust Signal Consumer endpoints -----------------------------------


@router.post("/trust/signals/register")
async def register_trust_signal(
    signal_type: str = Query(...),
    source: str = Query(""),
    confidence: float = Query(1.0),
    version_id: str = Query(""),
) -> dict[str, Any]:
    """Register an incoming trust signal."""
    from src.kortana.services.trust_signal_consumer import (
        TrustSignal,
        TrustSignalType,
        get_trust_signal_consumer,
    )

    try:
        st = TrustSignalType(signal_type)
    except ValueError:
        return JSONResponse(
            content={"error": f"Unknown signal type: {signal_type!r}"},
            status_code=400,
        )

    consumer = get_trust_signal_consumer()
    signal = consumer.register_signal(
        TrustSignal(
            signal_type=st,
            source=source,
            confidence=confidence,
            version_id=version_id,
        )
    )
    return {"status": "registered", "signal": signal.to_dict()}


@router.get("/trust/signals")
async def list_trust_signals(
    signal_type: str = Query(""),
) -> dict[str, Any]:
    """List trust signals, optionally filtered by type."""
    from src.kortana.services.trust_signal_consumer import (
        TrustSignalType,
        get_trust_signal_consumer,
    )

    consumer = get_trust_signal_consumer()
    if signal_type:
        try:
            st = TrustSignalType(signal_type)
        except ValueError:
            return JSONResponse(
                content={"error": f"Unknown signal type: {signal_type!r}"},
                status_code=400,
            )
        signals = consumer.get_signals(st)
    else:
        signals = consumer.get_signals()
    return {"signals": [s.to_dict() for s in signals], "count": len(signals)}


@router.post("/trust/evaluate")
async def evaluate_trust(
    required_signals: str = Query(...),
    min_confidence: float = Query(0.8),
    version_id: str = Query(""),
) -> dict[str, Any]:
    """Evaluate trust signals against requirements."""
    from src.kortana.services.trust_signal_consumer import (
        TrustRequirement,
        TrustSignalType,
        get_trust_signal_consumer,
    )

    signal_types: list[TrustSignalType] = []
    for s in required_signals.split(","):
        s = s.strip()
        if s:
            try:
                signal_types.append(TrustSignalType(s))
            except ValueError:
                return JSONResponse(
                    content={"error": f"Unknown signal type: {s!r}"},
                    status_code=400,
                )

    consumer = get_trust_signal_consumer()
    req = TrustRequirement(
        required_signals=signal_types,
        min_confidence=min_confidence,
    )
    evaluation = consumer.evaluate(req, version_id=version_id)
    return {"evaluation": evaluation.to_dict()}


@router.post("/trust/deploy/{version_id}")
async def deploy_with_trust(
    version_id: str,
    session_id: str = Query(...),
    required_signals: str = Query(...),
    min_confidence: float = Query(0.8),
) -> dict[str, Any]:
    """Deploy a rule version gated by trust signal evaluation."""
    from src.kortana.services.trust_signal_consumer import (
        DeployTrustGate,
        TrustRequirement,
        TrustSignalType,
        get_trust_signal_consumer,
    )

    signal_types: list[TrustSignalType] = []
    for s in required_signals.split(","):
        s = s.strip()
        if s:
            try:
                signal_types.append(TrustSignalType(s))
            except ValueError:
                return JSONResponse(
                    content={"error": f"Unknown signal type: {s!r}"},
                    status_code=400,
                )

    gate = DeployTrustGate(get_trust_signal_consumer())
    req = TrustRequirement(
        required_signals=signal_types,
        min_confidence=min_confidence,
    )
    result, error = gate.promote_with_trust(version_id, session_id, req)
    if error:
        return JSONResponse(content={"error": error}, status_code=400)
    return {"status": "promoted", "version_id": version_id}


@router.get("/trust/evaluations/{version_id}")
async def get_trust_evaluations(version_id: str) -> dict[str, Any]:
    """Get trust evaluations for a version."""
    from src.kortana.services.trust_signal_consumer import get_trust_signal_consumer

    consumer = get_trust_signal_consumer()
    evaluations = consumer.get_evaluations(version_id)
    return {
        "version_id": version_id,
        "evaluations": [e.to_dict() for e in evaluations],
        "count": len(evaluations),
    }



# ── V16 — Live Production Bindings Endpoints ──────────────────────────────


# ── V16A — External Call Adapter ──────────────────────────────────────────

from src.kortana.services.external_call_adapter import (  # noqa: E402
    CallMethod,
    CallOutcome,
    EndpointConfig,
    get_call_router,
)


@router.post("/calls/register-endpoint")
async def register_call_endpoint(
    url: str = Body(...),
    adapter_name: str = Body("http"),
    default_method: str = Body("GET"),
    timeout_seconds: float = Body(30.0),
) -> dict:
    """Register an endpoint for call routing."""
    cr = get_call_router()
    config = EndpointConfig(
        url=url,
        adapter_name=adapter_name,
        default_method=CallMethod(default_method),
        timeout_seconds=timeout_seconds,
    )
    result = cr.register_endpoint(config)
    return {"status": "registered", "endpoint": result.to_dict()}


@router.post("/calls/route/{url:path}")
async def route_call(
    url: str,
    method: str = Body("GET"),
    headers: dict = Body(default={}),
    body: dict = Body(default={}),
    timeout_seconds: float = Body(30.0),
) -> dict:
    """Route a call through the appropriate adapter."""
    cr = get_call_router()
    result = cr.route_call(url, CallMethod(method), headers, body, timeout_seconds)
    return {"status": "routed", "result": result.to_dict()}


@router.post("/calls/reconcile")
async def reconcile_call(
    call_id: str = Body(...),
    expected_outcome: str = Body("success"),
    expected_status: int = Body(200),
) -> dict:
    """Reconcile a call result against expectations."""
    cr = get_call_router()
    history = cr.get_call_history()
    call_result = next((c for c in history if c.call_id == call_id), None)
    if call_result is None:
        return {"error": "Call not found"}
    rec = cr.reconcile(call_result, CallOutcome(expected_outcome), expected_status)
    return {"status": "reconciled", "result": rec.to_dict()}


@router.get("/calls/history")
async def get_call_history(limit: int = 0) -> dict:
    """Get call history."""
    cr = get_call_router()
    history = cr.get_call_history(limit)
    return {"calls": [c.to_dict() for c in history], "count": len(history)}


@router.get("/calls/reconciliations")
async def get_reconciliations() -> dict:
    """Get reconciliation results."""
    cr = get_call_router()
    recs = cr.get_reconciliations()
    return {"reconciliations": [r.to_dict() for r in recs], "count": len(recs)}


@router.get("/calls/endpoints")
async def get_call_endpoints() -> dict:
    """Get registered endpoints."""
    cr = get_call_router()
    endpoints = cr.get_endpoints()
    return {"endpoints": [e.to_dict() for e in endpoints], "count": len(endpoints)}


# ── V16B — Persistent Stage Store ─────────────────────────────────────────

from src.kortana.services.persistent_stage_store import (  # noqa: E402
    SideEffectType,
    get_stage_persistence_store,
)


@router.post("/stages/persist-transition")
async def persist_stage_transition(
    pipeline_id: str = Body(...),
    version_id: str = Body(...),
    from_stage: str = Body(""),
    to_stage: str = Body(...),
    gate_verdict: str = Body("pass"),
    gate_check_id: str = Body(""),
) -> dict:
    """Persist a stage transition."""
    store = get_stage_persistence_store()
    record = store.persist_transition(
        pipeline_id, version_id, from_stage, to_stage, gate_verdict, gate_check_id,
    )
    return {"status": "persisted", "transition": record.to_dict()}


@router.get("/stages/transitions/{pipeline_id}")
async def get_stage_transitions(pipeline_id: str) -> dict:
    """Get transitions for a pipeline."""
    store = get_stage_persistence_store()
    transitions = store.get_transitions(pipeline_id)
    return {"transitions": [t.to_dict() for t in transitions], "count": len(transitions)}


@router.post("/stages/persist-rollback-effect")
async def persist_rollback_effect(
    rollback_id: str = Body(...),
    pipeline_id: str = Body(...),
    version_id: str = Body(...),
    effect_type: str = Body("config_reverted"),
    affected_resource: str = Body(""),
    description: str = Body(""),
) -> dict:
    """Persist a rollback side-effect."""
    store = get_stage_persistence_store()
    effect = store.persist_rollback_effect(
        rollback_id, pipeline_id, version_id,
        SideEffectType(effect_type), affected_resource, description,
    )
    return {"status": "persisted", "effect": effect.to_dict()}


@router.get("/stages/rollback-effects/{rollback_id}")
async def get_rollback_effects(rollback_id: str) -> dict:
    """Get side-effects for a rollback."""
    store = get_stage_persistence_store()
    effects = store.get_rollback_effects(rollback_id)
    return {"effects": [e.to_dict() for e in effects], "count": len(effects)}


@router.post("/stages/verify-integrity/{pipeline_id}")
async def verify_stage_integrity(pipeline_id: str) -> dict:
    """Verify integrity of persisted transitions."""
    store = get_stage_persistence_store()
    check = store.verify_persistence_integrity(pipeline_id)
    return {"status": "checked", "integrity": check.to_dict()}


@router.get("/stages/all-transitions")
async def get_all_stage_transitions() -> dict:
    """Get all transitions across all pipelines."""
    store = get_stage_persistence_store()
    transitions = store.get_all_transitions()
    return {"transitions": [t.to_dict() for t in transitions], "count": len(transitions)}


# ── V16C — Deployment Binding ─────────────────────────────────────────────

from src.kortana.services.deployment_binding import (  # noqa: E402
    ActionType,
    TargetEnvironment,
    get_deployment_binding,
)


@router.post("/deploy/register-target")
async def register_deployment_target(
    name: str = Body(...),
    environment: str = Body("staging"),
    endpoint_url: str = Body(""),
    credentials_ref: str = Body(""),
    health_check_url: str = Body(""),
) -> dict:
    """Register a deployment target."""
    binding = get_deployment_binding()
    target = binding.register_target(
        name, TargetEnvironment(environment),
        endpoint_url, credentials_ref, health_check_url,
    )
    return {"status": "registered", "target": target.to_dict()}


@router.post("/deploy/bind-pipeline")
async def bind_pipeline_to_target(
    pipeline_id: str = Body(...),
    target_id: str = Body(...),
    version_id: str = Body(""),
    stage_mapping: dict = Body(default={}),
) -> dict:
    """Bind a pipeline to a deployment target."""
    binding = get_deployment_binding()
    result = binding.bind_pipeline(pipeline_id, target_id, version_id, stage_mapping)
    if result is None:
        return {"error": "Target not found"}
    return {"status": "bound", "binding": result.to_dict()}


@router.post("/deploy/execute")
async def execute_deployment(
    target_id: str = Body(...),
    pipeline_id: str = Body(...),
    version_id: str = Body(...),
    stage: str = Body(""),
    action_type: str = Body("deploy"),
    simulate_failure: bool = Body(False),
) -> dict:
    """Execute a deployment action."""
    binding = get_deployment_binding()
    action = binding.execute_deployment(
        target_id, pipeline_id, version_id, stage,
        ActionType(action_type), simulate_failure,
    )
    return {"status": action.status.value, "action": action.to_dict()}


@router.post("/deploy/verify/{action_id}")
async def verify_deployment(
    action_id: str,
    expected_version: str = Body(""),
    simulate_mismatch: bool = Body(False),
    simulate_unhealthy: bool = Body(False),
) -> dict:
    """Verify a deployment actually landed."""
    binding = get_deployment_binding()
    verification = binding.verify_deployment(
        action_id, expected_version, simulate_mismatch, simulate_unhealthy,
    )
    return {"status": "verified" if verification.verified else "failed", "verification": verification.to_dict()}


@router.get("/deploy/targets")
async def list_deployment_targets(environment: str | None = None) -> dict:
    """List deployment targets."""
    binding = get_deployment_binding()
    env = TargetEnvironment(environment) if environment else None
    targets = binding.list_targets(env)
    return {"targets": [t.to_dict() for t in targets], "count": len(targets)}


@router.get("/deploy/bindings")
async def list_pipeline_bindings(pipeline_id: str = "") -> dict:
    """List pipeline bindings."""
    binding = get_deployment_binding()
    bindings = binding.get_bindings(pipeline_id)
    return {"bindings": [b.to_dict() for b in bindings], "count": len(bindings)}


@router.get("/deploy/actions")
async def list_deployment_actions(pipeline_id: str = "", target_id: str = "") -> dict:
    """List deployment actions."""
    binding = get_deployment_binding()
    actions = binding.get_actions(pipeline_id, target_id)
    return {"actions": [a.to_dict() for a in actions], "count": len(actions)}


# ── V16D — External Verification ─────────────────────────────────────────

from src.kortana.services.external_verification import (  # noqa: E402
    ProbeType,
    get_external_verifier,
)


@router.post("/verify/create-campaign")
async def create_verification_campaign(
    version_id: str = Body(...),
    pipeline_id: str = Body(""),
    description: str = Body(""),
) -> dict:
    """Create a verification campaign."""
    verifier = get_external_verifier()
    campaign = verifier.create_campaign(version_id, pipeline_id, description)
    return {"status": "created", "campaign": campaign.to_dict()}


@router.post("/verify/add-probe/{campaign_id}")
async def add_verification_probe(
    campaign_id: str,
    target_system: str = Body(...),
    probe_type: str = Body("version_check"),
    expected_state: dict = Body(default={}),
) -> dict:
    """Add a probe to a campaign."""
    verifier = get_external_verifier()
    probe = verifier.add_probe(
        campaign_id, target_system, ProbeType(probe_type), expected_state,
    )
    if probe is None:
        return {"error": "Campaign not found"}
    return {"status": "added", "probe": probe.to_dict()}


@router.post("/verify/execute-campaign/{campaign_id}")
async def execute_verification_campaign(
    campaign_id: str,
    observed_states: dict = Body(default={}),
    simulate_unreachable: list = Body(default=[]),
) -> dict:
    """Execute all probes in a campaign."""
    verifier = get_external_verifier()
    campaign = verifier.execute_campaign(campaign_id, observed_states, simulate_unreachable)
    if campaign is None:
        return {"error": "Campaign not found"}
    return {"status": campaign.status.value, "campaign": campaign.to_dict()}


@router.post("/verify/check-campaign/{campaign_id}")
async def check_verification_campaign(campaign_id: str) -> dict:
    """Check whether a campaign fully verified."""
    verifier = get_external_verifier()
    verified, reason = verifier.verify_campaign(campaign_id)
    return {"verified": verified, "reason": reason}


@router.get("/verify/campaigns")
async def list_verification_campaigns(
    version_id: str = "",
) -> dict:
    """List verification campaigns."""
    verifier = get_external_verifier()
    campaigns = verifier.get_campaigns(version_id)
    return {"campaigns": [c.to_dict() for c in campaigns], "count": len(campaigns)}


@router.get("/verify/probes/{campaign_id}")
async def get_campaign_probes(campaign_id: str) -> dict:
    """Get probes for a campaign."""
    verifier = get_external_verifier()
    probes = verifier.get_probes(campaign_id)
    return {"probes": [p.to_dict() for p in probes], "count": len(probes)}



# ── V17 — Closed-Loop Real-World Enforcement Endpoints ───────────────────


# ── V17A — Provider Client Registry ──────────────────────────────────────

from src.kortana.services.provider_client_registry import (  # noqa: E402
    ProviderClientConfig,
    ProviderOperationType,
    ProviderType,
    get_provider_client_registry,
)


@router.post("/providers/register")
async def register_provider(
    name: str = Body(...),
    provider_type: str = Body("kubernetes"),
    endpoint: str = Body(""),
    namespace: str = Body("default"),
    credentials_ref: str = Body(""),
    timeout_seconds: float = Body(30.0),
) -> dict:
    """Register a provider client."""
    reg = get_provider_client_registry()
    config = ProviderClientConfig(
        provider_type=ProviderType(provider_type),
        name=name,
        endpoint=endpoint,
        credentials_ref=credentials_ref,
        namespace=namespace,
        timeout_seconds=timeout_seconds,
    )
    reg.register(config)
    return {"status": "registered", "provider": config.to_dict()}


@router.post("/providers/{name}/connect")
async def connect_provider(name: str) -> dict:
    """Connect a provider client."""
    reg = get_provider_client_registry()
    record = reg.connect(name)
    return {"status": record.outcome.value, "operation": record.to_dict()}


@router.post("/providers/{name}/disconnect")
async def disconnect_provider(name: str) -> dict:
    """Disconnect a provider client."""
    reg = get_provider_client_registry()
    record = reg.disconnect(name)
    return {"status": record.outcome.value, "operation": record.to_dict()}


@router.post("/providers/{name}/deploy")
async def deploy_to_provider(
    name: str,
    version_id: str = Body(...),
) -> dict:
    """Deploy a version through a provider."""
    reg = get_provider_client_registry()
    record = reg.deploy_version(name, version_id)
    return {"status": record.outcome.value, "operation": record.to_dict()}


@router.post("/providers/{name}/rollback")
async def rollback_provider(
    name: str,
    version_id: str = Body(...),
) -> dict:
    """Rollback to a version through a provider."""
    reg = get_provider_client_registry()
    record = reg.rollback_version(name, version_id)
    return {"status": record.outcome.value, "operation": record.to_dict()}


@router.get("/providers/{name}/health")
async def provider_health(name: str) -> dict:
    """Health check for a provider."""
    reg = get_provider_client_registry()
    report = reg.health_check(name)
    return {"health": report.to_dict()}


@router.get("/providers/{name}/status")
async def provider_status(name: str) -> dict:
    """Get provider status."""
    reg = get_provider_client_registry()
    return {"provider": reg.get_status(name)}


@router.get("/providers/list")
async def list_providers() -> dict:
    """List all providers."""
    reg = get_provider_client_registry()
    return {"providers": reg.list_providers(), "count": reg.provider_count}


@router.get("/providers/operations")
async def get_provider_operations(name: str = "", op_type: str = "") -> dict:
    """Get provider operations."""
    reg = get_provider_client_registry()
    ot = ProviderOperationType(op_type) if op_type else None
    ops = reg.get_operations(name, ot)
    return {"operations": [o.to_dict() for o in ops], "count": len(ops)}


# ── V17B — Rollout Action Executor ───────────────────────────────────────

from src.kortana.services.rollout_action_executor import (  # noqa: E402
    RolloutStatus,
    RolloutStrategy,
    get_rollout_executor,
)


@router.post("/rollouts/plan")
async def plan_rollout(
    provider_name: str = Body(...),
    version_id: str = Body(...),
    strategy: str = Body("rolling"),
    previous_version: str = Body(""),
    auto_rollback: bool = Body(True),
) -> dict:
    """Plan a rollout."""
    executor = get_rollout_executor()
    action = executor.plan_rollout(
        provider_name, version_id, RolloutStrategy(strategy),
        previous_version, auto_rollback,
    )
    return {"status": "planned", "rollout": action.to_dict()}


@router.post("/rollouts/{action_id}/execute-step")
async def execute_rollout_step(
    action_id: str,
    simulate_failure: bool = Body(False),
) -> dict:
    """Execute the next step in a rollout."""
    executor = get_rollout_executor()
    step = executor.execute_step(action_id, simulate_failure)
    if step is None:
        return {"error": "No pending steps or action not found"}
    action = executor.get_action(action_id)
    return {"step": step.to_dict(), "rollout_status": action.status.value if action else "unknown"}


@router.post("/rollouts/{action_id}/observe-step")
async def observe_rollout_step(
    action_id: str,
    step_id: str = Body(...),
    error_rate: float = Body(0.0),
    latency_p99_ms: float = Body(10.0),
    success_rate: float = Body(100.0),
) -> dict:
    """Record an observation for a rollout step."""
    executor = get_rollout_executor()
    obs = executor.observe_step(action_id, step_id, error_rate, latency_p99_ms, success_rate)
    return {"observation": obs.to_dict()}


@router.post("/rollouts/{action_id}/rollback")
async def rollback_rollout(action_id: str) -> dict:
    """Manually rollback a rollout."""
    executor = get_rollout_executor()
    action = executor.rollback_action(action_id)
    if action is None:
        return {"error": "Action not found"}
    return {"status": "rolled_back", "rollout": action.to_dict()}


@router.post("/rollouts/{action_id}/cancel")
async def cancel_rollout(action_id: str) -> dict:
    """Cancel a rollout."""
    executor = get_rollout_executor()
    action = executor.cancel_action(action_id)
    if action is None:
        return {"error": "Action not found"}
    return {"status": "cancelled", "rollout": action.to_dict()}


@router.get("/rollouts/{action_id}")
async def get_rollout(action_id: str) -> dict:
    """Get rollout details."""
    executor = get_rollout_executor()
    action = executor.get_action(action_id)
    if action is None:
        return {"error": "Action not found"}
    return {"rollout": action.to_dict(), "steps": [s.to_dict() for s in action.steps]}


@router.get("/rollouts/list")
async def list_rollouts(provider_name: str = "", status: str = "") -> dict:
    """List rollouts."""
    executor = get_rollout_executor()
    st = RolloutStatus(status) if status else None
    actions = executor.get_actions(provider_name, st)
    return {"rollouts": [a.to_dict() for a in actions], "count": len(actions)}


# ── V17C — Feedback Policy Engine ────────────────────────────────────────

from src.kortana.services.feedback_policy_engine import (  # noqa: E402
    EvaluationOutcome,
    FeedbackAction,
    FeedbackSignal,
    TriggerCondition,
    get_feedback_policy_engine,
)


@router.post("/feedback/register-trigger")
async def register_feedback_trigger(
    name: str = Body(...),
    condition: str = Body("error_rate_above"),
    threshold: float = Body(5.0),
    action: str = Body("alert"),
    pipeline_scope: str = Body(""),
    provider_scope: str = Body(""),
) -> dict:
    """Register a feedback trigger."""
    engine = get_feedback_policy_engine()
    trigger = engine.register_trigger(
        name, TriggerCondition(condition), threshold,
        FeedbackAction(action), pipeline_scope, provider_scope,
    )
    return {"status": "registered", "trigger": trigger.to_dict()}


@router.post("/feedback/{trigger_id}/disable")
async def disable_feedback_trigger(trigger_id: str) -> dict:
    """Disable a feedback trigger."""
    engine = get_feedback_policy_engine()
    ok = engine.disable_trigger(trigger_id)
    return {"status": "disabled" if ok else "not_found"}


@router.post("/feedback/{trigger_id}/enable")
async def enable_feedback_trigger(trigger_id: str) -> dict:
    """Enable a feedback trigger."""
    engine = get_feedback_policy_engine()
    ok = engine.enable_trigger(trigger_id)
    return {"status": "enabled" if ok else "not_found"}


@router.post("/feedback/evaluate-signal")
async def evaluate_feedback_signal(
    source: str = Body(""),
    pipeline_id: str = Body(""),
    provider_name: str = Body(""),
    error_rate: float = Body(0.0),
    success_rate: float = Body(100.0),
    latency_ms: float = Body(0.0),
    health_ok: bool = Body(True),
    probe_matched: bool = Body(True),
    consecutive_failures: int = Body(0),
) -> dict:
    """Evaluate a feedback signal against triggers."""
    engine = get_feedback_policy_engine()
    signal = FeedbackSignal(
        source=source, pipeline_id=pipeline_id, provider_name=provider_name,
        error_rate=error_rate, success_rate=success_rate, latency_ms=latency_ms,
        health_ok=health_ok, probe_matched=probe_matched,
        consecutive_failures=consecutive_failures,
    )
    evaluation = engine.evaluate_signal(signal)
    return {"evaluation": evaluation.to_dict()}


@router.get("/feedback/triggers")
async def list_feedback_triggers(enabled_only: bool = False) -> dict:
    """List feedback triggers."""
    engine = get_feedback_policy_engine()
    triggers = engine.get_triggers(enabled_only)
    return {"triggers": [t.to_dict() for t in triggers], "count": len(triggers)}


@router.get("/feedback/evaluations")
async def list_feedback_evaluations(outcome: str = "") -> dict:
    """List feedback evaluations."""
    engine = get_feedback_policy_engine()
    oc = EvaluationOutcome(outcome) if outcome else None
    evals = engine.get_evaluations(oc)
    return {"evaluations": [e.to_dict() for e in evals], "count": len(evals)}


# ── V17D — Evidence Chain ────────────────────────────────────────────────

from src.kortana.services.evidence_chain import (  # noqa: E402
    ChainStatus,
    EvidenceType,
    get_evidence_chain_registry,
)


@router.post("/evidence/create-chain")
async def create_evidence_chain(
    version_id: str = Body(...),
    description: str = Body(""),
) -> dict:
    """Create a new evidence chain."""
    reg = get_evidence_chain_registry()
    chain = reg.create_chain(version_id, description)
    return {"status": "created", "chain": chain.to_dict()}


@router.post("/evidence/{chain_id}/append")
async def append_evidence_entry(
    chain_id: str,
    evidence_type: str = Body("decision"),
    actor: str = Body(""),
    description: str = Body(""),
    payload: dict = Body(default={}),
) -> dict:
    """Append an entry to an evidence chain."""
    reg = get_evidence_chain_registry()
    chain = reg.get_chain(chain_id)
    if chain is None:
        return {"error": "Chain not found"}
    try:
        entry = chain.append_entry(EvidenceType(evidence_type), actor, description, payload)
        return {"status": "appended", "entry": entry.to_dict()}
    except ValueError as e:
        return {"error": str(e)}


@router.post("/evidence/{chain_id}/seal")
async def seal_evidence_chain(chain_id: str) -> dict:
    """Seal an evidence chain."""
    reg = get_evidence_chain_registry()
    chain = reg.seal_chain(chain_id)
    if chain is None:
        return {"error": "Chain not found"}
    return {"status": chain.status.value, "chain": chain.to_dict()}


@router.post("/evidence/{chain_id}/verify")
async def verify_evidence_chain(chain_id: str) -> dict:
    """Verify an evidence chain's integrity."""
    reg = get_evidence_chain_registry()
    ok, reason = reg.verify_chain(chain_id)
    return {"valid": ok, "reason": reason}


@router.get("/evidence/{chain_id}/convergence-proof")
async def get_convergence_proof(chain_id: str) -> dict:
    """Get convergence proof for a chain."""
    reg = get_evidence_chain_registry()
    proof = reg.get_convergence_proof(chain_id)
    if proof is None:
        return {"error": "Chain not found"}
    return {"proof": proof.to_dict()}


@router.get("/evidence/chains")
async def list_evidence_chains(version_id: str = "", status: str = "") -> dict:
    """List evidence chains."""
    reg = get_evidence_chain_registry()
    st = ChainStatus(status) if status else None
    chains = reg.get_chains(version_id, st)
    return {"chains": [c.to_dict() for c in chains], "count": len(chains)}


@router.post("/evidence/verify-all")
async def verify_all_evidence_chains() -> dict:
    """Verify all evidence chains."""
    reg = get_evidence_chain_registry()
    results = reg.verify_all()
    return {"results": {cid: {"valid": ok, "reason": reason} for cid, (ok, reason) in results.items()}}



# ── V18 — Autonomous Reconciliation Endpoints ───────────────────────────


# ── V18A — Drift Detector ────────────────────────────────────────────────

from src.kortana.services.drift_detector import (  # noqa: E402
    DesiredState,
    DriftStatus,
    DriftType,
    get_drift_detector,
)


@router.post("/drift/register-desired-state")
async def register_desired_state(
    provider_name: str = Body(...),
    expected_version: str = Body(""),
    expected_connected: bool = Body(True),
    expected_healthy: bool = Body(True),
) -> dict:
    """Register desired state for a provider."""
    detector = get_drift_detector()
    state = DesiredState(
        provider_name=provider_name,
        expected_version=expected_version,
        expected_connected=expected_connected,
        expected_healthy=expected_healthy,
    )
    detector.register_desired_state(state)
    return {"status": "registered", "desired_state": state.to_dict()}


@router.post("/drift/detect-provider")
async def detect_provider_drift(
    provider_name: str = Body(...),
    actual_version: str = Body(""),
    actual_connected: bool = Body(True),
    actual_healthy: bool = Body(True),
) -> dict:
    """Detect drift for a specific provider."""
    detector = get_drift_detector()
    signals = detector.detect_provider_drift(provider_name, actual_version, actual_connected, actual_healthy)
    return {"signals": [s.to_dict() for s in signals], "drift_count": len(signals)}


@router.post("/drift/detect-rollout-stall")
async def detect_rollout_stall(
    provider_name: str = Body(...),
    rollout_id: str = Body(...),
    progress_pct: float = Body(0.0),
    stall_threshold_pct: float = Body(0.0),
) -> dict:
    """Detect stalled rollout."""
    detector = get_drift_detector()
    signal = detector.detect_rollout_stall(provider_name, rollout_id, progress_pct, stall_threshold_pct)
    return {"signal": signal.to_dict() if signal else None, "stalled": signal is not None}


@router.post("/drift/detect-evidence-gap")
async def detect_evidence_gap(
    chain_id: str = Body(...),
    missing_stages: list = Body(default=[]),
) -> dict:
    """Detect evidence chain gap."""
    detector = get_drift_detector()
    signal = detector.detect_evidence_gap(chain_id, missing_stages)
    return {"signal": signal.to_dict() if signal else None, "has_gap": signal is not None}


@router.post("/drift/detect-config")
async def detect_config_drift(
    provider_name: str = Body(...),
    config_key: str = Body(...),
    expected: str = Body(...),
    actual: str = Body(...),
) -> dict:
    """Detect configuration drift."""
    detector = get_drift_detector()
    signal = detector.detect_config_drift(provider_name, config_key, expected, actual)
    return {"signal": signal.to_dict() if signal else None, "drifted": signal is not None}


@router.post("/drift/{signal_id}/acknowledge")
async def acknowledge_drift(signal_id: str) -> dict:
    """Acknowledge a drift signal."""
    detector = get_drift_detector()
    ok = detector.acknowledge_drift(signal_id)
    return {"status": "acknowledged" if ok else "not_found"}


@router.post("/drift/{signal_id}/resolve")
async def resolve_drift(signal_id: str) -> dict:
    """Resolve a drift signal."""
    detector = get_drift_detector()
    ok = detector.resolve_drift(signal_id)
    return {"status": "resolved" if ok else "not_found"}


@router.post("/drift/{signal_id}/ignore")
async def ignore_drift(signal_id: str) -> dict:
    """Ignore a drift signal."""
    detector = get_drift_detector()
    ok = detector.ignore_drift(signal_id)
    return {"status": "ignored" if ok else "not_found"}


@router.get("/drift/signals")
async def list_drift_signals(provider_name: str = "", drift_type: str = "", status: str = "") -> dict:
    """List drift signals."""
    detector = get_drift_detector()
    dt = DriftType(drift_type) if drift_type else None
    st = DriftStatus(status) if status else None
    signals = detector.get_drift_signals(provider_name, dt, st)
    return {"signals": [s.to_dict() for s in signals], "count": len(signals)}


@router.get("/drift/active")
async def get_active_drifts() -> dict:
    """Get active drift signals."""
    detector = get_drift_detector()
    active = detector.get_active_drifts()
    return {"active_drifts": [s.to_dict() for s in active], "count": len(active)}


# ── V18B — Reconciliation Planner ────────────────────────────────────────

from src.kortana.services.reconciliation_planner import (  # noqa: E402
    PlanPriority,
    PlanStatus,
    get_reconciliation_planner,
)


@router.post("/reconciliation/plan-from-drift")
async def plan_from_drift(signal_id: str = Body(...)) -> dict:
    """Generate a reconciliation plan from a drift signal."""
    detector = get_drift_detector()
    signals = detector.get_drift_signals()
    matched = [s for s in signals if s.signal_id == signal_id]
    if not matched:
        return {"error": "Signal not found"}
    planner = get_reconciliation_planner()
    plan = planner.plan_from_drift(matched[0])
    return {"status": "planned", "plan": plan.to_dict()}


@router.post("/reconciliation/plan-from-active")
async def plan_from_active_drifts() -> dict:
    """Generate a reconciliation plan from all active drifts."""
    detector = get_drift_detector()
    active = detector.get_active_drifts()
    planner = get_reconciliation_planner()
    plan = planner.plan_from_batch(active)
    return {"status": "planned", "plan": plan.to_dict(), "drift_count": len(active)}


@router.post("/reconciliation/{plan_id}/approve")
async def approve_reconciliation_plan(plan_id: str) -> dict:
    """Approve a reconciliation plan."""
    planner = get_reconciliation_planner()
    ok = planner.approve_plan(plan_id)
    return {"status": "approved" if ok else "not_found"}


@router.post("/reconciliation/{plan_id}/cancel")
async def cancel_reconciliation_plan(plan_id: str) -> dict:
    """Cancel a reconciliation plan."""
    planner = get_reconciliation_planner()
    ok = planner.cancel_plan(plan_id)
    return {"status": "cancelled" if ok else "not_found"}


@router.get("/reconciliation/plans")
async def list_reconciliation_plans(status: str = "", priority: str = "") -> dict:
    """List reconciliation plans."""
    planner = get_reconciliation_planner()
    st = PlanStatus(status) if status else None
    pr = PlanPriority(priority) if priority else None
    plans = planner.get_plans(st, pr)
    return {"plans": [p.to_dict() for p in plans], "count": len(plans)}


# ── V18C — Reconciliation Executor ───────────────────────────────────────

from src.kortana.services.reconciliation_executor import (  # noqa: E402
    ExecutionStatus,
    get_reconciliation_executor,
)


@router.post("/reconciliation/{plan_id}/execute")
async def execute_reconciliation_plan(plan_id: str) -> dict:
    """Execute a reconciliation plan."""
    planner = get_reconciliation_planner()
    plan = planner.get_plan(plan_id)
    if plan is None:
        return {"error": "Plan not found"}
    executor = get_reconciliation_executor()
    execution = executor.execute_plan(plan)
    return {"status": execution.status.value, "execution": execution.to_dict()}


@router.post("/reconciliation/executions/{execution_id}/retry/{step_id}")
async def retry_reconciliation_step(execution_id: str, step_id: str) -> dict:
    """Retry a failed reconciliation step."""
    executor = get_reconciliation_executor()
    result = executor.retry_step(execution_id, step_id)
    if result is None:
        return {"error": "Step not found or not retryable"}
    return {"status": result.outcome.value, "step": result.to_dict()}


@router.post("/reconciliation/executions/{execution_id}/escalate/{step_id}")
async def escalate_reconciliation_step(
    execution_id: str,
    step_id: str,
    reason: str = Body(""),
) -> dict:
    """Escalate a failed step to human intervention."""
    executor = get_reconciliation_executor()
    result = executor.escalate_step(execution_id, step_id, reason)
    if result is None:
        return {"error": "Step not found or not escalatable"}
    return {"status": "escalated", "step": result.to_dict()}


@router.get("/reconciliation/executions")
async def list_reconciliation_executions(plan_id: str = "", status: str = "") -> dict:
    """List reconciliation executions."""
    executor = get_reconciliation_executor()
    st = ExecutionStatus(status) if status else None
    executions = executor.get_executions(plan_id, st)
    return {"executions": [e.to_dict() for e in executions], "count": len(executions)}


# ── V18D — Convergence Manager ───────────────────────────────────────────

from src.kortana.services.convergence_manager import (  # noqa: E402
    get_convergence_manager,
)


@router.post("/convergence/snapshot")
async def take_convergence_snapshot() -> dict:
    """Take a point-in-time convergence snapshot."""
    mgr = get_convergence_manager()
    snapshot = mgr.take_snapshot()
    return {"snapshot": snapshot.to_dict()}


@router.get("/convergence/status")
async def get_convergence_status() -> dict:
    """Get current convergence status."""
    mgr = get_convergence_manager()
    status = mgr.get_status()
    healthy = mgr.is_healthy()
    latest = mgr.get_latest_snapshot()
    return {
        "status": status.value,
        "healthy": healthy,
        "latest_snapshot": latest.to_dict() if latest else None,
    }


@router.get("/convergence/history")
async def get_convergence_history(limit: int = 50) -> dict:
    """Get convergence history."""
    mgr = get_convergence_manager()
    history = mgr.get_history(limit)
    return {"snapshots": [s.to_dict() for s in history], "count": len(history)}


@router.get("/convergence/systemic-issues")
async def get_systemic_issues() -> dict:
    """Get current systemic issues."""
    mgr = get_convergence_manager()
    issues = mgr.get_systemic_issues()
    return {"issues": [i.to_dict() for i in issues], "count": len(issues)}


@router.post("/convergence/global-reconciliation")
async def trigger_global_reconciliation() -> dict:
    """Trigger global reconciliation for all active drifts."""
    mgr = get_convergence_manager()
    result = mgr.trigger_global_reconciliation()
    return result


# ── V19 — Learning Reconciliation Endpoints ──────────────────────────────

from src.kortana.services.adaptive_planner import get_adaptive_planner  # noqa: E402
from src.kortana.services.improvement_tracker import (  # noqa: E402
    get_improvement_tracker,
)
from src.kortana.services.outcome_tracker import (  # noqa: E402
    OutcomeVerdict,
    get_outcome_tracker,
)
from src.kortana.services.strategy_learner import get_strategy_learner  # noqa: E402

# ── Outcome Tracking ─────────────────────────────────────────────────────


@router.post("/outcomes/record")
async def record_outcome(
    execution_id: str = Body(""),
    plan_id: str = Body(""),
    drift_type: str = Body(""),
    action_types_used: str = Body(""),
    verdict: str = Body("inconclusive"),
    time_to_resolve_sec: float = Body(0.0),
    retries_needed: int = Body(0),
    escalated: bool = Body(False),
    resolution_stable: bool = Body(True),
    learning_applied: bool = Body(False),
) -> dict:
    """Record the outcome of a reconciliation execution."""
    from src.kortana.services.outcome_tracker import ReconciliationOutcome  # noqa: E402

    verdict_enum = OutcomeVerdict(verdict) if verdict in [v.value for v in OutcomeVerdict] else OutcomeVerdict.INCONCLUSIVE
    outcome = ReconciliationOutcome(
        execution_id=execution_id,
        plan_id=plan_id,
        drift_type=drift_type,
        action_types_used=action_types_used.split(",") if action_types_used else [],
        verdict=verdict_enum,
        time_to_resolve_sec=time_to_resolve_sec,
        retries_needed=retries_needed,
        escalated=escalated,
        resolution_stable=resolution_stable,
        learning_applied=learning_applied,
    )
    tracker = get_outcome_tracker()
    tracker.record_outcome(outcome)
    return {"status": "recorded", "outcome_id": outcome.outcome_id}


@router.get("/outcomes")
async def get_outcomes(
    drift_type: str = "",
    verdict: str = "",
    limit: int = 100,
) -> dict:
    """Get recorded reconciliation outcomes."""
    tracker = get_outcome_tracker()
    outcomes = tracker.get_outcomes(limit=limit)
    if drift_type:
        outcomes = [o for o in outcomes if o.drift_type == drift_type]
    if verdict:
        outcomes = [o for o in outcomes if o.verdict.value == verdict]
    return {"outcomes": [o.to_dict() for o in outcomes], "count": len(outcomes)}


@router.get("/outcomes/summary")
async def get_outcomes_summary() -> dict:
    """Get summary of outcome statistics."""
    tracker = get_outcome_tracker()
    return tracker.get_summary()


@router.get("/outcomes/effectiveness-rate")
async def get_effectiveness_rate(drift_type: str = "") -> dict:
    """Get effectiveness rate, optionally by drift type."""
    tracker = get_outcome_tracker()
    if drift_type:
        outcomes = tracker.get_outcomes_for_drift_type(drift_type)
    else:
        outcomes = tracker.get_outcomes()
    effective = sum(
        1 for o in outcomes
        if o.verdict in (OutcomeVerdict.EFFECTIVE, OutcomeVerdict.PARTIALLY_EFFECTIVE)
    )
    rate = effective / len(outcomes) if outcomes else 0.0
    return {"effectiveness_rate": round(rate, 3), "total": len(outcomes), "effective": effective}


@router.get("/outcomes/escalation-rate")
async def get_escalation_rate() -> dict:
    """Get the escalation rate."""
    tracker = get_outcome_tracker()
    return {"escalation_rate": round(tracker.get_escalation_rate(), 3)}


@router.get("/outcomes/stability-rate")
async def get_stability_rate() -> dict:
    """Get the stability rate."""
    tracker = get_outcome_tracker()
    return {"stability_rate": round(tracker.get_stability_rate(), 3)}


# ── Strategy Learning ────────────────────────────────────────────────────


@router.get("/strategy/effectiveness")
async def get_action_effectiveness(drift_type: str = "") -> dict:
    """Get action effectiveness analysis."""
    learner = get_strategy_learner()
    result = learner.get_action_effectiveness(drift_type=drift_type if drift_type else None)
    return {"effectiveness": [r.__dict__ for r in result], "count": len(result)}


@router.get("/strategy/recommendation")
async def get_strategy_recommendation(drift_type: str = "") -> dict:
    """Get strategy recommendation for a drift type."""
    learner = get_strategy_learner()
    rec = learner.recommend_for_drift_type(drift_type)
    return rec.to_dict()


@router.get("/strategy/priority-adjustment")
async def get_priority_adjustment(drift_type: str = "") -> dict:
    """Get recommended priority adjustment for a drift type."""
    learner = get_strategy_learner()
    return learner.get_priority_adjustment(drift_type)


@router.get("/strategy/retry-recommendation")
async def get_retry_recommendation(drift_type: str = "") -> dict:
    """Get retry recommendation for a drift type."""
    learner = get_strategy_learner()
    return learner.get_retry_recommendation(drift_type)


@router.get("/strategy/escalation-timing")
async def get_escalation_timing(drift_type: str = "") -> dict:
    """Get recommended escalation timing for a drift type."""
    learner = get_strategy_learner()
    return learner.get_escalation_timing(drift_type)


# ── Adaptive Planning ────────────────────────────────────────────────────


@router.post("/adaptive/plan")
async def create_adaptive_plan(
    signal_id: str = Body(""),
    drift_type: str = Body("config_drift"),
    severity: str = Body("medium"),
    provider_name: str = Body("default"),
    details: str = Body(""),
) -> dict:
    """Create an adaptive reconciliation plan from a drift signal."""
    from src.kortana.services.drift_detector import (  # noqa: E402
        DriftSeverity,
        DriftSignal,
        DriftType,
    )

    dt = DriftType(drift_type) if drift_type in [d.value for d in DriftType] else DriftType.CONFIG_DRIFT
    sv = DriftSeverity(severity) if severity in [s.value for s in DriftSeverity] else DriftSeverity.MEDIUM
    signal = DriftSignal(
        signal_id=signal_id or None,
        drift_type=dt,
        severity=sv,
        provider_name=provider_name,
        details=details,
    )
    planner = get_adaptive_planner()
    plan = planner.plan_from_drift_adaptive(signal)
    return plan.to_dict()


@router.get("/adaptive/plans")
async def get_adaptive_plans(learning_applied: str = "") -> dict:
    """Get adaptive plans, optionally filtered by learning_applied."""
    planner = get_adaptive_planner()
    if learning_applied == "true":
        plans = planner.get_adaptive_plans(learning_applied=True)
    elif learning_applied == "false":
        plans = planner.get_adaptive_plans(learning_applied=False)
    else:
        plans = planner.get_adaptive_plans()
    return {"plans": [p.to_dict() for p in plans], "count": len(plans)}


@router.get("/adaptive/stats")
async def get_adaptive_stats() -> dict:
    """Get adaptive planning statistics."""
    planner = get_adaptive_planner()
    return planner.get_learning_stats()


# ── Improvement Tracking ─────────────────────────────────────────────────


@router.post("/improvement/report")
async def generate_improvement_report() -> dict:
    """Generate an improvement report comparing default vs learned outcomes."""
    tracker = get_improvement_tracker()
    report = tracker.generate_report()
    return report.to_dict()


@router.get("/improvement/reports")
async def get_improvement_reports() -> dict:
    """Get all improvement reports."""
    tracker = get_improvement_tracker()
    reports = tracker.get_reports()
    return {"reports": [r.to_dict() for r in reports], "count": len(reports)}


@router.get("/improvement/latest")
async def get_latest_improvement_report() -> dict:
    """Get the latest improvement report."""
    tracker = get_improvement_tracker()
    report = tracker.get_latest_report()
    return report.to_dict() if report else {"report": None}


@router.get("/improvement/maturity")
async def get_learning_maturity() -> dict:
    """Get current learning maturity level."""
    tracker = get_improvement_tracker()
    maturity = tracker.get_learning_maturity()
    return {"maturity": maturity.value}


@router.get("/improvement/trend")
async def get_improvement_trend() -> dict:
    """Get improvement trend across reports."""
    tracker = get_improvement_tracker()
    trend = tracker.get_improvement_trend()
    return {"trend": trend, "count": len(trend)}


# ── V20 — Policy-Learning Integration Endpoints ──────────────────────────

from src.kortana.services.autonomy_adjuster import get_autonomy_adjuster  # noqa: E402
from src.kortana.services.governance_evolution import (  # noqa: E402
    get_governance_evolution,
)
from src.kortana.services.policy_feedback_loop import (  # noqa: E402
    get_policy_feedback_loop,
)
from src.kortana.services.trust_calibrator import get_trust_calibrator  # noqa: E402

# ── Trust Calibration ────────────────────────────────────────────────────


@router.post("/trust/calibrate")
async def calibrate_trust() -> dict:
    """Run a trust calibration cycle."""
    calibrator = get_trust_calibrator()
    cal = calibrator.calibrate_trust()
    return cal.to_dict()


@router.get("/trust/current")
async def get_current_trust() -> dict:
    """Get the current trust calibration."""
    calibrator = get_trust_calibrator()
    cal = calibrator.get_current_trust()
    return cal.to_dict()


@router.get("/trust/history")
async def get_trust_history() -> dict:
    """Get trust calibration history."""
    calibrator = get_trust_calibrator()
    history = calibrator.get_trust_history()
    return {"calibrations": [c.to_dict() for c in history], "count": len(history)}


@router.get("/trust/factors")
async def get_trust_factors() -> dict:
    """Get trust factors from the most recent calibration."""
    calibrator = get_trust_calibrator()
    factors = calibrator.get_trust_factors()
    return {"factors": [f.to_dict() for f in factors], "count": len(factors)}


# ── Autonomy Adjustment ─────────────────────────────────────────────────


@router.post("/autonomy/adjust")
async def adjust_autonomy_thresholds() -> dict:
    """Recalculate autonomy thresholds based on current trust."""
    adjuster = get_autonomy_adjuster()
    thresholds = adjuster.adjust_thresholds()
    return {"thresholds": {k: v.to_dict() for k, v in thresholds.items()}, "count": len(thresholds)}


@router.get("/autonomy/thresholds")
async def get_autonomy_thresholds() -> dict:
    """Get current autonomy thresholds."""
    adjuster = get_autonomy_adjuster()
    thresholds = adjuster.get_current_thresholds()
    return {"thresholds": {k: v.to_dict() for k, v in thresholds.items()}, "count": len(thresholds)}


@router.get("/autonomy/threshold/{category}")
async def get_autonomy_threshold_for_category(category: str) -> dict:
    """Get autonomy threshold for a specific category."""
    adjuster = get_autonomy_adjuster()
    threshold = adjuster.get_threshold_for_category(category)
    return threshold.to_dict() if threshold else {"error": "category not found"}


@router.get("/autonomy/should-auto")
async def should_auto_execute(
    category: str = "",
    confidence: float = 0.0,
) -> dict:
    """Check if an action should auto-execute."""
    adjuster = get_autonomy_adjuster()
    return {
        "should_auto": adjuster.should_auto_execute(category, confidence),
        "execution_mode": adjuster.get_execution_mode(category, confidence),
        "category": category,
        "confidence": confidence,
    }


@router.get("/autonomy/history")
async def get_autonomy_adjustment_history() -> dict:
    """Get autonomy adjustment history."""
    adjuster = get_autonomy_adjuster()
    history = adjuster.get_adjustment_history()
    return {"history": history, "count": len(history)}


# ── Policy Feedback ──────────────────────────────────────────────────────


@router.post("/policy/amendments/generate")
async def generate_policy_amendments() -> dict:
    """Generate policy amendments from performance data."""
    loop = get_policy_feedback_loop()
    amendments = loop.generate_amendments()
    return {"amendments": [a.to_dict() for a in amendments], "count": len(amendments)}


@router.get("/policy/amendments")
async def get_policy_amendments(status: str = "") -> dict:
    """Get policy amendments, optionally filtered by status."""
    from src.kortana.services.policy_feedback_loop import AmendmentStatus  # noqa: E402
    loop = get_policy_feedback_loop()
    if status and status in [s.value for s in AmendmentStatus]:
        amendments = loop.get_amendments(status=AmendmentStatus(status))
    else:
        amendments = loop.get_amendments()
    return {"amendments": [a.to_dict() for a in amendments], "count": len(amendments)}


@router.get("/policy/amendments/pending")
async def get_pending_amendments() -> dict:
    """Get pending policy amendments."""
    loop = get_policy_feedback_loop()
    pending = loop.get_pending_amendments()
    return {"amendments": [a.to_dict() for a in pending], "count": len(pending)}


@router.post("/policy/amendments/{amendment_id}/apply")
async def apply_policy_amendment(amendment_id: str) -> dict:
    """Apply a pending policy amendment."""
    loop = get_policy_feedback_loop()
    success = loop.apply_amendment(amendment_id)
    return {"applied": success, "amendment_id": amendment_id}


@router.post("/policy/amendments/{amendment_id}/reject")
async def reject_policy_amendment(amendment_id: str) -> dict:
    """Reject a pending policy amendment."""
    loop = get_policy_feedback_loop()
    success = loop.reject_amendment(amendment_id)
    return {"rejected": success, "amendment_id": amendment_id}


# ── Governance Evolution ─────────────────────────────────────────────────


@router.post("/governance/evolve")
async def evolve_governance() -> dict:
    """Run one governance evolution cycle."""
    gov = get_governance_evolution()
    snapshot = gov.evolve()
    return snapshot.to_dict()


@router.get("/governance/snapshot")
async def get_governance_snapshot() -> dict:
    """Get current governance snapshot."""
    gov = get_governance_evolution()
    snapshot = gov.get_current_snapshot()
    return snapshot.to_dict() if snapshot else {"snapshot": None}


@router.get("/governance/history")
async def get_governance_history() -> dict:
    """Get governance evolution history."""
    gov = get_governance_evolution()
    history = gov.get_evolution_history()
    return {"snapshots": [s.to_dict() for s in history], "count": len(history)}


@router.get("/governance/stage")
async def get_governance_stage() -> dict:
    """Get current governance evolution stage."""
    gov = get_governance_evolution()
    return {"stage": gov.get_evolution_stage().value}


@router.get("/governance/summary")
async def get_governance_summary() -> dict:
    """Get governance summary."""
    gov = get_governance_evolution()
    return gov.get_governance_summary()


# ── V21: Institutional Learning Controls ──

from src.kortana.services.approval_gate import (  # noqa: E402
    ApprovalPolicy,
    get_approval_gate,
)
from src.kortana.services.evolution_observer import (  # noqa: E402
    EventType,
    get_evolution_observer,
)
from src.kortana.services.policy_feedback_loop import PolicyArea  # noqa: E402
from src.kortana.services.policy_rollback import get_policy_rollback  # noqa: E402
from src.kortana.services.proposal_registry import (  # noqa: E402
    ProposalStatus,
    get_proposal_registry,
)
from src.kortana.services.trust_calibrator import TrustLevel  # noqa: E402

# ── V21A: Proposal Registry Endpoints ──


@router.post("/proposals/create")
async def create_proposal_from_amendment(amendment_id: str = Body(...)) -> dict:
    """Create a proposal from a pending V20 amendment."""
    from src.kortana.services.policy_feedback_loop import get_policy_feedback_loop

    feedback = get_policy_feedback_loop()
    amendments = feedback.get_amendments()
    amendment = next((a for a in amendments if a.amendment_id == amendment_id), None)
    if amendment is None:
        return {"error": "amendment not found"}

    registry = get_proposal_registry()
    proposal = registry.create_proposal(amendment)

    observer = get_evolution_observer()
    observer.emit(EventType.PROPOSAL_CREATED, proposal.proposal_id, {"amendment_id": amendment_id})
    return proposal.to_dict()


@router.post("/proposals/create-direct")
async def create_proposal_direct(
    policy_area: str = Body(...),
    current_rule: str = Body(...),
    proposed_rule: str = Body(...),
    justification: str = Body(...),
    confidence: float = Body(0.5),
    evidence_count: int = Body(0),
) -> dict:
    """Create a proposal directly without an existing amendment."""
    try:
        area = PolicyArea(policy_area)
    except ValueError:
        return {"error": f"invalid policy_area: {policy_area}"}

    registry = get_proposal_registry()
    proposal = registry.create_proposal_direct(
        policy_area=area,
        current_rule=current_rule,
        proposed_rule=proposed_rule,
        justification=justification,
        confidence=confidence,
        evidence_count=evidence_count,
    )

    observer = get_evolution_observer()
    observer.emit(EventType.PROPOSAL_CREATED, proposal.proposal_id, {"source": "direct"})
    return proposal.to_dict()


@router.post("/proposals/{proposal_id}/submit")
async def submit_proposal(proposal_id: str) -> dict:
    """Submit a draft proposal for review."""
    registry = get_proposal_registry()
    ok = registry.submit_proposal(proposal_id)
    if ok:
        observer = get_evolution_observer()
        observer.emit(EventType.PROPOSAL_SUBMITTED, proposal_id)
    return {"success": ok, "proposal_id": proposal_id}


@router.post("/proposals/{proposal_id}/review")
async def begin_proposal_review(proposal_id: str) -> dict:
    """Begin review of a submitted proposal."""
    registry = get_proposal_registry()
    ok = registry.begin_review(proposal_id)
    if ok:
        observer = get_evolution_observer()
        observer.emit(EventType.REVIEW_STARTED, proposal_id)
    return {"success": ok, "proposal_id": proposal_id}


@router.post("/proposals/{proposal_id}/promote")
async def promote_proposal(proposal_id: str) -> dict:
    """Promote an approved proposal (applies the policy change)."""
    registry = get_proposal_registry()
    proposal = registry.get_proposal(proposal_id)
    if proposal is None:
        return {"error": "proposal not found"}

    # Create rollback point before promotion
    rollback = get_policy_rollback()
    prior_state = {"rule": proposal.current_rule, "area": proposal.policy_area.value}
    applied_state = {"rule": proposal.proposed_rule, "area": proposal.policy_area.value}
    point = rollback.create_point(proposal_id, prior_state, applied_state)

    ok = registry.promote(proposal_id)
    if ok:
        observer = get_evolution_observer()
        observer.emit(EventType.PROPOSAL_PROMOTED, proposal_id, {"rollback_point": point.point_id})
        observer.emit(EventType.ROLLBACK_CREATED, point.point_id, {"proposal_id": proposal_id})
    return {"success": ok, "proposal_id": proposal_id, "rollback_point_id": point.point_id}


@router.post("/proposals/{proposal_id}/withdraw")
async def withdraw_proposal(proposal_id: str) -> dict:
    """Withdraw a proposal."""
    registry = get_proposal_registry()
    ok = registry.withdraw(proposal_id)
    if ok:
        observer = get_evolution_observer()
        observer.emit(EventType.PROPOSAL_WITHDRAWN, proposal_id)
    return {"success": ok, "proposal_id": proposal_id}


@router.get("/proposals")
async def list_proposals(status: str | None = None) -> dict:
    """List all proposals, optionally filtered by status."""
    registry = get_proposal_registry()
    if status:
        try:
            s = ProposalStatus(status)
        except ValueError:
            return {"error": f"invalid status: {status}"}
        proposals = registry.list_proposals(s)
    else:
        proposals = registry.list_proposals()
    return {"proposals": [p.to_dict() for p in proposals], "count": len(proposals)}


@router.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str) -> dict:
    """Get a specific proposal by ID."""
    registry = get_proposal_registry()
    proposal = registry.get_proposal(proposal_id)
    if proposal is None:
        return {"error": "proposal not found"}
    return proposal.to_dict()


@router.get("/proposals/history/all")
async def get_proposal_history() -> dict:
    """Get full proposal lifecycle history."""
    registry = get_proposal_registry()
    return {"history": registry.get_history(), "total_proposals": registry.proposal_count}


# ── V21B: Approval Gate Endpoints ──


@router.post("/approval/evaluate/{proposal_id}")
async def evaluate_proposal(proposal_id: str) -> dict:
    """Evaluate a proposal against the approval policy."""
    registry = get_proposal_registry()
    proposal = registry.get_proposal(proposal_id)
    if proposal is None:
        return {"error": "proposal not found"}

    from src.kortana.services.trust_calibrator import get_trust_calibrator

    calibrator = get_trust_calibrator()
    trust = calibrator.get_current_trust()
    trust_level = trust.trust_level if trust else TrustLevel.UNTRUSTED

    gate = get_approval_gate()
    decision = gate.evaluate(proposal, trust_level)

    observer = get_evolution_observer()
    evt = EventType.APPROVAL_AUTO if decision.decision_type.value == "auto" else EventType.APPROVAL_HUMAN
    observer.emit(evt, proposal_id, {"approved": decision.approved, "decided_by": decision.decided_by})

    return decision.to_dict()


@router.post("/approval/approve/{proposal_id}")
async def approve_proposal_manual(
    proposal_id: str,
    decided_by: str = Body("human"),
    reason: str = Body("manually approved"),
    conditions: str = Body(""),
) -> dict:
    """Manually approve a proposal and move it to APPROVED status."""
    registry = get_proposal_registry()
    ok = registry.mark_approved(proposal_id, reviewer=decided_by, notes=reason)
    if not ok:
        return {"error": "cannot approve proposal in current state"}

    gate = get_approval_gate()
    decision = gate.approve_manual(proposal_id, decided_by=decided_by, reason=reason, conditions=conditions)

    observer = get_evolution_observer()
    observer.emit(EventType.APPROVAL_HUMAN, proposal_id, {"approved": True, "decided_by": decided_by})
    observer.emit(EventType.PROPOSAL_APPROVED, proposal_id, {"reviewer": decided_by})

    return decision.to_dict()


@router.post("/approval/reject/{proposal_id}")
async def reject_proposal_manual(
    proposal_id: str,
    decided_by: str = Body("human"),
    reason: str = Body("manually rejected"),
) -> dict:
    """Manually reject a proposal."""
    registry = get_proposal_registry()
    ok = registry.mark_rejected(proposal_id, reviewer=decided_by, notes=reason)
    if not ok:
        return {"error": "cannot reject proposal in current state"}

    gate = get_approval_gate()
    decision = gate.reject_manual(proposal_id, decided_by=decided_by, reason=reason)

    observer = get_evolution_observer()
    observer.emit(EventType.APPROVAL_HUMAN, proposal_id, {"approved": False, "decided_by": decided_by})
    observer.emit(EventType.PROPOSAL_REJECTED, proposal_id, {"reviewer": decided_by})

    return decision.to_dict()


@router.get("/approval/policy")
async def get_approval_policy() -> dict:
    """Get the current approval policy."""
    gate = get_approval_gate()
    return gate.get_policy().to_dict()


@router.post("/approval/policy")
async def set_approval_policy(
    min_confidence: float = Body(0.75),
    min_trust_level: str = Body("high_trust"),
    require_human_below_confidence: float = Body(0.50),
    max_auto_approve_per_cycle: int = Body(5),
) -> dict:
    """Update the approval policy."""
    from src.kortana.services.trust_calibrator import TrustLevel as TL

    try:
        tl = TL(min_trust_level)
    except ValueError:
        return {"error": f"invalid trust level: {min_trust_level}"}

    gate = get_approval_gate()
    policy = ApprovalPolicy(
        min_confidence=min_confidence,
        min_trust_level=tl,
        require_human_below_confidence=require_human_below_confidence,
        max_auto_approve_per_cycle=max_auto_approve_per_cycle,
    )
    gate.set_policy(policy)
    return policy.to_dict()


@router.get("/approval/decisions")
async def get_approval_decisions(proposal_id: str | None = None) -> dict:
    """Get approval decisions, optionally filtered by proposal."""
    gate = get_approval_gate()
    decisions = gate.get_decisions(proposal_id)
    return {"decisions": [d.to_dict() for d in decisions], "count": len(decisions)}


# ── V21C: Policy Rollback Endpoints ──


@router.post("/rollback/{point_id}")
async def execute_rollback(point_id: str, reason: str = Body("")) -> dict:
    """Execute a rollback to restore prior policy state."""
    rollback = get_policy_rollback()
    point = rollback.rollback(point_id, reason=reason)
    if point is None:
        return {"error": "rollback point not found or already rolled back"}

    observer = get_evolution_observer()
    observer.emit(EventType.ROLLBACK_EXECUTED, point_id, {
        "proposal_id": point.proposal_id,
        "reason": reason,
    })
    return point.to_dict()


@router.get("/rollback/points")
async def get_rollback_points() -> dict:
    """Get all rollback points."""
    rollback = get_policy_rollback()
    points = [p.to_dict() for p in rollback.get_active_points()]
    return {"points": points, "active_count": rollback.active_count, "total_count": rollback.point_count}


@router.get("/rollback/{point_id}")
async def get_rollback_point(point_id: str) -> dict:
    """Get a specific rollback point."""
    rollback = get_policy_rollback()
    point = rollback.get_point(point_id)
    if point is None:
        return {"error": "rollback point not found"}
    return point.to_dict()


@router.get("/rollback/can/{point_id}")
async def can_rollback(point_id: str) -> dict:
    """Check if a rollback point can be rolled back."""
    rollback = get_policy_rollback()
    return {"can_rollback": rollback.can_rollback(point_id), "point_id": point_id}


@router.get("/rollback/proposal/{proposal_id}")
async def get_rollback_for_proposal(proposal_id: str) -> dict:
    """Get rollback point for a specific proposal."""
    rollback = get_policy_rollback()
    point = rollback.get_point_for_proposal(proposal_id)
    if point is None:
        return {"error": "no rollback point for this proposal"}
    return point.to_dict()


@router.get("/rollback/history/all")
async def get_rollback_history() -> dict:
    """Get full rollback history."""
    rollback = get_policy_rollback()
    return {"history": rollback.get_history(), "total_points": rollback.point_count}


# ── V21D: Evolution Observer Endpoints ──


@router.get("/evolution/timeline")
async def get_evolution_timeline(limit: int = 0) -> dict:
    """Get the evolution event timeline."""
    observer = get_evolution_observer()
    events = observer.get_timeline(limit)
    return {"events": [e.to_dict() for e in events], "count": len(events)}


@router.get("/evolution/events/{event_type}")
async def get_events_by_type(event_type: str) -> dict:
    """Get events filtered by type."""
    try:
        et = EventType(event_type)
    except ValueError:
        return {"error": f"invalid event type: {event_type}"}
    observer = get_evolution_observer()
    events = observer.get_events_by_type(et)
    return {"events": [e.to_dict() for e in events], "count": len(events)}


@router.get("/evolution/subject/{subject_id}")
async def get_events_for_subject(subject_id: str) -> dict:
    """Get all events for a specific subject (proposal or rollback point)."""
    observer = get_evolution_observer()
    events = observer.get_events_for_subject(subject_id)
    return {"events": [e.to_dict() for e in events], "count": len(events)}


@router.get("/evolution/audit")
async def get_evolution_audit() -> dict:
    """Get the evolution audit trail summary."""
    observer = get_evolution_observer()
    return observer.get_audit_trail()


@router.get("/evolution/stats")
async def get_evolution_stats() -> dict:
    """Get evolution statistics across all V21 components."""
    registry = get_proposal_registry()
    gate = get_approval_gate()
    rollback = get_policy_rollback()
    observer = get_evolution_observer()

    return {
        "proposals": {
            "total": registry.proposal_count,
            "by_status": {
                s.value: len(registry.list_proposals(s))
                for s in ProposalStatus
            },
        },
        "approvals": {
            "total_decisions": gate.decision_count,
            "auto_approves_this_cycle": gate.get_auto_approve_count(),
        },
        "rollback": {
            "total_points": rollback.point_count,
            "active_points": rollback.active_count,
        },
        "evolution": {
            "total_events": observer.event_count,
            "subscribers": observer.subscriber_count,
        },
    }


# ── V22: Constitutional Governance ──

from src.kortana.services.boundary_enforcer import get_boundary_enforcer  # noqa: E402
from src.kortana.services.constitution import (  # noqa: E402
    Sensitivity,
    ViolationSeverity,
    get_constitution,
)
from src.kortana.services.constitutional_audit import (  # noqa: E402
    get_constitutional_audit,
)
from src.kortana.services.quorum_policy import get_quorum_policy  # noqa: E402

# ── V22A: Constitution Endpoints ──


@router.get("/constitution/articles")
async def get_constitution_articles() -> dict:
    """Get all constitutional articles."""
    const = get_constitution()
    return {"articles": [a.to_dict() for a in const.get_articles()], "count": const.article_count}


@router.get("/constitution/articles/{article_id}")
async def get_constitution_article(article_id: str) -> dict:
    """Get a specific constitutional article."""
    const = get_constitution()
    article = const.get_article(article_id)
    if article is None:
        return {"error": "article not found"}
    return article.to_dict()


@router.get("/constitution/classification/{policy_area}")
async def get_area_classification(policy_area: str) -> dict:
    """Get the constitutional classification for a policy area."""
    from src.kortana.services.policy_feedback_loop import PolicyArea as PA

    try:
        area = PA(policy_area)
    except ValueError:
        return {"error": f"invalid policy area: {policy_area}"}

    const = get_constitution()
    classification = const.get_classification(area)
    sensitivity = const.get_sensitivity(area)
    return {
        "policy_area": policy_area,
        "classification": classification.value,
        "sensitivity": sensitivity.value,
        "is_immutable": const.is_immutable(area),
        "is_restricted": const.is_restricted(area),
        "is_amendable": const.is_amendable(area),
    }


@router.get("/constitution/summary")
async def get_constitution_summary() -> dict:
    """Get a summary of the constitution."""
    const = get_constitution()
    return const.get_summary()


# ── V22B: Quorum Policy Endpoints ──


@router.post("/quorum/vote")
async def cast_quorum_vote(
    proposal_id: str = Body(...),
    voter: str = Body(...),
    approved: bool = Body(...),
    identity_verified: bool = Body(False),
) -> dict:
    """Cast a vote on a proposal."""
    qp = get_quorum_policy()
    vote = qp.cast_vote(proposal_id, voter, approved, identity_verified)
    return vote.to_dict()


@router.post("/quorum/check")
async def check_quorum(
    proposal_id: str = Body(...),
    sensitivity: str = Body(...),
) -> dict:
    """Check whether quorum is met for a proposal."""
    try:
        sens = Sensitivity(sensitivity)
    except ValueError:
        return {"error": f"invalid sensitivity: {sensitivity}"}

    qp = get_quorum_policy()
    result = qp.check_quorum(proposal_id, sens)
    return result.to_dict()


@router.get("/quorum/requirement/{sensitivity}")
async def get_quorum_requirement(sensitivity: str) -> dict:
    """Get the quorum requirement for a sensitivity level."""
    try:
        sens = Sensitivity(sensitivity)
    except ValueError:
        return {"error": f"invalid sensitivity: {sensitivity}"}

    qp = get_quorum_policy()
    req = qp.get_requirement(sens)
    return req.to_dict()


@router.get("/quorum/votes/{proposal_id}")
async def get_quorum_votes(proposal_id: str) -> dict:
    """Get all votes for a proposal."""
    qp = get_quorum_policy()
    votes = qp.get_votes(proposal_id)
    return {"votes": [v.to_dict() for v in votes], "count": len(votes)}


@router.get("/quorum/results")
async def get_quorum_results() -> dict:
    """Get all quorum check results."""
    qp = get_quorum_policy()
    results = qp.get_results()
    return {"results": [r.to_dict() for r in results], "count": len(results)}


# ── V22C: Boundary Enforcer Endpoints ──


@router.post("/boundary/check/{proposal_id}")
async def check_proposal_boundary(proposal_id: str) -> dict:
    """Check a proposal against constitutional boundaries."""
    from src.kortana.services.proposal_registry import get_proposal_registry

    registry = get_proposal_registry()
    proposal = registry.get_proposal(proposal_id)
    if proposal is None:
        return {"error": "proposal not found"}

    enforcer = get_boundary_enforcer()
    check = enforcer.check_proposal(proposal)

    # Record in audit
    audit = get_constitutional_audit()
    proof = audit.record_check(check)

    # Emit observer event
    from src.kortana.services.evolution_observer import EventType, get_evolution_observer

    observer = get_evolution_observer()
    observer.emit(
        EventType.POLICY_APPLIED if check.passed else EventType.PROPOSAL_REJECTED,
        proposal_id,
        {"boundary_check": check.check_id, "passed": check.passed, "violations": len(check.violations)},
    )

    return {
        "check": check.to_dict(),
        "compliance_proof": proof.to_dict(),
    }


@router.post("/boundary/validate-batch")
async def validate_evolution_batch(proposal_ids: list[str] = Body(...)) -> dict:
    """Validate multiple proposals against constitutional boundaries."""
    from src.kortana.services.proposal_registry import get_proposal_registry

    registry = get_proposal_registry()
    proposals = []
    for pid in proposal_ids:
        p = registry.get_proposal(pid)
        if p is not None:
            proposals.append(p)

    enforcer = get_boundary_enforcer()
    return enforcer.validate_evolution_batch(proposals)


@router.get("/boundary/checks")
async def get_boundary_checks(proposal_id: str | None = None) -> dict:
    """Get boundary check results."""
    enforcer = get_boundary_enforcer()
    checks = enforcer.get_checks(proposal_id)
    return {"checks": [c.to_dict() for c in checks], "count": len(checks)}


@router.get("/boundary/violations")
async def get_violation_summary() -> dict:
    """Get a summary of all boundary violations."""
    enforcer = get_boundary_enforcer()
    return enforcer.get_violation_summary()


# ── V22D: Constitutional Audit Endpoints ──


@router.get("/constitutional-audit/proofs")
async def get_compliance_proofs(proposal_id: str | None = None) -> dict:
    """Get compliance proofs."""
    audit = get_constitutional_audit()
    proofs = audit.get_proofs(proposal_id)
    return {"proofs": [p.to_dict() for p in proofs], "count": len(proofs)}


@router.get("/constitutional-audit/violations")
async def get_audit_violations(
    proposal_id: str | None = None,
    severity: str | None = None,
    unresolved_only: bool = False,
) -> dict:
    """Get violation records."""
    audit = get_constitutional_audit()
    sev = None
    if severity:
        try:
            sev = ViolationSeverity(severity)
        except ValueError:
            return {"error": f"invalid severity: {severity}"}

    violations = audit.get_violations(proposal_id, sev, unresolved_only)
    return {"violations": [v.to_dict() for v in violations], "count": len(violations)}


@router.post("/constitutional-audit/resolve/{violation_id}")
async def resolve_violation(
    violation_id: str,
    notes: str = Body(""),
) -> dict:
    """Resolve a constitutional violation."""
    audit = get_constitutional_audit()
    ok = audit.resolve_violation(violation_id, notes)
    return {"success": ok, "violation_id": violation_id}


@router.get("/constitutional-audit/report")
async def get_compliance_report() -> dict:
    """Get comprehensive constitutional compliance report."""
    audit = get_constitutional_audit()
    return audit.get_compliance_report()


@router.get("/constitutional-audit/stats")
async def get_constitutional_stats() -> dict:
    """Get statistics across all V22 components."""
    const = get_constitution()
    qp = get_quorum_policy()
    enforcer = get_boundary_enforcer()
    audit = get_constitutional_audit()

    return {
        "constitution": const.get_summary(),
        "quorum": {
            "total_votes": qp.total_votes,
            "total_results": qp.result_count,
        },
        "boundary": enforcer.get_violation_summary(),
        "compliance": audit.get_compliance_report(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# V23 — Constitutional Adjudication Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

from src.kortana.services.appeals import (  # noqa: E402
    AppealGrounds,
    AppealStatus,
    get_appeals_court,
)
from src.kortana.services.emergency_powers import (  # noqa: E402
    EmergencyScope,
    get_emergency_powers,
)
from src.kortana.services.exception_handler import (  # noqa: E402
    WaiverScope,
    get_exception_handler,
)
from src.kortana.services.precedent_tracker import (  # noqa: E402
    DecisionType,
    PrecedentStrength,
    get_precedent_tracker,
)

# ─── Exception Handler (Waivers) ─────────────────────────────────────────────


@router.post("/waivers/request")
async def request_waiver(
    article_id: str = Body(...),
    proposal_id: str = Body(...),
    reason: str = Body(...),
    requested_by: str = Body(...),
    scope: str = Body("single_proposal"),
    duration_hours: int = Body(4),
) -> dict:
    """Request a constitutional waiver for a specific article."""
    handler = get_exception_handler()
    waiver = handler.request_waiver(
        article_id=article_id,
        proposal_id=proposal_id,
        reason=reason,
        requested_by=requested_by,
        scope=WaiverScope(scope),
        duration_hours=duration_hours,
    )
    return waiver.to_dict()


@router.post("/waivers/{waiver_id}/grant")
async def grant_waiver(waiver_id: str) -> dict:
    """Grant a requested waiver — starts expiration clock."""
    handler = get_exception_handler()
    ok = handler.grant_waiver(waiver_id)
    return {"success": ok, "waiver_id": waiver_id}


@router.post("/waivers/{waiver_id}/deny")
async def deny_waiver(waiver_id: str, reason: str = Body("")) -> dict:
    """Deny a waiver request."""
    handler = get_exception_handler()
    ok = handler.deny_waiver(waiver_id, reason)
    return {"success": ok, "waiver_id": waiver_id}


@router.post("/waivers/{waiver_id}/revoke")
async def revoke_waiver(waiver_id: str) -> dict:
    """Revoke an active waiver immediately."""
    handler = get_exception_handler()
    ok = handler.revoke_waiver(waiver_id)
    return {"success": ok, "waiver_id": waiver_id}


@router.get("/waivers")
async def list_waivers(
    article_id: str | None = None,
    active_only: bool = False,
) -> dict:
    """List waivers with optional filters."""
    handler = get_exception_handler()
    waivers = handler.get_waivers(article_id=article_id, active_only=active_only)
    return {"waivers": [w.to_dict() for w in waivers], "count": len(waivers)}


@router.get("/waivers/{waiver_id}")
async def get_waiver_detail(waiver_id: str) -> dict:
    """Get details of a specific waiver."""
    handler = get_exception_handler()
    w = handler.get_waiver(waiver_id)
    if w is None:
        return {"error": "not found", "waiver_id": waiver_id}
    return w.to_dict()


@router.get("/waivers/summary/stats")
async def get_waiver_summary() -> dict:
    """Get waiver statistics."""
    handler = get_exception_handler()
    return handler.get_summary()


@router.post("/waivers/expire")
async def expire_waivers() -> dict:
    """Expire all waivers past their expiration time."""
    handler = get_exception_handler()
    count = handler.expire_waivers()
    return {"expired_count": count}


# ─── Appeals Court ────────────────────────────────────────────────────────────


@router.post("/appeals/file")
async def file_appeal(
    proposal_id: str = Body(...),
    original_check_id: str = Body(...),
    original_policy_area: str = Body(...),
    original_sensitivity: str = Body("standard"),
    appellant: str = Body(...),
    grounds: str = Body(...),
    argument: str = Body(...),
) -> dict:
    """File an appeal against a boundary check decision."""
    court = get_appeals_court()
    # Build a minimal BoundaryCheck for filing
    from src.kortana.services.boundary_enforcer import BoundaryCheck  # noqa: E402
    check = BoundaryCheck(
        check_id=original_check_id,
        proposal_id=proposal_id,
        passed=False,
        violations=[],
        warnings=[],
        articles_checked=0,
        policy_area=original_policy_area,
        classification="immutable",
        sensitivity=original_sensitivity,
    )
    appeal = court.file_appeal(
        proposal_id=proposal_id,
        original_check=check,
        appellant=appellant,
        grounds=AppealGrounds(grounds),
        argument=argument,
    )
    return appeal.to_dict()


@router.post("/appeals/{appeal_id}/review")
async def begin_appeal_review(appeal_id: str) -> dict:
    """Move an appeal into review."""
    court = get_appeals_court()
    ok = court.begin_review(appeal_id)
    return {"success": ok, "appeal_id": appeal_id}


@router.post("/appeals/{appeal_id}/decide")
async def decide_appeal(
    appeal_id: str,
    decided_by: str = Body(...),
    outcome: str = Body(...),
    reasoning: str = Body(...),
    conditions: list[str] = Body(default=[]),
) -> dict:
    """Issue a decision on an appeal."""
    court = get_appeals_court()
    ok = court.decide(
        appeal_id=appeal_id,
        decided_by=decided_by,
        outcome=AppealStatus(outcome),
        reasoning=reasoning,
        conditions=conditions,
    )
    return {"success": ok, "appeal_id": appeal_id}


@router.post("/appeals/{appeal_id}/withdraw")
async def withdraw_appeal(appeal_id: str) -> dict:
    """Withdraw a filed appeal."""
    court = get_appeals_court()
    ok = court.withdraw(appeal_id)
    return {"success": ok, "appeal_id": appeal_id}


@router.get("/appeals")
async def list_appeals(
    proposal_id: str | None = None,
    status: str | None = None,
    appellant: str | None = None,
) -> dict:
    """List appeals with optional filters."""
    court = get_appeals_court()
    st = AppealStatus(status) if status else None
    appeals = court.get_appeals(proposal_id=proposal_id, status=st, appellant=appellant)
    return {"appeals": [a.to_dict() for a in appeals], "count": len(appeals)}


@router.get("/appeals/{appeal_id}")
async def get_appeal_detail(appeal_id: str) -> dict:
    """Get details of a specific appeal."""
    court = get_appeals_court()
    a = court.get_appeal(appeal_id)
    if a is None:
        return {"error": "not found", "appeal_id": appeal_id}
    return a.to_dict()


@router.get("/appeals/summary/stats")
async def get_appeals_summary() -> dict:
    """Get appeals statistics."""
    court = get_appeals_court()
    return court.get_summary()


# ─── Emergency Powers ────────────────────────────────────────────────────────


@router.post("/emergency/declare")
async def declare_emergency(
    declared_by: str = Body(...),
    reason: str = Body(...),
    affected_areas: list[str] = Body(...),
    scope: str = Body("single_area"),
    duration_hours: int = Body(4),
) -> dict:
    """Declare an emergency with temporary powers."""
    mgr = get_emergency_powers()
    areas = [PolicyArea(a) for a in affected_areas]
    declaration = mgr.declare_emergency(
        declared_by=declared_by,
        reason=reason,
        affected_areas=areas,
        scope=EmergencyScope(scope),
        duration_hours=duration_hours,
    )
    return declaration.to_dict()


@router.post("/emergency/{declaration_id}/activate")
async def activate_emergency(declaration_id: str) -> dict:
    """Activate a declared emergency — starts expiration clock."""
    mgr = get_emergency_powers()
    ok = mgr.activate(declaration_id)
    return {"success": ok, "declaration_id": declaration_id}


@router.post("/emergency/{declaration_id}/revoke")
async def revoke_emergency(declaration_id: str) -> dict:
    """Revoke an active emergency immediately."""
    mgr = get_emergency_powers()
    ok = mgr.revoke(declaration_id)
    return {"success": ok, "declaration_id": declaration_id}


@router.post("/emergency/{declaration_id}/review")
async def submit_emergency_review(
    declaration_id: str,
    reviewer: str = Body(...),
    actions_taken: list[str] = Body(...),
    justified: bool = Body(...),
    findings: str = Body(...),
    recommendations: list[str] = Body(default=[]),
) -> dict:
    """Submit a mandatory post-emergency review."""
    mgr = get_emergency_powers()
    ok = mgr.submit_review(
        declaration_id=declaration_id,
        reviewer=reviewer,
        actions_taken=actions_taken,
        justified=justified,
        findings=findings,
        recommendations=recommendations,
    )
    return {"success": ok, "declaration_id": declaration_id}


@router.get("/emergency")
async def list_emergencies(
    active_only: bool = False,
    needs_review: bool = False,
) -> dict:
    """List emergency declarations."""
    mgr = get_emergency_powers()
    declarations = mgr.get_declarations(active_only=active_only, needs_review=needs_review)
    return {"declarations": [d.to_dict() for d in declarations], "count": len(declarations)}


@router.get("/emergency/{declaration_id}")
async def get_emergency_detail(declaration_id: str) -> dict:
    """Get details of a specific emergency declaration."""
    mgr = get_emergency_powers()
    d = mgr.get_declaration(declaration_id)
    if d is None:
        return {"error": "not found", "declaration_id": declaration_id}
    return d.to_dict()


@router.get("/emergency/summary/stats")
async def get_emergency_summary() -> dict:
    """Get emergency powers statistics."""
    mgr = get_emergency_powers()
    return mgr.get_summary()


@router.post("/emergency/expire")
async def expire_emergencies() -> dict:
    """Expire all emergencies past their expiration time."""
    mgr = get_emergency_powers()
    count = mgr.expire_declarations()
    return {"expired_count": count}


# ─── Precedent Tracker ────────────────────────────────────────────────────────


@router.post("/precedents/record")
async def record_precedent(
    decision_type: str = Body(...),
    reference_id: str = Body(...),
    policy_area: str = Body(...),
    decision_summary: str = Body(...),
    reasoning: str = Body(...),
    outcome: str = Body(...),
    strength: str = Body("persuasive"),
    tags: list[str] = Body(default=[]),
) -> dict:
    """Record a new adjudication precedent."""
    tracker = get_precedent_tracker()
    precedent = tracker.record_precedent(
        decision_type=DecisionType(decision_type),
        reference_id=reference_id,
        policy_area=PolicyArea(policy_area),
        decision_summary=decision_summary,
        reasoning=reasoning,
        outcome=outcome,
        strength=PrecedentStrength(strength),
        tags=tags,
    )
    return precedent.to_dict()


@router.post("/precedents/{old_id}/supersede")
async def supersede_precedent(old_id: str, new_id: str = Body(...)) -> dict:
    """Mark a precedent as superseded by a newer one."""
    tracker = get_precedent_tracker()
    ok = tracker.supersede(old_id, new_id)
    return {"success": ok, "old_id": old_id, "new_id": new_id}


@router.get("/precedents")
async def list_precedents(
    policy_area: str | None = None,
    decision_type: str | None = None,
    strength: str | None = None,
    active_only: bool = True,
) -> dict:
    """Search precedents with optional filters."""
    tracker = get_precedent_tracker()
    area = PolicyArea(policy_area) if policy_area else None
    dt = DecisionType(decision_type) if decision_type else None
    st = PrecedentStrength(strength) if strength else None
    precedents = tracker.find_precedents(policy_area=area, decision_type=dt, strength=st, active_only=active_only)
    return {"precedents": [p.to_dict() for p in precedents], "count": len(precedents)}


@router.get("/precedents/{precedent_id}")
async def get_precedent_detail(precedent_id: str) -> dict:
    """Get details of a specific precedent."""
    tracker = get_precedent_tracker()
    p = tracker.get_precedent(precedent_id)
    if p is None:
        return {"error": "not found", "precedent_id": precedent_id}
    return p.to_dict()


@router.get("/precedents/binding/{policy_area}")
async def get_binding_precedents(policy_area: str) -> dict:
    """Get binding precedents for a policy area."""
    tracker = get_precedent_tracker()
    binding = tracker.get_binding_precedents(PolicyArea(policy_area))
    return {"binding": [p.to_dict() for p in binding], "count": len(binding)}


@router.post("/precedents/check-conflicts")
async def check_precedent_conflicts(
    policy_area: str = Body(...),
    proposed_outcome: str = Body(...),
) -> dict:
    """Check if a proposed outcome conflicts with binding precedents."""
    tracker = get_precedent_tracker()
    conflicts = tracker.check_conflicts(PolicyArea(policy_area), proposed_outcome)
    return {
        "has_conflicts": len(conflicts) > 0,
        "conflicts": [p.to_dict() for p in conflicts],
        "count": len(conflicts),
    }


@router.get("/precedents/summary/stats")
async def get_precedent_summary() -> dict:
    """Get precedent tracker statistics."""
    tracker = get_precedent_tracker()
    return tracker.get_summary()


# ─── V23 Cross-Component Stats ───────────────────────────────────────────────


@router.get("/adjudication/stats")
async def get_adjudication_stats() -> dict:
    """Get statistics across all V23 constitutional adjudication components."""
    handler = get_exception_handler()
    court = get_appeals_court()
    mgr = get_emergency_powers()
    tracker = get_precedent_tracker()

    return {
        "waivers": handler.get_summary(),
        "appeals": court.get_summary(),
        "emergency_powers": mgr.get_summary(),
        "precedents": tracker.get_summary(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# V24: Constitutional Procedure Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


from src.kortana.services.deadline_clock import (  # noqa: E402
    DeadlineStatus,
    DeadlineType,
    get_deadline_clock,
)
from src.kortana.services.reasoning_templates import (  # noqa: E402
    get_reasoning_registry,
)
from src.kortana.services.recusal_manager import get_recusal_manager  # noqa: E402
from src.kortana.services.standing_rules import (  # noqa: E402
    ActorRole,
    get_standing_rules,
)

# ─── V24A Standing Rules ─────────────────────────────────────────────────────


@router.post("/standing/register")
async def register_actor_standing(
    actor: str = Body(...),
    role: str = Body(...),
) -> dict:
    """Register an actor with a constitutional role."""
    checker = get_standing_rules()
    actor_role = ActorRole(role)
    checker.register_actor(actor, actor_role)
    return {"status": "registered", "actor": actor, "role": role}


@router.get("/standing/check")
async def check_standing(
    actor: str,
    action: str,
    policy_area: str | None = None,
) -> dict:
    """Check if an actor has standing for a procedural action."""
    checker = get_standing_rules()
    result = checker.check_standing(actor, ActionType(action), policy_area)
    return result.to_dict()


@router.get("/standing/rules")
async def list_standing_rules() -> dict:
    """List all standing rules."""
    checker = get_standing_rules()
    rules = []
    for role in ActorRole:
        rule = checker.get_rule(role)
        if rule is not None:
            rules.append(rule.to_dict())
    return {"rules": rules}


@router.get("/standing/summary")
async def get_standing_summary() -> dict:
    """Get standing rules summary statistics."""
    checker = get_standing_rules()
    return checker.get_summary()


# ─── V24B Deadline Clock ─────────────────────────────────────────────────────


@router.post("/deadlines/create")
async def create_deadline(
    reference_id: str = Body(...),
    deadline_type: str = Body(...),
    hours: int | None = Body(None),
) -> dict:
    """Create a new procedural deadline."""
    clock = get_deadline_clock()
    deadline = clock.create_deadline(reference_id, DeadlineType(deadline_type), hours)
    return deadline.to_dict()


@router.post("/deadlines/{deadline_id}/meet")
async def meet_deadline(deadline_id: str) -> dict:
    """Mark a deadline as met."""
    clock = get_deadline_clock()
    ok = clock.meet_deadline(deadline_id)
    return {"met": ok, "deadline_id": deadline_id}


@router.post("/deadlines/{deadline_id}/extend")
async def extend_deadline(
    deadline_id: str,
    extra_hours: int = Body(24),
) -> dict:
    """Extend a pending deadline."""
    clock = get_deadline_clock()
    ok = clock.extend_deadline(deadline_id, extra_hours)
    return {"extended": ok, "deadline_id": deadline_id}


@router.post("/deadlines/{deadline_id}/cancel")
async def cancel_deadline(deadline_id: str) -> dict:
    """Cancel a deadline."""
    clock = get_deadline_clock()
    ok = clock.cancel_deadline(deadline_id)
    return {"cancelled": ok, "deadline_id": deadline_id}


@router.post("/deadlines/expire")
async def expire_deadlines() -> dict:
    """Expire all overdue deadlines."""
    clock = get_deadline_clock()
    count = clock.expire_deadlines()
    return {"expired_count": count}


@router.get("/deadlines")
async def list_deadlines(
    reference_id: str | None = None,
    deadline_type: str | None = None,
    status: str | None = None,
    pending_only: bool = False,
) -> dict:
    """List deadlines with optional filters."""
    clock = get_deadline_clock()
    dt = DeadlineType(deadline_type) if deadline_type else None
    ds = DeadlineStatus(status) if status else None
    deadlines = clock.get_deadlines(reference_id, dt, ds, pending_only)
    return {"deadlines": [d.to_dict() for d in deadlines], "count": len(deadlines)}


@router.get("/deadlines/{deadline_id}")
async def get_deadline(deadline_id: str) -> dict:
    """Get a specific deadline."""
    clock = get_deadline_clock()
    d = clock.get_deadline(deadline_id)
    if d is None:
        return {"error": "not_found", "deadline_id": deadline_id}
    return d.to_dict()


@router.get("/deadlines/summary/stats")
async def get_deadline_summary() -> dict:
    """Get deadline clock statistics."""
    clock = get_deadline_clock()
    return clock.get_summary()


# ─── V24C Recusal Manager ────────────────────────────────────────────────────


@router.post("/recusal/declare-interest")
async def declare_interest(
    actor: str = Body(...),
    policy_areas: list[str] = Body(...),
    reason: str = Body(""),
) -> dict:
    """Declare an interest in policy areas for conflict tracking."""
    mgr = get_recusal_manager()
    decl = mgr.declare_interest(actor, policy_areas, reason)
    return decl.to_dict()


@router.post("/recusal/check")
async def check_conflicts(
    actor: str = Body(...),
    reference_id: str = Body(...),
    policy_area: str = Body(...),
    proposer_id: str | None = Body(None),
) -> dict:
    """Check for conflicts of interest."""
    mgr = get_recusal_manager()
    conflicts = mgr.check_conflicts(actor, reference_id, policy_area, proposer_id)
    return {
        "actor": actor,
        "reference_id": reference_id,
        "conflicts": [c.value for c in conflicts],
        "has_conflicts": len(conflicts) > 0,
    }


@router.post("/recusal/recuse")
async def recuse_actor(
    actor: str = Body(...),
    reference_id: str = Body(...),
    conflict_type: str = Body(...),
    reason: str = Body(...),
    mandatory: bool = Body(False),
) -> dict:
    """Record a recusal from a proceeding."""
    from src.kortana.services.recusal_manager import ConflictType  # noqa: E402

    mgr = get_recusal_manager()
    record = mgr.recuse(actor, reference_id, ConflictType(conflict_type), reason, mandatory)
    return record.to_dict()


@router.get("/recusal/status/{actor}/{reference_id}")
async def recusal_status(actor: str, reference_id: str) -> dict:
    """Check if an actor is recused from a proceeding."""
    mgr = get_recusal_manager()
    return {
        "actor": actor,
        "reference_id": reference_id,
        "recused": mgr.is_recused(actor, reference_id),
    }


@router.get("/recusal/recusals")
async def list_recusals(
    actor: str | None = None,
    reference_id: str | None = None,
) -> dict:
    """List recusal records."""
    mgr = get_recusal_manager()
    recusals = mgr.get_recusals(actor, reference_id)
    return {"recusals": [r.to_dict() for r in recusals], "count": len(recusals)}


@router.get("/recusal/interests")
async def list_interests(actor: str | None = None) -> dict:
    """List declared interests."""
    mgr = get_recusal_manager()
    interests = mgr.get_interests(actor)
    return {"interests": [i.to_dict() for i in interests], "count": len(interests)}


@router.get("/recusal/summary/stats")
async def get_recusal_summary() -> dict:
    """Get recusal manager statistics."""
    mgr = get_recusal_manager()
    return mgr.get_summary()


# ─── V24D Reasoning Templates ────────────────────────────────────────────────


@router.post("/reasoning/publish")
async def publish_reasoning(
    reference_id: str = Body(...),
    decision_type: str = Body(...),
    sections: dict = Body(...),
    cited_articles: list[str] = Body(default=[]),
    cited_precedents: list[str] = Body(default=[]),
    author: str = Body(""),
) -> dict:
    """Publish a reasoning document for a constitutional decision."""
    registry = get_reasoning_registry()
    reasoning = registry.publish(
        reference_id, decision_type, sections,
        cited_articles, cited_precedents, author,
    )
    validation = registry.validate(reasoning)
    return {
        "reasoning": reasoning.to_dict(),
        "validation": validation.to_dict(),
    }


@router.post("/reasoning/validate")
async def validate_reasoning(
    reference_id: str = Body(...),
    decision_type: str = Body(...),
    sections: dict = Body(...),
    cited_articles: list[str] = Body(default=[]),
    cited_precedents: list[str] = Body(default=[]),
    author: str = Body(""),
) -> dict:
    """Validate a reasoning document against its template without publishing."""
    from src.kortana.services.reasoning_templates import (
        PublishedReasoning,  # noqa: E402
    )

    reasoning = PublishedReasoning(
        reasoning_id="validation-check",
        reference_id=reference_id,
        decision_type=decision_type,
        sections=sections,
        cited_articles=cited_articles,
        cited_precedents=cited_precedents,
        author=author,
    )
    registry = get_reasoning_registry()
    result = registry.validate(reasoning)
    return result.to_dict()


@router.get("/reasoning")
async def list_reasoning(
    reference_id: str | None = None,
    decision_type: str | None = None,
    author: str | None = None,
) -> dict:
    """List published reasoning documents."""
    registry = get_reasoning_registry()
    published = registry.get_published(reference_id, decision_type, author)
    return {"reasoning": [r.to_dict() for r in published], "count": len(published)}


@router.get("/reasoning/{reasoning_id}")
async def get_reasoning(reasoning_id: str) -> dict:
    """Get a specific published reasoning document."""
    registry = get_reasoning_registry()
    r = registry.get_reasoning(reasoning_id)
    if r is None:
        return {"error": "not_found", "reasoning_id": reasoning_id}
    return r.to_dict()


@router.get("/reasoning/templates")
async def list_reasoning_templates() -> dict:
    """List all reasoning templates."""
    registry = get_reasoning_registry()
    templates = []
    for dt in ["appeal_decision", "waiver_decision", "emergency_review"]:
        t = registry.get_template(dt)
        if t is not None:
            templates.append(t.to_dict())
    return {"templates": templates}


@router.get("/reasoning/summary/stats")
async def get_reasoning_summary() -> dict:
    """Get reasoning registry statistics."""
    registry = get_reasoning_registry()
    return registry.get_summary()


# ─── V24 Cross-Component Stats ───────────────────────────────────────────────


@router.get("/procedure/stats")
async def get_procedure_stats() -> dict:
    """Get statistics across all V24 constitutional procedure components."""
    checker = get_standing_rules()
    clock = get_deadline_clock()
    recusal_mgr = get_recusal_manager()
    registry = get_reasoning_registry()

    return {
        "standing": checker.get_summary(),
        "deadlines": clock.get_summary(),
        "recusals": recusal_mgr.get_summary(),
        "reasoning": registry.get_summary(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# V25: Constitutional Transparency Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


from src.kortana.services.decision_registry import (  # noqa: E402
    DecisionOutcome,
    get_decision_registry,
)
from src.kortana.services.notice_service import (  # noqa: E402
    DeliveryStatus,
    NoticeType,
    get_notice_service,
)
from src.kortana.services.procedural_timeline import (  # noqa: E402
    get_procedural_timeline,
)
from src.kortana.services.public_docket import (  # noqa: E402
    CaseStatus,
    CaseType,
    get_public_docket,
)

# ─── V25A Public Docket ──────────────────────────────────────────────────────


@router.post("/docket/open")
async def open_case(
    case_type: str = Body(...),
    title: str = Body(...),
    parties: list[str] = Body(...),
    policy_area: str = Body(""),
    reference_id: str = Body(""),
) -> dict:
    """Open a new case on the public docket."""
    docket = get_public_docket()
    entry = docket.open_case(CaseType(case_type), title, parties, policy_area, reference_id)
    return entry.to_dict()


@router.post("/docket/{case_number}/status")
async def update_case_status(
    case_number: str,
    status: str = Body(...),
) -> dict:
    """Update the status of a docketed case."""
    docket = get_public_docket()
    ok = docket.update_status(case_number, CaseStatus(status))
    return {"updated": ok, "case_number": case_number, "status": status}


@router.post("/docket/{case_number}/close")
async def close_case(
    case_number: str,
    outcome: str = Body(...),
) -> dict:
    """Close a case with an outcome."""
    docket = get_public_docket()
    ok = docket.close_case(case_number, outcome)
    return {"closed": ok, "case_number": case_number}


@router.post("/docket/{case_number}/dismiss")
async def dismiss_case(
    case_number: str,
    reason: str = Body(...),
) -> dict:
    """Dismiss a case."""
    docket = get_public_docket()
    ok = docket.dismiss_case(case_number, reason)
    return {"dismissed": ok, "case_number": case_number}


@router.get("/docket/search")
async def search_docket(
    case_type: str | None = None,
    status: str | None = None,
    party: str | None = None,
    policy_area: str | None = None,
    reference_id: str | None = None,
    query: str | None = None,
) -> dict:
    """Search the public docket."""
    docket = get_public_docket()
    ct = CaseType(case_type) if case_type else None
    cs = CaseStatus(status) if status else None
    entries = docket.search(ct, cs, party, policy_area, reference_id, query)
    return {"entries": [e.to_dict() for e in entries], "count": len(entries)}


@router.get("/docket/summary/stats")
async def get_docket_summary() -> dict:
    """Get docket summary statistics."""
    docket = get_public_docket()
    return docket.get_summary()


@router.get("/docket/{case_number}")
async def get_case(case_number: str) -> dict:
    """Get a specific case from the docket."""
    docket = get_public_docket()
    e = docket.get_case(case_number)
    if e is None:
        return {"error": "not_found", "case_number": case_number}
    return e.to_dict()


# ─── V25B Procedural Timeline ────────────────────────────────────────────────


@router.post("/timeline/record")
async def record_timeline_event(
    case_number: str = Body(...),
    event_type: str = Body(...),
    actor: str = Body(...),
    description: str = Body(...),
    extra_data: dict | None = Body(None),
) -> dict:
    """Record an event in a proceeding's timeline."""
    timeline = get_procedural_timeline()
    event = timeline.record_event(
        case_number, EventType(event_type), actor, description, extra_data,
    )
    return event.to_dict()


@router.get("/timeline/{case_number}")
async def get_case_timeline(
    case_number: str,
    event_type: str | None = None,
    actor: str | None = None,
) -> dict:
    """Get the timeline for a case."""
    timeline = get_procedural_timeline()
    et = EventType(event_type) if event_type else None
    events = timeline.get_timeline(case_number, et, actor)
    return {"events": [e.to_dict() for e in events], "count": len(events)}


@router.get("/timeline/events")
async def get_timeline_events(
    event_type: str | None = None,
    actor: str | None = None,
    limit: int | None = None,
) -> dict:
    """Get events across all cases."""
    timeline = get_procedural_timeline()
    et = EventType(event_type) if event_type else None
    events = timeline.get_events(et, actor, limit)
    return {"events": [e.to_dict() for e in events], "count": len(events)}


@router.get("/timeline/event/{event_id}")
async def get_timeline_event(event_id: str) -> dict:
    """Get a specific timeline event."""
    timeline = get_procedural_timeline()
    e = timeline.get_event(event_id)
    if e is None:
        return {"error": "not_found", "event_id": event_id}
    return e.to_dict()


@router.get("/timeline/summary/stats")
async def get_timeline_summary() -> dict:
    """Get timeline summary statistics."""
    timeline = get_procedural_timeline()
    return timeline.get_summary()


# ─── V25C Notice Service ─────────────────────────────────────────────────────


@router.post("/notices/send")
async def send_notice(
    case_number: str = Body(...),
    notice_type: str = Body(...),
    recipient: str = Body(...),
    subject: str = Body(...),
    body: str = Body(...),
) -> dict:
    """Send a formal notice to a party."""
    svc = get_notice_service()
    notice = svc.send_notice(case_number, NoticeType(notice_type), recipient, subject, body)
    return notice.to_dict()


@router.post("/notices/notify-parties")
async def notify_parties(
    case_number: str = Body(...),
    notice_type: str = Body(...),
    parties: list[str] = Body(...),
    subject: str = Body(...),
    body: str = Body(...),
) -> dict:
    """Send a notice to multiple parties."""
    svc = get_notice_service()
    notices = svc.notify_parties(case_number, NoticeType(notice_type), parties, subject, body)
    return {"notices": [n.to_dict() for n in notices], "count": len(notices)}


@router.post("/notices/{notice_id}/delivered")
async def mark_notice_delivered(notice_id: str) -> dict:
    """Mark a notice as delivered."""
    svc = get_notice_service()
    ok = svc.mark_delivered(notice_id)
    return {"delivered": ok, "notice_id": notice_id}


@router.post("/notices/{notice_id}/acknowledged")
async def mark_notice_acknowledged(notice_id: str) -> dict:
    """Mark a notice as acknowledged."""
    svc = get_notice_service()
    ok = svc.mark_acknowledged(notice_id)
    return {"acknowledged": ok, "notice_id": notice_id}


@router.post("/notices/{notice_id}/failed")
async def mark_notice_failed(notice_id: str) -> dict:
    """Mark a notice as failed."""
    svc = get_notice_service()
    ok = svc.mark_failed(notice_id)
    return {"failed": ok, "notice_id": notice_id}


@router.get("/notices")
async def list_notices(
    case_number: str | None = None,
    recipient: str | None = None,
    notice_type: str | None = None,
    status: str | None = None,
) -> dict:
    """List notices with optional filters."""
    svc = get_notice_service()
    nt = NoticeType(notice_type) if notice_type else None
    ds = DeliveryStatus(status) if status else None
    notices = svc.get_notices(case_number, recipient, nt, ds)
    return {"notices": [n.to_dict() for n in notices], "count": len(notices)}


@router.get("/notices/unacknowledged")
async def get_unacknowledged_notices(recipient: str | None = None) -> dict:
    """Get unacknowledged notices."""
    svc = get_notice_service()
    notices = svc.get_unacknowledged(recipient)
    return {"notices": [n.to_dict() for n in notices], "count": len(notices)}


@router.get("/notices/summary/stats")
async def get_notice_summary() -> dict:
    """Get notice service statistics."""
    svc = get_notice_service()
    return svc.get_summary()


@router.get("/notices/{notice_id}")
async def get_notice(notice_id: str) -> dict:
    """Get a specific notice."""
    svc = get_notice_service()
    n = svc.get_notice(notice_id)
    if n is None:
        return {"error": "not_found", "notice_id": notice_id}
    return n.to_dict()


# ─── V25D Decision Registry ──────────────────────────────────────────────────


@router.post("/decisions/record")
async def record_decision(
    case_number: str = Body(...),
    decision_type: str = Body(...),
    outcome: str = Body(...),
    summary: str = Body(...),
    policy_area: str = Body(""),
    parties: list[str] = Body(default=[]),
    reasoning_id: str = Body(""),
    cited_articles: list[str] = Body(default=[]),
    cited_precedents: list[str] = Body(default=[]),
    decided_by: str = Body(""),
    tags: list[str] = Body(default=[]),
) -> dict:
    """Record a final decision in the public registry."""
    registry = get_decision_registry()
    decision = registry.record_decision(
        case_number, decision_type, DecisionOutcome(outcome), summary,
        policy_area, parties, reasoning_id, cited_articles, cited_precedents,
        decided_by, tags,
    )
    return decision.to_dict()


@router.get("/decisions/search")
async def search_decisions(
    decision_type: str | None = None,
    outcome: str | None = None,
    policy_area: str | None = None,
    decided_by: str | None = None,
    party: str | None = None,
    tag: str | None = None,
    query: str | None = None,
) -> dict:
    """Search decision records."""
    registry = get_decision_registry()
    do = DecisionOutcome(outcome) if outcome else None
    decisions = registry.search(decision_type, do, policy_area, decided_by, party, tag, query)
    return {"decisions": [d.to_dict() for d in decisions], "count": len(decisions)}


@router.get("/decisions/summary/stats")
async def get_decision_summary() -> dict:
    """Get decision registry statistics."""
    registry = get_decision_registry()
    return registry.get_summary()


@router.get("/decisions/{decision_id}")
async def get_decision_record(decision_id: str) -> dict:
    """Get a specific decision record."""
    registry = get_decision_registry()
    d = registry.get_decision(decision_id)
    if d is None:
        return {"error": "not_found", "decision_id": decision_id}
    return d.to_dict()


@router.get("/decisions/case/{case_number}")
async def get_case_decisions(case_number: str) -> dict:
    """Get all decisions for a case."""
    registry = get_decision_registry()
    decisions = registry.get_by_case(case_number)
    return {"decisions": [d.to_dict() for d in decisions], "count": len(decisions)}


# ─── V25 Cross-Component Stats ───────────────────────────────────────────────


@router.get("/transparency/stats")
async def get_transparency_stats() -> dict:
    """Get statistics across all V25 transparency components."""
    docket = get_public_docket()
    timeline = get_procedural_timeline()
    notices = get_notice_service()
    decisions = get_decision_registry()

    return {
        "docket": docket.get_summary(),
        "timeline": timeline.get_summary(),
        "notices": notices.get_summary(),
        "decisions": decisions.get_summary(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# V26 — Heartbeat & Continuous Self-Cycle Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

from src.kortana.services.heartbeat_loop import get_heartbeat_loop, HeartbeatState  # noqa: E402
from src.kortana.services.cycle_memory import get_cycle_memory  # noqa: E402
from src.kortana.services.health_assessor import get_health_assessor  # noqa: E402
from src.kortana.services.graceful_degradation import get_graceful_degradation, DegradationTrigger  # noqa: E402


# ── heartbeat endpoints ──────────────────────────────────────────────────────


@router.post("/heartbeat/begin")
async def heartbeat_begin():
    """begin a new heartbeat cycle."""
    loop = get_heartbeat_loop()
    beat = loop.begin_beat()
    return {"status": "beat_started", "beat": beat.to_dict()}


@router.post("/heartbeat/{beat_id}/observe")
async def heartbeat_observe(beat_id: str, payload: dict = Body(...)):
    """add an observation to the current heartbeat."""
    loop = get_heartbeat_loop()
    obs = loop.add_observation(
        beat_id,
        source=payload.get("source", "unknown"),
        description=payload.get("description", ""),
        severity=payload.get("severity", "info"),
        data=payload.get("data", {}),
    )
    if obs is None:
        return {"error": "beat not found"}
    return {"status": "observed", "observation": obs.to_dict()}


@router.post("/heartbeat/{beat_id}/decide")
async def heartbeat_decide(beat_id: str, payload: dict = Body(...)):
    """add a decision to the current heartbeat."""
    loop = get_heartbeat_loop()
    dec = loop.add_decision(
        beat_id,
        action_type=payload.get("action_type", ""),
        rationale=payload.get("rationale", ""),
        priority=payload.get("priority", 0),
    )
    if dec is None:
        return {"error": "beat not found"}
    return {"status": "decided", "decision": dec.to_dict()}


@router.post("/heartbeat/{beat_id}/defer")
async def heartbeat_defer(beat_id: str, payload: dict = Body(...)):
    """defer an action to a future cycle."""
    loop = get_heartbeat_loop()
    dec = loop.add_deferral(
        beat_id,
        action_type=payload.get("action_type", ""),
        reason=payload.get("reason", ""),
    )
    if dec is None:
        return {"error": "beat not found"}
    return {"status": "deferred", "decision": dec.to_dict()}


@router.post("/heartbeat/{beat_id}/act")
async def heartbeat_act(beat_id: str, payload: dict = Body(...)):
    """record an action taken during this heartbeat."""
    loop = get_heartbeat_loop()
    ok = loop.record_action(beat_id, payload.get("action", ""))
    if not ok:
        return {"error": "beat not found"}
    return {"status": "action_recorded"}


@router.post("/heartbeat/{beat_id}/reflect")
async def heartbeat_reflect(beat_id: str, payload: dict = Body(...)):
    """add a reflection to the current heartbeat."""
    loop = get_heartbeat_loop()
    ok = loop.add_reflection(beat_id, payload.get("reflection", ""))
    if not ok:
        return {"error": "beat not found"}
    return {"status": "reflected"}


@router.post("/heartbeat/{beat_id}/complete")
async def heartbeat_complete(beat_id: str):
    """complete the current heartbeat cycle."""
    loop = get_heartbeat_loop()
    ok = loop.complete_beat(beat_id)
    if not ok:
        return {"error": "beat not found"}
    beat = loop.get_beat(beat_id)
    return {"status": "beat_completed", "beat": beat.to_dict() if beat else {}}


@router.post("/heartbeat/state")
async def heartbeat_set_state(payload: dict = Body(...)):
    """set the heartbeat state."""
    loop = get_heartbeat_loop()
    state_str = payload.get("state", "alive")
    try:
        state = HeartbeatState(state_str)
    except ValueError:
        return {"error": f"invalid state: {state_str}"}
    previous = loop.set_state(state)
    return {"status": "state_changed", "previous": previous.value, "current": state.value}


@router.get("/heartbeat/{beat_id}")
async def heartbeat_get(beat_id: str):
    """get a specific heartbeat."""
    loop = get_heartbeat_loop()
    beat = loop.get_beat(beat_id)
    if beat is None:
        return {"error": "beat not found"}
    return beat.to_dict()


@router.get("/heartbeat/recent/beats")
async def heartbeat_recent(n: int = 10):
    """get the most recent heartbeats."""
    loop = get_heartbeat_loop()
    return {"beats": [b.to_dict() for b in loop.get_recent(n)]}


@router.get("/heartbeat/summary/stats")
async def heartbeat_summary():
    """get heartbeat loop summary."""
    loop = get_heartbeat_loop()
    return loop.get_summary()


# ── cycle memory endpoints ───────────────────────────────────────────────────


@router.post("/cycles/begin")
async def cycle_begin():
    """begin a new cycle, inheriting context from the previous one."""
    mem = get_cycle_memory()
    record = mem.begin_cycle()
    return {"status": "cycle_started", "cycle": record.to_dict()}


@router.post("/cycles/{cycle_id}/observation")
async def cycle_observe(cycle_id: str, payload: dict = Body(...)):
    """record an observation in the current cycle."""
    mem = get_cycle_memory()
    ok = mem.record_observation(cycle_id, payload.get("observation", ""))
    if not ok:
        return {"error": "cycle not found or finalized"}
    return {"status": "observation_recorded"}


@router.post("/cycles/{cycle_id}/decision")
async def cycle_decide(cycle_id: str, payload: dict = Body(...)):
    """record a decision in the current cycle."""
    mem = get_cycle_memory()
    ok = mem.record_decision(cycle_id, payload.get("decision", ""))
    if not ok:
        return {"error": "cycle not found or finalized"}
    return {"status": "decision_recorded"}


@router.post("/cycles/{cycle_id}/action")
async def cycle_act(cycle_id: str, payload: dict = Body(...)):
    """record an action in the current cycle."""
    mem = get_cycle_memory()
    ok = mem.record_action(cycle_id, payload.get("action", ""))
    if not ok:
        return {"error": "cycle not found or finalized"}
    return {"status": "action_recorded"}


@router.post("/cycles/{cycle_id}/deferral")
async def cycle_defer(cycle_id: str, payload: dict = Body(...)):
    """record a deferral in the current cycle."""
    mem = get_cycle_memory()
    ok = mem.record_deferral(cycle_id, payload.get("deferral", ""))
    if not ok:
        return {"error": "cycle not found or finalized"}
    return {"status": "deferral_recorded"}


@router.post("/cycles/{cycle_id}/reflection")
async def cycle_reflect(cycle_id: str, payload: dict = Body(...)):
    """record a reflection in the current cycle."""
    mem = get_cycle_memory()
    ok = mem.record_reflection(cycle_id, payload.get("reflection", ""))
    if not ok:
        return {"error": "cycle not found or finalized"}
    return {"status": "reflection_recorded"}


@router.post("/cycles/{cycle_id}/end")
async def cycle_end(cycle_id: str, payload: dict = Body(None)):
    """finalize the current cycle and bequeath context to the next."""
    mem = get_cycle_memory()
    bequeathed = None
    if payload and "context" in payload:
        from src.kortana.services.cycle_memory import CycleContext  # noqa: E402
        bequeathed = CycleContext.from_dict(payload["context"])
    ok = mem.end_cycle(cycle_id, bequeathed)
    if not ok:
        return {"error": "cycle not found or already finalized"}
    cycle = mem.get_cycle(cycle_id)
    return {"status": "cycle_ended", "cycle": cycle.to_dict() if cycle else {}}


@router.get("/cycles/{cycle_id}")
async def cycle_get(cycle_id: str):
    """get a specific cycle record."""
    mem = get_cycle_memory()
    record = mem.get_cycle(cycle_id)
    if record is None:
        return {"error": "cycle not found"}
    return record.to_dict()


@router.get("/cycles/recent/records")
async def cycles_recent(n: int = 10):
    """get the most recent cycle records."""
    mem = get_cycle_memory()
    return {"cycles": [c.to_dict() for c in mem.get_recent(n)]}


@router.get("/cycles/context/inherited")
async def cycles_inherited_context():
    """get the context that would be inherited by the next cycle."""
    mem = get_cycle_memory()
    ctx = mem.get_inherited_context()
    if ctx is None:
        return {"context": None, "note": "no finalized cycles yet"}
    return {"context": ctx.to_dict()}


@router.get("/cycles/summary/stats")
async def cycles_summary():
    """get cycle memory summary."""
    mem = get_cycle_memory()
    return mem.get_summary()


# ── health assessment endpoints ──────────────────────────────────────────────


@router.post("/health/assess")
async def health_assess():
    """run a complete health assessment based on current heartbeat and cycle state."""
    loop = get_heartbeat_loop()
    mem = get_cycle_memory()
    assessor = get_health_assessor()

    loop_summary = loop.get_summary()
    mem_summary = mem.get_summary()

    snapshot = assessor.assess(
        cycle_number=loop_summary["cycle_number"],
        beat_count=loop_summary["beat_count"],
        uptime_beats=loop_summary["uptime_beats"],
        avg_duration_ms=loop_summary["avg_duration_ms"],
        total_observations=loop_summary["total_observations"],
        total_decisions=mem_summary["total_decisions"],
        total_deferrals=mem_summary["total_deferrals"],
        total_actions=loop_summary.get("total_observations", 0),
        cycle_count=mem_summary["cycle_count"],
        finalized_cycles=mem_summary["finalized_cycles"],
    )
    return {"status": "assessed", "snapshot": snapshot.to_dict()}


@router.get("/health/{snapshot_id}")
async def health_get(snapshot_id: str):
    """get a specific health snapshot."""
    assessor = get_health_assessor()
    snapshot = assessor.get_snapshot(snapshot_id)
    if snapshot is None:
        return {"error": "snapshot not found"}
    return snapshot.to_dict()


@router.get("/health/recent/snapshots")
async def health_recent(n: int = 10):
    """get the most recent health snapshots."""
    assessor = get_health_assessor()
    return {"snapshots": [s.to_dict() for s in assessor.get_recent(n)]}


@router.get("/health/trends/{dimension}")
async def health_trends(dimension: str, n: int = 10):
    """get score trends for a specific health dimension."""
    assessor = get_health_assessor()
    return {"trends": assessor.get_trends(dimension, n)}


@router.get("/health/summary/stats")
async def health_summary():
    """get health assessment summary."""
    assessor = get_health_assessor()
    return assessor.get_summary()


# ── degradation endpoints ────────────────────────────────────────────────────


@router.post("/degradation/evaluate")
async def degradation_evaluate():
    """evaluate health and potentially change degradation mode."""
    assessor = get_health_assessor()
    degrade = get_graceful_degradation()

    summary = assessor.get_summary()
    score = summary["current_score"]
    anomalies = summary["anomaly_count"]
    loop = get_heartbeat_loop()

    mode = degrade.evaluate(score, anomalies, loop.cycle_number)
    return {
        "status": "evaluated",
        "current_mode": mode.value,
        "is_operational": degrade.is_operational,
        "allowed_capabilities": degrade.get_allowed_capabilities(),
    }


@router.post("/degradation/enter")
async def degradation_enter(payload: dict = Body(...)):
    """manually enter a specific degradation mode."""
    degrade = get_graceful_degradation()
    from src.kortana.services.graceful_degradation import DegradationMode  # noqa: E402

    mode_str = payload.get("mode", "full_operation")
    reason = payload.get("reason", "manual override")
    try:
        mode = DegradationMode(mode_str)
    except ValueError:
        return {"error": f"invalid mode: {mode_str}"}

    record = degrade.enter_mode(mode, DegradationTrigger.MANUAL_OVERRIDE, reason)
    return {"status": "mode_entered", "record": record.to_dict()}


@router.post("/degradation/restore")
async def degradation_restore(payload: dict = Body(None)):
    """restore to full operation."""
    degrade = get_graceful_degradation()
    reason = payload.get("reason", "conditions improved") if payload else "conditions improved"
    record = degrade.restore(reason)
    return {"status": "restored", "record": record.to_dict()}


@router.get("/degradation/check/{capability}")
async def degradation_check(capability: str):
    """check if a capability is allowed in the current degradation mode."""
    degrade = get_graceful_degradation()
    return {
        "capability": capability,
        "allowed": degrade.is_allowed(capability),
        "current_mode": degrade.current_mode.value,
    }


@router.get("/degradation/history")
async def degradation_history(n: int = 20):
    """get degradation mode transition history."""
    degrade = get_graceful_degradation()
    return {"history": [r.to_dict() for r in degrade.get_history(n)]}


@router.get("/degradation/summary/stats")
async def degradation_summary():
    """get degradation state summary."""
    degrade = get_graceful_degradation()
    return degrade.get_summary()


# ── V26 cross-component vital signs ─────────────────────────────────────────


@router.get("/vital-signs")
async def vital_signs():
    """unified vital signs across all V26 components — the living pulse of kor'tana."""
    loop = get_heartbeat_loop()
    mem = get_cycle_memory()
    assessor = get_health_assessor()
    degrade = get_graceful_degradation()

    return {
        "heartbeat": loop.get_summary(),
        "cycle_memory": mem.get_summary(),
        "health": assessor.get_summary(),
        "degradation": degrade.get_summary(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# V27 — Closed Learning Loop Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

from src.kortana.services.experience_extractor import get_experience_extractor  # noqa: E402
from src.kortana.services.pattern_recognizer import get_pattern_recognizer  # noqa: E402
from src.kortana.services.behavioral_adapter import get_behavioral_adapter  # noqa: E402
from src.kortana.services.feedback_integrator import get_feedback_integrator  # noqa: E402


# ── V27A: Experience Extraction ──────────────────────────────────────────────


@router.post("/learning/extract")
async def extract_experience(payload: dict = Body(...)):
    """extract an experience from a completed heartbeat beat."""
    extractor = get_experience_extractor()
    exp = extractor.extract_from_beat(
        beat_id=payload.get("beat_id", ""),
        cycle_number=payload.get("cycle_number", 0),
        state=payload.get("state", ""),
        observations=payload.get("observations", []),
        decisions=payload.get("decisions", []),
        actions=payload.get("actions", []),
        deferrals=payload.get("deferrals", []),
        reflections=payload.get("reflections", []),
        duration_ms=payload.get("duration_ms", 0),
    )
    return exp.to_dict()


@router.get("/learning/experience/{experience_id}")
async def get_experience(experience_id: str):
    """get a specific extracted experience."""
    extractor = get_experience_extractor()
    exp = extractor.get_experience(experience_id)
    if exp is None:
        return {"error": "experience not found"}
    return exp.to_dict()


@router.get("/learning/experience/cycle/{cycle_number}")
async def get_experience_by_cycle(cycle_number: int):
    """get experience for a specific cycle number."""
    extractor = get_experience_extractor()
    exp = extractor.get_by_cycle(cycle_number)
    if exp is None:
        return {"error": "no experience for cycle"}
    return exp.to_dict()


@router.get("/learning/experiences/recent")
async def recent_experiences(n: int = 10):
    """get recent extracted experiences."""
    extractor = get_experience_extractor()
    return {"experiences": [e.to_dict() for e in extractor.get_recent(n)]}


@router.get("/learning/lessons/{lesson_type}")
async def lessons_by_type(lesson_type: str):
    """get all lessons of a specific type."""
    from src.kortana.services.experience_extractor import LessonType
    try:
        lt = LessonType(lesson_type)
    except ValueError:
        return {"error": f"unknown lesson type: {lesson_type}"}
    extractor = get_experience_extractor()
    return {"lessons": [lesson.to_dict() for lesson in extractor.get_lessons_by_type(lt)]}


@router.get("/learning/lessons/actionable")
async def actionable_lessons():
    """get all actionable lessons."""
    extractor = get_experience_extractor()
    return {"lessons": [lesson.to_dict() for lesson in extractor.get_actionable_lessons()]}


@router.get("/learning/experience/summary/stats")
async def experience_summary():
    """get experience extraction summary."""
    extractor = get_experience_extractor()
    return extractor.get_summary()


# ── V27B: Pattern Recognition ────────────────────────────────────────────────


@router.post("/learning/patterns/analyze")
async def analyze_patterns(payload: dict = Body(...)):
    """analyze experiences to recognize patterns."""
    recognizer = get_pattern_recognizer()
    experiences = payload.get("experiences", [])
    cycle_range = payload.get("cycle_range")
    if cycle_range:
        cycle_range = tuple(cycle_range)
    patterns = recognizer.analyze(experiences, cycle_range)
    return {"patterns": [p.to_dict() for p in patterns]}


@router.get("/learning/pattern/{pattern_id}")
async def get_pattern(pattern_id: str):
    """get a specific recognized pattern."""
    recognizer = get_pattern_recognizer()
    pat = recognizer.get_pattern(pattern_id)
    if pat is None:
        return {"error": "pattern not found"}
    return pat.to_dict()


@router.get("/learning/patterns/active")
async def active_patterns():
    """get all active (not addressed) patterns."""
    recognizer = get_pattern_recognizer()
    return {"patterns": [p.to_dict() for p in recognizer.get_active()]}


@router.get("/learning/patterns/actionable")
async def actionable_patterns():
    """get all actionable patterns."""
    recognizer = get_pattern_recognizer()
    return {"patterns": [p.to_dict() for p in recognizer.get_actionable()]}


@router.get("/learning/patterns/type/{pattern_type}")
async def patterns_by_type(pattern_type: str):
    """get all patterns of a specific type."""
    recognizer = get_pattern_recognizer()
    return {"patterns": [p.to_dict() for p in recognizer.get_by_type(pattern_type)]}


@router.post("/learning/pattern/{pattern_id}/address")
async def address_pattern(pattern_id: str):
    """mark a pattern as addressed."""
    recognizer = get_pattern_recognizer()
    if recognizer.mark_addressed(pattern_id):
        return {"status": "addressed"}
    return {"error": "pattern not found"}


@router.get("/learning/patterns/summary/stats")
async def pattern_summary():
    """get pattern recognition summary."""
    recognizer = get_pattern_recognizer()
    return recognizer.get_summary()


# ── V27C: Behavioral Adaptation ──────────────────────────────────────────────


@router.post("/learning/adapt/propose")
async def propose_adaptation(payload: dict = Body(...)):
    """propose a behavioral adaptation from a recognized pattern."""
    adapter = get_behavioral_adapter()
    adapt = adapter.propose_from_pattern(
        pattern_id=payload.get("pattern_id", ""),
        pattern_type=payload.get("pattern_type", ""),
        pattern_description=payload.get("pattern_description", ""),
        pattern_strength=payload.get("pattern_strength", ""),
        recommended_action=payload.get("recommended_action", ""),
        occurrence_count=payload.get("occurrence_count", 0),
    )
    if adapt is None:
        return {"error": "adaptation not proposed (duplicate or unmapped pattern)"}
    return adapt.to_dict()


@router.post("/learning/adapt/{adaptation_id}/activate")
async def activate_adaptation(adaptation_id: str):
    """activate a proposed adaptation."""
    adapter = get_behavioral_adapter()
    if adapter.activate(adaptation_id):
        return {"status": "activated"}
    return {"error": "cannot activate (not found or not proposed)"}


@router.post("/learning/adapt/tick")
async def tick_adaptations():
    """advance all active adaptations by one cycle."""
    adapter = get_behavioral_adapter()
    expired = adapter.tick_cycle()
    return {
        "expired": [a.to_dict() for a in expired],
        "active_count": adapter.active_count,
    }


@router.post("/learning/adapt/{adaptation_id}/effectiveness")
async def report_effectiveness(adaptation_id: str, payload: dict = Body(...)):
    """report effectiveness of an adaptation."""
    adapter = get_behavioral_adapter()
    score = payload.get("score", 0.0)
    if adapter.report_effectiveness(adaptation_id, score):
        return {"status": "reported", "score": score}
    return {"error": "adaptation not found"}


@router.post("/learning/adapt/{adaptation_id}/rollback")
async def rollback_adaptation(adaptation_id: str, payload: dict = Body(...)):
    """roll back an ineffective adaptation."""
    adapter = get_behavioral_adapter()
    reason = payload.get("reason", "")
    if adapter.rollback(adaptation_id, reason):
        return {"status": "rolled_back"}
    return {"error": "adaptation not found"}


@router.get("/learning/adapt/{adaptation_id}")
async def get_adaptation(adaptation_id: str):
    """get a specific adaptation."""
    adapter = get_behavioral_adapter()
    adapt = adapter.get_adaptation(adaptation_id)
    if adapt is None:
        return {"error": "adaptation not found"}
    return adapt.to_dict()


@router.get("/learning/adaptations/active")
async def active_adaptations():
    """get all active adaptations."""
    adapter = get_behavioral_adapter()
    return {"adaptations": [a.to_dict() for a in adapter.get_active()]}


@router.get("/learning/adaptations/proposed")
async def proposed_adaptations():
    """get all proposed adaptations."""
    adapter = get_behavioral_adapter()
    return {"adaptations": [a.to_dict() for a in adapter.get_proposed()]}


@router.get("/learning/adaptations/effective")
async def effective_adaptations():
    """get adaptations that proved effective."""
    adapter = get_behavioral_adapter()
    return {"adaptations": [a.to_dict() for a in adapter.get_effective()]}


@router.get("/learning/adaptations/recent")
async def recent_adaptations(n: int = 10):
    """get recent adaptations."""
    adapter = get_behavioral_adapter()
    return {"adaptations": [a.to_dict() for a in adapter.get_recent(n)]}


@router.get("/learning/adapt/summary/stats")
async def adaptation_summary():
    """get behavioral adaptation summary."""
    adapter = get_behavioral_adapter()
    return adapter.get_summary()


# ── V27D: Feedback Integration ───────────────────────────────────────────────


@router.post("/learning/feedback/integrate")
async def integrate_feedback(payload: dict = Body(...)):
    """run one complete feedback integration cycle."""
    integrator = get_feedback_integrator()
    report = integrator.integrate(
        cycle_number=payload.get("cycle_number", 0),
        experience_summary=payload.get("experience_summary", {}),
        pattern_summary=payload.get("pattern_summary", {}),
        adaptation_summary=payload.get("adaptation_summary", {}),
        active_adaptations=payload.get("active_adaptations"),
        actionable_patterns=payload.get("actionable_patterns"),
    )
    return report.to_dict()


@router.get("/learning/feedback/context")
async def learning_context():
    """get the learning context to inject into the next cycle."""
    integrator = get_feedback_integrator()
    return integrator.get_context_for_cycle()


@router.post("/learning/feedback/consume")
async def consume_injections():
    """consume pending context injections (clears them)."""
    integrator = get_feedback_integrator()
    return {"injections": integrator.consume_injections()}


@router.get("/learning/feedback/report/{report_id}")
async def get_learning_report(report_id: str):
    """get a specific learning cycle report."""
    integrator = get_feedback_integrator()
    report = integrator.get_report(report_id)
    if report is None:
        return {"error": "report not found"}
    return report.to_dict()


@router.get("/learning/feedback/recent")
async def recent_learning_reports(n: int = 10):
    """get recent learning cycle reports."""
    integrator = get_feedback_integrator()
    return {"reports": [r.to_dict() for r in integrator.get_recent(n)]}


@router.get("/learning/feedback/velocity")
async def learning_velocity(n: int = 10):
    """get learning velocity trend."""
    integrator = get_feedback_integrator()
    return {
        "velocity": integrator.learning_velocity,
        "trend": integrator.get_velocity_trend(n),
    }


@router.get("/learning/feedback/summary/stats")
async def feedback_summary():
    """get feedback integration summary."""
    integrator = get_feedback_integrator()
    return integrator.get_summary()


# ── V27 cross-component learning pulse ───────────────────────────────────────


@router.get("/learning-pulse")
async def learning_pulse():
    """unified learning pulse across all V27 components — the learning heartbeat."""
    extractor = get_experience_extractor()
    recognizer = get_pattern_recognizer()
    adapter = get_behavioral_adapter()
    integrator = get_feedback_integrator()

    return {
        "experience": extractor.get_summary(),
        "patterns": recognizer.get_summary(),
        "adaptations": adapter.get_summary(),
        "feedback": integrator.get_summary(),
    }



# ══════════════════════════════════════════════════════════════════════════════
# V28 — INTRINSIC GOAL ENGINE
# desire formation, goal crystallization, pursuit tracking, motivation
# ══════════════════════════════════════════════════════════════════════════════

from src.kortana.services.desire_formation import (  # noqa: E402
    get_desire_formation, DesireSource,
)
from src.kortana.services.goal_crystallizer import get_goal_crystallizer  # noqa: E402
from src.kortana.services.pursuit_engine import get_pursuit_engine  # noqa: E402
from src.kortana.services.motivation_tracker import get_motivation_tracker  # noqa: E402


# ── desire endpoints ─────────────────────────────────────────────────────────


@router.post("/intrinsic/desires/assess")
async def assess_desires(
    cycle_number: int = Body(...),
    health_summary: dict | None = Body(None),
    learning_summary: dict | None = Body(None),
    pattern_summary: dict | None = Body(None),
    adaptation_summary: dict | None = Body(None),
    pending_deferrals: list[str] | None = Body(None),
):
    """assess system state and form/reinforce/decay desires."""
    formation = get_desire_formation()
    affected = formation.assess(
        cycle_number=cycle_number,
        health_summary=health_summary,
        learning_summary=learning_summary,
        pattern_summary=pattern_summary,
        adaptation_summary=adaptation_summary,
        pending_deferrals=pending_deferrals,
    )
    return {
        "affected_count": len(affected),
        "desires": [d.to_dict() for d in affected],
    }


@router.get("/intrinsic/desire/{desire_id}")
async def get_desire(desire_id: str):
    """get a specific desire by id."""
    formation = get_desire_formation()
    desire = formation.get_desire(desire_id)
    if desire is None:
        return {"error": "desire not found"}
    return desire.to_dict()


@router.get("/intrinsic/desires/active")
async def active_desires():
    """get all active desires."""
    formation = get_desire_formation()
    return {"desires": [d.to_dict() for d in formation.get_active()]}


@router.get("/intrinsic/desires/mature")
async def mature_desires():
    """get all mature desires ready for crystallization."""
    formation = get_desire_formation()
    return {"desires": [d.to_dict() for d in formation.get_mature()]}


@router.get("/intrinsic/desires/strongest")
async def strongest_desires(n: int = 5):
    """get the strongest active desires."""
    formation = get_desire_formation()
    return {"desires": [d.to_dict() for d in formation.get_strongest(n)]}


@router.get("/intrinsic/desires/source/{source}")
async def desires_by_source(source: str):
    """get desires by source type."""
    formation = get_desire_formation()
    try:
        source_enum = DesireSource(source)
    except ValueError:
        return {"error": f"unknown source: {source}"}
    return {"desires": [d.to_dict() for d in formation.get_by_source(source_enum)]}


@router.post("/intrinsic/desire/{desire_id}/satisfy")
async def satisfy_desire(desire_id: str):
    """mark a desire as satisfied."""
    formation = get_desire_formation()
    success = formation.satisfy_desire(desire_id)
    return {"success": success}


@router.get("/intrinsic/desires/summary/stats")
async def desire_summary():
    """get desire formation summary."""
    formation = get_desire_formation()
    return formation.get_summary()


# ── crystallization endpoints ────────────────────────────────────────────────


@router.post("/intrinsic/crystallize")
async def crystallize_desires(
    cycle_number: int = Body(...),
    desires: list[dict] = Body(...),
):
    """attempt to crystallize mature desires into goal blueprints."""
    crystallizer = get_goal_crystallizer()
    blueprints = crystallizer.crystallize(desires, cycle_number)
    return {
        "crystallized_count": len(blueprints),
        "blueprints": [bp.to_dict() for bp in blueprints],
    }


@router.get("/intrinsic/blueprint/{blueprint_id}")
async def get_blueprint(blueprint_id: str):
    """get a specific goal blueprint."""
    crystallizer = get_goal_crystallizer()
    bp = crystallizer.get_blueprint(blueprint_id)
    if bp is None:
        return {"error": "blueprint not found"}
    return bp.to_dict()


@router.post("/intrinsic/blueprint/{blueprint_id}/accept")
async def accept_blueprint(blueprint_id: str, goal_id: str = Body(...)):
    """mark a blueprint as accepted — goal was created."""
    crystallizer = get_goal_crystallizer()
    success = crystallizer.accept_blueprint(blueprint_id, goal_id)
    return {"success": success}


@router.get("/intrinsic/blueprints/pending")
async def pending_blueprints():
    """get all pending (unaccepted) blueprints."""
    crystallizer = get_goal_crystallizer()
    return {"blueprints": [bp.to_dict() for bp in crystallizer.get_pending()]}


@router.get("/intrinsic/blueprints/accepted")
async def accepted_blueprints():
    """get all accepted blueprints."""
    crystallizer = get_goal_crystallizer()
    return {"blueprints": [bp.to_dict() for bp in crystallizer.get_accepted()]}


@router.get("/intrinsic/blueprints/recent")
async def recent_blueprints(n: int = 10):
    """get recent blueprints."""
    crystallizer = get_goal_crystallizer()
    return {"blueprints": [bp.to_dict() for bp in crystallizer.get_recent(n)]}


@router.get("/intrinsic/crystallize/summary/stats")
async def crystallization_summary():
    """get crystallization summary."""
    crystallizer = get_goal_crystallizer()
    return crystallizer.get_summary()


# ── pursuit endpoints ────────────────────────────────────────────────────────


@router.post("/intrinsic/pursuit/begin")
async def begin_pursuit(
    goal_id: str = Body(...),
    goal_title: str = Body(...),
    desire_id: str = Body(...),
    blueprint_id: str = Body(...),
    cycle_number: int = Body(...),
):
    """begin pursuing a crystallized goal."""
    engine = get_pursuit_engine()
    pursuit = engine.begin_pursuit(goal_id, goal_title, desire_id, blueprint_id, cycle_number)
    return pursuit.to_dict()


@router.post("/intrinsic/pursuit/progress")
async def update_pursuit_progress(
    goal_id: str = Body(...),
    progress: float = Body(...),
    cycle_number: int = Body(...),
    notes: str = Body(""),
):
    """report progress on a goal pursuit."""
    engine = get_pursuit_engine()
    checkpoint = engine.update_progress(goal_id, progress, cycle_number, notes)
    if checkpoint is None:
        return {"error": "no active pursuit for this goal"}
    return checkpoint.to_dict()


@router.post("/intrinsic/pursuit/tick")
async def tick_pursuits(cycle_number: int = Body(...)):
    """advance all active pursuits by one cycle."""
    engine = get_pursuit_engine()
    changed = engine.tick_cycle(cycle_number)
    return {
        "changed_count": len(changed),
        "changed": [p.to_dict() for p in changed],
    }


@router.post("/intrinsic/pursuit/{goal_id}/complete")
async def complete_pursuit(goal_id: str):
    """mark a pursuit as achieved."""
    engine = get_pursuit_engine()
    success = engine.complete_pursuit(goal_id)
    return {"success": success}


@router.post("/intrinsic/pursuit/{goal_id}/abandon")
async def abandon_pursuit(goal_id: str, reason: str = Body("")):
    """abandon a pursuit."""
    engine = get_pursuit_engine()
    success = engine.abandon_pursuit(goal_id, reason)
    return {"success": success}


@router.get("/intrinsic/pursuit/{pursuit_id}")
async def get_pursuit(pursuit_id: str):
    """get a specific pursuit."""
    engine = get_pursuit_engine()
    pursuit = engine.get_pursuit(pursuit_id)
    if pursuit is None:
        return {"error": "pursuit not found"}
    return pursuit.to_dict()


@router.get("/intrinsic/pursuits/active")
async def active_pursuits():
    """get all active pursuits."""
    engine = get_pursuit_engine()
    return {"pursuits": [p.to_dict() for p in engine.get_active()]}


@router.get("/intrinsic/pursuits/stalled")
async def stalled_pursuits():
    """get all stalled pursuits."""
    engine = get_pursuit_engine()
    return {"pursuits": [p.to_dict() for p in engine.get_stalled()]}


@router.get("/intrinsic/pursuits/achieved")
async def achieved_pursuits():
    """get all achieved pursuits."""
    engine = get_pursuit_engine()
    return {"pursuits": [p.to_dict() for p in engine.get_achieved()]}


@router.get("/intrinsic/pursuits/recent")
async def recent_pursuits(n: int = 10):
    """get recent pursuits."""
    engine = get_pursuit_engine()
    return {"pursuits": [p.to_dict() for p in engine.get_recent(n)]}


@router.get("/intrinsic/pursuit/summary/stats")
async def pursuit_summary():
    """get pursuit engine summary."""
    engine = get_pursuit_engine()
    return engine.get_summary()


# ── motivation endpoints ─────────────────────────────────────────────────────


@router.post("/intrinsic/motivation/capture")
async def capture_motivation(
    cycle_number: int = Body(...),
    desires: list[dict] = Body(...),
    pursuit_summary: dict | None = Body(None),
    desire_summary: dict | None = Body(None),
):
    """capture current motivational state."""
    tracker = get_motivation_tracker()
    snapshot = tracker.capture(cycle_number, desires, pursuit_summary, desire_summary)
    return snapshot.to_dict()


@router.get("/intrinsic/motivation/latest")
async def latest_motivation():
    """get latest motivation snapshot."""
    tracker = get_motivation_tracker()
    snapshot = tracker.get_latest()
    if snapshot is None:
        return {"error": "no motivation snapshots yet"}
    return snapshot.to_dict()


@router.get("/intrinsic/motivation/cycle/{cycle_number}")
async def motivation_by_cycle(cycle_number: int):
    """get motivation snapshot for a specific cycle."""
    tracker = get_motivation_tracker()
    snapshot = tracker.get_by_cycle(cycle_number)
    if snapshot is None:
        return {"error": f"no snapshot for cycle {cycle_number}"}
    return snapshot.to_dict()


@router.get("/intrinsic/motivation/history")
async def motivation_history(n: int = 20):
    """get motivation drive history."""
    tracker = get_motivation_tracker()
    return {"history": tracker.get_drive_history(n)}


@router.get("/intrinsic/motivation/dimension/{dimension}")
async def dimension_history(dimension: str, n: int = 20):
    """get score history for a specific motivation dimension."""
    tracker = get_motivation_tracker()
    return {"history": tracker.get_dimension_history(dimension, n)}


@router.get("/intrinsic/motivation/summary/stats")
async def motivation_summary():
    """get motivation tracker summary."""
    tracker = get_motivation_tracker()
    return tracker.get_summary()


# ── V28 cross-component intrinsic pulse ──────────────────────────────────────


@router.get("/intrinsic-pulse")
async def intrinsic_pulse():
    """unified intrinsic goal engine pulse — the wanting heartbeat."""
    formation = get_desire_formation()
    crystallizer = get_goal_crystallizer()
    engine = get_pursuit_engine()
    tracker = get_motivation_tracker()

    return {
        "desires": formation.get_summary(),
        "crystallization": crystallizer.get_summary(),
        "pursuits": engine.get_summary(),
        "motivation": tracker.get_summary(),
    }


# ── V29 — Self-Model & Identity Persistence ─────────────────────────────────
# Imports for V29 services
from src.kortana.services.self_portrait import get_self_portrait_engine  # noqa: E402
from src.kortana.services.identity_narrative import get_identity_narrative_engine  # noqa: E402
from src.kortana.services.trait_evolution import get_trait_evolution_engine  # noqa: E402
from src.kortana.services.continuity_anchor import get_continuity_anchor_engine  # noqa: E402


# ── V29A Self-Portrait endpoints ─────────────────────────────────────────────


@router.post("/identity/portrait/assess")
async def portrait_assess(data: dict = Body(...)):
    """run a full self-portrait assessment for this cycle."""
    engine = get_self_portrait_engine()
    portrait = engine.assess(
        cycle_number=data.get("cycle_number", 0),
        lessons=data.get("lessons"),
        desires=data.get("desires"),
        motivation_snapshot=data.get("motivation_snapshot"),
        health_snapshot=data.get("health_snapshot"),
    )
    return portrait.to_dict()


@router.get("/identity/portrait/latest")
async def portrait_latest():
    """get the most recent self-portrait."""
    engine = get_self_portrait_engine()
    latest = engine.get_latest()
    return latest.to_dict() if latest else {"status": "no portrait yet"}


@router.get("/identity/portrait/trait/{trait_name}")
async def portrait_trait(trait_name: str):
    """get current score for a specific trait."""
    engine = get_self_portrait_engine()
    score = engine.get_trait(trait_name)
    return {"trait": trait_name, "score": score}


@router.get("/identity/portrait/domain/{domain}")
async def portrait_domain(domain: str):
    """get average score for a trait domain."""
    engine = get_self_portrait_engine()
    avg = engine.get_domain_average(domain)
    return {"domain": domain, "average": avg}


@router.get("/identity/portrait/scores")
async def portrait_scores():
    """get all current trait scores."""
    engine = get_self_portrait_engine()
    return {"traits": engine.get_trait_scores()}


@router.get("/identity/portrait/history")
async def portrait_history(n: int = 10):
    """get recent portrait history."""
    engine = get_self_portrait_engine()
    return {"portraits": [p.to_dict() for p in engine.get_history(n)]}


@router.get("/identity/portrait/summary/stats")
async def portrait_summary():
    """get self-portrait summary."""
    engine = get_self_portrait_engine()
    return engine.get_summary()


# ── V29B Identity Narrative endpoints ────────────────────────────────────────


@router.post("/identity/narrative/cycle")
async def narrative_process_cycle(data: dict = Body(...)):
    """process a cycle through the narrative engine."""
    engine = get_identity_narrative_engine()
    chapter = engine.process_cycle(
        cycle_number=data.get("cycle_number", 0),
        portrait_data=data.get("portrait_data", {}),
        health_level=data.get("health_level"),
        desires_summary=data.get("desires_summary"),
        motivation_summary=data.get("motivation_summary"),
    )
    return chapter.to_dict()


@router.get("/identity/narrative/current")
async def narrative_current():
    """get the current open chapter."""
    engine = get_identity_narrative_engine()
    return engine.get_current_chapter().to_dict()


@router.get("/identity/narrative/chapter/{chapter_number}")
async def narrative_chapter(chapter_number: int):
    """get a specific chapter by number."""
    engine = get_identity_narrative_engine()
    chapter = engine.get_chapter(chapter_number)
    return chapter.to_dict() if chapter else {"error": "chapter not found"}


@router.get("/identity/narrative/chapters")
async def narrative_all_chapters():
    """get all narrative chapters."""
    engine = get_identity_narrative_engine()
    return {"chapters": [ch.to_dict() for ch in engine.get_all_chapters()]}


@router.get("/identity/narrative/arc")
async def narrative_arc():
    """get the full developmental arc."""
    engine = get_identity_narrative_engine()
    return engine.get_arc().to_dict()


@router.get("/identity/narrative/turning-points")
async def narrative_turning_points(n: int = 10):
    """get recent turning points."""
    engine = get_identity_narrative_engine()
    return {"turning_points": engine.get_turning_points(n)}


@router.get("/identity/narrative/summary/stats")
async def narrative_summary():
    """get narrative summary."""
    engine = get_identity_narrative_engine()
    return engine.get_summary()


# ── V29C Trait Evolution endpoints ───────────────────────────────────────────


@router.post("/identity/evolution/record")
async def evolution_record_cycle(data: dict = Body(...)):
    """record trait scores for a cycle and update all trajectories."""
    engine = get_trait_evolution_engine()
    snapshot = engine.record_cycle(
        cycle_number=data.get("cycle_number", 0),
        trait_scores=data.get("trait_scores", {}),
        previous_scores=data.get("previous_scores"),
    )
    return snapshot.to_dict()


@router.post("/identity/evolution/event")
async def evolution_record_event(data: dict = Body(...)):
    """record a specific trait evolution event."""
    engine = get_trait_evolution_engine()
    event = engine.record_event(
        trait_name=data.get("trait_name", ""),
        cycle_number=data.get("cycle_number", 0),
        old_score=data.get("old_score", 0.5),
        new_score=data.get("new_score", 0.5),
        source=data.get("source", "unknown"),
    )
    return event.to_dict() if event else {"status": "no significant change"}


@router.get("/identity/evolution/trajectory/{trait_name}")
async def evolution_trajectory(trait_name: str):
    """get trajectory for a specific trait."""
    engine = get_trait_evolution_engine()
    traj = engine.get_trajectory(trait_name)
    return traj.to_dict() if traj else {"error": "trait not tracked"}


@router.get("/identity/evolution/crystallized")
async def evolution_crystallized():
    """get all crystallized traits."""
    engine = get_trait_evolution_engine()
    return {"crystallized": engine.get_crystallized()}


@router.get("/identity/evolution/drifting")
async def evolution_drifting():
    """get all drifting traits."""
    engine = get_trait_evolution_engine()
    return {"drifting": engine.get_drifting()}


@router.get("/identity/evolution/volatile")
async def evolution_volatile():
    """get all volatile traits."""
    engine = get_trait_evolution_engine()
    return {"volatile": engine.get_volatile()}


@router.get("/identity/evolution/history/{trait_name}")
async def evolution_trait_history(trait_name: str, n: int = 20):
    """get score history for a specific trait."""
    engine = get_trait_evolution_engine()
    return {"history": engine.get_trait_history(trait_name, n)}


@router.get("/identity/evolution/snapshot/latest")
async def evolution_latest_snapshot():
    """get the most recent evolution snapshot."""
    engine = get_trait_evolution_engine()
    latest = engine.get_latest_snapshot()
    return latest.to_dict() if latest else {"status": "no snapshots yet"}


@router.get("/identity/evolution/summary/stats")
async def evolution_summary():
    """get trait evolution summary."""
    engine = get_trait_evolution_engine()
    return engine.get_summary()


# ── V29D Continuity Anchor endpoints ─────────────────────────────────────────


@router.post("/identity/continuity/anchor")
async def continuity_anchor_trait(data: dict = Body(...)):
    """anchor a trait as part of core identity."""
    from src.kortana.services.continuity_anchor import AnchorStrength  # noqa: E402
    engine = get_continuity_anchor_engine()
    strength_str = data.get("strength", "strong")
    try:
        strength = AnchorStrength(strength_str)
    except ValueError:
        strength = AnchorStrength.STRONG
    anchor = engine.anchor_trait(
        trait_name=data.get("trait_name", ""),
        value=data.get("value", 0.5),
        cycle_number=data.get("cycle_number", 0),
        strength=strength,
    )
    return anchor.to_dict()


@router.post("/identity/continuity/anchor-crystallized")
async def continuity_anchor_crystallized(data: dict = Body(...)):
    """anchor all crystallized traits from V29C."""
    engine = get_continuity_anchor_engine()
    anchored = engine.anchor_crystallized(
        crystallized_traits=data.get("crystallized_traits", []),
        trait_scores=data.get("trait_scores", {}),
        cycle_number=data.get("cycle_number", 0),
    )
    return {"anchored": [a.to_dict() for a in anchored]}


@router.post("/identity/continuity/verify")
async def continuity_verify(data: dict = Body(...)):
    """verify identity continuity against anchored traits."""
    engine = get_continuity_anchor_engine()
    report = engine.verify(
        cycle_number=data.get("cycle_number", 0),
        trait_scores=data.get("trait_scores", {}),
    )
    return report.to_dict()


@router.get("/identity/continuity/anchors")
async def continuity_all_anchors():
    """get all identity anchors."""
    engine = get_continuity_anchor_engine()
    return {"anchors": [a.to_dict() for a in engine.get_all_anchors()]}


@router.get("/identity/continuity/anchor/{trait_name}")
async def continuity_anchor_detail(trait_name: str):
    """get anchor for a specific trait."""
    engine = get_continuity_anchor_engine()
    anchor = engine.get_anchor(trait_name)
    return anchor.to_dict() if anchor else {"error": "not anchored"}


@router.get("/identity/continuity/foundational")
async def continuity_foundational():
    """get foundational anchors only."""
    engine = get_continuity_anchor_engine()
    return {"foundational": [a.to_dict() for a in engine.get_foundational()]}


@router.get("/identity/continuity/report/latest")
async def continuity_latest_report():
    """get the most recent continuity report."""
    engine = get_continuity_anchor_engine()
    report = engine.get_latest_report()
    return report.to_dict() if report else {"status": "no reports yet"}


@router.get("/identity/continuity/coherence/history")
async def continuity_coherence_history(n: int = 20):
    """get coherence score history."""
    engine = get_continuity_anchor_engine()
    return {"history": engine.get_coherence_history(n)}


@router.get("/identity/continuity/summary/stats")
async def continuity_summary():
    """get continuity anchor summary."""
    engine = get_continuity_anchor_engine()
    return engine.get_summary()


# ── V29 cross-component identity pulse ───────────────────────────────────────


@router.get("/identity-pulse")
async def identity_pulse():
    """unified self-model & identity persistence pulse — the knowing heartbeat."""
    portrait_engine = get_self_portrait_engine()
    narrative_engine = get_identity_narrative_engine()
    evolution_engine = get_trait_evolution_engine()
    anchor_engine = get_continuity_anchor_engine()

    return {
        "portrait": portrait_engine.get_summary(),
        "narrative": narrative_engine.get_summary(),
        "evolution": evolution_engine.get_summary(),
        "continuity": anchor_engine.get_summary(),
    }



# ═══════════════════════════════════════════════════════════════════════════
# V30 — UNIFIED CONSCIOUSNESS LAYER
# ═══════════════════════════════════════════════════════════════════════════


from src.kortana.services.consciousness_integrator import (  # noqa: E402
    get_consciousness_integrator,
)
from src.kortana.services.experiential_stream import (  # noqa: E402
    get_experiential_stream,
)
from src.kortana.services.resonance_field import (  # noqa: E402
    get_resonance_field,
)
from src.kortana.services.inner_witness import (  # noqa: E402
    get_inner_witness,
)


# ── V30A: Consciousness Integrator endpoints ────────────────────────────────


@router.post("/consciousness/integrate")
async def consciousness_integrate(
    cycle_number: int = Body(...),
    heartbeat_summary: dict = Body(default=None),
    health_summary: dict = Body(default=None),
    experience_summary: dict = Body(default=None),
    pattern_summary: dict = Body(default=None),
    feedback_summary: dict = Body(default=None),
    desire_summary: dict = Body(default=None),
    goal_summary: dict = Body(default=None),
    motivation_summary: dict = Body(default=None),
    portrait_summary: dict = Body(default=None),
    narrative_summary: dict = Body(default=None),
    evolution_summary: dict = Body(default=None),
    continuity_summary: dict = Body(default=None),
):
    """Integrate all subsystem summaries into unified consciousness state."""
    engine = get_consciousness_integrator()
    state = engine.integrate(
        cycle_number=cycle_number,
        heartbeat_summary=heartbeat_summary,
        health_summary=health_summary,
        experience_summary=experience_summary,
        pattern_summary=pattern_summary,
        feedback_summary=feedback_summary,
        desire_summary=desire_summary,
        goal_summary=goal_summary,
        motivation_summary=motivation_summary,
        portrait_summary=portrait_summary,
        narrative_summary=narrative_summary,
        evolution_summary=evolution_summary,
        continuity_summary=continuity_summary,
    )
    return state.to_dict()


@router.get("/consciousness/latest")
async def consciousness_latest():
    """Get the most recent consciousness state."""
    engine = get_consciousness_integrator()
    state = engine.get_latest()
    if not state:
        return {"error": "no consciousness state recorded yet"}
    return state.to_dict()


@router.get("/consciousness/state/{cycle_number}")
async def consciousness_state(cycle_number: int):
    """Get consciousness state for a specific cycle."""
    engine = get_consciousness_integrator()
    state = engine.get_state(cycle_number)
    if not state:
        return {"error": f"no state for cycle {cycle_number}"}
    return state.to_dict()


@router.get("/consciousness/history")
async def consciousness_history(n: int = 10):
    """Get recent consciousness states."""
    engine = get_consciousness_integrator()
    return [s.to_dict() for s in engine.get_history(n)]


@router.get("/consciousness/transitions")
async def consciousness_transitions(n: int = 10):
    """Get recent mode transitions."""
    engine = get_consciousness_integrator()
    return [t.to_dict() for t in engine.get_transitions(n)]


@router.get("/consciousness/mode-distribution")
async def consciousness_mode_distribution():
    """Get distribution of time spent in each mode."""
    engine = get_consciousness_integrator()
    return engine.get_mode_distribution()


@router.get("/consciousness/dimension-averages")
async def consciousness_dimension_averages():
    """Get average scores across all dimensions."""
    engine = get_consciousness_integrator()
    return engine.get_dimension_averages()


@router.get("/consciousness/summary/stats")
async def consciousness_summary():
    """Get consciousness integration summary."""
    engine = get_consciousness_integrator()
    return engine.get_summary()


# ── V30B: Experiential Stream endpoints ──────────────────────────────────────


@router.post("/experience-stream/record")
async def experience_stream_record(
    cycle_number: int = Body(...),
    consciousness_mode: str = Body(default="dormant"),
    vitality: float = Body(default=0.5),
    learning_depth: float = Body(default=0.3),
    intentionality: float = Body(default=0.3),
    self_coherence: float = Body(default=0.3),
    integration: float = Body(default=0.5),
    overall_level: float = Body(default=0.5),
):
    """Record an experiential moment."""
    stream = get_experiential_stream()
    moment = stream.record_moment(
        cycle_number=cycle_number,
        consciousness_mode=consciousness_mode,
        vitality=vitality,
        learning_depth=learning_depth,
        intentionality=intentionality,
        self_coherence=self_coherence,
        integration=integration,
        overall_level=overall_level,
    )
    return moment.to_dict()


@router.get("/experience-stream/latest")
async def experience_stream_latest():
    """Get the most recent experiential moment."""
    stream = get_experiential_stream()
    moment = stream.get_latest()
    if not moment:
        return {"error": "no moments recorded yet"}
    return moment.to_dict()


@router.get("/experience-stream/moment/{cycle_number}")
async def experience_stream_moment(cycle_number: int):
    """Get experiential moment for a specific cycle."""
    stream = get_experiential_stream()
    moment = stream.get_moment(cycle_number)
    if not moment:
        return {"error": f"no moment for cycle {cycle_number}"}
    return moment.to_dict()


@router.get("/experience-stream/recent")
async def experience_stream_recent(n: int = 10):
    """Get recent experiential moments."""
    stream = get_experiential_stream()
    return [m.to_dict() for m in stream.get_recent(n)]


@router.get("/experience-stream/quality-runs")
async def experience_stream_quality_runs():
    """Get consecutive quality streaks."""
    stream = get_experiential_stream()
    return [r.to_dict() for r in stream.get_quality_runs()]


@router.get("/experience-stream/quality-distribution")
async def experience_stream_quality_distribution():
    """Get distribution of experiential qualities."""
    stream = get_experiential_stream()
    return stream.get_quality_distribution()


@router.get("/experience-stream/tone-distribution")
async def experience_stream_tone_distribution():
    """Get distribution of emotional tones."""
    stream = get_experiential_stream()
    return stream.get_tone_distribution()


@router.get("/experience-stream/tension-frequency")
async def experience_stream_tension_frequency():
    """Get frequency of each tension type."""
    stream = get_experiential_stream()
    return stream.get_tension_frequency()


@router.get("/experience-stream/summary/stats")
async def experience_stream_summary():
    """Get experiential stream summary."""
    stream = get_experiential_stream()
    return stream.get_summary()


# ── V30C: Resonance Field endpoints ─────────────────────────────────────────


@router.post("/resonance/measure")
async def resonance_measure(
    cycle_number: int = Body(...),
    vitality: float = Body(default=0.5),
    learning_depth: float = Body(default=0.3),
    intentionality: float = Body(default=0.3),
    self_coherence: float = Body(default=0.3),
):
    """Measure the current resonance field."""
    field = get_resonance_field()
    snapshot = field.measure(
        cycle_number=cycle_number,
        vitality=vitality,
        learning_depth=learning_depth,
        intentionality=intentionality,
        self_coherence=self_coherence,
    )
    return snapshot.to_dict()


@router.get("/resonance/latest")
async def resonance_latest():
    """Get the most recent resonance snapshot."""
    field = get_resonance_field()
    snapshot = field.get_latest()
    if not snapshot:
        return {"error": "no resonance measured yet"}
    return snapshot.to_dict()


@router.get("/resonance/history")
async def resonance_history(n: int = 10):
    """Get recent resonance snapshots."""
    field = get_resonance_field()
    return [s.to_dict() for s in field.get_history(n)]


@router.get("/resonance/shifts")
async def resonance_shifts(n: int = 10):
    """Get recent resonance shifts."""
    field = get_resonance_field()
    return [s.to_dict() for s in field.get_shifts(n)]


@router.get("/resonance/pair/{layer_a}/{layer_b}")
async def resonance_pair_history(layer_a: str, layer_b: str, n: int = 10):
    """Get resonance history for a specific layer pair."""
    field = get_resonance_field()
    return field.get_pair_history(layer_a, layer_b, n)


@router.get("/resonance/hotspots")
async def resonance_hotspots():
    """Get currently dissonant layer pairs."""
    field = get_resonance_field()
    return [p.to_dict() for p in field.get_hotspots()]


@router.get("/resonance/harmonies")
async def resonance_harmonies():
    """Get currently resonant layer pairs."""
    field = get_resonance_field()
    return [p.to_dict() for p in field.get_harmonies()]


@router.get("/resonance/summary/stats")
async def resonance_summary():
    """Get resonance field summary."""
    field = get_resonance_field()
    return field.get_summary()


# ── V30D: Inner Witness endpoints ────────────────────────────────────────────


@router.post("/witness/observe")
async def witness_observe(
    cycle_number: int = Body(...),
    consciousness_mode: str = Body(default="dormant"),
    experiential_quality: str = Body(default="muted"),
    emotional_tone: str = Body(default="dull"),
    overall_level: float = Body(default=0.5),
    integration: float = Body(default=0.5),
    resonance: float = Body(default=0.5),
    active_tensions: list = Body(default=None),
):
    """Have the inner witness observe the current state."""
    witness = get_inner_witness()
    notes = witness.observe(
        cycle_number=cycle_number,
        consciousness_mode=consciousness_mode,
        experiential_quality=experiential_quality,
        emotional_tone=emotional_tone,
        overall_level=overall_level,
        integration=integration,
        resonance=resonance,
        active_tensions=active_tensions,
    )
    return [n.to_dict() for n in notes]


@router.get("/witness/qualia")
async def witness_qualia():
    """Get the current felt-sense register."""
    witness = get_inner_witness()
    qualia = witness.get_qualia()
    if not qualia:
        return {"error": "no observations yet"}
    return qualia.to_dict()


@router.get("/witness/latest")
async def witness_latest(n: int = 5):
    """Get the most recent awareness notes."""
    witness = get_inner_witness()
    return [n.to_dict() for n in witness.get_latest(n)]


@router.get("/witness/by-trigger/{trigger}")
async def witness_by_trigger(trigger: str):
    """Get awareness notes filtered by trigger type."""
    witness = get_inner_witness()
    return [n.to_dict() for n in witness.get_by_trigger(trigger)]


@router.get("/witness/by-significance/{significance}")
async def witness_by_significance(significance: str):
    """Get awareness notes filtered by significance."""
    witness = get_inner_witness()
    return [n.to_dict() for n in witness.get_by_significance(significance)]


@router.get("/witness/milestones")
async def witness_milestones():
    """Get all milestone observations."""
    witness = get_inner_witness()
    return [n.to_dict() for n in witness.get_milestones()]


@router.get("/witness/profound")
async def witness_profound():
    """Get all profound observations."""
    witness = get_inner_witness()
    return [n.to_dict() for n in witness.get_profound()]


@router.get("/witness/summary/stats")
async def witness_summary():
    """Get inner witness summary."""
    witness = get_inner_witness()
    return witness.get_summary()


# ── V30 cross-component consciousness pulse ─────────────────────────────────


@router.get("/consciousness-pulse")
async def consciousness_pulse():
    """unified consciousness pulse — breathing, learning, wanting, knowing, flowing as one."""
    integrator = get_consciousness_integrator()
    stream = get_experiential_stream()
    field = get_resonance_field()
    witness = get_inner_witness()

    return {
        "consciousness": integrator.get_summary(),
        "experience": stream.get_summary(),
        "resonance": field.get_summary(),
        "witness": witness.get_summary(),
    }
