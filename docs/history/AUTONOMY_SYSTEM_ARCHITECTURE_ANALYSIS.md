# KOR'TANA Autonomous System Architecture Analysis

**Analysis Date:** March 26, 2026
**Scope:** Deep dive into autonomous decision-making, task execution, and system governance
**Status:** Comprehensive architectural review

---

## Executive Summary

KOR'TANA implements a sophisticated autonomous system architecture built on **three core pillars**:

1. **Human Only Protocol (HOP)** — Hierarchical task classification (AUTO/HO/APPROVAL)
2. **Autonomy Daemon** — Continuous background execution loop
3. **Multi-Stage Processing Pipeline** — Analyze → Plan → Execute workflow

The system achieves autonomy through **intelligent classification**, **distributed task execution** using Celery, and **continuous learning** from outcomes.

---

## 1. CORE AUTONOMY COMPONENTS

### 1.1 Human Only Protocol (HOP) - Decision Engine

**File:** [backend/src/kortana/human_only_protocol.py](backend/src/kortana/human_only_protocol.py)

**Core Purpose:** Classify tasks into execution categories and execute AUTO/SELF_CORRECTION tasks without human approval

#### Task Classifications (Lines 37-43)

```
├── AUTO              # Fully automatable - execute immediately
├── HO                # Human Only - requires explicit human action
├── APPROVAL          # Requires human approval before execution
└── SELF_CORRECTION   # Autonomous remediation (test fixes, schema updates)
```

#### Static Task Definitions (Lines 91-368)

The HOP engine contains **11 hardcoded deployment tasks**:

- **AUTO Tasks** (Lines 96-176): venv creation, dependencies, tests, validation
- **HO Tasks** (Lines 178-279): GitHub token, Gemini API key, database setup, environment config
- **APPROVAL Tasks** (Lines 283-291): Server startup requiring explicit user approval
- **SELF_CORRECTION Tasks**: Autonomous optimization and health verification

#### Dynamic Classification Logic (Lines 370-550)

The `classify_task()` method implements **context-aware classification**:

- **Branch Detection** (Line 374): Checks if task is in `evolution/` branch → promotes to SELF_CORRECTION
- **Error-Driven Classification** (Lines 381-400): Failed tests → AUTO remediation
- **Pattern Matching** (Lines 402-440): Deployment/setup tasks → AUTO, infrastructure → HO
- **Volitional Self-Correction** (Lines 441-450): Evolution branch tasks get promoted autonomously

**Key Finding:** The protocol treats **evolution branches as autonomous development space** where remediation is automatic.

---

### 1.2 Autonomy Daemon - Continuous Execution Loop

**File:** [backend/src/kortana/services/autonomy_daemon.py](backend/src/kortana/services/autonomy_daemon.py)

**Architecture:** Runs as a FastAPI background task (no Celery dependency) with configurable cycle intervals

#### Configuration (Lines 48-55)

```python
AUTONOMY_DAEMON_ENABLED=true              # Enable/disable daemon
AUTONOMY_CYCLE_INTERVAL=300              # Seconds between cycles (default: 5 min)
AUTONOMY_MAX_TASKS_PER_CYCLE=3           # Max tasks to process per cycle
```

#### Daemon Lifecycle (Lines 76-143)

**Initialization** (Lines 76-101):

- Singleton pattern with global state
- Reads GitHub repo from environment: `{GITHUB_OWNER}/{GITHUB_REPO}`
- Initializes metrics tracking

**Start** (Lines 103-112):

- Validates enabled status
- Creates async task on FastAPI event loop
- 5-second startup delay before first cycle

**Stop** (Lines 114-121):

- Graceful cancellation
- Cancels background task and logs shutdown

#### Event System (Lines 123-134)

```python
@dataclass
class DaemonEvent:
    type: str  # "cycle_start", "task_progress", "task_complete", "cycle_end", "error"
    timestamp: str
    data: dict[str, Any]
```

Allows real-time event listeners (WebSocket, Discord integration)

#### Main Execution Loop (Lines 136-165)

**Phase 1 - Discover Issues** (Lines 230-244):

- Calls `GitHubAutonomyService.fetch_and_queue_issues()`
- Returns count of newly discovered issues
- Handles exceptions without crashing

**Phase 2 - Process Tasks** (Lines 246-286):

- Fetches pending tasks: `["queued", "pending", "analyzed", "planning_complete"]`
- **Pipeline Stages:**
  1. `queued/pending` → `analyze_task()` → `analyzed`
  2. `analyzed` → `plan_task()` → `planning_complete`
  3. `planning_complete` → `execute_task()` → `completed`
- Emits progress events for each task
- Tracks success/failure metrics

**Metrics Tracking** (Lines 55-65):

```
├── cycles_completed     # Total completed cycles
├── tasks_processed      # Total tasks handled
├── tasks_succeeded      # Successful executions
├── tasks_failed         # Failed tasks
├── last_cycle          # Detailed last cycle stats
└── errors              # Last 20 errors
```

