"""Tests for the workspace bridge service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.services.workspace_bridge_service import WorkspaceBridgeService


class TestWorkspaceBridgeService:
    def test_get_status_reports_canonical_warning_when_falling_back(
        self, tmp_path
    ) -> None:
        service = WorkspaceBridgeService()
        service.repo_root = tmp_path.resolve()
        service.configured_root = (tmp_path / "missing-root").resolve()
        service.root_source = "fallback"

        status = service.get_status()

        assert status["canonical_match"] is False
        assert "using fallback" in status["canonical_warning"]

    def test_get_status_marks_configured_root_as_canonical(self, tmp_path) -> None:
        service = WorkspaceBridgeService()
        service.repo_root = tmp_path.resolve()
        service.configured_root = tmp_path.resolve()
        service.root_source = "configured"

        status = service.get_status()

        assert status["canonical_match"] is True
        assert status["canonical_warning"] is None

    def test_extract_changed_files_handles_renames(self) -> None:
        lines = [
            " M backend/src/kortana/services/autonomy_daemon.py",
            "R  old_name.py -> new_name.py",
            "?? .kortana/operator_inbox.md",
        ]

        changed = WorkspaceBridgeService._extract_changed_files(lines)

        assert changed == [
            "backend/src/kortana/services/autonomy_daemon.py",
            "new_name.py",
            ".kortana/operator_inbox.md",
        ]

    def test_directive_type_from_entry_supports_protocol_fields(self) -> None:
        assert WorkspaceBridgeService._directive_type_from_entry("mode: plan") == "mode"
        assert (
            WorkspaceBridgeService._directive_type_from_entry("approval: manual")
            == "approval"
        )
        assert (
            WorkspaceBridgeService._directive_type_from_entry(
                "handoff: analyzer -> planner -> executor"
            )
            == "handoff"
        )
        assert (
            WorkspaceBridgeService._directive_type_from_entry("override: halt")
            == "override"
        )

    @pytest.mark.asyncio
    async def test_ingest_inbox_creates_directives_from_non_comment_lines(
        self, tmp_path, monkeypatch
    ) -> None:
        service = WorkspaceBridgeService()
        service.repo_root = tmp_path
        service.inbox_path = tmp_path / ".kortana" / "operator_inbox.md"
        service.inbox_path.parent.mkdir(parents=True, exist_ok=True)
        service.inbox_path.write_text(
            "# title\nfocus: tests\navoid: billing\n\nplain note\n",
            encoding="utf-8",
        )

        create_directive_mock = AsyncMock()

        class StubDirectiveService:
            def __init__(self) -> None:
                self.create_directive = create_directive_mock

        monkeypatch.setattr(
            "src.kortana.services.workspace_bridge_service.OperatorDirectiveService",
            StubDirectiveService,
        )

        ingested = await service._ingest_inbox()

        assert ingested == 3
        assert create_directive_mock.await_count == 3

    @pytest.mark.asyncio
    async def test_ingest_inbox_skips_when_digest_unchanged(
        self, tmp_path, monkeypatch
    ) -> None:
        service = WorkspaceBridgeService()
        service.repo_root = tmp_path
        service.inbox_path = tmp_path / ".kortana" / "operator_inbox.md"
        service.inbox_path.parent.mkdir(parents=True, exist_ok=True)
        service.inbox_path.write_text("focus: tests\n", encoding="utf-8")

        create_directive_mock = AsyncMock()

        class StubDirectiveService:
            def __init__(self) -> None:
                self.create_directive = create_directive_mock

        monkeypatch.setattr(
            "src.kortana.services.workspace_bridge_service.OperatorDirectiveService",
            StubDirectiveService,
        )

        first = await service._ingest_inbox()
        second = await service._ingest_inbox()

        assert first == 1
        assert second == 0
        assert create_directive_mock.await_count == 1

    def test_git_output_adds_safe_directory(self, tmp_path) -> None:
        service = WorkspaceBridgeService()
        service.repo_root = tmp_path.resolve()

        with patch(
            "src.kortana.services.workspace_bridge_service.subprocess.run"
        ) as mock_run:
            mock_run.return_value = MagicMock(stdout="main\n")

            output = service._git_output(["git", "branch", "--show-current"])

        assert output == "main"
        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == [
            "git",
            "-c",
            f"safe.directory={service.repo_root}",
            "branch",
            "--show-current",
        ]
