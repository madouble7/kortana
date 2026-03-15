"""
Multimodal AI Prompt Generation Module for Kor'tana

This module provides advanced multimodal capabilities for creating, processing,
and responding to prompts that include text, voice, video, and simulation-based queries.

Key Features:
- Text prompt processing and generation
- Voice/audio content handling
- Video content processing
- Simulation-based query generation
- Modular and extensible architecture
- Seamless integration with existing Kor'tana systems
"""

from .models import (
    ContentType,
    MultimodalContent,
    MultimodalPrompt,
    MultimodalResponse,
    SimulationQuery,
)
from .prompt_generator import MultimodalPromptGenerator
from .processors import MultimodalProcessor
from . import utils

__all__ = [
    "ContentType",
    "MultimodalContent",
    "MultimodalPrompt",
    "MultimodalResponse",
    "SimulationQuery",
    "MultimodalPromptGenerator",
    "MultimodalProcessor",
    "utils",
]
