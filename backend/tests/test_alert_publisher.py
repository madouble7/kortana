"""Tests for V6 — runtime enforcement: alert publisher, deploy gate, promotion board."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.services.alert_publisher import (
    AlertPublisher,
    AlertSinkConfig,
    _format_discord,
    _format_generic,
    _format_slack,
    reset_alert_publisher,
    reset_sink_config,
)
from src.kortana.services.rollout_policy import (
    RolloutAlert,
    check_deployment,
    check_escalation,
    surface_alerts,
)


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset module-level singletons between tests."""
    reset_sink_config()
    reset_alert_publisher()
    yield
    reset_sink_config()
    reset_alert_publisher()


def _make_alert(level: str = "warning", category: str = "test") -> RolloutAlert:
    return RolloutAlert(
        level=level,
        category=category,
        title="Test alert",
        detail="Detail text",
        recommended_action="Fix it",
    )


# ---------------------------------------------------------------------------
# AlertSinkConfig tests
# ---------------------------------------------------------------------------


class TestAlertSinkConfig:
    """Test sink configuration from environment."""

    def test_defaults(self) -> None:
        config = AlertSinkConfig()
        assert config.slack_webhook_url is None
        assert config.discord_webhook_url is None
        assert config.generic_webhook_urls == []
        assert config.log_to_structured is True

    def test_webhook_urls_from_env(self) -> None:
        with patch.dict("os.environ", {"KORTANA_ALERT_WEBHOOK_URLS": "https://a.com,https://b.com"}):
            config = AlertSinkConfig()
            assert len(config.generic_webhook_urls) == 2
            assert "https://a.com" in config.generic_webhook_urls

    def test_slack_from_env(self) -> None:
        with patch.dict("os.environ", {"KORTANA_SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"}):
            config = AlertSinkConfig()
            assert config.slack_webhook_url == "https://hooks.slack.com/test"


# ---------------------------------------------------------------------------
# Formatter tests
# ---------------------------------------------------------------------------


class TestFormatters:
    """Test alert payload formatters."""

    def test_slack_format(self) -> None:
        alert = _make_alert("critical")
        payload = _format_slack(alert)
        assert "text" in payload
        assert "CRITICAL" in payload["text"]
        assert "blocks" in payload

    def test_discord_format(self) -> None:
        alert = _make_alert("warning")
        payload = _format_discord(alert)
        assert "embeds" in payload
        assert len(payload["embeds"]) == 1
        assert payload["embeds"][0]["color"] == 0xFFA500

    def test_generic_format(self) -> None:
        alert = _make_alert("info")
        payload = _format_generic(alert)
        assert payload["source"] == "kortana-rollout-policy"
        assert payload["level"] == "info"
        assert payload["category"] == "test"
        assert payload["title"] == "Test alert"

    def test_discord_critical_color(self) -> None:
        alert = _make_alert("critical")
        payload = _format_discord(alert)
        assert payload["embeds"][0]["color"] == 0xFF0000

    def test_discord_info_color(self) -> None:
        alert = _make_alert("info")
        payload = _format_discord(alert)
        assert payload["embeds"][0]["color"] == 0x3498DB


# ---------------------------------------------------------------------------
# AlertPublisher tests
# ---------------------------------------------------------------------------


class TestAlertPublisher:
    """Test the alert publisher."""

    @pytest.mark.asyncio
    async def test_publish_empty_alerts(self) -> None:
        config = AlertSinkConfig()
        publisher = AlertPublisher(config)
        result = await publisher.publish([])
        assert result["total_alerts"] == 0
        assert result["sinks_attempted"] == 0
        await publisher.close()

    @pytest.mark.asyncio
    async def test_publish_structured_log_only(self) -> None:
        config = AlertSinkConfig()
        publisher = AlertPublisher(config)
        alerts = [_make_alert("critical"), _make_alert("warning")]
        result = await publisher.publish(alerts)
        assert result["total_alerts"] == 2
        assert result["sinks_attempted"] == 0
        assert result["sinks_succeeded"] == 0
        await publisher.close()

    @pytest.mark.asyncio
    async def test_publish_slack_success(self) -> None:
        config = AlertSinkConfig(slack_webhook_url="https://hooks.slack.com/test")
        publisher = AlertPublisher(config)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        with patch.object(publisher, "_get_client") as mock_client:
            client = AsyncMock()
            client.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = client
            result = await publisher.publish([_make_alert()])
            assert result["sinks_attempted"] == 1
            assert result["sinks_succeeded"] == 1
            assert result["sinks_failed"] == 0
        await publisher.close()

    @pytest.mark.asyncio
    async def test_publish_slack_failure(self) -> None:
        config = AlertSinkConfig(slack_webhook_url="https://hooks.slack.com/test")
        publisher = AlertPublisher(config)
        with patch.object(publisher, "_get_client") as mock_client:
            client = AsyncMock()
            client.post = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client.return_value = client
            result = await publisher.publish([_make_alert()])
            assert result["sinks_attempted"] == 1
            assert result["sinks_failed"] == 1
            assert len(result["failures"]) == 1
            assert result["failures"][0]["sink"] == "slack"
        await publisher.close()

    @pytest.mark.asyncio
    async def test_publish_discord_success(self) -> None:
        config = AlertSinkConfig(discord_webhook_url="https://discord.com/api/webhooks/test")
        publisher = AlertPublisher(config)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        with patch.object(publisher, "_get_client") as mock_client:
            client = AsyncMock()
            client.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = client
            result = await publisher.publish([_make_alert()])
            assert result["sinks_attempted"] == 1
            assert result["sinks_succeeded"] == 1
        await publisher.close()

    @pytest.mark.asyncio
    async def test_publish_generic_webhooks(self) -> None:
        config = AlertSinkConfig(generic_webhook_urls=["https://hook1.com", "https://hook2.com"])
        publisher = AlertPublisher(config)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        with patch.object(publisher, "_get_client") as mock_client:
            client = AsyncMock()
            client.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = client
            result = await publisher.publish([_make_alert()])
            assert result["sinks_attempted"] == 2
            assert result["sinks_succeeded"] == 2
        await publisher.close()

    @pytest.mark.asyncio
    async def test_publish_partial_failure(self) -> None:
        """One sink succeeds, another fails — both are reported."""
        config = AlertSinkConfig(
            slack_webhook_url="https://hooks.slack.com/test",
            discord_webhook_url="https://discord.com/api/webhooks/test",
        )
        publisher = AlertPublisher(config)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        call_count = 0

        async def _side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_response
            raise Exception("Discord down")

        with patch.object(publisher, "_get_client") as mock_client:
            client = AsyncMock()
            client.post = AsyncMock(side_effect=_side_effect)
            mock_client.return_value = client
            result = await publisher.publish([_make_alert()])
            assert result["sinks_attempted"] == 2
            assert result["sinks_succeeded"] == 1
            assert result["sinks_failed"] == 1
        await publisher.close()


