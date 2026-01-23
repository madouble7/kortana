"""
Debugging Team Module

This module provides automated debugging, error detection, and resolution capabilities
for the Kor'tana framework.
"""

from .error_detector import ErrorDetector
from .error_reporter import ErrorReporter
from .resolution_engine import ResolutionEngine

__all__ = ["ErrorDetector", "ErrorReporter", "ResolutionEngine"]
