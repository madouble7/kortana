import io
from typing import Any

import PIL.Image
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from src.kortana.services.gemini import gemini_service
from src.kortana.services.multi_model_ai import ai_service

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
    """Basic chat endpoint with multi-model fallback."""
    message = payload.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Missing 'message' field in payload")

    # Try multi-model service first (includes all providers)
    if ai_service is not None:
        try:
            response = await ai_service.analyze_text(message)
            return {"response": response}
        except Exception as e:
            print(f"Multi-model service failed: {e}")

    # Fallback to original Gemini service
    if gemini_service is not None:
        try:
            response = await gemini_service.analyze_text(message)
            return {"response": response}
        except Exception as e:
            print(f"Gemini fallback failed: {e}")

    raise HTTPException(
        status_code=503, detail="No AI services available. Check backend configuration."
    )


@router.post("/analyze/image")
async def analyze_image(
    prompt: str = Form("Analyze this image"), image: UploadFile = File(...)
) -> dict[str, Any]:
    """Analyze an image with a prompt."""
    try:
        image_data = await image.read()
        pil_image = PIL.Image.open(io.BytesIO(image_data))
        response = await gemini_service.analyze_multimodal(prompt, [pil_image])
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/video")
async def analyze_video(
    prompt: str = Form("Analyze this video"), video: UploadFile = File(...)
) -> dict[str, Any]:
    """Analyze a video with a prompt."""
    import os
    import shutil
    from pathlib import Path

    temp_path = Path(f"temp_{video.filename}")
    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # Gemini requires uploading video via the File API for best results
        import google.generativeai as genai

        uploaded_file = genai.upload_file(str(temp_path))

        # Wait for processing if needed (basic implementation)
        response = await gemini_service.analyze_multimodal(prompt, [uploaded_file])

        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            os.remove(temp_path)


@router.get("/models")
async def list_models() -> dict[str, Any]:
    """List available Gemini models."""
    try:
        import google.generativeai as genai

        models = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                models.append(
                    {
                        "name": m.name,
                        "display_name": m.display_name,
                        "description": m.description,
                    }
                )
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
