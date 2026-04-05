"""
Structured logging configuration for Kor'tana
Provides JSON-formatted logging with context tracking
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any


class ContextFilter(logging.Filter):
    """Filter to add contextual information to log records"""

    def __init__(self) -> None:
        super().__init__()
        self.request_id: str | None = None

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record"""
        if self.request_id:
            record.request_id = self.request_id
        else:
            record.request_id = "N/A"
        record.timestamp = datetime.utcnow().isoformat()
        return True


class CustomJsonFormatter(logging.Formatter):
    """Dependency-free JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": getattr(record, "timestamp", datetime.utcnow().isoformat()),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": getattr(record, "request_id", "N/A"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class AutonomyReflectionFilter(logging.Filter):
    """Filter for self-reflective autonomous logging"""

    def filter(self, record: logging.LogRecord) -> bool:
        # Add reflection metadata if not present
        if not hasattr(record, "autonomy_state"):
            record.autonomy_state = "active"
        if not hasattr(record, "self_awareness_level"):
            record.self_awareness_level = "high"
        return True


def setup_logging(log_level: str = "INFO", format_type: str = "json") -> logging.Logger:
    """
    Setup structured logging for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type - 'json' or 'text'

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("kortana")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # Add context filter
    context_filter = ContextFilter()
    console_handler.addFilter(context_filter)

    # Set formatter
    formatter: logging.Formatter
    if format_type.lower() == "json":
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(logger)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    return logging.getLogger(f"kortana.{name}")


# Module-level logger
logger = logging.getLogger("kortana")


def log_request(module: str, message: str, **kwargs: Any) -> None:
    """Log request information"""
    logger = get_logger(module)
    logger.info(f"{message}", extra=kwargs)


def log_error(module: str, message: str, **kwargs: Any) -> None:
    """Log error information"""
    logger = get_logger(module)
    logger.error(f"{message}", extra=kwargs)
