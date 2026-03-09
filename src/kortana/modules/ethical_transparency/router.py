"""
Ethical Transparency API Router for Kor'tana
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/ethics", tags=["ethical-transparency"])


@router.get("/status")
async def get_status():
    """Get ethical_transparency module status"""
    return {"module": "ethical_transparency", "status": "active"}