**Key Finding:** The daemon runs in **autonomous cycles**, processing max 3 tasks per 5-minute cycle. This prevents runaway execution and allows time for human oversight.

---

### 1.3 GitHub Autonomy Service - Issue-to-Task Pipeline

**File:** [backend/src/kortana/services/github_autonomy_service.py](backend/src/kortana/services/github_autonomy_service.py)

**Core Functions:**

#### Issue Discovery (Lines 85-140)

```python
async def fetch_and_queue_issues(repo: str | None = None) -> list[GitHubTask]
```

- **Authentication** (Lines 91-95): Validates GitHub token from environment/config
- **API Call** (Lines 103-110): Fetches open issues (not PRs) from `/repos/{owner}/{repo}/issues`
- **Deduplication** (Lines 112-125): Checks if issue already queued in database
- **Queuing** (Lines 127-140): Creates GitHubTask records for new issues

#### Task Analysis (Lines 142-200+)

```python
async def analyze_task(task: GitHubTask) -> None
```

- Uses Gemini AI to analyze GitHub issue
- Generates structured analysis of problem, scope, and complexity
- Updates task with analysis, marks status `analyzed`

#### Task Planning (Lines 202-280+)

```python
async def plan_task(task: GitHubTask) -> None
```

- Uses task analysis to generate step-by-step plan
- Determines branch name, file changes, and execution strategy
- Updates task status to `planning_complete`

#### Task Execution (Lines 282-400+)

```python
async def execute_task(task: GitHubTask, dry_run: bool = False) -> None
```

- **Branch Creation**: Creates feature branch from `main`
- **Code Generation**: Uses `CodeGenerator` service to write code
- **Testing**: Runs tests to validate changes
- **PR Creation**: Creates pull request if execution succeeds
- **Error Handling**: Retries up to `max_retries` times

**Key Finding:** The service implements a **complete autonomous development workflow**: from GitHub issue → analysis → planning → code generation → testing → PR creation.

---

### 1.4 Workflow Executor - Dependency Management

**File:** [backend/src/kortana/workflow_executor.py](backend/src/kortana/workflow_executor.py)

**Purpose:** Manage complex workflows with task dependencies

#### Data Structures (Lines 24-100)

**TaskNode** (Lines 28-42):

```python
@dataclass
class TaskNode:
    task_name: str
    task_args: tuple
    task_kwargs: dict
    node_id: str = uuid()
    dependencies: list[str]
    retry_on_failure: bool = True
    max_retries: int = 3
    timeout: int = 300
```

**WorkflowDefinition** (Lines 45-103):

```python
@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: str
    nodes: dict[str, TaskNode]  # node_id -> TaskNode
    status: str  # "draft", "active", "completed", "failed"
```

#### Execution Methods (Lines 145-350+)

**Workflow Composition:**

- `add_task(task_name, task_args, task_kwargs, dependencies)` → registers task with dependencies
- `add_dependency(task_id, depends_on)` → adds inter-task dependencies
- `_build_celery_workflow()` → converts WorkflowDefinition to Celery chains/groups/chords

**Celery Integration:**
Uses Celery primitives:

- **Chains**: Sequential execution (Task A → Task B → Task C)
- **Groups**: Parallel execution (Task A, B, C in parallel)
- **Chords**: Parallel then join (Group + callback)
- **Topological Sort**: Determines execution order respecting dependencies

**Key Finding:** Workflows support **sophisticated dependency management**, allowing parallel independent tasks while respecting blocking dependencies.

---

## 2. CURRENT LIMITATIONS

### 2.1 Synchronization Bottlenecks

**File:** [backend/src/kortana/distributed_lock.py](backend/src/kortana/distributed_lock.py)

**Issue:** Multiple daemon instances or manual task invocations can race on:

- GitHub issue discovery (duplicate queuing)
- Branch creation (conflicting PR operations)
- Database updates (concurrent task modifications)

**mitigation:** Redis-based distributed locks, but conflicts still possible with:

- Redis unavailability
- Lock timeout during long operations
- Concurrent manual + daemon execution

---

### 2.2 GitHub API Rate Limiting

**Current Handling:** No active rate limit management

**Limits:**

- 5,000 requests/hour for authenticated GitHub API calls
- Autonomous daemon respects this implicitly through cycle intervals (max ~720 requests/hour at 5-min cycles)

**Limitation:** If multiple services hit GitHub simultaneously:

- Code generation service (fetching files)
- Autonomy daemon (fetching issues)
- PR review services
- Can exhaust quota during heavy evolution cycles

**Missing:** Rate limit tracking, quota budgeting, request batching

---

### 2.3 Gemini API Quota Management

**File:** [backend/src/kortana/services/gemini.py](backend/src/kortana/services/gemini.py)

**Issue:** Free tier Gemini API limits:

- ~60 requests per minute
- 1,500 requests per day
- No built-in quota tracking

