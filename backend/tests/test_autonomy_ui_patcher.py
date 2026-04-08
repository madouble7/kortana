import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.kortana.services.autonomy_ui_patcher import (
    AutonomyUIPatcher,
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


def _make_patcher(tmp_path: Path) -> AutonomyUIPatcher:
    patcher = AutonomyUIPatcher.__new__(AutonomyUIPatcher)
    patcher.db = AsyncMock()
    patcher.diagnostic = MagicMock()
    patcher.diagnostic.analyze_error_string = AsyncMock()
    patcher.boundary = MagicMock()
    patcher.repo_root = tmp_path
    patcher.worktree_dir = tmp_path / ".autonomy_ui_patcher_worktree"
    patcher.boundary.resolve_canonical_path.side_effect = lambda raw_path: (
        _resolve_inside_repo(tmp_path, raw_path)
    )
    return patcher


@pytest.fixture
def repo_target(tmp_path: Path) -> Path:
    target = tmp_path / "frontend" / "src" / "components" / "sample.tsx"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "export function Sample(): JSX.Element {\n  return <div>old</div>;\n}\n",
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
        context={"branch": "auto-repair-ui/demo"},
    )

    task = db.add.call_args.args[0]
    assert task.metadata_json == {"branch": "auto-repair-ui/demo"}
    assert task.result == "{'branch': 'auto-repair-ui/demo'}"
    db.commit.assert_awaited_once()


def test_extract_code_content_handles_fenced_and_raw_text(tmp_path: Path) -> None:
    patcher = _make_patcher(tmp_path)

    fenced = patcher._extract_code_content("```tsx\n<div>ok</div>\n```")
    raw = patcher._extract_code_content("export const raw = true;")

    assert fenced == "<div>ok</div>\n"
    assert raw == "export const raw = true;\n"


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
        "src.kortana.services.autonomy_ui_patcher._call_gemini_analysis",
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
async def test_attempt_auto_fix_runs_in_worktree_and_merges_directly(
    tmp_path: Path, repo_target: Path
) -> None:
    patcher = _make_patcher(tmp_path)
    patcher.diagnostic.analyze_error_string.return_value = SimpleNamespace(
        auto_fixable=True,
        confidence=0.95,
        root_cause="wrong UI literal",
        suggested_fix="render the updated text",
    )

    async def fake_prepare_worktree(branch_name: str) -> bool:
        patcher.worktree_dir.mkdir(parents=True, exist_ok=True)
        return branch_name.startswith("auto-repair-ui/")

    patcher._prepare_worktree = AsyncMock(side_effect=fake_prepare_worktree)
    patcher._run_verification_suite = AsyncMock(
        return_value=[
            VerificationCommandResult(
                label="install",
                argv=("npm", "install"),
                returncode=0,
                output="install ok",
            ),
            VerificationCommandResult(
                label="lint",
                argv=("npm", "run", "lint"),
                returncode=0,
                output="lint ok",
            ),
            VerificationCommandResult(
                label="type-check",
                argv=("npm", "run", "type-check"),
                returncode=0,
                output="type-check ok",
            ),
            VerificationCommandResult(
                label="build",
                argv=("npm", "run", "build"),
                returncode=0,
                output="build ok",
            ),
        ]
    )
    patcher._commit_worktree_change = AsyncMock(return_value="abc123")
    patcher._cleanup_worktree = AsyncMock()

    with (
        patch(
            "src.kortana.services.autonomy_ui_patcher._call_gemini_analysis",
            new=AsyncMock(
                return_value=(
                    "```tsx\n"
                    "export function Sample(): JSX.Element {\n"
                    "  return <div>new</div>;\n"
                    "}\n"
                    "```"
                )
            ),
        ),
        patch.object(
            patcher,
            "_run_process",
            new=AsyncMock(
                return_value=subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="ok", stderr=""
                )
            ),
        ) as mock_run_process,
    ):
        result = await patcher.attempt_auto_fix(
            "AssertionError",
            "expected 'new'",
            repo_target.relative_to(tmp_path).as_posix(),
        )

    worktree_target = patcher.worktree_dir / repo_target.relative_to(tmp_path)

    assert result is True
    assert repo_target.read_text(encoding="utf-8") == (
        "export function Sample(): JSX.Element {\n  return <div>old</div>;\n}\n"
    )
    assert worktree_target.read_text(encoding="utf-8") == (
        "export function Sample(): JSX.Element {\n  return <div>new</div>;\n}\n"
    )
    patcher._commit_worktree_change.assert_awaited_once_with(
        repo_target.relative_to(tmp_path),
        error_type="AssertionError",
        root_cause="wrong UI literal",
    )
    patcher._cleanup_worktree.assert_awaited_once()

    # Validate the HOP override sequence
    calls = mock_run_process.call_args_list
    assert len(calls) == 6
    assert calls[0].args[0] == ("git", "branch", "--show-current")
    assert calls[1].args[0] == ("git", "checkout", "main")
    assert calls[2].args[0] == ("git", "rev-parse", "HEAD")
    assert calls[3].args[0][0:2] == ("git", "merge")
    assert calls[3].args[0][5].startswith("auto-repair-ui/")
    assert calls[4].args[0] == ("git", "push", "origin", "main")
    assert calls[5].args[0][0:2] == ("git", "checkout")


