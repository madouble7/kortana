"""
Base Plugin Interface for Kor'tana
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BasePlugin(ABC):
    """Base class for all Kor'tana plugins"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.enabled = True

    @abstractmethod
    def execute(self, **kwargs) -> dict[str, Any]:
        """
        Execute the plugin's main functionality

        Args:
            **kwargs: Plugin-specific parameters

        Returns:
            Dictionary with plugin results
        """
        pass

    @abstractmethod
    def get_info(self) -> dict[str, Any]:
        """
        Get plugin information

        Returns:
            Dictionary with plugin metadata
        """
        pass

    def validate_params(self, **kwargs) -> bool:
        """
        Validate plugin parameters

        Args:
            **kwargs: Parameters to validate

        Returns:
            True if valid, False otherwise
        """
        return True

    def enable(self):
        """Enable the plugin"""
        self.enabled = True

    def disable(self):
        """Disable the plugin"""
        self.enabled = False

    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self.enabled


class PluginRegistry:
    """Registry for managing plugins"""

    def __init__(self):
        self._plugins: dict[str, BasePlugin] = {}

    def register(self, plugin: BasePlugin):
        """
        Register a plugin

        Args:
            plugin: Plugin instance to register
        """
        self._plugins[plugin.name] = plugin

    def unregister(self, plugin_name: str):
        """
        Unregister a plugin

        Args:
            plugin_name: Name of plugin to unregister
        """
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]

    def get(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Get a plugin by name

        Args:
            plugin_name: Name of plugin to retrieve

        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> list[str]:
        """
        List all registered plugin names

        Returns:
            List of plugin names
        """
        return list(self._plugins.keys())

    def get_all(self) -> dict[str, BasePlugin]:
        """
        Get all registered plugins

        Returns:
            Dictionary of plugins
        """
        return self._plugins.copy()

    def execute(self, plugin_name: str, **kwargs) -> dict[str, Any]:
        """
        Execute a plugin

        Args:
            plugin_name: Name of plugin to execute
            **kwargs: Plugin-specific parameters

        Returns:
            Plugin execution results
        """
        plugin = self.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin {plugin_name} not found")

        if not plugin.is_enabled():
            raise ValueError(f"Plugin {plugin_name} is disabled")

        return plugin.execute(**kwargs)
