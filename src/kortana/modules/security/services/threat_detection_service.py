"""
Threat detection service for Kor'tana.
Monitors and detects security threats in real-time.
"""

import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from ..models.security_models import (
    ThreatDetection,
    ThreatLevel,
)


class ThreatDetectionService:
    """Service for detecting security threats."""

    def __init__(self):
        """Initialize threat detection service."""
        self._request_history: dict[str, list[datetime]] = defaultdict(list)
        self._blocked_ips: set[str] = set()
        self._suspicious_patterns = [
            r"(?i)(union|select|insert|update|delete|drop|exec|script)",  # SQL injection
            r"<script[^>]*>.*?</script>",  # XSS
            r"\.\./",  # Path traversal
            r"(?i)(eval\(|exec\(|system\()",  # Code injection
            r"(?i)(password|token|api[_-]?key|secret)",  # Credential exposure
        ]
        self._rate_limit_threshold = 100  # requests per minute
        self._anomaly_threshold = 0.7  # threat score threshold

    def analyze_request(
        self,
        endpoint: str,
        method: str,
        client_ip: str,
        headers: dict[str, str] | None = None,
        body: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> ThreatDetection:
        """
        Analyze an API request for threats.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            client_ip: Client IP address
            headers: Request headers
            body: Request body
            params: Query parameters

        Returns:
            ThreatDetection result
        """
        detected_threats = []
        threat_scores = []

        # Check if IP is blocked
        if client_ip in self._blocked_ips:
            detected_threats.append("blocked_ip")
            threat_scores.append(1.0)

        # Check rate limiting
        rate_limit_threat = self._check_rate_limit(client_ip)
        if rate_limit_threat:
            detected_threats.append("rate_limit_exceeded")
            threat_scores.append(0.8)

        # Check for injection attacks
        injection_threats = self._detect_injection_attacks(endpoint, body, params)
        if injection_threats:
            detected_threats.extend(injection_threats)
            threat_scores.extend([0.9] * len(injection_threats))

        # Check headers for anomalies
        if headers:
            header_threats = self._analyze_headers(headers)
            if header_threats:
                detected_threats.extend(header_threats)
                threat_scores.extend([0.6] * len(header_threats))

        # Calculate overall threat level
        confidence_score = max(threat_scores) if threat_scores else 0.0
        threat_level = self._calculate_threat_level(confidence_score)

        return ThreatDetection(
            threat_level=threat_level,
            detected_threats=detected_threats,
            confidence_score=confidence_score,
            analysis_details={
                "endpoint": endpoint,
                "method": method,
                "client_ip": client_ip,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def _check_rate_limit(self, client_ip: str) -> bool:
        """
        Check if client IP exceeds rate limit.

        Args:
            client_ip: Client IP address

        Returns:
            True if rate limit exceeded
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        # Clean old requests
        self._request_history[client_ip] = [
            ts for ts in self._request_history[client_ip] if ts > cutoff
        ]

        # Add current request
        self._request_history[client_ip].append(now)

        # Check if limit exceeded
        return len(self._request_history[client_ip]) > self._rate_limit_threshold

    def _detect_injection_attacks(
        self,
        endpoint: str,
        body: str | None,
        params: dict[str, Any] | None,
    ) -> list[str]:
        """
        Detect injection attacks in request data.

        Args:
            endpoint: API endpoint
            body: Request body
            params: Query parameters

        Returns:
            List of detected injection attack types
        """
        threats = []

        # Check endpoint
        for pattern in self._suspicious_patterns:
            if re.search(pattern, endpoint):
                threats.append("suspicious_endpoint_pattern")
                break

        # Check body
        if body:
            for i, pattern in enumerate(self._suspicious_patterns):
                if re.search(pattern, body):
                    threat_type = self._get_threat_type(i)
                    if threat_type not in threats:
                        threats.append(threat_type)

        # Check parameters
        if params:
            for value in params.values():
                if isinstance(value, str):
                    for i, pattern in enumerate(self._suspicious_patterns):
                        if re.search(pattern, value):
                            threat_type = self._get_threat_type(i)
                            if threat_type not in threats:
                                threats.append(threat_type)

        return threats

    def _get_threat_type(self, pattern_index: int) -> str:
        """Get threat type from pattern index."""
        threat_types = [
            "sql_injection",
            "xss_attack",
            "path_traversal",
            "code_injection",
            "credential_exposure",
        ]
        return threat_types[pattern_index] if pattern_index < len(threat_types) else "unknown_threat"

    def _analyze_headers(self, headers: dict[str, str]) -> list[str]:
        """
        Analyze request headers for suspicious activity.

        Args:
            headers: Request headers

        Returns:
            List of detected threats in headers
        """
        threats = []

        # Check User-Agent
        user_agent = headers.get("user-agent", "").lower()
        if not user_agent or any(
            bot in user_agent for bot in ["bot", "crawler", "spider", "scraper"]
        ):
            if "bot" not in user_agent or "google" not in user_agent:  # Allow Googlebot
                threats.append("suspicious_user_agent")

        # Check for missing security headers in response (placeholder)
        # This would be checked on the response side

        return threats

    def _calculate_threat_level(self, confidence_score: float) -> ThreatLevel:
        """
        Calculate threat level from confidence score.

        Args:
            confidence_score: Confidence score (0-1)

        Returns:
            ThreatLevel enum
        """
        if confidence_score >= 0.9:
            return ThreatLevel.CRITICAL
        elif confidence_score >= 0.7:
            return ThreatLevel.HIGH
        elif confidence_score >= 0.5:
            return ThreatLevel.MEDIUM
        elif confidence_score >= 0.3:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.NONE

    def block_ip(self, ip_address: str) -> None:
        """
        Block an IP address.

        Args:
            ip_address: IP address to block
        """
        self._blocked_ips.add(ip_address)

    def unblock_ip(self, ip_address: str) -> None:
        """
        Unblock an IP address.

        Args:
            ip_address: IP address to unblock
        """
        self._blocked_ips.discard(ip_address)

    def get_blocked_ips(self) -> list[str]:
        """Get list of blocked IP addresses."""
        return list(self._blocked_ips)

    def get_request_stats(self, client_ip: str) -> dict[str, Any]:
        """
        Get request statistics for a client IP.

        Args:
            client_ip: Client IP address

        Returns:
            Dictionary with request statistics
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        recent_requests = [
            ts for ts in self._request_history[client_ip] if ts > cutoff
        ]

        return {
            "ip_address": client_ip,
            "requests_last_minute": len(recent_requests),
            "is_blocked": client_ip in self._blocked_ips,
            "rate_limit_threshold": self._rate_limit_threshold,
        }
