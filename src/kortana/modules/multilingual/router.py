"""
Multilingual API Router for Kor'tana
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/multilingual", tags=["multilingual"])


@router.get("/status")
async def get_status():
    """Get multilingual module status"""
    return {"module": "multilingual", "status": "active"}
