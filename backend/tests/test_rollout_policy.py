"""Tests for V5 — enforced rollout policy."""

from __future__ import annotations

from src.kortana.services.rollout_policy import (
    AutonomyLevel,
    DeploymentDecision,
    EscalationDecision,
    check_deployment,
    check_escalation,
    compute_trends,
    surface_alerts,
)


# ---------------------------------------------------------------------------
# AutonomyLevel tests
# ---------------------------------------------------------------------------


class TestAutonomyLevel:
    """Test the ordered autonomy level enum."""

    def test_ordering(self) -> None:
        levels = AutonomyLevel.ordered()
        assert levels[0] == AutonomyLevel.PAUSED
        assert levels[-1] == AutonomyLevel.SELF_AWARE
        assert len(levels) == 6

    def test_rank(self) -> None:
        assert AutonomyLevel.PAUSED.rank() == 0
        assert AutonomyLevel.SELF_AWARE.rank() == 5

    def test_escalation_detection(self) -> None:
        assert AutonomyLevel.STANDARD.is_escalation_from(AutonomyLevel.CAUTIOUS)
        assert not AutonomyLevel.CAUTIOUS.is_escalation_from(AutonomyLevel.STANDARD)
        assert not AutonomyLevel.STANDARD.is_escalation_from(AutonomyLevel.STANDARD)


# ---------------------------------------------------------------------------
# Escalation gate tests
# ---------------------------------------------------------------------------


