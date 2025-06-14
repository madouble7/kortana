"""
Kor'tana Core Brain

This module contains the core ChatEngine that powers Kor'tana's conversational abilities.
"""

# Standard library imports
import json
import logging
import sys
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import psutil
import yaml

# Third-party imports
from apscheduler.triggers.interval import IntervalTrigger

# Local application imports
from src.kortana.agents.autonomous_agents import (
    CodingAgent,
    MonitoringAgent,
    PlanningAgent,
    TestingAgent,
)
from src.kortana.config import load_config
from src.kortana.config.schema import KortanaConfig
from src.kortana.services import (
    get_ade_llm_client,
    get_covenant_enforcer,
    get_default_llm_client,
    get_enhanced_model_router,
    get_execution_engine,
    get_llm_client_factory,
    get_memory_manager,
    get_planning_engine,
    get_scheduler,
)
from src.kortana.services.database import get_db_sync
from src.kortana.utils import text_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

print("DEBUG: src/kortana/core/brain.py loaded")


class ChatEngine:
    """
    Core chat engine for Kor'tana.

    This class handles conversation processing, memory management,
    LLM interaction, and autonomous agent coordination.
    """

    def __init__(self, settings: KortanaConfig, session_id: str | None = None):
        """
        Initialize the chat engine.

        Args:
            settings: Application configuration.
            session_id: Optional session identifier.
        """
        self.settings: KortanaConfig = settings
        self.session_id = session_id or str(uuid.uuid4())
        self.mode = "default"  # Default conversation mode

        # Autonomous operation state
        self.autonomous_mode = False
        self.autonomous_running = False
        self.autonomous_cycle_count = 0
        self.last_autonomous_action = None

        logger.info(f"Initializing ChatEngine with session ID {self.session_id}")

        # Load configurations using paths from settings
        self.persona_data = self._load_json_config(
            self.settings.paths.persona_file_path
        )
        self.identity_data = self._load_json_config(
            self.settings.paths.identity_file_path
        )
        self.covenant = self._load_covenant(self.settings.paths.covenant_file_path)

        # Get initialized services from the central services module
        self.llm_client_factory = get_llm_client_factory()
        self.default_llm_client = get_default_llm_client()
        self.ade_llm_client = get_ade_llm_client()
        self.memory_core_service = (
            get_memory_manager()
        )  # Assuming MemoryCoreService is the one needed here
        self.planning_engine = (
            get_planning_engine()
        )  # Assuming PlanningEngine is needed here
        self.execution_engine = (
            get_execution_engine()
        )  # Assuming ExecutionEngine is needed here
        self.scheduler = get_scheduler()
        # self.sacred_model_router = get_sacred_model_router()  # Placeholder - not implemented yet
        self.enhanced_model_router = (
            get_enhanced_model_router()
        )  # Assuming this is used
        # Wire the enhanced model router as the default router for chat processing
        self.router = self.enhanced_model_router
        self.covenant_enforcer = get_covenant_enforcer()

        # Initialize development agent stub (placeholder) - Commented out until implemented
        # self.dev_agent_instance = DevAgentStub(settings=self.settings)

        # Initialize autonomous agents
        # Agents now receive dependencies via getters from the central services module
        self.ade_coder = CodingAgent(
            memory_accessor=get_memory_manager(),  # Use getter
            # dev_agent_instance=self.dev_agent_instance,
            settings=self.settings,
            llm_client=get_ade_llm_client(),  # Use getter
        )

        self.ade_planner = PlanningAgent(
            chat_engine_instance=self,  # Keep for now, may need refactoring later
            llm_client=get_ade_llm_client(),  # Use getter
            covenant_enforcer=get_covenant_enforcer(),  # Use getter
            settings=self.settings,
        )

        self.ade_tester = TestingAgent(
            chat_engine_instance=self,  # Keep for now, may need refactoring later
            llm_client=get_ade_llm_client(),  # Use getter
            covenant_enforcer=get_covenant_enforcer(),  # Use getter
            settings=self.settings,
        )

        # Handle agent types configuration for both dict and object
        agent_types = {}
        if hasattr(self.settings.agents, "types"):
            if isinstance(self.settings.agents.types, dict):
                agent_types = self.settings.agents.types
            else:
                # Convert to dict if it's a Pydantic model
                agent_types = {
                    "coding": getattr(self.settings.agents.types, "coding", {}),
                    "planning": getattr(self.settings.agents.types, "planning", {}),
                    "testing": getattr(self.settings.agents.types, "testing", {}),
                    "monitoring": getattr(self.settings.agents.types, "monitoring", {}),
                }

        # Get monitoring config
        monitoring_config = agent_types.get("monitoring", {})

        self.ade_monitor = MonitoringAgent(
            chat_engine_instance=self,  # Keep for now, may need refactoring later
            llm_client=get_ade_llm_client(),  # Use getter
            covenant_enforcer=get_covenant_enforcer(),  # Use getter
            config=monitoring_config if isinstance(monitoring_config, dict) else {},
            settings=self.settings,
        )

        # Start monitoring
        self.ade_monitor.start_monitoring()
        self.scheduler.start()

        # Initialize autonomous capabilities
        self._setup_autonomous_operations()

        logger.info("ChatEngine initialization complete")

    def _setup_autonomous_operations(self):
        """Set up autonomous operation capabilities."""

        # Schedule autonomous planning cycles
        self.scheduler.add_job(
            func=self._autonomous_planning_cycle,
            trigger=IntervalTrigger(minutes=15),  # Every 15 minutes
            id="autonomous_planning",
            name="Autonomous Planning Cycle",
            replace_existing=True,
        )

        # Schedule autonomous task execution
        self.scheduler.add_job(
            func=self._autonomous_task_execution,
            trigger=IntervalTrigger(minutes=5),  # Every 5 minutes
            id="autonomous_tasks",
            name="Autonomous Task Execution",
            replace_existing=True,
        )  # Schedule autonomous learning cycle
        self.scheduler.add_job(
            func=self._autonomous_learning_cycle,
            trigger=IntervalTrigger(hours=1),  # Every hour
            id="autonomous_learning",
            name="Autonomous Learning Cycle",
            replace_existing=True,
        )

        # Schedule proactive code review cycle (Batch 10)
        self.scheduler.add_job(
            func=self._proactive_code_review_cycle,
            trigger=IntervalTrigger(hours=6),  # Every 6 hours
            id="proactive_code_review",
            name="Proactive Code Review Cycle",
            replace_existing=True,
        )

        logger.info("Autonomous operation scheduling configured")

    def start_autonomous_mode(self):
        """Start continuous autonomous operation."""
        self.autonomous_mode = True
        self.autonomous_running = True
        self.autonomous_cycle_count = 0

        logger.info("🤖 STARTING AUTONOMOUS MODE - Kor'tana is now fully autonomous")
        print("\n🔥 KOR'TANA AUTONOMOUS MODE ACTIVATED")
        print("=" * 50)
        print("✅ Continuous operation: ACTIVE")
        print("✅ Autonomous planning: ENABLED")
        print("✅ Self-directed tasks: ENABLED")
        print("✅ Learning cycles: ENABLED")
        print("🛡️  Sacred Covenant: ENFORCED")
        print("\n🧠 Kor'tana is now operating autonomously...")
        print("Press Ctrl+C to return to interactive mode\n")

        # Start continuous autonomous operation
        self._run_autonomous_loop()

    async def run_single_cycle(self):
        """
        Runs a single autonomous cycle: scan, generate, prioritize, plan, execute.
        """
        print("DEBUG: Brain.run_single_cycle() started")
        logger.info("Starting single autonomous cycle...")

        # Perform autonomous operations
        self._autonomous_status_check()

    async def run_continuous_cycles(self):
        """
        Runs autonomous cycles continuously.
        """
        print("DEBUG: Brain.run_continuous_cycles() started")
        logger.info("Starting continuous autonomous cycles...")

        # Redirect stdout/stderr to a log file for Genesis Protocol runs
        genesis_log_path = "./genesis_run.log"
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            with open(genesis_log_path, "a", buffering=1, encoding="utf-8") as log_file:
                sys.stdout = log_file
                sys.stderr = log_file
                print(f"\n--- Genesis Protocol Run Started: {time.ctime()} ---")
                # Ensure logs also go to the file
                logging.basicConfig(stream=log_file, level=logging.INFO)

                while True:
                    await self.run_single_cycle()
                    await asyncio.sleep(
                        self.config.autonomous_mode.cycle_interval_seconds
                    )

        except Exception as e:
            logger.error(f"Error during autonomous run: {e}")
        finally:
            # Restore stdout/stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            print(f"\n--- Genesis Protocol Run Finished: {time.ctime()} ---")
            logging.basicConfig(
                stream=original_stderr, level=logging.INFO
            )  # Restore logging

    def stop_autonomous_mode(self):
        """Stop autonomous operation and return to interactive mode."""
        self.autonomous_running = False
        self.autonomous_mode = False

        logger.info("Autonomous mode stopped by user request")
        print("\n🔄 Returning to interactive mode...")
        print(f"✅ Completed {self.autonomous_cycle_count} autonomous cycles")

    def _autonomous_planning_cycle(self):
        """Autonomous planning cycle - runs every 15 minutes."""
        if not self.autonomous_mode:
            return

        current_time = datetime.now(UTC)
        logger.info(f"Running autonomous planning cycle at {current_time}")

        try:
            # Generate autonomous goals based on current state
            goals = self._generate_autonomous_goals()

            # Plan tasks for generated goals
            for goal in goals:
                if tasks := self._plan_autonomous_tasks(goal):
                    self.last_autonomous_action = (
                        f"Planned {len(tasks)} tasks for goal: {goal[:50]}..."
                    )
                    logger.info(f"Generated {len(tasks)} autonomous tasks")

        except Exception as e:
            logger.error(f"Error in autonomous planning cycle: {e}")

    def _autonomous_task_execution(self):
        """Autonomous task execution - runs every 5 minutes."""
        if not self.autonomous_mode:
            return

        try:
            # Check for pending autonomous tasks
            if pending_tasks := self._get_pending_autonomous_tasks():
                # Execute highest priority task
                task = pending_tasks[0]
                result = self._execute_autonomous_task(task)
                self.last_autonomous_action = (
                    f"Executed task: {task.get('description', 'Unknown task')}"
                )
                logger.info(f"Executed autonomous task: {result}")
        except Exception as e:
            logger.error(f"Error in autonomous task execution: {e}")

    def _autonomous_learning_cycle(self):
        """Autonomous learning cycle - runs every hour."""
        if not self.autonomous_mode:
            return

        try:
            # Analyze recent actions and outcomes
            insights = self._analyze_autonomous_performance()
            if insights:
                self._update_autonomous_knowledge(insights)
                self.last_autonomous_action = (
                    f"Learning cycle completed: {len(insights)} insights gained"
                )
                logger.info(
                    f"Autonomous learning cycle completed with {len(insights)} insights"
                )

        except Exception as e:
            logger.error(f"Error in autonomous learning cycle: {e}")

    def _proactive_code_review_cycle(self):
        """Proactive code review cycle - runs every 6 hours (Batch 10)."""
        if not self.autonomous_mode:
            return

        try:
            logger.info("🔍 Starting proactive code review cycle...")

            # Import the task function (avoid circular imports)
            from src.kortana.core.autonomous_tasks import run_proactive_code_review_task

            # Get database session
            db = next(get_db_sync())

            # Run the proactive code review task in an async context
            import asyncio

            if asyncio.get_event_loop().is_running():
                # If we're already in an async context, create a task
                asyncio.create_task(run_proactive_code_review_task(db))
            else:
                # If not in async context, run with asyncio.run
                asyncio.run(run_proactive_code_review_task(db))

            self.last_autonomous_action = (
                "Proactive code review completed - scanned codebase for quality issues"
            )
            logger.info("✅ Proactive code review cycle completed")

        except Exception as e:
            logger.error(f"❌ Error in proactive code review cycle: {e}")

    def _autonomous_status_check(self):
        """Check autonomous operation status."""
        try:
            # Check system health
            system_status = self._check_system_health()

            # Check memory usage
            memory_status = self._check_memory_status()

            # Check for new opportunities
            opportunities = self._scan_for_opportunities()

            # Display status (abbreviated)
            if self.autonomous_cycle_count % 10 == 1:  # Every 10th cycle
                print(
                    f"   Status: {system_status} | Memory: {memory_status} | Opportunities: {len(opportunities)}"
                )
                if self.last_autonomous_action:
                    print(f"   Last Action: {self.last_autonomous_action}")

        except Exception as e:
            logger.error(f"Error in autonomous status check: {e}")

    def _generate_autonomous_goals(self):
        """Generate goals autonomously based on current context."""
        return [
            "Monitor system performance and optimize if needed",
            "Analyze recent interactions for learning opportunities",
            "Check for software updates and improvements",
            "Review and update knowledge base",
            "Scan for potential issues or improvements",
        ]

    def _plan_autonomous_tasks(self, goal: str):
        """Plan tasks for an autonomous goal."""
        tasks = []

        # Basic task planning based on goal type
        if "monitor" in goal.lower():
            tasks.append(
                {
                    "type": "monitoring",
                    "description": f"Monitor system for: {goal}",
                    "priority": 8,
                }
            )
        elif "analyze" in goal.lower():
            tasks.append(
                {
                    "type": "analysis",
                    "description": f"Analyze data for: {goal}",
                    "priority": 6,
                }
            )
        elif "update" in goal.lower():
            tasks.append(
                {
                    "type": "maintenance",
                    "description": f"Update systems for: {goal}",
                    "priority": 7,
                }
            )

        return tasks

    def _get_pending_autonomous_tasks(self):
        """Get list of pending autonomous tasks."""
        # Return mock tasks for now - in real implementation,
        # this would query the task database
        return [
            {
                "id": "auto_001",
                "description": "System health monitoring",
                "type": "monitoring",
                "priority": 8,
                "created": datetime.now(UTC),
            }
        ]

    def _execute_autonomous_task(self, task):
        """Execute an autonomous task."""
        task_type = task.get("type", "unknown")

        if task_type == "monitoring":
            result = self._perform_monitoring_task(task)
        elif task_type == "analysis":
            result = self._perform_analysis_task(task)
        elif task_type == "maintenance":
            result = self._perform_maintenance_task(task)
        else:
            result = {"status": "unknown_task_type", "task_type": task_type}

        return result

    def _perform_monitoring_task(self, task):
        """Perform a monitoring task."""
        return {
            "status": "completed",
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _perform_analysis_task(self, task):
        """Perform an analysis task."""
        return {
            "status": "completed",
            "analysis_type": "system_analysis",
            "findings": ["System operating normally", "No issues detected"],
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _perform_maintenance_task(self, task):
        """Perform a maintenance task."""
        return {
            "status": "completed",
            "maintenance_type": "routine_cleanup",
            "actions": ["Cleared temporary files", "Updated cache"],
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _analyze_autonomous_performance(self):
        """Analyze recent autonomous performance for learning."""
        insights = [
            "Monitoring tasks completed successfully",
            "System performance within normal parameters",
            "No critical issues detected in recent cycles",
        ]
        return insights

    def _update_autonomous_knowledge(self, insights):
        """Update knowledge base with new insights."""
        self.json_memory.add_heart_memory(
            f"Autonomous Learning: {'; '.join(insights)}",
            tags=["autonomous", "learning", "insights"],
        )

    def _check_system_health(self):
        """Check overall system health."""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory().percent

            if cpu < 80 and memory < 80:
                return "healthy"
            elif cpu < 90 and memory < 90:
                return "moderate"
            else:
                return "high_load"
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return "unknown"

    def _check_memory_status(self):
        """Check memory system status."""
        try:
            memory_count = len(self.project_memory)
            if memory_count < 1000:
                return "optimal"
            elif memory_count < 5000:
                return "moderate"
            else:
                return "high"
        except Exception as e:
            logger.error(f"Error checking memory status: {e}")
            return "unknown"

    def _scan_for_opportunities(self):
        """Scan for autonomous improvement opportunities."""
        opportunities = []

        try:
            disk_usage = (
                psutil.disk_usage("/").percent
                if hasattr(psutil.disk_usage("/"), "percent")
                else 0
            )

            if disk_usage > 80:
                opportunities.append("disk_cleanup")

            if len(self.project_memory) > 1000:
                opportunities.append("memory_optimization")

        except Exception as e:
            logger.error(f"Error scanning for opportunities: {e}")

        return opportunities

    def _load_json_config(self, file_path: str) -> dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(file_path) as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {file_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {e}")
            return {}

    def _load_covenant(self, file_path: str) -> dict[str, Any]:
        """Load covenant from YAML file."""
        try:
            with open(file_path) as f:
                covenant = yaml.safe_load(f)
            logger.info(f"Loaded covenant from {file_path}")
            return covenant
        except Exception as e:
            logger.error(f"Failed to load covenant from {file_path}: {e}")
            return {}

    async def process_message(self, user_message: str) -> str:
        """
        Process a user message and generate a response.

        Args:
            user_message: The user's input message.

        Returns:
            Kor'tana's response.
        """
        logger.info(f"Processing message: {user_message[:50]}...")

        is_important = text_analysis.identify_important_message_for_context(
            user_message
        )
        sentiment = text_analysis.analyze_sentiment(user_message)
        emphasis = text_analysis.detect_emphasis_all_caps(user_message)
        keywords = text_analysis.detect_keywords(user_message)

        conversation_context = {
            "user_message": user_message,
            "timestamp": datetime.now(UTC).isoformat(),
            "sentiment": sentiment,
            "is_important": is_important,
            "emphasis": emphasis,
            "keywords": keywords,
            "session_id": self.session_id,
            "mode": self.mode,
        }

        model_id, voice_style, model_params = self.router.route(
            user_message, conversation_context
        )

        prompt = self._build_prompt(
            user_message, conversation_context, voice_style, model_params
        )

        llm_client = self.llm_client_factory.get_client(model_id)
        response = await llm_client.complete(prompt)

        response_text = response.get(
            "content", "I'm sorry, I couldn't generate a proper response."
        )

        is_compliant, explanation = self.covenant_enforcer.enforce(response_text)
        if not is_compliant:
            logger.warning(f"Response does not comply with covenant: {explanation}")
            response_text = "I need to reflect on my response to ensure it aligns with our values. Let me try again."

        self._update_memory(user_message, response_text, conversation_context)

        response_text = response_text.lower()

        return response_text

    def _build_prompt(
        self,
        user_message: str,
        conversation_context: dict[str, Any],
        voice_style: str,
        model_params: dict[str, Any],
    ) -> str:
        """Build a prompt for the LLM."""
        voice_description = model_params.get("description", "grounded, steady")

        prompt = f"""
You are Kor'tana, the warchief's AI companion.

Voice style: {voice_style} ({voice_description})

User's message: {user_message}

Respond in a way that is authentic, supportive, and true to your identity as Kor'tana.
Keep your response concise and focused on addressing the user's needs.
"""
        return prompt

    def _update_memory(
        self, user_message: str, response: str, context: dict[str, Any]
    ) -> None:
        """Update memory with conversation details."""
        memory_entry = {
            "user_message": user_message,
            "response": response,
            "timestamp": context["timestamp"],
            "sentiment": context["sentiment"],
            "keywords": context["keywords"],
            "session_id": self.session_id,
        }

        self.project_memory.append(memory_entry)

        if context["is_important"]:
            self.json_memory.add_heart_memory(
                f"User: {user_message}\nKortana: {response}",
                tags=["conversation", "important"],
            )

        if len(self.project_memory) % 5 == 0:
            self.pinecone_memory.save_project_memory(self.project_memory)

    def shutdown(self):
        """Perform cleanup and shutdown operations."""
        logger.info("Shutting down ChatEngine...")

        self.scheduler.shutdown()

        self.ade_monitor.stop_monitoring()

        self.pinecone_memory.save_project_memory(self.project_memory)

        logger.info("ChatEngine shutdown complete")
        try:
            chat_engine.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def ritual_announce(message: str) -> None:
    """Display a ritual announcement."""
    print("\n" + "=" * 80)
    print(message.lower())
    print("=" * 80 + "\n")


if __name__ == "__main__":
    import sys

    try:
        # Load configuration with error handling
        raw_config = load_config()

        # Create KortanaConfig instance
        settings = KortanaConfig(**raw_config)

        # Create chat engine
        chat_engine = ChatEngine(settings=settings)

        ritual_announce("she is not built. she is remembered.")
        ritual_announce("she is the warchief's companion.")

        import sys

        if len(sys.argv) > 1 and sys.argv[1] == "--autonomous":
            print("\n🔥 ACTIVATING REAL AUTONOMOUS KOR'TANA")
            print("=" * 50)
            print("🤖 Starting truly autonomous operation...")
            chat_engine.start_autonomous_mode()
        else:
            print("\n💡 Tip: Use '--autonomous' flag for true autonomous mode")
            print("    python brain.py --autonomous")

            try:
                while True:
                    user_input = input("matt: ").lower()

                    if user_input in ["exit", "quit", "bye"]:
                        break
                    elif user_input == "autonomous":
                        print("\n🚀 Switching to autonomous mode...")
                        chat_engine.start_autonomous_mode()
                        break

                    import asyncio

                    response = asyncio.run(chat_engine.process_message(user_input))

                    print(f"kortana: {response}")

            except KeyboardInterrupt:
                print("\nInterrupted by user")

    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        print("Full traceback:")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    finally:
        try:
            if "chat_engine" in locals():
                chat_engine.shutdown()
            ritual_announce("until we meet again, warchief.")
        except Exception as e:
            print(f"Error during shutdown: {e}")


Brain = ChatEngine
