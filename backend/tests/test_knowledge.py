"""Tests for routers/knowledge.py - KnowledgeManager and endpoints"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def client():
    from src.kortana.main import app
    from tests.conftest import SyncTestClient

    return SyncTestClient(app)


@pytest.fixture(autouse=True)
def reset_knowledge_base():
    """Clear knowledge base before each test"""
    import src.kortana.routers.knowledge as km

    km.knowledge_base.clear()
    km.ritual_documents.clear()
    # Reset the manager's references (they point to same lists)
    km.knowledge_manager.knowledge = km.knowledge_base
    km.knowledge_manager.rituals = km.ritual_documents
    yield
    km.knowledge_base.clear()
    km.ritual_documents.clear()


class TestKnowledgeManagerExtractTags:
    def test_extracts_backend_tag(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        tags = km._extract_tags("This is an api endpoint handler", "")
        assert "backend" in tags

    def test_extracts_frontend_tag(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        tags = km._extract_tags("React component UI", "")
        assert "frontend" in tags

    def test_extracts_testing_tag(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        tags = km._extract_tags("pytest test coverage", "")
        assert "testing" in tags

    def test_extracts_deployment_tag(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        tags = km._extract_tags("docker deploy cloud", "")
        assert "deployment" in tags

    def test_extracts_autonomy_tag_from_analysis(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        tags = km._extract_tags("nothing", "autonomous ai system")
        assert "autonomy" in tags

    def test_extracts_debugging_tag_from_analysis(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        tags = km._extract_tags("nothing", "fix the bug error")
        assert "debugging" in tags

    def test_extracts_performance_tag_from_analysis(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        tags = km._extract_tags("nothing", "optimize performance speed")
        assert "performance" in tags

    def test_no_duplicate_tags(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        tags = km._extract_tags("api endpoint api backend", "")
        assert len(tags) == len(set(tags))


class TestKnowledgeManagerIsRecent:
    def test_recent_timestamp_returns_true(self):
        from datetime import datetime

        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        now = datetime.now().isoformat()
        assert km._is_recent(now) is True

    def test_old_timestamp_returns_false(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        assert km._is_recent("2020-01-01T00:00:00") is False

    def test_invalid_timestamp_returns_false(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        assert km._is_recent("not-a-timestamp") is False


class TestKnowledgeManagerIngestLearning:
    @pytest.mark.asyncio
    async def test_ingest_new_learning(self):
        from src.kortana.routers.knowledge import KnowledgeManager, knowledge_base

        km = KnowledgeManager()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"analysis": "Test insight analysis"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.kortana.routers.knowledge.httpx.AsyncClient", return_value=mock_client
        ):
            result = await km.ingest_learning("Test content", "test_source")

        assert "insight" in result
        assert len(knowledge_base) >= 1

    @pytest.mark.asyncio
    async def test_ingest_duplicate_updates_existing(self):
        from src.kortana.routers.knowledge import KnowledgeManager, knowledge_base

        km = KnowledgeManager()
        initial_len = len(knowledge_base)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"analysis": "Analysis"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.kortana.routers.knowledge.httpx.AsyncClient", return_value=mock_client
        ):
            await km.ingest_learning("Test content", "src")
            await km.ingest_learning("Test content", "src")

        assert len(knowledge_base) == initial_len + 1  # Should not duplicate

    @pytest.mark.asyncio
    async def test_ingest_with_metadata(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"analysis": "Analysis"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.kortana.routers.knowledge.httpx.AsyncClient", return_value=mock_client
        ):
            result = await km.ingest_learning("Content", "source", {"key": "value"})

        assert result["insight"]["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_ingest_gemini_failure_graceful(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.kortana.routers.knowledge.httpx.AsyncClient", return_value=mock_client
        ):
            result = await km.ingest_learning("Content", "source")

        assert "insight" in result  # Still works, just with fallback analysis

    @pytest.mark.asyncio
    async def test_ingest_request_exception_graceful(self):
        import httpx

        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.RequestError("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.kortana.routers.knowledge.httpx.AsyncClient", return_value=mock_client
        ):
            result = await km.ingest_learning("Content", "source")

        assert "insight" in result


class TestKnowledgeManagerSearchKnowledge:
    def test_search_returns_matching_results(self):
        from src.kortana.routers.knowledge import KnowledgeManager, knowledge_base

        km = KnowledgeManager()
        km.knowledge = knowledge_base

        knowledge_base.append(
            {
                "id": "abc",
                "source": "test",
                "content": "python programming guide",
                "insights": "Python best practices",
                "tags": ["backend"],
                "timestamp": "2026-01-01T00:00:00",
            }
        )

        results = km.search_knowledge("python")
        assert len(results) == 1

    def test_search_no_match_returns_empty(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        results = km.search_knowledge("nonexistent_term_xyz")
        assert results == []

    def test_search_respects_limit(self):
        from src.kortana.routers.knowledge import KnowledgeManager, knowledge_base

        km = KnowledgeManager()
        km.knowledge = knowledge_base

        for i in range(20):
            knowledge_base.append(
                {
                    "id": f"id{i}",
                    "source": "test",
                    "content": "python test",
                    "insights": "insights",
                    "tags": [],
                    "timestamp": "2026-01-01T00:00:00",
                }
            )

        results = km.search_knowledge("python", limit=5)
        assert len(results) == 5

    def test_search_with_tag_filter(self):
        from src.kortana.routers.knowledge import KnowledgeManager, knowledge_base

        km = KnowledgeManager()
        km.knowledge = knowledge_base

        knowledge_base.append(
            {
                "id": "x1",
                "content": "python backend api",
                "insights": "test insights",
                "tags": ["backend"],
                "timestamp": "2026-01-01T00:00:00",
            }
        )
        knowledge_base.append(
            {
                "id": "x2",
                "content": "python frontend react",
                "insights": "test insights",
                "tags": ["frontend"],
                "timestamp": "2026-01-01T00:00:00",
            }
        )

        results = km.search_knowledge("python", tags=["backend"])
        assert len(results) == 1
        assert results[0]["id"] == "x1"


class TestKnowledgeManagerCovenantIndex:
    def test_update_covenant_index_empty(self):
        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()
        result = km.update_covenant_index()
        assert "timestamp" in result
        assert result["autonomy_status"] == "initializing"

    def test_update_covenant_index_with_data(self):
        from src.kortana.routers.knowledge import KnowledgeManager, knowledge_base

        km = KnowledgeManager()
        km.knowledge = knowledge_base

        knowledge_base.append(
            {
                "id": "x1",
                "content": "content",
                "insights": "insights",
                "tags": ["backend", "testing"],
                "timestamp": "2026-01-01T00:00:00",
            }
        )

        result = km.update_covenant_index()
        assert result["autonomy_status"] == "active"
        assert result["knowledge_stats"]["total_insights"] == 1
        assert "backend" in result["knowledge_stats"]["unique_tags"]


class TestKnowledgeManagerGenerateRitual:
    @pytest.mark.asyncio
    async def test_generate_ritual_with_mock(self):
        from src.kortana.routers.knowledge import KnowledgeManager, ritual_documents

        km = KnowledgeManager()
        km.rituals = ritual_documents

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "analysis": "# Ritual Document\n\nMilestone achieved"
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.kortana.routers.knowledge.httpx.AsyncClient", return_value=mock_client
        ):
            ritual = await km.generate_ritual_document(
                "First PR Merged", "Context info"
            )

        assert "ritual_17" == ritual["id"]
        assert ritual["milestone"] == "First PR Merged"
        assert len(ritual_documents) >= 1

    @pytest.mark.asyncio
    async def test_generate_ritual_request_failure_graceful(self):
        import httpx

        from src.kortana.routers.knowledge import KnowledgeManager

        km = KnowledgeManager()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.RequestError("Error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.kortana.routers.knowledge.httpx.AsyncClient", return_value=mock_client
        ):
            ritual = await km.generate_ritual_document("Milestone", "Context")

        assert "content" in ritual  # Graceful fallback


class TestKnowledgeRouterEndpoints:
    def test_ingest_empty_content_returns_400(self, client):
        resp = client.post("/api/knowledge/ingest", json={"content": ""})
        assert resp.status_code == 400

    def test_ingest_valid_content(self, client):
        with patch("src.kortana.routers.knowledge.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200, json=MagicMock(return_value={"analysis": "insights"})
            )
            resp = client.post(
                "/api/knowledge/ingest",
                json={
                    "content": "Python API testing",
                    "source": "test_suite",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "insight" in data

    def test_search_with_query(self, client):
        import src.kortana.routers.knowledge as km_mod

        km_mod.knowledge_base.append(
            {
                "id": "s1",
                "content": "python testing guide",
                "insights": "Tests are important",
                "tags": [],
                "timestamp": "2026-01-01T00:00:00",
            }
        )
        km_mod.knowledge_manager.knowledge = km_mod.knowledge_base

        resp = client.get("/api/knowledge/search?query=python")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert data["total_results"] >= 1

    def test_search_no_results(self, client):
        resp = client.get("/api/knowledge/search?query=xyzunknown123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_results"] == 0

    def test_search_with_tags(self, client):
        import src.kortana.routers.knowledge as km_mod

        km_mod.knowledge_base.append(
            {
                "id": "s2",
                "content": "backend api",
                "insights": "test",
                "tags": ["backend"],
                "timestamp": "2026-01-01T00:00:00",
            }
        )
        km_mod.knowledge_manager.knowledge = km_mod.knowledge_base

        resp = client.get("/api/knowledge/search?query=backend&tags=backend")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_results"] >= 1

    def test_ritual_missing_milestone_returns_400(self, client):
        resp = client.post("/api/knowledge/ritual", json={})
        assert resp.status_code == 400

    def test_ritual_generation(self, client):
        with patch("src.kortana.routers.knowledge.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"analysis": "Ritual content"}),
            )
            resp = client.post(
                "/api/knowledge/ritual",
                json={
                    "milestone": "100% Coverage",
                    "context": "All tests passing",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "ritual" in data

    def test_covenant_status(self, client):
        resp = client.get("/api/knowledge/covenant")
        assert resp.status_code == 200
        data = resp.json()
        assert "covenant_status" in data
        assert "knowledge_base_size" in data
        assert "ritual_count" in data

    def test_knowledge_stats_empty(self, client):
        resp = client.get("/api/knowledge/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_insights"] == 0
        assert "tag_distribution" in data
        assert "source_distribution" in data

    def test_knowledge_stats_with_data(self, client):
        import src.kortana.routers.knowledge as km_mod

        km_mod.knowledge_base.append(
            {
                "id": "x1",
                "content": "content",
                "insights": "insights",
                "tags": ["backend"],
                "source": "github",
                "timestamp": "2026-01-01T00:00:00",
            }
        )
        km_mod.knowledge_manager.knowledge = km_mod.knowledge_base

        resp = client.get("/api/knowledge/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_insights"] == 1
        assert data["tag_distribution"]["backend"] == 1
        assert data["source_distribution"]["github"] == 1
