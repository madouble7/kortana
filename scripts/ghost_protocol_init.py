"""
Ghost Protocol Implementation Script

This script initializes the Tabby service, provisions the StarCoder model,
and integrates it into the Kor'tana service registry.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to sys.path for direct script execution
sys.path.append(str(Path(__file__).parent.parent / "src"))

from kortana.core.services import get_tabby_service, initialize_services


# Setup mock config
class MockConfig:
    def __init__(self):
        self.TABBY_EXECUTABLE = "tabby"
        self.TABBY_MODEL_ID = "StarCoder2-7B"
        self.TABBY_PORT = 8080
        self.TABBY_DEVICE = "cpu"


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ghost_protocol")

    logger.info("Initializing Kor'tana Ghost Protocol Infrastructure...")

    config = MockConfig()
    initialize_services(config)

    tabby = get_tabby_service()

    # 1. Check if Tabby is installed
    if not await tabby.check_availability():
        logger.error(
            "Tabby executable not found. Please install Tabby (https://tabby.sh)."
        )
        return

    # 2. Provision Model
    logger.info("Starting model provisioning (StarCoder-2-7B)...")
    success = await tabby.provision_model()

    if success:
        logger.info("Model provisioned. Starting Tabby server...")
        # 3. Start Server
        if await tabby.start_server():
            logger.info(f"Tabby server active: {tabby.get_status()}")
        else:
            logger.error("Failed to start Tabby server.")
    else:
        logger.error(
            "Ghost Protocol: Model provisioning failed. Manual intervention required."
        )


if __name__ == "__main__":
    asyncio.run(main())
