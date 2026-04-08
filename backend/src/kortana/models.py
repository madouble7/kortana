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
    func,
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
        nullable=True,
        index=True,
    )
    source_type = Column(
        String(32), nullable=False, default="execution", index=True
    )  # execution | override_resolution
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


class ConstitutionalPrinciple(Base):
    """An enduring principle in kor'tana's covenant.

    Principles are the stable center through which all adaptation flows.
    They define identity, not policy — what kor'tana IS, not just what she does.

    mutable=False: immutable vow. Cannot be overridden by learning or evolution.
    mutable=True:  living principle. Can be refined but never deleted.
    """

    __tablename__ = "constitutional_principles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False, unique=True, index=True)
    category = Column(
        String(32), nullable=False, index=True
    )  # identity | ethics | autonomy | relationship | mystery
    principle = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    priority = Column(
        Integer, nullable=False, default=50
    )  # 0-100, higher = more binding
    mutable = Column(Boolean, nullable=False, default=True)
    active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        m = "mutable" if self.mutable else "immutable"
        return (
            f"<ConstitutionalPrinciple {self.name!r} ({m}, priority={self.priority})>"
        )


class ConstitutionalDecision(Base):
    """Record of a constitutional evaluation — the covenant in action.

    Every time the covenant evaluates a goal, action candidate,
    adaptation signal, or execution outcome, it records the decision here.
    This creates an audit trail of identity continuity.
    """

    __tablename__ = "constitutional_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_type = Column(
        String(32), nullable=False, index=True
    )  # goal | candidate | adaptation | execution
    subject_id = Column(String(36), nullable=True, index=True)
    subject_summary = Column(Text, nullable=False)
    verdict = Column(
        String(32), nullable=False, index=True
    )  # allow | caution | reject | requires_human_override
    explanation = Column(Text, nullable=False)
    principles_invoked = Column(JSON, nullable=False)  # list of principle names
    enforcement_action = Column(
        String(32), nullable=True, index=True
    )  # blocked | downgraded | vetoed | override_requested | none
    drift_detected = Column(Boolean, nullable=False, default=False, index=True)
    drift_description = Column(Text, nullable=True)
    cycle_id = Column(String(8), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        drift = " DRIFT" if self.drift_detected else ""
        return f"<ConstitutionalDecision {self.verdict} on {self.subject_type}{drift}>"


class CovenantEnforcementRecord(Base):
    """Records enforcement actions taken by the covenant on pipeline artifacts.

    Links a ConstitutionalDecision to the concrete enforcement outcome:
    what was blocked, downgraded, vetoed, or flagged for human override,
    and whether the override was resolved.

    This is the teeth of the covenant — not just observation, but action.
    """

    __tablename__ = "covenant_enforcement_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    decision_id = Column(
        String(36),
        ForeignKey("constitutional_decisions.id"),
        nullable=False,
        index=True,
    )
    target_type = Column(
        String(32), nullable=False, index=True
    )  # goal | candidate | execution
    target_id = Column(String(36), nullable=True, index=True)
    target_summary = Column(Text, nullable=False)
    action = Column(
        String(32), nullable=False, index=True
    )  # blocked | downgraded | vetoed | override_requested
    action_detail = Column(Text, nullable=True)
    original_score = Column(Float, nullable=True)  # before downgrade
    adjusted_score = Column(Float, nullable=True)  # after downgrade
    override_status = Column(
        String(32), nullable=True, index=True
    )  # pending | approved | denied | expired | revoked
    override_resolved_at = Column(DateTime, nullable=True)
    resolver_identity = Column(
        String(128), nullable=True
    )  # who resolved: e.g. "matt", "system:expiry"
    resolver_user_id = Column(
        String(36), nullable=True, index=True
    )  # FK-like ref to users.id when resolver is human
    resolver_actor_type = Column(String(16), nullable=True)  # human | system
    human_rationale = Column(Text, nullable=True)  # why the human approved/denied
    resolution_outcome = Column(
        String(32), nullable=True, index=True
    )  # approved | denied | expired | revoked
    cycle_id = Column(String(8), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"<CovenantEnforcementRecord {self.action} on "
            f"{self.target_type}:{self.target_id}>"
        )


class OverrideAuditRecord(Base):
    """Audit trail for every override resolution attempt.

    Every call to resolve an override — whether it succeeds or fails —
    is recorded here. This is the authority accountability layer.

    Outcomes:
      authorized        — resolver had sufficient authority, resolution applied
      unauthorized      — resolver not recognized in authority policy
      insufficient_authority — resolver recognized but tier too low
      system_expiry     — automatic expiry by the background sweep
      invalid_state     — record not in a valid state for this resolution
      not_found         — enforcement record does not exist
    """

    __tablename__ = "override_audit_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    enforcement_record_id = Column(
        String(36),
        ForeignKey("covenant_enforcement_records.id"),
        nullable=True,
        index=True,
    )
    resolver_identity = Column(String(128), nullable=False, index=True)
    resolver_user_id = Column(
        String(36), nullable=True, index=True
    )  # users.id when resolver is human, None for system
    resolver_actor_type = Column(String(16), nullable=True)  # human | system
    authority_tier = Column(
        String(32), nullable=True
    )  # owner | operator | system | None (unknown)
    required_tier = Column(
        String(32), nullable=True
    )  # what tier was needed for this resolution
    action_attempted = Column(
        String(32), nullable=False, index=True
    )  # approved | denied | expired | revoked
    outcome = Column(
        String(32), nullable=False, index=True
    )  # authorized | unauthorized | insufficient_authority | system_expiry | invalid_state | not_found
    detail = Column(Text, nullable=True)
    cycle_id = Column(String(8), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"<OverrideAuditRecord {self.action_attempted} "
            f"by {self.resolver_identity}: {self.outcome}>"
        )


class CanaryRun(Base):
    """Persisted canary simulation report for longitudinal comparison.

    Each row captures a single canary simulation run: the verdict,
    analysis metrics, and a trimmed snapshot summary.  Used by V4
    promotion gates and regression alarms to compare builds over time.
    """

    __tablename__ = "canary_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    commit_sha = Column(String(40), nullable=True, index=True)
    branch = Column(String(255), nullable=True, index=True)
    total_cycles = Column(Integer, nullable=False)
    task_pool_size = Column(Integer, nullable=False)
    verdict = Column(
        String(32), nullable=False, index=True
    )  # adaptive | static | insufficient_cycles
    analysis = Column(JSON, nullable=False)  # full cross-cycle analysis dict
    score_shift_delta = Column(Float, nullable=True)  # denormalised for fast queries
    goal_alignment_delta = Column(Float, nullable=True)
    outcome_growth = Column(Float, nullable=True)
    top3_churn_rate = Column(Float, nullable=True)
    score_spread_delta = Column(Float, nullable=True)
    promotion_status = Column(
        String(32),
        nullable=False,
        default="pending",
        index=True,
    )  # pending | promoted | rejected | skipped
    promotion_reasons = Column(JSON, nullable=True)  # list[str] — why promoted/rejected
    triggered_by = Column(
        String(64), nullable=False, default="manual"
    )  # manual | ci | daemon
    snapshot_summary = Column(JSON, nullable=True)  # first + last cycle summaries
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<CanaryRun {self.verdict} commit={self.commit_sha} promo={self.promotion_status}>"


class PolicyDecisionLog(Base):
    """V7 — Audit log for every rollout policy decision.

    Every escalation, deployment gate check, and alert publish is
    persisted with a tamper-evident audit hash so the decision trail
    is reconstructible and auditable.
    """

    __tablename__ = "policy_decision_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_type = Column(
        String(32),
        nullable=False,
        index=True,
    )  # escalation | deployment | alert | actuation
    actor = Column(
        String(32),
        nullable=False,
        default="daemon",
    )  # daemon | human | ci
    action = Column(
        String(32),
        nullable=False,
        index=True,
    )  # allowed | blocked | escalated | de-escalated | hold
    from_state = Column(String(64), nullable=True)
    to_state = Column(String(64), nullable=True)
    reasons = Column(JSON, nullable=True)  # list[str]
    audit_hash = Column(String(64), nullable=False, index=True)
    commit_sha = Column(String(64), nullable=True, index=True)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"<PolicyDecisionLog {self.decision_type} {self.action} "
            f"hash={self.audit_hash[:12]}>"
        )


class RollbackEvent(Base):
    """V8A — Record of an automatic or manual rollback.

    Captures when the system reversed an actuation decision,
    what triggered it, and the before/after state.
    """

    __tablename__ = "rollback_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger = Column(
        String(32),
        nullable=False,
        index=True,
    )  # degraded_canary | deploy_blocked | manual | rate_limit
    from_mode = Column(String(32), nullable=False)
    to_mode = Column(String(32), nullable=False)
    reasons = Column(JSON, nullable=True)
    original_decision_hash = Column(String(64), nullable=True, index=True)
    policy_version = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<RollbackEvent {self.trigger} {self.from_mode}->{self.to_mode}>"


