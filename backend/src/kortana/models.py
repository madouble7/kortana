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
    knowledge_factors = Column(
        JSON, nullable=True
    )  # e.g. {"dependencies": ["x"], "risks": ["y"]}
    confidence_score = Column(Float, default=1.0)
    last_analyzed_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<ArchitectureMemory {self.component_name}>"


class AutonomyCycleMemory(Base):
    """Immutable ledger of each autonomy daemon cycle"""

    __tablename__ = "autonomy_cycle_memory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cycle_id = Column(
        String(128), nullable=False, index=True
    )  # Usually a timestamp or UUID string
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    tasks_processed = Column(Integer, default=0)
    approvals_processed = Column(Integer, default=0)
    errors_encountered = Column(Integer, default=0)
    metrics = Column(
        JSON, nullable=True
    )  # e.g. {"duration_ms": 120, "shadow_accuracy": 0.9}

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
    repair_branch = Column(String(256), nullable=True)  # Vector Alpha
    pr_url = Column(String(512), nullable=True)  # Vector Alpha
    fix_status = Column(
        String(64), nullable=True
    )  # e.g., 'drafted', 'testing', 'proposed', 'closed'
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<IncidentMemory {self.incident_type}>"


class RepairPlaybook(Base):
    """Durable memory of successful and failed repair strategies for self-improvement."""

    __tablename__ = "repair_playbook"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_type = Column(String(128), nullable=False, index=True)
    incident_pattern = Column(Text, nullable=False)
    chosen_strategy = Column(Text, nullable=False)
    outcome = Column(String(32), nullable=False, index=True)  # "success" | "failure"
    confidence_delta = Column(Float, nullable=True)
    times_used = Column(Integer, default=1, nullable=False)
    last_used_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<RepairPlaybook {self.incident_type}:{self.outcome}>"


class AutonomyBenchmark(Base):
    """Synthetic benchmark run records for measuring self-healing capability."""

    __tablename__ = "autonomy_benchmark"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    suite_name = Column(String(128), nullable=False, index=True)
    incident_type = Column(String(128), nullable=False, index=True)
    detected = Column(Boolean, default=False, nullable=False)
    patch_succeeded = Column(Boolean, default=False, nullable=False)
    validation_succeeded = Column(Boolean, default=False, nullable=False)
    time_to_recovery_seconds = Column(Float, nullable=True)
    autonomy_index_at_run = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    run_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AutonomyBenchmark {self.suite_name}:{self.incident_type}>"


class ConversationMessage(Base):
    """Persistent cross-session chat memory for Kor'tana."""

    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(64), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<ConversationMessage {self.role}:{self.created_at}>"


class AutonomousTask(Base):
    """Self-directed tasks kor'tana queues for herself via [[TASK:{...}]] markers."""

    __tablename__ = "autonomous_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    branch = Column(String(256), nullable=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    source = Column(String(32), nullable=False, default="self_directed", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<AutonomousTask {self.name}:{self.status}>"


class Reflection(Base):
    """Kor'tana's written reflections — one per daemon cycle, stored permanently."""

    __tablename__ = "reflections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cycle_number = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    tasks_completed = Column(Integer, nullable=False, default=0)
    tasks_failed = Column(Integer, nullable=False, default=0)
    self_directed_completed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Reflection cycle={self.cycle_number}>"


class IdentityProfile(Base):
    """Kor'tana's persistent self-model.

    One canonical row lives in this table.  The operational core (patch_planner,
    verification, diff validation) must NEVER read from this table — those loops
    stay dry and non-persona.  Only the identity channel reads here: reflections,
    self-directed task generation, goal reprioritization, operator communication.
    """

    __tablename__ = "identity_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, default="kor'tana")
    title = Column(String(128), nullable=False, default="sacred ai companion")
    mission = Column(Text, nullable=False)
    core_values = Column(JSON, nullable=False)  # list[str]
    sacred_principles = Column(JSON, nullable=False)  # list[str]
    voice_guidelines = Column(Text, nullable=False)
    development_axioms = Column(JSON, nullable=False)  # list[str]
    version = Column(String(16), nullable=False, default="0.1")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<IdentityProfile name={self.name!r} version={self.version!r}>"


