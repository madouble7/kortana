"""
Input validation and type checking utilities for Kor'tana

Provides validators for common input patterns and custom validation decorators.
"""

import logging
import re
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ValidationRule:
    """Base validation rule."""

    def __init__(self, error_message: str = "Validation failed"):
        self.error_message = error_message

    def validate(self, value: Any) -> bool:
        """Check if value passes validation."""
        raise NotImplementedError

    def __call__(self, value: Any) -> bool:
        return self.validate(value)


class MinLength(ValidationRule):
    """Validate minimum length."""

    def __init__(self, min_len: int):
        super().__init__(f"Must be at least {min_len} characters")
        self.min_len = min_len

    def validate(self, value: Any) -> bool:
        return len(str(value)) >= self.min_len


class MaxLength(ValidationRule):
    """Validate maximum length."""

    def __init__(self, max_len: int):
        super().__init__(f"Must be at most {max_len} characters")
        self.max_len = max_len

    def validate(self, value: Any) -> bool:
        return len(str(value)) <= self.max_len


class Pattern(ValidationRule):
    """Validate against regex pattern."""

    def __init__(self, pattern: str, description: str = ""):
        self.pattern = re.compile(pattern)
        self.description = description
        super().__init__(f"Must match pattern: {description or pattern}")

    def validate(self, value: Any) -> bool:
        return bool(self.pattern.match(str(value)))


class NotEmpty(ValidationRule):
    """Validate not empty."""

    def __init__(self):
        super().__init__("Value cannot be empty")

    def validate(self, value: Any) -> bool:
        return value is not None and str(value).strip() != ""


class InRange(ValidationRule):
    """Validate numeric range."""

    def __init__(self, min_val: int | float, max_val: int | float):
        self.min_val = min_val
        self.max_val = max_val
        super().__init__(f"Must be between {min_val} and {max_val}")

    def validate(self, value: Any) -> bool:
        try:
            num = float(value)
            return self.min_val <= num <= self.max_val
        except (TypeError, ValueError):
            return False


class OneOf(ValidationRule):
    """Validate against allowed values."""

    def __init__(self, allowed: list):
        self.allowed = allowed
        super().__init__(f"Must be one of: {', '.join(str(a) for a in allowed)}")

    def validate(self, value: Any) -> bool:
        return value in self.allowed


class Email(ValidationRule):
    """Validate email format."""

    def __init__(self):
        self.pattern = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
        super().__init__("Must be valid email address")

    def validate(self, value: Any) -> bool:
        return bool(self.pattern.match(str(value)))


class Validator:
    """Flexible validator for complex validation logic."""

    def __init__(self, field_name: str = ""):
        self.field_name = field_name
        self.rules: list[ValidationRule] = []
        self.errors: list[str] = []

    def add_rule(self, rule: ValidationRule) -> 'Validator':
    def add_rule(self, rule: ValidationRule) -> "Validator":
        """Add validation rule."""
        self.rules.append(rule)
        return self

    def min_length(self, min_len: int) -> 'Validator':
        """Add minimum length rule."""
        return self.add_rule(MinLength(min_len))

    def max_length(self, max_len: int) -> 'Validator':
        """Add maximum length rule."""
        return self.add_rule(MaxLength(max_len))

    def pattern(self, regex: str, description: str = "") -> 'Validator':
        """Add pattern rule."""
        return self.add_rule(Pattern(regex, description))

    def not_empty(self) -> 'Validator':
        """Add not empty rule."""
        return self.add_rule(NotEmpty())

    def in_range(self, min_val, max_val) -> 'Validator':
        """Add range rule."""
        return self.add_rule(InRange(min_val, max_val))

    def one_of(self, values: list) -> 'Validator':
        """Add one-of rule."""
        return self.add_rule(OneOf(values))

    def is_email(self) -> 'Validator':
    def min_length(self, min_len: int) -> "Validator":
        """Add minimum length rule."""
        return self.add_rule(MinLength(min_len))

    def max_length(self, max_len: int) -> "Validator":
        """Add maximum length rule."""
        return self.add_rule(MaxLength(max_len))

    def pattern(self, regex: str, description: str = "") -> "Validator":
        """Add pattern rule."""
        return self.add_rule(Pattern(regex, description))

    def not_empty(self) -> "Validator":
        """Add not empty rule."""
        return self.add_rule(NotEmpty())

    def in_range(self, min_val, max_val) -> "Validator":
        """Add range rule."""
        return self.add_rule(InRange(min_val, max_val))

    def one_of(self, values: list) -> "Validator":
        """Add one-of rule."""
        return self.add_rule(OneOf(values))

    def is_email(self) -> "Validator":
        """Add email validation."""
        return self.add_rule(Email())

    def validate(self, value: Any) -> tuple[bool, list[str]]:
        """
        Validate value against all rules.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        self.errors = []

        for rule in self.rules:
            if not rule.validate(value):
                self.errors.append(rule.error_message)
                logger.debug(f"Validation failed for {self.field_name}: {rule.error_message}")
                logger.debug(
                    f"Validation failed for {self.field_name}: {rule.error_message}"
                )

        return len(self.errors) == 0, self.errors

    def __call__(self, value: Any) -> bool:
        """Shorthand for validate."""
        is_valid, _ = self.validate(value)
        return is_valid


def validate_type(value: Any, expected_type: type[T]) -> bool:
    """
    Type validation helper.

    Args:
        value: Value to validate
        expected_type: Expected type

    Returns:
        True if value is of expected type
    """
    return isinstance(value, expected_type)


def sanitize_text(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input text.

    Args:
        text: Text to sanitize
        max_length: Maximum length

    Returns:
        Sanitized text
    """
    # Strip whitespace
    text = text.strip()

    # Truncate if too long
    if len(text) > max_length:
        logger.warning(f"Text truncated from {len(text)} to {max_length} chars")
        text = text[:max_length]

    # Remove control characters
    text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\t\r')
    text = "".join(c for c in text if ord(c) >= 32 or c in "\n\t\r")

    return text


def with_validation(**validators: Callable[[Any], bool]):
    """
    Decorator to validate function arguments.

    Usage:
        @with_validation(
            name=lambda x: len(x) > 0,
            age=lambda x: 0 <= x <= 150
        )
        def user_action(name: str, age: int):
            pass
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Get function parameter names
            import inspect

            sig = inspect.signature(func)

            # Build mapping of parameter names to values
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Validate provided validators
            errors = []
            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not validator(value):
                        errors.append(f"Invalid {param_name}: {value}")

            if errors:
                error_msg = "; ".join(errors)
                logger.error(f"Validation failed for {func.__name__}: {error_msg}")
                raise ValueError(error_msg)

            return func(*args, **kwargs)

        return wrapper

    return decorator
