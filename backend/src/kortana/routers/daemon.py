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

