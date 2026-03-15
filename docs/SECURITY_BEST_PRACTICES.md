# Security Best Practices for Kor'tana

This document outlines security best practices and the security improvements made to the Kor'tana project.

## Recent Security Fixes

### 1. Task Execution Security (manage_task.py)

#### Fixed Vulnerabilities

**Critical: Remote Code Execution via Dynamic Import**
- **Location**: `src/kortana/manage_task.py`
- **Issue**: The module used `__import__()` with user-supplied module names, allowing arbitrary code execution
- **Fix**: 
  - Replaced `__import__()` with `importlib.import_module()` for safer module loading
  - Implemented a whitelist of allowed modules (`ALLOWED_MODULES`)
  - Added validation function `validate_module_name()` to check module names against whitelist
  - Added validation for function names to prevent injection attacks

**Critical: Shell Injection via subprocess**
- **Location**: `src/kortana/manage_task.py`
- **Issue**: Commands were executed with `shell=True`, allowing shell injection attacks
- **Fix**:
  - Changed to `shell=False` with parsed command lists using `shlex.split()`
  - Added command validation function `validate_command_args()` to detect dangerous patterns
  - Validates against shell metacharacters: `;`, `&`, `|`, `` ` ``, `$`, `(`, `)`
  - Checks for variable expansion and redirection attempts

**High: Unsafe Environment Variable Handling**
- **Location**: `src/kortana/manage_task.py`
- **Issue**: Environment variables were set without validation, allowing potential injection
- **Fix**:
  - Added validation for environment variable names
  - Only allows uppercase letters, numbers, and underscores
  - Must start with a letter or underscore

#### Security Controls

```python
# Module whitelist
ALLOWED_MODULES = {
    "kortana.agents",
    "kortana.core",
    "kortana.tools",
    "kortana.utils",
}

# Environment variable name validation
if not re.match(r'^[A-Z_][A-Z0-9_]*$', key):
    # Reject invalid variable names

# Function name validation
if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', function_name):
    # Reject invalid function names
```

### 2. Code Quality Improvements

**Removed Debug Print Statements**
- Replaced `print("DEBUG: ...")` with `logger.debug(...)` throughout the codebase
- Files affected:
  - `src/kortana/core/brain.py`
  - `src/kortana/core/memory.py`

**Fixed Wildcard Imports**
- Replaced `from module import *` with explicit imports
- Files affected:
  - `src/kortana/services/__init__.py`
- Added `__all__` to explicitly define exported symbols

## General Security Best Practices

### 1. API Key Management

**Current Implementation:**
- API keys are stored in environment variables
- Configuration loaded from `.env` file

**Best Practices:**
- ✅ Never commit API keys to version control
- ✅ Use `.env.example` for template configuration
- ✅ Store sensitive keys in environment variables
- 🔄 Consider using a secret management service (e.g., HashiCorp Vault, AWS Secrets Manager)
- 🔄 Implement key rotation policies
- 🔄 Add encryption for keys at rest

**Example .env file:**
```env
# OpenAI Configuration
OPENAI_API_KEY=sk-...

# Anthropic Configuration  
ANTHROPIC_API_KEY=sk-ant-...

# Database
MEMORY_DB_URL=sqlite:///./kortana_memory_dev.db

# Never commit actual keys!
```

### 2. Input Validation

**Implemented Controls:**
- Module name whitelisting
- Function name format validation
- Command argument validation
- Environment variable name validation

**Additional Recommendations:**
- Validate all user inputs before processing
- Use parameterized queries for database operations
- Sanitize file paths to prevent directory traversal
- Validate file uploads (type, size, content)

### 3. Dependency Security

**Current Status:**
- Dependencies specified in `pyproject.toml` and `requirements.txt`
- Some dependencies have version ranges

**Recommendations:**
- ✅ Pin dependency versions for production deployments
- 🔄 Regularly update dependencies to patch security vulnerabilities
- 🔄 Use tools like `pip-audit` or `safety` to check for known vulnerabilities
- 🔄 Enable GitHub Dependabot for automated dependency updates

**Example usage:**
```bash
# Check for vulnerabilities
pip install pip-audit
pip-audit

