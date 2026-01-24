#!/usr/bin/env python3
"""
Script to run tests with coverage reporting for Kor'tana project.
This script provides easy access to coverage reports for developers.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run pytest with coverage and display results."""
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    
    print("=" * 70)
    print("Kor'tana Test Coverage Report")
    print("=" * 70)
    print()
    
    # Run pytest with coverage
    cmd = [
        "pytest",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        "-v"
    ]
    
    # Add any additional arguments passed to the script
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, cwd=project_root)
    
    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✓ Tests passed!")
    else:
        print("✗ Tests failed!")
    print()
    print("Coverage reports generated:")
    print(f"  - HTML: {project_root / 'htmlcov' / 'index.html'}")
    print(f"  - XML:  {project_root / 'coverage.xml'}")
    print()
    print("To view HTML report:")
    print(f"  open {project_root / 'htmlcov' / 'index.html'}")
    print("=" * 70)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
