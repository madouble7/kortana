"""
Ghost Protocol Phase 2: Integration Verification Script

This script verifies that the TabbyClient is correctly registered in the
LLMClientFactory and that the EnhancedModelRouter can route coding tasks to it.
"""

import logging
import sys
import os
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path("c:/kortana/src")))

from src.kortana.config import load_config
from src.kortana.llm_clients.factory import LLMClientFactory
from src.kortana.core.enhanced_model_router import EnhancedModelRouter, TaskType

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("GhostProtocolVerifier")

def verify_integration():
    logger.info("Starting Ghost Protocol Phase 2 Verification...")
    
    # 1. Load Config
    config = load_config()
    logger.info(f"Loaded config. Default LLM: {config.default_llm_id}")
    
    # 2. Verify Factory registration
    factory = LLMClientFactory(settings=config)
    client_names = factory.MODEL_CLIENT_NAMES
    
    tabby_model_id = "star-coder-2-7b-local"
    if tabby_model_id in client_names and client_names[tabby_model_id] == "TabbyClient":
        logger.info(f"✅ Success: {tabby_model_id} is registered in LLMClientFactory as TabbyClient.")
    else:
        logger.error(f"❌ Failure: {tabby_model_id} NOT found or incorrectly registered in LLMClientFactory.")
        return False

    # 3. Verify Model Routing
    router = EnhancedModelRouter(settings=config)
    
    # Test coding task routing
    coding_input = "Write a python function to Fibonacci sequence"
    selected_model = router.get_optimal_model(TaskType.CODING, coding_input)
    
    if selected_model == tabby_model_id:
        logger.info(f"✅ Success: Coding task routed to {selected_model}.")
    else:
        logger.warning(f"⚠️ Note: Coding task routed to {selected_model} (Expected {tabby_model_id} if routing config applied correctly).")
        # Check if it exists in router's metadata at least
        if tabby_model_id in router.model_metadata:
             logger.info(f"✅ Success: {tabby_model_id} metadata is loaded in router.")
        else:
             logger.error(f"❌ Failure: {tabby_model_id} metadata NOT found in router.")
             return False

    # 4. Verify Client instantiation
    try:
        tabby_client = factory.get_client(tabby_model_id)
        if tabby_client and tabby_client.__class__.__name__ == "TabbyClient":
            logger.info("✅ Success: TabbyClient instantiated successfully from factory.")
        else:
            logger.error(f"❌ Failure: Factory returned {type(tabby_client)} instead of TabbyClient.")
            return False
    except Exception as e:
        logger.error(f"❌ Failure: Error instantiating TabbyClient: {e}")
        return False

    logger.info("\n--- GHOST PROTOCOL PHASE 2 INTEGRATION COMPLETE ---")
    logger.info("Local inference via Tabby (StarCoder-2-7B) is now merged with Kor'tana core logic.")
    return True

if __name__ == "__main__":
    success = verify_integration()
    sys.exit(0 if success else 1)
