"""
Dynamic API Integration Plugin Framework for Kor'tana
Provides a plugin-based system for external data sources
"""

from .plugin_base import BasePlugin, PluginRegistry
from .plugin_loader import PluginLoader

__all__ = ["BasePlugin", "PluginRegistry", "PluginLoader"]
