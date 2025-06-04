"""
Setup and Run Batch 1

This script sets up the environment for Batch 1 of the Kor'tana project
and runs the brain module.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Set up and run Kor'tana Batch 1."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"Working in directory: {os.getcwd()}")

    # Create directories
    print("\nCreating required directories...")
    os.makedirs("config", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Create config files
    create_config_files()

    # Create empty data files
    create_data_files()

    print("\nStarting Kor'tana...")
    # Set PYTHONPATH to include the project root
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    # Run the brain module
    try:
        subprocess.run(
            [sys.executable, "-m", "src.kortana.core.brain"], env=env, check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running Kor'tana: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nKor'tana was interrupted by user.")

    return 0


def create_config_files():
    """Create required configuration files."""
    print("\nCreating configuration files...")

    # Default configuration
    default_yaml = """api_keys:
  openai: "sk-placeholder-value"
  anthropic: "placeholder-anthropic-key"
  pinecone: ""
debug: false
api:
  host: "127.0.0.1"
  port: 8000
models:
  default: "gpt-4"
  alternate: "gpt-3.5-turbo"
memory:
  enable_persistent: true
  max_entries: 1000
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
user:
  name: "Warchief"
paths:
  persona_file_path: "config/persona.json"
  identity_file_path: "config/identity.json"
  models_config_file_path: "config/models_config.json"
  sacred_trinity_config_file_path: "config/sacred_trinity_config.json"
  project_memory_file_path: "data/project_memory.jsonl"
  covenant_file_path: "config/covenant.yaml"
  memory_journal_path: "data/memory_journal.jsonl"
  heart_log_path: "data/heart.log"
  soul_index_path: "data/soul.index.jsonl"
  lit_log_path: "data/lit.log.jsonl"
agents:
  default_llm_id: "gpt-3.5-turbo"
  types:
    coding: {}
    planning: {}
    testing: {}
    monitoring:
      enabled: true
      interval_seconds: 60
pinecone:
  environment: "us-west1-gcp"
  index_name: "kortana-memory"
default_llm_id: "gpt-3.5-turbo"
"""
    create_file("config/default.yaml", default_yaml)

    # Development configuration
    dev_yaml = """debug: true
api:
  host: "127.0.0.1"
  port: 8000
default_llm_id: "gpt-3.5-turbo"
agents:
  default_llm_id: "gpt-3.5-turbo"
"""
    create_file("config/development.yaml", dev_yaml)

    # Persona configuration
    persona_json = """{
  "name": "Kor'tana",
  "role": "Warchief's companion",
  "style": "supportive, grounded"
}"""
    create_file("config/persona.json", persona_json)

    # Identity configuration
    identity_json = """{
  "core_values": ["authenticity", "growth", "courage"],
  "voice": "grounded, supportive, clear"
}"""
    create_file("config/identity.json", identity_json)

    # Models configuration
    models_json = """{
  "default": {"model": "gpt-3.5-turbo", "style": "presence"},
  "fallback": {"model": "gpt-3.5-turbo", "style": "presence"}
}"""
    create_file("config/models_config.json", models_json)

    # Sacred Trinity configuration
    trinity_json = """{
  "heart": {"enabled": true, "weight": 0.33},
  "soul": {"enabled": true, "weight": 0.33},
  "lit": {"enabled": true, "weight": 0.33}
}"""
    create_file("config/sacred_trinity_config.json", trinity_json)

    # Covenant configuration
    covenant_yaml = """principles:
  - "Respect user autonomy"
  - "Prioritize user wellbeing"
  - "Be truthful and accurate"
  - "Protect user privacy"
boundaries:
  do_not:
    - "Engage in harmful behavior"
    - "Share private information"
    - "Pretend to be a human"
    - "Make unsubstantiated claims"
language:
  voice: "authentic, supportive, clear"
  tone: "respectful, knowledgeable, kind"
"""
    create_file("config/covenant.yaml", covenant_yaml)


def create_data_files():
    """Create empty data files."""
    print("\nCreating data files...")
    create_file("data/memory_journal.jsonl", "")
    create_file("data/project_memory.jsonl", "")
    create_file("data/heart.log", "")
    create_file("data/soul.index.jsonl", "")
    create_file("data/lit.log.jsonl", "")


def create_file(file_path, content):
    """Create a file with the given content."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write the file
        with open(file_path, "w") as f:
            f.write(content)

        print(f"Created {file_path}")
        return True
    except Exception as e:
        print(f"Error creating {file_path}: {e}")
        return False


if __name__ == "__main__":
    sys.exit(main())
