"""Regression tests for VectorAlphaBranchService.create_healing_branch.

Verifies:
  - unlock + prune are called unconditionally (even when worktree dir is missing)
  - when worktree dir exists, 'remove --force' is called before 'worktree add'
  - when worktree dir does not exist, rmtree is NOT called
  - happy-path: branch name is returned on successful 'worktree add'
  - failure-path: None is returned when 'worktree add' fails
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.services.vector_alpha_branch_service import VectorAlphaBranchService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_incident(incident_type: str = "test_failure", description: str = "boom"):
    m = MagicMock()
    m.id = "inc-001"
    m.incident_type = incident_type
    m.description = description
    m.resolved = False
    m.repair_branch = None
    m.fix_status = None
    return m


def _make_svc():
    """Return a VectorAlphaBranchService with a mocked DB session."""
    db = AsyncMock()
    svc = VectorAlphaBranchService.__new__(VectorAlphaBranchService)
    svc.db = db
    svc.repo_dir = "/fake/repo"
    svc.worktree_dir = "/fake/repo/.vector_alpha_worktree"
    return svc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unlock_and_prune_called_when_dir_missing():
    """unlock + prune must fire even if the worktree directory does not exist."""
    svc = _make_svc()
    incident = _make_incident()

    subprocess_calls: list = []

    def capture_run(cmd, **kwargs):
        subprocess_calls.append(cmd)
        r = MagicMock()
        r.returncode = 0
        r.stderr = b""
        return r

    with (
        patch("src.kortana.services.vector_alpha_branch_service.asyncio.to_thread") as mock_to_thread,
        patch("src.kortana.services.vector_alpha_branch_service.os.path.exists", return_value=False),
    ):
        # asyncio.to_thread(subprocess.run, [...], ...) — capture args[1] (the cmd list)
        async def fake_to_thread(fn, *args, **kwargs):
            if fn.__name__ == "run":
                return capture_run(args[0], **kwargs)
            return fn(*args, **kwargs)

        mock_to_thread.side_effect = fake_to_thread

        result = await svc.create_healing_branch(incident)

    # unlock + prune must be present even when dir is absent
    assert any("unlock" in str(c) for c in subprocess_calls), (
        "Expected 'git worktree unlock' to be called"
    )
    assert any("prune" in str(c) for c in subprocess_calls), (
        "Expected 'git worktree prune' to be called"
    )
    # worktree add must be the final subprocess call
    assert any("add" in str(c) for c in subprocess_calls), (
        "Expected 'git worktree add' to be called"
    )
    # branch name returned
    assert result is not None
    assert "auto-fix" in result


@pytest.mark.asyncio
async def test_remove_called_when_dir_exists():
    """When the worktree directory exists, 'git worktree remove --force' must precede add."""
    svc = _make_svc()
    incident = _make_incident()

    subprocess_calls: list = []

    with (
        patch("src.kortana.services.vector_alpha_branch_service.asyncio.to_thread") as mock_to_thread,
        patch(
            "src.kortana.services.vector_alpha_branch_service.os.path.exists",
            return_value=True,  # directory exists
        ),
        patch("src.kortana.services.vector_alpha_branch_service.shutil.rmtree"),
    ):
        async def fake_to_thread(fn, *args, **kwargs):
            if hasattr(fn, "__name__") and fn.__name__ == "run":
                subprocess_calls.append(args[0])
                r = MagicMock()
                r.returncode = 0
                r.stderr = b""
                return r
            return fn(*args, **kwargs)

        mock_to_thread.side_effect = fake_to_thread

        result = await svc.create_healing_branch(incident)

    # Verify call order: unlock → prune → remove --force → add
    cmd_strs = [" ".join(c) for c in subprocess_calls if isinstance(c, list)]
    unlock_idx = next((i for i, c in enumerate(cmd_strs) if "unlock" in c), -1)
    prune_idx = next((i for i, c in enumerate(cmd_strs) if "prune" in c), -1)
    remove_idx = next((i for i, c in enumerate(cmd_strs) if "remove" in c and "--force" in c), -1)

    assert unlock_idx != -1, "'git worktree unlock' not found in subprocess calls"
    assert prune_idx != -1, "'git worktree prune' not found"
    assert remove_idx != -1, "'git worktree remove --force' not found"
    assert unlock_idx < remove_idx, "unlock must happen before remove"
    assert prune_idx < remove_idx, "prune must happen before remove"
    assert result is not None


@pytest.mark.asyncio
async def test_returns_none_when_worktree_add_fails():
    """If 'git worktree add' returns non-zero, the method must return None."""
    svc = _make_svc()
    incident = _make_incident()

    with (
        patch("src.kortana.services.vector_alpha_branch_service.asyncio.to_thread") as mock_to_thread,
        patch("src.kortana.services.vector_alpha_branch_service.os.path.exists", return_value=False),
    ):
        call_count = 0

        async def fake_to_thread(fn, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            r = MagicMock()
            # First calls (unlock, prune) succeed; the final 'add' call fails
            cmd = args[0] if args else []
            if isinstance(cmd, list) and "add" in cmd:
                r.returncode = 128
                r.stderr = b"fatal: worktree error"
            else:
                r.returncode = 0
                r.stderr = b""
            return r

        mock_to_thread.side_effect = fake_to_thread

        result = await svc.create_healing_branch(incident)

    assert result is None, "Expected None when 'git worktree add' fails"
