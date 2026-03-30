# Kor'tana: Development Guide & Blueprint
## Complete Implementation Reference for 6-Week Optimization

**Status:** Development-ready blueprint  
**Audience:** Developers, architects, tech leads  
**Updated:** 2026  

---

## TABLE OF CONTENTS

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure & Organization](#project-structure--organization)
3. [Week 1: Autonomy Layer Blueprint](#week-1-autonomy-layer-blueprint)
4. [Week 2: Performance Optimization Blueprint](#week-2-performance-optimization-blueprint)
5. [Week 3: Container Optimization Blueprint](#week-3-container-optimization-blueprint)
6. [Week 4: Observability Blueprint](#week-4-observability-blueprint)
7. [Week 5: Scalability Blueprint](#week-5-scalability-blueprint)
8. [Week 6: Production Hardening Blueprint](#week-6-production-hardening-blueprint)
9. [Testing Strategy](#testing-strategy)
10. [CI/CD Pipeline](#cicd-pipeline)
11. [Code Review & Quality](#code-review--quality)
12. [Deployment Procedures](#deployment-procedures)

---

# DEVELOPMENT ENVIRONMENT SETUP

## Prerequisites

### Required Software
```bash
# Core
- Python 3.11+ (backend)
- Node.js 20+ (frontend)
- Docker & Docker Compose (latest)
- PostgreSQL 16 (via Docker)
- Redis 7 (via Docker)
- Git 2.40+

# Development tools
- VS Code or PyCharm (backend)
- Visual Studio Code (frontend)
- Postman or Insomnia (API testing)
- DBeaver (database management)
- Git Bash / ZSH (shell)

# Optional but recommended
- make (build automation)
- tmux (terminal multiplexing)
- jq (JSON processing)
```

### Installation (macOS/Linux)
```bash
# Install Homebrew (macOS)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11
brew install python-tk

# Install Node
brew install node@20

# Install Docker
brew install docker docker-compose

# Install PostgreSQL CLI
brew install postgresql

# Install Redis CLI
brew install redis

# Install development tools
brew install git make tmux jq
```

### Installation (Windows/WSL2)
```bash
# Enable WSL2
wsl --install

# Inside WSL2 Ubuntu:
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y nodejs npm
sudo apt install -y docker.io docker-compose
sudo apt install -y postgresql-client redis-tools
sudo apt install -y git make tmux jq

# Add user to docker group
sudo usermod -aG docker $USER
```

---

## Project Structure Setup

### Directory Organization
```
c:\kor-tana\
├── kortana/                              # Main application
│   ├── backend/                          # FastAPI backend
│   │   ├── main.py                       # Entry point
│   │   ├── config.py                     # Configuration
│   │   ├── requirements.txt              # Python dependencies
│   │   ├── routers/                      # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── agents.py
│   │   │   ├── autonomy.py              # NEW: Autonomy endpoints
│   │   │   ├── auth.py
│   │   │   ├── code_generator.py
│   │   │   └── ...
│   │   ├── services/                     # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── self_awareness.py        # NEW: Self-awareness service
│   │   │   ├── adaptive_learning.py     # NEW: Learning service
│   │   │   ├── goal_manager.py          # NEW: Goal management
│   │   │   ├── agent_service.py
│   │   │   └── ...
│   │   ├── models/                       # Database models
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── execution.py
│   │   │   └── ...
│   │   ├── middleware/                   # Express-like middleware
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── metrics.py               # NEW: Prometheus metrics
│   │   │   └── errors.py
│   │   ├── database.py                   # Database setup
│   │   ├── dependencies.py               # FastAPI dependencies
│   │   ├── utils/                        # Utilities
│   │   └── alembic/                      # Database migrations
│   │
│   ├── frontend/                         # React frontend
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   └── App.tsx
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── Dockerfile                    # Frontend production build
│   │   └── Dockerfile.dev
│   │
│   ├── tests/                            # Test suite
│   │   ├── unit/                         # Unit tests
│   │   │   ├── services/
│   │   │   ├── routers/
│   │   │   └── models/
│   │   ├── integration/                  # Integration tests
│   │   ├── smoke/                        # Smoke tests
│   │   ├── load/                         # Load tests
│   │   └── conftest.py
│   │
│   ├── docker-compose.yml                # Local development
│   ├── docker-compose.prod.yml           # Production
│   ├── docker-compose.monitoring.yml     # Monitoring stack
│   ├── .dockerignore
│   └── .env.example
│
├── docs/                                 # Documentation
│   ├── architecture/
│   ├── api/
│   ├── deployment/
│   └── troubleshooting/
│
├── scripts/                              # Helper scripts
│   ├── db-migrate.sh
│   ├── seed-data.sh
│   ├── run-tests.sh
│   └── deploy.sh
│
├── Makefile                              # Build automation
├── .gitignore
└── README.md
```

### Create Directory Structure
```bash
cd c:\kor-tana\kortana\backend

# Create new directories
mkdir -p services/{autonomy,learning,goals}
mkdir -p routers/{v1,v2}
mkdir -p middleware/{auth,monitoring}
mkdir -p tests/{unit,integration,smoke,load}

# Create __init__.py files
touch services/__init__.py
touch middleware/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

---

## Development Environment Configuration

### Create `.env.development`
```bash
# Backend configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=kortana
DB_PASSWORD=dev_password
DB_NAME=kortana_dev

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API Keys (use test keys)
OPENAI_API_KEY=sk-test-development
GEMINI_API_KEY=test_development
ANTHROPIC_API_KEY=test_development

# External Services
GITHUB_TOKEN=ghp_test_development
DISCORD_BOT_TOKEN=test_development

# Monitoring (development)
PROMETHEUS_ENABLED=false
JAEGER_ENABLED=false

# Server
API_HOST=127.0.0.1
API_PORT=8000
API_WORKERS=1

# Security (relaxed for development)
CORS_ORIGINS=*
RATE_LIMIT_ENABLED=false
JWT_SECRET=dev-secret-key-change-in-production
```

### Frontend Development Configuration
```bash
# Create `.env.development.local` in frontend/

VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_DEBUG=true
VITE_LOG_LEVEL=debug
```

### Docker Compose Development Setup
```yaml
# docker-compose.yml (development)
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: kortana
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: kortana_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kortana"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./kortana/backend
      dockerfile: Dockerfile.dev
    environment:
      - $(cat .env.development)
    ports:
      - "8000:8000"
    volumes:
      - ./kortana/backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./kortana/frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./kortana/frontend/src:/app/src
    depends_on:
      - backend
    command: npm run dev

volumes:
  postgres_data:
```

### Quick Start Script
```bash
#!/bin/bash
# scripts/dev-setup.sh

set -e

echo "🚀 Setting up Kor'tana development environment..."

# Copy environment files
cp .env.example .env.development
cp kortana/frontend/.env.example kortana/frontend/.env.development.local

# Install Python dependencies
cd kortana/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio

# Install Node dependencies
cd ../frontend
npm install

# Start services
cd ../..
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed test data
docker-compose exec backend python -m scripts.seed_data

echo "✅ Development environment ready!"
echo "📍 Backend: http://localhost:8000"
echo "📍 Frontend: http://localhost:3000"
echo "📍 API Docs: http://localhost:8000/docs"
```

---

# PROJECT STRUCTURE & ORGANIZATION

## Naming Conventions

### Python Files
```python
# Services (business logic)
services/self_awareness.py           # Module name: snake_case
services/adaptive_learning.py

# Routers (API endpoints)
routers/autonomy.py                  # Router name: snake_case

# Models (database)
models/agent.py                      # Singular, snake_case

# Classes
class SelfAwarenessEngine:           # PascalCase (CapWords)
class AdaptiveLearner:
class HopDecision:

# Functions/Methods
async def assess_system_state():     # snake_case
def compute_confidence_score():

# Constants
SYSTEM_TIMEOUT = 30                  # UPPER_SNAKE_CASE
MAX_RETRIES = 3
```

### TypeScript/React Files
```typescript
// Components
components/Dashboard.tsx             # PascalCase
components/AgentCard.tsx
components/autonomy/SelfAwarenessPanel.tsx

// Hooks
hooks/useAutonomy.ts                 # camelCase with 'use' prefix
hooks/useSelfAwareness.ts

// Services
services/autonomyService.ts          # camelCase
services/agentService.ts

// Types
types/autonomy.ts                    # snake_case, descriptive
types/agent.ts

// Interfaces
interface SelfAwarenessState {        # PascalCase
interface AutonomyResponse {
}
```

## Module Organization

### Backend Service Module Pattern
```python
# File: services/self_awareness.py

"""Service module for system self-awareness and introspection.

This module provides the SelfAwarenessEngine class which enables
Kor'tana to monitor, assess, and understand its own system state,
performance, and decision-making capabilities.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Constants (top-level)
DEFAULT_ASSESSMENT_INTERVAL = 300  # seconds
DEFAULT_METRIC_RETENTION = 1000    # entries

# Enums
class SystemState(Enum):
    """System state enumeration."""
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    CRITICAL = "critical"

# Data classes
@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    # ...

# Main class
class SelfAwarenessEngine:
    """Main service class for self-awareness."""
    
    def __init__(self, redis_client, db_session):
        """Initialize the engine."""
        pass
    
    async def assess_system_state(self) -> SystemState:
        """Public method: Assess system state."""
        pass
    
    # Private methods (prefix with _)
    async def _collect_metrics(self) -> PerformanceMetrics:
        """Internal method: Collect metrics."""
        pass
```

### Router/Endpoint Pattern
```python
# File: routers/autonomy.py

"""API router for autonomous decision-making and self-awareness.

Endpoints:
  POST   /api/autonomy/self-awareness/assess
  POST   /api/autonomy/self-correction/plan
  POST   /api/autonomy/self-correction/execute
  POST   /api/autonomy/hop/propose
  POST   /api/autonomy/hop/vote
  GET    /api/autonomy/hop/consensus/{decision_id}
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from kortana.backend.dependencies import get_db, get_redis
from kortana.backend.services.self_awareness import SelfAwarenessEngine

router = APIRouter(prefix="/autonomy", tags=["autonomy"])

@router.post("/self-awareness/assess")
async def assess_system_awareness(
    session: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Assess system self-awareness and state."""
    engine = SelfAwarenessEngine(redis_client, session)
    # Implementation
    return {"state": "nominal"}

# More endpoints...
```

## Code Style & Standards

### Python Code Style
```python
# Line length: 88 characters (Black formatter)
# Type hints: Required for all public methods

from typing import Dict, List, Optional, Any
import asyncio

class Example:
    async def example_method(
        self,
        param1: str,
        param2: int,
        param3: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Docstring format: Google style.
        
        Args:
            param1: Description of param1.
            param2: Description of param2.
            param3: Optional parameter description.
        
        Returns:
            Dictionary containing result data.
        
        Raises:
            ValueError: If param1 is empty.
        """
        if not param1:
            raise ValueError("param1 cannot be empty")
        
        return {"result": param1}
```

### TypeScript/React Code Style
```typescript
// Line length: 100 characters
// Strict mode: enabled

interface ComponentProps {
  title: string;
  onClose: () => void;
  data?: Record<string, unknown>;
}

export const Example: React.FC<ComponentProps> = ({
  title,
  onClose,
  data,
}) => {
  const [state, setState] = React.useState<string>("");

  return (
    <div className="example">
      <h1>{title}</h1>
      <button onClick={onClose}>Close</button>
    </div>
  );
};
```

---

# WEEK 1: AUTONOMY LAYER BLUEPRINT

## Overview
**Goal:** Implement autonomous decision-making with self-awareness  
**Duration:** 38 hours  
**Team Size:** 1 senior + 1 mid-level developer  

---

## Sprint Breakdown

### Day 1-2: Planning & Setup (8 hours)

#### Task 1.1: Architecture Review & Planning (4 hours)
```
- Review existing HOP implementation
- Design SelfAwarenessEngine architecture
- Design distributed voting system
- Design data flow diagrams
- Plan API endpoints

Deliverables:
- Architecture decision record (ADR)
- Data flow diagrams
- API specification (OpenAPI)
```

#### Task 1.2: Development Environment Setup (4 hours)
```
- Create feature branch: feature/autonomy-layer
- Set up development databases
- Install required dependencies (hypothesis, opentelemetry-api)
- Create test fixtures and mocks
- Set up logging configuration

Dependencies added to requirements.txt:
- redis[asyncio]==5.0+
- sqlalchemy[asyncio]==2.0+
- dataclasses-json==0.6+
- pydantic==2.0+
```

---

### Day 3-4: SelfAwarenessEngine Implementation (16 hours)

#### Task 2.1: Core Service Implementation (10 hours)

**File:** `kortana/backend/services/self_awareness.py`

```python
# Implementation checklist:
- [x] SystemState enum with 4 states
- [x] PerformanceMetrics dataclass
- [x] SelfAwarenessEngine.__init__()
- [x] assess_system_state() method
- [x] _collect_metrics() helper
- [x] compute_confidence_score() method
- [x] detect_drift() method
- [x] plan_self_correction() method
- [x] execute_self_correction() method
- [x] Error handling with proper logging
- [x] Redis persistence for state history
- [x] Metrics tracking

Code metrics:
- Lines of code: 400-450
- Methods: 15+
- Async functions: 8
- Test coverage target: 85%+
```

**Key Implementation Points:**

```python
# 1. Enum-based state management
class SystemState(Enum):
    NOMINAL = "nominal"           # All systems normal
    DEGRADED = "degraded"         # Performance issues
    CRITICAL = "critical"         # Immediate attention needed
    RECOVERING = "recovering"     # Recovery in progress

# 2. Metric collection from multiple sources
async def _collect_metrics(self) -> PerformanceMetrics:
    metrics = PerformanceMetrics(
        timestamp=datetime.utcnow(),
        cpu_usage=await self._get_prometheus_metric('cpu_usage'),
        memory_usage=await self._get_prometheus_metric('memory_usage'),
        # ... more metrics
    )
    return metrics

# 3. Multi-factor confidence scoring
async def compute_confidence_score(self, decision: Dict) -> float:
    factors = {
        'data_quality': 0.9,
        'model_certainty': decision.get('certainty', 0.5),
        'system_load': 0.8,
        'historical_accuracy': 0.85,
    }
    
    # Weighted average
    return sum(factors.values()) / len(factors)

# 4. Drift detection (deviation from baseline)
async def detect_drift(self) -> Dict[str, Any]:
    current = await self._collect_metrics()
    baseline = self.baseline_metrics
    
    # Calculate percentage deviation for each metric
    # Flag if deviation > threshold
    
    return drift_report

# 5. Autonomous correction planning
async def plan_self_correction(self, issues: List[str]) -> List[Dict]:
    actions = []
    for issue in issues:
        if 'cpu' in issue:
            actions.append({
                'action': 'scale_backend_workers',
                'target_count': 4,
            })
    return actions
```

#### Task 2.2: API Endpoints for Self-Awareness (4 hours)

**File:** `kortana/backend/routers/autonomy.py` (new section)

```python
from fastapi import APIRouter
from kortana.backend.services.self_awareness import SelfAwarenessEngine

router = APIRouter(prefix="/autonomy", tags=["autonomy"])

# Endpoint 1: Assess system state
@router.post("/self-awareness/assess", response_model=SystemStateResponse)
async def assess_system_awareness(session: AsyncSession = Depends(get_db)):
    """Assess system self-awareness and current state."""
    engine = SelfAwarenessEngine(redis, session)
    state = await engine.assess_system_state()
    return {"state": state.value}

# Endpoint 2: Compute confidence score
@router.post("/confidence-score")
async def compute_decision_confidence(
    decision: Dict[str, Any],
    session: AsyncSession = Depends(get_db)
):
    """Compute confidence score for a decision."""
    engine = SelfAwarenessEngine(redis, session)
    confidence = await engine.compute_confidence_score(decision)
    return {"confidence": confidence}

# Endpoint 3: Detect drift
@router.get("/drift-detection")
async def detect_system_drift(session: AsyncSession = Depends(get_db)):
    """Detect deviation from baseline metrics."""
    engine = SelfAwarenessEngine(redis, session)
    drift = await engine.detect_drift()
    return {"drift": drift}

# Endpoint 4: Plan corrections
@router.post("/self-correction/plan")
async def plan_corrections(
    issues: List[str],
    session: AsyncSession = Depends(get_db)
):
    """Plan autonomous corrective actions."""
    engine = SelfAwarenessEngine(redis, session)
    actions = await engine.plan_self_correction(issues)
    return {"actions": actions}

# Endpoint 5: Execute corrections
@router.post("/self-correction/execute")
async def execute_corrections(
    actions: List[Dict[str, Any]],
    dry_run: bool = True,
    session: AsyncSession = Depends(get_db)
):
    """Execute autonomous corrections."""
    engine = SelfAwarenessEngine(redis, session)
    results = await engine.execute_self_correction(actions, dry_run=dry_run)
    return {"results": results}
```

#### Task 2.3: Unit Tests (4 hours)

**File:** `kortana/backend/tests/unit/services/test_self_awareness.py`

```python
import pytest
from datetime import datetime
from kortana.backend.services.self_awareness import (
    SelfAwarenessEngine, SystemState, PerformanceMetrics
)

@pytest.fixture
def awareness_engine(redis_mock, db_session):
    return SelfAwarenessEngine(redis_mock, db_session)

@pytest.mark.asyncio
async def test_assess_system_state_nominal(awareness_engine):
    """Test system state assessment in nominal conditions."""
    state = await awareness_engine.assess_system_state()
    assert state == SystemState.NOMINAL

@pytest.mark.asyncio
async def test_assess_system_state_degraded(awareness_engine):
    """Test system state assessment in degraded conditions."""
    # Mock high CPU
    awareness_engine._get_prometheus_metric = AsyncMock(return_value=85.0)
    state = await awareness_engine.assess_system_state()
    assert state == SystemState.DEGRADED

@pytest.mark.asyncio
async def test_confidence_scoring():
    """Test confidence score computation."""
    decision = {
        'type': 'scale_backend',
        'certainty': 0.9,
        'data_quality_score': 0.95,
    }
    confidence = await awareness_engine.compute_confidence_score(decision)
    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.8

@pytest.mark.asyncio
async def test_drift_detection():
    """Test drift detection from baseline."""
    drift = await awareness_engine.detect_drift()
    # Should be empty initially (no drift)
    assert drift == {}

@pytest.mark.asyncio
async def test_correction_planning(awareness_engine):
    """Test autonomous correction planning."""
    issues = ['high_cpu', 'high_memory']
    actions = await awareness_engine.plan_self_correction(issues)
    assert len(actions) >= 2
    assert any(a['action'] == 'scale_backend_workers' for a in actions)

# Test coverage target: 85%+
# Run: pytest tests/unit/services/test_self_awareness.py -v --cov
```

---

### Day 5: Enhanced HOP Implementation (12 hours)

#### Task 3.1: Distributed HOP with Voting (8 hours)

**File:** `kortana/backend/human_only_protocol.py` (enhancement)

```python
# Implementation checklist:
- [x] RiskLevel enum
- [x] VoteOutcome enum
- [x] HopDecision dataclass
- [x] DistributedHOP class
- [x] classify_decision() method
- [x] should_escalate_to_human() method
- [x] initiate_distributed_vote() method
- [x] cast_vote() method
- [x] reach_consensus() method (Byzantine fault tolerance)
- [x] execute_decision() method
- [x] Redis-based vote storage
- [x] Consensus logic with 2/3 majority

Key algorithms:
- Byzantine fault tolerance (2/3 majority)
- Distributed consensus
- Vote timeout handling
- State replication across nodes
```

**Implementation Structure:**

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class VoteOutcome(Enum):
    UNANIMOUS = "unanimous"
    MAJORITY = "majority"
    SPLIT = "split"
    NO_CONSENSUS = "no_consensus"

@dataclass
class HopDecision:
    decision_id: str
    decision_type: str
    risk_level: RiskLevel
    requires_approval: bool
    confidence: float
    created_at: datetime
    votes: Dict[str, bool] = None
    outcome: Optional[VoteOutcome] = None
    approved_by: Optional[str] = None

class DistributedHOP:
    """Distributed HOP with consensus voting."""
    
    def __init__(self, redis_client, node_id: str, total_nodes: int = 3):
        self.redis = redis_client
        self.node_id = node_id
        self.total_nodes = total_nodes
        
    async def classify_decision(
        self,
        decision_type: str,
        confidence: float,
    ) -> RiskLevel:
        """Classify decision risk level."""
        # Risk classification logic
        pass
    
    async def initiate_distributed_vote(
        self,
        decision_id: str,
        decision_type: str,
        risk_level: RiskLevel,
        confidence: float,
    ) -> HopDecision:
        """Start distributed vote across nodes."""
        # Vote initialization
        pass
    
    async def reach_consensus(self, decision_id: str) -> tuple:
        """Determine consensus using Byzantine fault tolerance.
        
        Returns: (approved, outcome, details)
        
        Algorithm:
        - Require 2/3+ majority for approval
        - Handle Byzantine failures
        - Timeout after 30 seconds
        """
        votes = await self._get_all_votes(decision_id)
        
        if not votes:
            return False, VoteOutcome.NO_CONSENSUS, {}
        
        approve_count = sum(1 for v in votes.values() if v)
        total_votes = len(votes)
        threshold = (2 * total_votes) / 3
        
        if approve_count >= threshold:
            outcome = VoteOutcome.UNANIMOUS if approve_count == total_votes else VoteOutcome.MAJORITY
            return True, outcome, {'approve': approve_count, 'total': total_votes}
        else:
            outcome = VoteOutcome.MAJORITY if total_votes > 1 else VoteOutcome.SPLIT
            return False, outcome, {'approve': approve_count, 'total': total_votes}
```

#### Task 3.2: HOP API Endpoints (4 hours)

**File:** `kortana/backend/routers/autonomy.py` (HOP section)

```python
@router.post("/hop/propose")
async def propose_autonomous_action(
    action_type: str,
    parameters: Dict[str, Any],
    confidence: float,
):
    """Propose autonomous action with HOP classification."""
    hop = DistributedHOP(redis, node_id="node-1", total_nodes=3)
    
    risk_level = await hop.classify_decision(action_type, confidence)
    needs_approval = await hop.should_escalate_to_human(risk_level, confidence)
    
    decision_id = f"{action_type}_{uuid.uuid4()}"
    decision = await hop.initiate_distributed_vote(
        decision_id, action_type, risk_level, confidence
    )
    
    return {
        'decision_id': decision_id,
        'risk_level': risk_level.value,
        'requires_approval': needs_approval,
    }

@router.post("/hop/vote")
async def vote_on_decision(decision_id: str, vote: bool):
    """Cast vote on autonomous decision."""
    hop = DistributedHOP(redis, node_id="node-1", total_nodes=3)
    result = await hop.cast_vote(decision_id, "node-1", vote)
    
    if result['quorum_reached']:
        approved, outcome, details = await hop.reach_consensus(decision_id)
        if approved:
            await hop.execute_decision(decision_id, True, approved_by="consensus")
    
    return result

@router.get("/hop/consensus/{decision_id}")
async def check_consensus(decision_id: str):
    """Check consensus status on decision."""
    hop = DistributedHOP(redis, node_id="node-1", total_nodes=3)
    approved, outcome, details = await hop.reach_consensus(decision_id)
    
    return {
        'approved': approved,
        'outcome': outcome.value,
        'details': details,
    }
```

---

### Day 6: AdaptiveLearner Implementation (10 hours)

#### Task 4.1: AdaptiveLearner Service (6 hours)

**File:** `kortana/backend/services/adaptive_learning.py`

```python
# Implementation checklist:
- [x] OutcomeType enum
- [x] AdaptiveLearner class
- [x] record_decision_outcome() method
- [x] _update_type_accuracy() method
- [x] compute_improvement_potential() method
- [x] suggest_strategy_adjustment() method
- [x] apply_strategy_adjustment() method
- [x] get_learning_report() method
- [x] Time-series data storage in Redis
- [x] Accuracy calculation and caching
- [x] Strategy optimization logic

Features:
- Decision outcome tracking
- Accuracy per decision type
- Confidence calibration detection
- Strategy improvement suggestions
- Automated adjustments
```

**Implementation:**

```python
from enum import Enum
from typing import Dict, List, Any
import json

class OutcomeType(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"

class AdaptiveLearner:
    """Learn from execution outcomes and improve decisions."""
    
    def __init__(self, redis_client, db_session):
        self.redis = redis_client
        self.db = db_session
    
    async def record_decision_outcome(
        self,
        decision_id: str,
        decision_type: str,
        outcome_type: OutcomeType,
        confidence: float,
        execution_time_ms: int,
    ) -> None:
        """Record outcome of autonomous decision."""
        outcome_record = {
            'decision_id': decision_id,
            'decision_type': decision_type,
            'outcome_type': outcome_type.value,
            'confidence': confidence,
            'execution_time_ms': execution_time_ms,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        # Store in time-series
        await self.redis.lpush(
            f"decision_outcomes:{decision_type}",
            json.dumps(outcome_record)
        )
        
        # Keep last 1000 entries
        await self.redis.ltrim(
            f"decision_outcomes:{decision_type}",
            0, 999
        )
        
        # Update accuracy
        await self._update_type_accuracy(decision_type)
    
    async def _update_type_accuracy(self, decision_type: str) -> None:
        """Compute and cache accuracy for decision type."""
        outcomes = await self.redis.lrange(
            f"decision_outcomes:{decision_type}",
            0, -1
        )
        
        if not outcomes:
            return
        
        parsed = [json.loads(o) for o in outcomes]
        success_count = sum(
            1 for o in parsed
            if o['outcome_type'] == OutcomeType.SUCCESS.value
        )
        
        accuracy = success_count / len(parsed)
        avg_confidence = sum(o['confidence'] for o in parsed) / len(parsed)
        
        # Cache accuracy metrics
        await self.redis.hset(
            f"decision_type_stats:{decision_type}",
            mapping={
                'accuracy': accuracy,
                'avg_confidence': avg_confidence,
                'total_decisions': len(parsed),
                'updated_at': datetime.utcnow().isoformat(),
            }
        )
    
    async def compute_improvement_potential(
        self,
        decision_type: str
    ) -> Dict[str, Any]:
        """Compute where improvements are needed."""
        stats = await self.redis.hgetall(
            f"decision_type_stats:{decision_type}"
        )
        
        if not stats:
            return {'status': 'insufficient_data'}
        
        accuracy = float(stats[b'accuracy'])
        improvements = []
        
        if accuracy < 0.8:
            improvements.append({
                'type': 'model_improvement',
                'current_accuracy': accuracy,
                'target_accuracy': 0.95,
            })
        
        return {
            'decision_type': decision_type,
            'improvements': improvements,
        }
```

#### Task 4.2: Learning API Endpoints & Tests (4 hours)

**File:** `kortana/backend/routers/autonomy.py` (learning section)

```python
@router.post("/learning/record-outcome")
async def record_outcome(
    decision_id: str,
    decision_type: str,
    outcome_type: str,
    confidence: float,
    execution_time_ms: int,
):
    """Record outcome of autonomous decision."""
    learner = AdaptiveLearner(redis, session)
    await learner.record_decision_outcome(
        decision_id, decision_type, OutcomeType(outcome_type), confidence, execution_time_ms
    )
    return {'status': 'recorded'}

@router.get("/learning/improvements/{decision_type}")
async def get_improvements(decision_type: str):
    """Get improvement suggestions for decision type."""
    learner = AdaptiveLearner(redis, session)
    improvements = await learner.compute_improvement_potential(decision_type)
    return improvements

@router.get("/learning/report")
async def get_learning_report():
    """Get overall learning progress report."""
    learner = AdaptiveLearner(redis, session)
    report = await learner.get_learning_report()
    return report
```

---

### Day 7: GoalManager Implementation (10 hours)

#### Task 5.1: GoalManager Service (6 hours)

**File:** `kortana/backend/services/goal_manager.py`

```python
# Implementation checklist:
- [x] GoalStatus enum
- [x] GoalPriority enum
- [x] Goal dataclass
- [x] AutonomousGoalManager class
- [x] create_goal() method
- [x] decompose_goal() method
- [x] add_dependency() method
- [x] check_dependencies() method
- [x] plan_goal_execution() method
- [x] update_goal_progress() method
- [x] execute_goals() method
- [x] Redis persistence
- [x] Dependency tracking

Features:
- Hierarchical goal structures
- Goal decomposition
- Dependency management
- Progress tracking
- Autonomous execution
```

#### Task 5.2: Goal Management API & Tests (4 hours)

---

### Day 8: Integration & Testing (16 hours)

#### Task 6.1: Integration Tests (8 hours)

```python
# File: tests/integration/test_autonomy_layer.py

@pytest.mark.asyncio
async def test_full_autonomy_flow():
    """Test complete autonomy flow: propose → vote → execute."""
    
    # 1. Propose autonomous action
    decision_id = f"test_{uuid.uuid4()}"
    hop = DistributedHOP(redis, node_id="node-1", total_nodes=3)
    
    decision = await hop.initiate_distributed_vote(
        decision_id, "scale_backend", RiskLevel.HIGH, 0.85
    )
    assert decision.requires_approval
    
    # 2. Cast votes from multiple nodes
    await hop.cast_vote(decision_id, "node-1", True, "Good CPU utilization")
    await hop.cast_vote(decision_id, "node-2", True, "Confirmed high load")
    await hop.cast_vote(decision_id, "node-3", True, "Agree")
    
    # 3. Check consensus
    approved, outcome, details = await hop.reach_consensus(decision_id)
    assert approved
    assert outcome == VoteOutcome.UNANIMOUS
    
    # 4. Execute decision
    result = await hop.execute_decision(decision_id, approved)
    assert result['status'] == 'executed'

@pytest.mark.asyncio
async def test_learning_feedback_loop():
    """Test adaptive learning from decision outcomes."""
    
    learner = AdaptiveLearner(redis, session)
    decision_type = "scale_backend"
    
    # Record multiple successful outcomes
    for i in range(10):
        await learner.record_decision_outcome(
            f"decision_{i}",
            decision_type,
            OutcomeType.SUCCESS,
            0.85,
            500
        )
    
    # Check accuracy improved
    improvements = await learner.compute_improvement_potential(decision_type)
    assert improvements['status'] != 'insufficient_data'
    
    # Get improvement suggestions
    stats = await learner.redis.hgetall(
        f"decision_type_stats:{decision_type}"
    )
    accuracy = float(stats[b'accuracy'])
    assert accuracy == 1.0  # All successful
```

#### Task 6.2: End-to-End Testing (8 hours)

```
- Test full API flow through FastAPI TestClient
- Test with real Redis (docker)
- Test database persistence
- Test error scenarios
- Load testing (100 decisions/sec)
- Stress testing (connection limits)
```

---

## Week 1 Deliverables

### Code
- ✅ `services/self_awareness.py` (400+ lines, 85%+ test coverage)
- ✅ Enhanced `human_only_protocol.py` (500+ lines)
- ✅ `services/adaptive_learning.py` (300+ lines)
- ✅ `services/goal_manager.py` (350+ lines)
- ✅ `routers/autonomy.py` (200+ lines, 6 endpoints)

### Tests
- ✅ `tests/unit/services/test_self_awareness.py` (100+ tests)
- ✅ `tests/unit/services/test_adaptive_learning.py` (50+ tests)
- ✅ `tests/unit/services/test_goal_manager.py` (50+ tests)
- ✅ `tests/integration/test_autonomy_layer.py` (30+ tests)
- ✅ `tests/load/test_autonomy_performance.py` (10+ tests)

### Documentation
- ✅ API documentation (OpenAPI/Swagger)
- ✅ Architecture decision record (ADR)
- ✅ Code comments (docstrings)

### Metrics
- Lines of Code: ~1,550
- Test Coverage: 85%+
- API Endpoints: 6
- Services: 4

---

# WEEK 2: PERFORMANCE OPTIMIZATION BLUEPRINT

## Overview
**Goal:** Achieve 5x throughput, 67% latency reduction  
**Duration:** 40 hours  
**Focus:** Database, API, task processing optimization  

## Performance Baseline (Before)
```
- P95 Latency: 750ms
- Task Throughput: 10 tasks/min
- DB Query Time: 200ms average
- API Endpoints: ~15
- Concurrent Users: 50
```

## Performance Targets (After)
```
- P95 Latency: 250ms (67% reduction)
- Task Throughput: 50 tasks/min (5x)
- DB Query Time: 60ms average (70% reduction)
- Connection Pool: 20 → 40 connections
- Concurrent Users: 50 → 500 (10x)
```

---

## Task 1: Database Connection Pooling (4 hours)

### Current Issue
```python
# BEFORE: Direct connections, no pooling
engine = create_async_engine(DATABASE_URL)
# Results: Connection exhaustion at ~50 concurrent users
```

### Solution: PgBouncer Connection Pooling

```yaml
# docker-compose.yml addition
services:
  pgbouncer:
    image: pgbouncer:latest
    environment:
      PGBOUNCER_DATABASES: "kortana_dev=host=postgres port=5432 user=kortana password=dev_password dbname=kortana_dev"
      PGBOUNCER_POOL_MODE: "transaction"
      PGBOUNCER_MAX_CLIENT_CONN: "200"
      PGBOUNCER_DEFAULT_POOL_SIZE: "25"
    ports:
      - "6432:6432"
    depends_on:
      - postgres
```

```python
# backend/database.py - AFTER optimization
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import AsyncQueuePool

engine = create_async_engine(
    "postgresql+asyncpg://kortana:dev_password@pgbouncer:6432/kortana_dev",
    echo=False,
    poolclass=AsyncQueuePool,
    pool_size=20,           # Base connections
    max_overflow=20,        # Additional connections
    pool_timeout=30,        # Wait timeout
    pool_recycle=3600,      # Recycle after 1 hour
    pool_pre_ping=True,     # Test before use
)

@asynccontextmanager
async def get_db_session():
    """Get database session with timeout."""
    try:
        session = AsyncSession(engine)
        yield session
    finally:
        await session.close()
```

**Expected Improvement:**
- Connection pool efficiency: 300% improvement
- Connection wait time: Eliminated
- Concurrent user support: 50 → 500

---

## Task 2: N+1 Query Fixes (10 hours)

### Identify N+1 Issues

```bash
# Enable query logging to detect N+1 issues
# Set SQLALCHEMY_ECHO=true in .env.development

# Run test and count queries
# Expected: Many duplicate queries = N+1 problem
```

### Example Fix: Agents Router

```python
# BEFORE: N+1 Query Problem
@router.get("/agents")
async def list_agents(session: AsyncSession):
    """List agents - N+1 query issue!"""
    result = await session.execute(select(Agent))
    agents = result.scalars().all()
    
    # This triggers N+1 queries!
    return [
        {
            'id': agent.id,
            'name': agent.name,
            'execution_count': len(agent.executions),  # ← Query N+1 times!
            'owner': agent.owner.name,  # ← Query N+2 times!
        }
        for agent in agents
    ]

# AFTER: Eager Loading with selectinload
from sqlalchemy.orm import selectinload

@router.get("/agents")
async def list_agents(
    session: AsyncSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """List agents - optimized with eager loading."""
    query = select(Agent).options(
        selectinload(Agent.executions),
        selectinload(Agent.owner),
    ).offset(skip).limit(limit)
    
    result = await session.execute(query)
    agents = result.scalars().unique().all()
    
    # Now no additional queries!
    return [
        {
            'id': agent.id,
            'name': agent.name,
            'execution_count': len(agent.executions),  # No query
            'owner': agent.owner.name,  # No query
        }
        for agent in agents
    ]
```

### N+1 Fixes Checklist
```
- [ ] agents.py - list_agents() endpoint
- [ ] agents.py - get_agent() endpoint
- [ ] memory.py - list_memories() endpoint
- [ ] executions.py - list_executions() endpoint
- [ ] tasks.py - list_tasks() endpoint
- [ ] code_reviews.py - list_reviews() endpoint
- [ ] tests for all fixes
- [ ] query count verification
```

**Expected Improvement:**
- Database query count: 100+ → 5
- Query time: 200ms → 60ms per request
- Latency: 50% reduction

---

## Task 3: Redis Caching Layer (8 hours)

### Cache Strategy

```python
# File: kortana/backend/services/cache_service.py

from functools import wraps
import json

class CacheService:
    """Redis caching service for expensive operations."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> None:
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        await self.redis.setex(
            key,
            ttl,
            json.dumps(value, default=str)
        )
    
    async def delete(self, key: str) -> None:
        """Delete from cache."""
        await self.redis.delete(key)
    
    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate cache by pattern."""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

def cache_result(key_prefix: str, ttl: int = 300):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{args}:{kwargs}"
            
            # Try to get from cache
            cached = await cache.get(cache_key)
            if cached:
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
```

### Apply Caching to Endpoints

```python
# File: kortana/backend/routers/agents.py

@router.get("/agents/{agent_id}")
@cache_result(key_prefix="agent", ttl=600)
async def get_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
):
    """Get agent details - cached 10 minutes."""
    # Query database
    result = await session.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent

# Invalidate cache when agent is updated
@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    update: AgentUpdate,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
):
    """Update agent and invalidate cache."""
    agent = await session.get(Agent, agent_id)
    
    # Update
    for field, value in update.dict(exclude_unset=True).items():
        setattr(agent, field, value)
    
    await session.commit()
    
    # Invalidate cache
    await cache.invalidate_pattern(f"agent:{agent_id}:*")
    
    return agent
```

**Expected Improvement:**
- Cache hit rate: 60%+
- API response time: 200ms → 50ms
- Database load: 40% reduction

---

## Task 4: API Response Optimization (6 hours)

### Pagination

```python
# File: kortana/backend/routers/base.py

from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginationParams(BaseModel):
    skip: int = Query(0, ge=0)
    limit: int = Query(10, ge=1, le=100)

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool

@router.get("/agents", response_model=PaginatedResponse[AgentResponse])
async def list_agents(
    params: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_db),
):
    """List agents with pagination."""
    # Get total count
    count_result = await session.execute(
        select(func.count()).select_from(Agent)
    )
    total = count_result.scalar()
    
    # Get paginated items
    query = select(Agent).offset(params.skip).limit(params.limit)
    result = await session.execute(query)
    items = result.scalars().all()
    
    return PaginatedResponse(
        items=[AgentResponse.from_orm(item) for item in items],
        total=total,
        skip=params.skip,
        limit=params.limit,
        has_more=(params.skip + params.limit) < total,
    )
```

### Response Compression

```python
# File: kortan/backend/main.py

from fastapi.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

### Field Selection (Sparse Fieldsets)

```python
# Allow clients to request only needed fields
@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    fields: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
):
    """Get agent with optional field selection.
    
    Usage: GET /agents/123?fields=id,name,status
    """
    agent = await session.get(Agent, agent_id)
    
    if fields:
        requested_fields = set(fields.split(','))
        available_fields = set(agent.__dict__.keys())
        selected_fields = requested_fields & available_fields
        
        return {k: getattr(agent, k) for k in selected_fields}
    
    return agent
```

**Expected Improvement:**
- Response size: 30% reduction (compression)
- Bandwidth: 30% reduction (sparse fieldsets)
- Client processing: 20% faster

---

## Task 5: Celery Task Queue Implementation (12 hours)

### Replace Custom Queue with Celery

```python
# File: kortana/backend/celery_app.py

from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    'kortana',
    broker='redis://redis:6379/1',
    backend='redis://redis:6379/2',
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes warning
    worker_concurrency=4,
    worker_prefetch_multiplier=4,
    result_expires=3600,
)

# Define tasks
@celery_app.task(bind=True, max_retries=3)
def execute_agent_task(self, agent_id: str, task_data: dict):
    """Execute agent task with retry logic."""
    try:
        # Task implementation
        logger.info(f"Executing task for agent {agent_id}")
        
        # Simulate work
        result = process_task(task_data)
        
        return {'status': 'success', 'result': result}
    
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        # Exponential backoff retry
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

# Schedule periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-old-executions': {
        'task': 'tasks.cleanup_old_executions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'health-check': {
        'task': 'tasks.health_check',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
```

### Update FastAPI Integration

```python
# File: kortana/backend/routers/tasks.py

from kortana.backend.celery_app import execute_agent_task

@router.post("/tasks/agent/{agent_id}/execute")
async def execute_task(
    agent_id: str,
    task_data: dict,
):
    """Queue agent task for background execution."""
    # Queue task
    task = execute_agent_task.delay(agent_id, task_data)
    
    return {
        'task_id': task.id,
        'status': 'queued',
    }

@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get task status."""
    from celery.result import AsyncResult
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    return {
        'task_id': task_id,
        'status': task_result.status,
        'result': task_result.result if task_result.ready() else None,
    }
```

### Docker Compose Update

```yaml
services:
  celery_worker:
    build: ./kortana/backend
    command: celery -A celery_app worker --loglevel=info --concurrency=4
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      - redis
      - postgres

  celery_beat:
    build: ./kortana/backend
    command: celery -A celery_app beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      - redis
```

**Expected Improvement:**
- Task throughput: 10/min → 50/min (5x)
- Response time: Offload to workers
- Concurrent tasks: Unlimited scaling

---

## Week 2 Deliverables

### Code Changes
- ✅ Database connection pooling (PgBouncer)
- ✅ N+1 query fixes (6+ endpoints)
- ✅ Redis caching layer (CacheService)
- ✅ API pagination (all list endpoints)
- ✅ Response compression (GZIPMiddleware)
- ✅ Celery task queue (with retries)

### Performance Improvements
- P95 Latency: 750ms → 250ms ✅
- Task Throughput: 10/min → 50/min ✅
- Query Time: 200ms → 60ms ✅
- Database Load: -40% ✅

### Tests
- ✅ Performance benchmarks
- ✅ Load testing (100 concurrent users)
- ✅ Cache invalidation tests
- ✅ Task retry logic tests

---

# WEEK 3: CONTAINER OPTIMIZATION BLUEPRINT

## Overview
**Goal:** 70% faster builds, 60% smaller images  
**Duration:** 20 hours  

## Optimization Targets
```
Backend Build Time: 150s → 45s
Backend Image Size: 500MB → 150MB
Frontend Build Time: 120s → 30s
Frontend Image Size: 280MB → 120MB
```

---

## Task 1: Backend Multi-Stage Dockerfile (6 hours)

### Current Dockerfile Issues
```dockerfile
# BEFORE: Single-stage, includes dev dependencies
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt      # Includes dev deps!
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app"]

# Result: 500MB, slow startup
```

### Optimized Multi-Stage Build

```dockerfile
# File: kortana/backend/Dockerfile

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages to user directory (no root)
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime (lean image)
FROM python:3.11-slim-alpine

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Set PATH
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Non-root user
RUN adduser -D -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/health', timeout=5)"

EXPOSE 8000

# Startup script with graceful shutdown
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--timeout-graceful-shutdown", "30"]

# Build metadata
LABEL org.opencontainers.image.title="Kor'tana Backend" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.source="https://github.com/kor-tana"
```

### .dockerignore Optimization

```
# File: kortana/backend/.dockerignore

# Version control
.git
.gitignore
.github

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
.pytest_cache/
.coverage
htmlcov/

# IDEs
.vscode
.idea
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project
.env
.env.local
.env.*.local
venv/
ENV/

# CI/CD
.gitlab-ci.yml
.travis.yml

# Documentation
docs/
*.md
!README.md
```

**Expected Improvement:**
- Image size: 500MB → 150MB (67% smaller)
- Build time: 60s → 20s
- Build cache efficiency: 80%+

---

## Task 2: Frontend Multi-Stage Build (6 hours)

### Optimized React Build

```dockerfile
# File: kortana/frontend/Dockerfile

# Stage 1: Dependencies
FROM node:20-alpine as dependencies

WORKDIR /app

COPY package*.json ./

RUN npm ci --only=production

# Stage 2: Build
FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./

# Install all dependencies (including dev)
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# Stage 3: Runtime
FROM node:20-alpine

WORKDIR /app

# Copy built assets from builder
COPY --from=builder /app/dist ./dist

# Copy node_modules from dependencies
COPY --from=dependencies /app/node_modules ./node_modules

# Copy package.json for preview server
COPY package*.json ./

# Non-root user
RUN addgroup -g 1000 appuser && \
    adduser -u 1000 -G appuser -s /bin/sh -D appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["npm", "run", "preview"]

LABEL org.opencontainers.image.title="Kor'tana Frontend" \
      org.opencontainers.image.version="1.0.0"
```

### Frontend .dockerignore

```
# File: kortana/frontend/.dockerignore

node_modules
npm-debug.log
.next
out
.vscode
.idea
dist
build
.env.local
.DS_Store
*.swp
```

### Vite Optimization

```typescript
// File: kortana/frontend/vite.config.ts

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  
  build: {
    // Optimization
    minify: 'terser',
    sourcemap: false,  // Disable in production
    
    // Code splitting
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom'],
          'ui': ['@mui/material'],
        }
      }
    },
    
    // Treeshake
    treeshake: true,
  },
  
  // Preview server
  preview: {
    port: 3000,
    strictPort: false,
  }
})
```

**Expected Improvement:**
- Image size: 280MB → 120MB (57% smaller)
- Build time: 120s → 30s (75% faster)
- Startup time: 10s → 2s

---

## Task 3: BuildKit & Caching Optimization (4 hours)

### Enable BuildKit

```bash
# File: .buildkitrc

export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain
```

### Optimized docker-compose build

```bash
#!/bin/bash
# scripts/build-optimized.sh

set -e

echo "🏗️  Building Kor'tana with BuildKit..."

# Backend
DOCKER_BUILDKIT=1 docker build \
  -t kortana-backend:latest \
  -t kortana-backend:$(git rev-parse --short HEAD) \
  -f kortana/backend/Dockerfile \
  --cache-from=kortana-backend:latest \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  kortana/backend/

# Frontend  
DOCKER_BUILDKIT=1 docker build \
  -t kortana-frontend:latest \
  -t kortana-frontend:$(git rev-parse --short HEAD) \
  -f kortana/frontend/Dockerfile \
  --cache-from=kortana-frontend:latest \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  kortana/frontend/

echo "✅ Build complete"
```

### Parallel Builds

```yaml
# File: Makefile

.PHONY: build build-backend build-frontend build-parallel

build: build-parallel

build-parallel:
	$(MAKE) -j2 build-backend build-frontend

build-backend:
	DOCKER_BUILDKIT=1 docker build -t kortana-backend:latest ./kortana/backend

build-frontend:
	DOCKER_BUILDKIT=1 docker build -t kortana-frontend:latest ./kortana/frontend
```

**Expected Improvement:**
- Parallel builds: 2x faster
- Cache reuse: 80% hit rate
- Incremental builds: 85% faster

---

## Task 4: Image Registry Optimization (4 hours)

### Slim Down Images Further

```dockerfile
# Use distroless for even smaller images
FROM gcr.io/distroless/python3.11-nonroot

# OR use Alpine with minimal packages
FROM alpine:latest
RUN apk add --no-cache python3.11
```

### Image Scanning & Cleanup

```bash
#!/bin/bash
# scripts/optimize-images.sh

# Analyze image size
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive:latest kortana-backend:latest

# Remove dangling images
docker image prune -a --filter "until=72h"

# Push to registry with compression
docker push kortana-backend:latest
```

---

## Week 3 Deliverables

### Docker Files
- ✅ Optimized `kortana/backend/Dockerfile`
- ✅ Optimized `kortana/frontend/Dockerfile`
- ✅ `.dockerignore` files
- ✅ `docker-compose.yml` updates

### Build Scripts
- ✅ `scripts/build-optimized.sh`
- ✅ `Makefile` with parallel builds
- ✅ Build verification scripts

### Performance Improvements
- Backend image: 500MB → 150MB ✅
- Frontend image: 280MB → 120MB ✅
- Build time: 150s → 45s ✅
- Build cache efficiency: 80%+ ✅

---

# WEEK 4: OBSERVABILITY BLUEPRINT

## Overview
**Goal:** Complete visibility into system behavior  
**Duration:** 35 hours  

## Observability Stack
```
Metrics:      Prometheus
Dashboards:   Grafana
Tracing:      Jaeger + OpenTelemetry
Logging:      ELK (Elasticsearch, Logstash, Kibana)
Alerts:       Alertmanager
```

---

## Task 1: Prometheus Metrics (15 hours)

### Instrumentation

```python
# File: kortana/backend/middleware/metrics.py

from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

active_tasks = Gauge(
    'active_background_tasks',
    'Number of currently executing tasks'
)

task_execution_time = Histogram(
    'task_execution_seconds',
    'Task execution duration',
    ['task_type'],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0)
)

database_query_time = Histogram(
    'database_query_seconds',
    'Database query duration',
    ['query_type'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0)
)

# Middleware for automatic collection
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

### Celery Task Metrics

```python
# Track Celery tasks
@celery_app.task
def execute_task(task_id: str):
    active_tasks.inc()
    start = time.time()
    
    try:
        # Task implementation
        result = do_work()
        duration = time.time() - start
        task_execution_time.labels(task_type='execute_task').observe(duration)
    finally:
        active_tasks.dec()
```

### Prometheus Configuration

```yaml
# File: prometheus/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
```

### Docker Compose Update

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  postgres_exporter:
    image: prometheuscommunity/postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://kortana:password@postgres:5432/kortana"
    ports:
      - "9187:9187"
    depends_on:
      - postgres

  redis_exporter:
    image: oliver006/redis_exporter
    command: -redis-addr redis:6379
    ports:
      - "9121:9121"
    depends_on:
      - redis
```

---

## Task 2: Grafana Dashboards (5 hours)

### Dashboard 1: System Health

```json
{
  "dashboard": {
    "title": "System Health Overview",
    "panels": [
      {
        "title": "CPU Usage",
        "targets": [{
          "expr": "rate(container_cpu_usage_seconds_total[5m]) * 100"
        }]
      },
      {
        "title": "Memory Usage",
        "targets": [{
          "expr": "container_memory_usage_bytes / 1024 / 1024"
        }]
      },
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(http_requests_total[1m])"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m])"
        }]
      }
    ]
  }
}
```

### Dashboard 2: API Performance

```
- Request latency (P50, P95, P99)
- Endpoint throughput
- Response times by endpoint
- Active connections
```

### Dashboard 3: Database Performance

```
- Query execution time
- Query count per second
- Connection pool usage
- Cache hit rate
```

### Dashboard 4: Background Tasks

```
- Active task count
- Task throughput
- Task duration histogram
- Failed task rate
- Queue depth
```

---

## Task 3: Distributed Tracing with Jaeger (12 hours)

### OpenTelemetry Integration

```python
# File: kortana/backend/tracing.py

from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

def init_tracing():
    """Initialize distributed tracing."""
    
    # Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    
    # Tracer provider
    trace_provider = TracerProvider()
    trace_provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    
    trace.set_tracer_provider(trace_provider)
    
    # Auto-instrumentation
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()

# Usage in code
tracer = trace.get_tracer(__name__)

async def process_request(request_id: str):
    with tracer.start_as_current_span("process_request") as span:
        span.set_attribute("request.id", request_id)
        
        # Processing logic
        result = await do_work()
        
        span.set_attribute("result.status", "success")
        return result
```

### Jaeger Docker Compose

```yaml
services:
  jaeger:
    image: jaegertracing/all-in-one
    ports:
      - "5775:5775/udp"
      - "6831:6831/udp"
      - "16686:16686"  # UI
    environment:
      COLLECTOR_ZIPKIN_HOST_PORT: ":9411"
```

---

## Task 4: ELK Log Aggregation (8 hours)

### Structured Logging

```python
# File: kortana/backend/logging_config.py

import logging
import json
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Setup JSON structured logging."""
    
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Usage
logger = logging.getLogger(__name__)

logger.info("Processing request", extra={
    'request_id': request_id,
    'user_id': user_id,
    'duration_ms': duration,
})
```

### ELK Stack Docker Compose

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.0.0
    user: root
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

---

## Week 4 Deliverables

### Monitoring Setup
- ✅ Prometheus metrics (50+ custom metrics)
- ✅ Prometheus configuration
- ✅ Grafana (12+ dashboards)
- ✅ Jaeger distributed tracing
- ✅ ELK log aggregation

### Dashboards Created
- ✅ System health overview
- ✅ API performance
- ✅ Database performance
- ✅ Background tasks
- ✅ Error tracking
- ✅ SLA compliance

### Integrations
- ✅ FastAPI instrumentation
- ✅ SQLAlchemy instrumentation
- ✅ Celery task tracking
- ✅ Custom business metrics

---

# WEEKS 5-6: SCALABILITY & PRODUCTION HARDENING

(Due to length limits, detailed blueprints for Weeks 5-6 follow similar pattern)

## Week 5: Scalability (32 hours)
- Load balancing (nginx)
- Database replication
- Redis clustering
- Session management

## Week 6: Production Hardening (40 hours)
- Security hardening
- Reliability patterns
- Backup & recovery
- Compliance

---

# TESTING STRATEGY

## Test Pyramid

```
        /\
       /  \  E2E Tests (10%)
      /----\
     /      \ Integration Tests (30%)
    /--------\
   /          \ Unit Tests (60%)
  /____________\
```

### Unit Testing (60%)
```python
# Test each service method independently
# Target: 85%+ coverage
# Tools: pytest, pytest-cov, hypothesis

pytest tests/unit/ -v --cov=kortana --cov-report=html
```

### Integration Testing (30%)
```python
# Test service interactions
# Target: 70%+ coverage
# Use test database, Redis mock

pytest tests/integration/ -v --cov=kortana
```

### E2E Testing (10%)
```python
# Test full API flows
# Use Selenium/Playwright for frontend
# Tools: pytest, requests

pytest tests/e2e/ -v
```

---

# CI/CD PIPELINE

## GitHub Actions Workflow

```yaml
# .github/workflows/test-and-deploy.yml

name: Test & Deploy

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
      redis:
        image: redis:7
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r kortana/backend/requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: pytest tests/ -v --cov=kortana
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Build images
        run: |
          docker build -t kortana-backend:${{ github.sha }} ./kortana/backend
          docker build -t kortana-frontend:${{ github.sha }} ./kortana/frontend
      
      - name: Push to registry
        run: |
          docker push kortana-backend:${{ github.sha }}
          docker push kortana-frontend:${{ github.sha }}
```

---

# CODE REVIEW STANDARDS

## Before Merging

- [ ] 85%+ test coverage
- [ ] Type hints on all public methods
- [ ] Docstrings (Google style)
- [ ] No breaking changes (or proper versioning)
- [ ] Security review (OWASP, SQLi prevention)
- [ ] Performance impact < 5%
- [ ] Code style (Black, Ruff, Pylint)

---

# DEPLOYMENT PROCEDURES

## Local Development

```bash
make dev
# Services start on:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:3000
# - API Docs: http://localhost:8000/docs
```

## Staging Deployment

```bash
# Deploy to staging server
make deploy-staging

# Verify
curl https://staging-api.kor-tana.example.com/api/health
```

## Production Deployment

```bash
# Blue-green deployment
make deploy-prod-blue-green

# Verify
curl https://api.kor-tana.example.com/api/health

# Monitor for 5 minutes
watch -n 5 'curl -s https://api.kor-tana.example.com/api/health | jq'

# Finalize (cleanup old version)
make finalize-prod-deployment
```

---

## SUMMARY

This development guide provides:

✅ **Complete setup instructions** - Environment, dependencies, configuration  
✅ **Week-by-week blueprints** - Detailed tasks, code examples, deliverables  
✅ **Implementation patterns** - Proven approaches, best practices  
✅ **Testing strategies** - Unit, integration, E2E, performance  
✅ **CI/CD pipeline** - Automated build, test, deploy  
✅ **Deployment procedures** - Local, staging, production  

**Ready to start implementation!**

---

**Version:** 1.0  
**Status:** Complete and ready for development  
**Last Updated:** 2026
