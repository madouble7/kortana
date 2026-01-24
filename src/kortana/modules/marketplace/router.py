"""
Marketplace API Router for Kor'tana
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


@router.get("/status")
async def get_status():
    """Get marketplace module status"""
    return {"module": "marketplace", "status": "active"}
