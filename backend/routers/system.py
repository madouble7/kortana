import platform
from pathlib import Path
from typing import Any

import psutil
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/logs")
async def get_logs(lines: int = 100) -> dict[str, Any]:
    """Get the last N lines of the autonomy log."""
    # Assuming log is in project root
    log_path = Path("AUTONOMY_EXECUTION.log")
    if not log_path.exists():
        # Try backend folder
        log_path = Path("backend/AUTONOMY_EXECUTION.log")

    if not log_path.exists():
        return {"logs": [], "message": "Log file not found"}

    try:
        with log_path.open("r", encoding="utf-8", errors="replace") as f:
            content = f.readlines()
            return {"logs": content[-lines:]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_system_info() -> dict[str, Any]:
    """Get basic system usage info."""
    return {
        "os": platform.system(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "python_version": platform.python_version(),
    }


@router.get("/settings")
async def get_settings_info() -> dict[str, Any]:
    """Get non-sensitive settings."""
    from config import get_settings

    settings = get_settings()
    return {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "version": "3.0.0-ecosystem",
    }
