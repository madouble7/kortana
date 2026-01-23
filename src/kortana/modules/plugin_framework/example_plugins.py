"""
Example Plugins for Kor'tana
Weather, Stock, and Task Management plugins
"""

from typing import Any

from .plugin_base import BasePlugin


class WeatherPlugin(BasePlugin):
    """Plugin for fetching weather information"""

    def __init__(self):
        super().__init__()
        self.name = "WeatherPlugin"

    def execute(self, **kwargs) -> dict[str, Any]:
        """Fetch weather data"""
        location = kwargs.get("location", "Unknown")
        # Placeholder implementation
        return {
            "location": location,
            "temperature": "22°C",
            "condition": "Partly Cloudy",
            "humidity": "65%",
        }

    def get_info(self) -> dict[str, Any]:
        """Get plugin info"""
        return {
            "name": self.name,
            "version": self.version,
            "description": "Fetches current weather information",
            "parameters": ["location"],
        }


class StockPlugin(BasePlugin):
    """Plugin for fetching stock market data"""

    def __init__(self):
        super().__init__()
        self.name = "StockPlugin"

    def execute(self, **kwargs) -> dict[str, Any]:
        """Fetch stock data"""
        symbol = kwargs.get("symbol", "UNKNOWN")
        # Placeholder implementation
        return {
            "symbol": symbol,
            "price": "$150.25",
            "change": "+2.5%",
            "volume": "1.2M",
        }

    def get_info(self) -> dict[str, Any]:
        """Get plugin info"""
        return {
            "name": self.name,
            "version": self.version,
            "description": "Fetches stock market data",
            "parameters": ["symbol"],
        }


class TaskManagementPlugin(BasePlugin):
    """Plugin for task management operations"""

    def __init__(self):
        super().__init__()
        self.name = "TaskManagementPlugin"
        self.tasks = []

    def execute(self, **kwargs) -> dict[str, Any]:
        """Manage tasks"""
        action = kwargs.get("action", "list")

        if action == "add":
            task = kwargs.get("task", "")
            self.tasks.append(task)
            return {"action": "add", "task": task, "total_tasks": len(self.tasks)}
        elif action == "list":
            return {"action": "list", "tasks": self.tasks}
        elif action == "clear":
            self.tasks.clear()
            return {"action": "clear", "tasks": []}
        else:
            return {"action": "unknown", "error": "Invalid action"}

    def get_info(self) -> dict[str, Any]:
        """Get plugin info"""
        return {
            "name": self.name,
            "version": self.version,
            "description": "Manages tasks and to-do items",
            "parameters": ["action", "task"],
        }
