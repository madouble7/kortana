#!/usr/bin/env python3
"""
Import Update Script for Project Kor'tana Restructuring
Updates imports to use the new src/kortana/ package structure
"""

import re
from pathlib import Path

# Mapping of old imports to new imports
IMPORT_MAPPINGS = {
    # Core imports
    "from kortana.core.autonomous_development_engine import": "from kortana.core.autonomous_development_engine import",
    "from kortana.core.brain import": "from kortana.core.brain import",
    "from kortana.core.core_rituals import": "from kortana.core.core_rituals import",
    "from kortana.core.covenant_enforcer import": "from kortana.core.covenant_enforcer import",
    "from kortana.core.covenant import": "from kortana.core.covenant import",
    # Agent imports
    "from kortana.agents.autonomous_agents import": "from kortana.agents.autonomous_agents import",
    "from kortana.agents.coding_agent import": "from kortana.agents.coding_agent import",
    "from kortana.agents.monitoring_agent import": "from kortana.agents.monitoring_agent import",
    "from kortana.agents.planning_agent import": "from kortana.agents.planning_agent import",
    "from kortana.agents.testing_agent import": "from kortana.agents.testing_agent import",
    # Memory imports
    "from kortana.memory.memory_manager import": "from kortana.memory.memory_manager import",
    "from kortana.memory.memory_store import": "from kortana.memory.memory_store import",
    "from kortana.memory.memory import": "from kortana.memory.memory import",
    # LLM client imports
    "from kortana.llm_clients.": "from kortana.llm_clients.",
    "import kortana.llm_clients.": "import kortana.llm_clients.",
    # Utils imports
    "from kortana.utils.": "from kortana.utils.",
    "import kortana.utils.": "import kortana.utils.",
    # Tools imports
    "from kortana.tools.": "from kortana.tools.",
    "import kortana.tools.": "import kortana.tools.",
    # Core directory imports
    "from kortana.core.": "from kortana.core.",
    "import kortana.core.": "import kortana.core.",
    # Config imports
    "from kortana import config": "from kortana from kortana import config",
    "from kortana.config import": "from kortana.config import",
}


def update_imports_in_file(file_path: Path) -> bool:
    """Update imports in a single file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Apply import mappings
        for old_import, new_import in IMPORT_MAPPINGS.items():
            content = content.replace(old_import, new_import)

        # Handle relative imports within the package
        if "src/kortana" in str(file_path):
            # Convert absolute imports to relative for files within kortana package
            content = re.sub(
                r"from kortana\.([^\.]+) import", r"from .\1 import", content
            )

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated imports in: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def update_all_imports(root_dir: str = ".") -> None:
    """Update imports in all Python files"""
    root_path = Path(root_dir)
    updated_files = []

    # Find all Python files
    python_files = list(root_path.rglob("*.py"))

    print(f"Found {len(python_files)} Python files to check...")

    for file_path in python_files:
        # Skip __pycache__ directories
        if "__pycache__" in str(file_path):
            continue

        # Skip virtual environment directories
        if "venv" in str(file_path) or ".venv" in str(file_path):
            continue

        if update_imports_in_file(file_path):
            updated_files.append(file_path)

    print(f"\nUpdated imports in {len(updated_files)} files:")
    for file_path in updated_files:
        print(f"  - {file_path}")


if __name__ == "__main__":
    update_all_imports()
