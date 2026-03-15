# Security Notes - CopilotKit Integration

## Overview

This document tracks security considerations specific to the CopilotKit integration in Kor'tana.

## Current Security Status

### Frontend Dependencies

**Last Updated**: January 22, 2026

#### Known Vulnerabilities

The CopilotKit frontend has **16 moderate severity vulnerabilities** in indirect dependencies:

| Package | Issue | Severity | Status |
|---------|-------|----------|--------|
| prismjs | DOM Clobbering (GHSA-x7hr-w5r2-h6wg) | Moderate | Tracked |
| refractor | Depends on vulnerable prismjs | Moderate | Tracked |
| react-syntax-highlighter | Depends on vulnerable refractor | Moderate | Tracked |

#### Impact Assessment

- **Affected Feature**: Syntax highlighting for code blocks in chat messages
- **Current Risk**: Low - These features are not actively used in the basic chat interface
- **Exploitation Requirements**: Attacker would need to inject specific DOM elements
- **Mitigation**: The vulnerabilities exist in optional UI features for code display

#### Remediation Options

1. **Wait for CopilotKit Update**: Monitor [@copilotkit/react-ui](https://www.npmjs.com/package/@copilotkit/react-ui) releases
2. **Force Fix (Breaking)**: Run `npm audit fix --force` to update to breaking versions
3. **Remove Syntax Highlighting**: Configure CopilotKit to disable code highlighting features

### Backend Security

#### API Authentication

- **Current State**: Development mode - API key validation is optional
- **Production Requirements**:
  - Enable strict API key validation
  - Implement rate limiting
  - Add request logging
  - Use HTTPS only

#### CORS Configuration

- **Current State**: Allows all origins (`allow_origins=["*"]`)
- **Production Requirements**:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://your-domain.com"],
      allow_credentials=True,
      allow_methods=["POST", "GET"],
      allow_headers=["*"],
  )
  ```

## Security Checklist for Production

### Before Deploying to Production

- [ ] Update CORS to whitelist specific origins
- [ ] Enable API key authentication in `copilotkit_adapter.py`
- [ ] Set up HTTPS with valid SSL certificates
- [ ] Implement rate limiting on API endpoints
- [ ] Review and update all environment variables
- [ ] Remove or restrict debug logging
- [ ] Run `npm audit` and address critical/high vulnerabilities
- [ ] Enable request/response logging for monitoring
- [ ] Set up monitoring and alerting
- [ ] Review and restrict file system permissions
- [ ] Implement input sanitization and validation
- [ ] Set up regular dependency updates

### Ongoing Maintenance

- [ ] Weekly: Check for new security advisories
- [ ] Monthly: Run `npm audit` and `pip check`
- [ ] Quarterly: Review access logs for anomalies
- [ ] Quarterly: Update all dependencies
- [ ] Annually: Full security audit

## Reporting Security Issues

If you discover a security vulnerability in this integration:

1. **Do not** open a public issue
2. Email the maintainers directly
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## References

- [CopilotKit Security Best Practices](https://docs.copilotkit.ai/security)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [npm Security Best Practices](https://docs.npmjs.com/packages-and-modules/securing-your-code)

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-22 | Initial security assessment for CopilotKit integration | AI Agent |