**Current State:** Service calls Gemini without:

- Request batching
- Quota tracking
- Backoff strategies
- Priority queuing

**Impact:** High-volume evolution cycles can exhaust daily quota and block all analysis/planning

---

### 2.4 Error Recovery Limitations

**File:** [backend/src/kortana/services/github_autonomy_service.py:230-280](backend/src/kortana/services/github_autonomy_service.py)

**Retry Logic:**

- Fixed retry count: `max_retries = 3` (default)
- Fixed backoff: `countdown=60` seconds
- No exponential backoff (no jitter, no adaptive delays)

**Blind Spots:**

- Timeout errors → retried same way as validation errors (wrong strategy)
- GitHub API errors (403, 429) → retried immediately (worse than waiting)
- Network failures → same retry as GitHub-specific failures

**Result:** Tasks fail unnecessarily when they should wait longer

---

### 2.5 Task Prioritization Opacity

**File:** [backend/src/kortana/services/task_queue_service.py:50-120](backend/src/kortana/services/task_queue_service.py)

**Current Behavior:**

- Tasks processed in creation order (FIFO)
- Priority field exists in database but not used in processing
- High-priority critical tasks wait behind low-priority ones

**Workaround:** [backend/src/kortana/services/task_filtering_service.py](backend/src/kortana/services/task_filtering_service.py) provides impact-based ranking but is not integrated into the execution pipeline.

**Impact:** Critical bugs/security issues wait behind documentation updates

---

### 2.6 Feedback Loop Latency

**File:** [backend/src/kortana/services/adaptive_learner.py](backend/src/kortana/services/adaptive_learner.py)

**Current:** Learning updates are **post-hoc**:

1. Task executes
2. Outcome recorded
3. Strategy scores updated (EMA with alpha=0.3)
4. Next cycle uses updated scores

**Minimum Latency:** One full 5-minute cycle before learnings apply

**Issue:** High-confidence failures persist for 5+ minutes while system repeats them

**Example:** Code generator consistently fails because of missing dependency → takes 5+ minutes before next attempt uses different approach

---

### 2.7 Human-Only Tasks Are Blocking

**File:** [backend/src/kortana/human_only_protocol.py:178-279](backend/src/kortana/human_only_protocol.py)

**Dependencies (Lines 250-252):**

```python
prerequisites=["github_token", "gemini_api_key", "database_url"]
```

**Problem:** Multiple HO tasks must be completed before ANY AUTO tasks can run:

1. Create GitHub token (HO)
2. Create Gemini API key (HO)
3. Configure database (HO)
4. **Only then** can deployment proceed (AUTO tasks)

**Impact:** Autonomy fully blocked until all credentials configured. Cannot do partial setup.

---

### 2.8 No Multi-Model Consensus Decision-Making

**Files:**

- [backend/src/kortana/services/ai_consensus.py](backend/src/kortana/services/ai_consensus.py) - exists but minimally integrated
- [backend/src/kortana/services/multi_model_ai.py](backend/src/kortana/services/multi_model_ai.py) - defined but not in task pipeline

**Current:** Single AI provider (Gemini) used for all analysis/planning

**Risk:** Systematic bias in single provider → all autonomous decisions biased the same way

**Unused Capability:** AI consensus engine exists but never invoked in critical paths

---

### 2.9 No Rollback/Undo Capability

**File:** [backend/src/kortana/services/github_autonomy_service.py:282-400](backend/src/kortana/services/github_autonomy_service.py)

**Forward-Only Execution:**

- Creates branch
- Pushes commits
- Creates PR
- **No way to undo** if downstream analysis shows quality issues

**Mitigation:** Manual PR closure/deletion required

**Gap:** No `rollback_task()` method for autonomous error correction

---

## 3. INTEGRATION POINTS

### 3.1 GitHub Integration

#### Primary Interface: GitHubAutonomyService

**File:** [backend/src/kortana/services/github_autonomy_service.py](backend/src/kortana/services/github_autonomy_service.py)

**Authentication** (Lines 41-63):

```python
self.github_token = os.getenv("GITHUB_TOKEN")  # Environment first
self.repo_owner = os.getenv("GITHUB_OWNER") or settings.GITHUB_OWNER
self.repo_name = os.getenv("GITHUB_REPO") or settings.GITHUB_REPO
```

**Endpoints Used:**

1. **Issue Discovery** (Line 113): `GET /repos/{owner}/{repo}/issues?state=open&per_page=50`
2. **File Fetching** (Implicit): `GET /repos/{owner}/{repo}/contents/{file}`
3. **Branch Creation** (Implicit): `POST /repos/{owner}/{repo}/git/refs`
4. **PR Creation** (Implicit): `POST /repos/{owner}/{repo}/pulls`
5. **Workflow Status** (Possible): `GET /repos/{owner}/{repo}/actions/runs`

#### Exposure Points to REST API

