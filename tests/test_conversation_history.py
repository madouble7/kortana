"""
Tests for conversation history service and API endpoints.
Validates UI consistency requirements including tag filtering, keyword search, and timestamp queries.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.kortana.services.conversation_history import (
    ConversationHistoryService,
)


class TestConversationHistoryService:
    """Test the conversation history service."""

    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create temporary storage for tests."""
        return tmp_path / "test_conversations"

    @pytest.fixture
    def service(self, temp_storage):
        """Create a service instance with temporary storage."""
        return ConversationHistoryService(storage_path=temp_storage)

    def test_create_conversation(self, service):
        """Test creating a new conversation."""
        conv = service.create_conversation(user_id="user123", tags=["work", "python"])

        assert conv.id is not None
        assert conv.user_id == "user123"
        assert "work" in conv.tags
        assert "python" in conv.tags
        assert len(conv.messages) == 0

    def test_save_and_retrieve_conversation(self, service):
        """Test saving and retrieving a conversation."""
        conv = service.create_conversation(user_id="user456")
        conv.add_message("user", "Hello, Kor'tana!")
        conv.add_message("assistant", "Hello! How can I help you today?")
        service.save_conversation(conv)

        # Retrieve
        retrieved = service.get_conversation(conv.id)
        assert retrieved is not None
        assert retrieved.id == conv.id
        assert len(retrieved.messages) == 2
        assert retrieved.messages[0].content == "Hello, Kor'tana!"

    def test_delete_conversation(self, service):
        """Test deleting a conversation."""
        conv = service.create_conversation()
        conv_id = conv.id

        # Verify it exists
        assert service.get_conversation(conv_id) is not None

        # Delete
        success = service.delete_conversation(conv_id)
        assert success is True

        # Verify it's gone
        assert service.get_conversation(conv_id) is None

    def test_add_tags(self, service):
        """Test adding tags to a conversation."""
        conv = service.create_conversation(tags=["initial"])
        service.add_tags(conv.id, ["tag1", "tag2"])

        updated = service.get_conversation(conv.id)
        assert "initial" in updated.tags
        assert "tag1" in updated.tags
        assert "tag2" in updated.tags

    def test_remove_tags(self, service):
        """Test removing tags from a conversation."""
        conv = service.create_conversation(tags=["tag1", "tag2", "tag3"])
        service.remove_tags(conv.id, ["tag2"])

        updated = service.get_conversation(conv.id)
        assert "tag1" in updated.tags
        assert "tag2" not in updated.tags
        assert "tag3" in updated.tags

    def test_filter_by_tags(self, service):
        """Test filtering conversations by tags."""
        # Create conversations with different tags
        conv1 = service.create_conversation(tags=["python", "ai"])
        conv2 = service.create_conversation(tags=["javascript", "web"])
        conv3 = service.create_conversation(tags=["python", "web"])

        # Filter by python tag
        results = service.list_conversations(tags=["python"])
        assert len(results) == 2
        assert any(c.id == conv1.id for c in results)
        assert any(c.id == conv3.id for c in results)

    def test_filter_by_keywords(self, service):
        """Test filtering conversations by keywords."""
        conv1 = service.create_conversation()
        conv1.add_message("user", "Tell me about machine learning")
        service.save_conversation(conv1)

        conv2 = service.create_conversation()
        conv2.add_message("user", "What is the weather?")
        service.save_conversation(conv2)

        # Search for "machine"
        results = service.list_conversations(keywords=["machine"])
        assert len(results) == 1
        assert results[0].id == conv1.id

    def test_filter_by_engagement_rank(self, service):
        """Test filtering by engagement rank."""
        # Create conversations with different lengths (affects engagement)
        conv1 = service.create_conversation()
        for i in range(20):  # High engagement
            conv1.add_message("user", f"Message {i}" * 10)
        service.save_conversation(conv1)

        conv2 = service.create_conversation()
        conv2.add_message("user", "Short")  # Low engagement
        service.save_conversation(conv2)

        # Filter high engagement
        results = service.list_conversations(min_engagement_rank=0.5)
        assert len(results) >= 1
        assert conv1.id in [c.id for c in results]

    def test_filter_by_user_and_timestamp(self, service):
        """Test filtering by user ID and timestamp range."""
        user_id = "test_user"

        # Create conversations at different times (simulate by manipulating created_at)
        conv1 = service.create_conversation(user_id=user_id)
        conv1.created_at = datetime.utcnow() - timedelta(days=2)
        service.save_conversation(conv1)

        conv2 = service.create_conversation(user_id=user_id)
        conv2.created_at = datetime.utcnow()
        service.save_conversation(conv2)

        conv3 = service.create_conversation(user_id="other_user")
        service.save_conversation(conv3)

        # Search for test_user conversations from last day
        start_time = datetime.utcnow() - timedelta(days=1)
        results = service.search_by_user_timestamp(
            user_id=user_id,
            start_timestamp=start_time,
        )

        assert len(results) == 1
        assert results[0].id == conv2.id

    def test_engagement_rank_calculation(self, service):
        """Test that engagement rank is calculated correctly."""
        conv = service.create_conversation()

        # Initially should be 0
        assert conv.engagement_rank == 0.0

        # Add messages
        for i in range(10):
            conv.add_message("user", f"This is a longer message about topic {i}" * 5)

        # Should have increased
        assert conv.engagement_rank > 0.0
        assert conv.engagement_rank <= 1.0

    def test_conversation_preview(self, service):
        """Test getting conversation preview."""
        conv = service.create_conversation()
        long_message = "This is a very long message that should be truncated " * 10
        conv.add_message("user", long_message)
        service.save_conversation(conv)

        preview = service.get_conversation_preview(conv.id, max_chars=50)
        assert len(preview) <= 53  # 50 + "..."
        assert preview.endswith("...")

    def test_statistics(self, service):
        """Test getting conversation statistics."""
        # Create several conversations
        for i in range(3):
            conv = service.create_conversation(
                user_id=f"user{i}",
                tags=[f"tag{i}", "common"],
            )
            conv.add_message("user", f"Message {i}")
            service.save_conversation(conv)

        stats = service.get_statistics()
        assert stats["total_conversations"] == 3
        assert stats["total_messages"] == 3
        assert stats["unique_users"] == 3
        assert "common" in stats["unique_tags"]


