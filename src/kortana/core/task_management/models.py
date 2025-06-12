"""
Kor'tana Task Management Models
Defines data models for autonomous task tracking and execution.
"""

import enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

class TaskStatus(enum.Enum):
    """Status of a task in the system"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    """Priority levels for tasks"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

class TaskCategory(enum.Enum):
    """Categories of autonomous tasks"""
    DEVELOPMENT = "development"        # Code development tasks
    MAINTENANCE = "maintenance"        # System maintenance
    RESEARCH = "research"             # Learning and research
    MONITORING = "monitoring"         # System monitoring
    COMMUNICATION = "communication"   # Inter-agent communication
    ANALYSIS = "analysis"            # Code/data analysis
    TESTING = "testing"              # Running tests
    OPTIMIZATION = "optimization"     # Performance improvements

@dataclass
class TaskContext:
    """Context information for a task"""
    allowed_dirs: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    token_budget: Optional[int] = None
    related_files: List[str] = field(default_factory=list)
    memory_refs: List[str] = field(default_factory=list)
    workspace_root: Optional[str] = None

@dataclass
class TaskResult:
    """Result of task execution"""
    success: bool
    completion_time: datetime
    output: Any = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Task:
    """Represents a single autonomous task"""
    id: str
    category: TaskCategory
    description: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: TaskContext = field(default_factory=TaskContext)
    subtasks: List['Task'] = field(default_factory=list)
    parent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)  # IDs of tasks this one depends on
    result: Optional[TaskResult] = None
    retries: int = 0
    max_retries: int = 3
