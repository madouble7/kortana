"""V5 — Enforced Rollout Policy.

Blocks autonomy-mode escalation when canary metrics regress, requires
promotion-gate pass before enabling stronger modes, computes retention
trends across canary history, and surfaces alerts outside the API layer
so regressions hit the places you actually watch.

This is the enforcement spine:
  canary pass → promote → escalate autonomy
  canary fail → reject → block + alert
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger("kortana.rollout_policy")


# ---------------------------------------------------------------------------
# Autonomy escalation levels
# ---------------------------------------------------------------------------


class AutonomyLevel(str, Enum):
    """Ordered autonomy modes — each higher level grants more power."""

    PAUSED = "paused"          # daemon halted
    SUPERVISED = "supervised"  # human approves every task
    CAUTIOUS = "cautious"     # auto-approve low-risk only
    STANDARD = "standard"     # auto-approve most tasks
    AGGRESSIVE = "aggressive"  # auto-approve all, self-healing
    SELF_AWARE = "self-aware"  # full autonomous with self-modification

    @classmethod
    def ordered(cls) -> list["AutonomyLevel"]:
        return [cls.PAUSED, cls.SUPERVISED, cls.CAUTIOUS, cls.STANDARD, cls.AGGRESSIVE, cls.SELF_AWARE]

    def rank(self) -> int:
        return self.ordered().index(self)

    def is_escalation_from(self, other: "AutonomyLevel") -> bool:
        return self.rank() > other.rank()


# ---------------------------------------------------------------------------
# Escalation gate — can we move to a higher autonomy mode?
# ---------------------------------------------------------------------------


@dataclass
class EscalationDecision:
    """Result of checking whether an autonomy escalation is allowed."""

    allowed: bool
    current_level: str
    requested_level: str
    reasons: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)


def check_escalation(
    current: str,
    requested: str,
    recent_runs: list[dict[str, Any]],
    *,
    min_consecutive_promoted: int = 2,
    max_hours_since_last_run: int = 24,
) -> EscalationDecision:
    """Decide whether an autonomy-level escalation is permitted.

    Rules:
    1. Cannot skip levels (must escalate one step at a time).
    2. Requires N consecutive promoted canary runs at the current level.
    3. Most recent run must be within max_hours_since_last_run.
    4. No critical regression alarms in the last run.
    """
    try:
        cur = AutonomyLevel(current)
        req = AutonomyLevel(requested)
    except ValueError:
        return EscalationDecision(
            allowed=False,
            current_level=current,
            requested_level=requested,
            reasons=[f"Unknown autonomy level: {current} or {requested}"],
        )

    reasons: list[str] = []
    actions: list[str] = []

    # Rule 0: De-escalation is always allowed
    if not req.is_escalation_from(cur):
        return EscalationDecision(
            allowed=True,
            current_level=current,
            requested_level=requested,
            reasons=["De-escalation or same level: always allowed"],
        )

    # Rule 1: No skipping levels
    if req.rank() - cur.rank() > 1:
        reasons.append(
            f"Cannot skip levels: {current} → {requested} "
            f"(must go through {AutonomyLevel.ordered()[cur.rank() + 1].value})"
        )
        actions.append(f"Escalate to {AutonomyLevel.ordered()[cur.rank() + 1].value} first")

    # Rule 2: Need recent canary runs
    if not recent_runs:
        reasons.append("No canary runs found — run POST /api/daemon/canary/evaluate first")
        actions.append("Run at least one canary simulation")
    else:
        # Check consecutive promoted
        promoted_streak = 0
        for run in recent_runs:
            if run.get("promotion_status") == "promoted":
                promoted_streak += 1
            else:
                break

        if promoted_streak < min_consecutive_promoted:
            reasons.append(
                f"Need {min_consecutive_promoted} consecutive promoted runs, "
                f"have {promoted_streak}"
            )
            remaining = min_consecutive_promoted - promoted_streak
            actions.append(f"Achieve {remaining} more promoted canary runs")

        # Rule 3: Recency check
        latest = recent_runs[0] if recent_runs else None
        if latest:
            created = latest.get("created_at")
            if isinstance(created, str):
                try:
                    ts = datetime.fromisoformat(created)
                    age_hours = (datetime.utcnow() - ts).total_seconds() / 3600
                    if age_hours > max_hours_since_last_run:
                        reasons.append(
                            f"Latest canary run is {age_hours:.1f}h old "
                            f"(max {max_hours_since_last_run}h)"
                        )
                        actions.append("Run a fresh canary simulation")
                except (ValueError, TypeError):
                    pass

        # Rule 4: No critical alarms in latest
        if latest:
            promo_reasons = latest.get("promotion_reasons") or []
            if latest.get("promotion_status") == "rejected":
                reasons.append(
                    f"Latest run was rejected: {'; '.join(promo_reasons[:2])}"
                )
                actions.append("Fix issues and achieve a promoted canary run")

    allowed = len(reasons) == 0
    if allowed:
        reasons.append(
            f"Escalation approved: {promoted_streak} consecutive promoted runs, "
            f"latest run is recent"
        )

    return EscalationDecision(
        allowed=allowed,
        current_level=current,
        requested_level=requested,
        reasons=reasons,
        required_actions=actions,
    )


# ---------------------------------------------------------------------------
# Deployment gate — can we deploy this build?
# ---------------------------------------------------------------------------


@dataclass
class DeploymentDecision:
    """Result of checking whether a deployment is allowed."""

    allowed: bool
    reasons: list[str] = field(default_factory=list)
    commit_sha: str | None = None
    verdict: str | None = None
    promotion_status: str | None = None


def check_deployment(
    latest_run: dict[str, Any] | None,
    *,
    require_adaptive: bool = True,
    require_promoted: bool = True,
    max_hours_since_run: int = 12,
) -> DeploymentDecision:
    """Decide whether the current build may be deployed.

    Blocks deployment when:
    - No canary run exists for the current commit
    - Verdict is not adaptive (if required)
    - Promotion status is rejected
    - Run is too old
    """
    if latest_run is None:
        return DeploymentDecision(
            allowed=False,
            reasons=["No canary run found — run canary/evaluate first"],
        )

    reasons: list[str] = []
    verdict = latest_run.get("verdict", "unknown")
    promo = latest_run.get("promotion_status", "pending")
    commit = latest_run.get("commit_sha")

    if require_adaptive and verdict != "adaptive":
        reasons.append(f"Verdict is '{verdict}', deployment requires 'adaptive'")

    if require_promoted and promo not in ("promoted", "skipped"):
        reasons.append(f"Promotion status is '{promo}', deployment requires 'promoted'")

    created = latest_run.get("created_at")
    if isinstance(created, str):
        try:
            ts = datetime.fromisoformat(created)
            age_hours = (datetime.utcnow() - ts).total_seconds() / 3600
            if age_hours > max_hours_since_run:
                reasons.append(
                    f"Canary run is {age_hours:.1f}h old (max {max_hours_since_run}h)"
                )
        except (ValueError, TypeError):
            pass

    allowed = len(reasons) == 0
    if allowed:
        reasons.append("All deployment criteria met")

    return DeploymentDecision(
        allowed=allowed,
        reasons=reasons,
        commit_sha=commit,
        verdict=verdict,
        promotion_status=promo,
    )


# ---------------------------------------------------------------------------
# Retention + trend analysis
# ---------------------------------------------------------------------------


@dataclass
class TrendAnalysis:
    """Longitudinal analysis across multiple canary runs."""

    total_runs: int
    adaptive_count: int
    static_count: int
    promoted_count: int
    rejected_count: int
    adaptive_rate: float  # 0.0 - 1.0
    promotion_rate: float  # 0.0 - 1.0
    score_shift_trend: list[float]   # per-run score_shift_delta
    goal_alignment_trend: list[float]
    outcome_growth_trend: list[float]
    trend_direction: str  # improving | stable | degrading
    consecutive_promoted: int  # current streak from most recent


def compute_trends(runs: list[dict[str, Any]]) -> TrendAnalysis:
    """Compute longitudinal trends across persisted canary runs.

    Expects runs ordered most-recent-first.
    """
    total = len(runs)
    if total == 0:
        return TrendAnalysis(
            total_runs=0, adaptive_count=0, static_count=0,
            promoted_count=0, rejected_count=0,
            adaptive_rate=0.0, promotion_rate=0.0,
            score_shift_trend=[], goal_alignment_trend=[], outcome_growth_trend=[],
            trend_direction="stable", consecutive_promoted=0,
        )

    adaptive = sum(1 for r in runs if r.get("verdict") == "adaptive")
    static = sum(1 for r in runs if r.get("verdict") == "static")
    promoted = sum(1 for r in runs if r.get("promotion_status") == "promoted")
    rejected = sum(1 for r in runs if r.get("promotion_status") == "rejected")

    # Trend arrays (reverse to get chronological order)
    score_shifts = [
        r.get("score_shift_delta", 0.0) or 0.0 for r in reversed(runs)
    ]
    goal_deltas = [
        r.get("goal_alignment_delta", 0.0) or 0.0 for r in reversed(runs)
    ]
    outcome_growths = [
        r.get("outcome_growth", 0.0) or 0.0 for r in reversed(runs)
    ]

    # Consecutive promoted streak (from most recent)
    streak = 0
    for r in runs:
        if r.get("promotion_status") == "promoted":
            streak += 1
        else:
            break

    # Direction: compare first half to second half
    direction = "stable"
    if total >= 4:
        mid = total // 2
        # Chronological: older half vs newer half
        older_promote_rate = sum(
            1 for r in runs[mid:] if r.get("promotion_status") == "promoted"
        ) / max(len(runs[mid:]), 1)
        newer_promote_rate = sum(
            1 for r in runs[:mid] if r.get("promotion_status") == "promoted"
        ) / max(len(runs[:mid]), 1)
        delta = newer_promote_rate - older_promote_rate
        if delta > 0.15:
            direction = "improving"
        elif delta < -0.15:
            direction = "degrading"

    return TrendAnalysis(
        total_runs=total,
        adaptive_count=adaptive,
        static_count=static,
        promoted_count=promoted,
        rejected_count=rejected,
        adaptive_rate=adaptive / total,
        promotion_rate=promoted / total,
        score_shift_trend=score_shifts,
        goal_alignment_trend=goal_deltas,
        outcome_growth_trend=outcome_growths,
        trend_direction=direction,
        consecutive_promoted=streak,
    )


# ---------------------------------------------------------------------------
# Alert surfacing — structured alerts for external consumption
# ---------------------------------------------------------------------------


@dataclass
class RolloutAlert:
    """An alert surfaced by the rollout policy for external consumption.

    These are designed to be pushed to logging, webhooks, or dashboards —
    not just returned from an API endpoint.
    """

    level: str      # critical | warning | info
    category: str   # escalation_blocked | deployment_blocked | regression | trend
    title: str
    detail: str
    recommended_action: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


def surface_alerts(
    escalation: EscalationDecision | None = None,
    deployment: DeploymentDecision | None = None,
    trends: TrendAnalysis | None = None,
    regressions: list[dict[str, Any]] | None = None,
) -> list[RolloutAlert]:
    """Collect and surface all active alerts from rollout policy state.

    Logs each alert and returns them for API/webhook/dashboard consumption.
    """
    alerts: list[RolloutAlert] = []

    # Escalation blocks
    if escalation and not escalation.allowed:
        alert = RolloutAlert(
            level="warning",
            category="escalation_blocked",
            title=f"Autonomy escalation blocked: {escalation.current_level} → {escalation.requested_level}",
            detail="; ".join(escalation.reasons),
            recommended_action="; ".join(escalation.required_actions) or "Run canary simulation",
        )
        alerts.append(alert)
        logger.warning("ROLLOUT ALERT: %s — %s", alert.title, alert.detail)

    # Deployment blocks
    if deployment and not deployment.allowed:
        alert = RolloutAlert(
            level="critical",
            category="deployment_blocked",
            title="Deployment blocked by canary policy",
            detail="; ".join(deployment.reasons),
            recommended_action="Achieve a promoted canary run before deploying",
        )
        alerts.append(alert)
        logger.error("ROLLOUT ALERT: %s — %s", alert.title, alert.detail)

    # Regression alarms
    if regressions:
        for reg in regressions:
            severity = reg.get("severity", "warning")
            alert = RolloutAlert(
                level=severity,
                category="regression",
                title=f"Regression detected: {reg.get('metric', 'unknown')}",
                detail=reg.get("message", ""),
                recommended_action="Investigate and fix before proceeding",
            )
            alerts.append(alert)
            if severity == "critical":
                logger.error("REGRESSION ALERT: %s", alert.detail)
            else:
                logger.warning("REGRESSION ALERT: %s", alert.detail)

    # Trend alerts
    if trends:
        if trends.trend_direction == "degrading":
            alert = RolloutAlert(
                level="warning",
                category="trend",
                title="Canary promotion rate is degrading",
                detail=(
                    f"Promotion rate: {trends.promotion_rate:.0%}, "
                    f"direction: {trends.trend_direction}, "
                    f"consecutive promoted: {trends.consecutive_promoted}"
                ),
                recommended_action="Review recent changes for autonomy regressions",
            )
            alerts.append(alert)
            logger.warning("TREND ALERT: %s", alert.detail)

        if trends.total_runs >= 3 and trends.consecutive_promoted == 0:
            alert = RolloutAlert(
                level="critical",
                category="trend",
                title="No promoted canary runs in recent history",
                detail=f"0 of last {min(trends.total_runs, 5)} runs were promoted",
                recommended_action="Canary quality has collapsed — investigate immediately",
            )
            alerts.append(alert)
            logger.error("TREND ALERT: %s", alert.detail)

    return alerts
