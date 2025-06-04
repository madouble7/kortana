"""
Very simple test to check if pytest discovery is working.
"""


def test_simple_pass():
    """A simple test that always passes."""
    assert True


class TestBasic:
    """A basic test class."""

    def test_simple_class_method(self):
        """A simple test method that always passes."""
        assert 1 + 1 == 2
