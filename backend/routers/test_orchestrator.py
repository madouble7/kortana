"""
Test Orchestrator for Kor'tana Autonomous System

Handles automatic test execution, coverage checking, and validation.
"""

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from logger import setup_logging

router = APIRouter()
logger = setup_logging()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
KORTANA_BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")


class TestOrchestrationError(Exception):
    """Raised when test orchestration fails"""

    pass


@dataclass
class TestResult:
    """Test execution result"""

    success: bool
    passed: int = 0
    failed: int = 0
    errors: int = 0
    coverage: float = 0.0
    output: str = ""
    duration_ms: int = 0
    timestamp: datetime | None = None


class TestOrchestrator:
    """Automated test execution and validation"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.backend_path = self.repo_path / "backend"
        self.results_dir = self.repo_path / "test_results"
        self.results_dir.mkdir(exist_ok=True)

    def run_pytest(self, test_path: str = "tests/", verbose: bool = True) -> TestResult:
        """Run pytest on specified test path"""
        result = TestResult(success=False, timestamp=datetime.utcnow())
        start_time = datetime.utcnow()

        try:
            cmd = [
                "python",
                "-m",
                "pytest",
                test_path,
                "-v" if verbose else "",
                "--tb=short",
                "--no-header",
                "-q",
            ]
            # Remove empty strings
            cmd = [c for c in cmd if c]

            process = subprocess.run(
                cmd,
                cwd=str(self.backend_path),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            result.output = process.stdout + process.stderr
            result.duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Parse output for test counts
            output_lower = result.output.lower()

            # Look for summary line like "X passed, Y failed"
            if "passed" in output_lower:
                # Extract numbers
                import re

                # Try different formats
                passed_match = re.search(r"(\d+) passed", output_lower)
                failed_match = re.search(r"(\d+) failed", output_lower)
                error_match = re.search(r"(\d+) error", output_lower)

                if passed_match:
                    result.passed = int(passed_match.group(1))
                if failed_match:
                    result.failed = int(failed_match.group(1))
                if error_match:
                    result.errors = int(error_match.group(1))

            result.success = result.failed == 0 and result.errors == 0

        except subprocess.TimeoutExpired:
            result.output = "Test execution timed out (5 minute limit)"
            result.errors = 1
        except Exception as e:
            result.output = f"Test execution failed: {str(e)}"
            result.errors = 1

        return result

    def check_coverage(self, target: float = 80.0, fail_under: float = 70.0) -> dict[str, Any]:
        """Check test coverage and return report"""
        result = {
            "coverage": 0.0,
            "files_covered": [],
            "files_missing": [],
            "status": "unknown",
            "message": "",
        }

        try:
            # Run coverage with report
            cmd = ["python", "-m", "pytest", "--cov=.", "--cov-report=term-missing"]

            process = subprocess.run(
                cmd,
                cwd=str(self.backend_path),
                capture_output=True,
                text=True,
                timeout=300,
            )

            output = process.stdout + process.stderr

            # Extract coverage percentage
            import re

            coverage_match = re.search(r"Coverage.*?([\d.]+)%", output, re.IGNORECASE)
            if coverage_match:
                result["coverage"] = float(coverage_match.group(1))

            # Determine status
            if result["coverage"] >= target:
                result["status"] = "excellent"
                result["message"] = f"Coverage {result['coverage']}% exceeds target {target}%"
            elif result["coverage"] >= fail_under:
                result["status"] = "acceptable"
                result["message"] = f"Coverage {result['coverage']}% meets minimum {fail_under}%"
            else:
                result["status"] = "insufficient"
                result["message"] = f"Coverage {result['coverage']}% below minimum {fail_under}%"

        except Exception as e:
            result["message"] = f"Coverage check failed: {str(e)}"

        return result

    def run_linting(self) -> dict[str, Any]:
        """Run linter (ruff) and return results"""
        result = {"passed": True, "errors": [], "warnings": [], "output": ""}

        try:
            # Try ruff first
            cmd = ["python", "-m", "ruff", "check", "."]

            process = subprocess.run(
                cmd,
                cwd=str(self.backend_path),
                capture_output=True,
                text=True,
                timeout=60,
            )

            result["output"] = process.stdout + process.stderr

            if process.returncode != 0:
                result["passed"] = False
                # Parse errors
                lines = result["output"].split("\n")
                for line in lines:
                    if line.strip():
                        if "error" in line.lower():
                            result["errors"].append(line.strip())
                        elif "warning" in line.lower():
                            result["warnings"].append(line.strip())

        except FileNotFoundError:
            # Try flake8
            try:
                cmd = ["python", "-m", "flake8", "."]

                process = subprocess.run(
                    cmd,
                    cwd=str(self.backend_path),
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                result["output"] = process.stdout + process.stderr
                result["passed"] = process.returncode == 0

            except FileNotFoundError:
                result["passed"] = True
                result["output"] = "No linter installed (ruff/flake8 not available)"

        except Exception as e:
            result["passed"] = False
            result["output"] = f"Linting failed: {str(e)}"

        return result

    def run_type_checking(self) -> dict[str, Any]:
        """Run mypy type checking"""
        result = {"passed": True, "errors": [], "output": ""}

        try:
            cmd = ["python", "-m", "mypy", ".", "--ignore-missing-imports"]

            process = subprocess.run(
                cmd,
                cwd=str(self.backend_path),
                capture_output=True,
                text=True,
                timeout=120,
            )

            result["output"] = process.stdout + process.stderr
            result["passed"] = process.returncode == 0

            # Parse errors
            if not result["passed"]:
                lines = result["output"].split("\n")
                for line in lines:
                    if ": error:" in line:
                        result["errors"].append(line.strip())

        except FileNotFoundError:
            result["passed"] = True
            result["output"] = "mypy not installed"
        except Exception as e:
            result["passed"] = False
            result["output"] = f"Type checking failed: {str(e)}"

        return result

    def run_integration_tests(self) -> TestResult:
        """Run integration tests"""
        return self.run_pytest("tests/integration/", verbose=True)

    def run_performance_tests(self) -> dict[str, Any]:
        """Run performance tests using locust or artillery"""
        result = {
            "passed": True,
            "metrics": {},
            "output": "",
            "duration_ms": 0,
            "tool_used": "none"
        }

        start_time = datetime.utcnow()

        try:
            # Try locust first
            if (self.backend_path / "locustfile.py").exists():
                cmd = ["python", "-m", "locust", "--headless", "--run-time", "30s", "--users", "10", "--spawn-rate", "1"]
                result["tool_used"] = "locust"
            elif (self.backend_path / "artillery.yml").exists() or (self.backend_path / "artillery.yaml").exists():
                cmd = ["npx", "artillery", "run", "artillery.yml"]
                result["tool_used"] = "artillery"
            else:
                result["passed"] = False
                result["output"] = "No performance test configuration found (locustfile.py or artillery.yml)"
                return result

            process = subprocess.run(
                cmd,
                cwd=str(self.backend_path),
                capture_output=True,
                text=True,
                timeout=300,
            )

            result["output"] = process.stdout + process.stderr
            result["passed"] = process.returncode == 0

            # Basic metrics extraction (would need tool-specific parsing)
            if result["passed"]:
                result["metrics"] = {"response_time_avg": 0, "requests_per_sec": 0}  # Placeholder

        except Exception as e:
            result["passed"] = False
            result["output"] = f"Performance test failed: {str(e)}"

        result["duration_ms"] = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        return result

    def run_security_tests(self) -> dict[str, Any]:
        """Run security tests including vulnerability scanning"""
        result = {
            "passed": True,
            "vulnerabilities": [],
            "dependency_issues": [],
            "output": "",
            "duration_ms": 0
        }

        start_time = datetime.utcnow()

        try:
            # Run bandit for security issues
            cmd = ["python", "-m", "bandit", "-r", ".", "-f", "json"]

            process = subprocess.run(
                cmd,
                cwd=str(self.backend_path),
                capture_output=True,
                text=True,
                timeout=120,
            )

            result["output"] = process.stdout + process.stderr

            if process.returncode != 0:
                # Parse JSON output for vulnerabilities
                import json
                try:
                    data = json.loads(result["output"])
                    result["vulnerabilities"] = data.get("results", [])
                    result["passed"] = len(result["vulnerabilities"]) == 0
                except json.JSONDecodeError:
                    result["passed"] = False

            # Check dependencies with safety
            try:
                cmd_safety = ["python", "-m", "safety", "check", "--json"]

                process_safety = subprocess.run(
                    cmd_safety,
                    cwd=str(self.backend_path),
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if process_safety.returncode != 0:
                    try:
                        safety_data = json.loads(process_safety.stdout)
                        result["dependency_issues"] = safety_data.get("vulnerabilities", [])
                        if result["passed"]:
                            result["passed"] = len(result["dependency_issues"]) == 0
                    except json.JSONDecodeError:
                        pass

            except FileNotFoundError:
                pass  # Safety not installed

        except FileNotFoundError:
            result["passed"] = False
            result["output"] = "Security tools not installed (bandit required)"
        except Exception as e:
            result["passed"] = False
            result["output"] = f"Security test failed: {str(e)}"

        result["duration_ms"] = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        return result

    def save_test_results(self, results: dict[str, Any], test_type: str) -> str:
        """Save test results to file and return file path"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_type}_{timestamp}.json"
        filepath = self.results_dir / filename

        results["saved_at"] = datetime.utcnow().isoformat()
        results["test_type"] = test_type

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        return str(filepath)

    def get_test_history(self, test_type: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Get historical test results"""
        results = []
        if not self.results_dir.exists():
            return results

        files = sorted(self.results_dir.glob("*.json"), reverse=True)
        for file in files[:limit]:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    if test_type is None or data.get("test_type") == test_type:
                        results.append(data)
            except (OSError, json.JSONDecodeError):
                continue

        return results

    def run_ci_cd_tests(self, event_type: str, branch: str = "main", commit_sha: str | None = None) -> dict[str, Any]:
        """Run tests triggered by CI/CD events"""
        logger.info(f"Running CI/CD tests for event: {event_type}, branch: {branch}")

        results = self.run_full_validation(include_slow=(event_type == "schedule"))

        results["ci_cd"] = {
            "event_type": event_type,
            "branch": branch,
            "commit_sha": commit_sha,
            "triggered_at": datetime.utcnow().isoformat()
        }

        # Save results with CI/CD context
        self.save_test_results(results, f"ci_cd_{event_type}")

        return results

    def schedule_automated_tests(self, schedule_type: str = "daily") -> dict[str, Any]:
        """Schedule automated test runs"""
        # This would typically integrate with a scheduler like APScheduler
        # For now, just run immediately and return scheduling info

        if schedule_type == "daily":
            results = self.run_full_validation(include_slow=True)
        elif schedule_type == "hourly":
            results = self.run_full_validation(include_slow=False)
        else:
            # Quick unit tests
            test_result = self.run_pytest()
            results = {
                "unit_tests": test_result,
                "overall_status": "passed" if test_result.success else "failed",
                "duration_ms": test_result.duration_ms
            }

        results["schedule"] = {
            "type": schedule_type,
            "scheduled_at": datetime.utcnow().isoformat()
        }

        self.save_test_results(results, f"scheduled_{schedule_type}")
        return results

    def get_test_configuration(self) -> dict[str, Any]:
        """Get current test configuration"""
        config = {
            "test_paths": {
                "unit": "tests/",
                "integration": "tests/integration/"
            },
            "performance_tools": ["locust", "artillery"],
            "security_tools": ["bandit", "safety"],
            "coverage_targets": {
                "excellent": 90.0,
                "acceptable": 80.0,
                "minimum": 70.0
            },
            "timeouts": {
                "unit_tests": 300,
                "integration_tests": 600,
                "performance_tests": 300,
                "security_tests": 120
            }
        }

        # Check what tools are available
        tools_status = {}
        for tool in ["pytest", "coverage", "ruff", "mypy", "bandit", "safety", "locust"]:
            try:
                subprocess.run([tool, "--version"], capture_output=True, timeout=5)
                tools_status[tool] = True
            except (FileNotFoundError, subprocess.SubprocessError, OSError):
                tools_status[tool] = False

        config["tools_available"] = tools_status
        return config

    def run_full_validation(self, include_slow: bool = False) -> dict[str, Any]:
        """Run complete validation suite"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "unit_tests": None,
            "integration_tests": None,
            "performance_tests": None,
            "security_tests": None,
            "coverage": None,
            "linting": None,
            "type_checking": None,
            "overall_status": "unknown",
            "duration_ms": 0,
        }

        start_time = datetime.utcnow()

        # Run unit tests
        logger.info("Running unit test suite...")
        results["unit_tests"] = self.run_pytest()

        # Run integration tests
        logger.info("Running integration tests...")
        results["integration_tests"] = self.run_integration_tests()

        # Run performance tests (if include_slow)
        if include_slow:
            logger.info("Running performance tests...")
            results["performance_tests"] = self.run_performance_tests()
        else:
            results["performance_tests"] = {"passed": True, "skipped": True, "output": "Skipped (use include_slow=True)"}

        # Run security tests
        logger.info("Running security tests...")
        results["security_tests"] = self.run_security_tests()

        # Check coverage
        logger.info("Checking coverage...")
        results["coverage"] = self.check_coverage()

        # Run linting
        logger.info("Running linter...")
        results["linting"] = self.run_linting()

        # Run type checking
        logger.info("Running type checker...")
        results["type_checking"] = self.run_type_checking()

        results["duration_ms"] = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Determine overall status
        all_passed = (
            results["unit_tests"].success
            and results["integration_tests"].success
            and results["performance_tests"]["passed"]
            and results["security_tests"]["passed"]
            and results["coverage"]["status"] in ["excellent", "acceptable"]
            and results["linting"]["passed"]
            and results["type_checking"]["passed"]
        )

        results["overall_status"] = "passed" if all_passed else "failed"

        return results

    def generate_test_report(self, task_id: str | None = None, include_slow: bool = False) -> str:
        """Generate a comprehensive markdown test report"""
        results = self.run_full_validation(include_slow)

        # Save results
        self.save_test_results(results, "full_validation")

        report = f"""# Comprehensive Test Report

**Generated:** {results["timestamp"]}
**Duration:** {results["duration_ms"]}ms
**Status:** {"✅ PASSED" if results["overall_status"] == "passed" else "❌ FAILED"}

---

## Unit Test Results

| Metric | Value |
|--------|-------|
| Passed | {results["unit_tests"].passed} |
| Failed | {results["unit_tests"].failed} |
| Errors | {results["unit_tests"].errors} |
| Duration | {results["unit_tests"].duration_ms}ms |

---

## Integration Test Results

| Metric | Value |
|--------|-------|
| Passed | {results["integration_tests"].passed} |
| Failed | {results["integration_tests"].failed} |
| Errors | {results["integration_tests"].errors} |
| Duration | {results["integration_tests"].duration_ms}ms |

---

## Performance Test Results

| Metric | Value |
|--------|-------|
| Status | {"✅ PASSED" if results["performance_tests"]["passed"] else "❌ FAILED"} |
| Tool Used | {results["performance_tests"]["tool_used"]} |
| Duration | {results["performance_tests"]["duration_ms"]}ms |

---

## Security Test Results

| Metric | Value |
|--------|-------|
| Status | {"✅ PASSED" if results["security_tests"]["passed"] else "❌ FAILED"} |
| Vulnerabilities | {len(results["security_tests"]["vulnerabilities"])} |
| Dependency Issues | {len(results["security_tests"]["dependency_issues"])} |
| Duration | {results["security_tests"]["duration_ms"]}ms |

---

## Coverage Report

| Metric | Value |
|--------|-------|
| Coverage | {results["coverage"]["coverage"]}% |
| Status | {results["coverage"]["status"].upper()} |

---

## Linting Results

| Status | Issues |
|--------|--------|
| {"✅ PASSED" if results["linting"]["passed"] else "❌ FAILED"} | {len(results["linting"]["errors"])} errors, {len(results["linting"]["warnings"])} warnings |

---

## Type Checking Results

| Status | Errors |
|--------|--------|
| {"✅ PASSED" if results["type_checking"]["passed"] else "❌ FAILED"} | {len(results["type_checking"]["errors"])} errors |

"""

        if results["security_tests"]["vulnerabilities"]:
            report += "### Security Vulnerabilities\n\n"
            for vuln in results["security_tests"]["vulnerabilities"][:5]:  # Limit to 5
                report += f"- **{vuln.get('test_name', 'Unknown')}**: {vuln.get('issue_text', 'No description')}\n"
            report += "\n"

        if results["security_tests"]["dependency_issues"]:
            report += "### Dependency Issues\n\n"
            for issue in results["security_tests"]["dependency_issues"][:5]:  # Limit to 5
                report += f"- {issue.get('package', 'Unknown')}: {issue.get('vulnerability', 'Unknown vulnerability')}\n"
            report += "\n"

        if results["linting"]["errors"]:
            report += "### Linting Errors\n\n"
            for error in results["linting"]["errors"][:10]:  # Limit to 10
                report += f"- `{error}`\n"
            report += "\n"

        if results["type_checking"]["errors"]:
            report += "### Type Errors\n\n"
            for error in results["type_checking"]["errors"][:10]:  # Limit to 10
                report += f"- `{error}`\n"
            report += "\n"

        report += """---

*Generated by Kor'tana Test Orchestrator*
"""

        return report


