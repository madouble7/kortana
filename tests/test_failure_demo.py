#!/usr/bin/env python3
"""
Test with intentional failures to demonstrate error reporting
"""

import pytest


def test_this_will_fail():
    """A test that will fail to demonstrate error reporting"""
    assert 1 + 1 == 3  # Intentional failure


def test_this_will_pass():
    """A test that will pass"""
    assert True


def test_import_error():
    """A test that will cause an import error"""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
