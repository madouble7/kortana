#!/usr/bin/env python3
"""
Script to display coverage targets for critical modules in Kor'tana.
This is an informational helper that shows which modules require higher coverage
and provides commands to check their coverage. It does not enforce coverage targets.
"""

from pathlib import Path


CRITICAL_MODULES = {
    "security": {
        "path": "src/kortana/modules/security/",
        "target": 90,
        "description": "Security module (authentication, authorization, encryption)",
    },
    "core": {
        "path": "src/kortana/core/",
        "target": 85,
        "description": "Core functionality",
    },
    "brain": {
        "path": "kortana.brain",
        "target": 85,
        "description": "Brain core logic",
    },
    "model_router": {
        "path": "kortana.model_router",
        "target": 85,
        "description": "Model routing logic",
    },
}


def main():
    """Display coverage targets for critical modules."""
    project_root = Path(__file__).parent.parent
    
    print("=" * 80)
    print("Kor'tana Critical Module Coverage Targets")
    print("=" * 80)
    print()
    print("This script shows coverage targets for critical modules.")
    print("Run the suggested pytest commands to check actual coverage.")
    print()
    
    for name, info in CRITICAL_MODULES.items():
        # For directory paths, check if they exist
        if "/" in info["path"]:
            module_path = project_root / info["path"]
            if not module_path.exists():
                print(f"⚠️  {name}: Module not found at {info['path']}")
                continue
        
        print(f"📊 {name}:")
        print(f"   Coverage Target: {info['target']}%")
        print(f"   Description: {info['description']}")
        print(f"   Command: pytest --cov={info['path']}")
        print()
    
    print("=" * 80)
    print("Quick Reference")
    print("=" * 80)
    print()
    print("Check all modules:")
    print("  pytest --cov=src")
    print()
    print("Check specific modules:")
    for name, info in CRITICAL_MODULES.items():
        print(f"  pytest --cov={info['path']}  # {name}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
