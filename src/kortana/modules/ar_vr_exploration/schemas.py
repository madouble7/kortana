"""
AR/VR Exploration Schemas

Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Environment Schemas
class ARVREnvironmentBase(BaseModel):
    """Base schema for AR/VR environments"""

    name: str = Field(..., description="Name of the environment")
    description: Optional[str] = Field(None, description="Description of the environment")
    environment_type: str = Field(
        ...,
        description="Type: 'immersive_simulation', 'real_world_overlay', 'mixed_reality'",
    )
    scene_data: Optional[Dict[str, Any]] = Field(None, description="Scene graph data")
    spatial_anchors: Optional[Dict[str, Any]] = Field(
        None, description="Spatial anchor points"
    )


class ARVREnvironmentCreate(ARVREnvironmentBase):
    """Schema for creating a new AR/VR environment"""

    pass


class ARVREnvironmentUpdate(BaseModel):
    """Schema for updating an AR/VR environment"""

    name: Optional[str] = None
    description: Optional[str] = None
    scene_data: Optional[Dict[str, Any]] = None
    spatial_anchors: Optional[Dict[str, Any]] = None


class ARVREnvironmentDisplay(ARVREnvironmentBase):
    """Schema for displaying AR/VR environment information"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Session Schemas
class ARVRSessionBase(BaseModel):
    """Base schema for AR/VR sessions"""

    environment_id: int = Field(..., description="ID of the environment")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_type: str = Field(..., description="Session type: 'ar', 'vr', 'mixed'")
    device_type: Optional[str] = Field(None, description="Device type information")


class ARVRSessionCreate(ARVRSessionBase):
    """Schema for creating a new AR/VR session"""

    pass


class ARVRSessionUpdate(BaseModel):
    """Schema for updating AR/VR session"""

    position_x: Optional[float] = Field(None, description="X position in 3D space")
    position_y: Optional[float] = Field(None, description="Y position in 3D space")
    position_z: Optional[float] = Field(None, description="Z position in 3D space")
    orientation: Optional[Dict[str, Any]] = Field(None, description="Orientation data")
    interaction_data: Optional[Dict[str, Any]] = Field(
        None, description="User interaction data"
    )


class ARVRSessionDisplay(ARVRSessionBase):
    """Schema for displaying AR/VR session information"""

    id: int
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    orientation: Optional[Dict[str, Any]] = None
    interaction_data: Optional[Dict[str, Any]] = None
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Spatial Object Schemas
class SpatialObjectBase(BaseModel):
    """Base schema for spatial objects"""

    environment_id: int = Field(..., description="ID of the environment")
    object_name: str = Field(..., description="Name of the object")
    object_type: str = Field(
        ...,
        description="Type: '3d_model', 'hologram', 'point_cloud', 'annotation'",
    )
    position_x: float = Field(..., description="X position")
    position_y: float = Field(..., description="Y position")
    position_z: float = Field(..., description="Z position")
    rotation: Optional[Dict[str, Any]] = Field(None, description="Rotation data")
    scale: Optional[Dict[str, Any]] = Field(None, description="Scale data")
    properties: Optional[Dict[str, Any]] = Field(
        None, description="Custom object properties"
    )


class SpatialObjectCreate(SpatialObjectBase):
    """Schema for creating a spatial object"""

    pass


class SpatialObjectUpdate(BaseModel):
    """Schema for updating a spatial object"""

    object_name: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    rotation: Optional[Dict[str, Any]] = None
    scale: Optional[Dict[str, Any]] = None
    properties: Optional[Dict[str, Any]] = None


class SpatialObjectDisplay(SpatialObjectBase):
    """Schema for displaying spatial object information"""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Additional response schemas
class ImmersiveSimulationResponse(BaseModel):
    """Response schema for immersive simulation operations"""

    environment_id: int
    simulation_status: str
    message: str
    scene_data: Optional[Dict[str, Any]] = None


class RealWorldOverlayResponse(BaseModel):
    """Response schema for real-world overlay operations"""

    session_id: int
    overlay_active: bool
    spatial_anchors: List[Dict[str, Any]]
    message: str
