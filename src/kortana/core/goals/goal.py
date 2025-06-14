"""
Core goal data structures for Kor'tana's Goal Framework.
Defines goals that drive autonomous behavior based on Sacred Trinity principles.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class GoalType(Enum):
    """Types of goals that Kor'tana can pursue"""

    DEVELOPMENT = "development"  # Code/feature development goals
    LEARNING = "learning"  # Knowledge acquisition goals
    OPTIMIZATION = "optimization"  # Performance/efficiency improvement goals
    MAINTENANCE = "maintenance"  # System maintenance/health goals
    ASSISTANCE = "assistance"  # User assistance/support goals
    INTEGRATION = "integration"  # System integration goals
    AUTONOMOUS = "autonomous"  # Self-directed goals
    COVENANT = "covenant"  # Sacred Covenant alignment goals


class GoalStatus(Enum):
    """Current status of a goal"""

    PENDING = "pending"  # Goal created but not started
    IN_PROGRESS = "in_progress"  # Goal is being actively worked on
    BLOCKED = "blocked"  # Goal is blocked by dependencies or issues
    NEEDS_REVIEW = "needs_review"  # Goal completed but needs validation
    COMPLETED = "completed"  # Goal successfully completed
    FAILED = "failed"  # Goal could not be achieved
    ABANDONED = "abandoned"  # Goal intentionally discontinued


@dataclass
class Goal:
    """
    Represents a goal that Kor'tana can pursue autonomously.
    Goals are aligned with the Sacred Trinity principles of Wisdom, Compassion, and Truth.
    """

    # Core attributes (non-defaults first)
    type: GoalType
    description: str
    id: UUID = field(default_factory=uuid4)
    status: GoalStatus = field(default=GoalStatus.PENDING)

    # Metadata and tracking
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    created_by: str = "kor_tana"  # Who/what created this goal
    priority: int = 1  # 1-5, higher is more important

    # Sacred Trinity alignment scores (0-1)
    wisdom_score: float = 0.0  # How much this goal promotes wisdom
    compassion_score: float = 0.0  # How much this goal shows compassion
    truth_score: float = 0.0  # How much this goal upholds truth

    # Dependencies and relationships
    parent_goal_id: UUID | None = None  # Parent goal if this is a subgoal
    child_goal_ids: list[UUID] = field(default_factory=list)  # Child/subgoals
    dependent_goal_ids: list[UUID] = field(
        default_factory=list
    )  # Goals that depend on this
    blocks_goal_ids: list[UUID] = field(default_factory=list)  # Goals blocked by this

    # Progress tracking
    progress: float = 0.0  # 0-1 completion progress
    success_criteria: list[str] = field(
        default_factory=list
    )  # How to measure completion
    next_steps: list[str] = field(default_factory=list)  # Planned next actions
    blockers: list[str] = field(default_factory=list)  # Current blockers/issues

    # Extended attributes
    tags: list[str] = field(default_factory=list)  # For categorization/filtering
    metadata: dict[str, Any] = field(
        default_factory=dict
    )  # Flexible storage for extra data
    covenant_approval: bool | None = None  # Whether goal passed covenant check
    covenant_feedback: str | None = None  # Feedback from covenant check

    # Add dynamic priority attribute
    dynamic_priority: float = field(default=0.0)

    def update_status(self, new_status: GoalStatus) -> None:
        """Update goal status with proper timestamp tracking"""
        self.status = new_status
        self.updated_at = datetime.now(UTC)
        if new_status == GoalStatus.COMPLETED:
            self.completed_at = datetime.now(UTC)
            self.progress = 1.0

    def add_child_goal(self, child_id: UUID) -> None:
        """Add a child/subgoal to this goal"""
        if child_id not in self.child_goal_ids:
            self.child_goal_ids.append(child_id)
            self.updated_at = datetime.now(UTC)

    def add_dependent_goal(self, dependent_id: UUID) -> None:
        """Add a goal that depends on this goal"""
        if dependent_id not in self.dependent_goal_ids:
            self.dependent_goal_ids.append(dependent_id)
            self.updated_at = datetime.now(UTC)

    def add_blocked_goal(self, blocked_id: UUID) -> None:
        """Add a goal that this goal blocks"""
        if blocked_id not in self.blocks_goal_ids:
            self.blocks_goal_ids.append(blocked_id)
            self.updated_at = datetime.now(UTC)

    def update_sacred_scores(
        self, wisdom: float, compassion: float, truth: float
    ) -> None:
        """Update Sacred Trinity alignment scores"""
        self.wisdom_score = max(0.0, min(1.0, wisdom))
        self.compassion_score = max(0.0, min(1.0, compassion))
        self.truth_score = max(0.0, min(1.0, truth))
        self.updated_at = datetime.now(UTC)

    def update_progress(self, progress: float) -> None:
        """Update goal progress"""
        self.progress = max(0.0, min(1.0, progress))
        self.updated_at = datetime.now(UTC)

    def add_blocker(self, blocker: str) -> None:
        """Add a blocker/issue preventing goal completion"""
        if blocker not in self.blockers:
            self.blockers.append(blocker)
            self.updated_at = datetime.now(UTC)

    def remove_blocker(self, blocker: str) -> None:
        """Remove a resolved blocker"""
        if blocker in self.blockers:
            self.blockers.remove(blocker)
            self.updated_at = datetime.now(UTC)

    def set_covenant_approval(
        self, approved: bool, feedback: str | None = None
    ) -> None:
        """Record Sacred Covenant approval status and feedback"""
        self.covenant_approval = approved
        self.covenant_feedback = feedback
        self.updated_at = datetime.now(UTC)
