# AR/VR Exploration Module

## Overview

The AR/VR Exploration module integrates advanced augmented and virtual reality capabilities into Kor'tana, inspired by the `sci-ctrl/VirtuScope` repository. This module provides a comprehensive framework for creating immersive experiences, real-world overlays, and spatial object management.

## Features

### 1. Immersive Simulations
- Create fully immersive VR environments
- Support for physics simulation and interactive elements
- Dynamic scene management with customizable properties
- Real-time environment updates

### 2. Real-World Environment Overlay
- AR overlay capabilities for real-world augmentation
- Spatial anchor point management
- Accurate alignment of virtual content with physical space
- Multi-device AR session support

### 3. Spatial Object Management
- 3D object positioning and manipulation
- Support for various object types (3D models, holograms, point clouds, annotations)
- Spatial queries for proximity-based interactions
- Object transformation (position, rotation, scale)

### 4. User-Friendly Interfaces
- RESTful API endpoints for all AR/VR operations
- Comprehensive request/response validation
- Session management for tracking user interactions
- Easy integration with existing Kor'tana frameworks

## Architecture

The module follows Kor'tana's modular architecture pattern:

```
src/kortana/modules/ar_vr_exploration/
├── __init__.py              # Module exports
├── models.py                # Database models (SQLAlchemy)
├── schemas.py               # API schemas (Pydantic)
├── services.py              # Business logic
└── routers/
    ├── __init__.py
    └── ar_vr_router.py      # API endpoints (FastAPI)
```

## Database Models

### ARVREnvironment
Represents an AR/VR environment or scene.

**Fields:**
- `id`: Primary key
- `name`: Environment name
- `description`: Optional description
- `environment_type`: Type of environment (`immersive_simulation`, `real_world_overlay`, `mixed_reality`)
- `scene_data`: JSON data containing scene graph and objects
- `spatial_anchors`: JSON data for spatial anchor points
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### ARVRSession
Tracks user sessions in AR/VR environments.

**Fields:**
- `id`: Primary key
- `environment_id`: Reference to environment
- `user_id`: User identifier
- `session_type`: Session type (`ar`, `vr`, `mixed`)
- `device_type`: Device information
- `position_x`, `position_y`, `position_z`: User position in 3D space
- `orientation`: JSON data for user orientation (quaternion or euler angles)
- `interaction_data`: JSON data for user interactions
- `started_at`: Session start timestamp
- `ended_at`: Session end timestamp (null if active)

### SpatialObject
Represents objects placed in AR/VR environments.

**Fields:**
- `id`: Primary key
- `environment_id`: Reference to environment
- `object_name`: Object name
- `object_type`: Type of object (`3d_model`, `hologram`, `point_cloud`, `annotation`)
- `position_x`, `position_y`, `position_z`: Object position in 3D space
- `rotation`: JSON data for rotation
- `scale`: JSON data for scale
- `properties`: JSON data for custom properties
- `created_at`: Creation timestamp

## API Endpoints

### Environment Management

#### Create Environment
```http
POST /ar-vr/environments
Content-Type: application/json

{
  "name": "My VR Environment",
  "description": "An immersive training simulation",
  "environment_type": "immersive_simulation",
  "scene_data": {
    "objects": [],
    "lighting": "dynamic",
    "physics": {"gravity": -9.81}
  }
}
```

#### Get Environment
```http
GET /ar-vr/environments/{environment_id}
```

#### List Environments
```http
GET /ar-vr/environments?skip=0&limit=100
```

#### Update Environment
```http
PATCH /ar-vr/environments/{environment_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "scene_data": {...}
}
```

#### Delete Environment
```http
DELETE /ar-vr/environments/{environment_id}
```

### Session Management

#### Create Session
```http
POST /ar-vr/sessions
Content-Type: application/json

{
  "environment_id": 1,
  "user_id": "user123",
  "session_type": "vr",
  "device_type": "Quest 3"
}
```

#### Get Session
```http
GET /ar-vr/sessions/{session_id}
```

#### Update Session
```http
PATCH /ar-vr/sessions/{session_id}
Content-Type: application/json

{
  "position_x": 1.5,
  "position_y": 2.0,
  "position_z": 3.5,
  "orientation": {"x": 0, "y": 0, "z": 0, "w": 1}
}
```

#### End Session
```http
POST /ar-vr/sessions/{session_id}/end
```

### Spatial Object Management

#### Create Spatial Object
```http
POST /ar-vr/objects
Content-Type: application/json

{
  "environment_id": 1,
  "object_name": "Training Target",
  "object_type": "hologram",
  "position_x": 0.0,
  "position_y": 1.5,
  "position_z": 2.0,
  "rotation": {"x": 0, "y": 45, "z": 0},
  "scale": {"x": 1, "y": 1, "z": 1}
}
```

#### Get Spatial Object
```http
GET /ar-vr/objects/{object_id}
```

#### List Spatial Objects
```http
GET /ar-vr/environments/{environment_id}/objects
```

#### Update Spatial Object
```http
PATCH /ar-vr/objects/{object_id}
Content-Type: application/json

{
  "position_x": 1.0,
  "position_y": 2.0,
  "position_z": 3.0
}
```

