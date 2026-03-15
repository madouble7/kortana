"""
Security data models for Kor'tana security module.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Security alert severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of security alerts."""

    THREAT_DETECTED = "threat_detected"
    VULNERABILITY_FOUND = "vulnerability_found"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    AUTHENTICATION_FAILURE = "authentication_failure"
    ANOMALY_DETECTED = "anomaly_detected"


class ThreatLevel(str, Enum):
    """Threat assessment levels."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityAlert(BaseModel):
    """Security alert model."""

    id: str = Field(default="", description="Unique alert identifier")
    alert_type: AlertType
    severity: AlertSeverity
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    source: str = Field(default="system", description="Source of the alert")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    resolved: bool = Field(default=False)
    resolved_at: datetime | None = None


class ThreatDetection(BaseModel):
    """Threat detection result model."""

    threat_level: ThreatLevel
    detected_threats: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    analysis_details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VulnerabilityScan(BaseModel):
    """Vulnerability scan result model."""

    scan_id: str
    scan_timestamp: datetime = Field(default_factory=datetime.utcnow)
    vulnerabilities_found: int = Field(ge=0)
    vulnerabilities: list[dict[str, Any]] = Field(default_factory=list)
    scan_duration_seconds: float = Field(ge=0.0)
    status: str = Field(default="completed")


class SecurityMetrics(BaseModel):
    """Security system metrics."""

    total_alerts: int = Field(ge=0)
    active_alerts: int = Field(ge=0)
    resolved_alerts: int = Field(ge=0)
    threats_detected: int = Field(ge=0)
    vulnerabilities_found: int = Field(ge=0)
    last_scan_timestamp: datetime | None = None
    system_health: str = Field(default="healthy")
    uptime_seconds: float = Field(ge=0.0)


class APIRequestLog(BaseModel):
    """API request logging for security monitoring."""

    request_id: str
    endpoint: str
    method: str
    client_ip: str
    user_agent: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    response_status: int = Field(ge=0)
    response_time_ms: float = Field(ge=0.0)
    threat_score: float = Field(ge=0.0, le=1.0, default=0.0)
