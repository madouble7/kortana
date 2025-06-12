"""
Kor'tana's Goal Framework - Core Data Structures
Enables autonomous goal setting, prioritization, and pursuit within Sacred Covenant boundaries.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class GoalType(Enum):
    """Types of goals Kor'tana can autonomously pursue"""
    MAINTENANCE = "maintenance"          # System health, code quality, cleanup
    LEARNING = "learning"               # Knowledge acquisition, skill improvement
    IMPROVEMENT = "improvement"         # Performance optimization, feature enhancement
    USER_SERVICE = "user_service"       # Direct user assistance, request fulfillment
    EXPLORATION = "exploration"         # Research, experimentation, discovery


class GoalStatus(Enum):
    """Lifecycle states for goals"""
    NEW = "new"                         # Recently created, not yet reviewed
    ACTIVE = "active"                   # Currently being pursued
    PAUSED = "paused"                   # Temporarily suspended
    COMPLETED = "completed"             # Successfully accomplished
    CANCELLED = "cancelled"             # Abandoned or rejected
    BLOCKED = "blocked"                 # Cannot proceed due to dependencies


@dataclass
class Goal:
    """
    Represents an autonomous goal that Kor'tana can set and pursue.

    This is the fundamental unit of Kor'tana's self-directed behavior,
    enabling her to transition from reactive responses to proactive planning.
    """

    # Core identification
    goal_id: str = field(default_factory=lambda: f"goal_{uuid.uuid4().hex[:8]}")
    type: GoalType = GoalType.MAINTENANCE
    title: str = ""
    description: str = ""

    # Priority and status management
    priority: int = 5  # 1-10, where 10 is highest priority
    status: GoalStatus = GoalStatus.NEW

    # Temporal tracking
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    target_completion: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Execution details
    success_criteria: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"  # "low", "medium", "high"

    # Progress and metrics
    progress_metrics: Dict[str, Any] = field(default_factory=dict)
    completion_percentage: float = 0.0

    # Hierarchical relationships
    parent_goal_id: Optional[str] = None
    sub_goals: List[str] = field(default_factory=list)

    # Learning and insights"""
Kor'tana's Goal Framework - Core Data Structures
Enables autonomous goal setting, prioritization, and pursuit within Sacred Covenant boundaries.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class GoalType(Enum):
    """Types of goals Kor'tana can autonomously pursue"""
    MAINTENANCE = "maintenance"          # System health, code quality, cleanup
    LEARNING = "learning"               # Knowledge acquisition, skill improvement
    IMPROVEMENT = "improvement"         # Performance optimization, feature enhancement
    USER_SERVICE = "user_service"       # Direct user assistance, request fulfillment
    EXPLORATION = "exploration"         # Research, experimentation, discovery


class GoalStatus(Enum):
    """Lifecycle states for goals"""
    NEW = "new"                         # Recently created, not yet reviewed
    ACTIVE = "active"                   # Currently being pursued
    PAUSED = "paused"                   # Temporarily suspended
    COMPLETED = "completed"             # Successfully accomplished
    CANCELLED = "cancelled"             # Abandoned or rejected
    BLOCKED = "blocked"                 # Cannot proceed due to dependencies