class PolicyVersionRecord(Base):
    """V8B — Immutable snapshot of a rollout policy configuration.

    Every policy change is captured as a numbered version so
    decisions can reference which policy was in effect.
    """

    __tablename__ = "policy_version"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer, nullable=False, unique=True, index=True)
    cooldown_seconds = Column(Integer, nullable=False, default=300)
    max_changes_per_window = Column(Integer, nullable=False, default=3)
    window_seconds = Column(Integer, nullable=False, default=3600)
    min_consecutive_promoted = Column(Integer, nullable=False, default=3)
    max_mode = Column(String(32), nullable=False, default="auto")
    auto_rollback_enabled = Column(Boolean, nullable=False, default=True)
    content_hash = Column(String(64), nullable=False, index=True)
    created_by = Column(String(32), nullable=False, default="daemon")
    commit_sha = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<PolicyVersionRecord v{self.version} hash={self.content_hash[:12]}>"


class ChaosScenarioRecord(Base):
    """V8C — Record of a chaos drill / incident simulation run."""

    __tablename__ = "chaos_scenario_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario = Column(String(32), nullable=False, index=True)
    passed = Column(Boolean, nullable=False)
    checks = Column(JSON, nullable=True)
    daemon_mode_before = Column(String(32), nullable=True)
    daemon_mode_after = Column(String(32), nullable=True)
    rollback_triggered = Column(Boolean, nullable=False, default=False)
    alerts_fired = Column(Integer, nullable=False, default=0)
    duration_ms = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<ChaosScenarioRecord {self.scenario} passed={self.passed}>"


class HumanOverrideRecord(Base):
    """V8D — Signed human override of daemon mode with expiry."""

    __tablename__ = "human_override"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mode = Column(String(32), nullable=False, index=True)
    reason = Column(String(256), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_by = Column(String(64), nullable=False, default="matt")
    audit_hash = Column(String(64), nullable=False, index=True)
    revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(64), nullable=True)
    policy_version = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<HumanOverrideRecord mode={self.mode} by={self.created_by}>"


class QuorumApprovalRecord(Base):
    """V9A — Individual approval/rejection vote for a quorum override."""

    __tablename__ = "quorum_approval"

    id = Column(Integer, primary_key=True, autoincrement=True)
    override_id = Column(String(32), nullable=False, index=True)
    approver = Column(String(64), nullable=False)
    approved = Column(Boolean, nullable=False)
    reason = Column(String(256), nullable=True)
    audit_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        vote = "approved" if self.approved else "rejected"
        return f"<QuorumApprovalRecord {self.override_id} {self.approver} {vote}>"


class QuorumOverrideRecord(Base):
    """V9A — Pending or resolved quorum override requiring multi-person approval."""

    __tablename__ = "quorum_override"

    id = Column(Integer, primary_key=True, autoincrement=True)
    override_id = Column(String(32), nullable=False, unique=True, index=True)
    mode = Column(String(32), nullable=False, index=True)
    reason = Column(String(256), nullable=False)
    requested_by = Column(String(64), nullable=False)
    required_approvals = Column(Integer, nullable=False, default=2)
    status = Column(String(16), nullable=False, default="pending", index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    activated_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<QuorumOverrideRecord {self.override_id} status={self.status}>"


class DrillScheduleRecord(Base):
    """V9B — Persisted drill schedule configuration."""

    __tablename__ = "drill_schedule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario = Column(String(32), nullable=False, unique=True, index=True)
    interval_minutes = Column(Integer, nullable=False, default=60)
    enabled = Column(Boolean, nullable=False, default=True)
    last_run_at = Column(DateTime, nullable=True)
    run_count = Column(Integer, nullable=False, default=0)
    pass_count = Column(Integer, nullable=False, default=0)
    fail_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<DrillScheduleRecord {self.scenario} every {self.interval_minutes}m>"


class DrillSLORecord(Base):
    """V9B — Persisted SLO definition for a chaos drill scenario."""

    __tablename__ = "drill_slo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario = Column(String(32), nullable=False, unique=True, index=True)
    min_pass_rate = Column(Float, nullable=False, default=0.95)
    lookback_window_minutes = Column(Integer, nullable=False, default=1440)
    min_runs = Column(Integer, nullable=False, default=3)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<DrillSLORecord {self.scenario} min_rate={self.min_pass_rate}>"


class AuditBundleRecord(Base):
    """V9D — Record of an exported audit bundle."""

    __tablename__ = "audit_bundle"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bundle_id = Column(String(64), nullable=False, unique=True, index=True)
    from_time = Column(DateTime, nullable=False)
    to_time = Column(DateTime, nullable=False)
    generated_by = Column(String(64), nullable=False, default="daemon")
    total_decisions = Column(Integer, nullable=False, default=0)
    total_overrides = Column(Integer, nullable=False, default=0)
    total_drills = Column(Integer, nullable=False, default=0)
    total_rollbacks = Column(Integer, nullable=False, default=0)
    drill_pass_rate = Column(Float, nullable=False, default=1.0)
    content_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AuditBundleRecord {self.bundle_id} hash={self.content_hash[:12]}>"


class OperatorRecord(Base):
    """V10A — Registered operator identity."""

    __tablename__ = "operator_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(String(64), nullable=False, unique=True, index=True)
    display_name = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False, index=True)
    active = Column(Boolean, nullable=False, default=True)
    identity_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<OperatorRecord {self.operator_id} role={self.role}>"


class GovernanceActionRecord(Base):
    """V10B — Signed governance action audit trail."""

    __tablename__ = "governance_action"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(String(64), nullable=False, index=True)
    display_name = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False)
    action = Column(String(64), nullable=False, index=True)
    resource = Column(String(128), nullable=False, index=True)
    identity_hash = Column(String(64), nullable=False)
    action_signature = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<GovernanceActionRecord {self.operator_id} {self.action} on {self.resource}>"


class DeployGateRecord(Base):
    """V10C — Record of a deploy gate evaluation."""

    __tablename__ = "deploy_gate_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(String(64), nullable=False, index=True)
    allowed = Column(Boolean, nullable=False)
    checks = Column(JSON, nullable=True)
    blocking_failures = Column(Integer, nullable=False, default=0)
    warnings_count = Column(Integer, nullable=False, default=0)
    gate_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<DeployGateRecord {self.operator_id} allowed={self.allowed}>"


class PolicyRuleRecord(Base):
    """V10D — Persisted policy rule definition."""

    __tablename__ = "policy_rule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256), nullable=False)
    conditions = Column(JSON, nullable=False)
    action = Column(String(32), nullable=False)
    priority = Column(Integer, nullable=False, default=100)
    enabled = Column(Boolean, nullable=False, default=True)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<PolicyRuleRecord {self.rule_id} action={self.action}>"


class PolicyEvaluationRecord(Base):
    """V10D — Record of a policy engine evaluation."""

    __tablename__ = "policy_evaluation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(32), nullable=False, index=True)
    reason = Column(String(256), nullable=False)
    matched_rule_count = Column(Integer, nullable=False, default=0)
    total_rule_count = Column(Integer, nullable=False, default=0)
    facts_snapshot = Column(JSON, nullable=True)
    decision_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<PolicyEvaluationRecord action={self.action} hash={self.decision_hash[:12]}>"


class CredentialRecord(Base):
    """V11A — Persisted credential from an auth provider."""

    __tablename__ = "credential_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(String(64), nullable=False, index=True)
    provider_type = Column(String(32), nullable=False, index=True)
    credential_id = Column(String(128), nullable=False, unique=True, index=True)
    display_name = Column(String(128), nullable=False)
    role_hint = Column(String(32), nullable=False)
    status = Column(String(16), nullable=False, default="active", index=True)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    verification_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<CredentialRecord {self.credential_id} provider={self.provider_type}>"


