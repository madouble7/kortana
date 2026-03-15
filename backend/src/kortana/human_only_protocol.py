"""
KOR'TANA Human Only Protocol (HOP) - Autonomy Engine

Core Protocol: KOR'TANA executes ALL automatable tasks without human approval.
Only presents scaffolded Human Only (HO) steps when absolutely necessary.

Owner: Matt (Primary Human)
Version: 1.0.0
"""

import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.kortana.database import get_db
from src.kortana.logger import get_logger
from src.kortana.models import Task

logger = get_logger(__name__)

# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================


class TaskClassification(Enum):
    """Task classification for autonomy decisions"""

    AUTO = "auto"  # Fully automatable, execute immediately
    HO = "ho"  # Human Only, requires explicit human action
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
            description="Create isolated Python environment for dependencies",
        ),
        "install_dependencies": DeploymentTask(
            id="install_dependencies",
            name="Install Python Dependencies",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            command="pip install -r backend/requirements.txt",
            description="Install all production dependencies",
        ),
        "run_tests": DeploymentTask(
            id="run_tests",
            name="Run Backend Test Suite",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            command="cd backend && python -m pytest",
            description="Execute automated tests to verify code integrity",
        ),
        "autonomous_merge": DeploymentTask(
            id="autonomous_merge",
            name="Autonomous Evolution Merge",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            command="git checkout main && git merge evolution/* --no-edit",
            description="Merge verified evolution branches into the canonical organism",
        ),
        "create_env_file": DeploymentTask(
            id="create_env_file",
            name="Create Environment Template",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            command="if not exist .env copy backend\\.env.example .env",
            description="Create .env file from template",
        ),
        "validate_codebase": DeploymentTask(
            id="validate_codebase",
            name="Validate Codebase Structure",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            command="python verify_deployment_readiness.py",
            description="Verify all routers, migrations, and dependencies",
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
            """,
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
            """,
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
            """,
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
            """,
        ),
        # AUTO tasks after HO prerequisites are met
        "run_migrations": DeploymentTask(
            id="run_migrations",
            name="Run Database Migrations",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            prerequisites=["configure_env"],
            command="python -m alembic -c backend/alembic.ini upgrade head",
            description="Apply database migrations",
        ),
        "start_server": DeploymentTask(
            id="start_server",
            name="Start Backend Server",
            classification=TaskClassification.APPROVAL,
            status=TaskStatus.PENDING,
            prerequisites=["run_migrations"],
            command="python -m uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000",
            description="Start KOR'TANA backend server",
        ),
        "verify_health": DeploymentTask(
            id="verify_health",
            name="Verify Health Endpoints",
            classification=TaskClassification.AUTO,
            status=TaskStatus.PENDING,
            prerequisites=["start_server"],
            command="python -c \"import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/health').read().decode())\"",
            description="Verify all health endpoints respond",
        ),
    }

    def __init__(self):
        self._definitions = self.DEPLOYMENT_TASKS

    async def synchronize_tasks(self, db: AsyncSession):
        """Synchronize hardcoded task definitions with the database"""
        for task_key, task_def in self._definitions.items():
            # Check if task exists in DB by title (or ID)
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
            else:
                # Update existing task if definition changed (and it's not completed)
                if db_task.status != TaskStatus.COMPLETED.value:
                    db_task.command = task_def.command
                    db_task.classification = task_def.classification.value
                    db_task.description = task_def.description
                    db_task.ho_scaffold = task_def.ho_scaffold
                    # logger.info(f"Updated task definition: {db_task.title}")

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
            return {
                "status": "completed",
                "task": task_id,
                "message": "No command needed",
            }

        try:
            # Determine project root (one level up from this file's directory)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # Prepare command for Windows compatibility and correct environment
            command = task.command

            # SECURITY: Validate command against hardcoded definitions to prevent injection
            # If the task came from DB, ensure its command matches a known safe command
            safe_commands = [t.command for t in self._definitions.values() if t.command]
            if command not in safe_commands:
                # Still allow if it's a slight variation (e.g. paths), but be very strict
                is_safe = False
                for safe_cmd in safe_commands:
                    if safe_cmd and command.startswith(safe_cmd.split()[0]):
                        # Allow variations of the same executable if they are in the whitelist
                        is_safe = True
                        break

                if not is_safe:
                    logger.error(
                        f"SECURITY ALERT: Blocked unauthorized command execution: {command}"
                    )
                    task.status = TaskStatus.FAILED.value
                    task.error = "Unauthorized command blocked for security"
                    await db.commit()
                    return {
                        "status": "failed",
                        "task": task_id,
                        "error": "Unauthorized command",
                    }

            # Use current python executable for 'python', 'pip', and 'alembic'
            py_exe = sys.executable
            if command.startswith("python "):
                command_to_run = command.replace("python ", f'"{py_exe}" ', 1)
            elif command.startswith("pip "):
                command_to_run = command.replace("pip ", f'"{py_exe}" -m pip ', 1)
            elif command.startswith("alembic "):
                command_to_run = command.replace("alembic ", f'"{py_exe}" -m alembic ', 1)
            else:
                command_to_run = command

            # Execute command relative to project root
            logger.info(f"Executing AUTO task {task_id}: {command_to_run} in {project_root}")

            # Use shell=True only if necessary (file copy on windows)
            use_shell = "copy " in command or "if not exist" in command or os.name == "nt"

            proc = subprocess.run(
                command_to_run,
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=project_root,
            )

            if proc.returncode == 0:
                task.status = TaskStatus.COMPLETED.value
                task.result = proc.stdout
                task.completed_at = datetime.utcnow()
                await db.commit()
                return {
                    "status": "completed",
                    "task": task_id,
                    "output": proc.stdout[:1000],
                }
            else:
                task.status = TaskStatus.FAILED.value
                # Combine stdout and stderr for better debugging on failure
                task.error = f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
                await db.commit()
                return {"status": "failed", "task": task_id, "error": task.error}

        except subprocess.TimeoutExpired:
            task.status = TaskStatus.FAILED.value
            task.error = "Command timed out after 300 seconds"
            await db.commit()
            return {"status": "failed", "task": task_id, "error": "Timeout"}
        except Exception as e:
            task.status = TaskStatus.FAILED.value
            task.error = str(e)
            await db.commit()
            return {"status": "failed", "task": task_id, "error": str(e)}

    async def complete_ho_task(self, task_id: str, db: AsyncSession) -> dict[str, Any]:
        """Mark an HO task as completed (called after human action)"""
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        if task.classification != TaskClassification.HO.value:
            raise HTTPException(status_code=400, detail=f"Task {task_id} is not an HO task")

        task.status = TaskStatus.COMPLETED.value
        task.completed_at = datetime.utcnow()
        await db.commit()

        return {"status": "completed", "task": task_id}

    async def get_status(self, db: AsyncSession) -> dict[str, Any]:
        """Get full deployment status from DB"""
        tasks = await self.get_all_tasks(db)

        auto_tasks = [t for t in tasks if t.classification == TaskClassification.AUTO.value]
        ho_tasks = [t for t in tasks if t.classification == TaskClassification.HO.value]
        approval_tasks = [t for t in tasks if t.classification == TaskClassification.APPROVAL.value]

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "protocol_version": "1.1.0",
            "owner": "Matt",
            "summary": {
                "total_tasks": len(tasks),
                "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED.value),
                "in_progress": sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS.value),
                "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING.value),
                "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED.value),
            },
            "classifications": {
                "auto": {
                    "count": sum(1 for t in auto_tasks if t.status == TaskStatus.COMPLETED.value),
                    "total": len(auto_tasks),
                    "tasks": [
                        {
                            "id": t.id,
                            "name": t.title,
                            "status": t.status,
                            "completed": t.completed_at.isoformat() if t.completed_at else None,
                        }
                        for t in auto_tasks
                    ],
                },
                "ho": {
                    "count": sum(1 for t in ho_tasks if t.status == TaskStatus.COMPLETED.value),
                    "total": len(ho_tasks),
                    "pending": [
                        {
                            "id": t.id,
                            "name": t.title,
                            "description": t.description,
                            "scaffold": t.ho_scaffold,
                        }
                        for t in ho_tasks
                        if t.status != TaskStatus.COMPLETED.value
                    ],
                },
                "approval": {
                    "count": sum(
                        1 for t in approval_tasks if t.status == TaskStatus.COMPLETED.value
                    ),
                    "total": len(approval_tasks),
                    "ready": [
                        {"id": t.id, "name": t.title, "command": t.command}
                        for t in approval_tasks
                        if t.status == TaskStatus.PENDING.value
                    ],
                },
            },
            "autonomy_progress": {
                "auto_complete": sum(
                    1 for t in auto_tasks if t.status == TaskStatus.COMPLETED.value
                ),
                "auto_total": len(auto_tasks),
                "ho_complete": sum(1 for t in ho_tasks if t.status == TaskStatus.COMPLETED.value),
                "ho_total": len(ho_tasks),
            },
        }

    async def get_next_ho_task(self, db: AsyncSession) -> Task | None:
        """Get the next pending HO task for Matt"""
        tasks = await self.get_all_tasks(db)
        for task in tasks:
            if (
                task.classification == TaskClassification.HO.value
                and task.status == TaskStatus.PENDING.value
            ):
                return task
        return None

    async def run_autonomous_cycle(self, db: AsyncSession) -> dict[str, Any]:
        """Execute one autonomous cycle using DB tasks"""
        tasks = await self.get_all_tasks(db)
        results = {
            "executed": [],
            "failed": [],
            "pending_ho": [],
        }

        # Find all ready AUTO tasks
        auto_ready = []
        completed_task_ids = {t.id for t in tasks if t.status == TaskStatus.COMPLETED.value}

        # Map titles to IDs for prerequisite checking
        title_to_id = {t.title: t.id for t in tasks}
        # Also map IDs to tasks for easier access
        {t.id: t for t in tasks}

        for task in tasks:
            if (
                task.classification == TaskClassification.AUTO.value
                and task.status == TaskStatus.PENDING.value
            ):
                # Check prerequisites
                # We need to find the task definition to get prerequisites
                task_def = self._definitions.get(task.id)
                if not task_def:
                    # Try to find by title if ID doesn't match
                    for td in self._definitions.values():
                        if td.name == task.title:
                            task_def = td
                            break

                if task_def:
                    prereqs_met = True
                    for prereq_id in task_def.prerequisites:
                        # Check if prerequisite is completed
                        # Prereq ID in definition might be the internal key
                        if prereq_id not in completed_task_ids:
                            # Also check if it's a title
                            prereq_task_id = title_to_id.get(prereq_id)
                            if not prereq_task_id or prereq_task_id not in completed_task_ids:
                                prereqs_met = False
                                break

                    if prereqs_met:
                        auto_ready.append(task)

        for task in auto_ready:
            exec_res = await self.execute_auto_task(task.id, db)
            if exec_res["status"] == "completed":
                results["executed"].append(task.id)
            else:
                results["failed"].append(task.id)

        # Check for pending HO tasks
        ho_task = await self.get_next_ho_task(db)
        if ho_task:
            results["pending_ho"] = {
                "id": ho_task.id,
                "name": ho_task.title,
                "scaffold": ho_task.ho_scaffold,
            }

        results["status"] = await self.get_status(db)
        return results


