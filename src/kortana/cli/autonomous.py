"""
Autonomous mode CLI entry point for Kor'tana.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure parent directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config import load_config

logger = logging.getLogger(__name__)


def main():
    """Start Kor'tana in autonomous mode."""
    parser = argparse.ArgumentParser(description="Kor'tana Autonomous Mode")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--config", default=None, help="Path to config directory")
    parser.add_argument(
        "--env", default=None, help="Environment to use (development, production, etc.)"
    )
    parser.add_argument("--task", default=None, help="Specific task to perform")
    parser.add_argument(
        "--monitor", action="store_true", help="Run in monitoring mode only"
    )

    args = parser.parse_args()

    # Set environment variables based on args
    if args.env:
        os.environ["KORTANA_ENV"] = args.env
    if args.config:
        os.environ["KORTANA_CONFIG_DIR"] = args.config

    # Load config
    settings = load_config()

    # Override config with command-line args
    debug = args.debug or getattr(settings, "debug", False)

    # Initialize logging
    log_level = (
        "DEBUG" if debug else getattr(getattr(settings, "logging", {}), "level", "INFO")
    )
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=getattr(
            getattr(settings, "logging", {}),
            "format",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        ),
    )

    logger.info(f"Starting Kor'tana in autonomous mode (debug={debug})")

    # Import here to avoid circular imports
    try:
        from kortana.agents.agent_manager import AgentManager

        # Initialize and run the agent manager
        agent_manager = AgentManager(settings=settings)

        if args.monitor:
            logger.info("Running in monitoring mode")
            agent_manager.run_monitoring_agent()
        elif args.task:
            logger.info(f"Running specific task: {args.task}")
            agent_manager.run_task(args.task)
        else:
            logger.info("Running full autonomous mode")
            agent_manager.run_autonomous()

    except ImportError as e:
        logger.error(f"Failed to import agent modules: {e}")
        logger.error("Please ensure the agent modules are properly installed.")
        logger.error("Run: pip install -e '.[agents]'")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in autonomous mode: {e}")
        if debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
