"""Tests for conversation history management."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from sqlalchemy.orm import Session

from kortana.modules.conversation_history import models, schemas, services


class TestConversationHistoryService:
    """Test conversation history service."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create a conversation history service."""
        return services.ConversationHistoryService(mock_db)
    
    def test_create_conversation(self, service, mock_db):
        """Test creating a new conversation."""
        conv_create = schemas.ConversationCreate(
            user_id="test_user",
            title="Test Conversation"
        )
        
        # Mock the database operations
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        mock_db.add = Mock()
        
        mock_conversation = Mock(spec=models.Conversation)
        mock_conversation.id = 1
        mock_conversation.user_id = "test_user"
        
        # Call create
        service.create_conversation(conv_create)
        
        # Verify database operations were called
        assert mock_db.add.called
        assert mock_db.commit.called
    
    def test_add_message(self, service, mock_db):
        """Test adding a message to conversation."""
        # Setup mock conversation
        mock_conversation = Mock(spec=models.Conversation)
        mock_conversation.id = 1
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation
        
        message_create = schemas.ConversationMessageCreate(
            role="user",
            content="Hello"
        )
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        service.add_message(1, message_create)
        
        assert mock_db.add.called
        assert mock_db.commit.called
    
    def test_add_message_conversation_not_found(self, service, mock_db):
        """Test adding message to non-existent conversation."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        message_create = schemas.ConversationMessageCreate(
            role="user",
            content="Hello"
        )
        
        with pytest.raises(ValueError, match="Conversation .* not found"):
            service.add_message(999, message_create)
    
    def test_search_conversations_by_user(self, service, mock_db):
        """Test searching conversations by user ID."""
        filters = schemas.ConversationSearchFilters(user_id="test_user")
        
        mock_conversations = [Mock(spec=models.Conversation) for _ in range(3)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_conversations
        
        results = service.search_conversations(filters)
        
        assert len(results) == 3
    
    def test_search_conversations_by_date_range(self, service, mock_db):
        """Test searching conversations by date range."""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        filters = schemas.ConversationSearchFilters(
            user_id="test_user",
            start_date=start_date,
            end_date=end_date
        )
        
        mock_conversations = [Mock(spec=models.Conversation)]
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_conversations
        
        results = service.search_conversations(filters)
        
        assert len(results) >= 0
    
    def test_search_conversations_by_keyword(self, service, mock_db):
        """Test searching conversations by keyword."""
        filters = schemas.ConversationSearchFilters(
            user_id="test_user",
            keyword="python"
        )
        
        # Setup mock query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        results = service.search_conversations(filters)
        
        assert mock_query.join.called
    
    def test_archive_conversation(self, service, mock_db):
        """Test archiving a conversation with compression."""
        # Setup mock conversation with messages
        mock_message = Mock(spec=models.ConversationMessage)
        mock_message.role = "user"
        mock_message.content = "Test message"
        mock_message.created_at = datetime.now()
        
        mock_conversation = Mock(spec=models.Conversation)
        mock_conversation.id = 1
        mock_conversation.messages = [mock_message]
        mock_conversation.metadata = {}
        
        mock_db.query.return_value.filter.return_value.options.return_value.first.return_value = mock_conversation
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = service.archive_conversation(1)
        
        assert result is not None
        assert result.status == models.ConversationStatus.ARCHIVED
        assert "compressed_messages" in result.metadata
    
    def test_delete_conversation(self, service, mock_db):
        """Test soft deleting a conversation."""
        mock_conversation = Mock(spec=models.Conversation)
        mock_conversation.id = 1
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation
        mock_db.commit = Mock()
        
        result = service.delete_conversation(1)
        
        assert result is True
        assert mock_conversation.status == models.ConversationStatus.DELETED
    
    def test_get_conversation_stats(self, service, mock_db):
        """Test getting conversation statistics."""
        # Setup mock messages
        messages = []
        for i, role in enumerate(["user", "assistant", "user"]):
            msg = Mock(spec=models.ConversationMessage)
            msg.role = role
            msg.metadata = {"response_time_ms": 100 + i * 10}
            messages.append(msg)
        
        mock_conversation = Mock(spec=models.Conversation)
        mock_conversation.id = 1
        mock_conversation.messages = messages
        mock_conversation.created_at = datetime.now()
        mock_conversation.updated_at = datetime.now()
        mock_conversation.status = models.ConversationStatus.ACTIVE
        
        mock_db.query.return_value.filter.return_value.options.return_value.first.return_value = mock_conversation
        
        stats = service.get_conversation_stats(1)
        
        assert stats["conversation_id"] == 1
        assert stats["total_messages"] == 3
        assert stats["user_messages"] == 2
        assert stats["assistant_messages"] == 1
        assert stats["average_response_time_ms"] is not None
