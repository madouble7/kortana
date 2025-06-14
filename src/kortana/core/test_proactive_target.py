"""
Test module for proactive code review demonstration
"""


def test_function_without_docstring(param1, param2):
    # This function intentionally lacks a docstring for demonstration
    return param1 + param2


def another_undocumented_function():
    # Another function without docstring
    pass


class TestClass:
    def undocumented_method(self):
        # Method without docstring
        return "test"
