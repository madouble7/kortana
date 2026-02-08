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

from kortana.core.execution_engine import ExecutionEngine
from kortana.core.models import Goal, GoalStatus, PlanStep
from kortana.core.planning_engine import PlanningEngine
from kortana.core.services import (
    get_execution_engine,
    get_llm_service,
    get_planning_engine,
)
from kortana.modules.memory_core import models
from kortana.modules.memory_core.models import MemoryType
from kortana.modules.memory_core.schemas import CoreMemoryCreate
from kortana.modules.memory_core.services import MemoryCoreService
from kortana.services.database import get_db_sync

logger = logging.getLogger(__name__)


# Use centralized services instead of direct instantiation
def get_planning_engine_instance():
    """Get planning engine from centralized services with fallback."""
    try:
        return get_planning_engine()
    except RuntimeError:
        # Fallback to direct instantiation if services not initialized
        return PlanningEngine()


def get_execution_engine_instance():
    """Get execution engine from centralized services with fallback."""
    try:
        return get_execution_engine()
    except RuntimeError:
        # Fallback to direct instantiation if services not initialized
        return ExecutionEngine(
            allowed_dirs=[
                r"c:\project-kortana",
                r"c:\project-kortana\docs",
                r"c:\project-kortana\data",
            ],
            blocked_commands=[
                "rm",
                "del",
                "shutdown",
                "reboot",
                "format",
                "mkfs",
                "rmdir",
                "mv",
                "cp",
                "dd",
                ":(){:|:&};:",
            ],
        )


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

        result = get_execution_engine_instance().execute_shell_command(
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


async def run_performance_analysis_task(db: Session):
    """
    An autonomous task for Kor'tana to reflect on her recent actions
    and generate new insights or 'best practices' for herself.
    """
    print(
        "\n🤔 --- AUTONOMOUS TASK: Starting Self-Reflection & Performance Analysis ---"
    )
    memory_service = MemoryCoreService(db)

    try:
        # 1. PLAN: Gather recent goal outcomes and analyze them.
        task_description = "Analyze the outcomes of my last 10 autonomous goals to identify patterns and derive new insights for self-improvement."
        print(f"🎯 PLAN: {task_description}")

        # 2. EXECUTE (Internal Action - Read Memory):
        recent_outcomes = (
            db.query(models.CoreMemory)
            .filter(
                models.CoreMemory.metadata["source"].astext == "goal_processing_cycle"
            )
            .order_by(models.CoreMemory.created_at.desc())
            .limit(10)
            .all()
        )

        if not recent_outcomes:
            print(
                "--- AUTONOMOUS TASK: No recent goal outcomes to analyze. Standing by. ---"
            )
            return

        # 3. REASON: Use the LLM to analyze the collected data.
        analysis_prompt = _build_self_analysis_prompt(recent_outcomes)
        llm_service = get_llm_service()
        llm_result = await llm_service.generate_response(
            analysis_prompt, temperature=0.5
        )

        new_insight = llm_result.get("content")

        if not new_insight or "no significant pattern" in new_insight.lower():
            print(
                "--- AUTONOMOUS TASK: Analysis complete. No new core belief was formed. ---"
            )
            return

        # 4. LEARN: Store the new insight as a Core Belief.
        print(f"💡 NEW INSIGHT: {new_insight}")
        belief_to_create = CoreMemoryCreate(
            memory_type=MemoryType.CORE_BELIEF,
            title="New Self-Generated Best Practice",
            content=new_insight,
            memory_metadata={
                "source": "performance_analysis_task",
                "is_self_generated": True,
            },
        )
        created_belief = memory_service.create_memory(memory_create=belief_to_create)

        print(
            f"🧠 LEARNING: New Core Belief recorded in Memory ID: {created_belief.id}"
        )
        print(
            "🎉 --- AUTONOMOUS TASK: Self-reflection complete. I have learned something new. ---\n"
        )

    except Exception as e:
        print(f"❌ AUTONOMOUS TASK ERROR (Self-Reflection): {e}")
    finally:
        db.close()


def _build_self_analysis_prompt(memories: list[models.CoreMemory]) -> str:
    """Constructs a prompt for the LLM to analyze past actions."""

    memory_log = "\n".join(
        [f"- Goal Outcome: {mem.title}\n  Summary: {mem.content}\n" for mem in memories]
    )

    return f"""
You are a reflective and analytical AI core. You are analyzing a log of your own recent autonomous actions to learn and improve.
Review the following outcomes of goals you have pursued. Look for patterns, especially regarding successes, failures, or repeated steps.

Recent Activity Log:
{memory_log}

Your Task:
Based only on the log above, derive a single, concise, and actionable "best practice" or "guiding principle" for yourself.

If you see repeated planning failures, suggest a way to improve planning.
If you see shell command errors, suggest a more robust way to execute them.
If you see successes, distill the strategy used.
Your output should be a single sentence starting with "I should..." or "My approach to...".
If there are no significant patterns, respond with "No significant pattern detected."
Your derived best practice is:
"""


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

        # Fetch Core Beliefs to guide planning
        core_beliefs_models = (
            db.query(models.CoreMemory)
            .filter(models.CoreMemory.memory_type == MemoryType.CORE_BELIEF)
            .all()
        )
        core_beliefs_content = [
            belief.content
            for belief in core_beliefs_models
            if hasattr(belief, "content") and isinstance(belief.content, str)
        ]

        # 2. Create a plan for the goal using the Planning Engine
        plan_steps_data = await get_planning_engine_instance().create_plan_for_goal(
            active_goal.description, core_beliefs=core_beliefs_content
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
                result_obj = await get_execution_engine_instance().read_file(**params)
                result = {
                    "success": result_obj.success,
                    "data": result_obj.data,
                    "error": result_obj.error,
                }
                if result_obj.success:
                    execution_context[f"step_{step.step_number}"] = result_obj.data
            elif step.action_type == "WRITE_FILE":
                result_obj = await get_execution_engine_instance().write_to_file(
                    **params
                )
                result = {
                    "success": result_obj.success,
                    "data": result_obj.data,
                    "error": result_obj.error,
                }
            elif step.action_type == "EXECUTE_SHELL":
                result_obj = (
                    await get_execution_engine_instance().execute_shell_command(
                        **params
                    )
                )
                result = {
                    "success": result_obj.success,
                    "data": result_obj.data,
                    "error": result_obj.error,
                }
            elif step.action_type == "SEARCH_CODEBASE":
                result_obj = await get_execution_engine_instance().search_codebase(
                    **params
                )
                result = {
                    "success": result_obj.success,
                    "data": result_obj.data,
                    "error": result_obj.error,
                }
                if result_obj.success:
                    execution_context[f"step_{step.step_number}"] = result_obj.data
            elif step.action_type == "APPLY_PATCH":
                result_obj = await get_execution_engine_instance().apply_patch(**params)
                result = {
                    "success": result_obj.success,
                    "data": result_obj.data,
                    "error": result_obj.error,
                }
            elif step.action_type == "RUN_TESTS":
                result_obj = await get_execution_engine_instance().run_tests(**params)
                result = {
                    "success": result_obj.success,
                    "data": result_obj.data,
                    "error": result_obj.error,
                }
                if result_obj.success:
                    execution_context[f"step_{step.step_number}"] = result_obj.data
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
        memory_metadata={
            "source": "goal_processing_cycle",
            "is_self_reflection": True,
            "goal_id": goal.id,
        },
    )
    memory_service.create_memory(memory_create=memory_to_create)
    print(f"🧠 LEARNING: Outcome for Goal ID {goal.id} recorded in memory.")


async def run_proactive_code_review_task(db: Session):
    """
    🚀 BATCH 10: PROACTIVE ENGINEER INITIATIVE

    Autonomously scan the codebase for quality issues and generate improvement goals.
    This transforms Kor'tana from reactive to proactive by enabling her to identify
    her own work and create self-improvement goals.

    This task:
    1. Scans the codebase for functions missing docstrings
    2. Creates new goals for each issue found
    3. Enables autonomous self-improvement cycles
    """
    logger.info("🔍 Starting proactive code review task...")

    try:
        # Get execution engine instance
        # Initialize execution engine to ensure it's available for task execution
    # This call ensures the executor is properly set up before running tasks
    executor = get_execution_engine_instance()
    if executor is None:
        logger.warning("Execution engine could not be initialized")

        # Define scan paths - focus on core Kor'tana code
        scan_paths = [
            "src/kortana/api/routers",
            "src/kortana/api/services",
            "src/kortana/core",
            "src/kortana/planning",
        ]

        logger.info(f"📂 Scanning paths: {scan_paths}")
        # Scan for missing docstrings using a simpler approach
        # Instead of using the execution engine method, we'll scan directly
        findings = []

        for scan_path in scan_paths:
            try:
                import ast
                import os
                from pathlib import Path

                # Walk through the directory and find Python files
                for root, _dirs, files in os.walk(scan_path):
                    for file in files:
                        if file.endswith(".py"):
                            file_path = Path(root) / file
                            try:
                                with open(file_path, encoding="utf-8") as f:
                                    content = f.read()

                                tree = ast.parse(content)

                                # Find functions without docstrings
                                for node in ast.walk(tree):
                                    if isinstance(
                                        node, (ast.FunctionDef, ast.AsyncFunctionDef)
                                    ):
                                        if not ast.get_docstring(node):
                                            findings.append(
                                                {
                                                    "file": str(file_path),
                                                    "line": node.lineno,
                                                    "type": "missing_docstring",
                                                    "function_name": node.name,
                                                }
                                            )
                            except Exception as e:
                                logger.warning(f"Could not scan {file_path}: {e}")
                                continue
            except Exception as e:
                logger.warning(f"Could not scan directory {scan_path}: {e}")
                continue
        logger.info(f"🔍 Found {len(findings)} functions missing docstrings")

        # Create goals for each finding (limit to prevent goal spam)
        goals_created = 0
        max_goals_per_run = 3  # Limit to prevent overwhelming the system

        for finding in findings[:max_goals_per_run]:
            if finding.get("type") == "missing_docstring":
                # Check if we already have a goal for this function
                existing_goal = (
                    db.query(Goal)
                    .filter(
                        Goal.description.contains(
                            f"Add docstring to '{finding['function_name']}'"
                        ),
                        Goal.description.contains(finding["file"]),
                    )
                    .first()
                )

                if existing_goal:
                    logger.info(
                        f"⏭️ Skipping {finding['function_name']} - goal already exists"
                    )
                    continue

                # Create a new goal for this missing docstring
                goal_description = (
                    f"Add a comprehensive docstring to the '{finding['function_name']}' function "
                    f"in '{finding['file']}' at line {finding['line']}. The docstring should describe "
                    f"the function's purpose, parameters, return value, and any important behavior. "
                    f"Follow Google/NumPy docstring style conventions."
                )

                new_goal = Goal(
                    description=goal_description,
                    priority=3,  # Medium priority for code quality improvements
                    status=GoalStatus.PENDING,
                    created_at=datetime.now(UTC),
                    metadata=json.dumps(
                        {
                            "type": "proactive_code_quality",
                            "source": "autonomous_code_review",
                            "file": finding["file"],
                            "function": finding["function_name"],
                            "line": finding["line"],
                            "issue_type": "missing_docstring",
                        }
                    ),
                )

                db.add(new_goal)
                goals_created += 1

                logger.info(
                    f"✅ Created goal for {finding['function_name']} in {finding['file']}"
                )

        if goals_created > 0:
            db.commit()
            logger.info(
                f"🎯 PROACTIVE SUCCESS: Created {goals_created} new self-improvement goals!"
            )

            # Store a memory about this proactive behavior
            try:
                memory = models.CoreMemory(
                    content=f"I autonomously scanned my codebase and identified {len(findings)} functions missing docstrings. I created {goals_created} self-improvement goals to address code quality issues. This demonstrates proactive engineering capabilities.",
                    memory_type=MemoryType.CORE_BELIEF,
                    created_at=datetime.now(UTC),
                    metadata=json.dumps(
                        {
                            "findings_count": len(findings),
                            "goals_created": goals_created,
                            "scan_paths": scan_paths,
                            "proactive_cycle": True,
                        }
                    ),
                )
                db.add(memory)
                db.commit()
                logger.info("💾 Stored memory of proactive code review")
            except Exception as e:
                logger.error(f"Error storing proactive memory: {e}")
        else:
            logger.info("✨ No new goals needed - codebase quality is good!")

    except Exception as e:
        logger.error(f"❌ Error in proactive code review task: {e}")
        db.rollback()
