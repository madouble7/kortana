# Kor'tana Frontend

A React-based dashboard for monitoring, managing, and interacting with the Kor'tana autonomous AI system.

## 🚀 Quick Start

### Prerequisites

- Node.js 16+ and npm/yarn
- React 18.0+

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
# Start the development server
npm start

# The app will open at http://localhost:3000
```

### Build for Production

```bash
npm run build

# Build output will be in the `build/` directory
```

## 📁 Project Structure

```
frontend/
├── public/
├── src/
│   ├── index.tsx          # Entry point
│   ├── App.tsx            # Main app component
│   ├── App.css            # Global styles
│   ├── components/
│   │   ├── GitHubDashboard.tsx      # GitHub repo monitoring
│   │   ├── MemoryBrowser.tsx        # Knowledge base browser
│   │   ├── PrayerAgentStatus.tsx    # Agent status display
│   │   ├── SystemStatus.tsx         # Overall system health
│   │   └── ...other components
│   └── services/
│       ├── apiService.ts           # API client/HTTP requests
│       └── ...other services
├── package.json
└── tsconfig.json
```

## 🎨 Components

### SystemStatus

Displays the overall health and status of the Kor'tana constellation:

- Backend connection status
- System uptime
- Active agents count
- Memory usage

### GitHubDashboard

Integrates with GitHub repositories for monitoring:

- Repository overview
- Pull requests and issues
- Commit history
- Autonomous development progress

### MemoryBrowser

Allows browsing and searching the knowledge base:

- Search functionality
- Document preview
- Knowledge entries management
- Vector search capabilities

### PrayerAgentStatus

Shows the status of autonomous agents:

- Agent names and IDs
- Current tasks
- Execution history
- Performance metrics

## 🔌 API Integration

The frontend communicates with the backend via `services/apiService.ts`:

```typescript
// Example API calls
import { apiService } from './services/apiService';

// Get system status
const status = await apiService.get('/api/health');

// List agents
const agents = await apiService.get('/api/agents/list');

// Execute agent task
const result = await apiService.post('/api/agents/execute/agent-id', { task: 'description' });
```

### API Endpoints Used

- `GET /api/health` - System health check
- `GET /api/agents/list` - List all agents
- `GET /api/agents/{id}/status` - Agent status
- `GET /api/memory/` - List memories
- `POST /api/memory/search` - Search knowledge base
- `GET /api/github/repos/{owner}/{repo}/issues` - GitHub issues
- `GET /api/autonomy/status` - Autonomy system status

## 🛠️ Development

### Running Tests

```bash
npm test
```

### Type Checking

TypeScript provides static type checking. Configuration is in `tsconfig.json`.

### Code Formatting

```bash
# If Prettier is installed
npx prettier --write src/
```

## 📦 Dependencies

- **react** - UI framework
- **react-dom** - DOM rendering
- **typescript** - Type safety
- **react-scripts** - Build tooling

## ☁️ Deployment

### Static Hosting

The frontend is a static SPA and can be deployed to:

- **Vercel**: `vercel deploy`
- **Netlify**: Connect GitHub repo
- **GitHub Pages**: Via GitHub Actions
- **Cloud Storage**: Google Cloud Storage with Cloud CDN

### Environment Configuration

Create a `.env` file (if needed):

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_BACKEND_URL=https://kor-tana-780422883904.us-west1.run.app
```

### Docker Deployment

```bash
# Build frontend
npm run build

# Serve with nginx (example)
docker run -p 80:80 -v $(pwd)/build:/usr/share/nginx/html nginx:alpine
```

## 🎯 Features

- **Real-time Dashboard**: Monitor Kor'tana constellation status
- **Agent Management**: Create, execute, and monitor agents
- **Knowledge Browser**: Search and navigate the memory system
- **GitHub Integration**: Direct repository monitoring
- **Responsive Design**: Works on desktop and mobile

## 🔐 Security

- API calls should use HTTPS in production
- Authentication headers can be added to `apiService.ts`
- CORS is handled by backend configuration
- Sensitive data should not be stored in frontend code

## 📝 Development Notes

- Components use functional components with hooks
- API calls are centralized in `apiService.ts`
- Styling uses CSS modules where possible
- TypeScript provides type safety throughout

---

**The interface to the constellation.**
