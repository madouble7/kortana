#!/usr/bin/env python
"""
Run the Kor'tana test suite with coverage reporting.
"""

import subprocess
import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Run the test suite with coverage and generate reports."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    print("🧪 Running Kor'tana test suite with coverage reporting...")

    # Run pytest with coverage
    result = subprocess.run(
        [
            "pytest",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_html",
            "--cov-report=xml:coverage.xml",
            "tests/",
        ],
        cwd=project_root,
    )

    if result.returncode == 0:
        print("\n✅ All tests passed!")
        print("\nCoverage reports generated:")
        print(f"  - HTML: {project_root / 'coverage_html/index.html'}")
        print(f"  - XML: {project_root / 'coverage.xml'}")
    else:
        print("\n❌ Some tests failed!")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