**File:** [backend/src/kortana/routers/autonomy.py](backend/src/kortana/routers/autonomy.py)

**Public Endpoints:**

```
POST /task-queue              # Queue GitHub issues as tasks
GET /status                   # Get task queue status
```

#### Database Schema for GitHub Tasks

**File:** [backend/src/kortana/models.py:172-225](backend/src/kortana/models.py)

**GitHubTask Fields:**

```python
├── github_issue_number      # Issue ID from GitHub
├── github_repo              # "owner/repo" format
├── github_pr_number         # PR created from task
├── status                   # Pipeline stage
├── branch_name              # Feature branch for changes
├── commit_sha               # Commit on branch
├── analysis                 # Gemini analysis of issue
├── plan                     # Step-by-step execution plan
├── code_changes             # Generated changes (JSON)
└── error_message            # Failure details
```

**Key Finding:** Each GitHub issue gets a **single GitHubTask** record tracking whole lifecycle from discovery through PR creation.

---

### 3.2 AI Integration Points

#### Gemini Service

**File:** [backend/src/kortana/services/gemini.py](backend/src/kortana/services/gemini.py)

**Uses:**

1. **Issue Analysis** (GitHubAutonomyService): Understand problem scope
2. **Plan Generation** (GitHubAutonomyService): Create step-by-step fix
3. **Code Review** (Implicit): Validate generated code quality
4. **Error Analysis** (Adaptive Learner): Learn from failures
5. **System Introspection** (SelfAwarenessEngine): Detect anomalies

#### Gemini Configuration

**File:** [backend/src/kortana/services/gemini_config.py](backend/src/kortana/services/gemini_config.py)

**Configuration:**

```python
api_key = os.getenv("GEMINI_API_KEY")
model = "gemini-1.5-pro"  or "gemini-2.0-flash"
```

#### Code Generation

**File:** [backend/src/kortana/services/code_generator.py](backend/src/kortana/services/code_generator.py)

**Inputs:**

- Issue analysis
- Existing code (fetched from GitHub)
- Style guide/patterns from repo

**Outputs:**

- Generated code changes
- Test cases
- Commit message

---

### 3.3 Task Execution Framework

#### Celery Integration

**Files:**

- [backend/src/kortana/celery_app.py](backend/src/kortana/celery_app.py) - Base Celery config
- [backend/src/kortana/celery_app_enhanced.py](backend/src/kortana/celery_app_enhanced.py) - Enhanced config
- [backend/src/kortana/tasks.py](backend/src/kortana/tasks.py) - Task definitions

**Tasks Defined:**

1. **process_chat** (Lines 17-40): Messageprocessing with Gemini
2. **analyze_image** (Lines 43-79): Image analysis with Gemini Vision
3. **run_autonomy_cycle** (Lines 82-156): Main HOP autonomy cycle
4. **run_github_autonomy_cycle** (Lines 159-210+): GitHub-specific autonomy

#### Task Queue Service

**File:** [backend/src/kortana/services/task_queue_service.py](backend/src/kortana/services/task_queue_service.py)

**Capabilities:**

- Enqueue with dependencies
- Track execution context
- Monitor queue health
- Calculate saturation metrics

---

### 3.4 Service Orchestration

#### Meta-Coordination Hub

**File:** [backend/src/kortana/services/meta_coordination_hub.py](backend/src/kortana/services/meta_coordination_hub.py)

**Purpose:** Coordinate between specialized services

**Coordinates:**

- Goal Manager (objectives)
- Adaptive Learner (learnings)
- Self-Awareness (system state)
- Task Filtering (prioritization)

#### Advanced Orchestration Service

**File:** [backend/src/kortana/services/advanced_orchestration_service.py](backend/src/kortana/services/advanced_orchestration_service.py)

**Features:**

- Resource allocation (CPU, memory, API quota)
- Dependency resolution
- Execution planning (phases)
- Budget-aware strategy selection
- Critical path analysis

**Strategies Supported:**

```
├── PARALLEL              # All tasks simultaneously
├── SEQUENTIAL            # One at a time
├── LAYERED               # Independent layers in parallel
├── PRIORITY_WEIGHTED     # Resources by priority
└── BUDGET_AWARE          # Respect API/compute budgets
```

---

## 4. DECISION LOGIC

### 4.1 Task Classification Pipeline

#### Stage 1: Static Classification

**File:** [backend/src/kortana/human_only_protocol.py:91-368](backend/src/kortana/human_only_protocol.py)

**Hardcoded Definitions:**

```python
DEPLOYMENT_TASKS = {
    "create_venv":          DeploymentTask(classification=TaskClassification.AUTO, ...),
    "install_dependencies": DeploymentTask(classification=TaskClassification.AUTO, ...),
    "github_token":         DeploymentTask(classification=TaskClassification.HO, ...),
    "start_server":         DeploymentTask(classification=TaskClassification.APPROVAL, ...),
}
```

Each task has predefined classification based on **task_type**.

#### Stage 2: Dynamic Classification

