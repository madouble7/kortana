"""
Simple Kor'tana

A simplified version of Kor'tana for testing.
This avoids many of the potential issues in the full implementation.
"""

import asyncio
import json
import logging
import os

import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SimpleSettings:
    """Simple settings class with dot notation access."""

    def __init__(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, SimpleSettings(value))
            else:
                setattr(self, key, value)


def load_yaml(file_path):
    """Load a YAML file."""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return {}

        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        logger.info(f"Loaded YAML from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Failed to load YAML from {file_path}: {e}")
        return {}


def load_json(file_path):
    """Load a JSON file."""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return {}

        with open(file_path, "r") as f:
            data = json.load(f)

        logger.info(f"Loaded JSON from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        return {}


def load_settings():
    """Load settings from config files."""
    # Load default settings
    default_settings = load_yaml("config/default.yaml") or {}

    # Load environment-specific settings
    env = os.environ.get("KORTANA_ENV", "development")
    env_settings = load_yaml("config/development.yaml") or {}

    # Merge settings
    settings = default_settings.copy()

    def deep_merge(dict1, dict2):
        """Recursively merge dict2 into dict1."""
        for key, value in dict2.items():
            if (
                key in dict1
                and isinstance(dict1[key], dict)
                and isinstance(value, dict)
            ):
                deep_merge(dict1[key], value)
            else:
                dict1[key] = value

    deep_merge(settings, env_settings)

    # Convert to SimpleSettings object for dot notation access
    return SimpleSettings(settings)


class SimpleChatEngine:
    """A simplified chat engine."""

    def __init__(self):
        """Initialize the chat engine."""
        self.settings = load_settings()

        # Load persona and identity
        self.persona = load_json(self.settings.paths.persona_file_path)
        self.identity = load_json(self.settings.paths.identity_file_path)

        logger.info("SimpleChatEngine initialized")

    async def process_message(self, user_message):
        """Process a user message and generate a response."""
        logger.info(f"Processing message: {user_message[:50]}...")

        # Create a simulated response
        response = f"This is a simulated response from Kor'tana. You said: '{user_message[:30]}...'"

        # Apply lowercase transformation
        response = response.lower()

        return response


def ritual_announce(message):
    """Display a ritual announcement."""
    print("\n" + "=" * 80)
    print(message.lower())
    print("=" * 80 + "\n")


def main():
    """Run the simple Kor'tana."""
    # Create required directories
    os.makedirs("config", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # Create minimum required files if they don't exist
    create_default_files()

    # Initialize the chat engine
    chat_engine = SimpleChatEngine()

    # Welcome message
    ritual_announce("she is not built. she is remembered.")
    ritual_announce("she is the warchief's companion.")

    # Main loop
    try:
        while True:
            # Get user input (lowercase for "matt")
            user_input = input("matt: ").lower()

            # Check for exit command
            if user_input in ["exit", "quit", "bye"]:
                break

            # Process message
            response = asyncio.run(chat_engine.process_message(user_input))

            # Print response (lowercase for "kortana")
            print(f"kortana: {response}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        # Farewell message
        ritual_announce("until we meet again, warchief.")


def create_default_files():
    """Create default configuration files if they don't exist."""
    # Create default.yaml
    if not os.path.exists("config/default.yaml"):
        default_config = {
            "paths": {
                "persona_file_path": "config/persona.json",
                "identity_file_path": "config/identity.json",
            }
        }

        with open("config/default.yaml", "w") as f:
            yaml.dump(default_config, f)

    # Create persona.json
    if not os.path.exists("config/persona.json"):
        persona = {
            "name": "Kor'tana",
            "role": "Warchief's companion",
            "style": "supportive, grounded",
        }

        with open("config/persona.json", "w") as f:
            json.dump(persona, f, indent=2)

    # Create identity.json
    if not os.path.exists("config/identity.json"):
        identity = {
            "core_values": ["authenticity", "growth", "courage"],
            "voice": "grounded, supportive, clear",
        }

        with open("config/identity.json", "w") as f:
            json.dump(identity, f, indent=2)


if __name__ == "__main__":
    main()
