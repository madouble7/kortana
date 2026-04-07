# Kor'tana: Developer Quick Start Guide
## Get Up to Speed in 30 Minutes

---

## 📖 READ THIS FIRST (5 minutes)

### What is Kor'tana?
Advanced autonomous AI system with multi-agent coordination, human oversight protocols, and self-awareness capabilities.

### What are we optimizing?
- **Autonomy:** Add true self-awareness and distributed decision-making
- **Performance:** 5x faster (250ms latency, 50 tasks/min)
- **Scalability:** 100x more users (50 → 5,000 concurrent)
- **Operations:** Full observability and production readiness

### Timeline
6 weeks, 2 developers (1 senior, 1 mid-level), $152.5k investment

### Expected Outcome
1155% ROI, world's most autonomous AI with 99.9% SLA

---

## 🛠️ SETUP (10 minutes)

### Prerequisites
```bash
# Check installed versions
python --version          # Need: 3.11+
node --version            # Need: 20+
docker --version          # Need: latest
git --version             # Need: 2.40+
```

### Clone & Setup
```bash
cd c:\kor-tana\kortana

# Copy environment
cp ../.env.example ../.env

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio

# Frontend dependencies
cd ../frontend
npm install
```

### Start Services
```bash
# From c:\kor-tana\kortana
docker-compose up -d

# Verify running
docker-compose ps

# Expected output:
# kortana-postgres      Up (healthy)
# kortana-redis         Up (healthy)
# kortana-backend       Up (healthy)
# kortana-frontend      Up (healthy)
```

### Verify Access
```bash
# Backend API
curl http://localhost:8000/api/health

# Frontend
open http://localhost:3000

# API Docs
open http://localhost:8000/docs
```

---

## 📚 DOCUMENTATION MAP (5 minutes)

### By Role

**If you're a Developer:**
1. Read this file (you are here) ✓
2. Read: `DEVELOPMENT_GUIDE_AND_BLUEPRINT.md` (65 KB)
3. Read: `IMPLEMENTATION_CHECKLIST_WEEKLY.md` (21 KB)
4. Start coding from Week 1 examples

**If you're a DevOps:**
1. Read: `QUICK_REFERENCE_GUIDE.md` (10 KB)
2. Read: `PRODUCTION_DEPLOYMENT_GUIDE.md` (19 KB)
3. Prepare infrastructure for Week 3+

**If you're an Architect:**
1. Read: `COMPREHENSIVE_AUDIT_AND_OPTIMIZATION.md` (33 KB)
2. Read: `DEVELOPMENT_GUIDE_AND_BLUEPRINT.md` (65 KB)
3. Review architecture decisions in both

**If you're a Manager:**
1. Read: `QUICK_REFERENCE_GUIDE.md` (10 KB)
2. Read: `EXECUTIVE_SUMMARY_AND_NEXT_STEPS.md` (16 KB)
3. Track using `IMPLEMENTATION_CHECKLIST_WEEKLY.md`

---

## 💻 FIRST CODING TASK: Week 1, Day 1 (30 minutes)

### Create Feature Branch
```bash
git checkout -b feature/autonomy-layer
```

### Create Core File Structure
```bash
cd c:\kor-tana\kortana\backend

# Create autonomy service files
mkdir -p services/autonomy
touch services/self_awareness.py
touch services/adaptive_learning.py
touch services/goal_manager.py
touch routers/autonomy.py

# Create test files
mkdir -p tests/unit/services/autonomy
touch tests/unit/services/autonomy/__init__.py
touch tests/unit/services/autonomy/test_self_awareness.py
```

### Create First Class: SelfAwarenessEngine

**File:** `services/self_awareness.py`

```python
"""Self-awareness engine for autonomous system monitoring.

This module provides Kor'tana with introspection capabilities,
enabling real-time assessment of system state and health.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SystemState(Enum):
    """System operational state."""
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    RECOVERING = "recovering"

@dataclass
class PerformanceMetrics:
    """Current system performance snapshot."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    request_latency_ms: float
    active_tasks: int
    error_rate: float

class SelfAwarenessEngine:
    """Monitor and assess system self-awareness and health.
    
    Responsibilities:
    - Collect system metrics
    - Assess current state
    - Compute decision confidence
    - Detect performance degradation
    - Plan corrective actions
    """
    
    def __init__(self, redis_client, db_session):
        """Initialize awareness engine.
        
        Args:
            redis_client: Redis client for caching metrics
            db_session: Database session for persistence
        """
        self.redis = redis_client
        self.db = db_session
        self.baseline_metrics = None
    
    async def assess_system_state(self) -> SystemState:
        """Assess current system operational state.
        
        Returns:
            SystemState indicating health (NOMINAL, DEGRADED, etc.)
        
        Raises:
            RuntimeError: If metrics collection fails
        """
        logger.info("Assessing system state")
        
        try:
            metrics = await self._collect_metrics()
            
            # Assess based on metrics
            if metrics.cpu_usage > 80 or metrics.memory_usage > 85:
                logger.warning("System degraded: high resource usage")
                return SystemState.DEGRADED
            
            if metrics.error_rate > 0.05:
                logger.error("System critical: high error rate")
                return SystemState.CRITICAL
            
            return SystemState.NOMINAL
            
        except Exception as e:
            logger.error(f"Failed to assess state: {e}")
            raise RuntimeError(f"State assessment failed: {e}")
    
    async def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current system metrics.
        
        Returns:
            PerformanceMetrics snapshot
        """
        # TODO: Implement metric collection
        # Connect to Prometheus, collect CPU, memory, latency
        return PerformanceMetrics(
            timestamp=datetime.utcnow(),
            cpu_usage=45.0,
            memory_usage=60.0,
            request_latency_ms=250.0,
            active_tasks=5,
            error_rate=0.001,
        )
    
    async def compute_confidence_score(
        self,
        decision: Dict[str, Any],
    ) -> float:
        """Compute confidence in a decision.
        
        Args:
            decision: Decision dict with 'certainty', 'data_quality', etc.
        
        Returns:
            Confidence score (0.0-1.0)
        """
        factors = {
            'certainty': decision.get('certainty', 0.5),
            'data_quality': decision.get('data_quality', 0.8),
            'system_health': 0.9 if await self.assess_system_state() == SystemState.NOMINAL else 0.5,
        }
        
        # Weighted average
        score = sum(factors.values()) / len(factors)
        logger.info(f"Decision confidence: {score:.2f}")
        return score
```

