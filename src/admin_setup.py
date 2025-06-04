"""
Admin Setup Script

This script creates configuration files with administrative privileges.
Run this script with elevated permissions (Run as Administrator).
"""

import json
import os
import shutil
import tempfile
from pathlib import Path


def setup_with_admin():
    """Set up all necessary files bypassing permissions issues."""
    print("Setting up Kor'tana environment with alternative approach...")

    # Create base directories
    print("\nCreating directories...")
    os.makedirs("config", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    print("\nCreating configuration files with workaround...")

    # Dictionary of file contents
    files = {
        "config/persona.json": json.dumps(
            {
                "name": "Kor'tana",
                "role": "Warchief's companion",
                "style": "supportive, grounded",
            },
            indent=2,
        ),
        "config/identity.json": json.dumps(
            {
                "core_values": ["authenticity", "growth", "courage"],
                "voice": "grounded, supportive, clear",
            },
            indent=2,
        ),
        "config/models_config.json": json.dumps(
            {
                "default": {"model": "gpt-3.5-turbo", "style": "presence"},
                "fallback": {"model": "gpt-3.5-turbo", "style": "presence"},
            },
            indent=2,
        ),
        "config/sacred_trinity_config.json": json.dumps(
            {
                "heart": {"enabled": True, "weight": 0.33},
                "soul": {"enabled": True, "weight": 0.33},
                "lit": {"enabled": True, "weight": 0.33},
            },
            indent=2,
        ),
        "config/covenant.yaml": """principles:
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
        "config/default.yaml": """api_keys:
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
""",
        "config/development.yaml": """debug: true
api:
  host: "127.0.0.1"
  port: 8000
default_llm_id: "gpt-3.5-turbo"
agents:
  default_llm_id: "gpt-3.5-turbo"
""",
        "data/memory_journal.jsonl": "",
        "data/project_memory.jsonl": "",
        "data/heart.log": "",
        "data/soul.index.jsonl": "",
        "data/lit.log.jsonl": "",
    }

    # Create each file
    for file_path, content in files.items():
        try:
            # Use different approaches based on file location
            create_file(file_path, content)
        except Exception as e:
            print(f"Error creating {file_path}: {e}")
            print("Trying alternative method...")
            try:
                create_file_alternative(file_path, content)
            except Exception as e2:
                print(f"Alternative method also failed: {e2}")

    print("\nSetup complete!")


def create_file(file_path, content):
    """Create a file directly."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create empty file first
    if not path.exists():
        path.touch()

    # Open and write content with explicit permissions
    with open(path, "w") as f:
        f.write(content)

    print(f"Created file: {file_path}")


def create_file_alternative(file_path, content):
    """Create a file using a temporary file approach."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
        temp.write(content)
        temp_name = temp.name

    # Create parent directory if needed
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Copy the temporary file to the target location
    shutil.copy2(temp_name, file_path)

    # Remove the temporary file
    os.unlink(temp_name)

    print(f"Created file (alternative method): {file_path}")


def quick_fix_brain_py():
    """Make a quick fix to brain.py to handle both dict and Pydantic models."""
    brain_py_path = "src/kortana/core/brain.py"
    if not os.path.exists(brain_py_path):
        print(f"Cannot find {brain_py_path}")
        return

    try:
        with open(brain_py_path, "r") as f:
            content = f.read()

        # Check if the fix is already applied
        if "# Get monitoring config" in content:
            print("brain.py seems to be already fixed.")
            return

        # Find the ade_tester section and the ade_monitor section
        tester_section = "        self.ade_tester = TestingAgent("
        monitor_section = "        self.ade_monitor = MonitoringAgent("

        if tester_section in content and monitor_section in content:
            # Replace the problematic part
            fixed_content = content.replace(
                f"{tester_section}",
                f"{tester_section}\n            chat_engine_instance=self,\n            llm_client=self.ade_llm_client,\n            covenant_enforcer=self.covenant_enforcer,\n            settings=self.settings\n        )\n        \n        # Get monitoring config (handle both dict and model types)\n        monitoring_config = {{}}\n        if hasattr(self.settings.agents, 'types'):\n            if hasattr(self.settings.agents.types, 'monitoring'):\n                monitoring_config = self.settings.agents.types.monitoring\n            elif isinstance(self.settings.agents.types, dict) and 'monitoring' in self.settings.agents.types:\n                monitoring_config = self.settings.agents.types['monitoring']\n        \n{monitor_section}",
            )

            with open(brain_py_path, "w") as f:
                f.write(fixed_content)

            print("Successfully fixed brain.py")
        else:
            print("Could not find the sections to fix in brain.py")

    except Exception as e:
        print(f"Error fixing brain.py: {e}")


if __name__ == "__main__":
    print("This script will set up the Kor'tana environment and fix any issues.")
    input("Press Enter to continue...")

    setup_with_admin()
    quick_fix_brain_py()

    print("\nSetup and fixes completed.")
    print("You can now run Kor'tana with: python -m src.kortana.core.brain")
    input("Press Enter to continue...")
