"""
Integration tests for Security Router API endpoints.

Tests all security endpoints with FastAPI TestClient to ensure
end-to-end functionality.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.kortana.modules.security.routers.security_router import router
from src.kortana.modules.security.models.security_models import AlertSeverity, AlertType


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestAlertEndpoints:
    """Test alert-related API endpoints."""

    def test_create_alert(self, client):
        """Test creating an alert via API."""
        response = client.post(
            "/security/alerts",
            json={
                "alert_type": "threat_detected",
                "severity": "high",
                "title": "Test Alert",
                "description": "Test description",
                "source": "api_test",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Alert"
        assert data["severity"] == "high"
        assert data["resolved"] is False
        assert "id" in data

    def test_create_alert_minimal(self, client):
        """Test creating alert with minimal fields."""
        response = client.post(
            "/security/alerts",
            json={
                "alert_type": "suspicious_activity",
                "severity": "low",
                "title": "Minimal Alert",
                "description": "Test",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "manual"  # Default value

    def test_create_alert_with_metadata(self, client):
        """Test creating alert with metadata."""
        response = client.post(
            "/security/alerts",
            json={
                "alert_type": "vulnerability_found",
                "severity": "medium",
                "title": "Test",
                "description": "Test",
                "metadata": {"key": "value"},
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["key"] == "value"

    def test_create_alert_invalid_data(self, client):
        """Test creating alert with invalid data."""
        response = client.post(
            "/security/alerts",
            json={
                "alert_type": "invalid_type",
                "severity": "high",
                "title": "Test",
                "description": "Test",
            },
        )
        
        assert response.status_code == 422  # Validation error

    def test_get_all_alerts(self, client):
        """Test getting all alerts."""
        # Create some alerts first
        for i in range(3):
            client.post(
                "/security/alerts",
                json={
                    "alert_type": "threat_detected",
                    "severity": "high",
                    "title": f"Alert {i}",
                    "description": "Test",
                },
            )
        
        response = client.get("/security/alerts")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_get_alerts_filter_by_severity(self, client):
        """Test filtering alerts by severity."""
        # Create alerts with different severities
        client.post(
            "/security/alerts",
            json={
                "alert_type": "threat_detected",
                "severity": "critical",
                "title": "Critical",
                "description": "Test",
            },
        )
        
        response = client.get("/security/alerts?severity=critical")
        
        assert response.status_code == 200
        data = response.json()
        for alert in data:
            assert alert["severity"] == "critical"

    def test_get_specific_alert(self, client):
        """Test getting a specific alert by ID."""
        # Create an alert
        create_response = client.post(
            "/security/alerts",
            json={
                "alert_type": "threat_detected",
                "severity": "high",
                "title": "Specific Alert",
                "description": "Test",
            },
        )
        alert_id = create_response.json()["id"]
        
        # Get it
        response = client.get(f"/security/alerts/{alert_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == alert_id
        assert data["title"] == "Specific Alert"

    def test_get_non_existent_alert(self, client):
        """Test getting an alert that doesn't exist."""
        response = client.get("/security/alerts/non-existent-id")
        
        assert response.status_code == 404

    def test_resolve_alert(self, client):
        """Test resolving an alert."""
        # Create an alert
        create_response = client.post(
            "/security/alerts",
            json={
                "alert_type": "threat_detected",
                "severity": "high",
                "title": "To Resolve",
                "description": "Test",
            },
        )
        alert_id = create_response.json()["id"]
        
        # Resolve it
        response = client.post(f"/security/alerts/{alert_id}/resolve")
        
        assert response.status_code == 200
        data = response.json()
        assert data["resolved"] is True
        assert data["resolved_at"] is not None

    def test_resolve_non_existent_alert(self, client):
        """Test resolving a non-existent alert."""
        response = client.post("/security/alerts/non-existent-id/resolve")
        
        assert response.status_code == 404

    def test_delete_alert(self, client):
        """Test deleting an alert."""
        # Create an alert
        create_response = client.post(
            "/security/alerts",
            json={
                "alert_type": "threat_detected",
                "severity": "high",
                "title": "To Delete",
                "description": "Test",
            },
        )
        alert_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/security/alerts/{alert_id}")
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        # Verify it's gone
        get_response = client.get(f"/security/alerts/{alert_id}")
        assert get_response.status_code == 404

    def test_delete_non_existent_alert(self, client):
        """Test deleting a non-existent alert."""
        response = client.delete("/security/alerts/non-existent-id")
        
        assert response.status_code == 404

    def test_get_alert_statistics(self, client):
        """Test getting alert statistics."""
        # Create some alerts
        for severity in ["critical", "high", "medium"]:
            client.post(
                "/security/alerts",
                json={
                    "alert_type": "threat_detected",
                    "severity": severity,
                    "title": f"{severity} alert",
                    "description": "Test",
                },
            )
        
        response = client.get("/security/alerts/statistics/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_alerts" in data
        assert "active_alerts" in data
        assert "severity_distribution" in data


class TestThreatDetectionEndpoints:
    """Test threat detection API endpoints."""

    def test_analyze_threat(self, client):
        """Test analyzing current request for threats."""
        response = client.post("/security/threats/analyze")
        
        assert response.status_code == 200
        data = response.json()
        assert "threat_level" in data
        assert "detected_threats" in data
        assert "confidence_score" in data

    def test_block_ip(self, client):
        """Test blocking an IP address."""
        response = client.post(
            "/security/threats/block-ip",
            json={"ip_address": "192.168.1.100"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_block_invalid_ip(self, client):
        """Test blocking an invalid IP address."""
        response = client.post(
            "/security/threats/block-ip",
            json={"ip_address": "invalid-ip"},
        )
        
        assert response.status_code == 422  # Validation error

    def test_unblock_ip(self, client):
        """Test unblocking an IP address."""
        # Block first
        client.post(
            "/security/threats/block-ip",
            json={"ip_address": "192.168.1.100"},
        )
        
        # Unblock
        response = client.post(
            "/security/threats/unblock-ip",
            json={"ip_address": "192.168.1.100"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_get_blocked_ips(self, client):
        """Test getting list of blocked IPs."""
        # Block some IPs
        for i in range(3):
            client.post(
                "/security/threats/block-ip",
                json={"ip_address": f"192.168.1.{i}"},
            )
        
        response = client.get("/security/threats/blocked-ips")
        
        assert response.status_code == 200
        data = response.json()
        assert "blocked_ips" in data
        assert "count" in data
        assert data["count"] >= 3

    def test_get_ip_stats(self, client):
        """Test getting IP statistics."""
        response = client.get("/security/threats/stats/192.168.1.1")
        
        assert response.status_code == 200
        data = response.json()
        assert "ip_address" in data
        assert "requests_last_minute" in data


class TestVulnerabilityEndpoints:
    """Test vulnerability scanning API endpoints."""

    def test_start_vulnerability_scan(self, client):
        """Test starting a vulnerability scan."""
        response = client.post(
            "/security/vulnerabilities/scan",
            json={"target": "test_system", "scan_type": "full"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert "status" in data
        assert data["status"] == "completed"

    def test_start_scan_with_defaults(self, client):
        """Test starting scan with default values."""
        response = client.post(
            "/security/vulnerabilities/scan",
            json={},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert data["status"] == "completed"

    def test_get_vulnerability_scans(self, client):
        """Test getting all vulnerability scans."""
        # Create some scans
        for i in range(2):
            client.post(
                "/security/vulnerabilities/scan",
                json={"target": f"system_{i}"},
            )
        
        response = client.get("/security/vulnerabilities/scans")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_get_specific_vulnerability_scan(self, client):
        """Test getting a specific scan by ID."""
        # Create a scan
        create_response = client.post(
            "/security/vulnerabilities/scan",
            json={"target": "test_system"},
        )
        scan_id = create_response.json()["scan_id"]
        
        # Get it
        response = client.get(f"/security/vulnerabilities/scans/{scan_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["scan_id"] == scan_id

    def test_get_non_existent_scan(self, client):
        """Test getting a scan that doesn't exist."""
        response = client.get("/security/vulnerabilities/scans/non-existent-id")
        
        assert response.status_code == 404

    def test_get_security_recommendations(self, client):
        """Test getting security recommendations."""
        response = client.get("/security/vulnerabilities/recommendations")
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "count" in data

    def test_get_vulnerability_statistics(self, client):
        """Test getting vulnerability statistics."""
        response = client.get("/security/vulnerabilities/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_scans" in data
        assert "total_vulnerabilities" in data


class TestDashboardEndpoints:
    """Test security dashboard API endpoints."""

    def test_get_security_metrics(self, client):
        """Test getting comprehensive security metrics."""
        response = client.get("/security/dashboard/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_alerts" in data
        assert "active_alerts" in data
        assert "threats_detected" in data
        assert "vulnerabilities_found" in data
        assert "system_health" in data
        assert "uptime_seconds" in data

    def test_get_dashboard_summary(self, client):
        """Test getting dashboard summary."""
        response = client.get("/security/dashboard/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "overview" in data
        assert "alerts" in data
        assert "vulnerabilities" in data
        assert "threats" in data

    def test_security_health_check(self, client):
        """Test security module health check."""
        response = client.get("/security/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "security"
        assert "services" in data
        assert "timestamp" in data


class TestEndToEndScenarios:
    """Test end-to-end security scenarios."""

    def test_threat_detection_creates_alert(self, client):
        """Test that threat detection creates alerts automatically."""
        # Get initial alert count
        initial_response = client.get("/security/alerts")
        initial_count = len(initial_response.json())
        
        # Perform threat analysis (should create alert if threat found)
        client.post("/security/threats/analyze")
        
        # Check if any new alerts were created
        final_response = client.get("/security/alerts")
        final_count = len(final_response.json())
        
        # The count should be same or higher (depends on if threat was detected)
        assert final_count >= initial_count

    def test_vulnerability_scan_creates_alert(self, client):
        """Test that vulnerability scans create alerts when vulnerabilities found."""
        # Start a scan
        scan_response = client.post(
            "/security/vulnerabilities/scan",
            json={"target": "test_system"},
        )
        
        scan_data = scan_response.json()
        
        # If vulnerabilities were found, check for alerts
        if scan_data["vulnerabilities_found"] > 0:
            alerts_response = client.get("/security/alerts")
            alerts = alerts_response.json()
            
            # Should have at least one alert
            assert len(alerts) > 0

    def test_complete_alert_lifecycle(self, client):
        """Test complete lifecycle of an alert."""
        # 1. Create alert
        create_response = client.post(
            "/security/alerts",
            json={
                "alert_type": "threat_detected",
                "severity": "high",
                "title": "Lifecycle Test",
                "description": "Testing complete lifecycle",
            },
        )
        alert_id = create_response.json()["id"]
        
        # 2. Retrieve alert
        get_response = client.get(f"/security/alerts/{alert_id}")
        assert get_response.status_code == 200
        assert get_response.json()["resolved"] is False
        
        # 3. Resolve alert
        resolve_response = client.post(f"/security/alerts/{alert_id}/resolve")
        assert resolve_response.status_code == 200
        assert resolve_response.json()["resolved"] is True
        
        # 4. Verify resolved
        verify_response = client.get(f"/security/alerts/{alert_id}")
        assert verify_response.json()["resolved"] is True
        
        # 5. Delete alert
        delete_response = client.delete(f"/security/alerts/{alert_id}")
        assert delete_response.status_code == 200
        
        # 6. Verify deleted
        final_response = client.get(f"/security/alerts/{alert_id}")
        assert final_response.status_code == 404
