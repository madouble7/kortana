"""
Direct Run Script

Runs Kor'tana directly without using batch files.
"""

import os
import sys
from pathlib import Path


def ensure_dirs_and_files():
    """Ensure all required directories and files exist."""
    # Create directories
    os.makedirs("config", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Create files if they don't exist
    create_file_if_not_exists(
        "config/default.yaml",
        """
# Default configuration for Kor'tana
api_keys:
  openai: "sk-placeholder-value"
  anthropic: "placeholder-anthropic-key"
default_llm_id: "gpt-3.5-turbo"
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
    monitoring:
      enabled: true
      interval_seconds: 60
""",
    )

    create_file_if_not_exists(
        "config/persona.json",
        """
{
  "name": "Kor'tana",
  "role": "Warchief's companion",
  "style": "supportive, grounded"
}
""",
    )

    create_file_if_not_exists(
        "config/identity.json",
        """
{
  "core_values": ["authenticity", "growth", "courage"],
  "voice": "grounded, supportive, clear"
}
""",
    )

    create_file_if_not_exists(
        "config/models_config.json",
        """
{
  "default": {"model": "gpt-3.5-turbo", "style": "presence"},
  "fallback": {"model": "gpt-3.5-turbo", "style": "presence"}
}
""",
    )

    create_file_if_not_exists(
        "config/sacred_trinity_config.json",
        """
{
  "heart": {"enabled": true, "weight": 0.33},
  "soul": {"enabled": true, "weight": 0.33},
  "lit": {"enabled": true, "weight": 0.33}
}
""",
    )

    create_file_if_not_exists(
        "config/covenant.yaml",
        """
principles:
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
""",
    )


def create_file_if_not_exists(file_path, content):
    """Create a file with the given content if it doesn't already exist."""
    path = Path(file_path)
    if not path.exists():
        print(f"Creating {file_path}")
        with open(path, "w") as f:
            f.write(content)


def main():
    """Run Kor'tana directly."""
    print("Preparing environment...")
    ensure_dirs_and_files()

    print("\nStarting Kor'tana core brain...\n")
    # Use the Python interpreter to run the module
    # This avoids any issues with batch files or PowerShell
    os.system(f"{sys.executable} -m src.kortana.core.brain")

    return 0


if __name__ == "__main__":
    sys.exit(main())
