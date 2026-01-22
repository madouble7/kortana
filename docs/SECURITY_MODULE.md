# Kor'tana Security Module Documentation

## Overview

The Kor'tana Security Module provides advanced cybersecurity features to enhance system resilience and security. It includes threat detection, real-time alerts, vulnerability management, advanced encryption, and secure API communication capabilities.

## Features

### 1. Threat Detection

The threat detection service monitors API requests in real-time to identify potential security threats:

- **SQL Injection Detection**: Identifies SQL injection patterns in requests
- **XSS Attack Detection**: Detects cross-site scripting attempts
- **Path Traversal Detection**: Identifies directory traversal attacks
- **Code Injection Detection**: Detects code execution attempts
- **Rate Limiting**: Monitors and blocks excessive request rates
- **IP Blocking**: Allows blocking/unblocking of suspicious IP addresses

### 2. Real-Time Alerts

The alert service provides comprehensive security event management:

- **Alert Types**: 
  - Threat Detected
  - Vulnerability Found
  - Suspicious Activity
  - Rate Limit Exceeded
  - Authentication Failure
  - Anomaly Detected

- **Severity Levels**: Low, Medium, High, Critical

- **Alert Management**: Create, retrieve, resolve, and delete alerts

### 3. Vulnerability Management

The vulnerability scanner identifies security weaknesses:

- **Scan Types**: Quick, Full, Targeted
- **Common Vulnerabilities Database**: Pre-loaded with known vulnerability patterns
- **Security Recommendations**: Provides remediation guidance
- **Vulnerability Statistics**: Tracks vulnerabilities over time

### 4. Advanced Encryption

The encryption service provides secure data handling:

- **AES Encryption**: Encrypt/decrypt sensitive data
- **Key Derivation**: PBKDF2-based key generation
- **Data Hashing**: SHA256, SHA512, MD5 support
- **Secure Token Generation**: Cryptographically secure random tokens
- **Dictionary Encryption**: Encrypt entire data structures

### 5. Security Dashboard

Comprehensive security analytics and monitoring:

- **Real-time Metrics**: Active alerts, threats, vulnerabilities
- **System Health**: Overall security status
- **Historical Data**: Alert and scan history
- **Visual Analytics**: Ready for frontend visualization

## API Endpoints

### Alert Management

#### Create Alert
```
POST /security/alerts
```

Request body:
```json
{
  "alert_type": "threat_detected",
  "severity": "high",
  "title": "Suspicious Activity Detected",
  "description": "Multiple failed login attempts from IP 192.168.1.100",
  "source": "authentication_system",
  "metadata": {
    "ip": "192.168.1.100",
    "attempts": 5
  }
}
```

#### Get All Alerts
```
GET /security/alerts?severity=high&resolved=false
```

Query parameters:
- `severity` (optional): Filter by severity (low, medium, high, critical)
- `alert_type` (optional): Filter by alert type
- `resolved` (optional): Filter by resolved status (true/false)

#### Get Alert by ID
```
GET /security/alerts/{alert_id}
```

#### Resolve Alert
```
POST /security/alerts/{alert_id}/resolve
```

#### Delete Alert
```
DELETE /security/alerts/{alert_id}
```

#### Get Alert Statistics
```
GET /security/alerts/statistics/summary
```

Returns:
```json
{
  "total_alerts": 45,
  "active_alerts": 12,
  "resolved_alerts": 33,
  "severity_distribution": {
    "low": 3,
    "medium": 5,
    "high": 3,
    "critical": 1
  },
  "type_distribution": {
    "threat_detected": 7,
    "vulnerability_found": 5
  }
}
```

### Threat Detection

#### Analyze Current Request for Threats
```
POST /security/threats/analyze
```

Automatically analyzes the current request and returns threat assessment.

Response:
```json
{
  "threat_level": "medium",
  "detected_threats": ["sql_injection", "suspicious_user_agent"],
  "confidence_score": 0.75,
  "analysis_details": {
    "endpoint": "/api/data",
    "method": "POST",
    "client_ip": "192.168.1.100"
  }
}
```

