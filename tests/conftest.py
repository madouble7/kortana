"""
Configuration and fixtures for pytest.

This file sets up common fixtures and configurations for all tests.
"""

import os
import sys
import pytest
import json
from pathlib import Path

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment for all tests."""
    # Create a minimal test models config
    test_config_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    os.makedirs(test_config_dir, exist_ok=True)
    
    test_models_config = {
        "default_llm_id": "test-model",
        "models": {
            "test-model": {
                "provider": "test",
                "model_name": "test-model",
                "api_key_env": "TEST_API_KEY",
                "enabled": True,
                "performance_scores": {},
                "cost_per_1m_input": 0.1,
                "cost_per_1m_output": 0.2
            }
        }
    }
    
    test_models_config_path = os.path.join(test_config_dir, 'test_models_config.json')
    with open(test_models_config_path, 'w') as f:
        json.dump(test_models_config, f)
    
    # Set environment variables for testing
    os.environ['TEST_API_KEY'] = 'test-api-key'
    os.environ['MODELS_CONFIG_PATH'] = test_models_config_path
    
    yield
    
    # Clean up
    if os.path.exists(test_models_config_path):
        os.remove(test_models_config_path)
    if 'TEST_API_KEY' in os.environ:
        del os.environ['TEST_API_KEY']
    if 'MODELS_CONFIG_PATH' in os.environ:
        del os.environ['MODELS_CONFIG_PATH']
