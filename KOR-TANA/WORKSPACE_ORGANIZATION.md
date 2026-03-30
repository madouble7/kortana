# Kortana Workspace Organization

## Overview
This document describes the reorganization of the Kortana project workspace as of January 2026.

## Directory Structure

```
c:\
├── KOR-TANA/                          # PRIMARY - Main multimodal AI system
│   ├── utilities/                     # Utility modules and services
│   │   ├── background-agent/         # Minimal background agent with SQLite memory store
│   │   ├── hub-dispatcher/           # Skill dispatcher architecture (Hub, Persona, Skills registry)
│   │   ├── heartbeat-service/        # Token refresh microservice
│   │   └── music-tools/              # Music/remix AI tools using OneMotion
│   └── [main system files - voice, camera, FastAPI backend, React frontend]
│
├── Archives/                          # Archived and unrelated projects
│   ├── kortana-backup-snapshots/     # 30+ dated development snapshots (May-Nov 2025)
│   ├── chat-bandit-fork/             # Forked Chat Bandit Electron AI chat app
│   └── ARCHIVE_README.md             # Details on archived content
│
└── (root-level kortana directories removed) - All consolidated
```

## Migration History ✅ COMPLETED

| Original Location | New Location | Status |
|-------------------|--------------|--------|
| c:\kortana | KOR-TANA/utilities/background-agent | ✓ Moved |
| c:\kortana_hub | KOR-TANA/utilities/hub-dispatcher | ✓ Moved |
| c:\kortana-heartbeat-service | KOR-TANA/utilities/heartbeat-service | ✓ Moved |
| c:\kordtana_starter_pack | KOR-TANA/utilities/music-tools | ✓ Moved |
| c:\project-kortana | Archives/kortana-backup-snapshots | ✓ Moved |
| c:\kortana-app | Archives/chat-bandit-fork | ✓ Moved |
| c:\kortana-frontend-fresh | DELETED (empty/abandoned) | ✓ Removed |

## Current Status

- **KOR-TANA**: Primary active development directory (~5.5GB+)
- **Archives**: Contains historical and unrelated projects
- **All root-level kortana directories**: Cleaned up and consolidated
- **Utilities**: All utility modules consolidated under `utilities/`

## Notes

- Naming convention: **KOR-TANA** (caps) for main system, **kortana** (lowercase) for utilities
- All utility modules can be imported/referenced from KOR-TANA
- The Archives folder contains projects that may be useful for reference but are not actively developed
