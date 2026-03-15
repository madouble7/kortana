"""
Marketplace API Router for Kor'tana
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .marketplace_service import MarketplaceService

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

marketplace_service = MarketplaceService()


class SubmitModuleRequest(BaseModel):
    name: str
    version: str
    author: str
    description: str
    category: str = "general"


class RateModuleRequest(BaseModel):
    name: str
    rating: float


@router.get("/modules")
async def browse_modules(category: str = None):
    """Browse available modules in the marketplace"""
    try:
        result = marketplace_service.browse_modules(category)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modules/search")
async def search_modules(query: str):
    """Search for modules"""
    try:
        result = marketplace_service.search_modules(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modules/{module_name}")
async def get_module_details(module_name: str):
    """Get detailed information about a module"""
    try:
        details = marketplace_service.get_module_details(module_name)
        if "error" in details:
            raise HTTPException(status_code=404, detail=details["error"])
        return details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modules/submit")
async def submit_module(request: SubmitModuleRequest):
    """Submit a new module to the marketplace"""
    try:
        module = marketplace_service.registry.register_module(
            request.name,
            request.version,
            request.author,
            request.description,
            request.category,
        )
        return {"status": "submitted", "module": module.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modules/{module_name}/install")
async def install_module(module_name: str):
    """Install a module"""
    try:
        result = marketplace_service.install_module(module_name)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modules/{module_name}/uninstall")
async def uninstall_module(module_name: str):
    """Uninstall a module"""
    try:
        result = marketplace_service.uninstall_module(module_name)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modules/rate")
async def rate_module(request: RateModuleRequest):
    """Rate a module"""
    try:
        result = marketplace_service.rate_module(request.name, request.rating)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
