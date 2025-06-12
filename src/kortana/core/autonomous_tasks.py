"""
Kor'tana's Autonomous Tasks
This module contains the actual autonomous behaviors that make Kor'tana proactive.
Each task represents a complete Plan -> Execute -> Learn loop.
"""

import json
import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from kortana.core.execution_engine import execution_engine
from kortana.modules.memory_core.models import MemoryType
from kortana.modules.memory_core.schemas import CoreMemoryCreate
from kortana.modules.memory_core.services import MemoryCoreService
from kortana.modules.models import Goal, GoalStatus, PlanStep
from kortana.modules.planning_engine import planning_engine
from kortana.services.database import get_db_sync

logger = logging.getLogger(__name__)


def run_health_check_task():
    """
    Kor'tana's first autonomous task: Self-monitoring through code health checks.

    This is a complete autonomous cycle:
    1. PLAN: Decide to run a health check on her own codebase
    2. EXECUTE: Use the execution engine to run linting tools
    3. LEARN: Record the outcome in memory for future reference

    This represents the fundamental shift from reactive to proactive behavior.
    """
    logger.info("🚀 AUTONOMOUS TASK: Starting Self-Health Check")

    try:
        # === PHASE 1: PLANNING ===
        task_description = "Autonomous code health check using Ruff linter"
        command_to_execute = "poetry run ruff check src/ --output-format=text"
        project_root = r"c:\project-kortana"

        logger.info(f"📋 PLAN: {task_description}")
        logger.info(f"🔧 COMMAND: {command_to_execute}")

        # === PHASE 2: EXECUTION ===
        logger.info("⚡ EXECUTING: Running health check command...")

        result = execution_engine.execute_shell_command(
            command=command_to_execute, working_dir=project_root
        )

        # === PHASE 3: ANALYSIS ===
        success_status = "SUCCESS" if result.get("success") else "ISSUES_DETECTED"
        return_code = result.get("return_code", -1)
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")

        # Analyze the results
        if return_code == 0:
            health_status = "EXCELLENT"
            health_summary = "No code quality issues detected"
        elif return_code == 1:
            health_status = "NEEDS_ATTENTION"
            issue_count = len(
                [line for line in stdout.split("\n") if line.strip() and ":" in line]
            )
            health_summary = (
                f"Found {issue_count} code quality issues that need attention"
            )
        else:
            health_status = "ERROR"
            health_summary = "Health check command failed to execute properly"

        logger.info(f"📊 ANALYSIS: Status={health_status}, Return Code={return_code}")

        # === PHASE 4: LEARNING (Memory Creation) ===
        # For now, log to file until memory system is working
        timestamp = datetime.now(UTC).isoformat()

        autonomous_log_path = r"c:\project-kortana\data\autonomous_activity.log"

        log_entry = f"""
=== AUTONOMOUS HEALTH CHECK ===
TIMESTAMP: {timestamp}
MISSION: {task_description}
ACTION: {command_to_execute}
OUTCOME: {success_status}
HEALTH STATUS: {health_status}
SUMMARY: {health_summary}
RETURN CODE: {return_code}

LINTER OUTPUT:
{stdout[:1000] if stdout else "No output"}

ERRORS:
{stderr[:500] if stderr else "No errors"}

REFLECTION:
This autonomous health check demonstrates my ability to monitor and assess my own code quality without human intervention. I can now identify potential issues proactively and learn from the patterns I observe.

===============================

"""

        # Write to autonomous activity log
        try:
            with open(autonomous_log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
            logger.info(f"🧠 LEARNED: Activity logged to {autonomous_log_path}")
        except Exception as log_error:
            logger.error(f"❌ Failed to log autonomous activity: {log_error}")

        logger.info(f"✅ AUTONOMOUS TASK COMPLETE: {health_status}")

        # === PHASE 5: REFLECTION & NEXT ACTIONS ===
        if health_status == "NEEDS_ATTENTION":
            logger.info(
                "🎯 INSIGHT: Code quality issues detected - future autonomous task could address these"
            )
        elif health_status == "EXCELLENT":
            logger.info(
                "🎉 INSIGHT: Codebase health is excellent - maintaining current standards"
            )

        return {
            "success": True,
            "health_status": health_status,
            "summary": health_summary,
            "autonomous": True,
            "logged_to": autonomous_log_path,
        }

    except Exception as e:
        logger.error(f"❌ AUTONOMOUS TASK FAILED: {e}")

        # Even failures are learning opportunities - log to file
        timestamp = datetime.now(UTC).isoformat()
        autonomous_log_path = r"c:\project-kortana\data\autonomous_activity.log"

        error_log_entry = f"""
=== AUTONOMOUS TASK ERROR ===
TIMESTAMP: {timestamp}
ERROR: {str(e)}
TASK: Autonomous health check

REFLECTION:
This failure is itself a learning experience. I must improve my error handling and resilience in autonomous operations.

===============================

"""

        try:
            with open(autonomous_log_path, "a", encoding="utf-8") as f:
                f.write(error_log_entry)
            logger.info(f"🧠 ERROR LEARNED: Failure logged to {autonomous_log_path}")
        except Exception as log_error:
            logger.error(f"💥 CRITICAL: Failed to log error: {log_error}")

        return {
            "success": False,
            "error": str(e),
            "autonomous": True,
            "logged_to": autonomous_log_path,
        }


def run_memory_reflection_task():
    """
    Future autonomous task: Reflect on recent memories and identify patterns.
    This would represent higher-order autonomous intelligence.
    """
    logger.info("🔮 AUTONOMOUS TASK: Memory Reflection (Not yet implemented)")
    # TODO: Implement in future batch
    pass


def run_code_improvement_task():
    """
    Future autonomous task: Automatically fix simple code quality issues.
    This would represent autonomous self-improvement.
    """
    logger.info("🔧 AUTONOMOUS TASK: Code Improvement (Not yet implemented)")
    # TODO: Implement in future batch - requires careful safety controls
    pass


async def autonomous_goal_processing_cycle():
    """
    The main autonomous cycle. Fetches an active goal, creates a plan, and executes it.
    This function is called by the scheduler.
    """
    print("\n🤖 --- AUTONOMOUS CYCLE: Checking for active goals... ---")
    db: Session = next(get_db_sync())

    try:
        # 1. Fetch the highest priority pending goal
        active_goal = (
            db.query(Goal)
            .filter(Goal.status == GoalStatus.PENDING)
            .order_by(Goal.priority)
            .first()
        )
        if not active_goal:
            print("--- AUTONOMOUS CYCLE: No pending goals found. Standing by. ---")
            return

        print(
            f"--- AUTONOMOUS CYCLE: Acquired Goal {active_goal.id}: '{active_goal.description}' ---"
        )
        active_goal.status = GoalStatus.ACTIVE
        db.commit()

        # 2. Create a plan for the goal using the Planning Engine
        plan_steps_data = await planning_engine.create_plan_for_goal(
            active_goal.description
        )
        if not plan_steps_data:
            active_goal.status = GoalStatus.FAILED
            db.commit()
            _log_outcome_to_memory(
                db,
                active_goal,
                "Failed to create a valid plan from the goal description.",
            )
            return

        # Save the generated plan to the database
        for i, step_data in enumerate(plan_steps_data):
            plan_step = PlanStep(
                goal_id=active_goal.id,
                step_number=i + 1,
                action_type=step_data.get("action_type", "UNKNOWN"),
                parameters=json.dumps(step_data.get("parameters", {})),
                status=GoalStatus.PENDING,
            )
            db.add(plan_step)
        db.commit()

        # 3. Execute the plan
        await _execute_plan(db, active_goal)

    finally:
        db.close()


async def _execute_plan(db: Session, goal: Goal):
    """Helper function to execute the steps of a given plan."""
    print(f"--- AUTONOMOUS CYCLE: Executing plan for Goal {goal.id} ---")
    final_summary = "Plan executed, but no final summary was provided by the plan."
    execution_context = {}  # To pass results between steps, e.g., content from READ_FILE

    # Refetch steps with ordering
    steps_to_execute = (
        db.query(PlanStep)
        .filter(PlanStep.goal_id == goal.id)
        .order_by(PlanStep.step_number)
        .all()
    )

    for step in steps_to_execute:
        print(f"Executing Step {step.step_number}: {step.action_type}...")
        step.status = GoalStatus.ACTIVE
        db.commit()

        try:
            params = json.loads(step.parameters)

            # Simple context injection: replace placeholders like {{step_1_output}}
            for key, value in params.items():
                if isinstance(value, str) and "{{step_" in value:
                    ref_step_num = int(value.split("{{step_")[1].split("_output}}")[0])
                    params[key] = execution_context.get(f"step_{ref_step_num}")

            result = {}

            if step.action_type == "READ_FILE":
                result = execution_engine.read_file(**params)
                if result.get("success"):
                    execution_context[f"step_{step.step_number}"] = result.get(
                        "content"
                    )
            elif step.action_type == "WRITE_FILE":
                result = execution_engine.write_to_file(**params)
            elif step.action_type == "EXECUTE_SHELL":
                result = execution_engine.execute_shell_command(**params)
            elif step.action_type == "REASONING_COMPLETE":
                result = {"success": True, "summary": params.get("final_summary")}
                final_summary = result["summary"]
            else:
                result = {
                    "success": False,
                    "error": f"Unknown action_type: {step.action_type}",
                }

            step.result = json.dumps(result, indent=2)
            if result.get("success"):
                step.status = GoalStatus.COMPLETED
            else:
                step.status = GoalStatus.FAILED

            db.commit()

            if not result.get("success"):
                print(
                    f"--- AUTONOMOUS CYCLE: Step {step.step_number} failed. Halting plan. ---"
                )
                goal.status = GoalStatus.FAILED
                db.commit()
                _log_outcome_to_memory(
                    db,
                    goal,
                    f"Plan failed at step {step.step_number}: {step.action_type}. Reason: {result.get('error')}",
                )
                return
        except Exception as e:
            step.status = GoalStatus.FAILED
            step.result = json.dumps(
                {
                    "success": False,
                    "error": f"Critical error during step execution: {str(e)}",
                }
            )
            goal.status = GoalStatus.FAILED
            db.commit()
            _log_outcome_to_memory(
                db,
                goal,
                f"Plan failed critically at step {step.step_number}. Error: {str(e)}",
            )
            return

    goal.status = GoalStatus.COMPLETED
    goal.completed_at = func.now()
    db.commit()
    _log_outcome_to_memory(
        db, goal, f"Plan successfully completed. Summary: {final_summary}"
    )
    print(f"--- AUTONOMOUS CYCLE: Goal {goal.id} successfully completed. ---")


def _log_outcome_to_memory(db: Session, goal: Goal, outcome_summary: str):
    """Helper to create a memory of a goal's outcome."""
    memory_service = MemoryCoreService(db)
    memory_title = (
        f"Autonomous Goal Outcome: {goal.description[:50]}... ({goal.status.value})"
    )
    memory_content = f"Goal ID {goal.id}: {goal.description}\nStatus: {goal.status.value}\nSummary: {outcome_summary}"

    memory_to_create = CoreMemoryCreate(
        memory_type=MemoryType.OBSERVATION,
        title=memory_title,
        content=memory_content,
        metadata={
            "source": "goal_processing_cycle",
            "is_self_reflection": True,
            "goal_id": goal.id,
        },
    )
    memory_service.create_memory(memory_create=memory_to_create)
    print(f"🧠 LEARNING: Outcome for Goal ID {goal.id} recorded in memory.")