class TestCheckEscalation:
    """Test autonomy-level escalation gates."""

    def _promoted_runs(self, n: int) -> list[dict]:
        from datetime import datetime
        return [
            {
                "promotion_status": "promoted",
                "verdict": "adaptive",
                "created_at": datetime.utcnow().isoformat(),
                "promotion_reasons": ["All promotion criteria passed"],
                "commit_sha": f"abc{i}",
            }
            for i in range(n)
        ]

    def test_de_escalation_always_allowed(self) -> None:
        result = check_escalation("standard", "cautious", [])
        assert result.allowed is True
        assert "De-escalation" in result.reasons[0]

    def test_same_level_always_allowed(self) -> None:
        result = check_escalation("standard", "standard", [])
        assert result.allowed is True

    def test_no_runs_blocks_escalation(self) -> None:
        result = check_escalation("cautious", "standard", [])
        assert result.allowed is False
        assert any("No canary runs" in r for r in result.reasons)

    def test_insufficient_promoted_blocks(self) -> None:
        runs = self._promoted_runs(1)  # Need 2
        result = check_escalation("cautious", "standard", runs)
        assert result.allowed is False
        assert any("consecutive" in r.lower() for r in result.reasons)

    def test_sufficient_promoted_allows(self) -> None:
        runs = self._promoted_runs(3)
        result = check_escalation("cautious", "standard", runs)
        assert result.allowed is True
        assert any("approved" in r.lower() for r in result.reasons)

    def test_skip_levels_blocked(self) -> None:
        runs = self._promoted_runs(5)
        result = check_escalation("cautious", "aggressive", runs)
        assert result.allowed is False
        assert any("skip" in r.lower() for r in result.reasons)

    def test_rejected_run_blocks(self) -> None:
        from datetime import datetime
        runs = [
            {
                "promotion_status": "rejected",
                "verdict": "static",
                "created_at": datetime.utcnow().isoformat(),
                "promotion_reasons": ["Verdict is static"],
                "commit_sha": "abc0",
            }
        ]
        result = check_escalation("cautious", "standard", runs)
        assert result.allowed is False

    def test_unknown_level_fails(self) -> None:
        result = check_escalation("unknown_level", "standard", [])
        assert result.allowed is False
        assert any("Unknown" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# Deployment gate tests
# ---------------------------------------------------------------------------


class TestCheckDeployment:
    """Test deployment gate evaluation."""

    def test_no_run_blocks_deployment(self) -> None:
        result = check_deployment(None)
        assert result.allowed is False
        assert any("No canary run" in r for r in result.reasons)

    def test_adaptive_promoted_allows(self) -> None:
        from datetime import datetime
        run = {
            "verdict": "adaptive",
            "promotion_status": "promoted",
            "commit_sha": "abc123",
            "created_at": datetime.utcnow().isoformat(),
        }
        result = check_deployment(run)
        assert result.allowed is True
        assert result.verdict == "adaptive"
        assert result.promotion_status == "promoted"

    def test_static_verdict_blocks(self) -> None:
        from datetime import datetime
        run = {
            "verdict": "static",
            "promotion_status": "rejected",
            "commit_sha": "abc123",
            "created_at": datetime.utcnow().isoformat(),
        }
        result = check_deployment(run)
        assert result.allowed is False
        assert any("static" in r for r in result.reasons)

    def test_rejected_blocks(self) -> None:
        from datetime import datetime
        run = {
            "verdict": "adaptive",
            "promotion_status": "rejected",
            "commit_sha": "abc123",
            "created_at": datetime.utcnow().isoformat(),
        }
        result = check_deployment(run)
        assert result.allowed is False
        assert any("rejected" in r for r in result.reasons)

    def test_permissive_thresholds_pass(self) -> None:
        from datetime import datetime
        run = {
            "verdict": "static",
            "promotion_status": "rejected",
            "commit_sha": "abc123",
            "created_at": datetime.utcnow().isoformat(),
        }
        result = check_deployment(run, require_adaptive=False, require_promoted=False)
        assert result.allowed is True


# ---------------------------------------------------------------------------
# Trend analysis tests
# ---------------------------------------------------------------------------


class TestComputeTrends:
    """Test longitudinal trend computation."""

    def test_empty_runs(self) -> None:
        trends = compute_trends([])
        assert trends.total_runs == 0
        assert trends.adaptive_rate == 0.0
        assert trends.trend_direction == "stable"

    def test_all_adaptive_promoted(self) -> None:
        runs = [
            {"verdict": "adaptive", "promotion_status": "promoted",
             "score_shift_delta": 2.0, "goal_alignment_delta": 1.0,
             "outcome_growth": 0.05}
            for _ in range(10)
        ]
        trends = compute_trends(runs)
        assert trends.total_runs == 10
        assert trends.adaptive_rate == 1.0
        assert trends.promotion_rate == 1.0
        assert trends.consecutive_promoted == 10

    def test_mixed_verdicts(self) -> None:
        runs = [
            {"verdict": "adaptive", "promotion_status": "promoted"},
            {"verdict": "static", "promotion_status": "rejected"},
            {"verdict": "adaptive", "promotion_status": "promoted"},
            {"verdict": "adaptive", "promotion_status": "promoted"},
        ]
        trends = compute_trends(runs)
        assert trends.adaptive_count == 3
        assert trends.static_count == 1
        assert trends.consecutive_promoted == 1  # streak from most recent

    def test_consecutive_streak_breaks(self) -> None:
        runs = [
            {"verdict": "adaptive", "promotion_status": "promoted"},
            {"verdict": "adaptive", "promotion_status": "promoted"},
            {"verdict": "static", "promotion_status": "rejected"},
            {"verdict": "adaptive", "promotion_status": "promoted"},
        ]
        trends = compute_trends(runs)
        assert trends.consecutive_promoted == 2  # first two from top

    def test_trend_direction_improving(self) -> None:
        # Older runs static, newer runs promoted
        runs = [
            {"verdict": "adaptive", "promotion_status": "promoted"},
            {"verdict": "adaptive", "promotion_status": "promoted"},
            {"verdict": "static", "promotion_status": "rejected"},
            {"verdict": "static", "promotion_status": "rejected"},
        ]
        trends = compute_trends(runs)
        assert trends.trend_direction == "improving"

    def test_trend_direction_degrading(self) -> None:
        runs = [
            {"verdict": "static", "promotion_status": "rejected"},
            {"verdict": "static", "promotion_status": "rejected"},
            {"verdict": "adaptive", "promotion_status": "promoted"},
            {"verdict": "adaptive", "promotion_status": "promoted"},
        ]
        trends = compute_trends(runs)
        assert trends.trend_direction == "degrading"

    def test_series_chronological_order(self) -> None:
        runs = [
            {"verdict": "adaptive", "promotion_status": "promoted", "score_shift_delta": 3.0},
            {"verdict": "adaptive", "promotion_status": "promoted", "score_shift_delta": 1.0},
        ]
        trends = compute_trends(runs)
        # Reversed to chronological: older (1.0) first, newer (3.0) last
        assert trends.score_shift_trend == [1.0, 3.0]


# ---------------------------------------------------------------------------
# Alert surfacing tests
# ---------------------------------------------------------------------------


class TestSurfaceAlerts:
    """Test alert generation from rollout policy state."""

    def test_no_alerts_when_all_good(self) -> None:
        alerts = surface_alerts()
        assert len(alerts) == 0

    def test_escalation_blocked_alert(self) -> None:
        decision = EscalationDecision(
            allowed=False,
            current_level="cautious",
            requested_level="standard",
            reasons=["Need 2 promoted runs"],
            required_actions=["Run canary simulation"],
        )
        alerts = surface_alerts(escalation=decision)
        assert len(alerts) == 1
        assert alerts[0].category == "escalation_blocked"
        assert alerts[0].level == "warning"

    def test_deployment_blocked_alert(self) -> None:
        decision = DeploymentDecision(
            allowed=False,
            reasons=["Verdict is static"],
        )
        alerts = surface_alerts(deployment=decision)
        assert len(alerts) == 1
        assert alerts[0].category == "deployment_blocked"
        assert alerts[0].level == "critical"

    def test_regression_alerts(self) -> None:
        regs = [
            {"severity": "critical", "metric": "verdict", "message": "Flipped to static"},
            {"severity": "warning", "metric": "goal_alignment", "message": "Dropped"},
        ]
        alerts = surface_alerts(regressions=regs)
        assert len(alerts) == 2
        assert alerts[0].category == "regression"
        assert alerts[0].level == "critical"
        assert alerts[1].level == "warning"

    def test_degrading_trend_alert(self) -> None:
        from src.kortana.services.rollout_policy import TrendAnalysis
        trends = TrendAnalysis(
            total_runs=10, adaptive_count=4, static_count=6,
            promoted_count=3, rejected_count=7,
            adaptive_rate=0.4, promotion_rate=0.3,
            score_shift_trend=[], goal_alignment_trend=[], outcome_growth_trend=[],
            trend_direction="degrading", consecutive_promoted=0,
        )
        alerts = surface_alerts(trends=trends)
        assert len(alerts) >= 1
        cats = [a.category for a in alerts]
        assert "trend" in cats

    def test_no_promoted_streak_is_critical(self) -> None:
        from src.kortana.services.rollout_policy import TrendAnalysis
        trends = TrendAnalysis(
            total_runs=5, adaptive_count=2, static_count=3,
            promoted_count=0, rejected_count=5,
            adaptive_rate=0.4, promotion_rate=0.0,
            score_shift_trend=[], goal_alignment_trend=[], outcome_growth_trend=[],
            trend_direction="degrading", consecutive_promoted=0,
        )
        alerts = surface_alerts(trends=trends)
        critical_trends = [a for a in alerts if a.category == "trend" and a.level == "critical"]
        assert len(critical_trends) >= 1

    def test_allowed_decisions_no_alerts(self) -> None:
        esc = EscalationDecision(allowed=True, current_level="cautious", requested_level="standard")
        dep = DeploymentDecision(allowed=True, reasons=["All good"])
        alerts = surface_alerts(escalation=esc, deployment=dep)
        assert len(alerts) == 0
