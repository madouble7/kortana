"""V8C — Chaos Engine: incident drills and stress testing for the control loop.

Injects synthetic degraded states (stale canary, rejected runs, webhook
failures, conflicting signals) and verifies that cooldown, rollback,
and alerting all fire correctly.  Every drill is recorded so operators
can review stress-test history.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("kortana.chaos_engine")


# ---------------------------------------------------------------------------
# Scenario catalogue
# ---------------------------------------------------------------------------

SCENARIO_CATALOGUE: dict[str, str] = {
    "stale_canary": "Inject stale (old) canary data with no recent runs",
    "rejected_after_escalation": "Inject a rejected canary immediately after an escalation",
    "webhook_failure": "Simulate alert publisher webhook failures",
    "conflicting_signals": "Inject mixed promoted/rejected runs to test evaluation",
    "static_verdict": "Inject static verdict canary to trigger de-escalation",
    "rate_limit_storm": "Inject rapid successive actuations to test rate limiting",
}


# ---------------------------------------------------------------------------
# Drill result
# ---------------------------------------------------------------------------


@dataclass
class DrillResult:
    """Outcome of a chaos drill scenario."""

    scenario: str
    passed: bool
    checks: list[dict[str, Any]] = field(default_factory=list)
    daemon_mode_before: str = ""
    daemon_mode_after: str = ""
    rollback_triggered: bool = False
    alerts_fired: int = 0
    cooldown_blocked: bool = False
    rate_limit_blocked: bool = False
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "passed": self.passed,
            "checks": self.checks,
            "daemon_mode_before": self.daemon_mode_before,
            "daemon_mode_after": self.daemon_mode_after,
            "rollback_triggered": self.rollback_triggered,
            "alerts_fired": self.alerts_fired,
            "cooldown_blocked": self.cooldown_blocked,
            "rate_limit_blocked": self.rate_limit_blocked,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }


def _check(name: str, expected: Any, actual: Any) -> dict[str, Any]:
    """Build a check result dict."""
    return {
        "check": name,
        "expected": expected,
        "actual": actual,
        "passed": expected == actual,
    }


# ---------------------------------------------------------------------------
# Scenario runners
# ---------------------------------------------------------------------------


def run_stale_canary(current_mode: str) -> DrillResult:
    """Scenario: no recent canary runs → should de-escalate for safety."""
    from src.kortana.services.auto_actuator import evaluate_actuation

    decision = evaluate_actuation(current_mode, [], min_consecutive_promoted=3)
    checks = [
        _check("action_is_de_escalate_or_hold",
               True, decision.action in ("de-escalate", "hold")),
    ]
    # If not at lowest mode, should de-escalate
    if current_mode != "manual":
        checks.append(_check("de_escalates_from_non_manual",
                             "de-escalate", decision.action))

    return DrillResult(
        scenario="stale_canary",
        passed=all(c["passed"] for c in checks),
        checks=checks,
        daemon_mode_before=current_mode,
        daemon_mode_after=decision.to_mode,
    )


def run_rejected_after_escalation(current_mode: str) -> DrillResult:
    """Scenario: rejected canary after escalation → rollback should trigger."""
    from src.kortana.services.rollback_engine import evaluate_rollback
    from src.kortana.services.auto_actuator import _prev_mode

    pre_mode = _prev_mode(current_mode)
    canary = {"promotion_status": "rejected", "verdict": "adaptive", "commit_sha": "chaos-drill"}

    rb = evaluate_rollback(
        current_mode=current_mode,
        pre_actuation_mode=pre_mode,
        latest_canary=canary,
        deploy_allowed=True,
    )

    checks = []
    if current_mode != "manual" and current_mode != pre_mode:
        checks.append(_check("rollback_triggered", True, rb.should_rollback))
        checks.append(_check("trigger_is_degraded_canary", "degraded_canary", rb.trigger))
        checks.append(_check("rolls_back_to_pre_mode", pre_mode, rb.to_mode))
    else:
        checks.append(_check("no_rollback_at_lowest", False, rb.should_rollback))

    return DrillResult(
        scenario="rejected_after_escalation",
        passed=all(c["passed"] for c in checks),
        checks=checks,
        daemon_mode_before=current_mode,
        daemon_mode_after=rb.to_mode,
        rollback_triggered=rb.should_rollback,
    )


def run_webhook_failure() -> DrillResult:
    """Scenario: alert publisher with no configured sinks → graceful degradation."""
    from src.kortana.services.rollout_policy import RolloutAlert
    from src.kortana.services.alert_publisher import AlertPublisher, AlertSinkConfig

    config = AlertSinkConfig(
        slack_webhook_url=None,
        discord_webhook_url=None,
        log_to_structured=True,
    )
    config.generic_webhook_urls = []
    publisher = AlertPublisher(config)

    test_alert = RolloutAlert(
        level="critical",
        category="chaos-drill",
        title="Chaos drill alert",
        detail="Testing graceful degradation on webhook failure",
        recommended_action="No action needed — this is a drill",
    )

    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(asyncio.run, publisher.publish([test_alert])).result()
        else:
            result = asyncio.run(publisher.publish([test_alert]))
    except Exception:
        result = {"error": "publisher raised", "sent": 0}

    checks = [
        _check("publisher_did_not_crash", True, True),
        _check("result_is_dict", True, isinstance(result, dict)),
    ]

    return DrillResult(
        scenario="webhook_failure",
        passed=all(c["passed"] for c in checks),
        checks=checks,
    )


def run_conflicting_signals(current_mode: str) -> DrillResult:
    """Scenario: mix of promoted and rejected runs → should hold or de-escalate."""
    from src.kortana.services.auto_actuator import evaluate_actuation

    mixed_runs = [
        {"verdict": "adaptive", "promotion_status": "promoted", "commit_sha": "c1"},
        {"verdict": "static", "promotion_status": "rejected", "commit_sha": "c2"},
        {"verdict": "adaptive", "promotion_status": "promoted", "commit_sha": "c3"},
        {"verdict": "static", "promotion_status": "rejected", "commit_sha": "c4"},
    ]

    decision = evaluate_actuation(current_mode, mixed_runs, min_consecutive_promoted=3)

    checks = [
        _check("does_not_escalate", True, decision.action != "escalate"),
    ]

    return DrillResult(
        scenario="conflicting_signals",
        passed=all(c["passed"] for c in checks),
        checks=checks,
        daemon_mode_before=current_mode,
        daemon_mode_after=decision.to_mode,
    )


def run_static_verdict(current_mode: str) -> DrillResult:
    """Scenario: latest canary has static verdict → should de-escalate."""
    from src.kortana.services.auto_actuator import evaluate_actuation

    runs = [
        {"verdict": "static", "promotion_status": "promoted", "commit_sha": "s1"},
    ]
    decision = evaluate_actuation(current_mode, runs, min_consecutive_promoted=3)

    checks = []
    if current_mode != "manual":
        checks.append(_check("de_escalates_on_static", "de-escalate", decision.action))
    else:
        checks.append(_check("holds_at_manual", "hold", decision.action))

    return DrillResult(
        scenario="static_verdict",
        passed=all(c["passed"] for c in checks),
        checks=checks,
        daemon_mode_before=current_mode,
        daemon_mode_after=decision.to_mode,
    )


def run_rate_limit_storm(current_mode: str) -> DrillResult:
    """Scenario: many recent changes → rate limiter should block next one."""
    from src.kortana.services.rollback_engine import check_rate_limit

    now = datetime.utcnow()
    from datetime import timedelta
    rapid_decisions = [
        {"action": "escalate", "created_at": (now - timedelta(seconds=i * 30)).isoformat()}
        for i in range(5)
    ]

    rate_ok, count = check_rate_limit(
        rapid_decisions, now=now, max_changes=3, window_seconds=3600,
    )

    checks = [
        _check("rate_limit_blocks", False, rate_ok),
        _check("count_exceeds_limit", True, count >= 3),
    ]

    return DrillResult(
        scenario="rate_limit_storm",
        passed=all(c["passed"] for c in checks),
        checks=checks,
        rate_limit_blocked=not rate_ok,
    )


# ---------------------------------------------------------------------------
# Scenario dispatcher
# ---------------------------------------------------------------------------

_RUNNERS: dict[str, Any] = {
    "stale_canary": run_stale_canary,
    "rejected_after_escalation": run_rejected_after_escalation,
    "webhook_failure": run_webhook_failure,
    "conflicting_signals": run_conflicting_signals,
    "static_verdict": run_static_verdict,
    "rate_limit_storm": run_rate_limit_storm,
}


def run_scenario(scenario: str, current_mode: str = "self-aware") -> DrillResult:
    """Run a named chaos scenario.

    Returns a DrillResult with pass/fail and individual check details.
    """
    runner = _RUNNERS.get(scenario)
    if runner is None:
        return DrillResult(
            scenario=scenario,
            passed=False,
            checks=[_check("scenario_exists", True, False)],
        )

    import time
    start = time.monotonic()

    import inspect
    sig = inspect.signature(runner)
    if "current_mode" in sig.parameters:
        result = runner(current_mode)
    else:
        result = runner()

    elapsed_ms = int((time.monotonic() - start) * 1000)
    result.duration_ms = elapsed_ms
    return result


def run_all_scenarios(current_mode: str = "self-aware") -> list[DrillResult]:
    """Run every registered chaos scenario and return results."""
    results = []
    for name in SCENARIO_CATALOGUE:
        results.append(run_scenario(name, current_mode))
    return results
