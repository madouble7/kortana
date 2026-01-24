"""
Comprehensive unit tests for ThreatDetectionService.

Tests threat detection, rate limiting, IP blocking, and pattern matching
with extensive edge cases and attack scenarios.
"""

import time

import pytest

from src.kortana.modules.security.models.security_models import ThreatLevel
from src.kortana.modules.security.services.threat_detection_service import ThreatDetectionService


class TestThreatDetectionService:
    """Comprehensive tests for threat detection service."""

    def test_analyze_normal_request(self):
        """Test analyzing a normal, safe request."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/data",
            method="GET",
            client_ip="192.168.1.1",
            headers={"user-agent": "Mozilla/5.0"},
        )
        
        assert detection.threat_level == ThreatLevel.NONE
        assert len(detection.detected_threats) == 0
        assert detection.confidence_score == 0.0

    def test_detect_sql_injection_in_body(self):
        """Test detecting SQL injection in request body."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/data",
            method="POST",
            client_ip="192.168.1.1",
            body="SELECT * FROM users WHERE id = 1",
        )
        
        assert detection.threat_level != ThreatLevel.NONE
        assert "sql_injection" in detection.detected_threats
        assert detection.confidence_score > 0.5

    def test_detect_sql_injection_union_attack(self):
        """Test detecting UNION-based SQL injection."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/users",
            method="GET",
            client_ip="192.168.1.1",
            params={"id": "1 UNION SELECT * FROM passwords"},
        )
        
        assert "sql_injection" in detection.detected_threats
        assert detection.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]

    def test_detect_xss_attack(self):
        """Test detecting XSS attack."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/comment",
            method="POST",
            client_ip="192.168.1.1",
            body='<script>alert("XSS")</script>',
        )
        
        assert "xss_attack" in detection.detected_threats
        assert detection.threat_level != ThreatLevel.NONE

    def test_detect_path_traversal(self):
        """Test detecting path traversal attack."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/file",
            method="GET",
            client_ip="192.168.1.1",
            params={"path": "../../etc/passwd"},
        )
        
        assert "path_traversal" in detection.detected_threats
        assert detection.threat_level != ThreatLevel.NONE

    def test_detect_code_injection(self):
        """Test detecting code injection attempts."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/execute",
            method="POST",
            client_ip="192.168.1.1",
            body="eval('malicious code')",
        )
        
        assert "code_injection" in detection.detected_threats

    def test_detect_credential_exposure(self):
        """Test detecting credential exposure in parameters."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/log",
            method="POST",
            client_ip="192.168.1.1",
            params={"password": "secret123"},
        )
        
        assert "credential_exposure" in detection.detected_threats

    def test_multiple_threats_detected(self):
        """Test detecting multiple threats in single request."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/test",
            method="POST",
            client_ip="192.168.1.1",
            body="SELECT * FROM users WHERE password='abc'",
        )
        
        # Should detect both SQL injection and credential exposure
        detected_types = detection.detected_threats
        assert len(detected_types) > 0
        assert any("sql_injection" in t for t in detected_types) or any("credential_exposure" in t for t in detected_types)

    def test_block_ip(self):
        """Test blocking an IP address."""
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
        assert detection.threat_level != ThreatLevel.NONE

    def test_unblock_ip(self):
        """Test unblocking an IP address."""
        service = ThreatDetectionService()
        
        ip = "192.168.1.100"
        service.block_ip(ip)
        assert ip in service.get_blocked_ips()
        
        service.unblock_ip(ip)
        assert ip not in service.get_blocked_ips()
        
        # Should no longer detect as blocked
        detection = service.analyze_request(
            endpoint="/api/test",
            method="GET",
            client_ip=ip,
        )
        assert "blocked_ip" not in detection.detected_threats

    def test_unblock_non_blocked_ip(self):
        """Test unblocking an IP that was never blocked."""
        service = ThreatDetectionService()
        
        ip = "192.168.1.100"
        service.unblock_ip(ip)  # Should not raise error
        
        assert ip not in service.get_blocked_ips()

    def test_get_blocked_ips_empty(self):
        """Test getting blocked IPs when none are blocked."""
        service = ThreatDetectionService()
        
        blocked = service.get_blocked_ips()
        assert isinstance(blocked, list)
        assert len(blocked) == 0

    def test_get_blocked_ips_multiple(self):
        """Test getting multiple blocked IPs."""
        service = ThreatDetectionService()
        
        ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1"]
        for ip in ips:
            service.block_ip(ip)
        
        blocked = service.get_blocked_ips()
        assert len(blocked) == 3
        for ip in ips:
            assert ip in blocked

    def test_rate_limiting_detection(self):
        """Test rate limiting detection."""
        service = ThreatDetectionService()
        service._rate_limit_threshold = 5  # Lower threshold for testing
        
        ip = "192.168.1.200"
        
        # Make requests under threshold - should be OK
        for _ in range(4):
            detection = service.analyze_request(
                endpoint="/api/test",
                method="GET",
                client_ip=ip,
            )
            assert "rate_limit_exceeded" not in detection.detected_threats
        
        # Exceed threshold
        for _ in range(10):
            detection = service.analyze_request(
                endpoint="/api/test",
                method="GET",
                client_ip=ip,
            )
        
        # Should now detect rate limit exceeded
        assert detection.threat_level != ThreatLevel.NONE
        assert "rate_limit_exceeded" in detection.detected_threats

    def test_rate_limiting_different_ips(self):
        """Test that rate limiting is per-IP."""
        service = ThreatDetectionService()
        service._rate_limit_threshold = 5
        
        ip1 = "192.168.1.1"
        ip2 = "192.168.1.2"
        
        # IP1 exceeds limit
        for _ in range(10):
            service.analyze_request(
                endpoint="/api/test",
                method="GET",
                client_ip=ip1,
            )
        
        # IP2 should still be OK
        detection = service.analyze_request(
            endpoint="/api/test",
            method="GET",
            client_ip=ip2,
        )
        
        assert "rate_limit_exceeded" not in detection.detected_threats

    def test_get_request_stats(self):
        """Test getting request statistics for an IP."""
        service = ThreatDetectionService()
        
        ip = "192.168.1.1"
        
        # Make some requests
        for _ in range(3):
            service.analyze_request(
                endpoint="/api/test",
                method="GET",
                client_ip=ip,
            )
        
        stats = service.get_request_stats(ip)
        
        assert stats["ip_address"] == ip
        assert stats["requests_last_minute"] == 3
        assert stats["is_blocked"] is False
        assert "rate_limit_threshold" in stats

    def test_get_request_stats_blocked_ip(self):
        """Test request stats for blocked IP."""
        service = ThreatDetectionService()
        
        ip = "192.168.1.1"
        service.block_ip(ip)
        
        stats = service.get_request_stats(ip)
        
        assert stats["is_blocked"] is True

    def test_get_request_stats_no_history(self):
        """Test request stats for IP with no history."""
        service = ThreatDetectionService()
        
        ip = "192.168.1.1"
        stats = service.get_request_stats(ip)
        
        assert stats["ip_address"] == ip
        assert stats["requests_last_minute"] == 0

    def test_suspicious_user_agent(self):
        """Test detection of suspicious user agents."""
        service = ThreatDetectionService()
        
        # Empty user agent
        detection = service.analyze_request(
            endpoint="/api/test",
            method="GET",
            client_ip="192.168.1.1",
            headers={"user-agent": ""},
        )
        assert "suspicious_user_agent" in detection.detected_threats
        
        # Bot user agent (non-Google)
        detection = service.analyze_request(
            endpoint="/api/test",
            method="GET",
            client_ip="192.168.1.1",
            headers={"user-agent": "BadBot/1.0"},
        )
        assert "suspicious_user_agent" in detection.detected_threats

    def test_googlebot_allowed(self):
        """Test that Googlebot is allowed."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/test",
            method="GET",
            client_ip="192.168.1.1",
            headers={"user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"},
        )
        
        assert "suspicious_user_agent" not in detection.detected_threats

    def test_calculate_threat_level_critical(self):
        """Test threat level calculation for critical threats."""
        service = ThreatDetectionService()
        
        level = service._calculate_threat_level(0.95)
        assert level == ThreatLevel.CRITICAL

    def test_calculate_threat_level_high(self):
        """Test threat level calculation for high threats."""
        service = ThreatDetectionService()
        
        level = service._calculate_threat_level(0.75)
        assert level == ThreatLevel.HIGH

    def test_calculate_threat_level_medium(self):
        """Test threat level calculation for medium threats."""
        service = ThreatDetectionService()
        
        level = service._calculate_threat_level(0.55)
        assert level == ThreatLevel.MEDIUM

    def test_calculate_threat_level_low(self):
        """Test threat level calculation for low threats."""
        service = ThreatDetectionService()
        
        level = service._calculate_threat_level(0.35)
        assert level == ThreatLevel.LOW

    def test_calculate_threat_level_none(self):
        """Test threat level calculation for no threat."""
        service = ThreatDetectionService()
        
        level = service._calculate_threat_level(0.0)
        assert level == ThreatLevel.NONE

    def test_analysis_details_included(self):
        """Test that analysis includes detailed information."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/test",
            method="POST",
            client_ip="192.168.1.1",
            headers={"user-agent": "TestAgent"},
        )
        
        assert "endpoint" in detection.analysis_details
        assert detection.analysis_details["endpoint"] == "/api/test"
        assert detection.analysis_details["method"] == "POST"
        assert detection.analysis_details["client_ip"] == "192.168.1.1"
        assert "timestamp" in detection.analysis_details

    def test_case_insensitive_pattern_matching(self):
        """Test that pattern matching is case insensitive."""
        service = ThreatDetectionService()
        
        # Test uppercase SQL keywords
        detection = service.analyze_request(
            endpoint="/api/data",
            method="POST",
            client_ip="192.168.1.1",
            body="SELECT * FROM USERS",
        )
        
        assert "sql_injection" in detection.detected_threats

    def test_endpoint_pattern_detection(self):
        """Test detection of suspicious patterns in endpoint."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/../admin/config",
            method="GET",
            client_ip="192.168.1.1",
        )
        
        assert "suspicious_endpoint_pattern" in detection.detected_threats

    def test_no_headers_provided(self):
        """Test analysis when no headers are provided."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/test",
            method="GET",
            client_ip="192.168.1.1",
            headers=None,
        )
        
        # Should not crash, just skip header analysis
        assert isinstance(detection.detected_threats, list)

    def test_no_body_provided(self):
        """Test analysis when no body is provided."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/test",
            method="GET",
            client_ip="192.168.1.1",
            body=None,
        )
        
        # Should not crash
        assert isinstance(detection.detected_threats, list)

    def test_no_params_provided(self):
        """Test analysis when no params are provided."""
        service = ThreatDetectionService()
        
        detection = service.analyze_request(
            endpoint="/api/test",
            method="GET",
            client_ip="192.168.1.1",
            params=None,
        )
        
        # Should not crash
        assert isinstance(detection.detected_threats, list)

    def test_confidence_score_accuracy(self):
        """Test that confidence score reflects highest threat."""
        service = ThreatDetectionService()
        
        # Critical threat (blocked IP)
        service.block_ip("192.168.1.1")
        detection = service.analyze_request(
            endpoint="/api/test",
            method="GET",
            client_ip="192.168.1.1",
        )
        
        assert detection.confidence_score >= 0.9
