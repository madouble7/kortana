"""Database models for Kor'tana Backend"""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """User account model"""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    agents = relationship("Agent", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class APIKey(Base):
    """User API keys for programmatic access"""

    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<APIKey {self.name}>"


class Agent(Base):
    """Autonomous agents"""

    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True)
    model = Column(String(64), nullable=False)  # gpt-4, claude-3, gemini-pro, etc.
    system_prompt = Column(Text, nullable=False)
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="agents")
    executions = relationship(
        "AgentExecution", back_populates="agent", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Agent {self.name}>"


class AgentExecution(Base):
    """Agent execution history"""

    __tablename__ = "agent_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    input_prompt = Column(Text, nullable=False)
    output = Column(Text, nullable=True)
    status = Column(String(32), nullable=False)  # pending, running, completed, failed
    error = Column(Text, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    agent = relationship("Agent", back_populates="executions")

    def __repr__(self) -> str:
        return f"<AgentExecution {self.id}>"


class Memory(Base):
    """Agent memory storage"""

    __tablename__ = "memories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    memory_type = Column(String(64), nullable=False)  # short_term, long_term, episodic
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # Vector embedding
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accessed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Memory {self.memory_type}>"


class Task(Base):
    """Autonomous tasks/goals"""

    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=True, index=True)
    parent_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    classification = Column(
        String(32), nullable=True, default="auto"
    )  # auto, ho, approval
    status = Column(
        String(32), nullable=False, default="pending"
    )  # pending, running, completed, failed, waiting_for_ho
    priority = Column(Integer, default=5, nullable=False)  # 1-10
    command = Column(Text, nullable=True)
    ho_scaffold = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    metadata_json = Column(
        "metadata", JSON, nullable=True
    )  # 'metadata' is reserved in some SQL implementations
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subtasks = relationship("Task", backref="parent", remote_side=[id])

    def __repr__(self) -> str:
        return f"<Task {self.title}>"


class GitHubTask(Base):
    """GitHub issue-to-autonomous-task mapping"""

    __tablename__ = "github_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    github_issue_number = Column(Integer, nullable=False, index=True)
    github_repo = Column(String(255), nullable=False)  # owner/repo format
    github_pr_number = Column(Integer, nullable=True, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(
        String(32), nullable=False, default="pending", index=True
    )  # pending, analyzing, planning, executing, pr_created, completed, failed
    classification = Column(
        String(32), nullable=True, default="auto", index=True
    )  # auto, ho, approval
    priority = Column(String(16), default="medium")  # low, medium, high
    analysis = Column(Text, nullable=True)  # Gemini analysis
    plan = Column(Text, nullable=True)  # Step-by-step execution plan
    ho_scaffold = Column(Text, nullable=True)
    branch_name = Column(String(255), nullable=True, unique=True)
    commit_sha = Column(String(40), nullable=True)  # Commit SHA on branch

    @property
    def branch(self) -> str | None:
        return self.branch_name  # type: ignore[return-value]

    @branch.setter
    def branch(self, value: str | None) -> None:
        self.branch_name = value  # type: ignore[assignment]

    code_changes = Column(JSON, nullable=True)
    validation_report = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    error_count = Column(Integer, default=0, nullable=False)  # Track retry attempts
    max_retries = Column(Integer, default=3, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    estimated_effort = Column(String(64), nullable=True)  # e.g., "2 hours", "1 day"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    analyzed_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Shadow execution diagnostic capture
    sandbox_result = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<GitHubTask #{self.github_issue_number}>"


class OperatorDirective(Base):
    """Persistent operator guidance for always-on autonomy."""

    __tablename__ = "operator_directives"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(64), nullable=False, default="user", index=True)
    directive_type = Column(String(32), nullable=False, default="comment", index=True)
    status = Column(String(32), nullable=False, default="active", index=True)
    priority = Column(Integer, default=50, nullable=False)
    content = Column(Text, nullable=False)
    scope = Column(String(64), nullable=False, default="global")
    directive_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<OperatorDirective {self.directive_type}:{self.status}>"


class TaskApproval(Base):
    """Approval decisions for autonomous GitHub tasks."""

    __tablename__ = "task_approvals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    github_task_id = Column(
        String(36), ForeignKey("github_tasks.id"), nullable=False, index=True
    )
    status = Column(
        String(32), nullable=False, default="pending", index=True
    )  # pending, auto_approved, approved, rejected
    approval_mode = Column(String(32), nullable=False, default="self-aware")
    review_required = Column(Boolean, nullable=False, default=False)
    reviewer = Column(String(64), nullable=True)
    github_comment_id = Column(String(64), nullable=True)
    github_comment_url = Column(String(512), nullable=True)
    last_processed_github_comment_id = Column(String(64), nullable=True)
    last_processed_github_comment_url = Column(String(512), nullable=True)
    last_github_delivery_id = Column(String(128), nullable=True)
    rationale = Column(Text, nullable=True)
    decision_factors = Column(JSON, nullable=True)
    risk_score = Column(Integer, nullable=False, default=0)
    risk_level = Column(String(16), nullable=False, default="low")
    confidence = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    task = relationship("GitHubTask")

    def __repr__(self) -> str:
        return f"<TaskApproval {self.github_task_id}:{self.status}>"


class AuditLog(Base):
    """Audit trail for compliance and debugging"""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(128), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(36), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action}>"


class ArchitectureMemory(Base):
    """Persistent understanding of repository structure, domains, and rules"""
    __tablename__ = "architecture_memory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    component_name = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=False)
    knowledge_factors = Column(JSON, nullable=True) # e.g. {"dependencies": ["x"], "risks": ["y"]}
    confidence_score = Column(Float, default=1.0)
    last_analyzed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ArchitectureMemory {self.component_name}>"


class AutonomyCycleMemory(Base):
    """Immutable ledger of each autonomy daemon cycle"""
    __tablename__ = "autonomy_cycle_memory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cycle_id = Column(String(128), nullable=False, index=True) # Usually a timestamp or UUID string
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    tasks_processed = Column(Integer, default=0)
    approvals_processed = Column(Integer, default=0)
    errors_encountered = Column(Integer, default=0)
    metrics = Column(JSON, nullable=True) # e.g. {"duration_ms": 120, "shadow_accuracy": 0.9}

    def __repr__(self) -> str:
        return f"<AutonomyCycleMemory {self.cycle_id}>"


class IncidentMemory(Base):
    """Records of system failures, panics, and self-healing attempts"""
    __tablename__ = "incident_memory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_type = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    resolution_strategy = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<IncidentMemory {self.incident_type}>"
