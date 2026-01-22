"""
AR/VR Exploration Models

Database models for storing spatial data, environments, and AR/VR sessions.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

from src.kortana.services.database_service import Base


class ARVREnvironment(Base):
    """Model for AR/VR environments and scenes"""

    __tablename__ = "ar_vr_environments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    environment_type = Column(
        String, nullable=False
    )  # 'immersive_simulation', 'real_world_overlay', 'mixed_reality'
    scene_data = Column(JSON, nullable=True)  # Scene graph, objects, spatial data
    spatial_anchors = Column(JSON, nullable=True)  # Spatial anchor points
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ARVRSession(Base):
    """Model for tracking AR/VR user sessions"""

    __tablename__ = "ar_vr_sessions"

    id = Column(Integer, primary_key=True, index=True)
    environment_id = Column(Integer, nullable=False)  # Reference to environment
    user_id = Column(String, nullable=True)  # User identifier
    session_type = Column(String, nullable=False)  # 'ar', 'vr', 'mixed'
    device_type = Column(String, nullable=True)  # Device information
    position_x = Column(Float, nullable=True)  # User position in 3D space
    position_y = Column(Float, nullable=True)
    position_z = Column(Float, nullable=True)
    orientation = Column(JSON, nullable=True)  # Quaternion or euler angles
    interaction_data = Column(JSON, nullable=True)  # User interactions
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)


class SpatialObject(Base):
    """Model for spatial objects in AR/VR environments"""

    __tablename__ = "spatial_objects"

    id = Column(Integer, primary_key=True, index=True)
    environment_id = Column(Integer, nullable=False)
    object_name = Column(String, nullable=False)
    object_type = Column(
        String, nullable=False
    )  # '3d_model', 'hologram', 'point_cloud', 'annotation'
    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    position_z = Column(Float, nullable=False)
    rotation = Column(JSON, nullable=True)  # Rotation data
    scale = Column(JSON, nullable=True)  # Scale data
    properties = Column(JSON, nullable=True)  # Custom properties
    created_at = Column(DateTime, default=datetime.utcnow)
