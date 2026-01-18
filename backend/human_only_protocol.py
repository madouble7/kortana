"""
KOR'TANA Human Only Protocol (HOP) - Autonomy Engine

Core Protocol: KOR'TANA executes ALL automatable tasks without human approval.
Only presents scaffolded Human Only (HO) steps when absolutely necessary.

Owner: Matt (Primary Human)
Version: 1.0.0
"""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import Task
from logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================


class TaskClassification(Enum):
    """Task classification for autonomy decisions"""
    AUTO = "auto"  # Fully automatable, execute immediately
    HO = "ho"      # Human Only, requires explicit human action
    APPROVAL = "approval"  # Requires human approval before execution


class TaskStatus(Enum):
    """Status for deployment tasks"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_HO = "waiting_for_ho"
    BLOCKED = "blocked"


@dataclass
class DeploymentTask:
    """Represents a single deployment task"""
    id: str
    name: str
    classification: TaskClassification
    status: TaskStatus
    command: str | None = None
    description: str = ""
    prerequisites: list[str] = field(default_factory=list)
    ho_scaffold: str | None = None
    result: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


# ============================================================================
# HUMAN ONLY PROTOCOL ENGINE
# ============================================================================


class HumanOnlyProtocol:
    """
    KOR'TANA's autonomy decision engine.

    Core Principle: Execute ALL automatable tasks without approval.
    Only present scaffolded HO steps when human action is absolutely required.
    """

    # Task definitions with classifications
    DEPLOYMENT_TASKS = {
        # AUTO tasks - KOR'TANA executes these automatically
        "create_venv": DeploymentTask(
            id="create_venv",
            name="Create Python Virtual Environment",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            command="python -m venv venv",
            description="Create isolated Python environment for dependencies"
        ),
        "install_dependencies": DeploymentTask(
            id="install_dependencies",
            name="Install Python Dependencies",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            command="pip install -r backend/requirements.txt",
            description="Install all production dependencies"
        ),
        "create_env_file": DeploymentTask(
            id="create_env_file",
            name="Create Environment Template",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            command="cp backend/.env.example backend/.env",
            description="Create .env file from template"
        ),
        "validate_codebase": DeploymentTask(
            id="validate_codebase",
            name="Validate Codebase Structure",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            command="python verify_deployment_readiness.py",
            description="Verify all routers, migrations, and dependencies"
        ),

        # HO tasks - Require human action
        "github_token": DeploymentTask(
            id="github_token",
            name="Create GitHub Personal Access Token",
            classification=TaskClassification.HO,
            status=TaskStatus.PENDING,
            description="GitHub token required for repository operations",
            ho_scaffold="""
### HO-1: Create GitHub Personal Access Token

1. Open: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: "KOR-TANA-Autonomy"
4. Expiration: "No expiration" or 1 year
5. Select scopes:
   - [x] `repo` - Full control of private repositories
   - [x] `workflow` - Update GitHub Action workflows
   - [x] `read:org` - Read org and team membership
6. Click "Generate token"
7. COPY the token immediately!

**Token format**: `ghp_xxxxxxxxxxxxxxxxxxxx`
            """
        ),
        "gemini_api_key": DeploymentTask(
            id="gemini_api_key",
            name="Create Gemini API Key",
            classification=TaskClassification.HO,
            status=TaskStatus.PENDING,
            description="Gemini API key required for AI analysis",
            ho_scaffold="""
### HO-2: Create Gemini API Key

1. Open: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Choose: "Create API key in new project"
4. Name: "KOR-TANA-Gemini"
5. Click "Create"
6. COPY the API key

**Key format**: `AIzaSy...`
            """
        ),
        "database_url": DeploymentTask(
            id="database_url",
            name="Configure PostgreSQL Database",
            classification=TaskClassification.HO,
            status=TaskStatus.PENDING,
            description="Database connection string required for migrations",
            ho_scaffold="""
### HO-3: Create PostgreSQL Database

**Option A: Docker**
```bash
docker run --name kortana-db \
  -e POSTGRES_DB=kortana \
  -e POSTGRES_USER=kortana_user \
  -e POSTGRES_PASSWORD=YourSecurePassword123! \
  -p 5432:5432 -d postgres
```

**Option B: Cloud (Supabase/Neon)**
1. Create account at https://supabase.com
2. Create new project
3. Copy connection URL

**Option C: Local**
```sql
CREATE DATABASE kortana;
CREATE USER kortana_user WITH PASSWORD 'YourPassword';
GRANT ALL ON DATABASE kortana TO kortana_user;
```

Then update `backend/.env`:
```env
DATABASE_URL=postgresql://user:pass@host:5432/kortana
```
            """
        ),
        "configure_env": DeploymentTask(
            id="configure_env",
            name="Configure Environment Variables",
            classification=TaskClassification.HO,
            status=TaskStatus.PENDING,
            description="Update .env with actual API credentials",
            prerequisites=["github_token", "gemini_api_key", "database_url"],
            ho_scaffold="""
### HO-4: Configure Environment