@dataclass
class Goal:
    """
    Represents an autonomous goal that Kor'tana can set and pursue.

    This is the fundamental unit of Kor'tana's self-directed behavior,
    enabling her to transition from reactive responses to proactive planning.
    """

    # Core identification
    goal_id: str = field(default_factory=lambda: f"goal_{uuid.uuid4().hex[:8]}")
    type: GoalType = GoalType.MAINTENANCE
    title: str = ""
    description: str = ""

    # Priority and status management
    priority: int = 5  # 1-10, where 10 is highest priority
    status: GoalStatus = GoalStatus.NEW

    # Temporal tracking
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    target_completion: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Execution details
    success_criteria: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"  # "low", "medium", "high"

    # Progress and metrics
    progress_metrics: Dict[str, Any] = field(default_factory=dict)
    completion_percentage: float = 0.0

    # Hierarchical relationships
    parent_goal_id: Optional[str] = None
    sub_goals: List[str] = field(default_factory=list)

    # Learning and insights
    learning_insights: List[str] = field(default_factory=list)
    lessons_learned: Dict[str, str] = field(default_factory=dict)

    # Sacred Covenant compliance
    covenant_approved: bool = False
    covenant_review_notes: str = ""

    # Metadata
    created_by: str = "autonomous"  # "autonomous", "user", "system"
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization validation and setup"""
        if not self.title:
            self.title = f"{self.type.value.title()} Goal {self.goal_id[-8:]}"

        if not self.description:
            self.description = f"Autonomous {self.type.value} goal created at {self.created_at.isoformat()}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert goal to dictionary for storage"""
        return {
            "goal_id": self.goal_id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "target_completion": self.target_completion.isoformat() if self.target_completion else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "success_criteria": self.success_criteria,
            "required_capabilities": self.required_capabilities,
            "estimated_effort": self.estimated_effort,
            "progress_metrics": self.progress_metrics,
            "completion_percentage": self.completion_percentage,
            "parent_goal_id": self.parent_goal_id,
            "sub_goals": self.sub_goals,
            "learning_insights": self.learning_insights,
            "lessons_learned": self.lessons_learned,
            "covenant_approved": self.covenant_approved,
            "covenant_review_notes": self.covenant_review_notes,
            "created_by": self.created_by,
            "tags": self.tags,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Goal":
        """Create goal from dictionary"""
        goal = cls()
        goal.goal_id = data.get("goal_id", goal.goal_id)
        goal.type = GoalType(data.get("type", "maintenance"))
        goal.title = data.get("title", "")
        goal.description = data.get("description", "")
        goal.priority = data.get("priority", 5)
        goal.status = GoalStatus(data.get("status", "new"))

        # Parse datetime fields
        if data.get("created_at"):
            goal.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("target_completion"):
            goal.target_completion = datetime.fromisoformat(data["target_completion"])
        if data.get("started_at"):
            goal.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            goal.completed_at = datetime.fromisoformat(data["completed_at"])

        # Set other fields
        goal.success_criteria = data.get("success_criteria", [])
        goal.required_capabilities = data.get("required_capabilities", [])
        goal.estimated_effort = data.get("estimated_effort", "medium")
        goal.progress_metrics = data.get("progress_metrics", {})
        goal.completion_percentage = data.get("completion_percentage", 0.0)
        goal.parent_goal_id = data.get("parent_goal_id")
        goal.sub_goals = data.get("sub_goals", [])
        goal.learning_insights = data.get("learning_insights", [])
        goal.lessons_learned = data.get("lessons_learned", {})
        goal.covenant_approved = data.get("covenant_approved", False)
        goal.covenant_review_notes = data.get("covenant_review_notes", "")
        goal.created_by = data.get("created_by", "autonomous")
        goal.tags = data.get("tags", [])
        goal.context = data.get("context", {})

        return goal

    def is_actionable(self) -> bool:
        """Check if goal is ready for execution"""
        return (
            self.status == GoalStatus.ACTIVE and
            self.covenant_approved and
            len(self.success_criteria) > 0 and
            self.priority >= 3  # Don't execute very low priority goals
        )

    def can_be_activated(self) -> bool:
        """Check if goal is ready to be activated"""
        return (
            self.status == GoalStatus.NEW and
            self.covenant_approved and
            len(self.success_criteria) > 0
        )

    def update_progress(self, percentage: float, metrics: Dict[str, Any] = None, insights: List[str] = None):
        """Update goal progress and learning"""
        self.completion_percentage = max(0.0, min(100.0, percentage))

        if metrics:
            self.progress_metrics.update(metrics)

        if insights:
            self.learning_insights.extend(insights)

        # Auto-complete if 100%
        if self.completion_percentage >= 100.0 and self.status == GoalStatus.ACTIVE:
            self.status = GoalStatus.COMPLETED
            self.completed_at = datetime.now(timezone.utc)

    def activate(self):
        """Activate goal for pursuit"""
        if self.can_be_activated():
            self.status = GoalStatus.ACTIVE
            self.started_at = datetime.now(timezone.utc)
            return True
        return False

    def complete(self, lessons: Dict[str, str] = None):
        """Mark goal as completed with optional lessons"""
        self.status = GoalStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.completion_percentage = 100.0

        if lessons:
            self.lessons_learned.update(lessons)

    def pause(self, reason: str = ""):
        """Pause goal execution"""
        if self.status == GoalStatus.ACTIVE:
            self.status = GoalStatus.PAUSED
            if reason:
                self.context["pause_reason"] = reason

    def cancel(self, reason: str = ""):
        """Cancel goal"""
        self.status = GoalStatus.CANCELLED
        if reason:
            self.context["cancellation_reason"] = reason

    def get_age_days(self) -> float:
        """Get goal age in days"""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds() / 86400

    def get_time_to_deadline_days(self) -> Optional[float]:
        """Get days until target completion"""
        if not self.target_completion:
            return None
        return (self.target_completion - datetime.now(timezone.utc)).total_seconds() / 86400

    def is_overdue(self) -> bool:
        """Check if goal is past its target completion date"""
        if not self.target_completion:
            return False
        return datetime.now(timezone.utc) > self.target_completion and self.status not in [GoalStatus.COMPLETED, GoalStatus.CANCELLED]

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        goal = Goal(
            goal_type=GoalType(data['type']),
            description=data['description'],
            priority=data.get('priority', 5),
            metadata=data.get('metadata', {})
        )
        goal.id = data['id']
        goal.status = GoalStatus(data['status'])
        goal.progress = data.get('progress', 0.0)
        goal.created_at = data.get('created_at')
        goal.updated_at = data.get('updated_at', goal.created_at)
        return goal

class GoalManager:
    def __init__(self, storage_path: str = GOAL_STORAGE_PATH):
        self.storage_path = storage_path
        self.goals = self._load_goals()

    def _load_goals(self) -> List[Goal]:
        if not os.path.exists(self.storage_path):
            return []
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            return [Goal.from_dict(json.loads(line)) for line in f if line.strip()]

    def _save_goals(self):
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            for goal in self.goals:
                f.write(json.dumps(goal.to_dict()) + '\n')

    def create_goal(self, goal_type: GoalType, description: str, priority: int = 5, metadata: Optional[Dict[str, Any]] = None) -> Goal:
        goal = Goal(goal_type, description, priority, metadata)
        self.goals.append(goal)
        self._save_goals()
        return goal

    def update_goal_status(self, goal_id: str, status: GoalStatus, progress: Optional[float] = None):
        for goal in self.goals:
            if goal.id == goal_id:
                goal.status = status
                if progress is not None:
                    goal.progress = progress
                goal.updated_at = datetime.utcnow().isoformat()
                self._save_goals()
                return goal
        return None

    def get_next_goal(self) -> Optional[Goal]:
        pending_goals = [g for g in self.goals if g.status == GoalStatus.PENDING]
        if not pending_goals:
            return None
        return sorted(pending_goals, key=lambda g: (-g.priority, g.created_at))[0]

    def archive_goal(self, goal_id: str):
        for goal in self.goals:
            if goal.id == goal_id:
                goal.status = GoalStatus.COMPLETED
                goal.updated_at = datetime.utcnow().isoformat()
                self._save_goals()
                return goal
        return None

    def list_goals(self, status: Optional[GoalStatus] = None) -> List[Goal]:
        if status:
            return [g for g in self.goals if g.status == status]
        return self.goals

class GoalEvaluator:
    def __init__(self, covenant_enforcer=None):
        self.covenant_enforcer = covenant_enforcer

    def evaluate_goal(self, goal: Goal) -> bool:
        # Placeholder: integrate with CovenantEnforcer for real checks
        if self.covenant_enforcer:
            return self.covenant_enforcer.check_goal(goal)
        return True

# Integration with scheduler and ADE would be implemented in their respective modules.
