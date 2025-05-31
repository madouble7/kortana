import logging
import subprocess
from typing import List, Dict, Any
import psutil

logger_planning = logging.getLogger(__name__ + ".PlanningAgent")
logger_coding = logging.getLogger(__name__ + ".CodingAgent")
logger_testing = logging.getLogger(__name__ + ".TestingAgent")
logger_monitoring = logging.getLogger(__name__ + ".MonitoringAgent")


class PlanningAgent:
    """
    The PlanningAgent takes high-level goals or problem descriptions, uses the LLM to break them into smaller, actionable tasks with priorities, and stores this plan in memory.jsonl (tagged as ade_plan).
    """

    def __init__(self, chat_engine_instance, llm_client, covenant_enforcer):
        self.chat_engine = chat_engine_instance
        self.llm_client = llm_client
        self.covenant_enforcer = covenant_enforcer
        logger_planning.info("PlanningAgent initialized.")

    def run(self, goal: str = None) -> List[Dict[str, Any]]:
        """
        Generate a plan (list of tasks) for a given high-level goal or from ADE goals in memory.
        """
        logger_planning.info("Running daily planning...")
        # 1. Retrieve ADE goals from memory.jsonl
        ade_goals = []
        if hasattr(self.chat_engine, "get_ade_goals"):
            ade_goals = self.chat_engine.get_ade_goals()
        if not ade_goals:
            logger_planning.warning("No ADE goals found in memory. Using dummy tasks.")
            ade_goals = [
                {
                    "content": "Review PR #123",
                    "metadata": {"priority": 1, "id": "task1"},
                },
                {
                    "content": "Draft documentation for memory.md",
                    "metadata": {"priority": 2, "id": "task2"},
                },
                {
                    "content": "Investigate LobeChat integration",
                    "metadata": {"priority": 1, "id": "task3"},
                },
            ]
        logger_planning.info(
            f"Planning input goals: {[g['content'] for g in ade_goals]}"
        )
        # 2. Rank tasks (simple ranking for now, could use an LLM later for complex prioritization)
        ranked_tasks = sorted(
            ade_goals, key=lambda t: t.get("metadata", {}).get("priority", 99)
        )
        # 3. Select top N tasks for today's plan
        todays_plan_tasks_content = [
            task["content"] for task in ranked_tasks[:5]
        ]  # Top 5
        logger_planning.info(f"Today's prioritized plan: {todays_plan_tasks_content}")
        # 4. Write out a top-N "today's plan" memory
        plan_content = f"Autonomous plan for today: {todays_plan_tasks_content}"
        if hasattr(self.chat_engine, "store_memory"):
            self.chat_engine.store_memory(
                text=plan_content,
                role="system_autonomous_planner",
                custom_metadata={
                    "anchor_type": "daily_plan",
                    "plan_tasks": todays_plan_tasks_content,
                    "status": "new",
                },
            )
            logger_planning.info("Daily plan stored in memory.")
        else:
            logger_planning.warning(
                "Memory accessor lacks 'store_memory'. Plan not stored."
            )
        return ranked_tasks[:5]


class CodingAgent:
    def __init__(self, memory_accessor: Any, dev_agent_instance: Any):
        self.memory_accessor = memory_accessor
        self.dev_agent = (
            dev_agent_instance  # e.g., DevAgentStub() or a real LangChain agent
        )
        logger_coding.info("CodingAgent initialized.")

    def execute_plan(self, tasks: List[str]) -> List[Dict[str, Any]]:
        logger_coding.info(f"CodingAgent received plan: {tasks}")
        results = []
        if not tasks:
            logger_coding.info("No tasks in the plan to execute.")
            return results

        for task_description in tasks:
            logger_coding.info(f"Executing dev task: {task_description}")
            try:
                dev_result = self.dev_agent.execute_dev_task(task_description)
                results.append({"task": task_description, "result": dev_result})

                self.memory_accessor.store_memory(
                    text=f"CodingAgent result for task '{task_description}': {dev_result.get('status', 'unknown')}. Details: {dev_result.get('log', '')[:500]}",
                    role="system_autonomous_coder",
                    custom_metadata={
                        "anchor_type": "auto_code_result",
                        "task_description": task_description,
                        "status": dev_result.get("status", "unknown"),
                        "code_snippet": dev_result.get("code_generated", None),
                    },
                )
                logger_coding.info(f"Result for task '{task_description}' logged.")
            except Exception as e:
                logger_coding.error(
                    f"Error executing dev task '{task_description}': {e}", exc_info=True
                )
                results.append(
                    {
                        "task": task_description,
                        "result": {"status": "error", "error": str(e)},
                    }
                )
                self.memory_accessor.store_memory(
                    text=f"CodingAgent ERROR for task '{task_description}': {str(e)}",
                    role="system_autonomous_coder",
                    custom_metadata={
                        "anchor_type": "auto_code_error",
                        "task_description": task_description,
                    },
                )

        logger_coding.info("All planned coding tasks processed.")
        return results


