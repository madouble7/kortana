"""
A testing agent for running automated tests.
This module provides functionality to run tests and capture their results.
"""

import subprocess
from typing import Dict, Union


class TestingAgent:
    """
    An agent responsible for running automated tests.
    Executes pytest and captures the results.
    """

    def run_tests(self) -> Dict[str, Union[bool, str]]:
        """
        Run automated tests using pytest.

        Returns:
            Dict[str, Union[bool, str]]: A dictionary containing test results with keys:
                - 'success': Boolean indicating if all tests passed
                - 'output': String containing the combined stdout/stderr output
        """
        res = subprocess.run(["pytest", "-q"], capture_output=True, text=True)
        return {"success": res.returncode == 0, "output": res.stdout + res.stderr}
