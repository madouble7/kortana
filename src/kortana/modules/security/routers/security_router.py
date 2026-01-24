"""
Security API Router for Kor'tana
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/security", tags=["security"])


@router.get("/status")
async def get_status():
    """Get security module status"""
    return {"module": "security", "status": "active"}
