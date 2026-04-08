"""V6 — Alert Publisher: fans RolloutAlerts to webhooks, Slack, Discord, and log sinks.

Turns rollout policy alerts into real-world signals so regressions
hit the places you actually watch, not just an API response body.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

import httpx

from src.kortana.services.rollout_policy import RolloutAlert

logger = logging.getLogger("kortana.alert_publisher")


# ---------------------------------------------------------------------------
# Sink configuration
# ---------------------------------------------------------------------------


@dataclass
class AlertSinkConfig:
    """Configuration for all outbound alert sinks.

    Reads from environment variables so each deployment can wire
    whichever channels it uses without code changes.
    """

    slack_webhook_url: str | None = field(
        default_factory=lambda: os.getenv("KORTANA_SLACK_WEBHOOK_URL")
    )
    discord_webhook_url: str | None = field(
        default_factory=lambda: os.getenv("KORTANA_DISCORD_WEBHOOK_URL")
    )
    generic_webhook_urls: list[str] = field(default_factory=list)
    log_to_structured: bool = True  # always emit structured log entries

    def __post_init__(self) -> None:
        raw = os.getenv("KORTANA_ALERT_WEBHOOK_URLS", "")
        if raw:
            self.generic_webhook_urls = [
                u.strip() for u in raw.split(",") if u.strip()
            ]


_config: AlertSinkConfig | None = None


def get_sink_config() -> AlertSinkConfig:
    """Lazy-initialize the singleton AlertSinkConfig."""
    global _config
    if _config is None:
        _config = AlertSinkConfig()
    return _config


def reset_sink_config() -> None:
    """Reset for testing."""
    global _config
    _config = None


# ---------------------------------------------------------------------------
# Formatters — convert RolloutAlert to sink-specific payloads
# ---------------------------------------------------------------------------

_LEVEL_EMOJI = {"critical": "\U0001f6a8", "warning": "\u26a0\ufe0f", "info": "\u2139\ufe0f"}
_LEVEL_COLOR = {"critical": 0xFF0000, "warning": 0xFFA500, "info": 0x3498DB}


def _format_slack(alert: RolloutAlert) -> dict[str, Any]:
    """Format a RolloutAlert as a Slack incoming-webhook payload."""
    emoji = _LEVEL_EMOJI.get(alert.level, "")
    return {
        "text": f"{emoji} *[{alert.level.upper()}] {alert.title}*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{emoji} *[{alert.level.upper()}] {alert.title}*\n"
                        f"_{alert.category}_\n\n"
                        f"{alert.detail}\n\n"
                        f"*Recommended:* {alert.recommended_action}"
                    ),
                },
            }
        ],
    }


def _format_discord(alert: RolloutAlert) -> dict[str, Any]:
    """Format a RolloutAlert as a Discord webhook embed payload."""
    color = _LEVEL_COLOR.get(alert.level, 0x95A5A6)
    return {
        "embeds": [
            {
                "title": f"[{alert.level.upper()}] {alert.title}",
                "description": alert.detail,
                "color": color,
                "fields": [
                    {"name": "Category", "value": alert.category, "inline": True},
                    {"name": "Action", "value": alert.recommended_action, "inline": False},
                ],
                "footer": {"text": f"kor\u2019tana rollout policy \u00b7 {alert.timestamp}"},
            }
        ]
    }


def _format_generic(alert: RolloutAlert) -> dict[str, Any]:
    """Format a RolloutAlert as a generic JSON webhook body."""
    return {
        "source": "kortana-rollout-policy",
        "level": alert.level,
        "category": alert.category,
        "title": alert.title,
        "detail": alert.detail,
        "recommended_action": alert.recommended_action,
        "timestamp": alert.timestamp,
    }


# ---------------------------------------------------------------------------
# Publisher — fans alerts to all configured sinks
# ---------------------------------------------------------------------------


class AlertPublisher:
    """Publishes RolloutAlerts to every configured external sink.

    Each sink is best-effort: a failure in one sink does not block the others.
    """

    def __init__(self, config: AlertSinkConfig | None = None) -> None:
        self.config = config or get_sink_config()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def publish(self, alerts: list[RolloutAlert]) -> dict[str, Any]:
        """Publish a batch of alerts to all configured sinks.

        Returns a summary of what was sent and any failures.
        """
        results: dict[str, Any] = {
            "total_alerts": len(alerts),
            "sinks_attempted": 0,
            "sinks_succeeded": 0,
            "sinks_failed": 0,
            "failures": [],
        }

        if not alerts:
            return results

        # Structured logging — always enabled
        if self.config.log_to_structured:
            for alert in alerts:
                log_fn = logger.error if alert.level == "critical" else logger.warning
                log_fn(
                    "ROLLOUT_ALERT category=%s level=%s title=%s detail=%s",
                    alert.category, alert.level, alert.title, alert.detail,
                )

        client = await self._get_client()

        # Slack
        if self.config.slack_webhook_url:
            results["sinks_attempted"] += 1
            try:
                for alert in alerts:
                    payload = _format_slack(alert)
                    resp = await client.post(self.config.slack_webhook_url, json=payload)
                    resp.raise_for_status()
                results["sinks_succeeded"] += 1
            except Exception as exc:
                results["sinks_failed"] += 1
                results["failures"].append({"sink": "slack", "error": str(exc)})
                logger.error("Slack alert delivery failed: %s", exc)

        # Discord
        if self.config.discord_webhook_url:
            results["sinks_attempted"] += 1
            try:
                for alert in alerts:
                    payload = _format_discord(alert)
                    resp = await client.post(self.config.discord_webhook_url, json=payload)
                    resp.raise_for_status()
                results["sinks_succeeded"] += 1
            except Exception as exc:
                results["sinks_failed"] += 1
                results["failures"].append({"sink": "discord", "error": str(exc)})
                logger.error("Discord alert delivery failed: %s", exc)

        # Generic webhooks
        for url in self.config.generic_webhook_urls:
            results["sinks_attempted"] += 1
            try:
                for alert in alerts:
                    payload = _format_generic(alert)
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                results["sinks_succeeded"] += 1
            except Exception as exc:
                results["sinks_failed"] += 1
                results["failures"].append({"sink": url, "error": str(exc)})
                logger.error("Webhook alert delivery failed to %s: %s", url, exc)

        return results


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_publisher: AlertPublisher | None = None


def get_alert_publisher() -> AlertPublisher:
    """Get or create the singleton AlertPublisher."""
    global _publisher
    if _publisher is None:
        _publisher = AlertPublisher()
    return _publisher


def reset_alert_publisher() -> None:
    """Reset for testing."""
    global _publisher
    _publisher = None
