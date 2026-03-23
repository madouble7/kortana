from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
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
    temperature: float = 0.7

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

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_HO = "waiting_for_ho"
    BLOCKED = "blocked"

class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    classification: TaskClassification = TaskClassification.AUTO

class TaskCreate(TaskBase):
    command: Optional[str] = None

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
