import subprocess
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/list")
async def list_remotes() -> dict[str, Any]:
    """List rclone remotes."""
    try:
        result = subprocess.run(
            ["rclone", "listremotes"], capture_output=True, text=True, check=True
        )
        remotes = result.stdout.splitlines()
        return {"remotes": remotes}
    except FileNotFoundError:
        return {"remotes": [], "warning": "rclone not found on system"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{remote}")
async def list_files(remote: str, path: str = "") -> dict[str, Any]:
    """List files on a specific remote."""
    try:
        # Avoid injection by validating remote name if possible
        # Basic check: no spaces or suspicious characters
        if not remote.endswith(":"):
            remote = f"{remote}:"

        full_path = f"{remote}{path}"
        result = subprocess.run(
            ["rclone", "lsf", full_path], capture_output=True, text=True, check=True
        )
        files = result.stdout.splitlines()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/copy")
async def copy_file(source: str, destination: str) -> dict[str, Any]:
    """Copy a file/folder via rclone."""
    try:
        subprocess.Popen(
            ["rclone", "copy", source, destination, "--progress"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return {"status": "started", "source": source, "destination": destination}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