#### Delete Spatial Object
```http
DELETE /ar-vr/objects/{object_id}
```

### VirtuScope-Inspired Features

#### Create Immersive Simulation
```http
POST /ar-vr/environments/{environment_id}/immersive-simulation
Content-Type: application/json

{
  "interactive_elements": ["button", "lever", "door"],
  "physics_enabled": true,
  "gravity": -9.81,
  "time_scale": 1.0
}
```

**Response:**
```json
{
  "environment_id": 1,
  "simulation_status": "active",
  "message": "Immersive simulation environment created successfully",
  "scene_data": {...}
}
```

#### Activate Real-World Overlay
```http
POST /ar-vr/sessions/{session_id}/real-world-overlay
Content-Type: application/json

[
  {"id": "anchor1", "x": 0, "y": 0, "z": 0},
  {"id": "anchor2", "x": 1, "y": 0, "z": 1}
]
```

**Response:**
```json
{
  "session_id": 1,
  "overlay_active": true,
  "spatial_anchors": [...],
  "message": "Real-world overlay activated successfully"
}
```

#### Spatial Query
```http
POST /ar-vr/environments/{environment_id}/spatial-query
Content-Type: application/json

{
  "position": {"x": 0, "y": 0, "z": 0},
  "radius": 5.0
}
```

**Response:** Array of spatial objects within the specified radius.

## Usage Examples

### Python Client Example

```python
import requests

base_url = "http://localhost:8000/ar-vr"

# Create an environment
environment = requests.post(
    f"{base_url}/environments",
    json={
        "name": "Training Simulation",
        "environment_type": "immersive_simulation",
        "description": "VR training environment"
    }
).json()

env_id = environment["id"]

# Create a VR session
session = requests.post(
    f"{base_url}/sessions",
    json={
        "environment_id": env_id,
        "user_id": "trainer_001",
        "session_type": "vr",
        "device_type": "Meta Quest 3"
    }
).json()

# Add spatial objects
hologram = requests.post(
    f"{base_url}/objects",
    json={
        "environment_id": env_id,
        "object_name": "Training Target",
        "object_type": "hologram",
        "position_x": 0.0,
        "position_y": 1.5,
        "position_z": 2.0
    }
).json()

# Update user position during session
requests.patch(
    f"{base_url}/sessions/{session['id']}",
    json={
        "position_x": 1.0,
        "position_y": 1.8,
        "position_z": 2.5,
        "orientation": {"x": 0, "y": 0.707, "z": 0, "w": 0.707}
    }
)

# Query nearby objects
nearby = requests.post(
    f"{base_url}/environments/{env_id}/spatial-query",
    json={
        "position": {"x": 1.0, "y": 1.8, "z": 2.5},
        "radius": 3.0
    }
).json()

print(f"Found {len(nearby)} objects nearby")

# End session
requests.post(f"{base_url}/sessions/{session['id']}/end")
```

### JavaScript/TypeScript Example

```typescript
const baseUrl = 'http://localhost:8000/ar-vr';

// Create an AR environment
const environment = await fetch(`${baseUrl}/environments`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'AR Office Tour',
    environment_type: 'real_world_overlay',
    description: 'Interactive office space tour'
  })
}).then(r => r.json());

// Start AR session
const session = await fetch(`${baseUrl}/sessions`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    environment_id: environment.id,
    session_type: 'ar',
    device_type: 'iPhone 15 Pro'
  })
}).then(r => r.json());

// Activate real-world overlay with spatial anchors
await fetch(`${baseUrl}/sessions/${session.id}/real-world-overlay`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify([
    { id: 'anchor1', x: 0, y: 0, z: 0 },
    { id: 'anchor2', x: 5, y: 0, z: 0 },
    { id: 'anchor3', x: 0, y: 0, z: 5 }
  ])
});
```

## Testing

The module includes comprehensive unit tests covering:
- Environment CRUD operations
- Session management
- Spatial object operations
- VirtuScope-inspired features (immersive simulations, real-world overlays)
- Spatial queries

Run tests with:
```bash
pytest tests/unit/modules/ar_vr_exploration/
```

## Integration with Kor'tana

The AR/VR module integrates seamlessly with Kor'tana's existing frameworks:

1. **Database Integration**: Uses Kor'tana's SQLAlchemy Base and database service
2. **API Integration**: Registered in `main.py` alongside other routers
3. **Dependency Injection**: Uses FastAPI's dependency injection for database sessions
4. **Schema Validation**: Leverages Pydantic for request/response validation
5. **Modular Design**: Follows the same pattern as `memory_core` module

## Future Enhancements

Potential future enhancements include:
- WebXR integration for browser-based AR/VR
- Multi-user collaborative environments
- Advanced physics simulation
- Voice commands in VR
- Hand tracking and gesture recognition
- Eye tracking support
- Haptic feedback integration
- Recording and playback of sessions
- AI-powered environment generation
- Integration with Kor'tana's memory system for persistent spatial knowledge

## Dependencies

The module requires:
- FastAPI
- SQLAlchemy
- Pydantic
- Python 3.11+

## License

This module is part of Kor'tana and follows the same MIT License.

## Credits

Inspired by the `sci-ctrl/VirtuScope` repository's innovative approach to AR/VR exploration and immersive experiences.
