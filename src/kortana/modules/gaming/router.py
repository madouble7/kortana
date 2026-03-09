"""
Gaming API Router for Kor'tana
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/gaming", tags=["gaming"])


@router.get("/status")
async def get_status():
    """Get gaming module status"""
    return {"module": "gaming", "status": "active"}
