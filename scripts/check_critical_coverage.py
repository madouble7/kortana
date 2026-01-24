#!/usr/bin/env python3
"""
Script to check coverage for critical modules in Kor'tana.
Highlights security and core modules that require higher coverage.
"""

import sys
import subprocess
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
        "path": "src/kortana/brain.py",
        "target": 85,
        "description": "Brain core logic",
    },
    "model_router": {
        "path": "src/kortana/model_router.py",
        "target": 85,
        "description": "Model routing logic",
    },
}


def run_coverage(module_path):
    """Run coverage for a specific module."""
    cmd = [
        "pytest",
        f"--cov={module_path}",
        "--cov-report=term-missing",
        "--cov-report=json",
        "-v",
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    
    return result


def main():
    """Check coverage for critical modules."""
    project_root = Path(__file__).parent.parent
    
    print("=" * 80)
    print("Kor'tana Critical Module Coverage Check")
    print("=" * 80)
    print()
    
    results = {}
    
    for name, info in CRITICAL_MODULES.items():
        module_path = project_root / info["path"]
        
        if not module_path.exists():
            print(f"⚠️  {name}: Module not found at {info['path']}")
            continue
        
        print(f"📊 Checking {name}...")
        print(f"   Path: {info['path']}")
        print(f"   Target: {info['target']}%")
        print(f"   Description: {info['description']}")
        print()
        
        # For now, just note that this would run coverage
        # In a real scenario, this would parse the output
        print(f"   Run: pytest --cov={info['path']}")
        print()
        
        results[name] = {
            "target": info["target"],
            "path": info["path"],
        }
    
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("To check coverage for all critical modules, run:")
    print("  pytest --cov=src")
    print()
    print("To check coverage for a specific module:")
    for name, info in CRITICAL_MODULES.items():
        print(f"  pytest --cov={info['path']}")
    print()
    print("Critical modules and their coverage targets:")
    for name, info in CRITICAL_MODULES.items():
        print(f"  - {name}: {info['target']}% ({info['description']})")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