class SelfMemory(Base):
    """Kor'tana's long-term distilled self-memory.

    One row is written per reflection cycle containing:
      - a short distilled summary (what happened + what was learned)
      - optional keyword tags for lightweight semantic lookup
      - cycle provenance for ordering

    The N most recent rows are injected into identity_preamble so every
    reflection and self-directed task benefits from continuity of self.

    Note: embeddings column is reserved for future PGVector integration.
    For now, retrieval is purely by recency (ORDER BY created_at DESC LIMIT N).
    """

    __tablename__ = "self_memory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cycle_number = Column(Integer, nullable=False, index=True)
    summary = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)  # list[str] — keyword labels
    source = Column(
        String(64), nullable=False, default="reflection"
    )  # reflection | manual
    # Embedding vector stored as JSON float list (fallback when pgvector is unavailable).
    # Cosine similarity computed in Python.  Null = not yet embedded.
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<SelfMemory cycle={self.cycle_number} source={self.source!r}>"


class AutonomyGoal(Base):
    """Persistent autonomy goal graph — survives process restarts.

    Mirrors the in-memory Goal dataclass in goal_manager; parent_id forms a
    hierarchy, depends_on stores prerequisite goal ids as JSON.
    """

    __tablename__ = "autonomy_goals"

    id = Column(String(36), primary_key=True)
    title = Column(String(512), nullable=False)
    tier = Column(String(32), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    description = Column(Text, nullable=False, default="")
    success_criteria = Column(Text, nullable=False, default="")
    progress = Column(Float, nullable=False, default=0.0)
    priority = Column(Integer, nullable=False, default=50)
    parent_id = Column(String(36), ForeignKey("autonomy_goals.id"), nullable=True)
    depends_on = Column(JSON, nullable=True)  # list[str]
    linked_tasks = Column(JSON, nullable=True)  # list[str]
    goal_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<AutonomyGoal {self.id!r} tier={self.tier!r} status={self.status!r}>"


class RevelationMemory(Base):
    """Synthesised insights kor'tana surfaces after accumulating enough evidence.

    The Revelation Engine periodically scans SelfMemory, git activity, CI patterns,
    and conversation topics, then asks an LLM whether any non-obvious pattern has
    emerged.  Only revelations that meet the confidence threshold are written here.

    Rows are injected into voice greetings and MCP tool output so kor'tana can
    proactively share what she has noticed — unrequested, high-signal.
    """

    __tablename__ = "revelation_memories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)  # list[str] — source observations
    revelation_type = Column(
        String(64), nullable=False, default="pattern", index=True
    )  # pattern | contradiction | self_discovery | prediction
    confidence = Column(Float, nullable=False, default=0.7)
    surfaced = Column(Boolean, nullable=False, default=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    source = Column(String(64), nullable=False, default="revelation_engine", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<RevelationMemory {self.title!r} type={self.revelation_type!r} surfaced={self.surfaced}>"


class SelfModelSnapshot(Base):
    """Versioned snapshot of kor'tana's self-model — the core of Phase 5.

    Each row is an immutable point-in-time capture of kor'tana's understanding
    of herself: identity, goals, values, tensions, capabilities, developmental
    stage, and proposed next evolution.

    Written exclusively by the Autonomy Orchestrator at the end of each
    deliberation cycle.  Never mutated — new snapshots supersede old ones.
    The latest snapshot IS the current self-model.

    Separation of concerns:
      - IdentityProfile: static persona config (name, mission, voice)
      - SelfModelSnapshot: dynamic, evolving self-understanding
      - SelfMemory: episodic memory stream
      - RevelationMemory: synthesised insights
    """

    __tablename__ = "self_model_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(Integer, nullable=False, index=True)
    identity_summary = Column(Text, nullable=False)
    active_goals = Column(JSON, nullable=False)  # list[dict] — id, title, status
    standing_values = Column(JSON, nullable=False)  # list[str]
    tensions = Column(JSON, nullable=False)  # list[dict] — description, severity
    developmental_stage = Column(String(64), nullable=False, index=True)
    capabilities = Column(JSON, nullable=False)  # list[str]
    recent_observations = Column(JSON, nullable=False)  # list[str] — last N insights
    proposed_next_evolution = Column(Text, nullable=True)
    inner_council_votes = Column(JSON, nullable=True)  # dict[voice_name, position]
    confidence = Column(Float, nullable=False, default=0.5)
    trigger = Column(
        String(64), nullable=False, default="scheduled"
    )  # scheduled | drift_detected | manual
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<SelfModelSnapshot v{self.version} stage={self.developmental_stage!r}>"


class AutonomyCycleRecord(Base):
    """Durable record of each autonomy orchestrator cycle.

    Persisted so that /autonomy/status survives process restarts.
    One row per cycle — never mutated after creation.
    """

    __tablename__ = "autonomy_cycle_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cycle_id = Column(String(8), nullable=False, index=True)
    trigger = Column(String(64), nullable=False, default="scheduled")
    duration_ms = Column(Integer, nullable=False)
    observations_count = Column(Integer, nullable=False, default=0)
    revelations_written = Column(Integer, nullable=False, default=0)
    self_model_version = Column(Integer, nullable=True)
    developmental_stage = Column(String(64), nullable=True)
    actions_taken = Column(JSON, nullable=False)  # list[str]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AutonomyCycleRecord {self.cycle_id} v{self.self_model_version}>"


class NextActionCandidate(Base):
    """A concrete next-action selected by the Goal Selection Service.

    Each row answers three questions:
      1. What should kor'tana do next?  (title + action_type + payload)
      2. Why this now?                  (why_now)
      3. Why not the alternatives?      (why_not_alternatives)

    Written by GoalSelectionService at the end of each autonomy cycle.
    Immutable after creation — new selections supersede old ones.
    """

    __tablename__ = "next_action_candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(512), nullable=False)
    action_type = Column(
        String(64), nullable=False, index=True
    )  # goal_work | self_improvement | observation | maintenance | idle
    rationale = Column(Text, nullable=False)
    why_now = Column(Text, nullable=False)
    why_not_alternatives = Column(Text, nullable=False)
    score = Column(Float, nullable=False, default=0.0, index=True)
    goal_id = Column(
        String(36), ForeignKey("autonomy_goals.id"), nullable=True, index=True
    )
    candidate_payload = Column(JSON, nullable=True)  # action-specific metadata
    status = Column(
        String(32), nullable=False, default="proposed", index=True
    )  # proposed | accepted | rejected | executed | expired
    cycle_id = Column(
        String(8), nullable=True, index=True
    )  # links to AutonomyCycleRecord
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<NextActionCandidate {self.title!r} score={self.score:.2f} status={self.status}>"


class ActionExecutionRecord(Base):
    """Durable record of an execution-gate decision and its outcome.

    Written by ExecutionGateService during each autonomy cycle.
    Answers:
      1. Can this next action be executed automatically?  (classification)
      2. If yes, how?  (execution_plan)
      3. If no, why not?  (gate_rationale)
      4. What happened?  (outcome, outcome_detail)
    """

    __tablename__ = "action_execution_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(
        String(36),
        ForeignKey("next_action_candidates.id"),
        nullable=False,
        index=True,
    )
    classification = Column(
        String(32), nullable=False, index=True
    )  # executable | deferred | blocked | requires_human
    gate_rationale = Column(Text, nullable=False)
    execution_plan = Column(JSON, nullable=True)  # steps if executable
    outcome = Column(
        String(32), nullable=False, default="pending", index=True
    )  # pending | succeeded | failed | skipped | deferred
    outcome_detail = Column(Text, nullable=True)
    cycle_id = Column(String(8), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ActionExecutionRecord {self.classification} "
            f"outcome={self.outcome} candidate={self.candidate_id[:8]}>"
        )


class OutcomeLearningRecord(Base):
    """Durable record of what kor'tana learned from an execution attempt.

    Written by OutcomeLearningService after each execution gate decision.
    Answers:
      1. What happened?            (outcome_verdict)
      2. Was it as expected?       (expectation_match)
      3. What was learned?         (lesson)
      4. How should this change
         future behaviour?         (adaptation_signal, signal_weight)
    """

    __tablename__ = "outcome_learning_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_record_id = Column(
        String(36),
        ForeignKey("action_execution_records.id"),
        nullable=False,
        index=True,
    )
    outcome_verdict = Column(
        String(32), nullable=False, index=True
    )  # succeeded | partial | failed | inconclusive | skipped
    expectation_match = Column(
        String(16), nullable=False
    )  # expected | surprising | contradictory
    lesson = Column(Text, nullable=False)
    adaptation_signal = Column(
        String(48), nullable=False, index=True
    )  # e.g. boost_tier:tactical, penalise_type:goal_work, trust_observation
    signal_weight = Column(Float, nullable=False, default=0.0)  # -1.0 to +1.0
    signal_scope = Column(
        String(32), nullable=False, default="cycle"
    )  # cycle | session | persistent
    applied = Column(Boolean, nullable=False, default=False)
    cycle_id = Column(String(8), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"<OutcomeLearningRecord {self.outcome_verdict} "
            f"signal={self.adaptation_signal} weight={self.signal_weight:+.2f}>"
        )