# ---------------------------------------------------------------------------
# Daemon rollout gate tests
# ---------------------------------------------------------------------------


class TestDaemonRolloutGate:
    """Test that daemon mode changes are gated by rollout policy."""

    def test_gate_blocks_escalation_no_history(self) -> None:
        """With no adaptation history, escalation from self-aware to auto is blocked."""
        from src.kortana.services.autonomy_daemon import AutonomyDaemon

        with patch("src.kortana.services.autonomy_daemon.get_settings") as mock:
            mock.return_value = MagicMock(
                GITHUB_OWNER="test", GITHUB_REPO="test",
                KORTANA_GITHUB_MODE="disabled",
            )
            daemon = AutonomyDaemon()
            daemon.default_approval_mode = "self-aware"
            daemon._adaptation_history = []

            gate = daemon._check_rollout_gate("auto")
            assert gate["allowed"] is False
            assert gate["effective_mode"] == "self-aware"

    def test_gate_allows_de_escalation(self) -> None:
        """De-escalation always allowed."""
        from src.kortana.services.autonomy_daemon import AutonomyDaemon

        with patch("src.kortana.services.autonomy_daemon.get_settings") as mock:
            mock.return_value = MagicMock(
                GITHUB_OWNER="test", GITHUB_REPO="test",
                KORTANA_GITHUB_MODE="disabled",
            )
            daemon = AutonomyDaemon()
            daemon.default_approval_mode = "auto"
            daemon._adaptation_history = []

            gate = daemon._check_rollout_gate("self-aware")
            assert gate["allowed"] is True
            assert gate["effective_mode"] == "self-aware"

    def test_gate_allows_same_mode(self) -> None:
        """Same mode is always allowed."""
        from src.kortana.services.autonomy_daemon import AutonomyDaemon

        with patch("src.kortana.services.autonomy_daemon.get_settings") as mock:
            mock.return_value = MagicMock(
                GITHUB_OWNER="test", GITHUB_REPO="test",
                KORTANA_GITHUB_MODE="disabled",
            )
            daemon = AutonomyDaemon()
            daemon.default_approval_mode = "self-aware"

            gate = daemon._check_rollout_gate("self-aware")
            assert gate["allowed"] is True

    def test_guidance_mode_clamped_on_block(self) -> None:
        """When rollout gate blocks, _apply_operator_guidance clamps the mode."""
        from src.kortana.services.autonomy_daemon import AutonomyDaemon

        with patch("src.kortana.services.autonomy_daemon.get_settings") as mock:
            mock.return_value = MagicMock(
                GITHUB_OWNER="test", GITHUB_REPO="test",
                KORTANA_GITHUB_MODE="disabled",
            )
            daemon = AutonomyDaemon()
            daemon.default_approval_mode = "self-aware"
            daemon._adaptation_history = []

            from src.kortana.services.operator_directive_service import DirectiveSummary
            guidance = DirectiveSummary()
            guidance.approval_mode = "auto"  # try to escalate

            daemon._apply_operator_guidance(guidance)

            # The mode should be clamped to self-aware (not auto)
            assert daemon.operator_guidance["approval_mode"] == "self-aware"


# ---------------------------------------------------------------------------
# Integration: surface_alerts -> publisher pipeline
# ---------------------------------------------------------------------------


class TestAlertPipeline:
    """Test the end-to-end alert pipeline."""

    @pytest.mark.asyncio
    async def test_deploy_block_publishes_critical(self) -> None:
        """A blocked deployment produces a critical alert that can be published."""
        decision = check_deployment(None)
        assert decision.allowed is False

        alerts = surface_alerts(deployment=decision)
        assert len(alerts) >= 1
        assert any(a.level == "critical" for a in alerts)

        config = AlertSinkConfig()
        publisher = AlertPublisher(config)
        result = await publisher.publish(alerts)
        assert result["total_alerts"] >= 1
        await publisher.close()

    @pytest.mark.asyncio
    async def test_escalation_block_publishes_warning(self) -> None:
        """A blocked escalation produces alerts that can be published."""
        decision = check_escalation("cautious", "standard", [])
        assert decision.allowed is False

        alerts = surface_alerts(escalation=decision)
        assert len(alerts) >= 1

        config = AlertSinkConfig()
        publisher = AlertPublisher(config)
        result = await publisher.publish(alerts)
        assert result["total_alerts"] >= 1
        await publisher.close()
