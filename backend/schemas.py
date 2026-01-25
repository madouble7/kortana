"""
Pydantic schemas for request/response validation
Kor'tana Backend - Input validation and data models
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field

# ========================================================
# Authentication Schemas
# ========================================================


class Token(BaseModel):
    """JWT Token response"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class TokenData(BaseModel):
    """Token payload data"""

    username: str | None = None
    scopes: list[str] = []


class UserBase(BaseModel):
    """Base user model"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr | None = None
    full_name: str | None = None


class UserCreate(UserBase):
    """User creation model"""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update model"""

    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = Field(None, min_length=8)


class User(UserBase):
    """User model with ID"""

    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Login request model"""

    username: str
    password: str


# ========================================================
# Agent Schemas
# ========================================================


class AgentStatus(str, Enum):
    """Agent status enum"""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class AgentBase(BaseModel):
    """Base agent model"""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    enabled: bool = True


class AgentCreate(AgentBase):
    """Agent creation model"""

    model: str = Field(..., description="AI model to use")
    temperature: float = Field(0.7, ge=0.0, le=1.0)


class AgentUpdate(BaseModel):
    """Agent update model"""

    name: str | None = None
    description: str | None = None
    enabled: bool | None = None
    temperature: float | None = Field(None, ge=0.0, le=1.0)


class Agent(AgentBase):
    """Full agent model"""

    id: int
    owner_id: int
    model: str
    temperature: float
    status: AgentStatus = AgentStatus.IDLE
    created_at: datetime
    updated_at: datetime | None = None
    last_activity: datetime | None = None

    class Config:
        from_attributes = True


# ========================================================
# Task Schemas
# ========================================================


class TaskStatus(str, Enum):
    """Task status enum"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskBase(BaseModel):
    """Base task model"""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    priority: int = Field(1, ge=1, le=5)


class TaskCreate(TaskBase):
    """Task creation model"""

    agent_id: int
    input_data: dict | None = None


class TaskUpdate(BaseModel):
    """Task update model"""

    title: str | None = None
    description: str | None = None
    priority: int | None = Field(None, ge=1, le=5)
    status: TaskStatus | None = None


class Task(TaskBase):
    """Full task model"""

    id: int
    agent_id: int
    status: TaskStatus = TaskStatus.PENDING
    input_data: dict | None = None
    output_data: dict | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


# ========================================================
# GitHub Schemas
# ========================================================


class GitHubRepository(BaseModel):
    """GitHub repository model"""

    id: int
    name: str
    full_name: str
    description: str | None = None
    url: str
    is_private: bool = False
    stars: int = 0
    forks: int = 0
    language: str | None = None


class GitHubIssue(BaseModel):
    """GitHub issue model"""

    id: int
    number: int
    title: str
    body: str | None = None
    state: str  # open, closed
    created_at: datetime
    updated_at: datetime | None = None
    author: str
    assignees: list[str] = []
    labels: list[str] = []


class GitHubPullRequest(BaseModel):
    """GitHub pull request model"""

    id: int
    number: int
    title: str
    description: str | None = None
    state: str  # open, closed, merged
    created_at: datetime
    updated_at: datetime | None = None
    author: str
    head_branch: str
    base_branch: str
    additions: int = 0
    deletions: int = 0


# ========================================================
# Memory Schemas
# ========================================================


class MemoryItem(BaseModel):
    """Memory item model"""

    id: int
    key: str
    value: dict
    agent_id: int
    created_at: datetime
    updated_at: datetime | None = None
    ttl: int | None = None  # Time to live in seconds

    class Config:
        from_attributes = True


class MemoryCreate(BaseModel):
    """Memory creation model"""

    key: str = Field(..., min_length=1)
    value: dict
    ttl: int | None = None


# ========================================================
# Knowledge Base Schemas
# ========================================================


class KnowledgeDocument(BaseModel):
    """Knowledge document model"""

    id: int
    title: str
    content: str
    source: str | None = None
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class KnowledgeCreate(BaseModel):
    """Knowledge document creation"""

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    source: str | None = None
    tags: list[str] = []


class KnowledgeSearch(BaseModel):
    """Knowledge search request"""

    query: str = Field(..., min_length=1)
    limit: int = Field(10, ge=1, le=100)
    min_relevance: float = Field(0.5, ge=0.0, le=1.0)


# ========================================================
# Error Schemas
# ========================================================


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: str
    status_code: int
    message: str
    details: dict | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationErrorResponse(BaseModel):
    """Validation error response"""

    error: str = "VALIDATION_ERROR"
    status_code: int = 422
    message: str
    details: list[dict]


# ========================================================
# Health Schemas
# ========================================================


class HealthCheck(BaseModel):
    """Health check response"""

    status: str
    message: str
    environment: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ServiceHealth(BaseModel):
    """Individual service health"""

    name: str
    status: str  # healthy, degraded, unhealthy
    response_time_ms: float
    last_check: datetime


# ========================================================
# Pagination Schemas
# ========================================================


class PaginationParams(BaseModel):
    """Pagination parameters"""

    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    sort_by: str | None = None
    sort_order: str = Field("asc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""

    data: list[dict]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool


# ========================================================
# Billing Schemas
# ========================================================


class BillingPlanType(str, Enum):
    """Billing plan types"""

    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class CustomerCreate(BaseModel):
    """Create Stripe customer"""

    email: EmailStr
    name: str | None = None
    metadata: dict | None = None


class Customer(BaseModel):
    """Stripe customer model"""

    id: str
    email: str
    name: str | None = None
    created: int
    metadata: dict | None = None


class SubscriptionCreate(BaseModel):
    """Create subscription"""

    customer_id: str
    price_id: str
    trial_period_days: int | None = None
    metadata: dict | None = None


class Subscription(BaseModel):
    """Stripe subscription model"""

    id: str
    customer_id: str
    status: str  # active, past_due, canceled, etc.
    current_period_start: int
    current_period_end: int
    cancel_at_period_end: bool
    plan_type: BillingPlanType | None = None
    metadata: dict | None = None


class PaymentIntentCreate(BaseModel):
    """Create payment intent"""

    amount: int = Field(..., ge=1, description="Amount in cents")
    currency: str = Field(
        "usd",
        min_length=3,
        max_length=3,
        pattern="^[a-z]{3}$",
        description="ISO 4217 currency code (3 lowercase letters, e.g., usd, eur)",
    )
    customer_id: str | None = None
    description: str | None = None
    metadata: dict | None = None


class PaymentIntent(BaseModel):
    """Payment intent model"""

    id: str
    amount: int
    currency: str
    status: str  # requires_payment_method, requires_confirmation, succeeded, etc.
    client_secret: str
    customer_id: str | None = None
    description: str | None = None


class WebhookEvent(BaseModel):
    """Stripe webhook event"""

    id: str
    type: str
    data: dict
    created: int


class BillingInfo(BaseModel):
    """User billing information"""

    customer_id: str | None = None
    subscription_id: str | None = None
    plan_type: BillingPlanType = BillingPlanType.FREE
    subscription_status: str | None = None
    current_period_end: int | None = None
    cancel_at_period_end: bool = False
