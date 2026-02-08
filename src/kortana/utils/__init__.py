# src/utils/__init__.py
"""
Utilities Package

Contains various utility functions and modules used throughout the Kor'tana system.
"""

# Text and encoding utilities
# Async utilities
from .async_helpers import (
    AsyncBatchProcessor,
    AsyncCache,
    AsyncRetry,
    ConnectionPool,
    gather_with_limit,
)

# Error handling utilities
from .errors import (
    ConfigurationError,
    ErrorContext,
    ErrorSeverity,
    KortanaError,
    MemoryError,
    ModelError,
    RetryableError,
    ServiceError,
    TimeoutError,
    ValidationError,
    handle_error,
)

# Performance and optimization utilities
from .performance import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    MetricsCollector,
    PerfMetrics,
    TTLCache,
    cached_async,
    timed_execution,
)
from .text_analysis import (
    analyze_sentiment,
    count_tokens,
    detect_emphasis_all_caps,
    detect_keywords,
    ensure_dir_exists,
    extract_keywords,
    format_timestamp,
    identify_important_message_for_context,
    load_all_configs,
    load_json_file,
    safe_write_jsonl,
    summarize_text,
    validate_config,
)
from .text_encoding import (
    decode_base64_to_text,
    encode_file_to_base64,
    encode_text_to_base64,
)
from .timestamp_utils import get_iso_timestamp

# Validation utilities
from .validation import (
    Email,
    InRange,
    MaxLength,
    MinLength,
    NotEmpty,
    OneOf,
    Pattern,
    Validator,
    sanitize_text,
    validate_type,
    with_validation,
)

__all__ = [
    # Text utilities
    "analyze_sentiment",
    "count_tokens",
    "detect_emphasis_all_caps",
    "detect_keywords",
    "ensure_dir_exists",
    "extract_keywords",
    "format_timestamp",
    "identify_important_message_for_context",
    "load_all_configs",
    "load_json_file",
    "safe_write_jsonl",
    "summarize_text",
    "validate_config",
    "decode_base64_to_text",
    "encode_file_to_base64",
    "encode_text_to_base64",
    "get_iso_timestamp",
    # Performance
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "MetricsCollector",
    "PerfMetrics",
    "TTLCache",
    "cached_async",
    "timed_execution",
    # Errors
    "ConfigurationError",
    "ErrorContext",
    "ErrorSeverity",
    "KortanaError",
    "MemoryError",
    "ModelError",
    "RetryableError",
    "ServiceError",
    "TimeoutError",
    "ValidationError",
    "handle_error",
    # Async
    "AsyncBatchProcessor",
    "AsyncCache",
    "AsyncRetry",
    "ConnectionPool",
    "gather_with_limit",
    # Validation
    "Email",
    "InRange",
    "MaxLength",
    "MinLength",
    "NotEmpty",
    "OneOf",
    "Pattern",
    "Validator",
    "sanitize_text",
    "validate_type",
    "with_validation",
]
