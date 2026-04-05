"""Regression tests for logging bootstrap resilience."""

from __future__ import annotations

import importlib
import logging
import sys


def test_logger_import_tolerates_missing_pythonjsonlogger(monkeypatch) -> None:
    """JSON logging should degrade gracefully when python-json-logger is absent."""
    original_module = sys.modules.pop("pythonjsonlogger", None)
    monkeypatch.setitem(sys.modules, "pythonjsonlogger", None)
    try:
        logger_module = importlib.import_module("src.kortana.logger")
        logger_module = importlib.reload(logger_module)

        logger = logger_module.setup_logging("INFO", "json")
        handler = logger.handlers[-1]
        assert isinstance(handler.formatter, logging.Formatter)

        record = logging.LogRecord(
            name="kortana.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=123,
            msg="hello",
            args=(),
            exc_info=None,
        )
        rendered = handler.format(record)
        assert '"message": "hello"' in rendered
        assert '"level": "INFO"' in rendered
    finally:
        sys.modules.pop("pythonjsonlogger", None)
        if original_module is not None:
            sys.modules["pythonjsonlogger"] = original_module
