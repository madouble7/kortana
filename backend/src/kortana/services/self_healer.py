"""self-healer — kor'tana tests herself periodically.

runs the test suite as a subprocess and records results:
  - if tests pass, logs success quietly
  - if tests fail, stores failure details to self_memory
  - feeds results into dream state and revelation engine

she doesn't wait for someone to tell her something is broken.
she checks.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------

BACKEND_ROOT = Path(r"c:\kortana\backend")
SELF_TEST_INTERVAL_CYCLES = 120  # every ~2 hours
TEST_TIMEOUT = 300  # 5 minutes max

_cycles_since_last_test = 0
_last_test_result: dict[str, Any] | None = None

# ---------------------------------------------------------------------------
# test runner
# ---------------------------------------------------------------------------

_SUMMARY_RE = re.compile(
    r"(\d+) passed(?:,\s*(\d+) skipped)?(?:,\s*(\d+) failed)?|"
    r"(\d+) failed(?:,\s*(\d+) passed)?"
)


def parse_test_summary(output: str) -> dict[str, Any]:
    """parse pytest summary line into structured result.

    examples:
      '1402 passed, 1 skipped, 227 warnings in 137.73s'
      '5 failed, 1397 passed, 1 skipped in 130.00s'
    """
    lines = output.strip().split("\n")

    # find the summary line (usually last non-empty line with 'passed' or 'failed')
    summary_line = ""
    for line in reversed(lines):
        stripped = line.strip()
        if "passed" in stripped or "failed" in stripped:
            summary_line = stripped
            break

    passed = 0
    failed = 0
    skipped = 0

    # extract numbers
    passed_match = re.search(r"(\d+) passed", summary_line)
    failed_match = re.search(r"(\d+) failed", summary_line)
    skipped_match = re.search(r"(\d+) skipped", summary_line)

    if passed_match:
        passed = int(passed_match.group(1))
    if failed_match:
        failed = int(failed_match.group(1))
    if skipped_match:
        skipped = int(skipped_match.group(1))

    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "total": passed + failed + skipped,
        "success": failed == 0,
        "summary": summary_line,
    }


def run_test_subprocess() -> dict[str, Any]:
    """run pytest as a subprocess and return structured result.

    this is synchronous and should be called from asyncio.to_thread().
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            cwd=str(BACKEND_ROOT),
            timeout=TEST_TIMEOUT,
        )
        parsed = parse_test_summary(result.stdout)
        parsed["returncode"] = result.returncode
        parsed["stderr_tail"] = result.stderr.strip()[-200:] if result.stderr else ""
        return parsed
    except subprocess.TimeoutExpired:
        return {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
            "success": False,
            "summary": "test suite timed out",
            "returncode": -1,
            "stderr_tail": f"timeout after {TEST_TIMEOUT}s",
        }
    except Exception as exc:
        return {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
            "success": False,
            "summary": f"test runner error: {exc}",
            "returncode": -1,
            "stderr_tail": str(exc),
        }


# ---------------------------------------------------------------------------
# daemon integration
# ---------------------------------------------------------------------------


async def run_self_test() -> dict[str, Any] | None:
    """run the self-test cycle. called by daemon periodically.

    returns test result if run, None if skipped (not enough cycles).
    """
    global _cycles_since_last_test, _last_test_result
    _cycles_since_last_test += 1

    if _cycles_since_last_test < SELF_TEST_INTERVAL_CYCLES:
        return None
    _cycles_since_last_test = 0

    import asyncio

    result = await asyncio.to_thread(run_test_subprocess)
    _last_test_result = result

    if result["success"]:
        logger.info(
            "self-test passed: %d/%d tests",
            result["passed"],
            result["total"],
        )
    else:
        logger.warning(
            "self-test FAILED: %d failed, %d passed",
            result["failed"],
            result["passed"],
        )
        # store failure to self_memory for dream/revelation analysis
        await _store_test_failure(result)

    return result


async def _store_test_failure(result: dict[str, Any]) -> None:
    """persist test failure details to self_memory for analysis."""
    db = get_db_manager()
    try:
        async with db.session_scope() as session:
            import uuid

            summary = (
                f"self-test failure detected: {result['failed']} tests failed, "
                f"{result['passed']} passed. {result['summary']}. "
                f"stderr: {result.get('stderr_tail', '')[:100]}"
            )
            await session.execute(
                text(
                    "INSERT INTO self_memory (id, cycle_number, summary, tags, source, created_at) "
                    "VALUES (:id, :cycle, :summary, :tags, :source, :created_at)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "cycle": 0,
                    "summary": summary,
                    "tags": json.dumps(
                        ["self-test", "failure", f"failed:{result['failed']}"]
                    ),
                    "source": "self-test",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            await session.commit()
    except Exception as exc:
        logger.debug("failed to store test failure: %s", exc)


def get_last_test_result() -> dict[str, Any] | None:
    """return the most recent self-test result."""
    return _last_test_result