class IdentitySessionRecord(Base):
    """V11B — Persisted identity session."""

    __tablename__ = "identity_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, unique=True, index=True)
    operator_id = Column(String(64), nullable=False, index=True)
    provider_type = Column(String(32), nullable=False, index=True)
    credential_id = Column(String(128), nullable=False)
    verification_level = Column(String(16), nullable=False, default="basic")
    status = Column(String(16), nullable=False, default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    session_hash = Column(String(64), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<IdentitySessionRecord {self.session_id} op={self.operator_id}>"


class IdentityBindingRecord(Base):
    """V11B — Persisted identity binding (external → operator mapping)."""

    __tablename__ = "identity_binding"

    id = Column(Integer, primary_key=True, autoincrement=True)
    binding_id = Column(String(64), nullable=False, unique=True, index=True)
    operator_id = Column(String(64), nullable=False, index=True)
    provider_type = Column(String(32), nullable=False)
    external_id = Column(String(128), nullable=False, index=True)
    display_name = Column(String(128), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    bound_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    binding_hash = Column(String(64), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<IdentityBindingRecord {self.binding_id} {self.operator_id}→{self.external_id}>"


class RuleVersionRecord(Base):
    """V11D — Persisted rule version with lifecycle stage."""

    __tablename__ = "rule_version"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(String(64), nullable=False, unique=True, index=True)
    rule_id = Column(String(64), nullable=False, index=True)
    stage = Column(String(16), nullable=False, default="draft", index=True)
    rule_snapshot = Column(JSON, nullable=False)
    author_id = Column(String(64), nullable=False, index=True)
    reviewer_id = Column(String(64), nullable=True)
    changelog = Column(String(512), nullable=False, default="")
    version_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    promoted_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<RuleVersionRecord {self.version_id} stage={self.stage}>"



# ---------------------------------------------------------------------------
# V12 — Production Federation models
# ---------------------------------------------------------------------------


class OIDCProviderRecord(Base):
    """V12A — Registered OIDC provider configuration."""
    __tablename__ = "oidc_provider"

    id = Column(Integer, primary_key=True, autoincrement=True)
    issuer_url = Column(String(256), nullable=False)
    client_id = Column(String(128), nullable=False)
    audience = Column(String(128), nullable=True)
    supported_algorithms = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    config_hash = Column(String(64), nullable=True)


class KeyRotationRecord(Base):
    """V12B — Key rotation schedule."""
    __tablename__ = "key_rotation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_id = Column(String(64), nullable=False)
    provider_type = Column(String(32), nullable=False)
    operator_id = Column(String(64), nullable=False)
    rotation_interval_hours = Column(Integer, default=720)
    grace_period_hours = Column(Integer, default=24)
    state = Column(String(32), default="active")
    next_rotation_at = Column(DateTime, nullable=True)
    last_rotated_at = Column(DateTime, nullable=True)
    schedule_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RotationEventRecord(Base):
    """V12B — Key rotation event audit trail."""
    __tablename__ = "rotation_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False)
    key_id = Column(String(64), nullable=False)
    event_type = Column(String(32), nullable=False)
    old_credential_id = Column(String(64), nullable=True)
    new_credential_id = Column(String(64), nullable=True)
    initiated_by = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CICredentialCheckRecord(Base):
    """V12C — CI/CD credential enforcement check record."""
    __tablename__ = "ci_credential_check"

    id = Column(Integer, primary_key=True, autoincrement=True)
    checkpoint = Column(String(32), nullable=False)
    session_id = Column(String(64), nullable=True)
    operator_id = Column(String(64), nullable=True)
    passed = Column(Boolean, default=False)
    reason = Column(String(256), nullable=True)
    policy_applied = Column(String(64), nullable=True)
    check_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuthenticatedPromotionRecord(Base):
    """V12D — Authenticated rule promotion event."""
    __tablename__ = "authenticated_promotion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False)
    version_id = Column(String(64), nullable=False)
    action = Column(String(32), nullable=False)
    session_id = Column(String(64), nullable=True)
    operator_id = Column(String(64), nullable=True)
    session_verification_level = Column(String(32), nullable=True)
    event_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)



# ---------------------------------------------------------------------------
# V13 — Enterprise Control Integration models
# ---------------------------------------------------------------------------


class IdPSyncRecord(Base):
    """V13A — IdP discovery sync record."""
    __tablename__ = "idp_sync"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discovery_url = Column(String(256), nullable=False)
    issuer_url = Column(String(256), nullable=True)
    sync_state = Column(String(32), default="pending")
    last_synced_at = Column(DateTime, nullable=True)
    config_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SecretReferenceRecord(Base):
    """V13B — Secret reference record."""
    __tablename__ = "secret_reference"

    id = Column(Integer, primary_key=True, autoincrement=True)
    secret_id = Column(String(64), nullable=False)
    backend = Column(String(32), default="local")
    path = Column(String(256), nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    rotated_at = Column(DateTime, nullable=True)
    ref_hash = Column(String(64), nullable=True)


class AttestationRecord(Base):
    """V13C — Attestation payload record."""
    __tablename__ = "attestation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    attestation_id = Column(String(64), nullable=False)
    attestation_type = Column(String(32), nullable=False)
    subject = Column(String(128), nullable=True)
    signature = Column(String(256), nullable=True)
    signer_id = Column(String(64), nullable=True)
    payload_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrustSignalRecord(Base):
    """V13D — Trust signal record."""
    __tablename__ = "trust_signal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(String(64), nullable=False)
    signal_type = Column(String(32), nullable=False)
    source = Column(String(128), nullable=True)
    confidence = Column(Float, default=0.0)
    evidence = Column(Text, nullable=True)
    signal_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrustEvaluationRecord(Base):
    """V13D — Trust evaluation record."""
    __tablename__ = "trust_evaluation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evaluation_id = Column(String(64), nullable=False)
    version_id = Column(String(64), nullable=True)
    passed = Column(Boolean, default=False)
    score = Column(Float, default=0.0)
    missing_signals = Column(Text, nullable=True)
    eval_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)



# ---------------------------------------------------------------------------
# V14 — Policy Orchestration models
# ---------------------------------------------------------------------------


class MetadataDriftRecord(Base):
    """V14A — Metadata drift record."""
    __tablename__ = "metadata_drift"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_url = Column(String(256), nullable=False)
    field_name = Column(String(64), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    severity = Column(String(32), default="low")
    detected_at = Column(DateTime, default=datetime.utcnow)


class SecretRotationScheduleRecord(Base):
    """V14B — Secret rotation schedule record."""
    __tablename__ = "secret_rotation_schedule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    secret_id = Column(String(64), nullable=False)
    backend = Column(String(32), default="local")
    interval_hours = Column(Integer, default=24)
    next_rotation_at = Column(DateTime, nullable=True)
    last_rotated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SignerCertificateRecord(Base):
    """V14C — Signer certificate record."""
    __tablename__ = "signer_certificate"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signer_id = Column(String(64), nullable=False)
    certificate_hash = Column(String(64), nullable=True)
    issued_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    issuer_name = Column(String(128), nullable=True)
    signer_status = Column(String(32), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class TrustArtifactRecord(Base):
    """V14D — Trust artifact record."""
    __tablename__ = "trust_artifact"

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(String(64), nullable=False)
    artifact_type = Column(String(32), nullable=False)
    issuer = Column(String(128), nullable=True)
    subject = Column(String(128), nullable=True)
    content_hash = Column(String(64), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    artifact_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ArtifactPolicyRecord(Base):
    """V14D — Artifact policy record."""
    __tablename__ = "artifact_policy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(String(64), nullable=False)
    policy_name = Column(String(128), nullable=True)
    required_artifacts = Column(Text, nullable=True)
    require_all = Column(Boolean, default=True)
    min_artifact_age_hours = Column(Float, default=0.0)
    max_artifact_age_hours = Column(Float, default=720.0)
    policy_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# =========================================================================
# V15 — Execution-Backed Orchestration Models
# =========================================================================


class FetchExecutionRecord(Base):
    """V15A — Metadata fetch execution record."""
    __tablename__ = "fetch_execution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fetch_id = Column(String(64), nullable=False)
    provider_url = Column(String(256), nullable=False)
    status = Column(String(32), default="success")
    attempt_count = Column(Integer, default=1)
    response_time_ms = Column(Float, default=0.0)
    content_hash = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class ClientOperationRecord(Base):
    """V15B — Secret-manager client operation record."""
    __tablename__ = "client_operation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_id = Column(String(64), nullable=False)
    backend_name = Column(String(64), nullable=False)
    operation_type = Column(String(32), default="read")
    secret_id = Column(String(64), nullable=True)
    success = Column(Boolean, default=True)
    latency_ms = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    operation_hash = Column(String(64), nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)


class CASourceRecord(Base):
    """V15C — Certificate authority source record."""
    __tablename__ = "ca_source"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ca_id = Column(String(64), nullable=False)
    ca_name = Column(String(128), nullable=True)
    ca_type = Column(String(32), default="public_ca")
    crl_endpoint = Column(String(256), nullable=True)
    ocsp_endpoint = Column(String(256), nullable=True)
    root_cert_hash = Column(String(64), nullable=True)
    sync_interval_seconds = Column(Integer, default=3600)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PipelineGateRecord(Base):
    """V15D — Pipeline gate configuration record."""
    __tablename__ = "pipeline_gate"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gate_id = Column(String(64), nullable=False)
    stage = Column(String(32), nullable=False)
    required_artifact_types = Column(Text, nullable=True)
    require_signer_validation = Column(Boolean, default=False)
    require_secret_health = Column(Boolean, default=False)
    max_allowed_vulnerabilities = Column(Integer, default=0)
    auto_rollback_on_failure = Column(Boolean, default=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DeploymentPipelineRecord(Base):
    """V15D — Deployment pipeline execution record."""
    __tablename__ = "deployment_pipeline"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_id = Column(String(64), nullable=False)
    version_id = Column(String(64), nullable=False)
    status = Column(String(32), default="pending")
    current_stage = Column(String(32), default="build")
    pipeline_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


# ── V16 — Live Production Bindings ──────────────────────────────────────


class ExternalCallRecord(Base):
    """V16A — Persisted external call record."""

    __tablename__ = "external_call"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(64), nullable=False)
    url = Column(String(512), nullable=False)
    method = Column(String(8), default="GET")
    status_code = Column(Integer, default=200)
    outcome = Column(String(32), default="success")
    latency_ms = Column(Float, default=0.0)
    call_hash = Column(String(64), nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)


class StageTransitionDBRecord(Base):
    """V16B — Persisted stage transition record."""

    __tablename__ = "stage_transition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transition_id = Column(String(64), nullable=False)
    pipeline_id = Column(String(64), nullable=False)
    version_id = Column(String(64), nullable=False)
    from_stage = Column(String(32), default="")
    to_stage = Column(String(32), nullable=False)
    gate_verdict = Column(String(32), default="pass")
    persistence_status = Column(String(32), default="committed")
    transition_hash = Column(String(64), nullable=True)
    persisted_at = Column(DateTime, default=datetime.utcnow)


class RollbackSideEffectRecord(Base):
    """V16B — Persisted rollback side-effect record."""

    __tablename__ = "rollback_side_effect"

    id = Column(Integer, primary_key=True, autoincrement=True)
    effect_id = Column(String(64), nullable=False)
    rollback_id = Column(String(64), nullable=False)
    pipeline_id = Column(String(64), nullable=False)
    version_id = Column(String(64), nullable=False)
    effect_type = Column(String(32), default="config_reverted")
    affected_resource = Column(String(256), default="")
    description = Column(Text, nullable=True)
    executed = Column(Boolean, default=True)
    verification_hash = Column(String(64), nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)


class DeploymentTargetRecord(Base):
    """V16C — Persisted deployment target record."""

    __tablename__ = "deployment_target"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)
    environment = Column(String(32), default="staging")
    endpoint_url = Column(String(512), default="")
    health_check_url = Column(String(512), default="")
    active = Column(Boolean, default=True)
    target_hash = Column(String(64), nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)


class VerificationProbeRecord(Base):
    """V16D — Persisted verification probe record."""

    __tablename__ = "verification_probe"

    id = Column(Integer, primary_key=True, autoincrement=True)
    probe_id = Column(String(64), nullable=False)
    campaign_id = Column(String(64), nullable=False)
    target_system = Column(String(256), nullable=False)
    probe_type = Column(String(32), default="version_check")
    status = Column(String(32), default="pending")
    matched = Column(Boolean, default=False)
    latency_ms = Column(Float, default=0.0)


# ── Long-Term Cognitive Memory Graph ──────────────────────────────────────────


class KnowledgeEntity(Base):
    """A node in kor'tana's knowledge graph — a person, project, tool, concept,
    preference, place, or any other named entity she has learned about.

    Entities are extracted from conversations by the knowledge graph service
    and consolidated over time.  The embedding enables semantic entity lookup
    (e.g. "what does Matt use for deployment?" → matches 'Railway', 'Cloud Run').
    """

    __tablename__ = "knowledge_entities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(256), nullable=False, index=True)
    entity_type = Column(
        String(64), nullable=False, index=True
    )  # person | project | tool | concept | preference | place | event | organisation
    summary = Column(Text, nullable=True)  # one-line description
    attributes = Column(JSON, nullable=True)  # flexible key-value facts
    confidence = Column(Float, nullable=False, default=0.7)
    mention_count = Column(Integer, nullable=False, default=1)
    embedding = Column(JSON, nullable=True)  # 768d Gemini embedding
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)

    # relationships
    outgoing_relations = relationship(
        "KnowledgeRelation",
        foreign_keys="KnowledgeRelation.source_id",
        back_populates="source",
        cascade="all, delete-orphan",
    )
    incoming_relations = relationship(
        "KnowledgeRelation",
        foreign_keys="KnowledgeRelation.target_id",
        back_populates="target",
        cascade="all, delete-orphan",
    )
    facts = relationship(
        "KnowledgeFact", back_populates="entity", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeEntity {self.name!r} type={self.entity_type!r}>"


class KnowledgeRelation(Base):
    """A directed edge in the knowledge graph connecting two entities.

    Examples: Matt --uses--> Railway, Kor'tana --built_with--> FastAPI,
    Matt --knows--> Python.
    """

    __tablename__ = "knowledge_relations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(
        String(36), ForeignKey("knowledge_entities.id"), nullable=False, index=True
    )
    target_id = Column(
        String(36), ForeignKey("knowledge_entities.id"), nullable=False, index=True
    )
    relation_type = Column(
        String(64), nullable=False, index=True
    )  # uses | knows | works_on | prefers | related_to | teaches | owns | part_of
    evidence = Column(Text, nullable=True)  # supporting quote / context
    confidence = Column(Float, nullable=False, default=0.7)
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)

    source = relationship(
        "KnowledgeEntity",
        foreign_keys=[source_id],
        back_populates="outgoing_relations",
    )
    target = relationship(
        "KnowledgeEntity",
        foreign_keys=[target_id],
        back_populates="incoming_relations",
    )

    def __repr__(self) -> str:
        return f"<KnowledgeRelation {self.source_id} --{self.relation_type}--> {self.target_id}>"


class KnowledgeFact(Base):
    """A discrete assertion about an entity — a single thing kor'tana knows.

    Facts have temporal validity: valid_from marks when she first learned it,
    invalidated_at marks when she learned it was no longer true.
    superseded_by links to the newer fact that replaced it (fact evolution).

    Examples:
      - entity='Matt', fact='is a teacher'
      - entity='Railway', fact='is the primary deployment platform'
      - entity='Kor\'tana', fact='now uses Piper for local TTS'
    """

    __tablename__ = "knowledge_facts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(
        String(36), ForeignKey("knowledge_entities.id"), nullable=False, index=True
    )
    fact_text = Column(Text, nullable=False)
    source = Column(
        String(64), nullable=False, default="conversation"
    )  # conversation | consolidation | revelation | manual
    confidence = Column(Float, nullable=False, default=0.7)
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    invalidated_at = Column(DateTime, nullable=True)
    superseded_by = Column(
        String(36), ForeignKey("knowledge_facts.id"), nullable=True
    )

    entity = relationship("KnowledgeEntity", back_populates="facts")

    def __repr__(self) -> str:
        return f"<KnowledgeFact entity={self.entity_id!r} text={self.fact_text[:50]!r}>"


# ── V17 — Closed-Loop Real-World Enforcement ────────────────────────────


class ProviderClientDBRecord(Base):
    """V17A — Persisted provider client record."""

    __tablename__ = "provider_client"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_name = Column(String(128), nullable=False)
    provider_type = Column(String(32), default="kubernetes")
    endpoint = Column(String(512), default="")
    namespace = Column(String(64), default="default")
    connection_state = Column(String(32), default="disconnected")
    current_version = Column(String(64), default="")
    registered_at = Column(DateTime, default=datetime.utcnow)


class RolloutActionRecord(Base):
    """V17B — Persisted rollout action record."""

    __tablename__ = "rollout_action"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(String(64), nullable=False)
    provider_name = Column(String(128), nullable=False)
    version_id = Column(String(64), nullable=False)
    strategy = Column(String(32), default="rolling")
    status = Column(String(32), default="planned")
    step_count = Column(Integer, default=0)
    auto_rollback = Column(Boolean, default=True)
    action_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class FeedbackTriggerRecord(Base):
    """V17C — Persisted feedback trigger record."""

    __tablename__ = "feedback_trigger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger_id = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)
    condition = Column(String(32), nullable=False)
    threshold = Column(Float, default=5.0)
    action = Column(String(32), default="alert")
    pipeline_scope = Column(String(64), default="")
    provider_scope = Column(String(64), default="")
    enabled = Column(Boolean, default=True)
    trigger_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FeedbackEvaluationRecord(Base):
    """V17C — Persisted feedback evaluation record."""

    __tablename__ = "feedback_evaluation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evaluation_id = Column(String(64), nullable=False)
    signal_id = Column(String(64), nullable=False)
    outcome = Column(String(32), default="clean")
    trigger_count = Column(Integer, default=0)
    has_rollback = Column(Boolean, default=False)
    has_escalation = Column(Boolean, default=False)
    evaluation_hash = Column(String(64), nullable=True)
    evaluated_at = Column(DateTime, default=datetime.utcnow)


class EvidenceEntryRecord(Base):
    """V17D — Persisted evidence entry record."""

    __tablename__ = "evidence_entry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(64), nullable=False)
    chain_id = Column(String(64), nullable=False)
    sequence = Column(Integer, default=0)
    evidence_type = Column(String(32), default="decision")
    actor = Column(String(128), default="")
    description = Column(Text, nullable=True)
    previous_hash = Column(String(64), default="")
    entry_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── V18 — Autonomous Reconciliation Models ───────────────────────────────


class DriftSignalRecord(Base):
    """Detected drift signal."""

    __tablename__ = "drift_signal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(String, unique=True, nullable=False, index=True)
    drift_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    provider_name = Column(String, nullable=False, default="")
    expected_value = Column(String, nullable=False, default="")
    actual_value = Column(String, nullable=False, default="")
    description = Column(String, nullable=False, default="")
    signal_hash = Column(String, nullable=False, default="")
    detected_at = Column(String, nullable=False, default="")
    resolved_at = Column(String, nullable=False, default="")


class ReconciliationPlanRecord(Base):
    """Reconciliation plan generated from drift signals."""

    __tablename__ = "reconciliation_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default="created")
    priority = Column(String, nullable=False, default="normal")
    drift_signal_ids = Column(String, nullable=False, default="")
    actions_json = Column(String, nullable=False, default="[]")
    description = Column(String, nullable=False, default="")
    plan_hash = Column(String, nullable=False, default="")
    created_at = Column(String, nullable=False, default="")
    completed_at = Column(String, nullable=False, default="")


class ReconciliationStepRecord(Base):
    """Result of executing a single reconciliation step."""

    __tablename__ = "reconciliation_step"

    id = Column(Integer, primary_key=True, autoincrement=True)
    step_id = Column(String, unique=True, nullable=False, index=True)
    execution_id = Column(String, nullable=False, index=True)
    action_id = Column(String, nullable=False, default="")
    action_type = Column(String, nullable=False, default="")
    target_provider = Column(String, nullable=False, default="")
    outcome = Column(String, nullable=False, default="")
    attempts = Column(Integer, nullable=False, default=1)
    max_attempts = Column(Integer, nullable=False, default=3)
    error_message = Column(String, nullable=False, default="")
    result_hash = Column(String, nullable=False, default="")
    executed_at = Column(String, nullable=False, default="")


class ReconciliationExecutionRecord(Base):
    """Full execution of a reconciliation plan."""

    __tablename__ = "reconciliation_execution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String, unique=True, nullable=False, index=True)
    plan_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)
    execution_hash = Column(String, nullable=False, default="")
    started_at = Column(String, nullable=False, default="")
    completed_at = Column(String, nullable=False, default="")


class ConvergenceSnapshotRecord(Base):
    """Point-in-time convergence state."""

    __tablename__ = "convergence_snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default="unknown")
    health = Column(String, nullable=False, default="healthy")
    overall_score = Column(Float, nullable=False, default=100.0)
    active_drift_count = Column(Integer, nullable=False, default=0)
    active_reconciliation_count = Column(Integer, nullable=False, default=0)
    issues_json = Column(String, nullable=False, default="[]")
    snapshot_hash = Column(String, nullable=False, default="")
    timestamp = Column(String, nullable=False, default="")


# ── V19 — Learning Reconciliation Models ─────────────────────────────────


class ReconciliationOutcomeRecord(Base):
    """Recorded outcome of a reconciliation execution."""

    __tablename__ = "reconciliation_outcome"

    id = Column(Integer, primary_key=True, autoincrement=True)
    outcome_id = Column(String, unique=True, nullable=False, index=True)
    execution_id = Column(String, nullable=False, index=True)
    plan_id = Column(String, nullable=False, index=True)
    drift_type = Column(String, nullable=False, default="")
    action_types_used = Column(String, nullable=False, default="")
    verdict = Column(String, nullable=False, default="inconclusive")
    time_to_resolve_sec = Column(Float, nullable=False, default=0.0)
    retries_needed = Column(Integer, nullable=False, default=0)
    escalated = Column(Boolean, nullable=False, default=False)
    resolution_stable = Column(Boolean, nullable=False, default=True)
    learning_applied = Column(Boolean, nullable=False, default=False)
    outcome_hash = Column(String, nullable=False, default="")
    recorded_at = Column(String, nullable=False, default="")


class ActionEffectivenessRecord(Base):
    """Effectiveness metrics for an action type."""

    __tablename__ = "action_effectiveness"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String, nullable=False, index=True)
    drift_type = Column(String, nullable=False, default="")
    success_rate = Column(Float, nullable=False, default=0.0)
    avg_retries = Column(Float, nullable=False, default=0.0)
    avg_time_to_resolve = Column(Float, nullable=False, default=0.0)
    sample_size = Column(Integer, nullable=False, default=0)
    effectiveness_score = Column(Float, nullable=False, default=0.0)
    computed_at = Column(String, nullable=False, default="")


