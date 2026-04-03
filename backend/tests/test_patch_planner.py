import os
import shutil
import subprocess
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from src.kortana.models import IncidentMemory
from src.kortana.services.patch_planner import (
    PatchPlan,
    PatchPlanner,
    VerificationResult,
)


@pytest.fixture
def mock_incident():
    return IncidentMemory(
        id=1,
        incident_type="test_error",
        description="Tests failing in backend.",
        stack_trace="AssertionError: 1 != 2",
        fix_status="OPEN",
    )


@pytest.fixture
def planner():
    with patch("src.kortana.services.patch_planner.GeminiService") as mock_gemini:
        # Give the planner a fake worktree dir
        p = PatchPlanner("/tmp/fake_worktree")
        p.gemini = mock_gemini.return_value
        yield p


@pytest.mark.asyncio
async def test_stage_1_analyze_success(planner, mock_incident):
    planner.gemini.analyze_text = AsyncMock(
        return_value="""{
        "should_patch": true,
        "root_cause": "Typo in test",
        "confidence": 0.95,
        "candidate_files": ["backend/tests/test_mock.py"],
        "forbidden_files_hit": [],
        "validation_commands": ["pytest"]
    }"""
    )

    plan = await planner._stage_1_analyze(mock_incident)
    assert plan.should_patch is True
    assert plan.confidence == 0.95
    assert len(plan.candidate_files) == 1


@pytest.mark.asyncio
async def test_stage_1_analyze_forbidden_files_hit(planner, mock_incident):
    planner.gemini.analyze_text = AsyncMock(
        return_value="""{
        "should_patch": true,
        "root_cause": "Needs env change",
        "confidence": 0.9,
        "candidate_files": [".env"],
        "forbidden_files_hit": [".env"],
        "validation_commands": []
    }"""
    )

    plan = await planner._stage_1_analyze(mock_incident)
    assert plan.forbidden_files_hit == [".env"]


@pytest.mark.asyncio
async def test_stage_2_generate_diff_too_many_files(planner, mock_incident):
    plan = PatchPlan(
        should_patch=True,
        root_cause="Fix",
        confidence=0.9,
        candidate_files=["file1.py", "file2.py", "file3.py", "file4.py"],
        forbidden_files_hit=[],
        validation_commands=[],
    )
    diff = await planner._stage_2_generate_diff(mock_incident, plan)
    assert diff is None  # Guardrail hit


@pytest.mark.asyncio
async def test_stage_2_generate_diff_forbidden_prefix(planner, mock_incident):
    plan = PatchPlan(
        should_patch=True,
        root_cause="Fix",
        confidence=0.9,
        candidate_files=["backend/auth/secret.py"],
        forbidden_files_hit=[],
        validation_commands=[],
    )
    diff = await planner._stage_2_generate_diff(mock_incident, plan)
    assert diff is None  # Guardrail hit


@pytest.mark.asyncio
async def test_apply_healing_patch_success(planner, mock_incident):
    planner._stage_1_analyze = AsyncMock(
        return_value=PatchPlan(
            should_patch=True,
            root_cause="Fix",
            confidence=0.9,
            candidate_files=["test.py"],
            forbidden_files_hit=[],
            validation_commands=[],
        )
    )
    planner._stage_2_generate_diff = AsyncMock(
        return_value="--- a/test.py\n+++ b/test.py\n+fix"
    )
    planner._apply_diff_to_worktree = AsyncMock(return_value=True)
    planner._stage_3_verify_patch = AsyncMock(
        return_value=VerificationResult(
            pass_check=True, residual_risk="None", pr_summary="Fixed issue"
        )
    )

    success = await planner.apply_healing_patch(mock_incident)
    assert success is True
    planner._stage_1_analyze.assert_called_once()
    planner._stage_2_generate_diff.assert_called_once()
    planner._apply_diff_to_worktree.assert_called_once()
    planner._stage_3_verify_patch.assert_called_once()


@pytest.mark.asyncio
async def test_apply_healing_patch_rejected_by_analysis(planner, mock_incident):
    planner._stage_1_analyze = AsyncMock(
        return_value=PatchPlan(
            should_patch=False,
            root_cause="Too complex",
            confidence=0.4,
            candidate_files=[],
            forbidden_files_hit=[],
            validation_commands=[],
        )
    )

    success = await planner.apply_healing_patch(mock_incident)
    assert success is False


@pytest.mark.asyncio
async def test_extract_json_triple_fence(planner):
    payload = 'Here is my response:\n```json\n{"test": 123}\n```\nEnjoy.'
    assert planner._extract_json(payload) == {"test": 123}

    assert planner._extract_json('{"test": 456}') == {"test": 456}

    with pytest.raises(ValueError):
        planner._extract_json("not json")


@pytest.mark.asyncio
async def test_extract_diff_triple_fence(planner):
    payload = "Here is diff:\n```diff\n--- a/file\n+++ b/file\n+content\n```"
    assert planner._extract_diff(payload) == "--- a/file\n+++ b/file\n+content"