# Or use safety
pip install safety
safety check
```

### 4. Database Security

**Best Practices:**
- Use parameterized queries (SQLAlchemy ORM does this by default)
- Apply principle of least privilege for database users
- Encrypt sensitive data at rest
- Use connection pooling with secure configurations
- Enable database audit logging

### 5. Authentication & Authorization

**Current Implementation:**
- Basic API key authentication for LLM services

**Recommendations:**
- Implement proper authentication for API endpoints
- Use JWT tokens for stateless authentication
- Implement rate limiting to prevent abuse
- Add role-based access control (RBAC)
- Log authentication attempts

### 6. Secure Communication

**Best Practices:**
- ✅ Use HTTPS for all external API communications
- 🔄 Implement certificate pinning for critical services
- 🔄 Validate SSL/TLS certificates
- 🔄 Use secure WebSocket connections (WSS) if applicable

### 7. Logging & Monitoring

**Current Implementation:**
- Logging configured in core modules
- Debug statements converted to proper logging

**Recommendations:**
- ✅ Use proper logging levels (DEBUG, INFO, WARNING, ERROR)
- ⚠️ Never log sensitive information (API keys, passwords, tokens)
- 🔄 Implement centralized logging
- 🔄 Set up security monitoring and alerting
- 🔄 Regular log review and analysis

**Example secure logging:**
```python
# BAD - Logs sensitive data
logger.info(f"API Key: {api_key}")

# GOOD - Masks sensitive data
logger.info(f"API Key: {api_key[:8]}...")
```

### 8. Error Handling

**Best Practices:**
- Don't expose internal error details to users
- Log detailed errors internally
- Return generic error messages to clients
- Implement proper exception handling

```python
try:
    # Risky operation
    result = execute_task(task_id)
except Exception as e:
    logger.error(f"Task execution failed: {e}", exc_info=True)
    return {"error": "Task execution failed", "task_id": task_id}
```

## Security Testing

### Manual Testing
Run the security test suite:
```bash
python -m pytest tests/test_manage_task_security.py -v
```

### Automated Security Scanning

**Recommended Tools:**
- **Bandit**: Python security linter
  ```bash
  pip install bandit
  bandit -r src/kortana/
  ```

- **Safety**: Checks dependencies for known vulnerabilities
  ```bash
  pip install safety
  safety check
  ```

- **CodeQL**: Advanced semantic code analysis (GitHub integration)

## Security Checklist

### For New Features
- [ ] Validate all inputs
- [ ] Use parameterized queries
- [ ] Avoid dynamic code execution
- [ ] Never use `shell=True` in subprocess calls
- [ ] Check for path traversal vulnerabilities
- [ ] Sanitize output to prevent XSS (if web-facing)
- [ ] Implement proper error handling
- [ ] Add security tests
- [ ] Review for sensitive data exposure

### For Production Deployment
- [ ] All API keys stored securely
- [ ] HTTPS enabled for all endpoints
- [ ] Database credentials rotated
- [ ] Logging configured (without sensitive data)
- [ ] Rate limiting implemented
- [ ] Security headers configured
- [ ] Dependencies updated
- [ ] Security scan completed
- [ ] Penetration testing performed (if applicable)

## Reporting Security Issues

If you discover a security vulnerability in Kor'tana, please report it responsibly:

1. **Do not** create a public GitHub issue
2. Email the maintainers directly
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [CWE Top 25](https://cwe.mitre.org/top25/)

## Changelog

### 2026-02-08
- Fixed critical RCE vulnerability in task execution
- Fixed shell injection vulnerability in subprocess calls
- Added input validation for module names, function names, and environment variables
- Replaced debug print statements with proper logging
- Fixed wildcard imports in services module
- Created comprehensive security documentation
