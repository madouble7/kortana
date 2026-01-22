# Security Module

Advanced cybersecurity features for Kor'tana system.

## Quick Start

### Using the Security Middleware (Recommended)

Add the security middleware to your FastAPI application for automatic threat detection:

```python
from src.kortana.modules.security.middleware.security_middleware import SecurityMiddleware

app = FastAPI()
app.add_middleware(SecurityMiddleware)
```

This will automatically:
- Monitor all incoming requests
- Detect security threats
- Block critical threats
- Add security headers to responses
- Create alerts for suspicious activity

### Using Security Services Directly

```python
from src.kortana.modules.security import (
    EncryptionService,
    AlertService,
    ThreatDetectionService,
    VulnerabilityService
)

# Encrypt sensitive data
encryption = EncryptionService(master_key="your_key")
encrypted = encryption.encrypt("sensitive_data")

# Create security alert
alerts = AlertService()
alert = alerts.create_alert(
    alert_type=AlertType.THREAT_DETECTED,
    severity=AlertSeverity.HIGH,
    title="Security Event",
    description="Suspicious activity detected"
)

# Scan for vulnerabilities
scanner = VulnerabilityService()
scan = scanner.perform_scan(target="system", scan_type="full")
```

## API Endpoints

All security endpoints are available at `/security/`:

- **Alerts**: `/security/alerts`
- **Threats**: `/security/threats`
- **Vulnerabilities**: `/security/vulnerabilities`
- **Dashboard**: `/security/dashboard`

See [SECURITY_MODULE.md](../../docs/SECURITY_MODULE.md) for complete API documentation.

## Features

- **Threat Detection**: Real-time security threat monitoring
- **Alerts**: Comprehensive alert management system
- **Vulnerability Scanning**: Automated security assessments
- **Encryption**: Advanced data encryption utilities
- **Security Dashboard**: Analytics and monitoring

## Testing

```bash
python -m pytest tests/test_security_module.py -v
```

## Documentation

See [docs/SECURITY_MODULE.md](../../docs/SECURITY_MODULE.md) for detailed documentation.