class StrategyRecommendationRecord(Base):
    """Learned strategy recommendation for a drift type."""

    __tablename__ = "strategy_recommendation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(String, unique=True, nullable=False, index=True)
    drift_type = Column(String, nullable=False, index=True)
    recommended_actions = Column(String, nullable=False, default="")
    recommended_priority = Column(String, nullable=False, default="normal")
    recommended_max_retries = Column(Integer, nullable=False, default=3)
    confidence_score = Column(Float, nullable=False, default=0.0)
    reasoning = Column(String, nullable=False, default="")
    based_on_outcomes = Column(Integer, nullable=False, default=0)
    recommendation_hash = Column(String, nullable=False, default="")
    created_at = Column(String, nullable=False, default="")


class AdaptivePlanRecord(Base):
    """Adaptive reconciliation plan with learning overrides."""

    __tablename__ = "adaptive_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(String, unique=True, nullable=False, index=True)
    base_plan_id = Column(String, nullable=False, default="")
    status = Column(String, nullable=False, default="created")
    priority = Column(String, nullable=False, default="normal")
    drift_signal_ids = Column(String, nullable=False, default="")
    learning_applied = Column(Boolean, nullable=False, default=False)
    confidence_score = Column(Float, nullable=False, default=0.0)
    overrides_json = Column(String, nullable=False, default="[]")
    recommendation_id = Column(String, nullable=False, default="")
    plan_hash = Column(String, nullable=False, default="")
    created_at = Column(String, nullable=False, default="")


