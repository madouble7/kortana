"""
Plugin Loader for Kor'tana
Manages dynamic loading and initialization of plugins
"""

from typing import Any

from .plugin_base import BasePlugin, PluginRegistry


class PluginLoader:
    """Service for loading and managing plugins"""

    def __init__(self):
        self.registry = PluginRegistry()

    def load_plugin(self, plugin: BasePlugin):
        """
        Load a plugin into the registry

        Args:
            plugin: Plugin instance to load
        """
        self.registry.register(plugin)

    def unload_plugin(self, plugin_name: str):
        """
        Unload a plugin from the registry

        Args:
            plugin_name: Name of plugin to unload
        """
        self.registry.unregister(plugin_name)

    def get_plugin(self, plugin_name: str) -> BasePlugin:
        """
        Get a loaded plugin

        Args:
            plugin_name: Name of plugin

        Returns:
            Plugin instance
        """
        plugin = self.registry.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin {plugin_name} not loaded")
        return plugin

    def list_plugins(self) -> list[dict[str, Any]]:
        """
        List all loaded plugins with their info

        Returns:
            List of plugin information dictionaries
        """
        plugins = []
        for _name, plugin in self.registry.get_all().items():
            info = plugin.get_info()
            info["enabled"] = plugin.is_enabled()
            plugins.append(info)
        return plugins

    def execute_plugin(self, plugin_name: str, **kwargs) -> dict[str, Any]:
        """
        Execute a plugin

        Args:
            plugin_name: Name of plugin to execute
            **kwargs: Plugin parameters

        Returns:
            Plugin execution results
        """
        return self.registry.execute(plugin_name, **kwargs)
