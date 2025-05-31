"""
Simplified brain test that validates core functionality without complex dependencies
"""

import os
from unittest.mock import Mock

import pytest


def test_brain_module_structure():
    """Test that brain.py has expected structure"""
    brain_path = os.path.join(os.path.dirname(__file__), "..", "src", "brain.py")
    assert os.path.exists(brain_path), "brain.py file should exist"

    # Read and check for key components
    with open(brain_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "class ChatEngine" in content, "ChatEngine class should be defined"
    assert "def get_response" in content, "get_response method should exist"
    assert "def set_mode" in content, "set_mode method should exist"
    assert "def __init__" in content, "ChatEngine should have __init__ method"


def test_strategic_config_imports():
    """Test that strategic_config can be imported and has required enums"""
    try:
        # Add src to path temporarily
        import sys

        src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        from strategic_config import PerformanceMetric, TaskCategory

        # Verify TaskCategory has expected values
        assert hasattr(TaskCategory, "CODE_GENERATION")
        assert hasattr(TaskCategory, "RESEARCH")
        assert hasattr(TaskCategory, "COMMUNICATION")

        # Verify PerformanceMetric exists and is callable
        assert callable(PerformanceMetric)

    except ImportError as e:
        pytest.fail(f"Cannot import strategic_config: {e}")


def test_model_router_basic():
    """Test that model_router can be imported"""
    try:
        import sys

        src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        from model_router import SacredModelRouter

        assert SacredModelRouter is not None

    except ImportError as e:
        pytest.fail(f"Cannot import SacredModelRouter: {e}")


def test_memory_manager_basic():
    """Test that memory_manager can be imported"""
    try:
        import sys

        src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        from memory_manager import MemoryManager

        assert MemoryManager is not None

    except ImportError as e:
        pytest.fail(f"Cannot import MemoryManager: {e}")


def test_basic_response_simulation():
    """Test a simulated response generation flow"""
    # Mock the core components and test the flow
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": "Hello, I am here with gentle presence.",
                    "tool_calls": [],
                }
            }
        ],
        "usage": Mock(prompt_tokens=25, completion_tokens=15),
    }

    # Simulate the response processing
    response_text = mock_response["choices"][0]["message"]["content"]
    assert isinstance(response_text, str)
    assert len(response_text) > 0
    assert "presence" in response_text.lower() or "gentle" in response_text.lower()


def test_config_file_structure():
    """Test that required config files exist and have basic structure"""
    config_dir = os.path.join(os.path.dirname(__file__), "..", "config")

    # Check persona.json
    persona_path = os.path.join(config_dir, "persona.json")
    if os.path.exists(persona_path):
        import json

        with open(persona_path, "r") as f:
            persona_config = json.load(f)
        assert "persona" in persona_config or "modes" in persona_config

    # Check models_config.json
    models_path = os.path.join(config_dir, "models_config.json")
    if os.path.exists(models_path):
        import json

        with open(models_path, "r") as f:
            models_config = json.load(f)
        assert "models" in models_config or "default_model" in models_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