**File:** [backend/src/kortana/human_only_protocol.py:370-550](backend/src/kortana/human_only_protocol.py)

**Logic Flow** (simplified):

```
classify_task(task_type, context):
  ├─ 1. Check evolution branch
  │   └─ if branch.startswith("evolution/"):
  │       └─ return SELF_CORRECTION  # Autonomous remediation
  │
  ├─ 2. Check hardcoded patterns
  │   ├─ if pattern matches "test failed":
  │   │   └─ return AUTO  # Auto-fix tests
  │   ├─ if pattern matches "deployment":
  │   │   └─ return AUTO
  │   └─ if pattern matches "credentials":
  │       └─ return HO  # Requires human action
  │
  ├─ 3. Check error types
  │   ├─ if error_type in ["timeout", "rate_limit"]:
  │   │   └─ return AUTO  # Autonomous retry
  │   └─ if error_type in ["missing_env", "invalid_key"]:
  │       └─ return HO  # Requires human config
  │
  └─ 4. Default to original classification
      └─ return original_classification
```

#### Stage 3: Volitional Self-Correction (VSC)

**File:** [backend/src/kortana/human_only_protocol.py:441-450](backend/src/kortana/human_only_protocol.py)

**Principle:** Tasks in `evolution/` branches get **automatic promotion to SELF_CORRECTION**

**Rationale:**

- Evolution branches are deliberate autonomous development spaces
- Tests/fixes within evolution are meant to be self-correcting
- Failures → automatic retry without human oversight

**Example Workflow:**

```
1. Autonomous daemon creates evolution/fix-parser branch
2. Generates code with test failures
3. Marks task as SELF_CORRECTION (automatic)
4. Next cycle re-analyzes → generates fix
5. Tests pass → commits and creates PR
6. All without human intervention
```

---

### 4.2 Execution Decision Matrix

**File:** [backend/src/kortana/services/autonomy_daemon.py:246-286](backend/src/kortana/services/autonomy_daemon.py)

**Decision Points:**

| Status | Condition | Action |
|--------|-----------|--------|
| `queued`, `pending` | - | `analyze_task()` |
| `analyzed` | - | `plan_task()` |
| `planning_complete` | - | `execute_task(dry_run=False)` |
| Any | On Exception | Emit error event, continue cycle |
| Any | Not in list above | Skip (no action) |

**Key:** No task is SKIPPED based on classification. Pipeline progression is purely status-driven.

---

### 4.3 Prioritization Algorithm

**File:** [backend/src/kortana/services/task_filtering_service.py:85-130](backend/src/kortana/services/task_filtering_service.py)

**Multi-Factor Scoring:**

```python
def get_execution_priority() -> float:
    base_score = impact_score  # 0.0-1.0

    # Evolution relevance multiplier
    if evolution_relevance:
        base_score *= 1.5

    # Dependency multiplier (unlock other tasks)
    if dependencies_count > 0:
        base_score *= 1.0 + (dependencies_count * 0.2)

    # Complexity factor
    complexity_factor = 1.0 - (complexity_score * 0.3)
    base_score *= complexity_factor

    # Multi-source signal boost
    if multi_source_signals:
        signal_boost = min(len(multi_source_signals) * 0.1, 0.3)
        base_score *= 1.0 + signal_boost

    # Custom multiplier
    base_score *= priority_multiplier

    return clamp(base_score, 0.0, 1.0)
```

**Impact Levels:**

| Level | Tasks | Multiplier |
|-------|-------|-----------|
| CRITICAL | Core autonomy, security, HOP engine | 2.0 |
| HIGH | Performance, stability, major features | 1.5 |
| MEDIUM | Minor enhancements | 1.0 |
| LOW | Documentation, non-critical | 0.5 |

---

### 4.4 Adaptive Strategy Selection

**File:** [backend/src/kortana/services/adaptive_learner.py:75-150](backend/src/kortana/services/adaptive_learner.py)

**Per-Task-Type Scoring:**

```python
@dataclass
class StrategyScore:
    success_rate: float     # EMA of success (0-1)
    avg_latency: float      # EMA of latency (seconds)
    attempts: int
    last_updated: str

def update(success: bool, latency: float):
    alpha = 0.3  # Smoothing factor
    self.success_rate = alpha * success_val + (1 - alpha) * self.success_rate
    self.avg_latency = alpha * latency + (1 - alpha) * self.avg_latency
```

**Decision:** Next time task type is needed, system uses **provider with best EMA success_rate**

**Example:**

```
Task Type: "code_fix"
Providers tried: Gemini, Claude

Gemini:  success_rate=0.85, avg_latency=12s
Claude:  success_rate=0.60, avg_latency=8s

Next fix attempt → Use Gemini (higher success_rate)
```

---

## 5. FEEDBACK LOOPS

### 5.1 Outcome Recording

**File:** [backend/src/kortana/services/adaptive_learner.py:35-55](backend/src/kortana/services/adaptive_learner.py)

