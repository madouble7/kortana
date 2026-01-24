# Kor'tana VSCode Extension

A Visual Studio Code extension for controlling and monitoring the Kor'tana autonomous AI constellation from within the editor.

## 🚀 Features

- **Control Panel**: Execute Kor'tana commands directly from VSCode
- **Real-time Status**: Monitor agent and system status
- **AI Studio Integration**: Access Google AI Studio for prompt development
- **Autonomy Audit**: Track autonomous operations and decisions
- **Deploy Control**: Manage deployment from the editor
- **Runtime Controls**: Start, stop, and restart services

## 📦 Installation

### From VSCode Extension Marketplace

1. Open VSCode
2. Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
3. Search for "Kor'tana Control Panel"
4. Click Install

### Development Installation

```bash
cd vscode-extension
npm install
npm run compile
```

Then in VSCode:

1. Press F5 to open debug window
2. Extension will load in a new VSCode window

## 🛠️ Development

### Prerequisites

- Node.js 16+
- npm or yarn
- VSCode 1.85.0+

### Setup

```bash
cd vscode-extension
npm install
npm run compile
```

### Build & Package

```bash
# Compile TypeScript
npm run compile

# Package as .vsix
npm run package
```

### Publishing

```bash
# Publish to VSCode Marketplace
vsce publish patch|minor|major
```

## 📁 Project Structure

```
vscode-extension/
├── src/
│   ├── extension.ts        # Main extension entry point
│   ├── webviews/           # Webview panels and components
│   │   └── AutonomyAudit.tsx
│   └── commands/           # Command implementations
├── out/                    # Compiled JavaScript
├── package.json
├── tsconfig.json
├── webpack.config.js       # Bundler configuration
└── vscode.proposed.d.ts    # Proposed API types
```

## 🎯 Commands

The extension contributes the following commands to VSCode:

### Kor'tana: I AM (Elevation Ritual)

**Command ID**: `kortana.elevation.iam`

Initiates the elevation ritual for administrative operations.

```json
{
  "command": "kortana.elevation.iam",
  "title": "Kor'tana: I AM (Elevation Ritual)",
  "category": "Kor'tana"
}
```

### Other Commands

See `package.json` contributes section for full command list.

## 🎨 Webviews

### AutonomyAudit Webview

Displays the autonomy audit log and tracks all autonomous operations:

- Decision history
- Operation status
- Audit trail
- System logs

**Location**: VSCode sidebar or custom panel

## 🔌 Configuration

Add to `.vscode/settings.json`:

```json
{
  "kortana.backendUrl": "http://localhost:8000",
  "kortana.enableAutoStart": true,
  "kortana.refreshInterval": 5000,
  "kortana.enableNotifications": true
}
```

### Settings Schema

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `kortana.backendUrl` | string | `http://localhost:8000` | Backend API URL |
| `kortana.enableAutoStart` | boolean | `true` | Auto-start services |
| `kortana.refreshInterval` | number | `5000` | Status refresh interval (ms) |
| `kortana.enableNotifications` | boolean | `true` | Show notifications |

## 🔐 Security

- No sensitive data stored in extension settings
- API keys passed via secure environment variables
- Communication with backend via HTTPS in production
- Requires valid VSCode session

## 📚 API Communication

The extension communicates with the Kor'tana backend:

```typescript
import * as vscode from 'vscode';

// Example: Check backend health
async function checkBackendHealth() {
  const response = await fetch('http://localhost:8000/api/health');
  const data = await response.json();
  return data.status === 'alive';
}
```

## 🧪 Testing

```bash
# Run extension tests (if configured)
npm test

# Start extension in debug mode
npm run compile && press F5
```

## 📖 Resources

- [VSCode Extension API](https://code.visualstudio.com/api)
- [Extension Marketplace](https://marketplace.visualstudio.com)
- [Kor'tana Main Repository](https://github.com/KOR-TANA/kortana)

## 🐛 Troubleshooting

### Extension Won't Load

1. Check VSCode version is 1.85.0+
2. Verify all dependencies installed: `npm install`
3. Recompile: `npm run compile`
4. Reload VSCode window

### Can't Connect to Backend

1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check `kortana.backendUrl` setting
3. Verify no firewall blocking localhost:8000
4. Check browser console for CORS errors

### Commands Not Appearing

1. Recompile extension: `npm run compile`
2. Reload VSCode
3. Check `package.json` contributes section is correct
4. Verify command IDs match implementation

## 📝 Development Notes

- Extension uses TypeScript for type safety
- Webviews use React (if configured)
- Commands are registered in `package.json`
- Settings are defined in `package.json` configuration section

---

**The instrument panel of the constellation.**
