"""
Structured logging configuration for Kor'tana
Provides JSON-formatted logging with context tracking
"""

import logging
import sys
from datetime import datetime
from typing import Any

from pythonjsonlogger import jsonlogger


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


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with structured logging"""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


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
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(logger)s %(message)s")
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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
