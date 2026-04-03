from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.services.autonomy_code_patcher import (
    AutonomyCodePatcher,
    VerificationCommandResult,
    submit_approval_task,
)


def _resolve_inside_repo(repo_root: Path, raw_path: str | Path) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    candidate = candidate.resolve()
    candidate.relative_to(repo_root.resolve())
    return candidate


def _make_patcher(tmp_path: Path) -> AutonomyCodePatcher:
    patcher = AutonomyCodePatcher.__new__(AutonomyCodePatcher)
    patcher.db = AsyncMock()
    patcher.diagnostic = MagicMock()
    patcher.diagnostic.analyze_error_string = AsyncMock()
    patcher.boundary = MagicMock()
    patcher.repo_root = tmp_path
    patcher.worktree_dir = tmp_path / ".autonomy_code_patcher_worktree"
    patcher.boundary.resolve_canonical_path.side_effect = lambda raw_path: (
        _resolve_inside_repo(tmp_path, raw_path)
    )
    return patcher


@pytest.fixture
def repo_target(tmp_path: Path) -> Path:
    target = tmp_path / "backend" / "src" / "kortana" / "services" / "sample.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "def current_value() -> str:\n    return 'old'\n",
        encoding="utf-8",
    )
    return target


@pytest.mark.asyncio
async def test_submit_approval_task_stores_metadata() -> None:
    db = AsyncMock()

    await submit_approval_task(
        db,
        title="approve",
        description="desc",
        context={"branch": "auto-repair/demo"},
    )

    task = db.add.call_args.args[0]
    assert task.metadata_json == {"branch": "auto-repair/demo"}
    assert task.result == "{'branch': 'auto-repair/demo'}"
    db.commit.assert_awaited_once()


def test_extract_python_content_handles_fenced_and_raw_text(tmp_path: Path) -> None:
    patcher = _make_patcher(tmp_path)

    fenced = patcher._extract_python_content("```python\nprint('ok')\n```")
    raw = patcher._extract_python_content("print('raw')")

    assert fenced == "print('ok')\n"
    assert raw == "print('raw')\n"


def test_validate_content_delta_rejects_large_rewrite(tmp_path: Path) -> None:
    patcher = _make_patcher(tmp_path)
    original = "\n".join(f"line_{index}" for index in range(250)) + "\n"
    new = "print('tiny replacement')\n"

    is_valid = patcher._validate_content_delta(
        original,
        new,
        Path("backend/src/kortana/services/sample.py"),
    )

    assert is_valid is False


@pytest.mark.asyncio
async def test_attempt_auto_fix_rejects_low_confidence_even_if_auto_fixable(
    tmp_path: Path, repo_target: Path
) -> None:
    patcher = _make_patcher(tmp_path)
    patcher.diagnostic.analyze_error_string.return_value = SimpleNamespace(
        auto_fixable=True,
        confidence=0.30,
        root_cause="not enough certainty",
        suggested_fix="do nothing",
    )

    with patch(
        "src.kortana.services.autonomy_code_patcher._call_gemini_analysis",
        new=AsyncMock(),
    ) as mock_gemini:
        result = await patcher.attempt_auto_fix(
            "AssertionError",
            "expected 2",
            repo_target.relative_to(tmp_path).as_posix(),
        )

    assert result is False
    mock_gemini.assert_not_awaited()