# Global orchestrator instance
test_orchestrator = TestOrchestrator()


@router.post("/run")
async def run_tests(test_path: str = "tests/", verbose: bool = True) -> dict[str, Any]:
    """Run tests on specified path"""
    try:
        result = test_orchestrator.run_pytest(test_path, verbose)
        return {
            "success": result.success,
            "passed": result.passed,
            "failed": result.failed,
            "errors": result.errors,
            "duration_ms": result.duration_ms,
            "output": result.output[:2000],  # Limit output size
        }
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coverage")
async def check_coverage(target: float = 80.0, fail_under: float = 70.0) -> dict[str, Any]:
    """Check test coverage"""
    try:
        result = test_orchestrator.check_coverage(target, fail_under)
        return result
    except Exception as e:
        logger.error(f"Coverage check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lint")
async def run_linting() -> dict[str, Any]:
    """Run linter checks"""
    try:
        result = test_orchestrator.run_linting()
        return result
    except Exception as e:
        logger.error(f"Linting failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/type-check")
async def run_type_check() -> dict[str, Any]:
    """Run type checker"""
    try:
        result = test_orchestrator.run_type_checking()
        return result
    except Exception as e:
        logger.error(f"Type checking failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def run_full_validation() -> dict[str, Any]:
    """Run complete validation suite"""
    try:
        result = test_orchestrator.run_full_validation()
        return result
    except Exception as e:
        logger.error(f"Full validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integration-tests")
async def run_integration_tests() -> dict[str, Any]:
    """Run integration tests"""
    try:
        result = test_orchestrator.run_integration_tests()
        return {
            "success": result.success,
            "passed": result.passed,
            "failed": result.failed,
            "errors": result.errors,
            "duration_ms": result.duration_ms,
            "output": result.output[:2000],
        }
    except Exception as e:
        logger.error(f"Integration tests failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance-tests")
async def run_performance_tests() -> dict[str, Any]:
    """Run performance tests"""
    try:
        result = test_orchestrator.run_performance_tests()
        return result
    except Exception as e:
        logger.error(f"Performance tests failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security-tests")
async def run_security_tests() -> dict[str, Any]:
    """Run security tests"""
    try:
        result = test_orchestrator.run_security_tests()
        return result
    except Exception as e:
        logger.error(f"Security tests failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ci-cd")
async def run_ci_cd_tests(event_type: str, branch: str = "main", commit_sha: str | None = None) -> dict[str, Any]:
    """Run CI/CD triggered tests"""
    try:
        result = test_orchestrator.run_ci_cd_tests(event_type, branch, commit_sha)
        return result
    except Exception as e:
        logger.error(f"CI/CD tests failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def schedule_tests(schedule_type: str = "daily") -> dict[str, Any]:
    """Schedule automated tests"""
    try:
        result = test_orchestrator.schedule_automated_tests(schedule_type)
        return result
    except Exception as e:
        logger.error(f"Scheduled tests failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_test_history(test_type: str | None = None, limit: int = 10) -> dict[str, Any]:
    """Get test execution history"""
    try:
        history = test_orchestrator.get_test_history(test_type, limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"Failed to get test history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_test_configuration() -> dict[str, Any]:
    """Get test configuration"""
    try:
        config = test_orchestrator.get_test_configuration()
        return config
    except Exception as e:
        logger.error(f"Failed to get test config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report")
async def generate_test_report(task_id: str | None = None, include_slow: bool = False) -> dict[str, Any]:
    """Generate comprehensive markdown test report"""
    try:
        report = test_orchestrator.generate_test_report(task_id, include_slow)
        return {"report": report}
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def test_health_check() -> dict[str, Any]:
    """Health check for test orchestrator"""
    config = test_orchestrator.get_test_configuration()
    return {
        "status": "healthy",
        "service": "test_orchestrator",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": [
            "unit_tests",
            "integration_tests",
            "performance_tests",
            "security_tests",
            "ci_cd_integration",
            "automated_scheduling",
            "result_storage",
            "comprehensive_reporting"
        ],
        "tools_available": config["tools_available"],
        "test_paths": config["test_paths"],
    }