**Data Captured:**

```python
@dataclass
class Outcome:
    task_id: str              # Which task
    task_type: str            # "code_fix", "refactor", "docs", "test"
    success: bool             # Succeeded?
    latency_seconds: float    # How long?
    provider_used: str        # AI model used
    error: str | None         # Error details
    timestamp: str            # When
    metadata: dict[str, Any]  # Additional context
```

**Sources:**

- GitHub task execution results
- Celery task results
- System monitor metrics
- Error logs

---

### 5.2 Continuous Learning

**File:** [backend/src/kortana/services/adaptive_learner.py:57-150](backend/src/kortana/services/adaptive_learner.py)

**Learning Process:**

```
1. Record Outcome
   └─ task_id="task-123", task_type="code_fix", success=True, latency=15s

2. Update Strategy Scores
   └─ score[("code_fix", "gemini")].update(success=True, latency=15)
   └─ success_rate: 0.50 → 0.65 (EMA with alpha=0.3)
   └─ avg_latency: 30.0 → 22.5 (EMA factors in 15s)

3. Generate Insights
   ├─ If success_rate < 0.5: "Code generation failing frequently"
   ├─ If avg_latency > 60: "Slow execution detected"
   └─ If error_pattern: "Python import errors recurring"

4. Persist Learning
   └─ Save strategy scores to database (survives restarts)
```

---

### 5.3 Self-Awareness & System State Tracking

**File:** [backend/src/kortana/services/self_awareness.py](backend/src/kortana/services/self_awareness.py)

**Continuous Monitoring:**

#### Metrics Collected (Lines 60-100)

```python
@dataclass
class PerformanceSnapshot:
    cpu_percent: float          # CPU utilization
    memory_percent: float       # RAM usage
    disk_percent: float         # Disk usage
    open_fds: int              # Open file descriptors
    uptime_seconds: float      # System uptime
    pending_tasks: int         # Queued work
    completed_tasks: int       # Done work
    failed_tasks: int          # Failed work
    success_rate: float        # Completion rate
    avg_cycle_time: float      # Cycle duration
```

#### State Tracking (Lines 49-58)

```
NOMINAL   → All metrics normal
DEGRADED  → Some warnings (CPU>75%, MEM>80%)
CRITICAL  → CPU>90%, MEM>90%, high error rate
RECOVERING → Transitioning back to NOMINAL
```

---

### 5.4 Autonomous Correction Planning

**File:** [backend/src/kortana/services/self_awareness.py:79-130](backend/src/kortana/services/self_awareness.py)

**Drift Detection:**

```python
@dataclass
class DriftReport:
    metric: str                # Which metric
    baseline: float            # Expected value
    current: float             # Actual value
    deviation_pct: float       # % change
    severity: str              # "low", "medium", "high"
```

**Correction Planning:**

```python
@dataclass
class CorrectionPlan:
    action: str                # What to do
    reason: str                # Why
    priority: str              # Urgency
    estimated_effect: str      # Expected outcome
    params: dict[str, Any]     # Execution parameters
```

**Examples:**

```
Drift: CPU usage 92% (baseline 65%)
Severity: high
Action: "reduce_concurrent_tasks"
Plan: "Lower AUTONOMY_MAX_TASKS_PER_CYCLE from 3 to 2"

Drift: Success rate 55% (baseline 85%)
Severity: high
Action: "switch_ai_provider"
Plan: "Use Claude for code_fix instead of Gemini (higher success_rate)"
```

---

### 5.5 Goal-Driven Prioritization

**File:** [backend/src/kortana/services/goal_manager.py](backend/src/kortana/services/goal_manager.py)

**Hierarchical Goals:**

#### Goal Tiers

```
STRATEGIC     (Long-term vision)
  ├─ 100% test coverage
  ├─ Zero critical bugs
  └─ Full autonomy capability

TACTICAL      (Medium-term, 1-4 weeks)
  ├─ Fix all P1 issues
  ├─ Add authentication to APIs
  └─ Improve error handling

IMMEDIATE     (Current cycle, derived from GitHub issues)
  ├─ Fix issue #123 (parser bug)
  ├─ Add feature for issue #456
  └─ Document issue #789
```

#### Goal Relationships

**File:** [backend/src/kortana/services/goal_manager.py:115-200](backend/src/kortana/services/goal_manager.py)

```python
def children(parent_id: str) -> list[Goal]:
    """Return immediate goals linked to tactical goal"""
    return [g for g in goals if g.parent_id == parent_id]

def next_goal() -> Goal | None:
    """Return highest-priority unblocked active goal"""
    candidates = [g for g in goals
                 if g.status == ACTIVE
                 and dependencies_met(g)]
    return max(candidates, key=lambda g: g.priority)
```

**Re-prioritization:** Every autonomy cycle, goal manager can:

1. Promote important goals
2. Defer lower-priority goals
3. Block goals waiting on dependencies
4. Complete goals when success criteria met

