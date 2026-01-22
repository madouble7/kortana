"""
Security API router for Kor'tana security module.
Provides endpoints for security monitoring, alerts, and threat detection.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..models.security_models import (
    AlertSeverity,
    AlertType,
    SecurityAlert,
    SecurityMetrics,
    ThreatDetection,
    VulnerabilityScan,
)
from ..services.alert_service import AlertService
from ..services.threat_detection_service import ThreatDetectionService
from ..services.vulnerability_service import VulnerabilityService

# Initialize services
alert_service = AlertService()
threat_detection_service = ThreatDetectionService()
vulnerability_service = VulnerabilityService()

# System start time for uptime calculation
_system_start_time = datetime.utcnow()

router = APIRouter(
    prefix="/security",
    tags=["Security"],
)


# Request models
class CreateAlertRequest(BaseModel):
    alert_type: AlertType
    severity: AlertSeverity
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    source: str = Field(default="manual")
    metadata: dict[str, Any] = Field(default_factory=dict)


class VulnerabilityScanRequest(BaseModel):
    target: str = Field(default="system")
    scan_type: str = Field(default="full")


class IPAddressRequest(BaseModel):
    ip_address: str = Field(..., pattern=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


# Alert endpoints
@router.post("/alerts", response_model=SecurityAlert)
async def create_alert(request: CreateAlertRequest):
    """Create a new security alert."""
    alert = alert_service.create_alert(
        alert_type=request.alert_type,
        severity=request.severity,
        title=request.title,
        description=request.description,
        source=request.source,
        metadata=request.metadata,
    )
    return alert


@router.get("/alerts", response_model=list[SecurityAlert])
async def get_alerts(
    severity: AlertSeverity | None = None,
    alert_type: AlertType | None = None,
    resolved: bool | None = None,
):
    """Get all security alerts with optional filtering."""
    return alert_service.get_all_alerts(
        severity=severity,
        alert_type=alert_type,
        resolved=resolved,
    )


@router.get("/alerts/{alert_id}", response_model=SecurityAlert)
async def get_alert(alert_id: str):
    """Get a specific alert by ID."""
    alert = alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/resolve", response_model=SecurityAlert)
async def resolve_alert(alert_id: str):
    """Mark an alert as resolved."""
    alert = alert_service.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert."""
    success = alert_service.delete_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success", "message": "Alert deleted"}


@router.get("/alerts/statistics/summary")
async def get_alert_statistics():
    """Get alert statistics and summary."""
    return alert_service.get_alert_statistics()


# Threat detection endpoints
@router.post("/threats/analyze", response_model=ThreatDetection)
async def analyze_threat(request: Request):
    """Analyze current request for threats."""
    client_ip = request.client.host if request.client else "unknown"
    
    # Get request details
    headers = dict(request.headers)
    
    detection = threat_detection_service.analyze_request(
        endpoint=str(request.url.path),
        method=request.method,
        client_ip=client_ip,
        headers=headers,
    )
    
    # Create alert if threat detected
    if detection.threat_level.value != "none" and detection.confidence_score > 0.5:
        alert_service.create_alert(
            alert_type=AlertType.THREAT_DETECTED,
            severity=AlertSeverity(detection.threat_level.value) if detection.threat_level.value in ["low", "medium", "high", "critical"] else AlertSeverity.MEDIUM,
            title=f"Threat detected from {client_ip}",
            description=f"Threats: {', '.join(detection.detected_threats)}",
            source="threat_detection",
            metadata=detection.analysis_details,
        )
    
    return detection


@router.post("/threats/block-ip")
async def block_ip(request: IPAddressRequest):
    """Block an IP address."""
    threat_detection_service.block_ip(request.ip_address)
    return {
        "status": "success",
        "message": f"IP {request.ip_address} blocked",
    }


@router.post("/threats/unblock-ip")
async def unblock_ip(request: IPAddressRequest):
    """Unblock an IP address."""
    threat_detection_service.unblock_ip(request.ip_address)
    return {
        "status": "success",
        "message": f"IP {request.ip_address} unblocked",
    }


@router.get("/threats/blocked-ips")
async def get_blocked_ips():
    """Get list of blocked IP addresses."""
    return {
        "blocked_ips": threat_detection_service.get_blocked_ips(),
        "count": len(threat_detection_service.get_blocked_ips()),
    }


@router.get("/threats/stats/{ip_address}")
async def get_ip_stats(ip_address: str):
    """Get request statistics for an IP address."""
    return threat_detection_service.get_request_stats(ip_address)


