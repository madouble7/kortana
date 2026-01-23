"""
Test Orchestrator for Kor'tana Autonomous System

Handles automatic test execution, coverage checking, and validation.
"""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from src.kortana.config import get_settings
from src.kortana.logger import setup_logging

router = APIRouter()
logger = setup_logging()

settings = get_settings()
GEMINI_API_KEY = settings.GEMINI_API_KEY
KORTANA_BACKEND_URL = settings.KORTANA_BACKEND_URL


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
        if not self.repo_path.exists():
            raise TestOrchestrationError(f"Repository path does not exist: {repo_path}")
        self.backend_path = self.repo_path / "backend"
        if not self.backend_path.exists():
            self.backend_path = self.repo_path

    def discover_tests(self, test_dir: str = "tests") -> list[str]:
        """Discover available tests in directory"""
        test_path = self.backend_path / test_dir
        if not test_path.exists():
            return []

        tests = []
        for p in test_path.rglob("test_*.py"):
            tests.append(str(p.relative_to(self.backend_path)))
        return tests

    def run_tests(
        self,
        test_path: str = "tests/",
        verbose: bool = True,
        coverage: bool = False,
        markers: str = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Run pytest on specified test path"""
        cmd = ["python", "-m", "pytest", test_path]
        if verbose:
            cmd.append("-v")
        cmd.extend(["--tb=short", "--no-header", "-q"])
        if coverage:
            cmd.extend(["--cov=.", "--cov-report=json"])
        if markers:
            cmd.extend(["-m", markers])
        cmd = [c for c in cmd if c]

        if dry_run:
            return {
                "success": True,
                "message": "Dry run successful",
                "output": "",
                "dry_run": True,
                "command": " ".join(cmd),
            }

        result = {
            "success": False,
            "timestamp": datetime.utcnow().isoformat(),
            "dry_run": False,
            "command": " ".join(cmd),
        }
        start_time = datetime.utcnow()

        try:
            process = subprocess.run(
                cmd,
                cwd=str(self.backend_path),
                capture_output=True,
                text=True,
                timeout=30,  # Shorter for tests
            )

            stdout = (
                process.stdout
                if isinstance(process.stdout, str)
                else str(process.stdout)
            )
            stderr = (
                process.stderr
                if isinstance(process.stderr, str)
                else str(process.stderr)
            )
            output = stdout + stderr
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            output_lower = output.lower()
            passed = 0
            failed = 0
            errors = 0

            import re

            passed_match = re.search(r"(\d+) passed", output_lower)
            failed_match = re.search(r"(\d+) failed", output_lower)
            error_match = re.search(r"(\d+) error", output_lower)

            if passed_match:
                passed = int(passed_match.group(1))
            if failed_match:
                failed = int(failed_match.group(1))
            if error_match:
                errors = int(error_match.group(1))

            result.update(
                {
                    "success": process.returncode == 0,
                    "return_code": process.returncode,
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "output": output,
                    "duration_ms": duration_ms,
                }
            )

            if process.returncode != 0 and failed == 0 and errors == 0:
                # Likely a collection error or something else
                result["errors"] = 1

        except subprocess.TimeoutExpired:
            raise TestOrchestrationError("Test execution timed out")
        except Exception as e:
            raise TestOrchestrationError(f"Test execution failed: {str(e)}")

        return result

    def run_pytest(self, test_path: str = "tests/", verbose: bool = True) -> TestResult:
        """Legacy wrapper for run_tests returning TestResult object"""
        res_dict = self.run_tests(test_path, verbose)
        return TestResult(
            success=res_dict["success"],
            passed=res_dict.get("passed", 0),
            failed=res_dict.get("failed", 0),
            errors=res_dict.get("errors", 0),
            output=res_dict.get("output", ""),
            duration_ms=res_dict.get("duration_ms", 0),
            timestamp=datetime.fromisoformat(res_dict["timestamp"])
            if "timestamp" in res_dict
            else None,
        )

    def parse_coverage(self) -> dict[str, Any]:
        """Parse coverage report from JSON file"""
        coverage_file = self.repo_path / "coverage.json"

        if not coverage_file.exists():
            return {
                "coverage": 0.0,
                "percent_covered": 0.0,
                "num_statements": 0,
                "success": False,
                "message": "Coverage file not found",
                "error": "File not found",
            }

        import json

        try:
            with open(coverage_file) as f:
                data = json.load(f)
                percent = data["totals"]["percent_covered"]
                statements = data["totals"]["num_statements"]
                files_count = len(data.get("files", {}))
                return {
                    "coverage": percent,
                    "percent_covered": percent,
                    "num_statements": statements,
                    "files": files_count,
                    "success": True,
                }
        except Exception as e:
            return {
                "coverage": 0.0,
                "percent_covered": 0.0,
                "num_statements": 0,
                "files": 0,
                "success": False,
                "message": str(e),
                "error": str(e),
            }

    def check_coverage_threshold(self, threshold: float = 80.0) -> bool:
        """Check if coverage meets threshold"""
        report = self.parse_coverage()
        return report.get("coverage", 0.0) >= threshold

    def check_coverage(
        self, target: float = 80.0, fail_under: float = 70.0
    ) -> dict[str, Any]:
        """Legacy check_coverage method"""
        current = self.parse_coverage().get("coverage", 0.0)
        status = "insufficient"
        if current >= target:
            status = "excellent"
        elif current >= fail_under:
            status = "acceptable"

        return {
            "coverage": current,
            "percent_covered": current,
            "status": status,
            "message": f"Coverage is {current}%",
        }

    def run_specific_tests(
        self, test_names: list[str], dry_run: bool = False
    ) -> dict[str, Any]:
        """Run specific tests by name"""
        if dry_run:
            return {
                "success": True,
                "message": "Dry run successful",
                "dry_run": True,
                "tests": test_names,
            }
        markers = " or ".join(test_names)
        result = self.run_tests(markers=markers)
        result["tests"] = test_names
        return result

    def run_linting(self, dry_run: bool = False) -> dict[str, Any]:
        """Run linter (ruff) and return results"""
        if dry_run:
            return {"success": True, "message": "Dry run successful", "dry_run": True}
        result = {
            "success": True,
            "errors": [],
            "warnings": [],
            "output": "",
            "dry_run": False,
        }
        try:
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
                result["success"] = False
            return result
        except Exception as e:
            return {"success": False, "output": str(e)}

    def run_type_checking(self, dry_run: bool = False) -> dict[str, Any]:
        """Run type checking (mypy)"""
        if dry_run:
            return {"success": True, "message": "Dry run successful", "dry_run": True}
        result = {"success": True, "output": "", "dry_run": False}
        try:
            cmd = ["python", "-m", "mypy", "."]
            process = subprocess.run(
                cmd,
                cwd=str(self.backend_path),
                capture_output=True,
                text=True,
                timeout=120,
            )
            result["output"] = process.stdout + process.stderr
            if process.returncode != 0:
                result["success"] = False
            return result
        except Exception as e:
            return {"success": False, "output": str(e)}

    def run_full_pipeline(self, dry_run: bool = False) -> dict[str, Any]:
        """Run linting, types, and tests"""
        if dry_run:
            return {"success": True, "steps": ["dry_run"]}

        steps = []

        lint = self.run_linting()
        steps.append({"name": "linting", "success": lint["success"]})
        if not lint["success"]:
            return {"success": False, "step": "linting", "result": lint, "steps": steps}

        types = self.run_type_checking()
        steps.append({"name": "type_checking", "success": types["success"]})
        if not types["success"]:
            return {
                "success": False,
                "step": "type_checking",
                "result": types,
                "steps": steps,
            }

        tests = self.run_tests()
        steps.append({"name": "tests", "success": tests["success"]})

        return {
            "success": tests["success"],
            "step": "tests",
            "result": tests,
            "steps": steps,
        }


test_orchestrator = TestOrchestrator()


@router.post("/run")
async def orchestra_run_tests(
    test_path: str = "tests/", verbose: bool = True
) -> dict[str, Any]:
    try:
        result = test_orchestrator.run_pytest(test_path, verbose)
        return {
            "success": result.success,
            "passed": result.passed,
            "failed": result.failed,
            "errors": result.errors,
            "duration_ms": result.duration_ms,
            "output": result.output[:2000],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover")
async def orchestra_discover_tests() -> dict[str, Any]:
    """Alias for discovering tests"""
    try:
        tests = test_orchestrator.discover_tests()
        return {"success": True, "tests": tests, "count": len(tests)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coverage")
@router.post("/coverage")  # Support both for test compatibility
async def orchestra_check_coverage(
    target: float = 80.0, fail_under: float = 70.0
) -> dict[str, Any]:
    try:
        return test_orchestrator.check_coverage(target, fail_under)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lint")
async def orchestra_run_linting() -> dict[str, Any]:
    try:
        return test_orchestrator.run_linting()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/type-check")
async def orchestra_run_type_check() -> dict[str, Any]:
    try:
        return test_orchestrator.run_type_checking()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
@router.post("/pipeline")  # Alias for pipeline
async def orchestra_run_full_validation() -> dict[str, Any]:
    try:
        return test_orchestrator.run_full_pipeline()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def orchestra_health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "test_orchestrator",
        "timestamp": datetime.utcnow().isoformat(),
    }
