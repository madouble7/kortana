"""
Comprehensive unit tests for AlertService.

Tests alert creation, retrieval, filtering, resolution, and statistics
with extensive edge cases.
"""

import pytest

from src.kortana.modules.security.models.security_models import (
    AlertSeverity,
    AlertType,
)
from src.kortana.modules.security.services.alert_service import AlertService


class TestAlertService:
    """Comprehensive tests for alert service."""

    def test_create_alert_basic(self):
        """Test creating a basic security alert."""
        service = AlertService()
        
        alert = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="This is a test alert",
            source="test",
        )
        
        assert alert.id is not None
        assert alert.alert_type == AlertType.THREAT_DETECTED
        assert alert.severity == AlertSeverity.HIGH
        assert alert.title == "Test Alert"
        assert alert.description == "This is a test alert"
        assert alert.source == "test"
        assert alert.resolved is False
        assert alert.resolved_at is None
        assert alert.timestamp is not None

    def test_create_alert_with_metadata(self):
        """Test creating alert with metadata."""
        service = AlertService()
        
        metadata = {"ip": "192.168.1.1", "endpoint": "/api/test"}
        alert = service.create_alert(
            alert_type=AlertType.SUSPICIOUS_ACTIVITY,
            severity=AlertSeverity.MEDIUM,
            title="Suspicious Activity",
            description="Test",
            metadata=metadata,
        )
        
        assert alert.metadata == metadata

    def test_create_alert_without_metadata(self):
        """Test creating alert without metadata."""
        service = AlertService()
        
        alert = service.create_alert(
            alert_type=AlertType.VULNERABILITY_FOUND,
            severity=AlertSeverity.LOW,
            title="Test",
            description="Test",
        )
        
        assert alert.metadata == {}

    def test_create_alert_default_source(self):
        """Test that default source is 'system'."""
        service = AlertService()
        
        alert = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Test",
            description="Test",
        )
        
        assert alert.source == "system"

    def test_get_alert_exists(self):
        """Test retrieving an existing alert."""
        service = AlertService()
        
        alert = service.create_alert(
            alert_type=AlertType.VULNERABILITY_FOUND,
            severity=AlertSeverity.MEDIUM,
            title="Vulnerability Alert",
            description="Test vulnerability",
        )
        
        retrieved = service.get_alert(alert.id)
        assert retrieved is not None
        assert retrieved.id == alert.id
        assert retrieved.title == alert.title

    def test_get_alert_not_exists(self):
        """Test retrieving a non-existent alert."""
        service = AlertService()
        
        retrieved = service.get_alert("non-existent-id")
        assert retrieved is None

    def test_resolve_alert(self):
        """Test resolving an alert."""
        service = AlertService()
        
        alert = service.create_alert(
            alert_type=AlertType.SUSPICIOUS_ACTIVITY,
            severity=AlertSeverity.LOW,
            title="Suspicious Activity",
            description="Test activity",
        )
        
        resolved = service.resolve_alert(alert.id)
        assert resolved is not None
        assert resolved.resolved is True
        assert resolved.resolved_at is not None

    def test_resolve_non_existent_alert(self):
        """Test resolving a non-existent alert."""
        service = AlertService()
        
        resolved = service.resolve_alert("non-existent-id")
        assert resolved is None

    def test_resolve_already_resolved_alert(self):
        """Test resolving an already resolved alert."""
        service = AlertService()
        
        alert = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Test",
            description="Test",
        )
        
        # Resolve once
        first_resolve = service.resolve_alert(alert.id)
        first_resolved_at = first_resolve.resolved_at
        
        # Resolve again
        second_resolve = service.resolve_alert(alert.id)
        
        # Should update resolved_at timestamp
        assert second_resolve.resolved is True
        assert second_resolve.resolved_at != first_resolved_at

    def test_delete_alert_exists(self):
        """Test deleting an existing alert."""
        service = AlertService()
        
        alert = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Test",
            description="Test",
        )
        
        success = service.delete_alert(alert.id)
        assert success is True
        
        # Verify it's deleted
        retrieved = service.get_alert(alert.id)
        assert retrieved is None

    def test_delete_alert_not_exists(self):
        """Test deleting a non-existent alert."""
        service = AlertService()
        
        success = service.delete_alert("non-existent-id")
        assert success is False

    def test_get_all_alerts_empty(self):
        """Test getting all alerts when none exist."""
        service = AlertService()
        
        alerts = service.get_all_alerts()
        assert isinstance(alerts, list)
        assert len(alerts) == 0

    def test_get_all_alerts_multiple(self):
        """Test getting all alerts with multiple alerts."""
        service = AlertService()
        
        # Create multiple alerts
        for i in range(5):
            service.create_alert(
                alert_type=AlertType.THREAT_DETECTED,
                severity=AlertSeverity.HIGH,
                title=f"Alert {i}",
                description=f"Description {i}",
            )
        
        alerts = service.get_all_alerts()
        assert len(alerts) == 5

    def test_get_all_alerts_sorted_by_timestamp(self):
        """Test that alerts are sorted by timestamp (newest first)."""
        service = AlertService()
        
        alert1 = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="First",
            description="First",
        )
        
        alert2 = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Second",
            description="Second",
        )
        
        alerts = service.get_all_alerts()
        
        # Newest should be first
        assert alerts[0].id == alert2.id
        assert alerts[1].id == alert1.id

    def test_get_all_alerts_filter_by_severity(self):
        """Test filtering alerts by severity."""
        service = AlertService()
        
        service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.CRITICAL,
            title="Critical",
            description="Critical",
        )
        service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.LOW,
            title="Low",
            description="Low",
        )
        
        critical_alerts = service.get_all_alerts(severity=AlertSeverity.CRITICAL)
        assert len(critical_alerts) == 1
        assert critical_alerts[0].severity == AlertSeverity.CRITICAL

    def test_get_all_alerts_filter_by_type(self):
        """Test filtering alerts by type."""
        service = AlertService()
        
        service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Threat",
            description="Threat",
        )
        service.create_alert(
            alert_type=AlertType.VULNERABILITY_FOUND,
            severity=AlertSeverity.HIGH,
            title="Vulnerability",
            description="Vulnerability",
        )
        
        threat_alerts = service.get_all_alerts(alert_type=AlertType.THREAT_DETECTED)
        assert len(threat_alerts) == 1
        assert threat_alerts[0].alert_type == AlertType.THREAT_DETECTED

    def test_get_all_alerts_filter_by_resolved_status(self):
        """Test filtering alerts by resolved status."""
        service = AlertService()
        
        alert1 = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Unresolved",
            description="Unresolved",
        )
        alert2 = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Resolved",
            description="Resolved",
        )
        
        service.resolve_alert(alert2.id)
        
        active_alerts = service.get_all_alerts(resolved=False)
        assert len(active_alerts) == 1
        assert active_alerts[0].id == alert1.id
        
        resolved_alerts = service.get_all_alerts(resolved=True)
        assert len(resolved_alerts) == 1
        assert resolved_alerts[0].id == alert2.id

    def test_get_all_alerts_multiple_filters(self):
        """Test filtering alerts with multiple criteria."""
        service = AlertService()
        
        # Create various alerts
        service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.CRITICAL,
            title="Critical Threat",
            description="Test",
        )
        service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.LOW,
            title="Low Threat",
            description="Test",
        )
        service.create_alert(
            alert_type=AlertType.VULNERABILITY_FOUND,
            severity=AlertSeverity.CRITICAL,
            title="Critical Vuln",
            description="Test",
        )
        
        # Filter by type and severity
        filtered = service.get_all_alerts(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.CRITICAL,
        )
        
        assert len(filtered) == 1
        assert filtered[0].alert_type == AlertType.THREAT_DETECTED
        assert filtered[0].severity == AlertSeverity.CRITICAL

    def test_get_alert_statistics_empty(self):
        """Test statistics when no alerts exist."""
        service = AlertService()
        
        stats = service.get_alert_statistics()
        
        assert stats["total_alerts"] == 0
        assert stats["active_alerts"] == 0
        assert stats["resolved_alerts"] == 0
        assert stats["oldest_active_alert"] is None
        assert stats["latest_alert"] is None

    def test_get_alert_statistics_with_alerts(self):
        """Test getting alert statistics."""
        service = AlertService()
        
        # Create some test alerts
        alert1 = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.CRITICAL,
            title="Critical Threat",
            description="Test",
        )
        alert2 = service.create_alert(
            alert_type=AlertType.VULNERABILITY_FOUND,
            severity=AlertSeverity.HIGH,
            title="High Vulnerability",
            description="Test",
        )
        alert3 = service.create_alert(
            alert_type=AlertType.SUSPICIOUS_ACTIVITY,
            severity=AlertSeverity.MEDIUM,
            title="Medium Activity",
            description="Test",
        )
        
        # Resolve one
        service.resolve_alert(alert3.id)
        
        stats = service.get_alert_statistics()
        
        assert stats["total_alerts"] == 3
        assert stats["active_alerts"] == 2
        assert stats["resolved_alerts"] == 1
        assert stats["severity_distribution"]["critical"] == 1
        assert stats["severity_distribution"]["high"] == 1
        assert stats["severity_distribution"]["medium"] == 0  # Resolved, not counted
        assert stats["oldest_active_alert"] is not None
        assert stats["latest_alert"] is not None

    def test_get_alert_statistics_type_distribution(self):
        """Test type distribution in statistics."""
        service = AlertService()
        
        service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Threat 1",
            description="Test",
        )
        service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Threat 2",
            description="Test",
        )
        service.create_alert(
            alert_type=AlertType.VULNERABILITY_FOUND,
            severity=AlertSeverity.HIGH,
            title="Vuln",
            description="Test",
        )
        
        stats = service.get_alert_statistics()
        
        assert stats["type_distribution"]["threat_detected"] == 2
        assert stats["type_distribution"]["vulnerability_found"] == 1

    def test_clear_resolved_alerts(self):
        """Test clearing resolved alerts."""
        service = AlertService()
        
        # Create and resolve some alerts
        alert1 = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Alert 1",
            description="Test",
        )
        alert2 = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Alert 2",
            description="Test",
        )
        alert3 = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Alert 3",
            description="Test",
        )
        
        service.resolve_alert(alert1.id)
        service.resolve_alert(alert2.id)
        
        cleared_count = service.clear_resolved_alerts()
        
        assert cleared_count == 2
        
        # Verify they're gone
        assert service.get_alert(alert1.id) is None
        assert service.get_alert(alert2.id) is None
        assert service.get_alert(alert3.id) is not None

    def test_clear_resolved_alerts_none_resolved(self):
        """Test clearing resolved alerts when none are resolved."""
        service = AlertService()
        
        service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Alert",
            description="Test",
        )
        
        cleared_count = service.clear_resolved_alerts()
        assert cleared_count == 0

    def test_get_alert_history_empty(self):
        """Test getting alert history when empty."""
        service = AlertService()
        
        history = service.get_alert_history()
        assert isinstance(history, list)
        assert len(history) == 0

    def test_get_alert_history_with_alerts(self):
        """Test getting alert history."""
        service = AlertService()
        
        # Create some alerts
        for i in range(5):
            service.create_alert(
                alert_type=AlertType.THREAT_DETECTED,
                severity=AlertSeverity.HIGH,
                title=f"Alert {i}",
                description="Test",
            )
        
        history = service.get_alert_history()
        assert len(history) == 5

    def test_get_alert_history_with_limit(self):
        """Test getting alert history with limit."""
        service = AlertService()
        
        # Create many alerts
        for i in range(10):
            service.create_alert(
                alert_type=AlertType.THREAT_DETECTED,
                severity=AlertSeverity.HIGH,
                title=f"Alert {i}",
                description="Test",
            )
        
        history = service.get_alert_history(limit=5)
        assert len(history) == 5

    def test_alert_history_includes_resolved(self):
        """Test that alert history includes resolved alerts."""
        service = AlertService()
        
        alert = service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Test",
            description="Test",
        )
        
        service.resolve_alert(alert.id)
        
        history = service.get_alert_history()
        assert len(history) == 2  # Original + resolved version

    def test_alert_added_to_history_on_creation(self):
        """Test that alerts are added to history on creation."""
        service = AlertService()
        
        service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Test",
            description="Test",
        )
        
        history = service.get_alert_history()
        assert len(history) == 1

    def test_history_size_limit(self):
        """Test that history respects size limit."""
        service = AlertService()
        service._max_history_size = 10  # Set small limit for testing
        
        # Create more alerts than limit
        for i in range(15):
            service.create_alert(
                alert_type=AlertType.THREAT_DETECTED,
                severity=AlertSeverity.HIGH,
                title=f"Alert {i}",
                description="Test",
            )
        
        history = service.get_alert_history()
        
        # Should be trimmed to max size
        assert len(history) <= 10