#### Block IP Address
```
POST /security/threats/block-ip
```

Request body:
```json
{
  "ip_address": "192.168.1.100"
}
```

#### Unblock IP Address
```
POST /security/threats/unblock-ip
```

#### Get Blocked IPs
```
GET /security/threats/blocked-ips
```

#### Get IP Statistics
```
GET /security/threats/stats/{ip_address}
```

Returns:
```json
{
  "ip_address": "192.168.1.100",
  "requests_last_minute": 45,
  "is_blocked": false,
  "rate_limit_threshold": 100
}
```

### Vulnerability Scanning

#### Start Vulnerability Scan
```
POST /security/vulnerabilities/scan
```

Request body:
```json
{
  "target": "api_endpoints",
  "scan_type": "full"
}
```

Response:
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "scan_timestamp": "2026-01-22T06:30:00Z",
  "vulnerabilities_found": 3,
  "vulnerabilities": [
    {
      "id": "VULN-009",
      "title": "Missing Security Headers",
      "severity": "medium",
      "description": "Response missing security headers",
      "location": "api_endpoints/api/",
      "remediation": "Add security headers middleware"
    }
  ],
  "scan_duration_seconds": 2.5,
  "status": "completed"
}
```

#### Get All Scans
```
GET /security/vulnerabilities/scans?limit=50
```

#### Get Scan by ID
```
GET /security/vulnerabilities/scans/{scan_id}
```

#### Get Security Recommendations
```
GET /security/vulnerabilities/recommendations
```

#### Get Vulnerability Statistics
```
GET /security/vulnerabilities/statistics
```

### Security Dashboard

#### Get Security Metrics
```
GET /security/dashboard/metrics
```

Returns comprehensive security metrics including total alerts, threats detected, vulnerabilities found, and system health.

#### Get Dashboard Summary
```
GET /security/dashboard/summary
```

Returns a complete dashboard summary with recent alerts, scans, and threat information.

#### Security Health Check
```
GET /security/health
```

Returns:
```json
{
  "status": "healthy",
  "module": "security",
  "services": {
    "alert_service": "operational",
    "threat_detection": "operational",
    "vulnerability_scanner": "operational"
  },
  "timestamp": "2026-01-22T06:30:00Z"
}
```

## Python API Usage

### Encryption Service

```python
from src.kortana.modules.security import EncryptionService

# Initialize service
encryption = EncryptionService(master_key="your_secure_key")

# Encrypt sensitive data
encrypted = encryption.encrypt("sensitive_data")

# Decrypt data
decrypted = encryption.decrypt(encrypted)

# Hash data
hash_value = EncryptionService.hash_data("data_to_hash", algorithm="sha256")

# Generate secure token
token = EncryptionService.generate_secure_token(length=32)

# Encrypt dictionary
encrypted_dict = encryption.encrypt_dict({
    "api_key": "secret123",
    "password": "mypassword"
})
```

### Alert Service

```python
from src.kortana.modules.security import AlertService
from src.kortana.modules.security.models.security_models import (
    AlertType, 
    AlertSeverity
)

# Initialize service
alerts = AlertService()

# Create alert
alert = alerts.create_alert(
    alert_type=AlertType.THREAT_DETECTED,
    severity=AlertSeverity.HIGH,
    title="Suspicious Activity",
    description="Multiple failed login attempts",
    metadata={"ip": "192.168.1.100"}
)

# Get all active critical alerts
critical_alerts = alerts.get_all_alerts(
    severity=AlertSeverity.CRITICAL,
    resolved=False
)

# Resolve alert
alerts.resolve_alert(alert.id)

# Get statistics
stats = alerts.get_alert_statistics()
```

### Threat Detection Service

```python
from src.kortana.modules.security import ThreatDetectionService

# Initialize service
threat_detector = ThreatDetectionService()

# Analyze request
detection = threat_detector.analyze_request(
    endpoint="/api/users",
    method="POST",
    client_ip="192.168.1.100",
    headers={"user-agent": "Mozilla/5.0"},
    body='{"username": "admin\' OR 1=1--"}'
)

