"""
ADE Coordinator - Integrates autonomous development with existing agents
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from autonomous_development_engine import create_ade
from autonomous_agents import PlanningAgent, CodingAgent, TestingAgent, MonitoringAgent

class ADECoordinator:
    """
    Coordinates between the new Autonomous Development Engine and existing agents
    """
    
    def __init__(self, chat_engine):
        self.chat_engine = chat_engine
        self.ade = create_ade(
            chat_engine.llm_clients.get(chat_engine.default_model_id),
            chat_engine.covenant_enforcer,
            chat_engine.memory_manager
        )
        
        # Existing agents
        self.planning_agent = chat_engine.ade_planner
        self.coding_agent = getattr(chat_engine, 'ade_coder', None)
        self.testing_agent = chat_engine.ade_tester
        self.monitoring_agent = chat_engine.ade_monitor
        
    async def start_autonomous_session(self, goals: List[str]):
        """Start a coordinated autonomous development session"""
        logging.info(f"🚀 Starting coordinated ADE session with goals: {goals}")
        
        # Run new ADE engine
        ade_results = await self.ade.autonomous_development_cycle(goals, max_cycles=2)
        
        # Coordinate with existing agents
        for result in ade_results:
            if result.get("success"):
                # Trigger testing after successful code changes
                if "generate_code" in str(result.get("results", [])):
                    test_result = self.testing_agent.run_tests()
                    logging.info(f"Tests after code generation: {test_result}")
                
                # Monitor system health
                health = self.monitoring_agent.run()
                logging.info(f"System health check: {health}")
        
        return {
            "ade_results": ade_results,
            "session_completed": datetime.now(timezone.utc).isoformat(),
            "goals_processed": len(goals)
        }
    
    def add_development_goal(self, goal: str):
        """Add a new development goal for autonomous processing"""
        goal_entry = {
            "role": "ade_goal",
            "content": goal,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            "metadata": {"source": "ade_coordinator", "added_by": "Matt"}
        }
        
        # Store in memory
        self.chat_engine._append_to_memory_journal(goal_entry)
        logging.info(f"🎯 Added ADE goal: {goal}")
        
        return goal_entry
