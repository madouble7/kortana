"""
Alert service for Kor'tana security module.
Manages security alerts and notifications.
"""

import uuid
from datetime import datetime
from typing import Any

from ..models.security_models import (
    AlertSeverity,
    AlertType,
    SecurityAlert,
)


class AlertService:
    """Service for managing security alerts."""

    def __init__(self):
        """Initialize alert service."""
        self._alerts: dict[str, SecurityAlert] = {}
        self._alert_history: list[SecurityAlert] = []
        self._max_history_size = 1000

    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: str,
        source: str = "system",
        metadata: dict[str, Any] | None = None,
    ) -> SecurityAlert:
        """
        Create a new security alert.

        Args:
            alert_type: Type of alert
            severity: Alert severity level
            title: Alert title
            description: Detailed alert description
            source: Source of the alert
            metadata: Additional metadata

        Returns:
            Created SecurityAlert
        """
        alert = SecurityAlert(
            id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            source=source,
            metadata=metadata or {},
            timestamp=datetime.utcnow(),
        )

        self._alerts[alert.id] = alert
        self._add_to_history(alert)

        return alert

    def get_alert(self, alert_id: str) -> SecurityAlert | None:
        """
        Get alert by ID.

        Args:
            alert_id: Alert identifier

        Returns:
            SecurityAlert or None if not found
        """
        return self._alerts.get(alert_id)

    def get_all_alerts(
        self,
        severity: AlertSeverity | None = None,
        alert_type: AlertType | None = None,
        resolved: bool | None = None,
    ) -> list[SecurityAlert]:
        """
        Get all alerts with optional filtering.

        Args:
            severity: Filter by severity level
            alert_type: Filter by alert type
            resolved: Filter by resolved status

        Returns:
            List of SecurityAlert objects
        """
        alerts = list(self._alerts.values())

        if severity is not None:
            alerts = [a for a in alerts if a.severity == severity]

        if alert_type is not None:
            alerts = [a for a in alerts if a.alert_type == alert_type]

        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)

        return alerts

    def resolve_alert(self, alert_id: str) -> SecurityAlert | None:
        """
        Mark an alert as resolved.

        Args:
            alert_id: Alert identifier

        Returns:
            Updated SecurityAlert or None if not found
        """
        alert = self._alerts.get(alert_id)
        if alert:
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            self._add_to_history(alert)

        return alert

    def delete_alert(self, alert_id: str) -> bool:
        """
        Delete an alert.

        Args:
            alert_id: Alert identifier

        Returns:
            True if deleted, False if not found
        """
        if alert_id in self._alerts:
            del self._alerts[alert_id]
            return True
        return False

    def get_alert_statistics(self) -> dict[str, Any]:
        """
        Get alert statistics.

        Returns:
            Dictionary with alert statistics
        """
        all_alerts = list(self._alerts.values())
        active_alerts = [a for a in all_alerts if not a.resolved]
        resolved_alerts = [a for a in all_alerts if a.resolved]

        severity_counts = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0,
        }

        for alert in active_alerts:
            severity_counts[alert.severity.value] += 1

        type_counts: dict[str, int] = {}
        for alert in active_alerts:
            type_counts[alert.alert_type.value] = (
                type_counts.get(alert.alert_type.value, 0) + 1
            )

        return {
            "total_alerts": len(all_alerts),
            "active_alerts": len(active_alerts),
            "resolved_alerts": len(resolved_alerts),
            "severity_distribution": severity_counts,
            "type_distribution": type_counts,
            "oldest_active_alert": (
                min(active_alerts, key=lambda x: x.timestamp).timestamp.isoformat()
                if active_alerts
                else None
            ),
            "latest_alert": (
                max(all_alerts, key=lambda x: x.timestamp).timestamp.isoformat()
                if all_alerts
                else None
            ),
        }

    def clear_resolved_alerts(self) -> int:
        """
        Clear all resolved alerts.

        Returns:
            Number of alerts cleared
        """
        resolved_ids = [aid for aid, alert in self._alerts.items() if alert.resolved]
        for aid in resolved_ids:
            del self._alerts[aid]
        return len(resolved_ids)

    def _add_to_history(self, alert: SecurityAlert) -> None:
        """
        Add alert to history.

        Args:
            alert: Alert to add to history
        """
        self._alert_history.append(alert)

        # Trim history if needed
        if len(self._alert_history) > self._max_history_size:
            self._alert_history = self._alert_history[-self._max_history_size :]

    def get_alert_history(self, limit: int = 100) -> list[SecurityAlert]:
        """
        Get alert history.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of SecurityAlert objects from history
        """
        return self._alert_history[-limit:]
