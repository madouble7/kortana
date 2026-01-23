#!/usr/bin/env python3
"""
Demo script showcasing the Kor'tana Security Module features.

This script demonstrates:
1. Encryption and secure data handling
2. Threat detection and analysis
3. Security alerts
4. Vulnerability scanning
5. Security dashboard metrics
"""

import os
import sys

# Set dummy API key for demo
os.environ["OPENAI_API_KEY"] = "demo_key"

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from src.kortana.modules.security.services.encryption_service import EncryptionService
from src.kortana.modules.security.services.alert_service import AlertService
from src.kortana.modules.security.services.threat_detection_service import (
    ThreatDetectionService,
)
from src.kortana.modules.security.services.vulnerability_service import (
    VulnerabilityService,
)
from src.kortana.modules.security.models.security_models import (
    AlertType,
    AlertSeverity,
)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def demo_encryption():
    """Demonstrate encryption features."""
    print_section("1. ENCRYPTION & SECURE DATA HANDLING")

    # Initialize encryption service
    encryption = EncryptionService(master_key="demo_master_key_123")

    # Encrypt sensitive data
    sensitive_data = "API_KEY_SECRET_12345"
    encrypted = encryption.encrypt(sensitive_data)
    print(f"Original data:  {sensitive_data}")
    print(f"Encrypted:      {encrypted[:50]}...")
    print()

    # Decrypt data
    decrypted = encryption.decrypt(encrypted)
    print(f"Decrypted:      {decrypted}")
    print(f"Match:          {'✓' if decrypted == sensitive_data else '✗'}")
    print()

    # Hash data
    password = "user_password_123"
    hash_sha256 = EncryptionService.hash_data(password, algorithm="sha256")
    print(f"Password hash (SHA256): {hash_sha256[:32]}...")
    print()

    # Generate secure token
    token = EncryptionService.generate_secure_token(32)
    print(f"Secure token (32 bytes): {token[:32]}...")
    print()

    # Encrypt dictionary
    credentials = {
        "api_key": "sk-1234567890",
        "secret": "my_secret_key",
    }
    encrypted_dict = encryption.encrypt_dict(credentials)
    print(f"Encrypted dictionary keys: {list(encrypted_dict.keys())}")
    print(f"Encrypted value sample:    {list(encrypted_dict.values())[0][:40]}...")


def demo_threat_detection():
    """Demonstrate threat detection features."""
    print_section("2. THREAT DETECTION & ANALYSIS")

    threat_detector = ThreatDetectionService()

    # Analyze normal request
    print("Analyzing normal request...")
    detection = threat_detector.analyze_request(
        endpoint="/api/users",
        method="GET",
        client_ip="192.168.1.10",
        headers={"user-agent": "Mozilla/5.0"},
    )
    print(f"  Threat Level:   {detection.threat_level.value}")
    print(f"  Confidence:     {detection.confidence_score:.2f}")
    print(f"  Threats:        {detection.detected_threats or 'None'}")
    print()

    # Analyze SQL injection attempt
    print("Analyzing SQL injection attempt...")
    detection = threat_detector.analyze_request(
        endpoint="/api/users",
        method="POST",
        client_ip="192.168.1.20",
        body="username=admin' OR '1'='1",
    )
    print(f"  Threat Level:   {detection.threat_level.value}")
    print(f"  Confidence:     {detection.confidence_score:.2f}")
    print(f"  Threats:        {', '.join(detection.detected_threats)}")
    print()

    # Block suspicious IP
    print("Blocking suspicious IP...")
    threat_detector.block_ip("192.168.1.100")
    blocked_ips = threat_detector.get_blocked_ips()
    print(f"  Blocked IPs:    {blocked_ips}")
    print()

    # Check request stats
    stats = threat_detector.get_request_stats("192.168.1.10")
    print(f"Request stats for 192.168.1.10:")
    print(f"  Requests/min:   {stats['requests_last_minute']}")
    print(f"  Is blocked:     {stats['is_blocked']}")
    print(f"  Rate limit:     {stats['rate_limit_threshold']}")


