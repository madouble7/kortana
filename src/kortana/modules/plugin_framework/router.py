"""
Plugin Framework API Router for Kor'tana
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .example_plugins import StockPlugin, TaskManagementPlugin, WeatherPlugin
from .plugin_loader import PluginLoader

router = APIRouter(prefix="/api/plugins", tags=["plugins"])

# Initialize plugin loader and load example plugins
plugin_loader = PluginLoader()
plugin_loader.load_plugin(WeatherPlugin())
plugin_loader.load_plugin(StockPlugin())
plugin_loader.load_plugin(TaskManagementPlugin())


class PluginExecuteRequest(BaseModel):
    plugin_name: str
    parameters: dict = {}


@router.get("/list")
async def list_plugins():
    """List all available plugins"""
    try:
        plugins = plugin_loader.list_plugins()
        return {"plugins": plugins, "count": len(plugins)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plugin_name}")
async def get_plugin_info(plugin_name: str):
    """Get information about a specific plugin"""
    try:
        plugin = plugin_loader.get_plugin(plugin_name)
        return plugin.get_info()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_plugin(request: PluginExecuteRequest):
    """Execute a plugin with given parameters"""
    try:
        result = plugin_loader.execute_plugin(
            request.plugin_name, **request.parameters
        )
        return {"plugin": request.plugin_name, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_name}/enable")
async def enable_plugin(plugin_name: str):
    """Enable a plugin"""
    try:
        plugin = plugin_loader.get_plugin(plugin_name)
        plugin.enable()
        return {"plugin": plugin_name, "enabled": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_name}/disable")
async def disable_plugin(plugin_name: str):
    """Disable a plugin"""
    try:
        plugin = plugin_loader.get_plugin(plugin_name)
        plugin.disable()
        return {"plugin": plugin_name, "enabled": False}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
