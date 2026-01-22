"""
AR/VR Exploration Service

Business logic for AR/VR exploration capabilities including immersive simulations,
real-world overlays, and spatial object management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from . import models, schemas


class ARVRExplorationService:
    """Service class for AR/VR exploration operations"""

    def __init__(self, db: Session):
        self.db = db

    # Environment Management
    def create_environment(
        self, environment: schemas.ARVREnvironmentCreate
    ) -> models.ARVREnvironment:
        """Create a new AR/VR environment"""
        db_environment = models.ARVREnvironment(
            name=environment.name,
            description=environment.description,
            environment_type=environment.environment_type,
            scene_data=environment.scene_data,
            spatial_anchors=environment.spatial_anchors,
        )
        self.db.add(db_environment)
        self.db.commit()
        self.db.refresh(db_environment)
        return db_environment

    def get_environment(self, environment_id: int) -> Optional[models.ARVREnvironment]:
        """Get an environment by ID"""
        return (
            self.db.query(models.ARVREnvironment)
            .filter(models.ARVREnvironment.id == environment_id)
            .first()
        )

    def list_environments(
        self, skip: int = 0, limit: int = 100
    ) -> List[models.ARVREnvironment]:
        """List all AR/VR environments"""
        return self.db.query(models.ARVREnvironment).offset(skip).limit(limit).all()

    def update_environment(
        self, environment_id: int, environment_update: schemas.ARVREnvironmentUpdate
    ) -> Optional[models.ARVREnvironment]:
        """Update an existing environment"""
        db_environment = self.get_environment(environment_id)
        if not db_environment:
            return None

        update_data = environment_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_environment, key, value)

        db_environment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_environment)
        return db_environment

    def delete_environment(self, environment_id: int) -> bool:
        """Delete an environment"""
        db_environment = self.get_environment(environment_id)
        if not db_environment:
            return False

        self.db.delete(db_environment)
        self.db.commit()
        return True

    # Session Management
    def create_session(
        self, session: schemas.ARVRSessionCreate
    ) -> models.ARVRSession:
        """Create a new AR/VR session"""
        # Validate that environment exists
        environment = self.get_environment(session.environment_id)
        if not environment:
            raise ValueError(f"Environment with id {session.environment_id} not found")

        db_session = models.ARVRSession(
            environment_id=session.environment_id,
            user_id=session.user_id,
            session_type=session.session_type,
            device_type=session.device_type,
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def get_session(self, session_id: int) -> Optional[models.ARVRSession]:
        """Get a session by ID"""
        return (
            self.db.query(models.ARVRSession)
            .filter(models.ARVRSession.id == session_id)
            .first()
        )

    def update_session(
        self, session_id: int, session_update: schemas.ARVRSessionUpdate
    ) -> Optional[models.ARVRSession]:
        """Update session position and interaction data"""
        db_session = self.get_session(session_id)
        if not db_session:
            return None

        update_data = session_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_session, key, value)

        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def end_session(self, session_id: int) -> Optional[models.ARVRSession]:
        """End an AR/VR session"""
        db_session = self.get_session(session_id)
        if not db_session:
            return None

        db_session.ended_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    # Spatial Object Management
    def create_spatial_object(
        self, spatial_object: schemas.SpatialObjectCreate
    ) -> models.SpatialObject:
        """Create a new spatial object in an environment"""
        # Validate that environment exists
        environment = self.get_environment(spatial_object.environment_id)
        if not environment:
            raise ValueError(
                f"Environment with id {spatial_object.environment_id} not found"
            )

        db_object = models.SpatialObject(
            environment_id=spatial_object.environment_id,
            object_name=spatial_object.object_name,
            object_type=spatial_object.object_type,
            position_x=spatial_object.position_x,
            position_y=spatial_object.position_y,
            position_z=spatial_object.position_z,
            rotation=spatial_object.rotation,
            scale=spatial_object.scale,
            properties=spatial_object.properties,
        )
        self.db.add(db_object)
        self.db.commit()
        self.db.refresh(db_object)
        return db_object

    def get_spatial_object(self, object_id: int) -> Optional[models.SpatialObject]:
        """Get a spatial object by ID"""
        return (
            self.db.query(models.SpatialObject)
            .filter(models.SpatialObject.id == object_id)
            .first()
        )

    def list_spatial_objects(
        self, environment_id: int
    ) -> List[models.SpatialObject]:
        """List all spatial objects in an environment"""
        return (
            self.db.query(models.SpatialObject)
            .filter(models.SpatialObject.environment_id == environment_id)
            .all()
        )

    def update_spatial_object(
        self, object_id: int, object_update: schemas.SpatialObjectUpdate
    ) -> Optional[models.SpatialObject]:
        """Update a spatial object"""
        db_object = self.get_spatial_object(object_id)
        if not db_object:
            return None

        update_data = object_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_object, key, value)

        self.db.commit()
        self.db.refresh(db_object)
        return db_object

    def delete_spatial_object(self, object_id: int) -> bool:
        """Delete a spatial object"""
        db_object = self.get_spatial_object(object_id)
        if not db_object:
            return False

        self.db.delete(db_object)
        self.db.commit()
        return True

    # VirtuScope-inspired features
    def create_immersive_simulation(
        self, environment_id: int, simulation_config: Dict[str, Any]
    ) -> schemas.ImmersiveSimulationResponse:
        """
        Create an immersive simulation environment
        Inspired by VirtuScope's simulation capabilities
        """
        environment = self.get_environment(environment_id)
        if not environment:
            return schemas.ImmersiveSimulationResponse(
                environment_id=environment_id,
                simulation_status="error",
                message="Environment not found",
            )

        # Update environment with simulation configuration
        scene_data = environment.scene_data or {}
        scene_data.update(
            {
                "simulation_type": "immersive",
                "config": simulation_config,
                "interactive_elements": simulation_config.get(
                    "interactive_elements", []
                ),
                "physics_enabled": simulation_config.get("physics_enabled", True),
            }
        )

        environment.scene_data = scene_data
        environment.updated_at = datetime.utcnow()
        self.db.commit()

        return schemas.ImmersiveSimulationResponse(
            environment_id=environment_id,
            simulation_status="active",
            message="Immersive simulation environment created successfully",
            scene_data=scene_data,
        )

    def activate_real_world_overlay(
        self, session_id: int, anchor_points: List[Dict[str, Any]]
    ) -> schemas.RealWorldOverlayResponse:
        """
        Activate real-world overlay for an AR session
        Inspired by VirtuScope's AR overlay capabilities
        """
        session = self.get_session(session_id)
        if not session:
            return schemas.RealWorldOverlayResponse(
                session_id=session_id,
                overlay_active=False,
                spatial_anchors=[],
                message="Session not found",
            )

        environment = self.get_environment(session.environment_id)
        if not environment:
            return schemas.RealWorldOverlayResponse(
                session_id=session_id,
                overlay_active=False,
                spatial_anchors=[],
                message="Environment not found",
            )

        # Update environment with spatial anchors
        spatial_anchors = environment.spatial_anchors or {}
        spatial_anchors.update(
            {"active": True, "anchor_points": anchor_points, "session_id": session_id}
        )

        environment.spatial_anchors = spatial_anchors
        environment.updated_at = datetime.utcnow()
        self.db.commit()

        return schemas.RealWorldOverlayResponse(
            session_id=session_id,
            overlay_active=True,
            spatial_anchors=anchor_points,
            message="Real-world overlay activated successfully",
        )

    def get_spatial_query(
        self, environment_id: int, position: Dict[str, float], radius: float
    ) -> List[models.SpatialObject]:
        """
        Query spatial objects within a radius of a position
        Useful for proximity-based interactions

        Note: Current implementation uses Python-side filtering for simplicity.
        For production with large object counts, consider implementing:
        1. Database-level spatial indexes (PostGIS for PostgreSQL)
        2. Bounding box pre-filtering in SQL
        3. R-tree or quad-tree spatial indexing
        """
        objects = self.list_spatial_objects(environment_id)

        # Simple distance calculation (can be enhanced with more sophisticated spatial queries)
        nearby_objects = []
        for obj in objects:
            dx = obj.position_x - position.get("x", 0)
            dy = obj.position_y - position.get("y", 0)
            dz = obj.position_z - position.get("z", 0)
            distance = (dx**2 + dy**2 + dz**2) ** 0.5

            if distance <= radius:
                nearby_objects.append(obj)

        return nearby_objects