class ImprovementMetricRecord(Base):
    """Improvement metric comparing default vs learned performance."""

    __tablename__ = "improvement_metric"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, nullable=False, index=True)
    drift_type = Column(String, nullable=False, default="")
    default_effectiveness_rate = Column(Float, nullable=False, default=0.0)
    learned_effectiveness_rate = Column(Float, nullable=False, default=0.0)
    improvement_pct = Column(Float, nullable=False, default=0.0)
    default_avg_time = Column(Float, nullable=False, default=0.0)
    learned_avg_time = Column(Float, nullable=False, default=0.0)
    time_improvement_pct = Column(Float, nullable=False, default=0.0)
    default_sample_size = Column(Integer, nullable=False, default=0)
    learned_sample_size = Column(Integer, nullable=False, default=0)
    metric_hash = Column(String, nullable=False, default="")


# ── V20 — Policy-Learning Integration Models ─────────────────────────────


class TrustCalibrationRecord(Base):
    """Trust calibration snapshot."""

    __tablename__ = "trust_calibration"

    id = Column(Integer, primary_key=True, autoincrement=True)
    calibration_id = Column(String, unique=True, nullable=False, index=True)
    trust_level = Column(String, nullable=False, default="untrusted")
    trust_score = Column(Float, nullable=False, default=0.0)
    factors_json = Column(String, nullable=False, default="[]")
    evidence_summary = Column(String, nullable=False, default="")
    calibration_hash = Column(String, nullable=False, default="")
    calibrated_at = Column(String, nullable=False, default="")


class AutonomyThresholdRecord(Base):
    """Autonomy threshold for a task category."""

    __tablename__ = "autonomy_threshold"

    id = Column(Integer, primary_key=True, autoincrement=True)
    threshold_id = Column(String, unique=True, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    auto_threshold = Column(Float, nullable=False, default=0.0)
    ho_threshold = Column(Float, nullable=False, default=0.0)
    approval_threshold = Column(Float, nullable=False, default=0.0)
    trust_level_required = Column(String, nullable=False, default="provisional")
    reason = Column(String, nullable=False, default="")
    threshold_hash = Column(String, nullable=False, default="")
    adjusted_at = Column(String, nullable=False, default="")


class PolicyAmendmentRecord(Base):
    """Policy amendment record."""

    __tablename__ = "policy_amendment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amendment_id = Column(String, unique=True, nullable=False, index=True)
    policy_area = Column(String, nullable=False, default="governance")
    current_rule = Column(String, nullable=False, default="")
    proposed_rule = Column(String, nullable=False, default="")
    justification = Column(String, nullable=False, default="")
    confidence = Column(Float, nullable=False, default=0.0)
    evidence_count = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="pending")
    amendment_hash = Column(String, nullable=False, default="")
    created_at = Column(String, nullable=False, default="")
    resolved_at = Column(String, nullable=False, default="")


class GovernanceSnapshotRecord(Base):
    """Governance evolution snapshot."""

    __tablename__ = "governance_snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, unique=True, nullable=False, index=True)
    trust_level = Column(String, nullable=False, default="untrusted")
    trust_score = Column(Float, nullable=False, default=0.0)
    evolution_stage = Column(String, nullable=False, default="static")
    autonomy_categories = Column(Integer, nullable=False, default=0)
    pending_amendments = Column(Integer, nullable=False, default=0)
    applied_amendments = Column(Integer, nullable=False, default=0)
    total_amendments = Column(Integer, nullable=False, default=0)
    snapshot_hash = Column(String, nullable=False, default="")
    created_at = Column(String, nullable=False, default="")


