"""Tests for PatchValidator middleware guardrail."""

import os
import shutil
import tempfile

import pytest
from src.kortana.services.patch_validator import (
    PatchValidator,
    ValidationFailure,
    ValidationOK,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_worktree():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def validator(tmp_worktree):
    return PatchValidator(tmp_worktree)


def write_file(worktree: str, rel_path: str, content: str) -> None:
    abs_path = os.path.join(worktree, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as fh:
        fh.write(content)


def make_diff(path: str, orig_lines: int, keep_lines: int) -> str:
    """Build a minimal unified diff that deletes (orig_lines - keep_lines) lines."""
    removed = orig_lines - keep_lines
    hunk = [f"--- a/{path}", f"+++ b/{path}", f"@@ -1,{orig_lines} +1,{keep_lines} @@"]
    for i in range(keep_lines):
        hunk.append(f" line {i + 1}")
    for i in range(removed):
        hunk.append(f"-deleted {i + 1}")
    return "\n".join(hunk) + "\n"


# ---------------------------------------------------------------------------
# LDR tests
# ---------------------------------------------------------------------------


def test_ok_when_below_ldr_threshold(validator, tmp_worktree):
    # 100-line file, delete 10 lines → LDR = 0.10 (well below 0.40)
    content = "".join(f"line {i}\n" for i in range(100))
    write_file(tmp_worktree, "app.py", content)
    diff = make_diff("app.py", 100, 90)
    result = validator.validate(diff)
    assert isinstance(result, ValidationOK)
    assert result.ldr == pytest.approx(0.10, abs=0.01)


def test_failure_when_ldr_exceeds_threshold(validator, tmp_worktree):
    # 100-line file, delete 80 lines → LDR = 0.80 (far above 0.40)
    content = "".join(f"line {i}\n" for i in range(100))
    write_file(tmp_worktree, "app.py", content)
    diff = make_diff("app.py", 100, 20)
    result = validator.validate(diff)
    assert isinstance(result, ValidationFailure)
    assert any("LDR" in r for r in result.reasons)


def test_ldr_file_not_in_worktree_treated_as_total_deletion(validator, tmp_worktree):
    # File referenced in diff doesn't exist → ratio = 1.0 → exceed threshold
    diff = make_diff("ghost.py", 50, 5)
    result = validator.validate(diff)
    assert isinstance(result, ValidationFailure)


# ---------------------------------------------------------------------------
# Net-shrink tests
# ---------------------------------------------------------------------------


def test_failure_when_net_shrink_exceeds_threshold(validator, tmp_worktree):
    # Create two large files; delete enough to exceed MAX_NET_SHRINK (120)
    n = 300
    content = "".join(f"line {i}\n" for i in range(n))
    write_file(tmp_worktree, "a.py", content)
    write_file(tmp_worktree, "b.py", content)

    # Each diff removes 70 lines, no additions → net shrink = 140 > 120
    diff_a = make_diff("a.py", n, n - 70)
    diff_b = make_diff("b.py", n, n - 70)
    combined = diff_a + "\n" + diff_b

    result = validator.validate(combined, max_ldr=0.99)  # disable LDR check
    assert isinstance(result, ValidationFailure)
    assert any("shrink" in r.lower() for r in result.reasons)


def test_ok_net_shrink_within_threshold(validator, tmp_worktree):
    n = 200
    content = "".join(f"line {i}\n" for i in range(n))
    write_file(tmp_worktree, "c.py", content)

    diff = make_diff("c.py", n, n - 30)  # net shrink = 30, well below 120
    result = validator.validate(diff, max_ldr=0.99)
    assert isinstance(result, ValidationOK)
    assert result.net_shrink == 30


# ---------------------------------------------------------------------------
# Context-availability tests
# ---------------------------------------------------------------------------


def test_failure_when_context_mostly_unavailable(validator):
    snippets = (
        "# src/a.py\n// [Context Unavailable: worktree path could not be resolved.]\n\n"
        "# src/b.py\n// [Context Unavailable: OSError reading worktree path.]\n\n"
        "# src/c.py\n```python\ndef ok(): pass\n```\n"
    )
    # 2/3 unavailable = 0.67 > MAX_UNAVAILABLE_CONTEXT_FRACTION (0.50)
    # Use a clean diff that passes LDR/shrink to isolate context check
    diff = "--- a/stub.py\n+++ b/stub.py\n@@ -1 +1 @@\n+pass\n"
    result = validator.validate(diff=diff, context_snippets=snippets)
    assert isinstance(result, ValidationFailure)
    assert result.unavailable_fraction > 0.50


def test_ok_when_context_availability_sufficient(validator):
    snippets = (
        "# src/a.py\n```python\ndef foo(): pass\n```\n\n"
        "# src/b.py\n```python\ndef bar(): pass\n```\n\n"
        "# src/c.py\n// [Context Unavailable: worktree path could not be resolved.]\n"
    )
    # 1/3 = 0.33 < 0.50 threshold → should pass context check
    diff = "--- a/stub.py\n+++ b/stub.py\n@@ -1 +1 @@\n+pass\n"
    result = validator.validate(diff=diff, context_snippets=snippets)
    assert result.unavailable_fraction == pytest.approx(1 / 3, abs=0.01)


def test_empty_context_does_not_trigger_context_check(validator):
    diff = "--- a/stub.py\n+++ b/stub.py\n@@ -1 +1 @@\n+pass\n"
    result = validator.validate(diff=diff, context_snippets="")
    assert result.unavailable_fraction == 0.0


# ---------------------------------------------------------------------------
# Integration: the old destructive 3e3394f5-style patch would be caught
# ---------------------------------------------------------------------------


def test_destructive_rewrite_caught(validator, tmp_worktree):
    """Simulate a 705-deletion patch on a ~750-line file (the regression scenario)."""
    original_lines = 750
    content = "".join(f"line {i}\n" for i in range(original_lines))
    write_file(tmp_worktree, "patch_planner.py", content)

    # 750 lines → 45 kept → LDR = 705/750 ≈ 0.94
    diff = make_diff("patch_planner.py", original_lines, 45)
    result = validator.validate(diff)
    assert isinstance(result, ValidationFailure)
    assert result.ldr > 0.90
    assert any("LDR" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# validate method signature
# ---------------------------------------------------------------------------


def test_validate_accepts_keyword_overrides(validator, tmp_worktree):
    """Custom thresholds must be respected."""
    n = 20
    content = "".join(f"line {i}\n" for i in range(n))
    write_file(tmp_worktree, "small.py", content)

    diff = make_diff("small.py", n, 10)  # LDR = 0.50, net_shrink = 10
    # With default MAX_LDR=0.40 → failure; with max_ldr=0.99 → passes
    assert isinstance(validator.validate(diff), ValidationFailure)
    assert isinstance(
        validator.validate(diff, max_ldr=0.99, max_net_shrink=999), ValidationOK
    )
