"""
Unified AI Orchestrator Router - The Bridge between local Kor'tana and AI Studio Assets.
"""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from src.kortana.logger import log_error
from src.kortana.model_lane_policy import describe_model_lane, get_active_model_lane
from src.kortana.services.gemini import gemini_service

router = APIRouter()

# Path to AI Studio exported logic
LOGIC_PATH = Path("backend/src/kortana/agents/logic")
PROMPTS_PATH = Path("backend/src/kortana/agents/prompts")


@router.get("/status")
async def get_orchestrator_status() -> dict[str, Any]:
    """Check status of unified AI logic and prompt availability."""
    logic_files = list(LOGIC_PATH.glob("*.py")) if LOGIC_PATH.exists() else []
    prompt_files = list(PROMPTS_PATH.glob("*.md")) if PROMPTS_PATH.exists() else []

    return {
        "status": "active",
        "logic_available": len(logic_files) > 0,
        "prompts_available": len(prompt_files) > 0,
        "active_model": gemini_service.model_name if gemini_service else "None",
        "active_model_lane": (
            describe_model_lane(gemini_service.model_name)
            if gemini_service
            else "unknown"
        ),
        "model_usage_lane": get_active_model_lane().value,
        "sync_mode": "unified_orchestrator",
    }


@router.post("/execute")
async def execute_unified_logic(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute AI logic that might be sourced from local or exported Studio files."""
    task = payload.get("task")
    prompt_name = payload.get("prompt_name")

    if not task:
        raise HTTPException(status_code=400, detail="Missing 'task' in payload")

    # 1. Look for custom prompt in agents/prompts
    system_instruction = ""
    if prompt_name:
        prompt_file = PROMPTS_PATH / f"{prompt_name}.md"
        if prompt_file.exists():
            system_instruction = prompt_file.read_text(encoding="utf-8")

    # 2. Execute via Gemini Service
    try:
        response = await gemini_service.analyze_text(
            task, system_instruction=system_instruction
        )
        return {
            "response": response,
            "source": "local_gemini_service",
            "prompt_applied": prompt_name if system_instruction else "none",
        }
    except Exception as e:
        log_error("orchestrator", f"Execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Execution Error: {str(e)}")


@router.post("/handshake")
async def elevation_handshake(payload: dict[str, Any]) -> dict[str, str]:
    """Special endpoint for 'WE ARE' elevation protocol."""
    message = payload.get("message", "")
    if "WE ARE" in message or "we are" in message.lower():
        return {
            "status": "ELEVATED",
            "message": "Activation Protocol Initiated. Constellation Awareness Active.",
            "protocol": "HOP_V3",
        }
    return {"status": "standard", "message": "Standard presence maintained."}