@pytest.mark.asyncio
async def test_attempt_auto_fix_runs_in_worktree_and_submits_for_approval(
    tmp_path: Path, repo_target: Path
) -> None:
    patcher = _make_patcher(tmp_path)
    patcher.diagnostic.analyze_error_string.return_value = SimpleNamespace(
        auto_fixable=True,
        confidence=0.95,
        root_cause="wrong return literal",
        suggested_fix="return the updated string",
    )

    async def fake_prepare_worktree(branch_name: str) -> bool:
        patcher.worktree_dir.mkdir(parents=True, exist_ok=True)
        return branch_name.startswith("auto-repair/")

    patcher._prepare_worktree = AsyncMock(side_effect=fake_prepare_worktree)
    patcher._run_verification_suite = AsyncMock(
        return_value=[
            VerificationCommandResult(
                label="ruff",
                argv=("python", "-m", "ruff", "check", "src", "tests"),
                returncode=0,
                output="ruff ok",
            ),
            VerificationCommandResult(
                label="mypy",
                argv=("python", "-m", "mypy", "src"),
                returncode=0,
                output="mypy ok",
            ),
            VerificationCommandResult(
                label="pytest",
                argv=("python", "-m", "pytest", "tests", "-q"),
                returncode=0,
                output="pytest ok",
            ),
        ]
    )
    patcher._commit_worktree_change = AsyncMock(return_value="abc123")
    patcher._cleanup_worktree = AsyncMock()

    with (
        patch(
            "src.kortana.services.autonomy_code_patcher._call_gemini_analysis",
            new=AsyncMock(
                return_value=(
                    "```python\n"
                    "def current_value() -> str:\n"
                    "    return 'new'\n"
                    "```"
                )
            ),
        ),
        patch(
            "src.kortana.services.autonomy_code_patcher.submit_approval_task",
            new=AsyncMock(),
        ) as mock_submit,
    ):
        result = await patcher.attempt_auto_fix(
            "AssertionError",
            "expected 'new'",
            repo_target.relative_to(tmp_path).as_posix(),
        )

    worktree_target = patcher.worktree_dir / repo_target.relative_to(tmp_path)

    assert result is True
    assert repo_target.read_text(encoding="utf-8") == (
        "def current_value() -> str:\n    return 'old'\n"
    )
    assert worktree_target.read_text(encoding="utf-8") == (
        "def current_value() -> str:\n    return 'new'\n"
    )
    patcher._commit_worktree_change.assert_awaited_once_with(
        repo_target.relative_to(tmp_path),
        error_type="AssertionError",
        root_cause="wrong return literal",
    )
    patcher._cleanup_worktree.assert_awaited_once()

    approval_context = mock_submit.await_args.kwargs["context"]
    assert approval_context["commit_sha"] == "abc123"
    assert approval_context["target_file"] == repo_target.relative_to(tmp_path).as_posix()
    assert approval_context["verification"][-1]["label"] == "pytest"


@pytest.mark.asyncio
async def test_attempt_auto_fix_stops_after_failed_verification(
    tmp_path: Path, repo_target: Path
) -> None:
    patcher = _make_patcher(tmp_path)
    patcher.diagnostic.analyze_error_string.return_value = SimpleNamespace(
        auto_fixable=True,
        confidence=0.90,
        root_cause="bad edit",
        suggested_fix="return a different value",
    )

    async def fake_prepare_worktree(branch_name: str) -> bool:
        patcher.worktree_dir.mkdir(parents=True, exist_ok=True)
        return branch_name.startswith("auto-repair/")

    patcher._prepare_worktree = AsyncMock(side_effect=fake_prepare_worktree)
    patcher._run_verification_suite = AsyncMock(
        return_value=[
            VerificationCommandResult(
                label="ruff",
                argv=("python", "-m", "ruff", "check", "src", "tests"),
                returncode=1,
                output="lint failed",
            )
        ]
    )
    patcher._commit_worktree_change = AsyncMock()
    patcher._cleanup_worktree = AsyncMock()

    with (
        patch(
            "src.kortana.services.autonomy_code_patcher._call_gemini_analysis",
            new=AsyncMock(
                return_value=(
                    "```python\n"
                    "def current_value() -> str:\n"
                    "    return 'candidate'\n"
                    "```"
                )
            ),
        ),
        patch(
            "src.kortana.services.autonomy_code_patcher.submit_approval_task",
            new=AsyncMock(),
        ) as mock_submit,
    ):
        result = await patcher.attempt_auto_fix(
            "AssertionError",
            "expected 'candidate'",
            repo_target.relative_to(tmp_path).as_posix(),
        )

    assert result is False
    patcher._commit_worktree_change.assert_not_awaited()
    patcher._cleanup_worktree.assert_awaited_once()
    mock_submit.assert_not_awaited()
