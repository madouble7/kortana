#!/usr/bin/env python3
"""
Kor'tana Test Suite Runner
Complete test execution with reporting
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class TestRunner:
    """Run and report on test execution."""

    def __init__(self):
        self.repo_root = Path(r"c:\kortana")
        self.venv_python = (
            self.repo_root / ".kortana_config_test_env" / "Scripts" / "python.exe"
        )
        self.src_path = self.repo_root / "src"

    def setup_environment(self):
        """Configure environment variables."""
        os.chdir(str(self.repo_root))
        os.environ["PYTHONPATH"] = str(self.src_path)
        os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

    def verify_setup(self) -> bool:
        """Verify all components are in place."""
        print("=" * 70)
        print("VERIFICATION CHECK")
        print("=" * 70)

        checks = [
            ("Virtual Environment", self.venv_python.exists()),
            ("Source Directory", self.src_path.exists()),
            ("Tests Directory", (self.repo_root / "tests").exists()),
            ("pytest Module", self._check_pytest()),
            ("kortana Package", self._check_kortana_package()),
        ]

        for check_name, result in checks:
            status = "✓" if result else "✗"
            print(f"{status} {check_name}")

        all_pass = all(r for _, r in checks)
        print()
        return all_pass

    def _check_pytest(self) -> bool:
        """Check if pytest is installed."""
        result = subprocess.run(
            [str(self.venv_python), "-m", "pip", "show", "pytest"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def _check_kortana_package(self) -> bool:
        """Check if kortana package is importable."""
        result = subprocess.run(
            [str(self.venv_python), "-c", "import kortana"],
            capture_output=True,
            text=True,
            env=os.environ,
        )
        return result.returncode == 0

    def discover_tests(self) -> int:
        """Discover  and count test items."""
        print("=" * 70)
        print("TEST DISCOVERY")
        print("=" * 70)

        result = subprocess.run(
            [str(self.venv_python), "-m", "pytest", "tests/", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            env=os.environ,
            cwd=str(self.repo_root),
        )

        print(result.stdout)

        # Parse output to get count
        lines = result.stdout.split("\n")
        for line in lines:
            if "collected" in line.lower() or "test" in line.lower():
                print(f"Discovery Result: {line}")
        print()

        return result.returncode

    def run_tests(self) -> tuple[int, str]:
        """Execute all tests."""
        print("=" * 70)
        print("EXECUTING TESTS")
        print("=" * 70)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        result = subprocess.run(
            [
                str(self.venv_python),
                "-m",
                "pytest",
                "tests/",
                "-v",
                "--tb=short",
                "--timeout=60",
            ],
            env=os.environ,
            cwd=str(self.repo_root),
        )

        return result.returncode, result.stdout if result.stdout else ""

    def generate_report(self, test_result: int):
        """Generate final report."""
        print("\n" + "=" * 70)
        print("TEST EXECUTION REPORT")
        print("=" * 70)

        if test_result == 0:
            print("✓ ALL TESTS PASSED")
        else:
            print("✗ SOME TESTS FAILED")

        print("\nNext Steps:")
        print("1. Review any test failures above")
        print("2. Fix failing tests")
        print("3. Run specific test: pytest tests/test_name.py -v")
        print("4. Check TEST_EXECUTION_GUIDE.md for more options\n")

        return test_result

    def run(self) -> int:
        """Execute full test workflow."""
        print("\n")
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║          KOR'TANA AUTOMATED TEST SUITE                        ║")
        print("╚════════════════════════════════════════════════════════════════╝\n")

        self.setup_environment()

        # Step 1: Verify setup
        if not self.verify_setup():
            print("\n✗ Setup verification failed. Cannot run tests.")
            return 1

        # Step 2: Discover tests
        if self.discover_tests() != 0:
            print("⚠ Test discovery warnings (non-critical)")

        # Step 3: Run tests
        test_result, output = self.run_tests()

        # Step 4: Generate report
        final_result = self.generate_report(test_result)

        return final_result


def main():
    """Main entry point."""
    runner = TestRunner()
    exit_code = runner.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