class TestingAgent:
    """
    The TestingAgent executes tests (e.g., pytest), parses results, logs them, and can create new tasks for PlanningAgent if tests fail.
    """

    def __init__(self, chat_engine_instance, llm_client, covenant_enforcer):
        self.chat_engine = chat_engine_instance
        self.llm_client = llm_client
        self.covenant_enforcer = covenant_enforcer
        logger_testing.info("TestingAgent initialized.")

    def run_tests(self) -> Dict[str, Any]:
        """
        Run tests and return structured results.
        """
        logger_testing.info("Running tests...")
        report = {"success": False, "summary": "Tests not executed.", "full_output": ""}

        test_command = ["python", "-m", "pytest", "-q"]  # Basic quiet pytest

        try:
            process = subprocess.run(
                test_command,
                cwd=self.project_root_path,
                capture_output=True,
                text=True,
                timeout=300,
            )
            report["full_output"] = process.stdout + "\n" + process.stderr

            if process.returncode == 0:
                report["success"] = True
                report["summary"] = "All tests passed."
                logger_testing.info("Tests passed.")
            elif process.returncode == 1:
                report["summary"] = "Some tests failed."
                logger_testing.warning("Tests failed.")
            elif process.returncode == 5:
                report["summary"] = "No tests were collected."
                report["success"] = True
                logger_testing.info("No tests collected.")
            else:
                report["summary"] = (
                    f"Test execution error. Exit code: {process.returncode}."
                )
                logger_testing.error(
                    f"Test execution error. Output: {report['full_output']}"
                )

        except subprocess.TimeoutExpired:
            report["summary"] = "Test execution timed out."
            report["full_output"] = "Timeout after 300 seconds."
            logger_testing.error("Test execution timed out.")
        except FileNotFoundError:
            report["summary"] = (
                "'pytest' command not found. Is it installed and in PATH?"
            )
            report["full_output"] = "pytest not found."
            logger_testing.error(report["summary"])
        except Exception as e:
            report["summary"] = f"An error occurred during testing: {e}"
            report["full_output"] = str(e)
            logger_testing.error(report["summary"], exc_info=True)

        self.chat_engine.store_memory(
            text=f"TestingAgent Report: {report['summary']}. Output head: {report['full_output'][:500]}",
            role="ade_tester",
            custom_metadata={
                "anchor_type": "test_report",
                "success": report["success"],
                "summary": report["summary"],
            },
        )

        if not report["success"] and report["summary"] == "Some tests failed.":
            logger_testing.info(
                "Tests failed, creating a 'Fix failing tests' task for tomorrow."
            )
            self.chat_engine.store_memory(
                text="Fix failing tests from previous run.",
                role="system_autonomous_planner",
                custom_metadata={
                    "anchor_type": "task",
                    "status": "unfinished",
                    "priority": 0,
                    "origin": "TestingAgent",
                },
            )
        logger_testing.info("Test run and reporting complete.")
        return report


class MonitoringAgent:
    """
    The MonitoringAgent checks system health, logs status, and can attempt healing routines or create tasks for PlanningAgent.
    """

    def __init__(
        self, chat_engine_instance, llm_client, covenant_enforcer, config=None
    ):
        self.chat_engine = chat_engine_instance
        self.llm_client = llm_client
        self.covenant_enforcer = covenant_enforcer
        config = config or {}
        self.ram_threshold = config.get("ram_threshold_percent", 80.0)
        self.disk_threshold = config.get("disk_threshold_percent", 90.0)
        self.log_file_path = config.get("error_log_path", "data/error.log")
        logger_monitoring.info(
            f"MonitoringAgent initialized. RAM Threshold: {self.ram_threshold}%, Disk Threshold: {self.disk_threshold}%."
        )

    def run(self) -> Dict[str, Any]:
        """
        Check system health and log status.
        """
        logger_monitoring.info("Performing system health check...")
        alerts = []

        # Check RAM Usage
        ram_percent = psutil.virtual_memory().percent
        if ram_percent > self.ram_threshold:
            alert_msg = f"High RAM usage detected: {ram_percent:.2f}% (Threshold: {self.ram_threshold}%)"
            logger_monitoring.warning(alert_msg)
            alerts.append(
                {"type": "ram_usage", "value": ram_percent, "message": alert_msg}
            )
            self._attempt_healing("ram_usage")

        # Check Disk Usage (for the partition where the app is running or a specified path)
        disk_usage = psutil.disk_usage("/").percent
        if disk_usage > self.disk_threshold:
            alert_msg = f"High Disk usage detected: {disk_usage:.2f}% (Threshold: {self.disk_threshold}%)"
            logger_monitoring.warning(alert_msg)
            alerts.append(
                {"type": "disk_usage", "value": disk_usage, "message": alert_msg}
            )
            self._attempt_healing("disk_usage")

        # Placeholder for error log checks
        # recent_errors = self._check_error_logs()
        # if recent_errors:
        #     alerts.append({"type": "error_log", "count": len(recent_errors), "message": f"Found {len(recent_errors)} new critical errors."})
        #     self._attempt_healing("error_log")

        if alerts:
            self.chat_engine.store_memory(
                text=f"MonitoringAgent Health Alert: {len(alerts)} issues detected. First: {alerts[0]['message']}",
                role="ade_monitor",
                custom_metadata={"anchor_type": "health_alert", "alerts": alerts},
            )
        else:
            logger_monitoring.info("System health normal.")
        return alerts

    def _attempt_healing(self, issue_type: str):
        logger_monitoring.info(f"Attempting to apply healing routine for: {issue_type}")
        # Placeholder for actual healing routines
        self.chat_engine.store_memory(
            text=f"MonitoringAgent: Attempted healing for {issue_type}.",
            role="ade_monitor",
            custom_metadata={"anchor_type": "healing_attempt", "issue": issue_type},
        )
        logger_monitoring.info(f"Healing attempt logged for {issue_type}.")
