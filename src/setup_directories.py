"""
Setup Directories

This script creates the required directories for the Kor'tana system.
"""

import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def create_required_dirs():
    """Create all required directories."""
    # Change to project root directory
    os.chdir(PROJECT_ROOT)
    print(f"Working in directory: {os.getcwd()}")

    # List of directories to create
    dirs = ["config", "data", "logs"]

    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

    # Create placeholder config files
    create_placeholder_configs()

    print("Directory setup complete.")


def create_placeholder_configs():
    """Create placeholder config files."""
    # Persona
    persona_path = "config/persona.json"
    if not os.path.exists(persona_path):
        with open(persona_path, "w") as f:
            f.write(
                '{\n  "name": "Kor\'tana",\n  "role": "Warchief\'s companion",\n  "style": "supportive, grounded"\n}'
            )
        print(f"Created placeholder: {persona_path}")

    # Identity
    identity_path = "config/identity.json"
    if not os.path.exists(identity_path):
        with open(identity_path, "w") as f:
            f.write(
                '{\n  "core_values": ["authenticity", "growth", "courage"],\n  "voice": "grounded, supportive, clear"\n}'
            )
        print(f"Created placeholder: {identity_path}")

    # Models config
    models_path = "config/models_config.json"
    if not os.path.exists(models_path):
        with open(models_path, "w") as f:
            f.write(
                '{\n  "default": {"model": "gpt-4", "style": "presence"},\n  "fallback": {"model": "gpt-3.5-turbo", "style": "presence"}\n}'
            )
        print(f"Created placeholder: {models_path}")

    # Sacred Trinity config
    trinity_path = "config/sacred_trinity_config.json"
    if not os.path.exists(trinity_path):
        with open(trinity_path, "w") as f:
            f.write(
                '{\n  "heart": {"enabled": true, "weight": 0.33},\n  "soul": {"enabled": true, "weight": 0.33},\n  "lit": {"enabled": true, "weight": 0.33}\n}'
            )
        print(f"Created placeholder: {trinity_path}")

    # Covenant
    covenant_path = "config/covenant.yaml"
    if not os.path.exists(covenant_path):
        with open(covenant_path, "w") as f:
            f.write(
                'principles:\n  - "Respect user autonomy"\n  - "Prioritize user wellbeing"\n  - "Be truthful and accurate"\n  - "Protect user privacy"\nboundaries:\n  do_not:\n    - "Engage in harmful behavior"\n    - "Share private information"\n    - "Pretend to be a human"\n    - "Make unsubstantiated claims"\nlanguage:\n  voice: "authentic, supportive, clear"\n  tone: "respectful, knowledgeable, kind"'
            )
        print(f"Created placeholder: {covenant_path}")


if __name__ == "__main__":
    create_required_dirs()