class TestConversationAPI:
    """Test the conversation history API endpoints."""

    @pytest.fixture
    def client(self, tmp_path):
        """Create a test client with temporary storage."""
        with patch(
            "src.kortana.api.routers.conversation_router.ConversationHistoryService"
        ) as mock_service_class:
            # Use actual service with temp storage
            service = ConversationHistoryService(storage_path=tmp_path / "api_test_conversations")
            mock_service_class.return_value = service

            # Import here to use the patched service
            from src.kortana.api.routers.conversation_router import router
            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            # Replace the module-level service instance
            import src.kortana.api.routers.conversation_router as conv_router_module
            conv_router_module.conversation_service = service

            return TestClient(app)

    def test_create_conversation_endpoint(self, client):
        """Test POST /conversations/ endpoint."""
        response = client.post(
            "/conversations/",
            json={"user_id": "user123", "tags": ["test"]},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "user123"
        assert "test" in data["tags"]
        assert "id" in data

    def test_get_conversation_endpoint(self, client):
        """Test GET /conversations/{id} endpoint."""
        # Create a conversation first
        create_response = client.post(
            "/conversations/",
            json={"user_id": "user456"},
        )
        conv_id = create_response.json()["id"]

        # Get it
        response = client.get(f"/conversations/{conv_id}")
        assert response.status_code == 200
        assert response.json()["id"] == conv_id

    def test_add_message_endpoint(self, client):
        """Test POST /conversations/{id}/messages endpoint."""
        # Create conversation
        create_response = client.post("/conversations/", json={})
        conv_id = create_response.json()["id"]

        # Add message
        response = client.post(
            f"/conversations/{conv_id}/messages",
            json={
                "role": "user",
                "content": "Hello!",
                "metadata": {"source": "test"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Hello!"

    def test_list_with_filters_endpoint(self, client):
        """Test GET /conversations/ with filters."""
        # Create test conversations
        client.post("/conversations/", json={"tags": ["python"]})
        client.post("/conversations/", json={"tags": ["javascript"]})

        # List with tag filter
        response = client.get("/conversations/?tags=python")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_tag_management_endpoints(self, client):
        """Test tag add/remove endpoints."""
        # Create conversation
        create_response = client.post("/conversations/", json={"tags": ["initial"]})
        conv_id = create_response.json()["id"]

        # Add tags
        response = client.post(
            f"/conversations/{conv_id}/tags",
            json={"tags": ["new1", "new2"]},
        )
        assert response.status_code == 200
        tags = response.json()["tags"]
        assert "new1" in tags
        assert "new2" in tags

        # Remove tags
        response = client.delete(
            f"/conversations/{conv_id}/tags",
            json={"tags": ["new1"]},
        )
        assert response.status_code == 200
        tags = response.json()["tags"]
        assert "new1" not in tags
        assert "new2" in tags

    def test_user_search_endpoint(self, client):
        """Test GET /conversations/users/{user_id}/search endpoint."""
        user_id = "search_test_user"

        # Create conversations for this user
        client.post("/conversations/", json={"user_id": user_id})
        client.post("/conversations/", json={"user_id": user_id})

        # Search
        response = client.get(f"/conversations/users/{user_id}/search")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert data["total"] == 2

    def test_statistics_endpoint(self, client):
        """Test GET /conversations/statistics endpoint."""
        # Create some conversations
        client.post("/conversations/", json={"user_id": "user1"})
        client.post("/conversations/", json={"user_id": "user2"})

        response = client.get("/conversations/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_conversations" in data
        assert "total_messages" in data
        assert data["total_conversations"] >= 2
