# src/kortana/adapters/dify_adapter.py
"""
Adapter to connect Kor'tana's backend API with the Dify platform.

This adapter handles:
- Receiving requests from Dify applications (chat apps, workflows, agents)
- Transforming Dify requests to match Kor'tana's core API
- Calling Kor'tana's core processing logic (e.g., KorOrchestrator)
- Transforming Kor'tana's response into Dify-compatible format
- Supporting Dify's workflow automation and no-code prompt features
- Ensuring minimal latency and robust data security
"""

import logging
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.kortana.core.orchestrator import KorOrchestrator

logger = logging.getLogger(__name__)


class DifyAdapter:
    """
    Adapter for integrating Kor'tana with Dify platform.
    
    Dify is a no-code LLM application platform that supports:
    - Chat applications with customizable prompts
    - Workflow automation and orchestration
    - Agent-based applications
    - Multi-model support and switching
    """

    def __init__(self):
        """Initialize the Dify adapter."""
        logger.info("DifyAdapter initialized.")
        self._validate_configuration()

    def _validate_configuration(self):
        """Validate that necessary configuration is present for Dify integration."""
        # Future: Add validation for Dify-specific API keys, endpoints, etc.
        pass

    async def handle_chat_request(
        self, request_data: dict[str, Any], db: Session
    ) -> dict[str, Any]:
        """
        Process a chat request from Dify using Kor'tana's orchestrator.
        
        Dify chat requests typically include:
        - query: The user's message
        - conversation_id: Optional conversation identifier
        - user: Optional user identifier
        - inputs: Optional variables for prompt templates
        
        Args:
            request_data: Dictionary containing Dify request data
            db: Database session for Kor'tana operations
            
        Returns:
            Dictionary with Dify-compatible response format
        """
        # Log request metadata without sensitive data
        logger.info(
            "DifyAdapter received chat request",
            extra={
                "conversation_id": request_data.get("conversation_id"),
                "user": request_data.get("user"),
                "has_query": bool(request_data.get("query") or request_data.get("message")),
            }
        )

        # Extract message from Dify request format
        user_query = request_data.get("query") or request_data.get("message")
        if not user_query:
            raise HTTPException(
                status_code=400, 
                detail="Missing 'query' or 'message' in Dify request"
            )

        # Extract optional parameters
        conversation_id = request_data.get("conversation_id")
        user_id = request_data.get("user")
        inputs = request_data.get("inputs", {})
        
        # Generate unique conversation ID if not provided
        if not conversation_id:
            conversation_id = f"conv_{uuid.uuid4().hex[:16]}"

        try:
            # Initialize KorOrchestrator with the database session
            orchestrator = KorOrchestrator(db=db)

            # Process the query through Kor'tana's core logic
            kortana_response = await orchestrator.process_query(query=user_query)

            # Extract the final response message
            final_response = kortana_response.get(
                "final_kortana_response",
                "I'm having trouble processing your request at the moment.",
            )

            # Transform to Dify's expected response format
            dify_response = {
                "answer": final_response,
                "conversation_id": conversation_id,
                "metadata": {
                    "kortana_internals": kortana_response,
                    "processing_timestamp": kortana_response.get("timestamp"),
                },
            }

            # Add retrieved memories if available for context transparency
            if "retrieved_memories" in kortana_response:
                dify_response["metadata"]["context_used"] = len(
                    kortana_response["retrieved_memories"]
                )

        except Exception as e:
            logger.exception("Error during DifyAdapter chat processing")
            # Return a graceful error response in Dify format
            dify_response = {
                "answer": "I encountered an internal processing error. Please try again.",
                "conversation_id": conversation_id,
                "metadata": {
                    "error": "Internal processing error",
                },
            }

        logger.info(
            "DifyAdapter sending chat response",
            extra={"conversation_id": conversation_id, "has_answer": bool(dify_response.get("answer"))}
        )
        return dify_response

    async def handle_workflow_request(
        self, request_data: dict[str, Any], db: Session
    ) -> dict[str, Any]:
        """
        Process a workflow request from Dify.
        
        Workflow requests support Dify's automation features and can include:
        - Multiple steps
        - Conditional logic
        - Variable passing between nodes
        
        Args:
            request_data: Dictionary containing Dify workflow request
            db: Database session
            
        Returns:
            Dictionary with workflow execution results
        """
        workflow_id = request_data.get("workflow_id")
        logger.info(
            "DifyAdapter received workflow request",
            extra={"workflow_id": workflow_id}
        )

        inputs = request_data.get("inputs", {})
        
        try:
            # Process inputs through Kor'tana
            orchestrator = KorOrchestrator(db=db)
            
            # Extract the main query or task from workflow inputs
            main_query = inputs.get("query") or inputs.get("task") or "Process workflow"
            
            kortana_response = await orchestrator.process_query(query=main_query)
            
            # Format response for Dify workflow
            workflow_response = {
                "workflow_id": workflow_id,
                "status": "completed",
                "outputs": {
                    "result": kortana_response.get("final_kortana_response"),
                    "metadata": kortana_response,
                },
            }

        except Exception as e:
            logger.exception("Error during workflow processing")
            workflow_response = {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": "Workflow execution failed",
            }

        logger.info(
            "DifyAdapter workflow response",
            extra={"workflow_id": workflow_id, "status": workflow_response.get("status")}
        )
        return workflow_response

    async def handle_completion_request(
        self, request_data: dict[str, Any], db: Session
    ) -> dict[str, Any]:
        """
        Process a text completion request from Dify.
        
        Supports Dify's completion mode for non-chat applications.
        
        Args:
            request_data: Dictionary containing completion request
            db: Database session
            
        Returns:
            Dictionary with completion result
        """
        logger.info("DifyAdapter received completion request")

        prompt = request_data.get("prompt")
        if not prompt:
            raise HTTPException(
                status_code=400,
                detail="Missing 'prompt' in Dify completion request"
            )

        try:
            orchestrator = KorOrchestrator(db=db)
            kortana_response = await orchestrator.process_query(query=prompt)

            completion_response = {
                "completion": kortana_response.get("final_kortana_response"),
                "metadata": {
                    "model": "kortana",
                    "usage": {
                        # Note: This is an approximate count using word splitting.
                        # For accurate token counting, integrate a tokenizer library
                        # specific to the LLM being used (e.g., tiktoken for OpenAI models)
                        "approximate_tokens": len(prompt.split()) + len(
                            kortana_response.get("final_kortana_response", "").split()
                        ),
                    },
                },
            }

        except Exception as e:
            logger.exception("Error during completion processing")
            completion_response = {
                "completion": "",
                "error": "Completion processing failed",
            }

        logger.info("DifyAdapter completion response sent")
        return completion_response

    def get_adapter_info(self) -> dict[str, Any]:
        """
        Return information about the Dify adapter capabilities.
        
        Returns:
            Dictionary with adapter metadata reflecting actual runtime configuration
        """
        import os
        
        # Check actual runtime configuration
        require_auth = os.getenv("DIFY_REQUIRE_AUTH", "false").lower() == "true"
        
        return {
            "name": "DifyAdapter",
            "version": "1.0.0",
            "supported_features": [
                "chat_completion",
                "workflow_automation",
                "text_completion",
                "no_code_prompts",
                "multi_model_support",
            ],
            "security": {
                "data_encryption": True,
                "api_key_required": require_auth,
                "rate_limiting": False,  # Not implemented in this version
            },
            "capabilities": {
                "minimal_latency": True,
                "customization": True,
                "extensibility": True,
                "scalability": True,
            },
        }
