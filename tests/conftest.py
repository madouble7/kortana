"""
Configuration and fixtures for pytest.

This file sets up common fixtures and configurations for all tests.
"""

import json
import os
import sys

import pytest

# Add the src directory to the path so we can import modules
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

# Try to import database components, but don't fail if they're not available
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.kortana.services.database import Base
    
    # Define a global test database engine
    engine_test = create_engine("sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)
    DATABASE_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"Database components not available: {e}")
    DATABASE_AVAILABLE = False
    engine_test = None
    TestingSessionLocal = None


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment for all tests."""
    # Create a minimal test models config
    test_config_dir = os.path.join(os.path.dirname(__file__), "test_data")
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
                "cost_per_1m_output": 0.2,
            }
        },
    }

    test_models_config_path = os.path.join(test_config_dir, "test_models_config.json")
    with open(test_models_config_path, "w") as f:
        json.dump(test_models_config, f)

    # Set environment variables for testing
    os.environ["TEST_API_KEY"] = "test-api-key"
    os.environ["MODELS_CONFIG_PATH"] = test_models_config_path

    yield

    # Clean up
    if os.path.exists(test_models_config_path):
        os.remove(test_models_config_path)
    if "TEST_API_KEY" in os.environ:
        del os.environ["TEST_API_KEY"]
    if "MODELS_CONFIG_PATH" in os.environ:
        del os.environ["MODELS_CONFIG_PATH"]


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up the test database schema for all tests."""
    if not DATABASE_AVAILABLE or engine_test is None:
        # Skip database setup if not available
        yield
        return
    
    # Create the schema
    Base.metadata.create_all(bind=engine_test)
    yield
    # Drop the schema
    Base.metadata.drop_all(bind=engine_test)
