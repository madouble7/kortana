# src/kortana/adapters/autogen_adapter.py
"""
Compatibility adapter exposing AutoGen-style endpoints for Kor'tana's backend API.

This module does NOT run the Microsoft AutoGen framework or perform true
multi-agent coordination. Instead, it:
- Accepts requests and returns responses in AutoGen-inspired formats for client compatibility
- Delegates all processing to Kor'tana's single orchestrator
- Optionally formats outputs to appear as if they come from multiple agents

Use this adapter when you need AutoGen-formatted interactions with Kor'tana, while
understanding that native AutoGen multi-agent collaboration is not implemented here.
"""

import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.kortana.core.orchestrator import KorOrchestrator

logger = logging.getLogger(__name__)


class AutoGenAdapter:
    """
    Adapter for integrating Microsoft AutoGen multi-agent framework with Kor'tana.
    
    This adapter provides an AutoGen-compatible interface for Kor'tana's orchestrator.
    It accepts requests in AutoGen format and returns responses in AutoGen format,
    while using Kor'tana's backend for processing.
    
    Note: This is a compatibility layer. Full native AutoGen agent orchestration
    is planned for future releases. Currently, the adapter translates between
    AutoGen's request/response format and Kor'tana's orchestrator.
    """

    def __init__(self):
        """Initialize the AutoGen adapter."""
        logger.info("AutoGenAdapter initialized")
        self.agents_config = {
            "assistant": {
                "role": "assistant",
                "system_message": "You are a helpful AI assistant powered by Kor'tana.",
            },
            "user_proxy": {
                "role": "user_proxy",
                "system_message": "You are a user proxy agent that represents the user.",
            },
        }

    async def handle_autogen_request(
        self, request_data: dict[str, Any], db: Session
    ) -> dict[str, Any]:
        """
        Process a request in AutoGen format using Kor'tana's orchestrator.
        
        This method accepts AutoGen-formatted requests and translates them
        to work with Kor'tana's backend, then formats responses in AutoGen's
        expected format. This provides compatibility with AutoGen clients
        while leveraging Kor'tana's existing capabilities.
        
        Args:
            request_data: Request data in AutoGen format
            db: Database session
            
        Returns:
            Response formatted for AutoGen clients
        """
        logger.info(f"AutoGenAdapter received request: {request_data}")

        # Extract message from AutoGen request format
        messages = request_data.get("messages", [])
        if not messages:
            raise HTTPException(
                status_code=400, detail="Missing 'messages' in AutoGen request"
            )

        # Get the last user message
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content")
                break

        if not user_message:
            raise HTTPException(
                status_code=400, detail="No user message found in request"
            )

        try:
            # Initialize KorOrchestrator with the database session
            orchestrator = KorOrchestrator(db=db)

            # Process the query through Kor'tana's orchestrator
            kortana_response = await orchestrator.process_query(query=user_message)

            # Extract the final response
            final_response = kortana_response.get(
                "final_kortana_response",
                "I'm having trouble processing your request at the moment.",
            )

            # Format response for AutoGen multi-agent system
            autogen_response = {
                "agent_responses": [
                    {
                        "agent": "kortana_assistant",
                        "role": "assistant",
                        "content": final_response,
                        "metadata": {
                            "agent_type": "kortana_orchestrator",
                            "capabilities": ["reasoning", "memory", "ethics"],
                        },
                    }
                ],
                "conversation_id": request_data.get("conversation_id", "default"),
                "status": "success",
                "debug_info": {
                    "kortana_internals": kortana_response,
                },
            }

        except Exception as e:
            logger.error(f"Error during AutoGen request processing: {e}", exc_info=True)
            # Return graceful error response in AutoGen format
            autogen_response = {
                "agent_responses": [
                    {
                        "agent": "kortana_assistant",
                        "role": "assistant",
                        "content": "I encountered an internal processing error. Please try again.",
                        "metadata": {
                            "error": True,
                        },
                    }
                ],
                "conversation_id": request_data.get("conversation_id", "default"),
                "status": "error",
                "debug_info": {
                    "error": str(e),
                },
            }

        logger.info(f"AutoGenAdapter sending response: {autogen_response}")
        return autogen_response

    async def handle_multi_agent_collaboration(
        self, request_data: dict[str, Any], db: Session
    ) -> dict[str, Any]:
        """
        Handle multi-agent collaboration requests using AutoGen-compatible format.
        
        This method provides an AutoGen-compatible interface for complex tasks.
        Currently, it uses Kor'tana's orchestrator and formats the response to
        simulate multi-agent collaboration structure that AutoGen clients expect.
        
        Future Enhancement: This will be upgraded to use native AutoGen agents
        for true multi-agent orchestration and collaboration.
        
        Args:
            request_data: Request data containing task and agent configuration
            db: Database session
            
        Returns:
            Collaborative response formatted for AutoGen clients
        """
        logger.info(f"Multi-agent collaboration request: {request_data}")

        task = request_data.get("task")
        agent_config = request_data.get("agent_config", {})

        if not task:
            raise HTTPException(
                status_code=400, detail="Missing 'task' in multi-agent request"
            )

        try:
            # Initialize orchestrator
            orchestrator = KorOrchestrator(db=db)

            # Process the task through orchestrator
            result = await orchestrator.process_query(query=task)

            # Format response in AutoGen's multi-agent collaboration structure
            # Note: Currently uses Kor'tana's single orchestrator response
            # Future: Will coordinate actual AutoGen agents
            multi_agent_response = {
                "collaboration_result": result.get("final_kortana_response"),
                # For now, only the Kor'tana orchestrator is involved; this list
                # maintains AutoGen's expected structure without implying real
                # multi-agent execution.
                "agents_involved": ["kortana_orchestrator"],
                "task": task,
                "status": "completed",
                "agent_contributions": [
                    {
                        "agent": "kortana_orchestrator",
                        "contribution": "Processed the task using Kor'tana's orchestrator pipeline.",
                    },
                ],
                "debug_info": {
                    "orchestrator_result": result,
                    "multi_agent_simulation": (
                        "Response is formatted for AutoGen compatibility but does not "
                        "yet represent true multi-agent execution."
                    ),
                },
            }

            return multi_agent_response

        except Exception as e:
            logger.error(f"Error in multi-agent collaboration: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Multi-agent collaboration failed: {str(e)}",
            )

    def get_agent_status(self) -> dict[str, Any]:
        """
        Get status of available agents in the AutoGen system.
        
        Returns:
            Status information for all configured agents
        """
        return {
            "available_agents": list(self.agents_config.keys()),
            "agent_details": self.agents_config,
            "framework": "Microsoft AutoGen",
            "status": "operational",
        }
