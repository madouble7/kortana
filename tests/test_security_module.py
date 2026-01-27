"""
Tests for the Kor'tana security module.
"""

import pytest
from kortana.modules.security.models.security_models import (
    AlertSeverity,
    AlertType,
    ThreatLevel,
)
from kortana.modules.security.services.alert_service import AlertService
from kortana.modules.security.services.encryption_service import EncryptionService
from kortana.modules.security.services.threat_detection_service import (
    ThreatDetectionService,
)
from kortana.modules.security.services.vulnerability_service import (
    VulnerabilityService,
)


class TestEncryptionService:
    """Test encryption service functionality."""

    def test_encrypt_decrypt(self):
        """Test basic encryption and decryption."""
        service = EncryptionService(master_key="test_key_123")
        
        original_data = "sensitive_information"
        encrypted = service.encrypt(original_data)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == original_data
        assert encrypted != original_data

    def test_hash_data(self):
        """Test data hashing."""
        data = "test_data"
        hash1 = EncryptionService.hash_data(data, algorithm="sha256")
        hash2 = EncryptionService.hash_data(data, algorithm="sha256")
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 hex characters

    def test_generate_secure_token(self):
        """Test secure token generation."""
        token1 = EncryptionService.generate_secure_token(32)
        token2 = EncryptionService.generate_secure_token(32)
        
        assert token1 != token2
        assert len(token1) == 64  # 32 bytes = 64 hex characters

    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption."""
        service = EncryptionService(master_key="test_key_123")
        
        original_dict = {
            "api_key": "secret123",
            "password": "mypassword",
        }
        
        encrypted_dict = service.encrypt_dict(original_dict)
        decrypted_dict = service.decrypt_dict(encrypted_dict)
        
        assert decrypted_dict == original_dict


class TestAlertService:
    """Test alert service functionality."""

    def test_create_alert(self):
        """Test creating a security alert."""
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
        assert alert.resolved is False

    def test_get_alert(self):
        """Test retrieving an alert."""
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

    def test_get_alert_statistics(self):
        """Test getting alert statistics."""
        service = AlertService()
        
        # Create some test alerts
        service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity.CRITICAL,
            title="Critical Threat",
            description="Test",
        )
        service.create_alert(
            alert_type=AlertType.VULNERABILITY_FOUND,
            severity=AlertSeverity.HIGH,
            title="High Vulnerability",
            description="Test",
        )
        
        stats = service.get_alert_statistics()
        assert stats["total_alerts"] == 2
        assert stats["active_alerts"] == 2
        assert stats["severity_distribution"]["critical"] == 1
        assert stats["severity_distribution"]["high"] == 1


class TestThreatDetectionService:
    """Test threat detection service functionality."""

    def test_analyze_normal_request(self):
        """Test analyzing a normal request."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/data",
            method="GET",
            client_ip="192.168.1.1",
            headers={"user-agent": "Mozilla/5.0"},
        )
        
        assert detection.threat_level == ThreatLevel.NONE
        assert len(detection.detected_threats) == 0

    def test_detect_sql_injection(self):
        """Test detecting SQL injection attempts."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/data",
            method="GET",
            client_ip="192.168.1.1",
            body="SELECT * FROM users WHERE id = 1",
        )
        
        assert detection.threat_level != ThreatLevel.NONE
        assert "sql_injection" in detection.detected_threats

    def test_block_unblock_ip(self):
        """Test blocking and unblocking IPs."""
        service = ThreatDetectionService()
        
        ip = "192.168.1.100"
        service.block_ip(ip)
        
        assert ip in service.get_blocked_ips()
        
        # Should detect as threat
        detection = service.analyze_request(
            endpoint="/api/test",
            method="GET",
            client_ip=ip,
        )
        assert "blocked_ip" in detection.detected_threats
        
        service.unblock_ip(ip)
        assert ip not in service.get_blocked_ips()

    def test_rate_limiting(self):
        """Test rate limiting detection."""
        service = ThreatDetectionService()
        service._rate_limit_threshold = 5  # Lower threshold for testing
        
        ip = "192.168.1.200"
        
        # Make multiple requests
        for _ in range(10):
            detection = service.analyze_request(
                endpoint="/api/test",
                method="GET",
                client_ip=ip,
            )
        
        # Should detect rate limit exceeded
        assert detection.threat_level != ThreatLevel.NONE
        assert "rate_limit_exceeded" in detection.detected_threats


class TestVulnerabilityService:
    """Test vulnerability service functionality."""

    def test_perform_scan(self):
        """Test performing a vulnerability scan."""
        service = VulnerabilityService()
        
        scan = service.perform_scan(target="test_system", scan_type="full")
        
        assert scan.scan_id is not None
        assert scan.status == "completed"
        assert scan.vulnerabilities_found >= 0

    def test_get_scan(self):
        """Test retrieving a scan result."""
        service = VulnerabilityService()
        
        scan = service.perform_scan()
        retrieved = service.get_scan(scan.scan_id)
        
        assert retrieved is not None
        assert retrieved.scan_id == scan.scan_id

    def test_get_security_recommendations(self):
        """Test getting security recommendations."""
        service = VulnerabilityService()
        
        recommendations = service.get_security_recommendations()
        
        assert len(recommendations) > 0
        assert all("id" in rec for rec in recommendations)
        assert all("title" in rec for rec in recommendations)
        assert all("severity" in rec for rec in recommendations)

    def test_get_vulnerability_statistics(self):
        """Test getting vulnerability statistics."""
        service = VulnerabilityService()
        
        # Perform some scans
        service.perform_scan(scan_type="quick")
        service.perform_scan(scan_type="full")
        
        stats = service.get_vulnerability_statistics()
        
        assert stats["total_scans"] == 2
        assert "total_vulnerabilities" in stats
        assert "severity_distribution" in stats
