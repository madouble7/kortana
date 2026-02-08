"""
Enhanced error handling for Kor'tana

Provides structured exception hierarchy and error recovery strategies.
"""

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"         # Can retry without issue
    MEDIUM = "medium"   # May need intervention
    HIGH = "high"       # Requires immediate attention
    CRITICAL = "critical"  # System failure


class KortanaError(Exception):
    """Base exception for Kor'tana."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        error_code: Optional[str] = None,
        recoverable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.error_code = error_code
        self.recoverable = recoverable
        
        logger.log(
            level=logging.ERROR if severity == ErrorSeverity.CRITICAL else logging.WARNING,
            msg=f"[{severity.value}] {self.__class__.__name__}: {message}"
        )
    
    def __str__(self) -> str:
        """Return formatted error message."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(KortanaError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            error_code=f"CONFIG_{config_key.upper() if config_key else 'INVALID'}",
            recoverable=False
        )


class MemoryError(KortanaError):
    """Raised when memory operations fail."""
    
    def __init__(self, message: str, recoverable: bool = True):
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            error_code="MEMORY_ERROR",
            recoverable=recoverable
        )


class ModelError(KortanaError):
    """Raised when model/LLM operations fail."""
    
    def __init__(self, message: str, model_name: Optional[str] = None, recoverable: bool = True):
        code = f"MODEL_{model_name.upper()}" if model_name else "MODEL_ERROR"
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            error_code=code,
            recoverable=recoverable
        )


class ServiceError(KortanaError):
    """Raised when external services fail."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, http_status: Optional[int] = None):
        code = f"SERVICE_{service_name.upper()}" if service_name else "SERVICE_ERROR"
        if http_status:
            code += f"_{http_status}"
        
        severity = (
            ErrorSeverity.HIGH if http_status and http_status >= 500
            else ErrorSeverity.MEDIUM
        )
        
        super().__init__(
            message=message,
            severity=severity,
            error_code=code,
            recoverable=http_status in (408, 429, 500, 502, 503, 504)
        )


class ValidationError(KortanaError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        code = f"VALIDATION_{field.upper()}" if field else "VALIDATION_ERROR"
        super().__init__(
            message=message,
            severity=ErrorSeverity.LOW,
            error_code=code,
            recoverable=False
        )


class TimeoutError(KortanaError):
    """Raised when operations timeout."""
    
    def __init__(self, message: str, operation: Optional[str] = None, timeout_seconds: Optional[float] = None):
        parts = ["Operation timed out"]
        if operation:
            parts.append(f"{operation}")
        if timeout_seconds:
            parts.append(f"({timeout_seconds}s)")
        
        full_msg = " ".join(parts) if len(parts) > 1 else message
        
        super().__init__(
            message=full_msg,
            severity=ErrorSeverity.MEDIUM,
            error_code="TIMEOUT",
            recoverable=True
        )


class RetryableError(KortanaError):
    """Indicates an error that can be retried."""
    
    def __init__(
        self,
        message: str,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
    ):
        super().__init__(
            message=message,
            severity=ErrorSeverity.LOW,
            error_code="RETRYABLE_ERROR",
            recoverable=True
        )
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.attempt = 0
    
    def next_backoff(self) -> float:
        """Calculate next backoff duration (exponential)."""
        self.attempt += 1
        return self.backoff_seconds * (2 ** (self.attempt - 1))


def handle_error(error: Exception) -> tuple[bool, str]:
    """
    Analyze an error and determine if it's recoverable.
    
    Args:
        error: The exception to handle
        
    Returns:
        Tuple of (is_recoverable, error_message)
    """
    if isinstance(error, KortanaError):
        return error.recoverable, str(error)
    
    # Default handling for unknown errors
    return False, str(error)


class ErrorContext:
    """Context manager for graceful error handling."""
    
    def __init__(
        self,
        operation: str,
        on_error: Optional[callable] = None,
        raise_on_error: bool = True,
    ):
        self.operation = operation
        self.on_error = on_error
        self.raise_on_error = raise_on_error
        self.error: Optional[Exception] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val
            logger.error(f"Error in {self.operation}: {exc_val}")
            
            if self.on_error:
                self.on_error(exc_val)
            
            if not self.raise_on_error:
                return True  # Suppress exception
        
        return False
