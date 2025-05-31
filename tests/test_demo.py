#!/usr/bin/env python3
"""
Demonstration test suite to show test reporter capabilities
"""

import time

import pytest


def test_passing_basic():
    """A simple passing test"""
    assert 1 + 1 == 2


def test_passing_with_delay():
    """A passing test with some execution time"""
    time.sleep(0.1)  # Small delay to show timing
    assert "hello".upper() == "HELLO"


def test_skipped_example():
    """A test that gets skipped"""
    pytest.skip("Demonstrating skip functionality")


def test_passing_complex():
    """A more complex passing test"""
    data = {"name": "Kor'tana", "version": "1.0", "status": "active"}
    assert data["name"] == "Kor'tana"
    assert data["status"] == "active"
    assert len(data) == 3


@pytest.mark.xfail(reason="Intentional failure for demo")
def test_expected_failure():
    """A test that's expected to fail"""
    assert False  # Intentional failure


def test_math_operations():
    """Test basic mathematical operations"""
    assert 5 * 5 == 25
    assert 10 / 2 == 5.0
    assert 2**3 == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