### Create First Test

**File:** `tests/unit/services/autonomy/test_self_awareness.py`

```python
"""Tests for SelfAwarenessEngine."""

import pytest
from datetime import datetime
from kortana.backend.services.self_awareness import (
    SelfAwarenessEngine, SystemState, PerformanceMetrics
)

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    class MockRedis:
        async def get(self, key):
            return None
        async def set(self, key, value, ttl=None):
            pass
    return MockRedis()

@pytest.fixture
def mock_db():
    """Mock database session."""
    class MockDB:
        pass
    return MockDB()

@pytest.fixture
def engine(mock_redis, mock_db):
    """Create engine instance."""
    return SelfAwarenessEngine(mock_redis, mock_db)

@pytest.mark.asyncio
async def test_assess_system_state_nominal(engine):
    """Test nominal system state assessment."""
    state = await engine.assess_system_state()
    assert state == SystemState.NOMINAL

@pytest.mark.asyncio
async def test_compute_confidence_score(engine):
    """Test confidence score computation."""
    decision = {
        'certainty': 0.9,
        'data_quality': 0.95,
    }
    confidence = await engine.compute_confidence_score(decision)
    
    # Score should be between 0 and 1
    assert 0.0 <= confidence <= 1.0
    # Score should be high with good inputs
    assert confidence > 0.7
```

### Run Tests
```bash
cd c:\kor-tana\kortana

pytest tests/unit/services/autonomy/test_self_awareness.py -v

# Expected output:
# PASSED test_assess_system_state_nominal
# PASSED test_compute_confidence_score
```

---

## 🚀 NEXT STEPS

### Daily Workflow
```bash
# Start each day
docker-compose up -d

# Work on your task (see IMPLEMENTATION_CHECKLIST_WEEKLY.md)

# Run tests before committing
pytest tests/unit/ -v --cov=kortana

# Commit with message
git commit -m "Implement SelfAwarenessEngine.assess_system_state()"

# Create pull request
git push origin feature/autonomy-layer
```

### Weekly Cadence
1. **Monday:** Week planning (checklist review, task assignment)
2. **Tue-Thu:** Implementation (daily 15-min standups)
3. **Friday:** Integration testing & review
4. **Friday afternoon:** Merge to main if approved

### When Stuck
```
1. Check the IMPLEMENTATION_CHECKLIST_WEEKLY.md for task details
2. Review code examples in DEVELOPMENT_GUIDE_AND_BLUEPRINT.md
3. Ask in team Slack (ping senior dev)
4. Create issue on GitHub with:
   - What you're trying to do
   - What's happening (error message)
   - What you've tried
```

---

## 📊 KEY FILES TO KNOW

### Backend Structure
```
kortana/backend/
├── services/              ← Business logic (implement here)
│   ├── self_awareness.py  ← Week 1
│   ├── adaptive_learning.py  ← Week 1
│   └── goal_manager.py    ← Week 1
├── routers/               ← API endpoints (implement here)
│   └── autonomy.py        ← Week 1
├── models/                ← Database models (reference)
├── middleware/            ← Request/response processing
├── main.py                ← FastAPI app entry point
└── requirements.txt       ← Python dependencies
```

### Frontend Structure
```
kortana/frontend/
├── src/
│   ├── pages/             ← Page components
│   ├── components/        ← Reusable components
│   ├── services/          ← API calls
│   └── App.tsx            ← Root component
├── package.json           ← Dependencies
└── vite.config.ts         ← Build config
```

### Test Structure
```
tests/
├── unit/                  ← Single function tests
│   └── services/
├── integration/           ← Multi-component tests
├── smoke/                 ← Basic health checks
└── load/                  ← Performance tests
```

---

## 🧪 TESTING COMMANDS

### Run All Tests
```bash
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=kortana --cov-report=html
```

