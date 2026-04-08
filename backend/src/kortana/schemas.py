from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class User(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    enabled: bool = True


class AgentCreate(AgentBase):
    model: str
    temperature: float = Field(0.7, ge=0.0, le=1.0)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    enabled: Optional[bool] = None


class Agent(AgentBase):
    id: str
    model: str
    temperature: float
    status: AgentStatus = AgentStatus.IDLE
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskClassification(str, Enum):
    AUTO = "auto"
    HO = "ho"
    APPROVAL = "approval"
    SELF_CORRECTION = "self_correction"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_FOR_HO = "waiting_for_ho"
    BLOCKED = "blocked"


class TaskBase(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    classification: TaskClassification = TaskClassification.AUTO
    agent_id: Optional[str] = None


class TaskCreate(TaskBase):
    command: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)


class Task(TaskBase):
    id: str
    status: TaskStatus
    command: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    ho_scaffold: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HealthCheck(BaseModel):
    status: str
    message: str
    environment: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standard error response schema"""

    error: str
    message: str
    status_code: int
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BillingPlanType(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class CustomerCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    metadata: Optional[dict] = None


class Customer(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created: int
    metadata: Optional[dict] = None


class SubscriptionCreate(BaseModel):
    customer_id: str
    price_id: str
    trial_period_days: Optional[int] = None
    metadata: Optional[dict] = None


class Subscription(BaseModel):
    id: str
    customer_id: str
    status: str
    current_period_start: int
    current_period_end: int
    cancel_at_period_end: bool
    plan_type: Optional[BillingPlanType] = None
    metadata: Optional[dict] = None


class PaymentIntentCreate(BaseModel):
    amount: int = Field(..., ge=1)
    currency: str = Field("usd", min_length=3, max_length=3)
    customer_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None


class PaymentIntent(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    client_secret: str
    customer_id: Optional[str] = None
    description: Optional[str] = None


class BillingInfo(BaseModel):
    customer_id: Optional[str] = None
    subscription_id: Optional[str] = None
    plan_type: BillingPlanType = BillingPlanType.FREE
    current_period_end: Optional[int] = None
    cancel_at_period_end: bool = False


class WorkflowStatus(str, Enum):
    """Workflow execution status"""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskNodeSchema(BaseModel):
    """Schema for a task node in a workflow"""

    task_name: str
    task_args: tuple = Field(default_factory=tuple)
    task_kwargs: dict = Field(default_factory=dict)
    node_id: str
    dependencies: List[str] = Field(default_factory=list)
    retry_on_failure: bool = True
    max_retries: int = 3
    timeout: int = 300


class Workflow(BaseModel):
    """Workflow definition for autonomous task orchestration"""

    workflow_id: str
    name: str
    description: str
    nodes: dict = Field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PersistentState(BaseModel):
    """Persistent workflow execution state for autonomous systems"""

    workflow_id: str
    task_id: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    current_level: int = 0
    completed_tasks: List[str] = Field(default_factory=list)
    failed_tasks: List[str] = Field(default_factory=list)
    results: dict = Field(default_factory=dict)
    errors: dict = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    summary: str
    priority: str
    analysis: str
    suggested_actions: List[str]
    estimated_effort: str


class SongwritingAnalyzeRequest(BaseModel):
    lyrics: str
    key: str = "C"
    mood: str = "neutral"
    genre: str = "pop"


class SongwritingLineAnalysis(BaseModel):
    line: str
    syllables: int
    rhyme_key: str
    rhyme_label: str


class SongwritingRhymePair(BaseModel):
    label: str
    lines: List[int]


class SongwritingProgression(BaseModel):
    name: str
    numeral_progression: List[str]
    chords: List[str]


class SongwritingAnalyzeResponse(BaseModel):
    rhyme_scheme: str
    lines: List[SongwritingLineAnalysis]
    rhyme_pairs: List[SongwritingRhymePair]
    structure: dict
    chord_progressions: List[SongwritingProgression]
    alignment_score: dict


# -- Chord analysis ----------------------------------------------------------


class ChordDetailSchema(BaseModel):
    degree: int
    roman: str
    root: str
    quality: str
    name: str
    notes: List[str]


class ChordAnalysisRequest(BaseModel):
    key: str
    progression: Optional[str] = None
    degrees: Optional[List[int]] = None


class ChordAnalysisResponse(BaseModel):
    key: str
    scale: List[str]
    diatonic_chords: List[ChordDetailSchema]
    progression: Optional[dict] = None


# -- Syllable endpoint -------------------------------------------------------


class SyllableRequest(BaseModel):
    line: str


class SyllableResponse(BaseModel):
    line: str
    syllable_count: int
    word_counts: List[dict]


# -- Generate endpoint -------------------------------------------------------


class SongGenerateRequest(BaseModel):
    topic: str
    genre: str = "pop"
    mood: str = "uplifting"
    key: str = "C"
    progression: str = "I-V-vi-IV"
    structure: str = "standard"


class SongGenerateResponse(BaseModel):
    topic: str
    genre: str
    mood: str
    key: str
    progression: dict
    structure: List[str]
    scale: List[str]
    lyrics: Optional[str] = None
    analysis: Optional[dict] = None
    note: Optional[str] = None