@pytest.mark.asyncio
async def test_attempt_auto_fix_reverts_local_merge_when_push_fails(
    tmp_path: Path, repo_target: Path
) -> None:
    patcher = _make_patcher(tmp_path)
    patcher.diagnostic.analyze_error_string.return_value = SimpleNamespace(
        auto_fixable=True,
        confidence=0.95,
        root_cause="wrong UI literal",
        suggested_fix="render the updated text",
    )

    async def fake_prepare_worktree(branch_name: str) -> bool:
        patcher.worktree_dir.mkdir(parents=True, exist_ok=True)
        return branch_name.startswith("auto-repair-ui/")

    patcher._prepare_worktree = AsyncMock(side_effect=fake_prepare_worktree)
    patcher._run_verification_suite = AsyncMock(
        return_value=[
            VerificationCommandResult(
                label="build",
                argv=("npm", "run", "build"),
                returncode=0,
                output="build ok",
            )
        ]
    )
    patcher._commit_worktree_change = AsyncMock(return_value="abc123")
    patcher._cleanup_worktree = AsyncMock()

    run_process_results = [
        subprocess.CompletedProcess(
            args=["git", "branch", "--show-current"],
            returncode=0,
            stdout="feature/demo\n",
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["git", "checkout", "main"],
            returncode=0,
            stdout="",
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["git", "rev-parse", "HEAD"],
            returncode=0,
            stdout="deadbeef1234567890\n",
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["git", "merge"],
            returncode=0,
            stdout="",
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["git", "push", "origin", "main"],
            returncode=1,
            stdout="",
            stderr="push failed",
        ),
        subprocess.CompletedProcess(
            args=["git", "reset", "--hard", "deadbeef1234567890"],
            returncode=0,
            stdout="",
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["git", "checkout", "feature/demo"],
            returncode=0,
            stdout="",
            stderr="",
        ),
    ]

    with (
        patch(
            "src.kortana.services.autonomy_ui_patcher._call_gemini_analysis",
            new=AsyncMock(
                return_value=(
                    "```tsx\n"
                    "export function Sample(): JSX.Element {\n"
                    "  return <div>new</div>;\n"
                    "}\n"
                    "```"
                )
            ),
        ),
        patch.object(
            patcher,
            "_run_process",
            new=AsyncMock(side_effect=run_process_results),
        ) as mock_run_process,
    ):
        result = await patcher.attempt_auto_fix(
            "AssertionError",
            "expected 'new'",
            repo_target.relative_to(tmp_path).as_posix(),
        )

    assert result is False
    patcher._cleanup_worktree.assert_awaited_once()
    calls = mock_run_process.call_args_list
    assert len(calls) == 7
    assert calls[0].args[0] == ("git", "branch", "--show-current")
    assert calls[1].args[0] == ("git", "checkout", "main")
    assert calls[2].args[0] == ("git", "rev-parse", "HEAD")
    assert calls[3].args[0][0:2] == ("git", "merge")
    assert calls[4].args[0] == ("git", "push", "origin", "main")
    assert calls[5].args[0] == ("git", "reset", "--hard", "deadbeef1234567890")
    assert calls[6].args[0] == ("git", "checkout", "feature/demo")


