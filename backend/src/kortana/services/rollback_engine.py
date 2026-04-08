"""V8A — Rollback Engine: automatic rollback, cooldown windows, rate limiting.

When an actuation decision causes degraded canary or deploy state,
the engine automatically reverses the change. Cooldown windows prevent
oscillation, and max-change-per-window rules cap actuation frequency.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("kortana.rollback_engine")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_COOLDOWN_SECONDS = 300  # 5 minutes between mode changes
DEFAULT_MAX_CHANGES_PER_WINDOW = 3
DEFAULT_WINDOW_SECONDS = 3600  # 1-hour sliding window


@dataclass
class RollbackConfig:
    """Tuneable safety rails for the actuation loop."""

    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS
    max_changes_per_window: int = DEFAULT_MAX_CHANGES_PER_WINDOW
    window_seconds: int = DEFAULT_WINDOW_SECONDS
    auto_rollback_enabled: bool = True


# ---------------------------------------------------------------------------
# Cooldown guard
# ---------------------------------------------------------------------------


def check_cooldown(
    last_change_at: datetime | None,
    now: datetime | None = None,
    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS,
) -> tuple[bool, int]:
    """Check whether the cooldown period has elapsed since the last mode change.

    Returns (allowed, remaining_seconds).
    """
    if last_change_at is None:
        return True, 0

    now = now or datetime.utcnow()
    elapsed = (now - last_change_at).total_seconds()
    remaining = cooldown_seconds - int(elapsed)

    if remaining > 0:
        return False, remaining
    return True, 0


# ---------------------------------------------------------------------------
# Rate limiter (max changes per window)
# ---------------------------------------------------------------------------


def check_rate_limit(
    recent_decisions: list[dict[str, Any]],
    now: datetime | None = None,
    max_changes: int = DEFAULT_MAX_CHANGES_PER_WINDOW,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
) -> tuple[bool, int]:
    """Check whether the actuation rate limit has been exceeded.

    Counts non-hold decisions within the sliding window.
    Returns (allowed, changes_in_window).
    """
    now = now or datetime.utcnow()
    cutoff = now - timedelta(seconds=window_seconds)

    changes = 0
    for d in recent_decisions:
        action = d.get("action", "hold")
        if action == "hold":
            continue
        created = d.get("created_at")
        if created is None:
            continue
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except ValueError:
                continue
        if created >= cutoff:
            changes += 1

    return changes < max_changes, changes


# ---------------------------------------------------------------------------
# Rollback evaluation
# ---------------------------------------------------------------------------


@dataclass
class RollbackDecision:
    """Result of rollback evaluation."""

    should_rollback: bool
    from_mode: str
    to_mode: str
    trigger: str  # "degraded_canary", "deploy_blocked", "manual", "none"
    reasons: list[str] = field(default_factory=list)
    original_decision_hash: str | None = None


def evaluate_rollback(
    current_mode: str,
    pre_actuation_mode: str,
    latest_canary: dict[str, Any] | None,
    deploy_allowed: bool,
    *,
    config: RollbackConfig | None = None,
) -> RollbackDecision:
    """Evaluate whether the last actuation should be rolled back.

    Triggers:
    1. Latest canary is rejected after an escalation → rollback.
    2. Latest canary verdict is static after an escalation → rollback.
    3. Deployment is blocked after an escalation → rollback.
    4. De-escalation is never rolled back (it is already safety-bound).
    """
    config = config or RollbackConfig()

    if not config.auto_rollback_enabled:
        return RollbackDecision(
            should_rollback=False,
            from_mode=current_mode,
            to_mode=current_mode,
            trigger="none",
            reasons=["Auto-rollback is disabled"],
        )

    # Only rollback escalations — de-escalations are safety moves
    from src.kortana.services.auto_actuator import _mode_rank
    if _mode_rank(current_mode) <= _mode_rank(pre_actuation_mode):
        return RollbackDecision(
            should_rollback=False,
            from_mode=current_mode,
            to_mode=current_mode,
            trigger="none",
            reasons=["Current mode is not higher than pre-actuation — no rollback needed"],
        )

    # Check canary degradation
    if latest_canary is not None:
        status = latest_canary.get("promotion_status", "")
        verdict = latest_canary.get("verdict", "")

        if status == "rejected":
            return RollbackDecision(
                should_rollback=True,
                from_mode=current_mode,
                to_mode=pre_actuation_mode,
                trigger="degraded_canary",
                reasons=[
                    f"Canary rejected after escalation to {current_mode}",
                    f"Rolling back to {pre_actuation_mode}",
                ],
            )

        if verdict == "static":
            return RollbackDecision(
                should_rollback=True,
                from_mode=current_mode,
                to_mode=pre_actuation_mode,
                trigger="degraded_canary",
                reasons=[
                    f"Canary verdict static after escalation to {current_mode}",
                    f"Rolling back to {pre_actuation_mode}",
                ],
            )

    # Check deploy gate
    if not deploy_allowed:
        return RollbackDecision(
            should_rollback=True,
            from_mode=current_mode,
            to_mode=pre_actuation_mode,
            trigger="deploy_blocked",
            reasons=[
                f"Deploy gate blocked after escalation to {current_mode}",
                f"Rolling back to {pre_actuation_mode}",
            ],
        )

    return RollbackDecision(
        should_rollback=False,
        from_mode=current_mode,
        to_mode=current_mode,
        trigger="none",
        reasons=["Post-actuation state is healthy — no rollback needed"],
    )


# ---------------------------------------------------------------------------
# Gated actuation (combines cooldown + rate limit + rollback)
# ---------------------------------------------------------------------------


def gate_actuation(
    last_change_at: datetime | None,
    recent_decisions: list[dict[str, Any]],
    config: RollbackConfig | None = None,
    now: datetime | None = None,
) -> tuple[bool, list[str]]:
    """Pre-flight check: can a new actuation proceed?

    Returns (allowed, blocking_reasons).
    """
    config = config or RollbackConfig()
    now = now or datetime.utcnow()
    reasons: list[str] = []

    cool_ok, remaining = check_cooldown(last_change_at, now, config.cooldown_seconds)
    if not cool_ok:
        reasons.append(f"Cooldown active: {remaining}s remaining")

    rate_ok, count = check_rate_limit(
        recent_decisions, now, config.max_changes_per_window, config.window_seconds,
    )
    if not rate_ok:
        reasons.append(
            f"Rate limit exceeded: {count}/{config.max_changes_per_window} "
            f"changes in {config.window_seconds}s window"
        )

    return len(reasons) == 0, reasons


def apply_rollback(
    daemon: Any,
    rollback: RollbackDecision,
) -> bool:
    """Apply a rollback decision to the daemon.

    Returns True if mode was changed, False if no rollback needed.
    """
    if not rollback.should_rollback:
        return False

    old = daemon.default_approval_mode
    daemon.default_approval_mode = rollback.to_mode

    logger.warning(
        "ROLLBACK: %s -> %s (trigger=%s) — %s",
        old,
        rollback.to_mode,
        rollback.trigger,
        "; ".join(rollback.reasons),
    )
    return True
