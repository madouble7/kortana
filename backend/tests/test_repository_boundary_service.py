from __future__ import annotations

from pathlib import Path

import pytest

from src.kortana.services.repository_boundary_service import RepositoryBoundaryService


def _make_repo_root(path: Path) -> None:
    (path / ".git").mkdir(parents=True, exist_ok=True)
    (path / "backend").mkdir(parents=True, exist_ok=True)
    (path / "frontend").mkdir(parents=True, exist_ok=True)


class TestRepositoryBoundaryService:
    def test_reference_root_resolves_relative_to_canonical_root(
        self, tmp_path: Path
    ) -> None:
        canonical_root = tmp_path / "canonical"
        reference_root = canonical_root / "KOR-TANA" / "kortana"
        _make_repo_root(canonical_root)
        _make_repo_root(reference_root)

        service = RepositoryBoundaryService(
            canonical_root=canonical_root,
            reference_root="KOR-TANA/kortana",
        )

        assert service.canonical_repo_root == canonical_root.resolve()
        assert service.reference_repo_root == reference_root.resolve()

    def test_resolve_canonical_path_rejects_reference_repo_paths(
        self, tmp_path: Path
    ) -> None:
        canonical_root = tmp_path / "canonical"
        reference_root = canonical_root / "KOR-TANA" / "kortana"
        _make_repo_root(canonical_root)
        _make_repo_root(reference_root)

        service = RepositoryBoundaryService(
            canonical_root=canonical_root,
            reference_root=reference_root,
        )

        allowed = service.resolve_canonical_path("backend/example.py")
        assert allowed == (canonical_root / "backend" / "example.py").resolve()

        with pytest.raises(ValueError, match="reference repo"):
            service.resolve_canonical_path(reference_root / "backend" / "example.py")

    def test_read_reference_file_is_bounded_to_reference_root(
        self, tmp_path: Path
    ) -> None:
        canonical_root = tmp_path / "canonical"
        reference_root = canonical_root / "KOR-TANA" / "kortana"
        _make_repo_root(canonical_root)
        _make_repo_root(reference_root)
        sample = reference_root / "backend" / "sample.py"
        sample.write_text("print('reference')\n", encoding="utf-8")

        service = RepositoryBoundaryService(
            canonical_root=canonical_root,
            reference_root=reference_root,
        )

        assert "reference" in service.read_reference_file("backend/sample.py")

        with pytest.raises(ValueError, match="escapes reference repo root"):
            service.read_reference_file("../outside.py")

    def test_search_reference_repo_returns_matches(self, tmp_path: Path) -> None:
        canonical_root = tmp_path / "canonical"
        reference_root = canonical_root / "KOR-TANA" / "kortana"
        _make_repo_root(canonical_root)
        _make_repo_root(reference_root)
        (reference_root / "backend" / "alpha.py").write_text(
            "def build_vector_alpha():\n    return 'alpha'\n",
            encoding="utf-8",
        )
        (reference_root / "frontend" / "beta.tsx").write_text(
            "export const label = 'beta';\n",
            encoding="utf-8",
        )

        service = RepositoryBoundaryService(
            canonical_root=canonical_root,
            reference_root=reference_root,
        )

        results = service.search_reference_repo("vector_alpha")

        assert len(results) == 1
        assert results[0].path == "backend/alpha.py"
        assert results[0].line_number == 1

    def test_reference_status_marks_missing_reference_repo_as_unavailable(
        self, tmp_path: Path
    ) -> None:
        canonical_root = tmp_path / "canonical"
        _make_repo_root(canonical_root)

        service = RepositoryBoundaryService(
            canonical_root=canonical_root,
            reference_root="KOR-TANA/kortana",
        )

        status = service.reference_status()

        assert status["available"] is False
        assert status["reference_repo_root"] is None
