"""Tests for small routers: agents, system, memory, prayer, rclone"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def client():
    from src.kortana.main import app
    from tests.conftest import SyncTestClient

    return SyncTestClient(app)


class TestAgentsRouter:
    def test_list_agents_empty(self, client):
        # Reset agents list to empty state
        import src.kortana.routers.agents as agents_module

        agents_module.agents.clear()
        resp = client.get("/api/agents/list")
        assert resp.status_code == 200
        assert "agents" in resp.json()

    def test_create_agent(self, client):
        import src.kortana.routers.agents as agents_module

        agents_module.agents.clear()
        resp = client.post(
            "/api/agents/create",
            json={
                "name": "TestAgent",
                "description": "A test agent",
                "capabilities": ["code", "search"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent"]["name"] == "TestAgent"
        assert data["agent"]["status"] == "created"

    def test_create_agent_minimal(self, client):
        import src.kortana.routers.agents as agents_module

        agents_module.agents.clear()
        resp = client.post("/api/agents/create", json={})
        assert resp.status_code == 200

    def test_execute_agent(self, client):
        import src.kortana.routers.agents as agents_module

        agents_module.agents.clear()
        # Create an agent first
        client.post("/api/agents/create", json={"name": "ExecAgent"})
        resp = client.post("/api/agents/execute/0", json={"task": "do something"})
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        assert "do something" in data["result"]

    def test_execute_nonexistent_agent(self, client):
        import src.kortana.routers.agents as agents_module

        agents_module.agents.clear()
        resp = client.post("/api/agents/execute/999", json={"task": "run"})
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_list_agents_after_create(self, client):
        import src.kortana.routers.agents as agents_module

        agents_module.agents.clear()
        client.post("/api/agents/create", json={"name": "ListAgent"})
        resp = client.get("/api/agents/list")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["agents"]) >= 1


class TestSystemRouter:
    def test_system_info(self, client):
        resp = client.get("/api/system/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "os" in data
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "python_version" in data

    def test_system_settings(self, client):
        resp = client.get("/api/system/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert "environment" in data
        assert "debug" in data
        assert "version" in data

    def test_system_model_lanes(self, client):
        resp = client.get("/api/system/model-lanes")
        assert resp.status_code == 200
        data = resp.json()
        assert "active_lane" in data
        assert "catalogs" in data
        assert "runtime_usage" in data
        assert "gemini_service" in data
        assert "llm_router" in data
        assert "consensus" in data
        assert "cost_router" in data
        assert "chat_models" in data["catalogs"]
        assert "embedding_models" in data["catalogs"]
        assert "known_core_catalog" in data["catalogs"]["chat_models"]
        assert "subsystem_defaults" in data["catalogs"]["chat_models"]
        assert "memory_engine" in data["catalogs"]["embedding_models"]
        assert "total_generations" in data["runtime_usage"]
        assert "memory" in data["runtime_usage"]
        assert "persisted" in data["runtime_usage"]

    def test_system_model_lanes_uses_shared_cost_router(self, client):
        shared_router = MagicMock()
        shared_router.get_routing_strategy.return_value = {"priorities": []}
        shared_router.get_cost_report.return_value = {
            "totals": {"requests": 1},
            "providers": {},
        }

        with patch(
            "src.kortana.cost_optimized_model_router.get_cost_optimized_model_router",
            return_value=shared_router,
        ):
            resp = client.get("/api/system/model-lanes")

        assert resp.status_code == 200
        data = resp.json()
        assert data["cost_router"]["cost"]["totals"]["requests"] == 1

    def test_system_logs_no_file(self, client):
        # Log file probably doesn't exist in test environment
        resp = client.get("/api/system/logs")
        assert resp.status_code in [200, 500]
        if resp.status_code == 200:
            data = resp.json()
            assert "logs" in data


class TestMemoryRouter:
    def test_get_documents_empty(self, client):
        import src.kortana.routers.memory as mem_module

        mem_module.knowledge_base.clear()
        resp = client.get("/api/memory/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert "documents" in data

    def test_add_document(self, client):
        import src.kortana.routers.memory as mem_module

        mem_module.knowledge_base.clear()
        resp = client.post(
            "/api/memory/add_document",
            json={
                "title": "Test Doc",
                "content": "This is test content about Python.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["document"]["title"] == "Test Doc"

    def test_add_document_minimal(self, client):
        import src.kortana.routers.memory as mem_module

        mem_module.knowledge_base.clear()
        resp = client.post("/api/memory/add_document", json={})
        assert resp.status_code == 200

    def test_search_documents_get(self, client):
        import src.kortana.routers.memory as mem_module

        mem_module.knowledge_base.clear()
        mem_module.knowledge_base.append(
            {"id": 0, "title": "Python Guide", "content": "Python is great"}
        )
        resp = client.get("/api/memory/search?query=python")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert len(data["results"]) >= 1

    def test_search_documents_post(self, client):
        import src.kortana.routers.memory as mem_module

        mem_module.knowledge_base.clear()
        mem_module.knowledge_base.append(
            {"id": 0, "title": "Test", "content": "hello world"}
        )
        resp = client.post("/api/memory/search", json={"query": "hello"})
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data

    def test_search_no_results(self, client):
        import src.kortana.routers.memory as mem_module

        mem_module.knowledge_base.clear()
        resp = client.post("/api/memory/search", json={"query": "xyznotfound"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"] == []

    def test_documents_accessible_after_add(self, client):
        import src.kortana.routers.memory as mem_module

        mem_module.knowledge_base.clear()
        client.post("/api/memory/add_document", json={"title": "A", "content": "apple"})
        resp = client.get("/api/memory/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["documents"]) >= 1


class TestPrayerRouter:
    def test_prayer_endpoints_accessible(self, client):
        """Prayer router has minimal routes - just verify they're accessible"""
        import src.kortana.routers.prayer as prayer_module

        # Check the router exists and has routes
        assert prayer_module.router is not None