Open `backend/.env` and replace:
```env
GITHUB_TOKEN=ghp_your_token_here
GEMINI_API_KEY=your_gemini_key_here
DATABASE_URL=postgresql://user:pass@host:5432/kortana
```
            """
        ),

        # AUTO tasks after HO prerequisites are met
        "run_migrations": DeploymentTask(
            id="run_migrations",
            name="Run Database Migrations",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            prerequisites=["configure_env"],
            command="cd backend && alembic upgrade head",
            description="Apply database migrations"
        ),
        "start_server": DeploymentTask(
            id="start_server",
            name="Start Backend Server",
            classification=TaskClassification.APPROVAL,
            status=TaskStatus.PENDING,
            prerequisites=["run_migrations"],
            command="python -m uvicorn main:app --host 0.0.0.0 --port 8000",
            description="Start KOR'TANA backend server"
        ),
        "verify_health": DeploymentTask(
            id="verify_health",
            name="Verify Health Endpoints",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            prerequisites=["start_server"],
            command="curl -s http://localhost:8000/health | jq .",
            description="Verify all health endpoints respond"
        ),
    }

    def __init__(self):
        self.progress_file = Path(__file__).parent / "DEPLOYMENT_PROGRESS.json"
        self._definitions = self.DEPLOYMENT_TASKS

    async def synchronize_tasks(self, db: AsyncSession):
        """Synchronize hardcoded task definitions with the database"""
        for task_key, task_def in self._definitions.items():
            # Check if task exists in DB by title
            result = await db.execute(select(Task).where(Task.title == task_def.name))
            db_task = result.scalar_one_or_none()

            if not db_task:
                # Create new task from definition
                db_task = Task(
                    id=task_key if len(task_key) <= 36 else None,
                    title=task_def.name,
                    description=task_def.description,
                    classification=task_def.classification.value,
                    status=task_def.status.value,
                    command=task_def.command,
                    ho_scaffold=task_def.ho_scaffold,
                )
                db.add(db_task)
                logger.info(f"Initialized new autonomy task in DB: {task_def.name}")

        await db.commit()

    async def get_all_tasks(self, db: AsyncSession) -> list[Task]:
        """Fetch all autonomy tasks from the database"""
        await self.synchronize_tasks(db)
        result = await db.execute(select(Task).order_by(Task.created_at))
        return list(result.scalars().all())

    async def execute_auto_task(self, task_id: str, db: AsyncSession) -> dict[str, Any]:
        """Execute an AUTO task and persist result in DB"""
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        if task.classification != TaskClassification.AUTO.value:
            raise HTTPException(status_code=400, detail=f"Task {task_id} is not AUTO classifiable")

        task.status = TaskStatus.IN_PROGRESS.value
        task.started_at = datetime.utcnow()
        await db.commit()

        if not task.command:
            task.status = TaskStatus.COMPLETED.value
            task.completed_at = datetime.utcnow()
            await db.commit()
            return {"status": "completed", "task": task_id, "message": "No command needed"}

        try:
            # Note: subprocess.run is blocking, but for simple deployment tasks it's acceptable.
            # In a production environment with many concurrent tasks, we'd use asyncio.create_subprocess_shell
            proc_result = subprocess.run(
                task.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                task.status = TaskStatus.COMPLETED
                task.result = result.stdout
                task.completed_at = datetime.utcnow()
                self.save_tasks()
                return {
                    "status": "completed",
                    "task": task_id,
                    "output": result.stdout[:1000]
                }
            else:
                task.status = TaskStatus.FAILED
                task.error = result.stderr
                self.save_tasks()
                return {
                    "status": "failed",
                    "task": task_id,
                    "error": result.stderr
                }

        except subprocess.TimeoutExpired:
            task.status = TaskStatus.FAILED
            task.error = "Command timed out after 300 seconds"
            self.save_tasks()
            return {"status": "failed", "task": task_id, "error": "Timeout"}
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.save_tasks()
            return {"status": "failed", "task": task_id, "error": str(e)}

    def complete_ho_task(self, task_id: str) -> dict[str, Any]:
        """Mark an HO task as completed (called after human action)"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.classification != TaskClassification.HO:
            raise ValueError(f"Task {task_id} is not an HO task")

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        self.save_tasks()

        # Check if this unlocks other tasks
        unlocked = self._check_unlocked_tasks()

        return {
            "status": "completed",
            "task": task_id,
            "unlocked_tasks": unlocked
        }

    def _check_unlocked_tasks(self) -> list[str]:
        """Check which tasks are now unlocked after task completion"""
        unlocked = []
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.PENDING:
                if self._prerequisites_met(task):
                    unlocked.append(task_id)
        return unlocked

    def get_status(self) -> dict[str, Any]:
        """Get full deployment status"""
        auto_tasks = [t for t in self.tasks.values() if t.classification == TaskClassification.AUTO]
        ho_tasks = [t for t in self.tasks.values() if t.classification == TaskClassification.HO]
        approval_tasks = [t for t in self.tasks.values() if t.classification == TaskClassification.APPROVAL]

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "protocol_version": "1.0.0",
            "owner": "Matt",
            "summary": {
                "total_tasks": len(self.tasks),
                "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
                "in_progress": sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS),
                "pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
                "failed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
                "waiting_for_ho": sum(1 for t in self.tasks.values() if t.status == TaskStatus.WAITING_FOR_HO),
            },
            "classifications": {
                "auto": {
                    "count": sum(1 for t in auto_tasks if t.status == TaskStatus.COMPLETED),
                    "total": len(auto_tasks),
                    "tasks": [
                        {
                            "id": t.id,
                            "name": t.name,
                            "status": t.status.value,
                            "completed": t.completed_at.isoformat() if t.completed_at else None
                        }
                        for t in auto_tasks
                    ]
                },
                "ho": {
                    "count": sum(1 for t in ho_tasks if t.status == TaskStatus.COMPLETED),
                    "total": len(ho_tasks),
                    "pending": [
                        {
                            "id": t.id,
                            "name": t.name,
                            "description": t.description,
                            "scaffold": t.ho_scaffold
                        }
                        for t in ho_tasks if t.status != TaskStatus.COMPLETED
                    ]
                },
                "approval": {
                    "count": sum(1 for t in approval_tasks if t.status == TaskStatus.COMPLETED),
                    "total": len(approval_tasks),
                    "ready": [
                        {
                            "id": t.id,
                            "name": t.name,
                            "command": t.command
                        }
                        for t in approval_tasks if self._prerequisites_met(t) and t.status == TaskStatus.PENDING
                    ]
                }
            },
            "autonomy_progress": {
                "auto_complete": sum(1 for t in auto_tasks if t.status == TaskStatus.COMPLETED),
                "auto_total": len(auto_tasks),
                "ho_complete": sum(1 for t in ho_tasks if t.status == TaskStatus.COMPLETED),
                "ho_total": len(ho_tasks)
            }
        }

    def get_next_ho_task(self) -> DeploymentTask | None:
        """Get the next pending HO task for Matt"""
        for task in self.tasks.values():
            if task.classification == TaskClassification.HO and task.status == TaskStatus.PENDING:
                return task
        return None

    def run_autonomous_cycle(self) -> dict[str, Any]:
        """
        Execute one autonomous cycle.
        Runs all ready AUTO tasks without human approval.
        Returns status and any pending HO tasks.
        """
        results = {
            "executed": [],
            "failed": [],
            "pending_ho": [],
            "status": self.get_status()
        }

        # Execute all ready AUTO tasks
        for task in self.get_auto_tasks():
            result = self.execute_auto_task(task.id)
            if result["status"] == "completed":
                results["executed"].append(task.id)
            else:
                results["failed"].append(task.id)

        # Check for pending HO tasks
        ho_task = self.get_next_ho_task()
        if ho_task:
            results["pending_ho"] = {
                "id": ho_task.id,
                "name": ho_task.name,
                "scaffold": ho_task.ho_scaffold
            }

        return results


