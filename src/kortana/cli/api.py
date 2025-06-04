"""
API server CLI entry point for Kor'tana.
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
    """Start the Kor'tana API server."""
    parser = argparse.ArgumentParser(description="Kor'tana API Server")
    parser.add_argument(
        "--host", default=None, help="Host to bind the server to (default: from config)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind the server to (default: from config)",
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--config", default=None, help="Path to config directory")
    parser.add_argument(
        "--env", default=None, help="Environment to use (development, production, etc.)"
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
    host = args.host or getattr(settings.api, "host", "127.0.0.1")
    port = args.port or getattr(settings.api, "port", 8000)
    debug = args.debug or getattr(settings, "debug", False)

    # Initialize logging
    log_level = "DEBUG" if debug else getattr(settings.logging, "level", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=getattr(
            settings.logging,
            "format",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        ),
    )

    # Import here to avoid circular imports
    from kortana.core.api_server import start_server

    logger.info(f"Starting Kor'tana API server on {host}:{port} (debug={debug})")

    # Start the server
    start_server(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
