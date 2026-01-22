# CopilotKit Integration - Quick Start

This guide will help you quickly get started with Kor'tana's CopilotKit integration.

## What is CopilotKit?

CopilotKit is a framework for building AI-powered applications with React. It provides:
- Pre-built UI components for AI chat interfaces
- Easy integration with custom backends
- Customizable appearance and behavior
- Modern, responsive design

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed
- **Node.js 18+** and npm installed
- **API Keys** for:
  - OpenAI (required)
  - Anthropic (optional)

## Quick Start (3 Steps)

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd kortana

# Create and configure .env file
cp .env.example .env
# Edit .env and add your API keys
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -e .

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Step 3: Start the Application

**Option A: Using the launch script (Recommended)**

Linux/Mac:
```bash
./start_copilotkit.sh
```

Windows:
```bash
start_copilotkit.bat
```

**Option B: Manual start**

Terminal 1 - Backend:
```bash
python -m uvicorn src.kortana.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

### Step 4: Access the Application

Open your browser to:
- **Frontend**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs

## Features

Once running, you can:

1. **Chat with Kor'tana** through the sidebar interface
2. **View responses** with memory context and ethical evaluation
3. **Customize the UI** by editing `frontend/src/App.tsx`
4. **Access API directly** at `http://localhost:8000/copilotkit`

## Architecture Overview

```
┌─────────────────────────┐
│   React Frontend        │
│   (localhost:5173)      │
│                         │
│  ┌──────────────────┐  │
│  │  CopilotKit UI   │  │
│  │  Sidebar Chat    │  │
│  └──────────────────┘  │
└───────────┬─────────────┘
            │ HTTP POST
            │ /copilotkit
            ▼
┌─────────────────────────┐
│   FastAPI Backend       │
│   (localhost:8000)      │
│                         │
│  ┌──────────────────┐  │
│  │ CopilotKit       │  │
│  │ Adapter          │  │
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │ KorOrchestrator  │  │
│  │ - Memory Search  │  │
│  │ - LLM Processing │  │
│  │ - Ethical Check  │  │
│  └──────────────────┘  │
└─────────────────────────┘
```

## Configuration

### Backend Configuration

Edit `.env`:

```env
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Custom API key for frontend authentication
KORTANA_API_KEY=your-secure-key

# Database
MEMORY_DB_URL=sqlite:///./kortana_memory_dev.db

# Logging
LOG_LEVEL=INFO
```

### Frontend Configuration

To change the backend URL, edit `frontend/src/App.tsx`:

```tsx
<CopilotKit runtimeUrl="http://your-backend-url:port/copilotkit">
```

## Customization

### UI Customization

Edit `frontend/src/App.tsx` to customize:

```tsx
<CopilotSidebar
  defaultOpen={true}
  labels={{
    title: "Your Custom Title",
    initial: "Your custom greeting",
  }}
  // Add more customization options
/>
```

### Styling

Edit `frontend/src/App.css` to change colors, fonts, and layout.

## Troubleshooting

### Backend won't start

1. Check Python dependencies: `pip install -e .`
2. Verify API keys in `.env`
3. Check port 8000 is not in use

### Frontend won't start

1. Install dependencies: `cd frontend && npm install`
2. Check Node.js version: `node --version` (should be 18+)
3. Check port 5173 is not in use

### Can't connect frontend to backend

1. Verify backend is running at http://localhost:8000/health
2. Check CORS settings in `src/kortana/main.py`
3. Look for errors in browser console (F12)

## Next Steps

- **Explore the API**: http://localhost:8000/docs
- **Read full documentation**: [docs/COPILOTKIT_INTEGRATION.md](docs/COPILOTKIT_INTEGRATION.md)
- **Customize the UI**: Modify `frontend/src/App.tsx`
- **Add custom actions**: Extend the CopilotKit adapter

## Comparison with LobeChat

| Feature | CopilotKit | LobeChat |
|---------|-----------|----------|
| Integration | Embedded component | External service |
| Setup | Single repository | Separate repos |
| Customization | Full React control | Configuration-based |
| Deployment | Built-in | Independent |

Choose CopilotKit if you want tight integration and full UI control. Choose LobeChat if you prefer a standalone chat application.

## Support

For issues or questions:
1. Check [docs/COPILOTKIT_INTEGRATION.md](docs/COPILOTKIT_INTEGRATION.md)
2. Review the API docs at http://localhost:8000/docs
3. Open an issue in the repository

---

**Happy chatting with Kor'tana! 🚀**
