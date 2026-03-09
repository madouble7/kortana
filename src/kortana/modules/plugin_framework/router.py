"""
Plugin Framework API Router for Kor'tana
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


@router.get("/status")
async def get_status():
    """Get plugin_framework module status"""
    return {"module": "plugin_framework", "status": "active"}
