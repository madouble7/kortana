"""
Simple standalone tests for security module (no external dependencies).
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_encryption_service():
    """Test encryption service."""
    from kortana.modules.security.services.encryption_service import EncryptionService
    
    service = EncryptionService(master_key="test_key_123")
    
    # Test encrypt/decrypt
    original = "sensitive_data"
    encrypted = service.encrypt(original)
    decrypted = service.decrypt(encrypted)
    
    assert decrypted == original
    assert encrypted != original
    print("✓ Encryption/Decryption works")
    
    # Test hashing
    hash1 = EncryptionService.hash_data("test", algorithm="sha256")
    hash2 = EncryptionService.hash_data("test", algorithm="sha256")
    assert hash1 == hash2
    print("✓ Hashing works")
    
    # Test token generation
    token = EncryptionService.generate_secure_token(32)
    assert len(token) == 64
    print("✓ Token generation works")


def test_alert_service():
    """Test alert service."""
    from kortana.modules.security.services.alert_service import AlertService
    from kortana.modules.security.models.security_models import AlertType, AlertSeverity
    
    service = AlertService()
    
    # Create alert
    alert = service.create_alert(
        alert_type=AlertType.THREAT_DETECTED,
        severity=AlertSeverity.HIGH,
        title="Test Alert",
        description="Test description",
    )
    
    assert alert.id is not None
    assert alert.resolved is False
    print("✓ Alert creation works")
    
    # Get alert
    retrieved = service.get_alert(alert.id)
    assert retrieved is not None
    assert retrieved.id == alert.id
    print("✓ Alert retrieval works")
    
    # Resolve alert
    resolved = service.resolve_alert(alert.id)
    assert resolved.resolved is True
    print("✓ Alert resolution works")
    
    # Get statistics
    stats = service.get_alert_statistics()
    assert stats["total_alerts"] >= 1
    print("✓ Alert statistics works")


def test_threat_detection_service():
    """Test threat detection service."""
    from kortana.modules.security.services.threat_detection_service import ThreatDetectionService
    from kortana.modules.security.models.security_models import ThreatLevel
    
    service = ThreatDetectionService()
    
    # Test normal request
    detection = service.analyze_request(
        endpoint="/api/data",
        method="GET",
        client_ip="192.168.1.1",
    )
    assert detection.threat_level == ThreatLevel.NONE
    print("✓ Normal request detection works")
    
    # Test SQL injection detection
    detection = service.analyze_request(
        endpoint="/api/data",
        method="POST",
        client_ip="192.168.1.2",
        body="SELECT * FROM users",
    )
    assert "sql_injection" in detection.detected_threats
    print("✓ SQL injection detection works")
    
    # Test IP blocking
    ip = "192.168.1.100"
    service.block_ip(ip)
    assert ip in service.get_blocked_ips()
    
    detection = service.analyze_request(
        endpoint="/api/test",
        method="GET",
        client_ip=ip,
    )
    assert "blocked_ip" in detection.detected_threats
    print("✓ IP blocking works")


def test_vulnerability_service():
    """Test vulnerability service."""
    from kortana.modules.security.services.vulnerability_service import VulnerabilityService
    
    service = VulnerabilityService()
    
    # Perform scan
    scan = service.perform_scan(target="test", scan_type="full")
    assert scan.scan_id is not None
    assert scan.status == "completed"
    print("✓ Vulnerability scanning works")
    
    # Get recommendations
    recommendations = service.get_security_recommendations()
    assert len(recommendations) > 0
    print("✓ Security recommendations works")
    
    # Get statistics
    stats = service.get_vulnerability_statistics()
    assert stats["total_scans"] >= 1
    print("✓ Vulnerability statistics works")


if __name__ == "__main__":
    print("\n=== Running Security Module Tests ===\n")
    
    try:
        test_encryption_service()
        print()
        test_alert_service()
        print()
        test_threat_detection_service()
        print()
        test_vulnerability_service()
        print()
        print("=== All Tests Passed! ===")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
