"""
Content Generation API Router for Kor'tana
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/content", tags=["content-generation"])


@router.get("/status")
async def get_status():
    """Get content_generation module status"""
    return {"module": "content_generation", "status": "active"}