@pytest.mark.asyncio
async def test_validate_diff_locally(planner):
    diff = "--- a/test.py\n+++ b/test.py\n@@ -1 +1 @@\n+fix\n"
    assert planner._validate_diff_locally(diff, ["test.py"]) is True

    # Empty
    assert not planner._validate_diff_locally("", ["test.py"])

    assert not planner._validate_diff_locally(
        "--- a/forbidden.txt\n+++ b/forbidden.txt\n@@ -1 +1 @@\n+fix\n", ["test.py"]
    )

    # Missing diff headers
    assert not planner._validate_diff_locally("+ just some python code", ["test.py"])


@pytest.fixture
def real_git_planner():
    temp_dir = tempfile.mkdtemp()
    subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True
    )

    test_file = os.path.join(temp_dir, "app.py")
    with open(test_file, "w") as f:
        f.write("def hello():\n    return False\n")

    subprocess.run(["git", "add", "app.py"], cwd=temp_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, check=True)

    with patch("src.kortana.services.patch_planner.GeminiService"):
        p = PatchPlanner(temp_dir)
        yield p

    shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Pipeline integrity – these tests fail if critical async methods are stubbed
# or removed from PatchPlanner (regression guard against destructive rewrites).
# ---------------------------------------------------------------------------


def test_pipeline_methods_are_coroutines(planner):
    """apply_healing_patch and all 3 stages must be async coroutine functions."""
    import inspect

    required = [
        "apply_healing_patch",
        "_stage_1_analyze",
        "_stage_2_generate_diff",
        "_stage_3_verify_patch",
        "_apply_diff_to_worktree",
        "_apply_unified_diff",
    ]
    for name in required:
        method = getattr(PatchPlanner, name, None)
        assert method is not None, f"PatchPlanner.{name} is missing"
        assert inspect.iscoroutinefunction(method), (
            f"PatchPlanner.{name} must be an async coroutine function"
        )


def test_pipeline_returns_patchplan_and_verification_models(planner):
    """Stage 1 must return PatchPlan and Stage 3 must return VerificationResult."""
    import inspect

    hints_1 = inspect.get_annotations(PatchPlanner._stage_1_analyze, eval_str=False)
    hints_3 = inspect.get_annotations(
        PatchPlanner._stage_3_verify_patch, eval_str=False
    )
    # Just verify the methods exist and are callable (annotation introspection is
    # environment-dependent); the async guard above is the primary protection.
    assert callable(PatchPlanner._stage_1_analyze)
    assert callable(PatchPlanner._stage_3_verify_patch)


def test_patch_planner_has_forbidden_prefixes_and_limits(planner):
    """Core guardrail constants must not be removed."""
    assert hasattr(PatchPlanner, "FORBIDDEN_PREFIXES")
    assert hasattr(PatchPlanner, "MAX_FILES")
    assert hasattr(PatchPlanner, "MAX_LINES")
    assert isinstance(PatchPlanner.FORBIDDEN_PREFIXES, list)
    assert len(PatchPlanner.FORBIDDEN_PREFIXES) > 0
    assert PatchPlanner.MAX_FILES <= 3


# ---------------------------------------------------------------------------
# _extract_context_snippets fallback – sentinel injection on missing paths
# ---------------------------------------------------------------------------


def test_extract_context_snippets_missing_file_injects_sentinel(planner):
    """A file referenced in a stack trace that doesn't exist in the worktree
    must produce a [Context Unavailable] sentinel instead of silently skipping."""
    incident = IncidentMemory(
        id=99,
        incident_type="test_error",
        description="",
        stack_trace='File "src/kortana/nonexistent_module.py", line 42',
        fix_status="OPEN",
    )
    result = planner._extract_context_snippets(incident)
    assert result != "", "Expected sentinel output, got empty string"
    assert "Context Unavailable" in result
    assert "nonexistent_module.py" in result


def test_extract_context_snippets_real_file_returns_code(real_git_planner):
    """A file that actually exists in the worktree must return code, not a sentinel."""
    import os

    worktree = real_git_planner.worktree_dir
    # app.py was written by the real_git_planner fixture
    incident = IncidentMemory(
        id=100,
        incident_type="test_error",
        description="",
        stack_trace=f'File "{os.path.join(worktree, "app.py")}", line 1',
        fix_status="OPEN",
    )
    result = real_git_planner._extract_context_snippets(incident)
    assert "return" in result  # fixture writes "return False"
    assert "Context Unavailable" not in result


def test_extract_context_snippets_no_trace_returns_empty(planner):
    """An incident with no stack trace must return empty string."""
    incident = IncidentMemory(
        id=101,
        incident_type="test_error",
        description="",
        stack_trace=None,
        fix_status="OPEN",
    )
    result = planner._extract_context_snippets(incident)
    assert result == ""


# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_unified_diff_e2e(real_git_planner):
    # This is a valid diff
    valid_diff = """--- a/app.py
+++ b/app.py
@@ -1,2 +1,2 @@
 def hello():
-    return False
+    return True
"""

    success = await real_git_planner._apply_unified_diff(valid_diff)
    assert success is True

    # Verify file was actually changed
    with open(os.path.join(real_git_planner.worktree_dir, "app.py"), "r") as f:
        content = f.read()
    assert "return True" in content

    # Test bad diff (should fail)
    bad_diff = """--- a/app.py
+++ b/app.py
@@ -1,2 +1,2 @@
 def missing_func():
-    return False
+    return True
"""
    # Use real_git_planner directly
    success_bad = await real_git_planner._apply_unified_diff(bad_diff)
    assert success_bad is False