def demo_alerts():
    """Demonstrate alert management features."""
    print_section("3. SECURITY ALERTS")

    alert_service = AlertService()

    # Create critical alert
    print("Creating critical security alert...")
    alert1 = alert_service.create_alert(
        alert_type=AlertType.THREAT_DETECTED,
        severity=AlertSeverity.CRITICAL,
        title="Multiple SQL Injection Attempts",
        description="Detected 5 SQL injection attempts from IP 192.168.1.20",
        metadata={"ip": "192.168.1.20", "attempts": 5},
    )
    print(f"  Alert ID:       {alert1.id[:20]}...")
    print(f"  Type:           {alert1.alert_type.value}")
    print(f"  Severity:       {alert1.severity.value}")
    print(f"  Title:          {alert1.title}")
    print()

    # Create high severity alert
    print("Creating high severity alert...")
    alert2 = alert_service.create_alert(
        alert_type=AlertType.VULNERABILITY_FOUND,
        severity=AlertSeverity.HIGH,
        title="Missing Security Headers",
        description="API responses missing critical security headers",
    )
    print(f"  Alert ID:       {alert2.id[:20]}...")
    print(f"  Severity:       {alert2.severity.value}")
    print()

    # Get alert statistics
    print("Alert statistics:")
    stats = alert_service.get_alert_statistics()
    print(f"  Total alerts:   {stats['total_alerts']}")
    print(f"  Active:         {stats['active_alerts']}")
    print(f"  Resolved:       {stats['resolved_alerts']}")
    print(f"  Critical:       {stats['severity_distribution']['critical']}")
    print(f"  High:           {stats['severity_distribution']['high']}")
    print()

    # Resolve an alert
    print(f"Resolving alert {alert2.id[:20]}...")
    resolved = alert_service.resolve_alert(alert2.id)
    print(f"  Resolved:       {resolved.resolved}")
    print(f"  Resolved at:    {resolved.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if resolved.resolved_at else 'N/A'}")


def demo_vulnerability_scanning():
    """Demonstrate vulnerability scanning features."""
    print_section("4. VULNERABILITY SCANNING")

    vuln_service = VulnerabilityService()

    # Perform full scan
    print("Performing full system scan...")
    scan = vuln_service.perform_scan(target="kortana_system", scan_type="full")
    print(f"  Scan ID:        {scan.scan_id[:20]}...")
    print(f"  Status:         {scan.status}")
    print(f"  Vulnerabilities: {scan.vulnerabilities_found}")
    print(f"  Duration:       {scan.scan_duration_seconds:.2f}s")
    print()

    # Show detected vulnerabilities
    if scan.vulnerabilities:
        print("Detected vulnerabilities:")
        for vuln in scan.vulnerabilities[:3]:  # Show first 3
            print(f"\n  [{vuln['severity'].upper()}] {vuln['title']}")
            print(f"    Location:     {vuln['location']}")
            print(f"    Description:  {vuln['description']}")
            print(f"    Remediation:  {vuln['remediation']}")
    print()

    # Get security recommendations
    print("Security recommendations:")
    recommendations = vuln_service.get_security_recommendations()
    for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
        print(f"\n  {i}. [{rec['severity'].upper()}] {rec['title']}")
        print(f"     Recommendation: {rec['recommendation']}")


def demo_dashboard():
    """Demonstrate security dashboard metrics."""
    print_section("5. SECURITY DASHBOARD")

    alert_service = AlertService()
    vuln_service = VulnerabilityService()

    # Get alert statistics
    alert_stats = alert_service.get_alert_statistics()
    vuln_stats = vuln_service.get_vulnerability_statistics()

    print("System Security Status:")
    print(f"  Overall Health:      {'⚠ Attention Needed' if alert_stats['active_alerts'] > 0 else '✓ Healthy'}")
    print()

    print("Alert Metrics:")
    print(f"  Total Alerts:        {alert_stats['total_alerts']}")
    print(f"  Active Alerts:       {alert_stats['active_alerts']}")
    print(f"  Critical:            {alert_stats['severity_distribution']['critical']}")
    print(f"  High:                {alert_stats['severity_distribution']['high']}")
    print(f"  Medium:              {alert_stats['severity_distribution']['medium']}")
    print(f"  Low:                 {alert_stats['severity_distribution']['low']}")
    print()

    print("Vulnerability Metrics:")
    print(f"  Total Scans:         {vuln_stats['total_scans']}")
    print(f"  Total Vulnerabilities: {vuln_stats['total_vulnerabilities']}")
    print(f"  Critical:            {vuln_stats['severity_distribution']['critical']}")
    print(f"  High:                {vuln_stats['severity_distribution']['high']}")
    print(f"  Medium:              {vuln_stats['severity_distribution']['medium']}")
    print(f"  Low:                 {vuln_stats['severity_distribution']['low']}")


def main():
    """Run the security demo."""
    print("\n" + "=" * 70)
    print("  KOR'TANA SECURITY MODULE - DEMONSTRATION")
    print("=" * 70)

    try:
        demo_encryption()
        demo_threat_detection()
        demo_alerts()
        demo_vulnerability_scanning()
        demo_dashboard()

        print("\n" + "=" * 70)
        print("  DEMONSTRATION COMPLETE")
        print("=" * 70)
        print("\nAll security features demonstrated successfully!")
        print("\nFor more information, see:")
        print("  - docs/SECURITY_MODULE.md")
        print("  - src/kortana/modules/security/README.md")
        print()

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
