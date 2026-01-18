from typing import Any

from fastapi import APIRouter, HTTPException
from services.gemini import gemini_service

router = APIRouter()

@router.post("/analyze")
async def analyze_issue(payload: dict[str, Any]) -> dict[str, Any]:
    """Pass GitHub issue/PR text to Gemini for analysis."""
    text = payload.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' field in payload")

    analysis = await gemini_service.analyze_text(text)
    return {"analysis": analysis}

@router.post("/generate")
async def generate_code(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate code based on description."""
    description = payload.get("description")
    if not description:
        raise HTTPException(status_code=400, detail="Missing 'description' field in payload")

    code = await gemini_service.generate_code(description)
    return {"code": code}

@router.post("/chat")
async def chat_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """Basic chat endpoint."""
    message = payload.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Missing 'message' field in payload")

    response = await gemini_service.analyze_text(message)
    return {"response": response}
