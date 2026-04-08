"""V4 — Continuous Eval: Promotion Gates & Regression Alarms.

Evaluates canary reports against promotion thresholds, persists runs for
longitudinal comparison, and raises alarms when a build regresses from
adaptive to static or key metrics degrade.

Workflow:  build → simulate → measure → compare → promote or reject.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Any

from src.kortana.services.canary_simulator import CanaryReport


# ---------------------------------------------------------------------------
# Promotion thresholds
# ---------------------------------------------------------------------------


@dataclass
class PromotionThresholds:
    """Configurable thresholds for deciding if a canary run is promotable."""

    verdict_must_be_adaptive: bool = True
    min_goal_alignment_delta: float = -0.5   # allow slight regression
    max_score_spread_delta: float = 15.0     # keep spread sane
    max_top3_churn_rate: float = 0.95        # >95% churn is instability
    min_outcome_growth: float = -0.05        # allow small negative


# ---------------------------------------------------------------------------
# Promotion gate evaluation
# ---------------------------------------------------------------------------


@dataclass
class PromotionResult:
    """Outcome of evaluating a canary report against promotion thresholds."""

    promoted: bool
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def evaluate_promotion(
    report: CanaryReport,
    thresholds: PromotionThresholds | None = None,
) -> PromotionResult:
    """Decide if a canary report meets promotion criteria.

    Returns a PromotionResult with pass/fail and human-readable reasons.
    """
    t = thresholds or PromotionThresholds()
    analysis = report.analysis
    reasons: list[str] = []
    warnings: list[str] = []

    if not analysis:
        return PromotionResult(promoted=False, reasons=["No analysis available"])

    verdict = analysis.get("verdict", "unknown")

    # 1. Verdict check
    if t.verdict_must_be_adaptive and verdict != "adaptive":
        reasons.append(f"Verdict is '{verdict}', expected 'adaptive'")

    # 2. Goal alignment
    goal_delta = analysis.get("goal_alignment", {}).get("delta", 0.0)
    if goal_delta < t.min_goal_alignment_delta:
        reasons.append(
            f"Goal alignment delta {goal_delta:.2f} below threshold "
            f"{t.min_goal_alignment_delta:.2f}"
        )
    elif goal_delta < 0:
        warnings.append(f"Goal alignment slightly regressed: {goal_delta:.2f}")

    # 3. Score spread
    spread_delta = analysis.get("score_spread", {}).get("delta", 0.0)
    if abs(spread_delta) > t.max_score_spread_delta:
        reasons.append(
            f"Score spread delta {spread_delta:.2f} exceeds bound "
            f"±{t.max_score_spread_delta:.2f}"
        )

    # 4. Top-3 churn (instability)
    churn = analysis.get("ranking_stability", {}).get("top3_churn_rate", 0.0)
    if churn > t.max_top3_churn_rate:
        reasons.append(
            f"Top-3 churn rate {churn:.3f} exceeds {t.max_top3_churn_rate:.3f}"
        )

    # 5. Outcome growth
    outcome_growth = analysis.get("outcome_adaptation", {}).get("growth", 0.0)
    if outcome_growth < t.min_outcome_growth:
        reasons.append(
            f"Outcome growth {outcome_growth:.4f} below threshold "
            f"{t.min_outcome_growth:.4f}"
        )

    promoted = len(reasons) == 0
    if promoted:
        reasons.append("All promotion criteria passed")

    return PromotionResult(promoted=promoted, reasons=reasons, warnings=warnings)


# ---------------------------------------------------------------------------
# Regression alarms — compare current run to previous
# ---------------------------------------------------------------------------


@dataclass
class RegressionAlarm:
    """A single alarm raised when a metric regresses between canary runs."""

    severity: str  # critical | warning
    metric: str
    message: str
    previous_value: Any = None
    current_value: Any = None


def detect_regressions(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
) -> list[RegressionAlarm]:
    """Compare current canary analysis to the previous run and flag regressions.

    Both arguments are the raw analysis dict from CanaryReport.
    """
    if previous is None:
        return []

    alarms: list[RegressionAlarm] = []

    # 1. Verdict regression: adaptive → static
    cur_verdict = current.get("verdict", "unknown")
    prev_verdict = previous.get("verdict", "unknown")
    if prev_verdict == "adaptive" and cur_verdict == "static":
        alarms.append(RegressionAlarm(
            severity="critical",
            metric="verdict",
            message="Canary verdict regressed from 'adaptive' to 'static'",
            previous_value=prev_verdict,
            current_value=cur_verdict,
        ))

    # 2. Goal alignment drop
    cur_goal = current.get("goal_alignment", {}).get("late_avg_in_top5", 0)
    prev_goal = previous.get("goal_alignment", {}).get("late_avg_in_top5", 0)
    if prev_goal > 0 and cur_goal < prev_goal - 0.5:
        alarms.append(RegressionAlarm(
            severity="warning",
            metric="goal_alignment",
            message=(
                f"Goal-aligned tasks in top-5 dropped from "
                f"{prev_goal:.1f} → {cur_goal:.1f}"
            ),
            previous_value=prev_goal,
            current_value=cur_goal,
        ))

    # 3. Score spread explosion
    cur_spread = current.get("score_spread", {}).get("late", 0)
    prev_spread = previous.get("score_spread", {}).get("late", 0)
    if prev_spread > 0 and cur_spread > prev_spread * 1.5:
        alarms.append(RegressionAlarm(
            severity="warning",
            metric="score_spread",
            message=(
                f"Late-cycle score spread widened from "
                f"{prev_spread:.1f} → {cur_spread:.1f} (>50% increase)"
            ),
            previous_value=prev_spread,
            current_value=cur_spread,
        ))

    # 4. Outcome growth collapse
    cur_growth = current.get("outcome_adaptation", {}).get("growth", 0)
    prev_growth = previous.get("outcome_adaptation", {}).get("growth", 0)
    if prev_growth > 0.01 and cur_growth <= 0:
        alarms.append(RegressionAlarm(
            severity="critical",
            metric="outcome_growth",
            message=(
                f"Outcome learning growth collapsed from "
                f"{prev_growth:.4f} → {cur_growth:.4f}"
            ),
            previous_value=prev_growth,
            current_value=cur_growth,
        ))

    # 5. Signal accumulation stall
    cur_signals = current.get("signal_accumulation", {}).get("net_new", 0)
    prev_signals = previous.get("signal_accumulation", {}).get("net_new", 0)
    if prev_signals > 3 and cur_signals == 0:
        alarms.append(RegressionAlarm(
            severity="warning",
            metric="signal_accumulation",
            message=(
                f"No new signals accumulated (was {prev_signals}, now {cur_signals})"
            ),
            previous_value=prev_signals,
            current_value=cur_signals,
        ))

    return alarms


# ---------------------------------------------------------------------------
# Persistence helpers (convert report → db-ready dict)
# ---------------------------------------------------------------------------


def report_to_db_dict(
    report: CanaryReport,
    triggered_by: str = "manual",
    promotion: PromotionResult | None = None,
) -> dict[str, Any]:
    """Convert a CanaryReport + optional PromotionResult to a flat dict
    suitable for creating a CanaryRun row."""
    analysis = report.analysis or {}

    # Git context
    commit_sha = _current_commit_sha()
    branch = _current_branch()

    # Snapshot summary: first + last
    summary: dict[str, Any] = {}
    if report.snapshots:
        first = report.snapshots[0]
        last = report.snapshots[-1]
        summary = {
            "first": {
                "cycle": first.cycle,
                "mean_score": first.mean_score,
                "score_spread": first.score_spread,
                "signals_active": first.signals_active,
                "top_3_ids": first.top_3_ids,
                "goal_aligned_in_top_5": first.goal_aligned_in_top_5,
            },
            "last": {
                "cycle": last.cycle,
                "mean_score": last.mean_score,
                "score_spread": last.score_spread,
                "signals_active": last.signals_active,
                "top_3_ids": last.top_3_ids,
                "goal_aligned_in_top_5": last.goal_aligned_in_top_5,
            },
        }

    promo_status = "pending"
    promo_reasons: list[str] | None = None
    if promotion:
        promo_status = "promoted" if promotion.promoted else "rejected"
        promo_reasons = promotion.reasons

    return {
        "commit_sha": commit_sha,
        "branch": branch,
        "total_cycles": report.total_cycles,
        "task_pool_size": report.task_pool_size,
        "verdict": analysis.get("verdict", "unknown"),
        "analysis": analysis,
        "score_shift_delta": analysis.get("score_shift", {}).get("delta"),
        "goal_alignment_delta": analysis.get("goal_alignment", {}).get("delta"),
        "outcome_growth": analysis.get("outcome_adaptation", {}).get("growth"),
        "top3_churn_rate": analysis.get("ranking_stability", {}).get("top3_churn_rate"),
        "score_spread_delta": analysis.get("score_spread", {}).get("delta"),
        "promotion_status": promo_status,
        "promotion_reasons": promo_reasons,
        "triggered_by": triggered_by,
        "snapshot_summary": summary,
    }


# ---------------------------------------------------------------------------
# Git context helpers
# ---------------------------------------------------------------------------


def _current_commit_sha() -> str | None:
    """Get the current HEAD commit SHA."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True,
            cwd=os.getenv("KORTANA_WORKSPACE_ROOT", "/workspace"),
            timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def _current_branch() -> str | None:
    """Get the current git branch."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True,
            cwd=os.getenv("KORTANA_WORKSPACE_ROOT", "/workspace"),
            timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None
