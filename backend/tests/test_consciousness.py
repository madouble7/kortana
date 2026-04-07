"""Tests for Phase 8 — Consciousness Persistence & Self-Repair

Covers:
  - Memory Engine (store, search, stats, backfill)
  - Self-Diagnostic (analyze failure, history, patterns)
  - Experience Distiller (distil, capsules, cost tracking)
  - Consciousness Router endpoints
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.kortana.provider_model_defaults import MEMORY_ENGINE_EMBEDDING_MODEL


# ---------------------------------------------------------------
# Unit tests — cosine similarity
# ---------------------------------------------------------------
class TestCosineSimilarity:
    def test_identical_vectors(self):
        from src.kortana.services.memory_engine import _cosine_similarity

        v = [1.0, 0.0, 0.0]
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        from src.kortana.services.memory_engine import _cosine_similarity

        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert _cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        from src.kortana.services.memory_engine import _cosine_similarity

        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert _cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_empty_vectors(self):
        from src.kortana.services.memory_engine import _cosine_similarity

        assert _cosine_similarity([], []) == 0.0

    def test_mismatched_lengths(self):
        from src.kortana.services.memory_engine import _cosine_similarity

        assert _cosine_similarity([1.0], [1.0, 2.0]) == 0.0

    def test_zero_vector(self):
        from src.kortana.services.memory_engine import _cosine_similarity

        assert _cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


# ---------------------------------------------------------------
# Unit tests — DiagnosticResult
# ---------------------------------------------------------------
class TestDiagnosticResult:
    def test_to_dict(self):
        from src.kortana.services.self_diagnostic import DiagnosticResult

        dr = DiagnosticResult(
            error_type="ValueError",
            error_message="bad input",
            root_cause="invalid argument",
            suggested_fix="validate input first",
            confidence=0.9,
            auto_fixable=True,
        )
        d = dr.to_dict()
        assert d["error_type"] == "ValueError"
        assert d["root_cause"] == "invalid argument"
        assert d["confidence"] == 0.9
        assert d["auto_fixable"] is True
        assert "id" in d
        assert "timestamp" in d

    def test_defaults(self):
        from src.kortana.services.self_diagnostic import DiagnosticResult

        dr = DiagnosticResult(error_type="E", error_message="msg")
        assert dr.root_cause == ""
        assert dr.confidence == 0.0
        assert dr.auto_fixable is False
        assert dr.context == {}


# ---------------------------------------------------------------
# Unit tests — ExperienceCapsule
# ---------------------------------------------------------------
class TestExperienceCapsule:
    def test_to_dict(self):
        from src.kortana.services.experience_distiller import ExperienceCapsule

        c = ExperienceCapsule(
            insight="Always retry on network timeout",
            category="diagnostics",
            source_count=12,
            confidence=0.85,
        )
        d = c.to_dict()
        assert d["insight"] == "Always retry on network timeout"
        assert d["category"] == "diagnostics"
        assert d["source_count"] == 12
        assert "id" in d
        assert "created_at" in d


# ---------------------------------------------------------------
# Unit tests — MemoryEngine (with mocked DB + embedding)
# ---------------------------------------------------------------
class TestMemoryEngine:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_store_with_embedding(self, mock_db):
        from src.kortana.services.memory_engine import MemoryEngine

        fake_embedding = [0.1] * 768
        with patch(
            "src.kortana.services.memory_engine.generate_embedding",
            return_value=fake_embedding,
        ):
            engine = MemoryEngine(mock_db)
            await engine.store("test content")
            mock_db.add.assert_called_once()
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_store_without_embedding(self, mock_db):
        from src.kortana.services.memory_engine import MemoryEngine

        with patch(
            "src.kortana.services.memory_engine.generate_embedding",
            return_value=None,
        ):
            engine = MemoryEngine(mock_db)
            await engine.store("test content")
            mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_stats_empty(self, mock_db):
        from src.kortana.services.memory_engine import MemoryEngine

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        engine = MemoryEngine(mock_db)
        stats = await engine.stats()
        assert stats["total_memories"] == 0
        assert stats["embedded"] == 0
        assert stats["embedding_model"] == MEMORY_ENGINE_EMBEDDING_MODEL

    @pytest.mark.asyncio
    async def test_recall_no_results(self, mock_db):
        from src.kortana.services.memory_engine import MemoryEngine

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        with patch(
            "src.kortana.services.memory_engine.generate_embedding",
            return_value=[0.1] * 768,
        ):
            engine = MemoryEngine(mock_db)
            result = await engine.recall("test query")
            assert result is None


# ---------------------------------------------------------------
# Unit tests — SelfDiagnostic (with mocked Gemini)
# ---------------------------------------------------------------
class TestSelfDiagnostic:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.execute = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_analyze_failure_with_gemini(self, mock_db):
        from src.kortana.services.self_diagnostic import SelfDiagnostic

        gemini_response = (
            "ROOT_CAUSE: Missing database connection\n"
            "SUGGESTED_FIX: Check DATABASE_URL env var\n"
            "CONFIDENCE: 0.85\n"
            "AUTO_FIXABLE: false\n"
        )
        with patch(
            "src.kortana.services.self_diagnostic._call_gemini_analysis",
            return_value=gemini_response,
        ):
            diag = SelfDiagnostic(mock_db)
            result = await diag.analyze_failure(
                ValueError("connection refused"),
                task_context={"task": "db_init"},
            )
            assert result.root_cause == "Missing database connection"
            assert result.suggested_fix == "Check DATABASE_URL env var"
            assert result.confidence == pytest.approx(0.85)
            assert result.auto_fixable is False

    @pytest.mark.asyncio
    async def test_analyze_failure_without_gemini(self, mock_db):
        from src.kortana.services.self_diagnostic import SelfDiagnostic

        with patch(
            "src.kortana.services.self_diagnostic._call_gemini_analysis",
            return_value=None,
        ):
            diag = SelfDiagnostic(mock_db)
            result = await diag.analyze_failure(RuntimeError("boom"))
            assert "RuntimeError" in result.root_cause
            assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_cache_hit(self, mock_db):
        from src.kortana.services.self_diagnostic import SelfDiagnostic

        with patch(
            "src.kortana.services.self_diagnostic._call_gemini_analysis",
            return_value="ROOT_CAUSE: cached\nSUGGESTED_FIX: fix\nCONFIDENCE: 0.9\nAUTO_FIXABLE: true\n",
        ):
            diag = SelfDiagnostic(mock_db)
            r1 = await diag.analyze_failure(ValueError("same error"))
            r2 = await diag.analyze_failure(ValueError("same error"))
            # Second call should hit cache (same root cause)
            assert r1.root_cause == r2.root_cause

    @pytest.mark.asyncio
    async def test_get_history(self, mock_db):
        from src.kortana.services.self_diagnostic import SelfDiagnostic

        with patch(
            "src.kortana.services.self_diagnostic._call_gemini_analysis",
            return_value=None,
        ):
            diag = SelfDiagnostic(mock_db)
            await diag.analyze_failure(ValueError("err1"))
            await diag.analyze_failure(TypeError("err2"))
            history = diag.get_history()
            assert len(history) == 2

    @pytest.mark.asyncio
    async def test_analyze_error_string(self, mock_db):
        from src.kortana.services.self_diagnostic import SelfDiagnostic

        with patch(
            "src.kortana.services.self_diagnostic._call_gemini_analysis",
            return_value="ROOT_CAUSE: test\nSUGGESTED_FIX: fix it\nCONFIDENCE: 0.7\nAUTO_FIXABLE: false\n",
        ):
            diag = SelfDiagnostic(mock_db)
            result = await diag.analyze_error_string(
                error_type="ImportError",
                error_message="No module named 'foo'",
            )
            assert result.error_type == "ImportError"
            assert result.root_cause == "test"

    def test_analysis_model_info_exposes_resolved_lane(self):
        from src.kortana.services.self_diagnostic import get_analysis_model_info

        with patch(
            "src.kortana.services.self_diagnostic.get_preferred_model_name",
            return_value="gemini-3.1-flash-lite-preview",
        ):
            info = get_analysis_model_info()

        assert info["preferred_model"] == "gemini-2.5-flash"
        assert info["model"] == "gemini-3.1-flash-lite-preview"
        assert "model_lane" in info


# ---------------------------------------------------------------
# Unit tests — ExperienceDistiller (with mocked Gemini)
# ---------------------------------------------------------------
class TestExperienceDistiller:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_distil_no_old_memories(self, mock_db):
        from src.kortana.services.experience_distiller import ExperienceDistiller

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        distiller = ExperienceDistiller(mock_db)
        capsules = await distiller.distil()
        assert capsules == []

    def test_cost_stats(self):
        from src.kortana.services.experience_distiller import ExperienceDistiller

        distiller = ExperienceDistiller(AsyncMock())
        stats = distiller.get_cost_stats()
        assert "session_tokens_used" in stats
        assert "session_token_budget" in stats
        assert "budget_pct_used" in stats
        assert "model" in stats
        assert "model_lane" in stats

    def test_get_capsules_empty(self):
        from src.kortana.services.experience_distiller import ExperienceDistiller

        distiller = ExperienceDistiller(AsyncMock())
        assert distiller.get_capsules() == []


# ---------------------------------------------------------------
# Router integration tests
# ---------------------------------------------------------------
@pytest.fixture
def client():
    from src.kortana.main import app
    from tests.conftest import SyncTestClient

    return SyncTestClient(app)


class TestConsciousnessRouter:
    def test_status_endpoint(self, client):
        resp = client.get("/api/consciousness/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["phase"] == 8
        assert "memory_engine" in data["systems"]
        assert "self_diagnostic" in data["systems"]
        assert "experience_distiller" in data["systems"]
        assert "revelation_engine" in data["systems"]
        assert "model" in data["systems"]["self_diagnostic"]
        assert "model_lane" in data["systems"]["self_diagnostic"]
        assert "model" in data["systems"]["experience_distiller"]
        assert "model_lane" in data["systems"]["experience_distiller"]
        assert "unsurfaced_revelations" in data["systems"]["revelation_engine"]
        assert "token_stats" in data

    def test_memory_stats(self, client):
        resp = client.get("/api/consciousness/memory/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_memories" in data
        assert "embedding_model" in data

    def test_memory_store(self, client):
        resp = client.post(
            "/api/consciousness/memory/store",
            json={"content": "test memory for phase 8"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "stored"
        assert "id" in data

    def test_memory_store_validation(self, client):
        resp = client.post(
            "/api/consciousness/memory/store",
            json={"content": ""},
        )
        assert resp.status_code == 422

    def test_memory_search(self, client):
        resp = client.get("/api/consciousness/memory/search?q=test")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "query" in data

    def test_diagnostics_analyze(self, client):
        resp = client.post(
            "/api/consciousness/diagnostics/analyze",
            json={
                "error_type": "ValueError",
                "error_message": "invalid input for test",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "root_cause" in data
        assert "suggested_fix" in data

    def test_diagnostics_history(self, client):
        resp = client.get("/api/consciousness/diagnostics/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "history" in data

    def test_diagnostics_patterns(self, client):
        resp = client.get("/api/consciousness/diagnostics/patterns")
        assert resp.status_code == 200
        data = resp.json()
        assert "patterns" in data

    def test_experience_capsules(self, client):
        resp = client.get("/api/consciousness/experience/capsules")
        assert resp.status_code == 200
        data = resp.json()
        assert "capsules" in data

    def test_experience_cost(self, client):
        resp = client.get("/api/consciousness/experience/cost")
        assert resp.status_code == 200
        data = resp.json()
        assert "session_tokens_used" in data
        assert "model" in data
        assert "model_lane" in data

    def test_experience_distil(self, client):
        resp = client.post(
            "/api/consciousness/experience/distil",
            json={"age_hours": 1},
        )
        assert resp.status_code == 200

    def test_memory_backfill(self, client):
        resp = client.post("/api/consciousness/memory/backfill")
        assert resp.status_code == 200
        data = resp.json()
        assert "backfilled" in data

    def test_revelation_synthesise_endpoint(self, client):
        created_at = datetime.utcnow()
        revelation = SimpleNamespace(
            id="rev-1",
            title="Pattern emerging",
            content="Recent work keeps converging on silent autonomy.",
            revelation_type="pattern",
            confidence=0.82,
            evidence=["memory", "git"],
            created_at=created_at,
        )

        with (
            patch(
                "src.kortana.routers.consciousness.RevelationEngine.synthesise",
                new=AsyncMock(return_value=[revelation]),
            ),
            patch(
                "src.kortana.routers.consciousness.get_token_stats",
                return_value={
                    "session_tokens_used": 120,
                    "session_token_budget": 30000,
                    "budget_remaining": 29880,
                    "budget_pct_used": 0.4,
                },
            ),
        ):
            resp = client.post(
                "/api/consciousness/memory/revelation",
                json={"force": True},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["revelations_written"] == 1
        assert data["revelations"][0]["title"] == "Pattern emerging"
        assert data["token_stats"]["session_tokens_used"] == 120

    def test_revelation_list_endpoint(self, client):
        created_at = datetime.utcnow()
        revelation = SimpleNamespace(
            id="rev-2",
            title="Operator stewardship matters",
            content="Manual acknowledgement keeps high-signal insights scarce.",
            revelation_type="self_discovery",
            confidence=0.74,
            evidence=["operator", "daemon"],
            surfaced=False,
            acknowledged_at=None,
            created_at=created_at,
        )

        with patch(
            "src.kortana.routers.consciousness.RevelationEngine.list_revelations",
            new=AsyncMock(return_value=[revelation]),
        ):
            resp = client.get("/api/consciousness/memory/revelations?unsurfaced_only=true")

        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["revelations"][0]["revelation_type"] == "self_discovery"
        assert data["revelations"][0]["surfaced"] is False

    def test_revelation_acknowledge_endpoint(self, client):
        with patch(
            "src.kortana.routers.consciousness.RevelationEngine.mark_surfaced",
            new=AsyncMock(return_value=True),
        ):
            resp = client.post("/api/consciousness/memory/revelations/rev-2/acknowledge")

        assert resp.status_code == 200
        assert resp.json() == {"id": "rev-2", "surfaced": True}

    def test_revelation_acknowledge_returns_404(self, client):
        with patch(
            "src.kortana.routers.consciousness.RevelationEngine.mark_surfaced",
            new=AsyncMock(return_value=False),
        ):
            resp = client.post("/api/consciousness/memory/revelations/missing/acknowledge")

        assert resp.status_code == 404
