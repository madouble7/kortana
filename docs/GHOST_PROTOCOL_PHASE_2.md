# Ghost Protocol - Phase 2: Local AI Provisioning

## Overview
Phase 2 of the Ghost Protocol establishes a local inference bridge using the **Tabby ML** framework. This enables Kor'tana to operate autonomously using locally-hosted models like **StarCoder-2-7B**, reducing cloud dependency and improving code privacy.

## Components

### 1. Tabby Service
- **Source**: `src/kortana/core/services/tabby_service.py`
- **Purpose**: Lifecycle management for the Tabby server and automated model downloads.
- **Registry**: Integrated into `ServiceRegistry` for centralized access.

### 2. ADE Local Operations
- **Source**: `src/kortana/core/ade_model_ops.py`
- **Tool**: `provision_local_model`
- **Logic**: Automates checks for the `tabby` executable, downloads the specified model, and starts the server as a background subprocess.

### 3. StarCoder-2-7B
- **ID**: `StarCoder2-7B`
- **Role**: Primary LLM for code generation tasks within the ADE during Ghost Protocol operation.

## Setup Instructions

### Prerequisites
1. Install [Tabby CLI](https://tabby.sh) and ensure it's in the system `PATH`.
2. Configure the `TABBY_EXECUTABLE` path in the Kor'tana `config.yaml` (optional if in PATH).

### Automated Activation
To activate Phase 2 via the ADE, issue the following goal:
> "Provision the local StarCoder model and prepare for Ghost Protocol operations."

### Manual Verification
Run the verification script:
```powershell
python scripts/ghost_protocol_init.py
```

### Tests
Run the dedicated test suite:
```bash
pytest tests/test_tabby_service.py
```

## Security & Covenant
- All local model operations are monitored by the `CovenantEnforcer`.
- Subprocess execution is restricted to the Tabby binary and specified models.
- Port 8080 is the default; verify firewall rules for local traffic.

---
*Status: IMPLEMENTED - READY FOR VALIDATION*