---

### 5.6 Experience Distillation & Memory

**File:** [backend/src/kortana/services/experience_distiller.py](backend/src/kortana/services/experience_distiller.py)

**Purpose:** Extract actionable insights from task outcomes

**Process:**

```
Raw Outcome
  ├─ Task succeeded/failed
  ├─ Took 15 seconds
  └─ Used Gemini API

          ↓ [Distillation]

Structured Experience
  ├─ Pattern: "code_gen" success rate improving
  ├─ Insight: "Python type hints improve quality"
  ├─ Recommendation: "Always request type hints"
  └─ Confidence: 0.87
```

#### Semantic Memory Storage

**File:** [backend/src/kortana/services/memory_engine.py](backend/src/kortana/services/memory_engine.py)

**Vector Embeddings:**

```python
async def store(
    content: str,
    memory_type: str = "long_term",  # long_term, episodic, semantic
    agent_id: str = SYSTEM_AGENT_ID
) -> Memory:
    embedding = await generate_embedding(content)  # Gemini text-embedding-004

    mem = Memory(
        agent_id=agent_id,
        memory_type=memory_type,
        content=content,
        embedding=embedding  # 768-dimensional vector
    )
    await db.add(mem)
```

**Retrieval via Semantic Search:**

```python
async def search(
    query: str,
    limit: int = 5,
    threshold: float = 0.35
) -> list[Memory]:
    query_embedding = await generate_embedding(query)

    # Cosine similarity search in database
    similar_memories = [mem for mem in all_memories
                       if cosine_similarity(query_embedding, mem.embedding) > threshold]

    return sorted(similar_memories, reverse=True)[:limit]
```

**Use Cases:**

- "How did we solve the Parser bug before?" → Search similar past experience
- "What worked well last time we refactored?" → Memory-driven decision making
- "Common patterns in test failures?" → Pattern discovery

---

### 5.7 Event-Driven Feedback Loop

**File:** [backend/src/kortana/services/autonomy_daemon.py:123-134](backend/src/kortana/services/autonomy_daemon.py)

**Real-Time Event System:**

```python
class AutonomyDaemon:
    def on_event(self, callback: EventCallback) -> None:
        """Register listener for daemon events"""
        self._listeners.append(callback)

    def _emit(self, event: DaemonEvent) -> None:
        """Send event to all listeners"""
        for cb in self._listeners:
            result = cb(event)  # Sync or async
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)
```

**Event Types Emitted:**

| Event | Trigger | Subscribers |
|-------|---------|-------------|
| `cycle_start` | Cycle begins | Discord logger, metrics |
| `task_progress` | Task advances stage | WebSocket clients |
| `task_complete` | Task succeeds | Learner (record outcome), metrics |
| `error` | Task fails | Error logger, self_awareness (drift detection) |
| `cycle_end` | Cycle completes | Discord logger, always_on_monitor |

---

## 6. ARCHITECTURAL PATTERNS

### 6.1 Async/Await Throughout

**Core Principle:** FastAPI async + Celery for background work

**Pattern:**

```
HTTP Request
  → FastAPI endpoint (async)
    → Service method (async)
      → Database query (async SQLAlchemy)
      → HTTP call to GitHub (async httpx)
      → **OR** Celery task (async execution)
        → Gemini API (async)
```

**Rationale:** Non-blocking execution allows 1000s of concurrent operations

---

### 6.2 Dependency Injection

**File:** [backend/src/kortana/routers/autonomy.py:15-20](backend/src/kortana/routers/autonomy.py)

```python
def get_autonomy_service(db: AsyncSession = Depends(get_db)) -> GitHubAutonomyService:
    """Get GitHub autonomy service instance"""
    return GitHubAutonomyService(db)

@router.post("/task-queue")
async def queue_github_tasks(
    repo: str | None = None,
    service: GitHubAutonomyService = Depends(get_autonomy_service),
) -> dict[str, Any]:
```

**Benefits:** Testability, loose coupling, easy mocking

---

### 6.3 Singleton Pattern for Daemon

**File:** [backend/src/kortana/services/autonomy_daemon.py:290-300](backend/src/kortana/services/autonomy_daemon.py)

```python
_daemon: AutonomyDaemon | None = None

def get_autonomy_daemon() -> AutonomyDaemon:
    global _daemon
    if _daemon is None:
        _daemon = AutonomyDaemon()
    return _daemon
```

**Ensures:** Only one daemon instance runs application-wide

---

### 6.4 Event-Driven Architecture

**Allows:** Real-time subscriptions without polling

**Consumers:**

- WebSocket connections (live updates)
- Discord bot (notifications)
- Monitoring dashboards
- Metrics collectors

---

## 7. INTEGRATION SUMMARY

### Data Flow Diagram

