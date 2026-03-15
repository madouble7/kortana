"""
Development Agent Stub

This module provides a stub implementation of the Development Agent
for use in testing and development.
"""

from kortana.config.schema import KortanaConfig


class DevAgentStub:
    """Stub for the Development Agent."""

    def __init__(self, settings: KortanaConfig):
        """
        Initialize the development agent stub.

        Args:
            settings: Application configuration.
        """
        self.settings = settings

    async def perform_task(self, task: str) -> str:
        """
        Perform a development task.

        Args:
            task: The task to perform.

        Returns:
            A string indicating the task was received.
        """
        return f"Development task received: {task}"
