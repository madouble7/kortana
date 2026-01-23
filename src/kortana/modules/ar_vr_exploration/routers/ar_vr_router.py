"""
AR/VR Exploration API Router

FastAPI router for AR/VR exploration endpoints including environment management,
session tracking, spatial object operations, and VirtuScope-inspired features.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.kortana.services.database_service import get_db_sync

from .. import schemas, services

router = APIRouter(prefix="/ar-vr", tags=["AR/VR Exploration"])


# Environment Endpoints
@router.post("/environments", response_model=schemas.ARVREnvironmentDisplay)
def create_environment(
    environment: schemas.ARVREnvironmentCreate, db: Session = Depends(get_db_sync)
):
    """Create a new AR/VR environment"""
    service = services.ARVRExplorationService(db=db)
    return service.create_environment(environment)


@router.get("/environments/{environment_id}", response_model=schemas.ARVREnvironmentDisplay)
def get_environment(environment_id: int, db: Session = Depends(get_db_sync)):
    """Get an AR/VR environment by ID"""
    service = services.ARVRExplorationService(db=db)
    environment = service.get_environment(environment_id)
    if not environment:
        raise HTTPException(status_code=404, detail="Environment not found")
    return environment


@router.get("/environments", response_model=List[schemas.ARVREnvironmentDisplay])
def list_environments(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db_sync)
):
    """List all AR/VR environments"""
    service = services.ARVRExplorationService(db=db)
    return service.list_environments(skip=skip, limit=limit)


@router.patch("/environments/{environment_id}", response_model=schemas.ARVREnvironmentDisplay)
def update_environment(
    environment_id: int,
    environment_update: schemas.ARVREnvironmentUpdate,
    db: Session = Depends(get_db_sync),
):
    """Update an AR/VR environment"""
    service = services.ARVRExplorationService(db=db)
    environment = service.update_environment(environment_id, environment_update)
    if not environment:
        raise HTTPException(status_code=404, detail="Environment not found")
    return environment


@router.delete("/environments/{environment_id}")
def delete_environment(environment_id: int, db: Session = Depends(get_db_sync)):
    """Delete an AR/VR environment"""
    service = services.ARVRExplorationService(db=db)
    success = service.delete_environment(environment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Environment not found")
    return {"message": "Environment deleted successfully"}


# Session Endpoints
@router.post("/sessions", response_model=schemas.ARVRSessionDisplay)
def create_session(
    session: schemas.ARVRSessionCreate, db: Session = Depends(get_db_sync)
):
    """Create a new AR/VR session"""
    service = services.ARVRExplorationService(db=db)
    try:
        return service.create_session(session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sessions/{session_id}", response_model=schemas.ARVRSessionDisplay)
def get_session(session_id: int, db: Session = Depends(get_db_sync)):
    """Get an AR/VR session by ID"""
    service = services.ARVRExplorationService(db=db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/sessions/{session_id}", response_model=schemas.ARVRSessionDisplay)
def update_session(
    session_id: int,
    session_update: schemas.ARVRSessionUpdate,
    db: Session = Depends(get_db_sync),
):
    """Update AR/VR session position and interaction data"""
    service = services.ARVRExplorationService(db=db)
    session = service.update_session(session_id, session_update)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/end", response_model=schemas.ARVRSessionDisplay)
def end_session(session_id: int, db: Session = Depends(get_db_sync)):
    """End an AR/VR session"""
    service = services.ARVRExplorationService(db=db)
    session = service.end_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# Spatial Object Endpoints
@router.post("/objects", response_model=schemas.SpatialObjectDisplay)
def create_spatial_object(
    spatial_object: schemas.SpatialObjectCreate, db: Session = Depends(get_db_sync)
):
    """Create a new spatial object in an environment"""
    service = services.ARVRExplorationService(db=db)
    try:
        return service.create_spatial_object(spatial_object)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/objects/{object_id}", response_model=schemas.SpatialObjectDisplay)
def get_spatial_object(object_id: int, db: Session = Depends(get_db_sync)):
    """Get a spatial object by ID"""
    service = services.ARVRExplorationService(db=db)
    spatial_object = service.get_spatial_object(object_id)
    if not spatial_object:
        raise HTTPException(status_code=404, detail="Spatial object not found")
    return spatial_object


@router.get(
    "/environments/{environment_id}/objects",
    response_model=List[schemas.SpatialObjectDisplay],
)
def list_spatial_objects(environment_id: int, db: Session = Depends(get_db_sync)):
    """List all spatial objects in an environment"""
    service = services.ARVRExplorationService(db=db)
    return service.list_spatial_objects(environment_id)


@router.patch("/objects/{object_id}", response_model=schemas.SpatialObjectDisplay)
def update_spatial_object(
    object_id: int,
    object_update: schemas.SpatialObjectUpdate,
    db: Session = Depends(get_db_sync),
):
    """Update a spatial object"""
    service = services.ARVRExplorationService(db=db)
    spatial_object = service.update_spatial_object(object_id, object_update)
    if not spatial_object:
        raise HTTPException(status_code=404, detail="Spatial object not found")
    return spatial_object


@router.delete("/objects/{object_id}")
def delete_spatial_object(object_id: int, db: Session = Depends(get_db_sync)):
    """Delete a spatial object"""
    service = services.ARVRExplorationService(db=db)
    success = service.delete_spatial_object(object_id)
    if not success:
        raise HTTPException(status_code=404, detail="Spatial object not found")
    return {"message": "Spatial object deleted successfully"}


# VirtuScope-inspired Feature Endpoints
@router.post(
    "/environments/{environment_id}/immersive-simulation",
    response_model=schemas.ImmersiveSimulationResponse,
)
def create_immersive_simulation(
    environment_id: int,
    simulation_config: Dict[str, Any],
    db: Session = Depends(get_db_sync),
):
    """
    Create an immersive simulation environment
    Supports interactive elements, physics simulation, and user-friendly interfaces
    """
    service = services.ARVRExplorationService(db=db)
    return service.create_immersive_simulation(environment_id, simulation_config)


@router.post(
    "/sessions/{session_id}/real-world-overlay",
    response_model=schemas.RealWorldOverlayResponse,
)
def activate_real_world_overlay(
    session_id: int,
    anchor_points: List[Dict[str, Any]],
    db: Session = Depends(get_db_sync),
):
    """
    Activate real-world environment overlay for AR sessions
    Uses spatial anchors to align virtual content with real-world coordinates
    """
    service = services.ARVRExplorationService(db=db)
    return service.activate_real_world_overlay(session_id, anchor_points)


@router.post(
    "/environments/{environment_id}/spatial-query",
    response_model=List[schemas.SpatialObjectDisplay],
)
def spatial_query(
    environment_id: int,
    position: Dict[str, float],
    radius: float,
    db: Session = Depends(get_db_sync),
):
    """
    Query spatial objects within a radius of a position
    Useful for proximity-based interactions and spatial awareness
    """
    service = services.ARVRExplorationService(db=db)
    return service.get_spatial_query(environment_id, position, radius)
