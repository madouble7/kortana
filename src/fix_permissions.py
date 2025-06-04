"""
Fix Permissions

This script creates all necessary directories and files with proper permissions.
"""

import json
import os

import yaml


def ensure_dirs_and_files():
    """Create all necessary directories and files with proper permissions."""
    print("Creating directories...")

    # Create directories
    directories = ["config", "data", "logs"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

    # Create files with explicit write permissions
    print("\nCreating configuration files...")

    # Persona config
    create_file(
        "config/persona.json",
        json.dumps(
            {
                "name": "Kor'tana",
                "role": "Warchief's companion",
                "style": "supportive, grounded",
            },
            indent=2,
        ),
    )

    # Identity config
    create_file(
        "config/identity.json",
        json.dumps(
            {
                "core_values": ["authenticity", "growth", "courage"],
                "voice": "grounded, supportive, clear",
            },
            indent=2,
        ),
    )

    # Models config
    create_file(
        "config/models_config.json",
        json.dumps(
            {
                "default": {"model": "gpt-3.5-turbo", "style": "presence"},
                "fallback": {"model": "gpt-3.5-turbo", "style": "presence"},
            },
            indent=2,
        ),
    )

    # Sacred Trinity config
    create_file(
        "config/sacred_trinity_config.json",
        json.dumps(
            {
                "heart": {"enabled": True, "weight": 0.33},
                "soul": {"enabled": True, "weight": 0.33},
                "lit": {"enabled": True, "weight": 0.33},
            },
            indent=2,
        ),
    )

    # Covenant config
    covenant_content = {
        "principles": [
            "Respect user autonomy",
            "Prioritize user wellbeing",
            "Be truthful and accurate",
            "Protect user privacy",
        ],
        "boundaries": {
            "do_not": [
                "Engage in harmful behavior",
                "Share private information",
                "Pretend to be a human",
                "Make unsubstantiated claims",
            ]
        },
        "language": {
            "voice": "authentic, supportive, clear",
            "tone": "respectful, knowledgeable, kind",
        },
    }
    create_file(
        "config/covenant.yaml", yaml.dump(covenant_content, default_flow_style=False)
    )

    # Default config
    default_config = {
        "api_keys": {
            "openai": "sk-placeholder-value",
            "anthropic": "placeholder-anthropic-key",
            "pinecone": "",
        },
        "debug": False,
        "api": {"host": "127.0.0.1", "port": 8000},
        "models": {"default": "gpt-4", "alternate": "gpt-3.5-turbo"},
        "memory": {"enable_persistent": True, "max_entries": 1000},
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "user": {"name": "Warchief"},
        "paths": {
            "persona_file_path": "config/persona.json",
            "identity_file_path": "config/identity.json",
            "models_config_file_path": "config/models_config.json",
            "sacred_trinity_config_file_path": "config/sacred_trinity_config.json",
            "project_memory_file_path": "data/project_memory.jsonl",
            "covenant_file_path": "config/covenant.yaml",
            "memory_journal_path": "data/memory_journal.jsonl",
            "heart_log_path": "data/heart.log",
            "soul_index_path": "data/soul.index.jsonl",
            "lit_log_path": "data/lit.log.jsonl",
        },
        "agents": {
            "default_llm_id": "gpt-3.5-turbo",
            "types": {
                "coding": {},
                "planning": {},
                "testing": {},
                "monitoring": {"enabled": True, "interval_seconds": 60},
            },
        },
        "pinecone": {"environment": "us-west1-gcp", "index_name": "kortana-memory"},
        "default_llm_id": "gpt-3.5-turbo",
    }
    create_file(
        "config/default.yaml", yaml.dump(default_config, default_flow_style=False)
    )

    # Development config
    dev_config = {
        "debug": True,
        "api": {"host": "127.0.0.1", "port": 8000},
        "default_llm_id": "gpt-3.5-turbo",
        "agents": {"default_llm_id": "gpt-3.5-turbo"},
    }
    create_file(
        "config/development.yaml", yaml.dump(dev_config, default_flow_style=False)
    )

    # Create empty memory files
    create_file("data/memory_journal.jsonl", "")
    create_file("data/project_memory.jsonl", "")
    create_file("data/heart.log", "")
    create_file("data/soul.index.jsonl", "")
    create_file("data/lit.log.jsonl", "")


def create_file(file_path, content):
    """Create a file with the given content and ensure it's writable."""
    try:
        with open(file_path, "w") as f:
            f.write(content)

        # Make sure the file is readable and writable
        os.chmod(file_path, 0o666)

        print(f"Created file: {file_path}")
        return True
    except Exception as e:
        print(f"Error creating file {file_path}: {e}")
        return False


if __name__ == "__main__":
    print("Setting up Kor'tana environment with proper permissions...\n")
    ensure_dirs_and_files()
    print("\nSetup complete!")
    input("Press Enter to continue...")
