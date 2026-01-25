"""
Frontend Adapter Routers
Provides compatibility layers for various frontend frameworks
"""

from . import autogen_adapter, copilotkit_adapter, lobechat_adapter, openwebui_adapter

__all__ = [
    "autogen_adapter",
    "copilotkit_adapter",
    "lobechat_adapter",
    "openwebui_adapter",
]