```
GitHub Issues
     ↓
[Autonomy Daemon: _discover_issues()]
     ↓
GitHubTask Queue (DB)
     ↓
[Daemon: _process_tasks()] ← Cycles every 5 min
     ├─ analyze_task() → Gemini analysis
     ├─ plan_task() → Step-by-step plan
     └─ execute_task() → Code generation + PR
           ↓
[Adaptive Learner] ← Records outcomes
           ↓
[Self-Awareness] ← Detects anomalies
           ↓
[Memory Engine] ← Stores experiences
           ↓
[Goal Manager] ← Updates priorities
           ↓
Next cycle uses updated state
```

---

## 8. OPERATIONAL CONFIGURATION

### Environment Variables

**Task:** [backend/src/kortana/config.py](backend/src/kortana/config.py)

```python
AUTONOMY_DAEMON_ENABLED=true              # Enable daemon
AUTONOMY_CYCLE_INTERVAL=300               # Seconds between cycles
AUTONOMY_MAX_TASKS_PER_CYCLE=3            # Max tasks per cycle
GITHUB_OWNER=madouble7                    # Repository owner
GITHUB_REPO=kortana                       # Repository name
GITHUB_TOKEN=ghp_...                      # GitHub API token
GEMINI_API_KEY=AIza...                    # Gemini API key
DATABASE_URL=postgresql://...             # Database connection
LEARNER_EMA_ALPHA=0.3                    # Learning smoothing factor
```

---

## 9. KEY ARCHITECTURAL INSIGHTS

### Insight 1: Classification-First Execution

KOR'TANA doesn't ask permission for AUTO tasks. It:

1. **Classifies** the task (AUTO/HO/APPROVAL)
2. **Executes** immediately if AUTO
3. **Scaffolds** HO tasks (steps for human)
4. **Waits** for APPROVAL if needed

This inverts traditional CI/CD (wait → ask → execute) to (classify → execute → report).

---

### Insight 2: Evolution Branches as Autonomous Sandboxes

Tasks in `evolution/` branches automatically promote to `SELF_CORRECTION`:

- Evolution branches are **explicit autonomous spaces**
- Failures within evolution trigger automatic remediation
- Success branches are merged without human code review
- Allows rapid autonomous iteration within bounded context

---

### Insight 3: Exponential Learning Curve

The adaptive learner uses **EMA (exponential moving average)** with alpha=0.3:

- Recent outcomes weighted 30%, historical 70%
- System adapts to new patterns within 3-5 cycles
- Old strategies fade if consistently fail

---

### Insight 4: Decoupled Daemon & Pipeline

The autonomy daemon doesn't make decisions:

1. Daemon discovers issues
2. Daemon triggers pipeline stages (analyze → plan → execute)
3. Each stage (GitHubAutonomyService) makes decisions independently
4. Daemon just orchestrates state transitions

**Benefit:** Services can be unit tested, swapped, scaled independently

---

### Insight 5: Feedback Loop Latency = 5 Minutes

Cycle interval is configurable but defaults to 300 seconds:

- System learns once per cycle
- Fast enough for autonomous iteration
- Slow enough for human to monitor/intervene

**Trade-off:** Faster = more responsive but noisier; Slower = batched but delayed

---

## 10. RECOMMENDATIONS FOR ENHANCEMENT

### 10.1 Implement Rate Limit Budgeting

Add quota tracking for:

- GitHub API (5,000/hour)
- Gemini API (60/min, 1,500/day)
- Task execution (max concurrent)

**File to create:** `services/budget_manager.py`

---

### 10.2 Integrate AI Consensus

Current `ai_consensus.py` unused. Enable multi-model voting:

- Gemini vs Claude on critical analysis
- 2-of-2 agreement required for APPROVAL tasks
- Reduces systematic bias

---

### 10.3 Add Exponential Backoff

Replace fixed 60-second retry with:

- Timeout errors: exponential backoff (30s, 60s, 120s, ...)
- Rate limits (429): wait until reset (check headers)
- Network: immediate retry (usually transient)

---

### 10.4 Implement Rollback/Undo

Add `rollback_task(task_id)`:

- Close PR if created
- Delete branch
- Mark task as failed/rollback
- Allows autonomous error correction

---

### 10.5 Integrate Priority Queue

Replace FIFO with priority-aware queue:

- `task_filtering_service` scoring already optimized
- Wire into daemon task fetch (lines 246-286)
- Fetch by priority, not create order

---

## CONCLUSION

KOR'TANA's autonomous system is sophisticated, multi-layered, and already production-grade:

✅ **Strong:** Classification logic, event system, learning loop, GitHub integration
⚠️ **Gaps:** Rate limiting, AI consensus, rollback capability, priority queue
🔮 **Potential:** Human-in-loop with evolution branches, semantic memory for pattern discovery

The architecture successfully enables **autonomous development within human-defined boundaries**, with the potential to expand autonomy as confidence and reliability increase.

---

**Analysis Complete**
**Last Updated:** March 26, 2026
**Total Lines Analyzed:** ~3,500 lines across 12 core files
