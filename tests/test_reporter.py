#!/usr/bin/env python3
"""
Kor'tana Test Summary Reporter
==============================

High-level test summary reporter for faster relay diagnostics during development.
Provides compact, readable summaries of test status and highlights failing modules.

Usage:
    python tests/test_reporter.py
    python -m pytest tests/test_reporter.py -v
"""

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)


@dataclass
class TestResult:
    """Individual test result data"""

    name: str
    status: str  # 'PASSED', 'FAILED', 'SKIPPED', 'ERROR'
    duration: float
    error_message: Optional[str] = None
    file_path: Optional[str] = None


@dataclass
class ModuleResult:
    """Test module result summary"""

    module_name: str
    file_path: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    status: str  # 'CLEAN', 'ISSUES', 'BROKEN', 'NOT_TESTED'
    issues: List[str]


class TestSummaryReporter:
    """Comprehensive test summary reporter for Kor'tana project"""

    def __init__(self, project_root: str = None):
        """Initialize the test reporter"""
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )
        self.tests_dir = self.project_root / "tests"
        self.src_dir = self.project_root / "src"
        self.results: List[ModuleResult] = []

    def discover_test_files(self) -> List[Path]:
        """Discover all test files in the tests directory"""
        test_files = []
        for pattern in ["test_*.py", "*_test.py"]:
            test_files.extend(self.tests_dir.glob(pattern))
        return sorted(test_files)

    def discover_source_files(self) -> List[Path]:
        """Discover all Python source files that should have tests"""
        source_files = []
        for py_file in self.src_dir.rglob("*.py"):
            if not py_file.name.startswith("__"):
                source_files.append(py_file)
        return sorted(source_files)

    def run_individual_test_module(self, test_file: Path) -> ModuleResult:
        """Run a single test module and collect results"""
        module_name = test_file.stem

        try:
            # Run pytest on individual module with JSON report
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(test_file),
                "--tb=short",
                "-v",
                "--json-report",
                "--json-report-file=/tmp/test_report.json",
            ]

            start_time = time.time()
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )
            duration = time.time() - start_time

            # Parse results
            passed = result.stdout.count(" PASSED")
            failed = result.stdout.count(" FAILED")
            skipped = result.stdout.count(" SKIPPED")
            errors = result.stdout.count(" ERROR")

            total_tests = passed + failed + skipped + errors

            # Determine status
            if result.returncode == 0 and failed == 0 and errors == 0:
                status = "CLEAN"
                issues = []
            elif failed > 0 or errors > 0:
                status = "BROKEN" if errors > 0 else "ISSUES"
                issues = self._extract_error_messages(result.stdout, result.stderr)
            else:
                status = "CLEAN"
                issues = []

            return ModuleResult(
                module_name=module_name,
                file_path=str(test_file),
                total_tests=total_tests,
                passed=passed,
                failed=failed,
                skipped=skipped,
                errors=errors,
                duration=duration,
                status=status,
                issues=issues,
            )

        except Exception as e:
            return ModuleResult(
                module_name=module_name,
                file_path=str(test_file),
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration=0.0,
                status="BROKEN",
                issues=[f"Test execution failed: {str(e)}"],
            )

    def _extract_error_messages(self, stdout: str, stderr: str) -> List[str]:
        """Extract meaningful error messages from test output"""
        issues = []

        # Parse stderr for import errors
        if "ImportError" in stderr:
            for line in stderr.split("\n"):
                if "ImportError" in line:
                    issues.append(f"Import Error: {line.strip()}")

        # Parse stdout for test failures
        if "FAILED" in stdout:
            lines = stdout.split("\n")
            for i, line in enumerate(lines):
                if " FAILED" in line:
                    issues.append(f"Test Failed: {line.strip()}")
                    # Try to get error context
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if lines[j].strip() and not lines[j].startswith("="):
                            issues.append(f"  → {lines[j].strip()}")
                            break

        # Parse for collection errors
        if "error during collection" in stdout.lower():
            for line in stdout.split("\n"):
                if "ERROR" in line and "collecting" in line:
                    issues.append(f"Collection Error: {line.strip()}")

        return issues[:10]  # Limit to first 10 issues

    def check_code_coverage(self) -> Dict[str, str]:
        """Check which source files have corresponding tests"""
        coverage = {}
        source_files = self.discover_source_files()
        test_files = self.discover_test_files()

        # Create mapping of test files to source files
        test_modules = {f.stem.replace("test_", ""): f for f in test_files}

        for src_file in source_files:
            module_name = src_file.stem
            relative_path = src_file.relative_to(self.src_dir)

            # Check for direct test file
            if f"test_{module_name}" in [f.stem for f in test_files]:
                coverage[str(relative_path)] = "TESTED"
            # Check for integration tests
            elif any(module_name in test_file.stem for test_file in test_files):
                coverage[str(relative_path)] = "PARTIAL"
            else:
                coverage[str(relative_path)] = "NOT_TESTED"

        return coverage

    def run_full_test_suite(self) -> Dict[str, any]:
        """Run the complete test suite and generate comprehensive report"""
        print("🔍 Kor'tana Test Summary Reporter")
        print("=" * 50)
        print(f"📁 Project: {self.project_root}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Discover test files
        test_files = self.discover_test_files()
        print(f"📋 Discovered {len(test_files)} test modules")

        # Run each test module
        print("\n🧪 Running Test Modules:")
        print("-" * 30)

        for test_file in test_files:
            print(f"⚡ Testing {test_file.name}...", end=" ", flush=True)
            result = self.run_individual_test_module(test_file)
            self.results.append(result)

            # Status emoji
            status_emoji = {
                "CLEAN": "✅",
                "ISSUES": "⚠️",
                "BROKEN": "❌",
                "NOT_TESTED": "⏭️",
            }
            print(f"{status_emoji.get(result.status, '❓')} {result.status}")

        # Generate summary
        return self._generate_summary()

    def _generate_summary(self) -> Dict[str, any]:
        """Generate comprehensive test summary"""
        total_modules = len(self.results)
        clean_modules = len([r for r in self.results if r.status == "CLEAN"])
        issue_modules = len([r for r in self.results if r.status == "ISSUES"])
        broken_modules = len([r for r in self.results if r.status == "BROKEN"])

        total_tests = sum(r.total_tests for r in self.results)
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)

        total_duration = sum(r.duration for r in self.results)

        # Check code coverage
        coverage = self.check_code_coverage()
        tested_files = len([k for k, v in coverage.items() if v == "TESTED"])
        partial_files = len([k for k, v in coverage.items() if v == "PARTIAL"])
        untested_files = len([k for k, v in coverage.items() if v == "NOT_TESTED"])

        summary = {
            "timestamp": datetime.now().isoformat(),
            "project_status": (
                "STABLE"
                if broken_modules == 0 and issue_modules == 0
                else "ISSUES" if broken_modules == 0 else "BROKEN"
            ),
            "modules": {
                "total": total_modules,
                "clean": clean_modules,
                "issues": issue_modules,
                "broken": broken_modules,
            },
            "tests": {
                "total": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "errors": total_errors,
                "skipped": total_skipped,
            },
            "coverage": {
                "tested": tested_files,
                "partial": partial_files,
                "untested": untested_files,
                "total_source_files": len(coverage),
            },
            "performance": {
                "total_duration": round(total_duration, 2),
                "avg_module_time": round(total_duration / max(total_modules, 1), 2),
            },
            "details": self.results,
        }

        self._print_summary(summary)
        return summary

    def _print_summary(self, summary: Dict[str, any]):
        """Print formatted summary to console"""
        print("\n" + "=" * 50)
        print("📊 KOR'TANA TEST SUMMARY REPORT")
        print("=" * 50)

        # Overall status
        status_emoji = {"STABLE": "🟢", "ISSUES": "🟡", "BROKEN": "🔴"}
        print(
            f"🎯 Overall Status: {status_emoji.get(summary['project_status'], '❓')} {summary['project_status']}"
        )
        print()

        # Module summary
        modules = summary["modules"]
        print("📦 Module Summary:")
        print(f"   Total Modules: {modules['total']}")
        print(f"   ✅ Clean: {modules['clean']}")
        print(f"   ⚠️  Issues: {modules['issues']}")
        print(f"   ❌ Broken: {modules['broken']}")
        print()

        # Test summary
        tests = summary["tests"]
        print("🧪 Test Summary:")
        print(f"   Total Tests: {tests['total']}")
        print(f"   ✅ Passed: {tests['passed']}")
        print(f"   ❌ Failed: {tests['failed']}")
        print(f"   💥 Errors: {tests['errors']}")
        print(f"   ⏭️  Skipped: {tests['skipped']}")
        print()

        # Coverage summary
        coverage = summary["coverage"]
        coverage_pct = round(
            (coverage["tested"] / max(coverage["total_source_files"], 1)) * 100, 1
        )
        print("📋 Coverage Summary:")
        print(f"   📁 Total Source Files: {coverage['total_source_files']}")
        print(f"   ✅ Tested: {coverage['tested']} ({coverage_pct}%)")
        print(f"   🔄 Partial: {coverage['partial']}")
        print(f"   ❌ Untested: {coverage['untested']}")
        print()

        # Performance
        perf = summary["performance"]
        print("⚡ Performance:")
        print(f"   Total Duration: {perf['total_duration']}s")
        print(f"   Avg Module Time: {perf['avg_module_time']}s")
        print()

        # Detailed issues
        if modules["broken"] > 0 or modules["issues"] > 0:
            print("🚨 ISSUES DETECTED:")
            print("-" * 30)
            for result in self.results:
                if result.status in ["BROKEN", "ISSUES"]:
                    print(f"\n❌ {result.module_name} ({result.status}):")
                    for issue in result.issues[:3]:  # Show first 3 issues
                        print(f"   • {issue}")
                    if len(result.issues) > 3:
                        print(f"   ... and {len(result.issues) - 3} more issues")

        # Quick fix recommendations
        print("\n💡 QUICK FIX RECOMMENDATIONS:")
        print("-" * 30)
        if modules["broken"] > 0:
            print("🔧 Priority 1: Fix broken modules (import/syntax errors)")
        if modules["issues"] > 0:
            print("🔧 Priority 2: Address failing tests")
        if coverage["untested"] > 0:
            print(f"🔧 Priority 3: Add tests for {coverage['untested']} untested files")

        print("\n" + "=" * 50)
        print(f"⏰ Report completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Main entry point for the test reporter"""
    import argparse

    parser = argparse.ArgumentParser(description="Kor'tana Test Summary Reporter")
    parser.add_argument("--project-root", help="Project root directory", default=None)
    parser.add_argument("--json", help="Output JSON report to file", default=None)
    parser.add_argument("--quick", help="Quick status check only", action="store_true")

    args = parser.parse_args()

    reporter = TestSummaryReporter(args.project_root)

    if args.quick:
        # Quick status check
        test_files = reporter.discover_test_files()
        coverage = reporter.check_code_coverage()
        print(f"📋 Test modules: {len(test_files)}")
        print(
            f"📁 Source coverage: {len([v for v in coverage.values() if v == 'TESTED'])}/{len(coverage)} files tested"
        )
    else:
        # Full report
        summary = reporter.run_full_test_suite()

        if args.json:
            with open(args.json, "w") as f:
                json.dump(summary, f, indent=2, default=str)
            print(f"📄 JSON report saved to: {args.json}")


if __name__ == "__main__":
    main()
