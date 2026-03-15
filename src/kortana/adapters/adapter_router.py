# src/kortana/adapters/adapter_router.py
"""
API Router for LobeChat adapter and potentially other adapters.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.kortana.services.database import get_db_sync

from .lobechat_adapter import LobeChatAdapter


# Pydantic models for LobeChat interaction (can be refined based on LobeChat's actual API)
class LobeChatRequest(BaseModel):
    message: str = Field(..., examples=["Hello Kor'tana, how are you?"])
    # Potentially other fields LobeChat sends, like conversation_id, user_id, stream option, etc.
    # For example:
    # conversation_id: str | None = None
    # stream: bool = False


class LobeChatResponse(BaseModel):
    message: str
    # Potentially other fields LobeChat expects, like error codes, session info, etc.
    # For example:
    # success: bool = True
    # error_message: str | None = None
    debug_kortana_internals: dict[str, Any] | None = None  # Optional for debugging


router = APIRouter(
    prefix="/adapters",  # General prefix for all adapters
    tags=["Adapters"],  # Tag for OpenAPI docs
)

# Instantiate the adapter.
# For a simple case, a singleton might be fine.
# For more complex scenarios involving state or DB sessions per request,
# you might instantiate it within the endpoint or use FastAPI's dependency injection.
lobe_adapter_instance = LobeChatAdapter()


@router.post("/lobechat/chat", response_model=LobeChatResponse)
async def handle_lobechat_message(
    request: LobeChatRequest, db: Session = Depends(get_db_sync)
):
    """
    Endpoint to receive messages from LobeChat and respond via Kor'tana.
    """
    try:
        # Pass the database session to the adapter method
        response_data = await lobe_adapter_instance.handle_lobe_chat_request(
            request.model_dump(), db
        )
        # Ensure the response from the adapter matches the LobeChatResponse model
        return LobeChatResponse(**response_data)
    except HTTPException as e:  # FastAPI's HTTPException
        # Re-raise HTTPException to let FastAPI handle it
        raise e
    except Exception as e:
        # Catch any other unexpected errors from the adapter
        print(f"Error in LobeChat adapter endpoint: {e}")
        # Return a structured error response matching LobeChatResponse model
        return LobeChatResponse(
            message="An unexpected error occurred while processing your request with Kor'tana.",
            debug_kortana_internals={"error": str(e)},
        )
