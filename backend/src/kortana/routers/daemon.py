"""
Autonomy Daemon API Router

Monitor local daemon state in embedded mode and report external daemon
liveness in split-service deployments.
"""

from __future__ import annotations

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
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
        compute_trends,
        check_deployment,
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
    from src.kortana.services.rollout_policy import check_deployment, surface_alerts
    from src.kortana.services.alert_publisher import get_alert_publisher

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
    from src.kortana.services.auto_actuator import ActuationDecision, decision_to_log_dict
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
    from src.kortana.services.rollout_policy import (
        check_deployment,
        compute_trends,
        surface_alerts,
    )
    from src.kortana.services.alert_publisher import get_alert_publisher

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
    from src.kortana.services.auto_actuator import (
        apply_actuation,
        decision_to_log_dict,
        evaluate_actuation,
    )
    from src.kortana.services.alert_publisher import get_alert_publisher

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
    from src.kortana.services.auto_actuator import (
        apply_actuation,
        decision_to_log_dict,
        evaluate_actuation,
    )
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
    from src.kortana.services.alert_publisher import get_alert_publisher
    from src.kortana.services.policy_versioning import get_policy_registry

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
    from src.kortana.services.human_override import get_override_manager
    from src.kortana.services.policy_comparison import compute_policy_comparison
    from src.kortana.services.policy_versioning import get_policy_registry
    from src.kortana.services.quorum_override import get_quorum_manager
    from src.kortana.services.drill_scheduler import get_drill_scheduler

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