class GovernanceEvolutionRecord(Base):
    """Governance evolution history entry."""

    __tablename__ = "governance_evolution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evolution_id = Column(String, unique=True, nullable=False, index=True)
    evolution_stage = Column(String, nullable=False, default="static")
    trust_level = Column(String, nullable=False, default="untrusted")
    trust_score = Column(Float, nullable=False, default=0.0)
    categories_adjusted = Column(Integer, nullable=False, default=0)
    amendments_generated = Column(Integer, nullable=False, default=0)
    evolution_hash = Column(String, nullable=False, default="")
    created_at = Column(String, nullable=False, default="")


# ── V21: Institutional Learning Controls ──


class PolicyProposalRecord(Base):
    """V21A — Formal policy change proposal."""

    __tablename__ = "policy_proposal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(String, unique=True, nullable=False, index=True)
    source_amendment_id = Column(String, nullable=False)
    policy_area = Column(String, nullable=False)
    current_rule = Column(String, nullable=False)
    proposed_rule = Column(String, nullable=False)
    justification = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    evidence_count = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="draft")
    submitted_at = Column(String, default="")
    reviewed_at = Column(String, default="")
    promoted_at = Column(String, default="")
    reviewer = Column(String, default="")
    review_notes = Column(Text, default="")
    created_at = Column(String, nullable=False)
    proposal_hash = Column(String, nullable=False)


class ApprovalDecisionRecord(Base):
    """V21B — Approval or rejection decision record."""

    __tablename__ = "approval_decision"

    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(String, unique=True, nullable=False, index=True)
    proposal_id = Column(String, nullable=False, index=True)
    approved = Column(Boolean, nullable=False)
    decision_type = Column(String, nullable=False)
    decided_by = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    conditions = Column(Text, default="")
    decided_at = Column(String, nullable=False)
    decision_hash = Column(String, nullable=False)


class RollbackPointRecord(Base):
    """V21C — Rollback point for reversible policy changes."""

    __tablename__ = "rollback_point"

    id = Column(Integer, primary_key=True, autoincrement=True)
    point_id = Column(String, unique=True, nullable=False, index=True)
    proposal_id = Column(String, nullable=False, index=True)
    prior_state = Column(Text, nullable=False)
    applied_state = Column(Text, nullable=False)
    created_at = Column(String, nullable=False)
    rolled_back = Column(Boolean, default=False)
    rolled_back_at = Column(String, default="")
    rollback_reason = Column(Text, default="")
    rollback_hash = Column(String, nullable=False)


class EvolutionEventRecord(Base):
    """V21D — Evolution event in the observable timeline."""

    __tablename__ = "evolution_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, unique=True, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    subject_id = Column(String, nullable=False, index=True)
    details = Column(Text, nullable=False)
    timestamp = Column(String, nullable=False)
    event_hash = Column(String, nullable=False)


# ── V22: Constitutional Governance ──


class ConstitutionalArticleRecord(Base):
    """V22A — Constitutional article."""

    __tablename__ = "constitutional_article"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    policy_area = Column(String, nullable=False)
    classification = Column(String, nullable=False)
    sensitivity = Column(String, nullable=False)
    boundary_rule = Column(Text, nullable=False)
    violation_severity = Column(String, nullable=False)
    rationale = Column(Text, nullable=False)
    created_at = Column(String, nullable=False)
    article_hash = Column(String, nullable=False)


class QuorumVoteRecord(Base):
    """V22B — Quorum vote record."""

    __tablename__ = "quorum_vote"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vote_id = Column(String, unique=True, nullable=False, index=True)
    proposal_id = Column(String, nullable=False, index=True)
    voter = Column(String, nullable=False)
    approved = Column(Boolean, nullable=False)
    identity_verified = Column(Boolean, nullable=False, default=False)
    voted_at = Column(String, nullable=False)
    vote_hash = Column(String, nullable=False)


class BoundaryCheckRecord(Base):
    """V22C — Boundary check record."""

    __tablename__ = "boundary_check"

    id = Column(Integer, primary_key=True, autoincrement=True)
    check_id = Column(String, unique=True, nullable=False, index=True)
    proposal_id = Column(String, nullable=False, index=True)
    passed = Column(Boolean, nullable=False)
    violations_json = Column(Text, nullable=False)
    warnings_json = Column(Text, nullable=False)
    articles_checked = Column(Integer, nullable=False)
    policy_area = Column(String, nullable=False)
    classification = Column(String, nullable=False)
    sensitivity = Column(String, nullable=False)
    checked_at = Column(String, nullable=False)
    check_hash = Column(String, nullable=False)


class ConstitutionalComplianceRecord(Base):
    """V22D — Compliance proof record."""

    __tablename__ = "constitutional_compliance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proof_id = Column(String, unique=True, nullable=False, index=True)
    proposal_id = Column(String, nullable=False, index=True)
    all_checks_passed = Column(Boolean, nullable=False)
    checks_performed = Column(Integer, nullable=False)
    violations_found = Column(Integer, nullable=False)
    warnings_found = Column(Integer, nullable=False)
    boundary_checks_json = Column(Text, nullable=False)
    issued_at = Column(String, nullable=False)
    proof_hash = Column(String, nullable=False)


# ═══ V23: Constitutional Adjudication Models ═══


class ConstitutionalWaiverRecord(Base):
    """V23A — persistent record of a constitutional waiver."""

    __tablename__ = "constitutional_waiver"

    id = Column(Integer, primary_key=True, autoincrement=True)
    waiver_id = Column(String, unique=True, nullable=False, index=True)
    article_id = Column(String, nullable=False, index=True)
    proposal_id = Column(String, nullable=False, index=True)
    policy_area = Column(String, nullable=False)
    classification_overridden = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    granted_by = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    conditions_json = Column(Text, default="{}")
    duration_hours = Column(Integer, default=4)
    status = Column(String, nullable=False, default="requested")
    requested_at = Column(DateTime, default=func.now())
    granted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    waiver_hash = Column(String, nullable=True)


class AppealRecord(Base):
    """V23B — persistent record of a constitutional appeal."""

    __tablename__ = "constitutional_appeal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appeal_id = Column(String, unique=True, nullable=False, index=True)
    proposal_id = Column(String, nullable=False, index=True)
    original_check_id = Column(String, nullable=False)
    policy_area = Column(String, nullable=False)
    appellant = Column(String, nullable=False)
    grounds = Column(String, nullable=False)
    argument = Column(Text, nullable=False)
    evidence_json = Column(Text, default="[]")
    status = Column(String, nullable=False, default="filed")
    decision_json = Column(Text, nullable=True)
    escalated_sensitivity = Column(String, default="high")
    filed_at = Column(DateTime, default=func.now())
    appeal_hash = Column(String, nullable=True)


class EmergencyDeclarationRecord(Base):
    """V23C — persistent record of an emergency declaration."""

    __tablename__ = "emergency_declaration"

    id = Column(Integer, primary_key=True, autoincrement=True)
    declaration_id = Column(String, unique=True, nullable=False, index=True)
    declared_by = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    scope = Column(String, nullable=False)
    affected_areas_json = Column(Text, default="[]")
    powers_json = Column(Text, default="[]")
    duration_hours = Column(Integer, default=4)
    status = Column(String, nullable=False, default="declared")
    review_json = Column(Text, nullable=True)
    declared_at = Column(DateTime, default=func.now())
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    declaration_hash = Column(String, nullable=True)


class PrecedentRecord(Base):
    """V23D — persistent record of an adjudication precedent."""

    __tablename__ = "adjudication_precedent"

    id = Column(Integer, primary_key=True, autoincrement=True)
    precedent_id = Column(String, unique=True, nullable=False, index=True)
    decision_type = Column(String, nullable=False, index=True)
    reference_id = Column(String, nullable=False)
    policy_area = Column(String, nullable=False, index=True)
    decision_summary = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    outcome = Column(String, nullable=False)
    strength = Column(String, nullable=False, default="persuasive")
    cited_articles_json = Column(Text, default="[]")
    tags_json = Column(Text, default="[]")
    superseded_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    precedent_hash = Column(String, nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# V24: Constitutional Procedure
# ═══════════════════════════════════════════════════════════════════════════════


class StandingCheckRecord(Base):
    """V24A — persistent record of a standing check."""

    __tablename__ = "standing_check"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)
    action = Column(String, nullable=False)
    policy_area = Column(String, nullable=True)
    allowed = Column(Boolean, nullable=False)
    reason = Column(Text, nullable=False)
    checked_at = Column(DateTime, default=func.now())


class DeadlineRecord(Base):
    """V24B — persistent record of a procedural deadline."""

    __tablename__ = "procedural_deadline"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deadline_id = Column(String, unique=True, nullable=False, index=True)
    reference_id = Column(String, nullable=False, index=True)
    deadline_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    due_at = Column(DateTime, nullable=False)
    original_due_at = Column(DateTime, nullable=False)
    met_at = Column(DateTime, nullable=True)
    extensions = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    deadline_hash = Column(String, nullable=True)