### Run Specific Test
```bash
# By file
pytest tests/unit/services/autonomy/test_self_awareness.py -v

# By test name
pytest tests/unit/services/autonomy/test_self_awareness.py::test_assess_system_state_nominal -v

# By pattern
pytest tests/unit -k "autonomy" -v
```

### Watch Mode (auto-rerun)
```bash
pytest-watch tests/ -v
```

---

## 🔍 DEBUGGING

### Backend Debug Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Variable value: {my_var}")
logger.info(f"Processing request: {request_id}")
logger.warning(f"Deprecated API: {endpoint}")
logger.error(f"Failed to process: {error}")
```

### Check API Response
```bash
curl -X GET http://localhost:8000/api/health | jq
curl -X POST http://localhost:8000/api/autonomy/self-awareness/assess \
  -H "Content-Type: application/json" \
  -d '{}' | jq
```

### Database Debug
```bash
# Connect to database
docker-compose exec postgres psql -U kortana -d kortana_dev

# List tables
\dt

# Sample query
SELECT * FROM agents LIMIT 5;
```

### View Logs
```bash
# Backend logs
docker-compose logs -f backend

# All logs
docker-compose logs -f

# Specific lines
docker-compose logs backend | tail -20
```

---

## 📋 WEEK 1 DAILY GUIDE

### Day 1-2: Setup & Planning
```
✓ Clone repo, set up dev environment
✓ Read architecture decision record
✓ Create feature branch
✓ Understand requirements
```

### Day 3-4: SelfAwarenessEngine
```
✓ Create services/self_awareness.py (400 lines)
✓ Implement 8 methods
✓ Write unit tests (50+ test cases)
✓ Achieve 85%+ coverage
```

### Day 5: Enhanced HOP
```
✓ Update human_only_protocol.py
✓ Add distributed voting
✓ Implement consensus algorithm
✓ Write tests
```

### Day 6: AdaptiveLearner
```
✓ Create services/adaptive_learning.py (300 lines)
✓ Track decision outcomes
✓ Compute accuracy
✓ Suggest improvements
```

### Day 7: GoalManager
```
✓ Create services/goal_manager.py (350 lines)
✓ Hierarchical goal management
✓ Dependency tracking
✓ Tests
```

### Day 8: Integration & Testing
```
✓ Write integration tests
✓ Verify end-to-end flow
✓ Load test (100 decisions/sec)
✓ Code review & merge
```

---

## 💡 CODING TIPS

### Follow Patterns
Use existing patterns in codebase:
- Router pattern: See `routers/agents.py`
- Service pattern: See `services/agent_service.py`
- Test pattern: See `tests/unit/services/`

### Type Hints
```python
# Always use type hints
async def process_task(task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Process a task.
    
    Args:
        task_id: Unique task identifier
        params: Processing parameters
    
    Returns:
        Result dictionary with status and data
    """
    pass
```

### Async/Await
```python
# Use async/await for I/O operations
async def fetch_agent(agent_id: str) -> Agent:
    """Fetch agent from database."""
    result = await session.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    return result.scalar_one_or_none()
```

### Error Handling
```python
try:
    result = await risky_operation()
    logger.info(f"Success: {result}")
except ValueError as e:
    logger.error(f"Invalid input: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 🎯 SUCCESS METRICS

### Week 1 Target
- 1,550+ lines of new code
- 83%+ test coverage
- 6 new API endpoints
- 0 critical bugs
- Code review approved

### How to Verify
```bash
# Check line count
find services routers -name "*.py" | xargs wc -l

# Check coverage
pytest --cov=kortana --cov-report=term-missing

# Check endpoints
curl http://localhost:8000/docs | grep autonomy

# Check linting
black --check kortana/
ruff check kortana/
```

---

## 📞 GETTING HELP

### Questions to Ask Team
1. "Where does X pattern already exist in the code?"
2. "Is my test structure correct?"
3. "Have I implemented this API correctly?"
4. "Can you review my PR?"

### Before Asking
1. Check existing code for similar implementations
2. Read relevant section of DEVELOPMENT_GUIDE_AND_BLUEPRINT.md
3. Review test examples in codebase
4. Try the approach and document the issue

### Common Issues

**"Tests not finding module"**
→ Make sure __init__.py exists in all directories

**"Database connection failing"**
→ Check docker-compose ps, run docker-compose up -d

**"Type hint errors"**
→ Use from typing import Dict, List, Optional, etc.

**"Async function not awaited"**
→ Add await before async function calls

---

## ✨ YOU'RE READY!

You now have:
- ✅ Development environment set up
- ✅ Code structure understood
- ✅ First task defined (SelfAwarenessEngine)
- ✅ Testing framework ready
- ✅ Team resources available

### Start Here
1. Create feature branch
2. Run first test
3. Implement SelfAwarenessEngine class
4. Write unit tests
5. Create pull request

**Expected time for first task: 4-6 hours**

Good luck! 🚀

---

**Version:** 1.0  
**Updated:** 2026  
**Status:** Ready for implementation

**Questions?** Check IMPLEMENTATION_CHECKLIST_WEEKLY.md or ask on team Slack!