# ============================================================================
# FASTAPI ROUTER
# ============================================================================

router = APIRouter()
hop = HumanOnlyProtocol()


@router.get("/protocol/status")
async def get_protocol_status(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Get full Human Only Protocol status"""
    return await hop.get_status(db)


@router.get("/protocol/auto/tasks")
async def get_auto_tasks(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    """Get all AUTO tasks ready for execution"""
    tasks = await hop.get_all_tasks(db)
    return [
        {
            "id": t.id,
            "name": t.title,
            "command": t.command,
            "description": t.description,
        }
        for t in tasks
        if t.classification == TaskClassification.AUTO.value
        and t.status == TaskStatus.PENDING.value
    ]


@router.post("/protocol/auto/execute/{task_id}")
async def execute_auto_task_endpoint(
    task_id: str, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Execute an AUTO task without human approval"""
    return await hop.execute_auto_task(task_id, db)


@router.post("/protocol/auto/cycle")
async def run_autonomous_cycle_endpoint(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute all ready AUTO tasks in one cycle"""
    return await hop.run_autonomous_cycle(db)


@router.get("/protocol/ho/next")
async def get_next_ho_task_endpoint(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get next Human Only task for Matt"""
    task = await hop.get_next_ho_task(db)
    if not task:
        return {"message": "All HO tasks completed!", "task": None}
    return {
        "task": {
            "id": task.id,
            "name": task.title,
            "description": task.description,
            "scaffold": task.ho_scaffold,
        }
    }


@router.get("/protocol/ho/all")
async def get_all_ho_tasks_endpoint(
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get all Human Only tasks with their status"""
    tasks = await hop.get_all_tasks(db)
    return [
        {
            "id": t.id,
            "name": t.title,
            "description": t.description,
            "status": t.status,
            "scaffold": t.ho_scaffold,
            "completed": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in tasks
        if t.classification == TaskClassification.HO.value
    ]


@router.post("/protocol/ho/complete/{task_id}")
async def complete_ho_task_endpoint(
    task_id: str, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Mark an HO task as completed (called after Matt completes the task)"""
    return await hop.complete_ho_task(task_id, db)


@router.get("/protocol/health")
async def protocol_health() -> dict[str, Any]:
    """Health check for Human Only Protocol"""
    return {
        "status": "healthy",
        "service": "human_only_protocol",
        "owner": "Matt",
        "timestamp": datetime.utcnow().isoformat(),
    }