@pytest.mark.asyncio
async def test_attempt_auto_fix_stops_after_failed_verification(
    tmp_path: Path, repo_target: Path
) -> None:
    patcher = _make_patcher(tmp_path)
    patcher.diagnostic.analyze_error_string.return_value = SimpleNamespace(
        auto_fixable=True,
        confidence=0.90,
        root_cause="bad edit",
        suggested_fix="render a different value",
    )

    async def fake_prepare_worktree(branch_name: str) -> bool:
        patcher.worktree_dir.mkdir(parents=True, exist_ok=True)
        return branch_name.startswith("auto-repair-ui/")

    patcher._prepare_worktree = AsyncMock(side_effect=fake_prepare_worktree)
    patcher._run_verification_suite = AsyncMock(
        return_value=[
            VerificationCommandResult(
                label="lint",
                argv=("npm", "run", "lint"),
                returncode=1,
                output="lint failed",
            )
        ]
    )
    patcher._commit_worktree_change = AsyncMock()
    patcher._cleanup_worktree = AsyncMock()

    with patch(
        "src.kortana.services.autonomy_ui_patcher._call_gemini_analysis",
        new=AsyncMock(
            return_value=(
                "```tsx\n"
                "export function Sample(): JSX.Element {\n"
                "  return <div>candidate</div>;\n"
                "}\n"
                "```"
            )
        ),
    ):
        result = await patcher.attempt_auto_fix(
            "AssertionError",
            "expected 'candidate'",
            repo_target.relative_to(tmp_path).as_posix(),
        )

    assert result is False
    patcher._commit_worktree_change.assert_not_awaited()
    patcher._cleanup_worktree.assert_awaited_once()


@pytest.mark.asyncio
async def test_attempt_auto_fix_returns_false_when_restore_checkout_fails(
    tmp_path: Path, repo_target: Path
) -> None:
    patcher = _make_patcher(tmp_path)
    patcher.diagnostic.analyze_error_string.return_value = SimpleNamespace(
        auto_fixable=True,
        confidence=0.95,
        root_cause="wrong UI literal",
        suggested_fix="render the updated text",
    )

    async def fake_prepare_worktree(branch_name: str) -> bool:
        patcher.worktree_dir.mkdir(parents=True, exist_ok=True)
        return branch_name.startswith("auto-repair-ui/")

    patcher._prepare_worktree = AsyncMock(side_effect=fake_prepare_worktree)
    patcher._run_verification_suite = AsyncMock(
        return_value=[
            VerificationCommandResult(
                label="build",
                argv=("npm", "run", "build"),
                returncode=0,
                output="build ok",
            ),
        ]
    )
    patcher._commit_worktree_change = AsyncMock(return_value="abc123")
    patcher._cleanup_worktree = AsyncMock()

    run_process_results = [
        subprocess.CompletedProcess(
            args=["git", "branch", "--show-current"],
            returncode=0,
            stdout="feature/demo\n",
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["git", "checkout", "main"],
            returncode=0,
            stdout="",
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["git", "rev-parse", "HEAD"],
            returncode=0,
            stdout="deadbeef1234567890\n",
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["git", "merge"],
            returncode=0,
            stdout="",
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["git", "push", "origin", "main"],
            returncode=0,
            stdout="",
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["git", "checkout", "feature/demo"],
            returncode=1,
            stdout="",
            stderr="error: pathspec 'feature/demo' did not match any file(s) known to git",
        ),
    ]

    with (
        patch(
            "src.kortana.services.autonomy_ui_patcher._call_gemini_analysis",
            new=AsyncMock(
                return_value=(
                    "```tsx\n"
                    "export function Sample(): JSX.Element {\n"
                    "  return <div>new</div>;\n"
                    "}\n"
                    "```"
                )
            ),
        ),
        patch.object(
            patcher,
            "_run_process",
            new=AsyncMock(side_effect=run_process_results),
        ) as mock_run_process,
    ):
        result = await patcher.attempt_auto_fix(
            "AssertionError",
            "expected 'new'",
            repo_target.relative_to(tmp_path).as_posix(),
        )

    assert result is False
    patcher._cleanup_worktree.assert_awaited_once()
    calls = mock_run_process.call_args_list
    assert len(calls) == 6
    assert calls[0].args[0] == ("git", "branch", "--show-current")
    assert calls[1].args[0] == ("git", "checkout", "main")
    assert calls[2].args[0] == ("git", "rev-parse", "HEAD")
    assert calls[3].args[0][0:2] == ("git", "merge")
    assert calls[4].args[0] == ("git", "push", "origin", "main")
    assert calls[5].args[0][0:2] == ("git", "checkout")