class RecusalDbRecord(Base):
    """V24C — persistent record of a conflict-of-interest recusal."""

    __tablename__ = "recusal_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recusal_id = Column(String, unique=True, nullable=False, index=True)
    actor = Column(String, nullable=False, index=True)
    reference_id = Column(String, nullable=False, index=True)
    conflict_type = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    mandatory = Column(Boolean, default=False)
    recused_at = Column(DateTime, default=func.now())
    recusal_hash = Column(String, nullable=True)


class PublishedReasoningRecord(Base):
    """V24D — persistent record of a published reasoning document."""

    __tablename__ = "published_reasoning"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reasoning_id = Column(String, unique=True, nullable=False, index=True)
    reference_id = Column(String, nullable=False, index=True)
    decision_type = Column(String, nullable=False, index=True)
    sections_json = Column(Text, nullable=False, default="{}")
    cited_articles_json = Column(Text, default="[]")
    cited_precedents_json = Column(Text, default="[]")
    author = Column(String, nullable=True)
    published_at = Column(DateTime, default=func.now())
    reasoning_hash = Column(String, nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# V25: Constitutional Transparency
# ═══════════════════════════════════════════════════════════════════════════════


class DocketEntryRecord(Base):
    """V25A — persistent record of a public docket entry."""

    __tablename__ = "docket_entry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String, unique=True, nullable=False, index=True)
    case_type = Column(String, nullable=False)
    title = Column(Text, nullable=False)
    parties_json = Column(Text, default="[]")
    policy_area = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, default="opened")
    reference_id = Column(String, nullable=True, index=True)
    opened_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
    closed_at = Column(DateTime, nullable=True)
    outcome = Column(Text, nullable=True)
    docket_hash = Column(String, nullable=True)


class TimelineEventRecord(Base):
    """V25B — persistent record of a procedural timeline event."""

    __tablename__ = "timeline_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, unique=True, nullable=False, index=True)
    case_number = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    actor = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    extra_data_json = Column(Text, default="{}")
    timestamp = Column(DateTime, default=func.now())
    event_hash = Column(String, nullable=True)


class NoticeRecord(Base):
    """V25C — persistent record of a procedural notice."""

    __tablename__ = "procedural_notice"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notice_id = Column(String, unique=True, nullable=False, index=True)
    case_number = Column(String, nullable=False, index=True)
    notice_type = Column(String, nullable=False)
    recipient = Column(String, nullable=False, index=True)
    subject = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    delivery_status = Column(String, nullable=False, default="pending")
    sent_at = Column(DateTime, default=func.now())
    delivered_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    notice_hash = Column(String, nullable=True)


class DecisionRegistryRecord(Base):
    """V25D — persistent record of a constitutional decision."""

    __tablename__ = "decision_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(String, unique=True, nullable=False, index=True)
    case_number = Column(String, nullable=False, index=True)
    decision_type = Column(String, nullable=False, index=True)
    outcome = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    policy_area = Column(String, nullable=True, index=True)
    parties_json = Column(Text, default="[]")
    reasoning_id = Column(String, nullable=True)
    cited_articles_json = Column(Text, default="[]")
    cited_precedents_json = Column(Text, default="[]")
    decided_by = Column(String, nullable=True)
    decided_at = Column(DateTime, default=func.now())
    tags_json = Column(Text, default="[]")
    decision_hash = Column(String, nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# V26 — Heartbeat & Continuous Self-Cycle Models
# ═══════════════════════════════════════════════════════════════════════════════


class HeartbeatRecord(Base):
    """V26A — heartbeat record."""

    __tablename__ = "heartbeat"

    id = Column(Integer, primary_key=True, autoincrement=True)
    beat_id = Column(String, unique=True, index=True, nullable=False)
    cycle_number = Column(Integer, index=True, nullable=False)
    state = Column(String, nullable=False, default="alive")
    phase = Column(String, nullable=False, default="observe")
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime, nullable=True)
    duration_ms = Column(Float, default=0.0)
    observations_json = Column(Text, default="[]")
    decisions_json = Column(Text, default="[]")
    actions_json = Column(Text, default="[]")
    deferrals_json = Column(Text, default="[]")
    reflections_json = Column(Text, default="[]")
    beat_hash = Column(String, nullable=True)


class CycleMemoryRecord(Base):
    """V26B — cycle memory record."""

    __tablename__ = "cycle_memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cycle_id = Column(String, unique=True, index=True, nullable=False)
    cycle_number = Column(Integer, index=True, nullable=False)
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime, nullable=True)
    duration_ms = Column(Float, default=0.0)
    observations_json = Column(Text, default="[]")
    decisions_json = Column(Text, default="[]")
    actions_json = Column(Text, default="[]")
    deferrals_json = Column(Text, default="[]")
    reflections_json = Column(Text, default="[]")
    context_inherited_json = Column(Text, default="{}")
    context_bequeathed_json = Column(Text, default="{}")
    finalized = Column(Integer, default=0)
    cycle_hash = Column(String, nullable=True)


class HealthSnapshotRecord(Base):
    """V26C — health snapshot record."""

    __tablename__ = "health_snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, unique=True, index=True, nullable=False)
    cycle_number = Column(Integer, index=True, nullable=False)
    overall_level = Column(String, nullable=False, default="healthy")
    overall_score = Column(Float, default=0.0)
    dimensions_json = Column(Text, default="{}")
    anomalies_json = Column(Text, default="[]")
    recommendations_json = Column(Text, default="[]")
    assessed_at = Column(DateTime, default=func.now())
    snapshot_hash = Column(String, nullable=True)