if detection.threat_level != "none":
    print(f"Threat detected: {detection.detected_threats}")
    print(f"Confidence: {detection.confidence_score}")

# Block suspicious IP
threat_detector.block_ip("192.168.1.100")

# Get request stats
stats = threat_detector.get_request_stats("192.168.1.100")
```

### Vulnerability Service

```python
from src.kortana.modules.security import VulnerabilityService

# Initialize service
vuln_scanner = VulnerabilityService()

# Perform scan
scan = vuln_scanner.perform_scan(
    target="system",
    scan_type="full"
)

print(f"Found {scan.vulnerabilities_found} vulnerabilities")

# Get recommendations
recommendations = vuln_scanner.get_security_recommendations()

# Get statistics
stats = vuln_scanner.get_vulnerability_statistics()
```

## Security Best Practices

### 1. Regular Vulnerability Scans

Schedule regular vulnerability scans:

```python
# Run daily full scan
scan = vuln_scanner.perform_scan(scan_type="full")
```

### 2. Monitor Alerts

Set up monitoring for critical alerts:

```python
critical_alerts = alerts.get_all_alerts(
    severity=AlertSeverity.CRITICAL,
    resolved=False
)

if critical_alerts:
    # Send notifications, take action
    pass
```

### 3. Implement Rate Limiting

The threat detection service automatically tracks request rates. Consider blocking IPs that exceed thresholds:

```python
stats = threat_detector.get_request_stats(ip_address)
if stats["requests_last_minute"] > 100:
    threat_detector.block_ip(ip_address)
```

### 4. Use Encryption for Sensitive Data

Always encrypt sensitive data before storage:

```python
# Encrypt API keys, passwords, tokens
encrypted_key = encryption.encrypt(api_key)
# Store encrypted_key in database
```

### 5. Review Security Metrics

Regularly review security metrics:

```python
# Get dashboard summary
summary = get_dashboard_summary()
print(f"Active alerts: {summary['alerts']['active_alerts']}")
print(f"System health: {summary['overview']['system_status']}")
```

## Configuration

The security module uses sensible defaults but can be configured:

### Rate Limiting

```python
# Adjust rate limit threshold
threat_detector._rate_limit_threshold = 50  # requests per minute
```

### Anomaly Threshold

```python
# Adjust threat detection sensitivity
threat_detector._anomaly_threshold = 0.8  # 0.0 to 1.0
```

## Integration with Existing Systems

The security module is designed to integrate seamlessly with Kor'tana's existing architecture:

1. **Automatic Threat Detection**: The `/security/threats/analyze` endpoint can be called from middleware to analyze all incoming requests

2. **Alert Integration**: Security alerts are stored separately but can be correlated with other system events

3. **Dashboard Integration**: Security metrics are available via REST API for frontend dashboards

4. **Modular Design**: Each service can be used independently or together

## Testing

Run security module tests:

```bash
python -m pytest tests/test_security_module.py -v
```

## Troubleshooting

### Issue: Encryption/Decryption Errors

Make sure you're using the same master key for encryption and decryption:

```python
# Use consistent key
encryption = EncryptionService(master_key="same_key_for_both")
```

### Issue: Rate Limiting False Positives

Adjust the rate limit threshold or whitelist trusted IPs:

```python
# Unblock trusted IP
threat_detector.unblock_ip("192.168.1.10")
```

### Issue: Too Many Alerts

Filter alerts by severity and resolve old ones:

```python
# Clear resolved alerts
alerts.clear_resolved_alerts()
```

## Future Enhancements

Potential future enhancements:

1. **Machine Learning**: AI-powered anomaly detection
2. **Integration**: SIEM system integration
3. **Automated Response**: Automatic threat mitigation
4. **Advanced Scanning**: Deep code analysis
5. **Compliance**: Compliance reporting (GDPR, HIPAA, etc.)

## Support

For issues or questions about the security module, please refer to the main Kor'tana documentation or submit an issue on GitHub.
