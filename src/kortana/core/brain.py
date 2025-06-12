"""
Kor'tana Core Brain

This module contains the core ChatEngine that powers Kor'tana's conversational abilities.
"""
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from config.schema import KortanaConfig

from src.kortana.config import load_config
from src.dev_agent_stub import DevAgentStub
from src.kortana.agents.autonomous_agents import (CodingAgent, MonitoringAgent,
                                                  PlanningAgent, TestingAgent)
from src.kortana.core.covenant_enforcer import CovenantEnforcer
from src.kortana.memory.memory import MemoryManager as JsonLogMemoryManager
from src.kortana.memory.memory_manager import \
    MemoryManager as PineconeMemoryManager
from src.kortana.utils import text_analysis
from src.llm_clients.factory import LLMClientFactory
from src.model_router import SacredModelRouter

try:
    from src.sacred_trinity_router import SacredTrinityRouter
except ImportError:
    # Create a stub if the module doesn't exist
    class SacredTrinityRouter:
        def __init__(self, settings):
            self.settings = settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ChatEngine:
    """
    Core chat engine for Kor'tana.

    This class handles conversation processing, memory management,
    LLM interaction, and autonomous agent coordination.
    """

    def __init__(self, settings: KortanaConfig, session_id: Optional[str] = None):
        """
        Initialize the chat engine.

        Args:
            settings: Application configuration.
            session_id: Optional session identifier.
        """
        self.settings = settings
        self.session_id = session_id or str(uuid.uuid4())
        self.mode = "default"  # Default conversation mode

        logger.info(f"Initializing ChatEngine with session ID {self.session_id}")

        # Load configurations using paths from settings
        self.persona_data = self._load_json_config(self.settings.paths.persona_file_path)
        self.identity_data = self._load_json_config(self.settings.paths.identity_file_path)
        self.covenant = self._load_covenant(self.settings.paths.covenant_file_path)

        # Initialize LLM clients
        self.llm_client_factory = LLMClientFactory(settings=self.settings)
        LLMClientFactory.validate_configuration(self.settings)
        self.default_llm_client = self.llm_client_factory.get_client(self.settings.default_llm_id)
        self.ade_llm_client = self.llm_client_factory.get_client(self.settings.agents.default_llm_id)

        # Initialize memory systems
        self.pinecone_memory = PineconeMemoryManager(settings=self.settings)
        self.json_memory = JsonLogMemoryManager(settings=self.settings)
        self.project_memory = self.pinecone_memory.load_project_memory()

        # Initialize routers and enforcers
        self.router = SacredModelRouter(settings=self.settings)
        self.covenant_enforcer = CovenantEnforcer(settings=self.settings)

        # Initialize scheduler for background tasks
        self.scheduler = BackgroundScheduler()

        # Initialize development agent stub (placeholder)
        self.dev_agent_instance = DevAgentStub(settings=self.settings)

        # Initialize autonomous agents
        self.ade_coder = CodingAgent(
            memory_accessor=self.pinecone_memory,
            dev_agent_instance=self.dev_agent_instance,
            settings=self.settings,
            llm_client=self.ade_llm_client
        )

        self.ade_planner = PlanningAgent(
            chat_engine_instance=self,
            llm_client=self.ade_llm_client,
            covenant_enforcer=self.covenant_enforcer,
            settings=self.settings
        )

        self.ade_tester = TestingAgent(
            chat_engine_instance=self,
            llm_client=self.ade_llm_client,
            covenant_enforcer=self.covenant_enforcer,
            settings=self.settings
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
                    "monitoring": getattr(self.settings.agents.types, "monitoring", {})
                }

        # Get monitoring config
        monitoring_config = agent_types.get("monitoring", {})

        self.ade_monitor = MonitoringAgent(
            chat_engine_instance=self,
            llm_client=self.ade_llm_client,
            covenant_enforcer=self.covenant_enforcer,
            config=monitoring_config,
            settings=self.settings
        )

        # Start monitoring
        self.ade_monitor.start_monitoring()
        self.scheduler.start()

        logger.info("ChatEngine initialization complete")

    def _load_json_config(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {file_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {e}")
            return {}

    def _load_covenant(self, file_path: str) -> Dict[str, Any]:
        """Load covenant from YAML file."""
        try:
            with open(file_path, 'r') as f:
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

        # Analyze message
        is_important = text_analysis.identify_important_message_for_context(user_message)
        sentiment = text_analysis.analyze_sentiment(user_message)
        emphasis = text_analysis.detect_emphasis_all_caps(user_message)
        keywords = text_analysis.detect_keywords(user_message)

        conversation_context = {
            "user_message": user_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sentiment": sentiment,
            "is_important": is_important,
            "emphasis": emphasis,
            "keywords": keywords,
            "session_id": self.session_id,
            "mode": self.mode
        }

        # Determine which model and voice style to use
        model_id, voice_style, model_params = self.router.route(user_message, conversation_context)

        # Get relevant memories
        # memories = self.pinecone_memory.search_memory(user_message, top_k=5)

        # Prepare prompt
        prompt = self._build_prompt(user_message, conversation_context, voice_style, model_params)

        # Generate response using the selected model
        llm_client = self.llm_client_factory.get_client(model_id)
        response = await llm_client.complete(prompt)

        # Extract response text
        response_text = response.get("content", "I'm sorry, I couldn't generate a proper response.")

        # Check response against covenant
        is_compliant, explanation = self.covenant_enforcer.enforce(response_text)
        if not is_compliant:
            logger.warning(f"Response does not comply with covenant: {explanation}")
            response_text = "I need to reflect on my response to ensure it aligns with our values. Let me try again."

        # Update memory with the conversation
        self._update_memory(user_message, response_text, conversation_context)

        # Apply lowercase transformation
        response_text = response_text.lower()

        return response_text

    def _build_prompt(
        self,
        user_message: str,
        conversation_context: Dict[str, Any],
        voice_style: str,
        model_params: Dict[str, Any]
    ) -> str:
        """Build a prompt for the LLM."""
        # A simple prompt template - in a real implementation, this would be more sophisticated
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
        self,
        user_message: str,
        response: str,
        context: Dict[str, Any]
    ) -> None:
        """Update memory with conversation details."""
        # In a real implementation, this would use more sophisticated memory management
        memory_entry = {
            "user_message": user_message,
            "response": response,
            "timestamp": context["timestamp"],
            "sentiment": context["sentiment"],
            "keywords": context["keywords"],
            "session_id": self.session_id
        }

        # Add to project memory
        self.project_memory.append(memory_entry)

        # Save to memory files
        if context["is_important"]:
            self.json_memory.add_heart_memory(
                f"User: {user_message}\nKortana: {response}",
                tags=["conversation", "important"]
            )

        # Save project memory periodically
        if len(self.project_memory) % 5 == 0:  # Save every 5 messages
            self.pinecone_memory.save_project_memory(self.project_memory)

    def shutdown(self):
        """Perform cleanup and shutdown operations."""
        logger.info("Shutting down ChatEngine...")

        # Stop scheduler
        self.scheduler.shutdown()

        # Stop monitoring
        self.ade_monitor.stop_monitoring()

        # Save memory
        self.pinecone_memory.save_project_memory(self.project_memory)

        logger.info("ChatEngine shutdown complete")


def ritual_announce(message: str) -> None:
    """Display a ritual announcement."""
    print("\n" + "=" * 80)
    print(message.lower())
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Load configuration
    settings = load_config()

    # Create chat engine
    chat_engine = ChatEngine(settings=settings)

    # Welcome message
    ritual_announce("she is not built. she is remembered.")
    ritual_announce("she is the warchief's companion.")

    # Main loop
    try:
        while True:
            # Get user input (lowercase for "matt")
            user_input = input("matt: ").lower()

            # Check for exit command
            if user_input in ["exit", "quit", "bye"]:
                break

            # Process message
            import asyncio
            response = asyncio.run(chat_engine.process_message(user_input))

            # Print response (lowercase for "kortana")
            print(f"kortana: {response}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        # Shutdown
        chat_engine.shutdown()
        ritual_announce("until we meet again, warchief.")