# ============================================================================
# FASTAPI ROUTER
# ============================================================================

router = APIRouter()
hop = HumanOnlyProtocol()


@router.get("/protocol/status")
async def get_protocol_status() -> dict[str, Any]:
    """Get full Human Only Protocol status"""
    return hop.get_status()


@router.get("/protocol/auto/tasks")
async def get_auto_tasks() -> list[dict[str, Any]]:
    """Get all AUTO tasks ready for execution"""
    return [
        {
            "id": t.id,
            "name": t.name,
            "command": t.command,
            "description": t.description
        }
        for t in hop.get_auto_tasks()
    ]


@router.post("/protocol/auto/execute/{task_id}")
async def execute_auto_task(task_id: str) -> dict[str, Any]:
    """Execute an AUTO task without human approval"""
    try:
        return hop.execute_auto_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/protocol/auto/cycle")
async def run_autonomous_cycle() -> dict[str, Any]:
    """Execute all ready AUTO tasks in one cycle"""
    return hop.run_autonomous_cycle()


@router.get("/protocol/ho/next")
async def get_next_ho_task() -> dict[str, Any]:
    """Get next Human Only task for Matt"""
    task = hop.get_next_ho_task()
    if not task:
        return {"message": "All HO tasks completed!", "task": None}
    return {
        "task": {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "scaffold": task.ho_scaffold
        }
    }


@router.get("/protocol/ho/all")
async def get_all_ho_tasks() -> list[dict[str, Any]]:
    """Get all Human Only tasks with their status"""
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "status": t.status.value,
            "scaffold": t.ho_scaffold,
            "completed": t.completed_at.isoformat() if t.completed_at else None
        }
        for t in hop.get_ho_tasks()
    ]


@router.post("/protocol/ho/complete/{task_id}")
async def complete_ho_task(task_id: str) -> dict[str, Any]:
    """Mark an HO task as completed (called after Matt completes the task)"""
    try:
        return hop.complete_ho_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/protocol/health")
async def protocol_health() -> dict[str, Any]:
    """Health check for Human Only Protocol"""
    return {
        "status": "healthy",
        "service": "human_only_protocol",
        "owner": "Matt",
        "timestamp": datetime.utcnow().isoformat()
    }