# Vulnerability scanning endpoints
@router.post("/vulnerabilities/scan", response_model=VulnerabilityScan)
async def start_vulnerability_scan(request: VulnerabilityScanRequest):
    """Start a vulnerability scan."""
    scan_result = vulnerability_service.perform_scan(
        target=request.target,
        scan_type=request.scan_type,
    )
    
    # Create alert if vulnerabilities found
    if scan_result.vulnerabilities_found > 0:
        alert_service.create_alert(
            alert_type=AlertType.VULNERABILITY_FOUND,
            severity=AlertSeverity.HIGH if scan_result.vulnerabilities_found > 5 else AlertSeverity.MEDIUM,
            title=f"Vulnerability scan found {scan_result.vulnerabilities_found} issues",
            description=f"Scan ID: {scan_result.scan_id}",
            source="vulnerability_scanner",
            metadata={"scan_id": scan_result.scan_id},
        )
    
    return scan_result


@router.get("/vulnerabilities/scans", response_model=list[VulnerabilityScan])
async def get_vulnerability_scans(limit: int = 50):
    """Get all vulnerability scans."""
    return vulnerability_service.get_all_scans(limit=limit)


@router.get("/vulnerabilities/scans/{scan_id}", response_model=VulnerabilityScan)
async def get_vulnerability_scan(scan_id: str):
    """Get a specific vulnerability scan by ID."""
    scan = vulnerability_service.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.get("/vulnerabilities/recommendations")
async def get_security_recommendations():
    """Get security recommendations."""
    return {
        "recommendations": vulnerability_service.get_security_recommendations(),
        "count": len(vulnerability_service.get_security_recommendations()),
    }


@router.get("/vulnerabilities/statistics")
async def get_vulnerability_statistics():
    """Get vulnerability statistics."""
    return vulnerability_service.get_vulnerability_statistics()


# Security dashboard endpoints
@router.get("/dashboard/metrics", response_model=SecurityMetrics)
async def get_security_metrics():
    """Get comprehensive security metrics for dashboard."""
    alert_stats = alert_service.get_alert_statistics()
    vuln_stats = vulnerability_service.get_vulnerability_statistics()
    
    # Calculate uptime
    uptime = (datetime.utcnow() - _system_start_time).total_seconds()
    
    # Determine system health
    critical_alerts = sum(
        1 for alert in alert_service.get_all_alerts(resolved=False)
        if alert.severity == AlertSeverity.CRITICAL
    )
    system_health = "critical" if critical_alerts > 0 else "healthy"
    
    metrics = SecurityMetrics(
        total_alerts=alert_stats["total_alerts"],
        active_alerts=alert_stats["active_alerts"],
        resolved_alerts=alert_stats["resolved_alerts"],
        threats_detected=len(threat_detection_service.get_blocked_ips()),
        vulnerabilities_found=vuln_stats["total_vulnerabilities"],
        last_scan_timestamp=(
            datetime.fromisoformat(vuln_stats["latest_scan_timestamp"])
            if vuln_stats["latest_scan_timestamp"]
            else None
        ),
        system_health=system_health,
        uptime_seconds=uptime,
    )
    
    return metrics


@router.get("/dashboard/summary")
async def get_dashboard_summary():
    """Get comprehensive dashboard summary."""
    alert_stats = alert_service.get_alert_statistics()
    vuln_stats = vulnerability_service.get_vulnerability_statistics()
    blocked_ips = threat_detection_service.get_blocked_ips()
    
    recent_alerts = alert_service.get_all_alerts(resolved=False)[:5]
    recent_scans = vulnerability_service.get_all_scans(limit=5)
    
    uptime = (datetime.utcnow() - _system_start_time).total_seconds()
    
    return {
        "overview": {
            "system_status": "operational",
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
        },
        "alerts": {
            **alert_stats,
            "recent_alerts": [
                {
                    "id": alert.id,
                    "type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "timestamp": alert.timestamp.isoformat(),
                }
                for alert in recent_alerts
            ],
        },
        "vulnerabilities": {
            **vuln_stats,
            "recent_scans": [
                {
                    "scan_id": scan.scan_id,
                    "vulnerabilities_found": scan.vulnerabilities_found,
                    "timestamp": scan.scan_timestamp.isoformat(),
                }
                for scan in recent_scans
            ],
        },
        "threats": {
            "blocked_ips_count": len(blocked_ips),
            "blocked_ips": blocked_ips[:10],  # Limit to first 10
        },
    }


@router.get("/health")
async def security_health_check():
    """Security module health check."""
    return {
        "status": "healthy",
        "module": "security",
        "services": {
            "alert_service": "operational",
            "threat_detection": "operational",
            "vulnerability_scanner": "operational",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
