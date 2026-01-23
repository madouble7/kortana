"""
AR/VR Exploration Module

This module provides AR/VR exploration capabilities for Kor'tana, including:
- Immersive simulation environments
- Real-world environment overlay
- Spatial object management
- User-friendly AR/VR interfaces

Inspired by sci-ctrl/VirtuScope capabilities.
"""

from . import models, schemas, services
from .routers import ar_vr_router

__all__ = ["models", "schemas", "services", "ar_vr_router"]
