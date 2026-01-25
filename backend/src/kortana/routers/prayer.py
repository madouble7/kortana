from datetime import datetime

from fastapi import APIRouter

router = APIRouter(prefix="/api/prayer", tags=["prayer"])


@router.get("/status")
async def get_prayer_status():
    """Get status of the prayer agent cycle"""
    return {
        "status": "ready",
        "message": "Prayer agents are standing by",
        "timestamp": datetime.now().isoformat(),
        "persons": ["Matt", "Foundation"],
        "next_cycle": (datetime.now()).isoformat(),  # placeholder
    }


@router.get("/request")
async def prayer_request(person: str = "both", request: str = ""):
    """Submit a prayer request"""
    return {
        "status": "received",
        "message": f"Prayer request received for {person}",
        "request": request,
        "timestamp": datetime.now().isoformat(),
    }
