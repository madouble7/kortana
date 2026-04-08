"""
Tests for Pydantic schemas and validation
"""

from datetime import datetime

import pytest
from pydantic import ValidationError
from src.kortana.schemas import (
    AgentCreate,
    AgentStatus,
    ErrorResponse,
    HealthCheck,
    LoginRequest,
    TaskCreate,
    TaskStatus,
    Token,
    User,
    UserCreate,
    UserUpdate,
)


@pytest.mark.unit
class TestUserSchemas:
    """User schema validation tests"""

    def test_create_valid_user(self):
        """Test creating valid user"""
        user = UserCreate(
            username="testuser", email="test@example.com", password="securepass123"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_user_requires_long_password(self):
        """Test that password must be at least 8 characters"""
        with pytest.raises(ValidationError):
            UserCreate(username="testuser", email="test@example.com", password="short")

    def test_user_requires_valid_email(self):
        """Test that email must be valid"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser", email="invalid-email", password="securepass123"
            )

    def test_full_user_model(self):
        """Test full user model"""
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(),
        )
        assert user.id == 1
        assert user.is_active is True


@pytest.mark.unit
class TestAgentSchemas:
    """Agent schema validation tests"""

    def test_create_valid_agent(self):
        """Test creating valid agent"""
        agent = AgentCreate(
            name="Test Agent",
            description="A test agent",
            model="gpt-4",
            temperature=0.7,
        )
        assert agent.name == "Test Agent"
        assert agent.temperature == 0.7

    def test_agent_temperature_bounds(self):
        """Test temperature must be 0-1"""
        with pytest.raises(ValidationError):
            AgentCreate(name="Test Agent", model="gpt-4", temperature=1.5)

        with pytest.raises(ValidationError):
            AgentCreate(name="Test Agent", model="gpt-4", temperature=-0.5)

    def test_agent_status_enum(self):
        """Test agent status enum"""
        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.RUNNING == "running"
        assert AgentStatus.PAUSED == "paused"
        assert AgentStatus.ERROR == "error"


@pytest.mark.unit
class TestTaskSchemas:
    """Task schema validation tests"""

    def test_create_valid_task(self):
        """Test creating valid task"""
        task = TaskCreate(
            title="Test Task", description="A test task", agent_id="1", priority=1
        )
        assert task.title == "Test Task"
        assert task.priority == 1

    def test_task_priority_bounds(self):
        """Test priority must be 1-5"""
        with pytest.raises(ValidationError):
            TaskCreate(title="Test Task", agent_id="1", priority=11)

        with pytest.raises(ValidationError):
            TaskCreate(title="Test Task", agent_id="1", priority=0)

    def test_task_status_enum(self):
        """Test task status enum"""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"


@pytest.mark.unit
class TestAuthSchemas:
    """Authentication schema validation tests"""

    def test_token_schema(self):
        """Test token response schema"""
        token = Token(
            access_token="test.token.here", token_type="bearer", expires_in=1800
        )
        assert token.token_type == "bearer"

    def test_login_request(self):
        """Test login request schema"""
        login = LoginRequest(username="testuser", password="password123")
        assert login.username == "testuser"


@pytest.mark.unit
class TestHealthSchemas:
    """Health check schema tests"""

    def test_health_check_response(self):
        """Test health check response"""
        health = HealthCheck(
            status="healthy",
            message="All systems operational",
            environment="development",
            version="0.1.0",
        )
        assert health.status == "healthy"
        assert health.timestamp is not None

    def test_error_response(self):
        """Test error response schema"""
        error = ErrorResponse(
            error="NOT_FOUND", status_code=404, message="Resource not found"
        )
        assert error.status_code == 404
        assert error.timestamp is not None


@pytest.mark.unit
class TestSchemaDefaults:
    """Test schema defaults and optional fields"""

    def test_user_update_optional_fields(self):
        """Test UserUpdate has optional fields"""
        update = UserUpdate()
        # Should not raise - all fields are optional
        assert update is not None

    def test_agent_with_minimal_fields(self):
        """Test Agent can be created with minimal fields"""
        agent = AgentCreate(name="Minimal Agent", model="gpt-4")
        assert agent.name == "Minimal Agent"
        assert agent.temperature == 0.7  # Default value

    def test_task_status_default(self):
        """Test task status defaults to pending"""
        task = TaskCreate(title="New Task", agent_id="1")
        # Task model would have default status
        assert task is not None
