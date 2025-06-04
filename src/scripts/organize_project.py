"""
Organize Project Structure

This script creates the standard project structure for the Kor'tana project
and moves files to their appropriate directories.
"""

import os
import shutil
from pathlib import Path


def ensure_dirs():
    """Create the standard directory structure."""
    directories = [
        "scripts",
        "tests/unit",
        "tests/integration",
        "docs",
        ".vscode",
        "config",
        "data",
        "logs",
    ]

    # Create directories
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")


def move_scripts():
    """Move scripts to the appropriate directories."""
    # List of scripts to move to scripts/ directory
    script_files = [
        "setup_directories.py",
        "check_dependencies.py",
        "fix_permissions.py",
        "fix_syntax.py",
        "fix_brain.py",
        "fix_indentation.py",
        "run_with_output.py",
        "admin_setup.py",
    ]

    # Move root scripts to scripts/
    for script in script_files:
        if os.path.exists(script):
            dest = f"scripts/{script}"
            shutil.copy2(script, dest)
            print(f"Moved {script} to {dest}")
        elif os.path.exists(f"src/{script}"):
            dest = f"scripts/{script}"
            shutil.copy2(f"src/{script}", dest)
            print(f"Moved src/{script} to {dest}")


def create_gitignore():
    """Create or update the .gitignore file."""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environments
.env
.venv
env/
venv/
venv311/
ENV/
test_env/
env.bak/
venv.bak/

# IDE
.idea/
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json
*.code-workspace
.history/

# OS specific
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Specific for this project
data/memory_journal.jsonl
data/project_memory.jsonl
data/heart.log
data/soul.index.jsonl
data/lit.log.jsonl

# Temp and backup files
*.bak
*.tmp
*~
"""

    # Write to .gitignore file
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)

    print("Created/updated .gitignore file")


def create_vscode_settings():
    """Create VSCode settings file."""
    settings_content = """{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.analysis.extraPaths": [
        "${workspaceFolder}"
    ]
}
"""

    # Create .vscode directory if it doesn't exist
    os.makedirs(".vscode", exist_ok=True)

    # Write settings.json file
    with open(".vscode/settings.json", "w") as f:
        f.write(settings_content)

    print("Created .vscode/settings.json")


def create_readme():
    """Create or update the README.md file."""
    readme_content = """# Kor'tana

The Warchief's AI companion.

## Project Structure

```
kortana/
├── config/           # Configuration files
├── data/             # Data files
├── docs/             # Documentation
├── logs/             # Log files
├── scripts/          # Utility scripts
├── src/              # Source code
│   ├── kortana/      # Main Kor'tana package
│   │   ├── agents/   # Autonomous agents
│   │   ├── core/     # Core functionality
│   │   └── memory/   # Memory systems
│   └── llm_clients/  # LLM API clients
└── tests/            # Test suite
    ├── integration/  # Integration tests
    └── unit/         # Unit tests
```

## Setup and Installation

1. Create a virtual environment:
   ```
   python -m venv venv311
   ```

2. Activate the virtual environment:
   ```
   venv311\\Scripts\\activate
   ```

3. Install dependencies:
   ```
   pip install pyyaml apscheduler pydantic
   ```

4. Set up the directory structure and placeholder configs:
   ```
   python scripts/setup_directories.py
   ```

5. Check dependencies:
   ```
   python scripts/check_dependencies.py
   ```

## Running Kor'tana

Start the main system:
```
python -m src.kortana.core.brain
```

## Development

### Running Tests
```
python -m pytest tests
```

### Code Style
This project uses Black for formatting and pylint for linting.
"""

    # Write to README.md file
    with open("README.md", "w") as f:
        f.write(readme_content)

    print("Created/updated README.md")


if __name__ == "__main__":
    # Get the project root directory
    os.chdir(Path(__file__).parent.parent.parent)
    print(f"Working in directory: {os.getcwd()}")

    ensure_dirs()
    move_scripts()
    create_gitignore()
    create_vscode_settings()
    create_readme()

    print("Project structure organized successfully!")
