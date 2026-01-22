"""
Unit tests for AR/VR Exploration module
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.kortana.modules.ar_vr_exploration import models, schemas, services
from src.kortana.services.database import Base

# Create test database
test_engine = create_engine("sqlite:///:memory:", echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test"""
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def ar_vr_service(test_db):
    """Create an AR/VR service instance"""
    return services.ARVRExplorationService(db=test_db)


class TestARVREnvironment:
    """Tests for AR/VR environment operations"""

    def test_create_environment(self, ar_vr_service):
        """Test creating a new AR/VR environment"""
        environment_data = schemas.ARVREnvironmentCreate(
            name="Test Environment",
            description="A test immersive environment",
            environment_type="immersive_simulation",
            scene_data={"objects": [], "lighting": "dynamic"},
            spatial_anchors={"anchor_1": {"x": 0, "y": 0, "z": 0}},
        )

        environment = ar_vr_service.create_environment(environment_data)

        assert environment.id is not None
        assert environment.name == "Test Environment"
        assert environment.environment_type == "immersive_simulation"
        assert environment.scene_data is not None

    def test_get_environment(self, ar_vr_service):
        """Test retrieving an environment by ID"""
        # Create an environment first
        environment_data = schemas.ARVREnvironmentCreate(
            name="Test Environment",
            description="A test environment",
            environment_type="real_world_overlay",
        )
        created = ar_vr_service.create_environment(environment_data)

        # Retrieve it
        retrieved = ar_vr_service.get_environment(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test Environment"

    def test_list_environments(self, ar_vr_service):
        """Test listing all environments"""
        # Create multiple environments
        for i in range(3):
            env_data = schemas.ARVREnvironmentCreate(
                name=f"Environment {i}",
                description=f"Test environment {i}",
                environment_type="mixed_reality",
            )
            ar_vr_service.create_environment(env_data)

        # List them
        environments = ar_vr_service.list_environments()

        assert len(environments) == 3

    def test_update_environment(self, ar_vr_service):
        """Test updating an environment"""
        # Create an environment
        environment_data = schemas.ARVREnvironmentCreate(
            name="Original Name",
            description="Original description",
            environment_type="immersive_simulation",
        )
        created = ar_vr_service.create_environment(environment_data)

        # Update it
        update_data = schemas.ARVREnvironmentUpdate(
            name="Updated Name", description="Updated description"
        )
        updated = ar_vr_service.update_environment(created.id, update_data)

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"

    def test_delete_environment(self, ar_vr_service):
        """Test deleting an environment"""
        # Create an environment
        environment_data = schemas.ARVREnvironmentCreate(
            name="To Delete", description="This will be deleted", environment_type="vr"
        )
        created = ar_vr_service.create_environment(environment_data)

        # Delete it
        success = ar_vr_service.delete_environment(created.id)
        assert success is True

        # Verify it's gone
        retrieved = ar_vr_service.get_environment(created.id)
        assert retrieved is None


class TestARVRSession:
    """Tests for AR/VR session operations"""

    def test_create_session(self, ar_vr_service):
        """Test creating a new AR/VR session"""
        # Create an environment first
        env_data = schemas.ARVREnvironmentCreate(
            name="Session Environment", environment_type="ar"
        )
        env = ar_vr_service.create_environment(env_data)

        # Create a session
        session_data = schemas.ARVRSessionCreate(
            environment_id=env.id,
            user_id="user123",
            session_type="ar",
            device_type="mobile",
        )
        session = ar_vr_service.create_session(session_data)

        assert session.id is not None
        assert session.environment_id == env.id
        assert session.user_id == "user123"
        assert session.session_type == "ar"

    def test_update_session(self, ar_vr_service):
        """Test updating session position and data"""
        # Create environment and session
        env_data = schemas.ARVREnvironmentCreate(
            name="Session Environment", environment_type="vr"
        )
        env = ar_vr_service.create_environment(env_data)

        session_data = schemas.ARVRSessionCreate(
            environment_id=env.id, session_type="vr"
        )
        session = ar_vr_service.create_session(session_data)

        # Update session
        update_data = schemas.ARVRSessionUpdate(
            position_x=1.5,
            position_y=2.0,
            position_z=3.5,
            orientation={"x": 0, "y": 0, "z": 0, "w": 1},
        )
        updated = ar_vr_service.update_session(session.id, update_data)

        assert updated.position_x == 1.5
        assert updated.position_y == 2.0
        assert updated.position_z == 3.5

    def test_end_session(self, ar_vr_service):
        """Test ending a session"""
        # Create environment and session
        env_data = schemas.ARVREnvironmentCreate(
            name="Session Environment", environment_type="vr"
        )
        env = ar_vr_service.create_environment(env_data)

        session_data = schemas.ARVRSessionCreate(
            environment_id=env.id, session_type="vr"
        )
        session = ar_vr_service.create_session(session_data)

        # End session
        ended = ar_vr_service.end_session(session.id)

        assert ended.ended_at is not None


class TestSpatialObject:
    """Tests for spatial object operations"""

    def test_create_spatial_object(self, ar_vr_service):
        """Test creating a spatial object"""
        # Create an environment first
        env_data = schemas.ARVREnvironmentCreate(
            name="Object Environment", environment_type="mixed_reality"
        )
        env = ar_vr_service.create_environment(env_data)

        # Create a spatial object
        object_data = schemas.SpatialObjectCreate(
            environment_id=env.id,
            object_name="Test Hologram",
            object_type="hologram",
            position_x=1.0,
            position_y=2.0,
            position_z=3.0,
            rotation={"x": 0, "y": 45, "z": 0},
            scale={"x": 1, "y": 1, "z": 1},
        )
        spatial_object = ar_vr_service.create_spatial_object(object_data)

        assert spatial_object.id is not None
        assert spatial_object.object_name == "Test Hologram"
        assert spatial_object.position_x == 1.0

    def test_list_spatial_objects(self, ar_vr_service):
        """Test listing spatial objects in an environment"""
        # Create an environment
        env_data = schemas.ARVREnvironmentCreate(
            name="Object Environment", environment_type="vr"
        )
        env = ar_vr_service.create_environment(env_data)

        # Create multiple objects
        for i in range(3):
            object_data = schemas.SpatialObjectCreate(
                environment_id=env.id,
                object_name=f"Object {i}",
                object_type="3d_model",
                position_x=float(i),
                position_y=0.0,
                position_z=0.0,
            )
            ar_vr_service.create_spatial_object(object_data)

        # List objects
        objects = ar_vr_service.list_spatial_objects(env.id)

        assert len(objects) == 3


class TestVirtuScopeFeatures:
    """Tests for VirtuScope-inspired features"""

    def test_create_immersive_simulation(self, ar_vr_service):
        """Test creating an immersive simulation"""
        # Create an environment
        env_data = schemas.ARVREnvironmentCreate(
            name="Simulation Environment", environment_type="immersive_simulation"
        )
        env = ar_vr_service.create_environment(env_data)

        # Create simulation
        simulation_config = {
            "interactive_elements": ["button", "lever"],
            "physics_enabled": True,
            "gravity": -9.81,
        }
        response = ar_vr_service.create_immersive_simulation(env.id, simulation_config)

        assert response.environment_id == env.id
        assert response.simulation_status == "active"
        assert response.scene_data is not None

    def test_activate_real_world_overlay(self, ar_vr_service):
        """Test activating real-world overlay"""
        # Create environment and session
        env_data = schemas.ARVREnvironmentCreate(
            name="AR Environment", environment_type="real_world_overlay"
        )
        env = ar_vr_service.create_environment(env_data)

        session_data = schemas.ARVRSessionCreate(
            environment_id=env.id, session_type="ar"
        )
        session = ar_vr_service.create_session(session_data)

        # Activate overlay
        anchor_points = [
            {"id": "anchor1", "x": 0, "y": 0, "z": 0},
            {"id": "anchor2", "x": 1, "y": 0, "z": 1},
        ]
        response = ar_vr_service.activate_real_world_overlay(session.id, anchor_points)

        assert response.session_id == session.id
        assert response.overlay_active is True
        assert len(response.spatial_anchors) == 2

    def test_spatial_query(self, ar_vr_service):
        """Test spatial query for nearby objects"""
        # Create environment
        env_data = schemas.ARVREnvironmentCreate(
            name="Query Environment", environment_type="vr"
        )
        env = ar_vr_service.create_environment(env_data)

        # Create objects at different positions
        positions = [(0, 0, 0), (1, 1, 1), (5, 5, 5)]
        for i, (x, y, z) in enumerate(positions):
            object_data = schemas.SpatialObjectCreate(
                environment_id=env.id,
                object_name=f"Object {i}",
                object_type="3d_model",
                position_x=float(x),
                position_y=float(y),
                position_z=float(z),
            )
            ar_vr_service.create_spatial_object(object_data)

        # Query for objects near origin
        nearby = ar_vr_service.get_spatial_query(
            env.id, position={"x": 0, "y": 0, "z": 0}, radius=2.0
        )

        # Should find objects at (0,0,0) and (1,1,1), but not (5,5,5)
        assert len(nearby) == 2
