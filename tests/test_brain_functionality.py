#!/usr/bin/env python3
"""
Test runner for validating the refactored brain.py functionality.
"""

import logging
import sys
from pathlib import Path

# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir.absolute()))

# Try to import and test the brain
try:
    logger.info("Testing fixed brain module...")

    # First try the fixed version
    from kortana.brain_fixed import ChatEngine

    logger.info("Successfully imported fixed ChatEngine")

    # Create a simple mock config for testing
    from dataclasses import dataclass

    @dataclass
    class MockPaths:
        persona_file_path: str = "config/persona.json"
        identity_file_path: str = "config/identity.json"

    @dataclass
    class MockConfig:
        default_llm_id: str = "test-llm"
        paths: MockPaths = MockPaths()

    # Create a simple test instance
    try:
        test_engine = ChatEngine(MockConfig())
        logger.info("Successfully created ChatEngine instance")
        logger.info(f"Current mode: {test_engine.current_mode}")

        # Test some simple methods
        test_engine.set_mode("test")
        logger.info(f"Updated mode: {test_engine.current_mode}")

        # Get memory stats
        stats = test_engine.get_memory_stats()
        logger.info(f"Memory stats: {stats}")

        logger.info("Basic tests passed!")

    except Exception as e:
        logger.error(f"Error creating/testing ChatEngine: {e}")

except ImportError:
    logger.error("Could not import ChatEngine from kortana.brain_fixed")
    logger.info("Trying original brain.py...")

    try:
        from kortana.brain import ChatEngine

        logger.info("Successfully imported original ChatEngine")
    except ImportError:
        logger.error("Could not import ChatEngine from kortana.brain either")
except Exception as e:
    logger.error(f"Unexpected error during import: {e}")

logger.info("Test complete")