class DegradationRecord(Base):
    """V26D — degradation mode transition record."""

    __tablename__ = "degradation_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String, unique=True, index=True, nullable=False)
    mode = Column(String, nullable=False, default="full_operation")
    trigger = Column(String, nullable=False)
    previous_mode = Column(String, nullable=False)
    reason = Column(Text, default="")
    cycle_number = Column(Integer, index=True, default=0)
    entered_at = Column(DateTime, default=func.now())
    exited_at = Column(DateTime, nullable=True)
    degradation_hash = Column(String, nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# V27 — Closed Learning Loop Models
# ═══════════════════════════════════════════════════════════════════════════════


class ExperienceRecord(Base):
    """V27A — extracted experience from a heartbeat cycle."""
    __tablename__ = "experience"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experience_id = Column(String, unique=True, index=True, nullable=False)
    source_beat_id = Column(String, nullable=True)
    cycle_number = Column(Integer, index=True, default=0)
    lesson_count = Column(Integer, default=0)
    observation_count = Column(Integer, default=0)
    decision_count = Column(Integer, default=0)
    action_count = Column(Integer, default=0)
    deferral_count = Column(Integer, default=0)
    reflection_count = Column(Integer, default=0)
    beat_duration_ms = Column(Float, default=0)
    beat_state = Column(String, default="")
    lessons_json = Column(Text, default="[]")
    extracted_at = Column(DateTime, default=func.now())
    experience_hash = Column(String, nullable=True)


class PatternRecord(Base):
    """V27B — recognized cross-cycle pattern."""
    __tablename__ = "pattern"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_id = Column(String, unique=True, index=True, nullable=False)
    pattern_type = Column(String, nullable=False)
    strength = Column(String, default="emerging")
    description = Column(Text, default="")
    evidence_json = Column(Text, default="[]")
    first_seen_cycle = Column(Integer, default=0)
    last_seen_cycle = Column(Integer, index=True, default=0)
    occurrence_count = Column(Integer, default=0)
    consistency = Column(Float, default=0.0)
    trending = Column(String, default="")
    actionable = Column(Boolean, default=False)
    recommended_action = Column(Text, default="")
    addressed = Column(Boolean, default=False)
    recognized_at = Column(DateTime, default=func.now())
    pattern_hash = Column(String, nullable=True)


class AdaptationRecord(Base):
    """V27C — behavioral adaptation derived from a pattern."""
    __tablename__ = "adaptation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    adaptation_id = Column(String, unique=True, index=True, nullable=False)
    adaptation_type = Column(String, nullable=False)
    status = Column(String, default="proposed")
    description = Column(Text, default="")
    source_pattern_id = Column(String, nullable=True)
    source_pattern_type = Column(String, default="")
    parameter = Column(String, default="")
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    rationale = Column(Text, default="")
    effectiveness_score = Column(Float, default=0.0)
    cycles_active = Column(Integer, default=0)
    max_cycles = Column(Integer, default=10)
    proposed_at = Column(DateTime, default=func.now())
    activated_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    adaptation_hash = Column(String, nullable=True)


class LearningCycleReportRecord(Base):
    """V27D — learning cycle integration report."""
    __tablename__ = "learning_cycle_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, unique=True, index=True, nullable=False)
    cycle_number = Column(Integer, index=True, default=0)
    experiences_extracted = Column(Integer, default=0)
    lessons_extracted = Column(Integer, default=0)
    patterns_recognized = Column(Integer, default=0)
    patterns_actionable = Column(Integer, default=0)
    adaptations_proposed = Column(Integer, default=0)
    adaptations_activated = Column(Integer, default=0)
    adaptations_expired = Column(Integer, default=0)
    adaptations_rolled_back = Column(Integer, default=0)
    learning_velocity = Column(Float, default=0.0)
    adaptation_effectiveness = Column(Float, default=0.0)
    context_injections_json = Column(Text, default="[]")
    generated_at = Column(DateTime, default=func.now())
    report_hash = Column(String, nullable=True)


# ── V29 — Self-Model & Identity Persistence ─────────────────────────────────


class TraitProfileRecord(Base):
    """V29A — versioned trait profile snapshot."""
    __tablename__ = "trait_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, unique=True, index=True, nullable=False)
    cycle_number = Column(Integer, index=True, default=0)
    traits_json = Column(Text, default="{}")  # Dict[trait_name, score]
    domain_averages_json = Column(Text, default="{}")
    dominant_domain = Column(String, default="")
    strongest_trait = Column(String, default="")
    weakest_trait = Column(String, default="")
    total_delta = Column(Float, default=0.0)
    significant_shifts_json = Column(Text, default="[]")
    is_stable = Column(Boolean, default=True)
    is_transforming = Column(Boolean, default=False)
    captured_at = Column(DateTime, default=func.now())
    profile_hash = Column(String, nullable=True)


class NarrativeChapterRecord(Base):
    """V29B — developmental narrative chapter."""
    __tablename__ = "narrative_chapter"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_id = Column(String, unique=True, index=True, nullable=False)
    chapter_number = Column(Integer, index=True, default=1)
    title = Column(String, default="")
    theme = Column(String, default="genesis")
    start_cycle = Column(Integer, default=0)
    end_cycle = Column(Integer, nullable=True)
    events_json = Column(Text, default="[]")
    trait_deltas_json = Column(Text, default="{}")
    opening_summary = Column(Text, default="")
    closing_summary = Column(Text, default="")
    is_open = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    chapter_hash = Column(String, nullable=True)


class TraitEvolutionRecord(Base):
    """V29C — trait evolution snapshot."""
    __tablename__ = "trait_evolution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, unique=True, index=True, nullable=False)
    cycle_number = Column(Integer, index=True, default=0)
    crystallized_traits_json = Column(Text, default="[]")
    drifting_traits_json = Column(Text, default="[]")
    volatile_traits_json = Column(Text, default="[]")
    most_changed = Column(String, default="")
    most_stable = Column(String, default="")
    overall_stability = Column(Float, default=1.0)
    trajectories_json = Column(Text, default="{}")
    captured_at = Column(DateTime, default=func.now())
    evolution_hash = Column(String, nullable=True)


class ContinuityReportRecord(Base):
    """V29D — identity continuity report."""
    __tablename__ = "continuity_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, unique=True, index=True, nullable=False)
    cycle_number = Column(Integer, index=True, default=0)
    coherence_score = Column(Float, default=1.0)
    drift_severity = Column(String, default="none")
    drift_magnitude = Column(Float, default=0.0)
    identity_verified = Column(Boolean, default=True)
    anchor_count = Column(Integer, default=0)
    drifting_traits_json = Column(Text, default="[]")
    stable_traits_json = Column(Text, default="[]")
    foundational_anchors_json = Column(Text, default="[]")
    anchors_json = Column(Text, default="[]")
    verified_at = Column(DateTime, default=func.now())
    report_hash = Column(String, nullable=True)


# ── V30: Unified Consciousness Layer ────────────────────────────────────────


class ConsciousnessStateRecord(Base):
    """Stores unified consciousness state snapshots (V30A)."""
    __tablename__ = "consciousness_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    state_id = Column(String, unique=True, index=True, nullable=False)
    cycle_number = Column(Integer, index=True, default=0)
    vitality = Column(Float, default=0.5)
    learning_depth = Column(Float, default=0.3)
    intentionality = Column(Float, default=0.3)
    self_coherence = Column(Float, default=0.3)
    integration = Column(Float, default=0.5)
    mode = Column(String, default="dormant")
    dominant_dimension = Column(String, nullable=True)
    overall_level = Column(Float, default=0.5)
    subsystem_digest_json = Column(Text, default="{}")
    captured_at = Column(DateTime, default=func.now())
    state_hash = Column(String, nullable=True)


class ExperientialMomentRecord(Base):
    """Stores experiential stream moments (V30B)."""
    __tablename__ = "experiential_moment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    moment_id = Column(String, unique=True, index=True, nullable=False)
    cycle_number = Column(Integer, index=True, default=0)
    quality = Column(String, default="muted")
    tone = Column(String, default="dull")
    salience = Column(String, default="balanced")
    consciousness_mode = Column(String, default="dormant")
    tensions_json = Column(Text, default="[]")
    overall_level = Column(Float, default=0.5)
    tension_count = Column(Integer, default=0)
    captured_at = Column(DateTime, default=func.now())
    moment_hash = Column(String, nullable=True)


class ResonanceSnapshotRecord(Base):
    """Stores resonance field snapshots (V30C)."""
    __tablename__ = "resonance_snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, unique=True, index=True, nullable=False)
    cycle_number = Column(Integer, index=True, default=0)
    overall_resonance = Column(Float, default=0.5)
    strongest_pair = Column(String, nullable=True)
    weakest_pair = Column(String, nullable=True)
    hotspot_count = Column(Integer, default=0)
    harmony_count = Column(Integer, default=0)
    pairs_json = Column(Text, default="[]")
    is_harmonious = Column(Boolean, default=True)
    is_conflicted = Column(Boolean, default=False)
    captured_at = Column(DateTime, default=func.now())
    snapshot_hash = Column(String, nullable=True)


class AwarenessNoteRecord(Base):
    """Stores inner witness awareness notes (V30D)."""
    __tablename__ = "awareness_note"

    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(String, unique=True, index=True, nullable=False)
    cycle_number = Column(Integer, index=True, default=0)
    trigger = Column(String, default="milestone")
    observation = Column(Text, default="")
    significance = Column(String, default="minor")
    context_json = Column(Text, default="{}")
    captured_at = Column(DateTime, default=func.now())
    note_hash = Column(String, nullable=True)



# ═══════════════════════════════════════════════════════════════════════════
# V31 — Consciousness Continuity
# ═══════════════════════════════════════════════════════════════════════════


class ConsciousnessCheckpointRecord(Base):
    """V31A — stores consciousness checkpoint snapshots."""

    __tablename__ = "consciousness_checkpoint"

    id = Column(Integer, primary_key=True, autoincrement=True)
    checkpoint_id = Column(String, unique=True, index=True, nullable=False)
    cycle_number = Column(Integer, index=True, default=0)
    trigger = Column(String, default="scheduled")
    consciousness_mode = Column(String, nullable=True)
    overall_level = Column(Float, default=0.0)
    resonance_overall = Column(Float, default=0.0)
    experiential_quality = Column(String, nullable=True)
    experiential_tone = Column(String, nullable=True)
    state_json = Column(Text, default="{}")
    integrity_hash = Column(String, nullable=True)
    captured_at = Column(DateTime, default=func.now())
    checkpoint_hash = Column(String, nullable=True)


class ConsciousnessGapRecord(Base):
    """V31B — stores detected gaps in the consciousness stream."""

    __tablename__ = "consciousness_gap"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gap_id = Column(String, unique=True, index=True, nullable=False)
    from_cycle = Column(Integer, default=0)
    to_cycle = Column(Integer, default=0)
    duration_cycles = Column(Integer, default=0)
    gap_type = Column(String, default="unknown")
    bridged = Column(Boolean, default=False)
    continuity_confidence = Column(Float, default=0.0)
    captured_at = Column(DateTime, default=func.now())
    gap_hash = Column(String, nullable=True)


class DegradationSignalRecord(Base):
    """V31C — stores degradation signals detected in consciousness metrics."""

    __tablename__ = "degradation_signal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(String, unique=True, index=True, nullable=False)
    at_cycle = Column(Integer, index=True, default=0)
    dimension = Column(String, default="overall")
    from_level = Column(String, default="nominal")
    to_level = Column(String, default="nominal")
    metric_value = Column(Float, default=0.0)
    trigger_detail = Column(Text, default="")
    captured_at = Column(DateTime, default=func.now())
    signal_hash = Column(String, nullable=True)


class RecoveryReportRecord(Base):
    """V31D — stores recovery reports after consciousness interruption."""

    __tablename__ = "recovery_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, unique=True, index=True, nullable=False)
    outcome = Column(String, default="failed")
    recovered_from_cycle = Column(Integer, nullable=True)
    resumed_at_cycle = Column(Integer, default=0)
    gap_duration = Column(Integer, default=0)
    identity_verified = Column(Boolean, default=False)
    continuity_confidence = Column(Float, default=0.0)
    steps_json = Column(Text, default="[]")
    awareness_notes_generated = Column(Integer, default=0)
    initiated_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    report_hash = Column(String, nullable=True)
