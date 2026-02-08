"""
Security middleware for automatic threat detection and request monitoring.
"""

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..models.security_models import AlertSeverity, AlertType
from ..services.alert_service import AlertService
from ..services.threat_detection_service import ThreatDetectionService

# Global service instances
_threat_detector = ThreatDetectionService()
_alert_service = AlertService()


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic security monitoring and threat detection.

    This middleware:
    - Monitors all incoming requests
    - Detects potential security threats
    - Creates alerts for suspicious activity
    - Blocks requests from blocked IPs
    - Tracks request metrics
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security checks."""
        start_time = time.time()

        # Get request details
        client_ip = request.client.host if request.client else "unknown"
        endpoint = str(request.url.path)
        method = request.method

        # Skip security checks for security endpoints to avoid recursion
        if endpoint.startswith("/security/"):
            return await call_next(request)

        # Get headers
        headers = dict(request.headers)

        # Analyze request for threats
        detection = _threat_detector.analyze_request(
            endpoint=endpoint,
            method=method,
            client_ip=client_ip,
            headers=headers,
        )

        # If critical threat detected, block the request
        if detection.threat_level.value == "critical":
            # Create critical alert
            _alert_service.create_alert(
                alert_type=AlertType.THREAT_DETECTED,
                severity=AlertSeverity.CRITICAL,
                title=f"Critical threat from {client_ip}",
                description=f"Threats: {', '.join(detection.detected_threats)}",
                source="security_middleware",
                metadata={
                    "endpoint": endpoint,
                    "method": method,
                    "ip": client_ip,
                    "threats": detection.detected_threats,
                },
            )

            # Return 403 Forbidden
            return Response(
                content='{"detail": "Access denied due to security threat"}',
                status_code=403,
                media_type="application/json",
            )

        # If high threat detected, create alert but allow request
        if detection.threat_level.value == "high" and detection.confidence_score > 0.7:
            _alert_service.create_alert(
                alert_type=AlertType.THREAT_DETECTED,
                severity=AlertSeverity.HIGH,
                title=f"High threat from {client_ip}",
                description=f"Threats: {', '.join(detection.detected_threats)}",
                source="security_middleware",
                metadata={
                    "endpoint": endpoint,
                    "method": method,
                    "ip": client_ip,
                    "threats": detection.detected_threats,
                },
            )

        # Process request
        response = await call_next(request)

        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000  # Convert to ms
        # TODO: Log or collect response_time_ms for metrics

        # Add security headers to response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Add custom security header with threat level
        response.headers["X-Security-Threat-Level"] = detection.threat_level.value

        return response


def get_threat_detector() -> ThreatDetectionService:
    """Get the global threat detector instance."""
    return _threat_detector


def get_alert_service() -> AlertService:
    """Get the global alert service instance."""
    return _alert_service
