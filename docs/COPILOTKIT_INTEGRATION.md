# CopilotKit Integration Guide for Kor'tana

This guide explains how the CopilotKit frontend is integrated with Kor'tana's backend API.

## Overview

CopilotKit provides a modern React-based interface for AI-powered chat applications. This integration enables users to interact with Kor'tana through a sleek, customizable UI with real-time communication.

## Architecture

```
┌─────────────────────┐
│  React Frontend     │
│  (CopilotKit UI)    │
│  Port: 5173         │
└──────────┬──────────┘
           │ HTTP
           ▼
┌─────────────────────┐
│  FastAPI Backend    │
│  (Kor'tana)         │
│  Port: 8000         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  KorOrchestrator    │
│  - Memory Search    │
│  - LLM Processing   │
│  - Ethical Check    │
└─────────────────────┘
```

## Components

### Frontend (`/frontend`)

Built with:
- **React 18** with TypeScript
- **Vite** for fast development and building
- **CopilotKit** for AI chat interface
  - `@copilotkit/react-core`: Core functionality
  - `@copilotkit/react-ui`: UI components
  - `@copilotkit/react-textarea`: Enhanced text input

Key files:
- `src/App.tsx`: Main application with CopilotKit integration
- `src/App.css`: Custom styling for Kor'tana theme
- `vite.config.ts`: Dev server configuration with API proxy

### Backend Adapter (`/src/kortana/adapters/copilotkit_adapter.py`)

The adapter handles:
1. **Request Transformation**: Converts CopilotKit message format to Kor'tana format
2. **Authentication**: Validates API keys (optional for development)
3. **Response Transformation**: Returns responses in CopilotKit-compatible format
4. **Error Handling**: Provides user-friendly error messages

API Endpoint: `POST /copilotkit`

## Setup Instructions

### 1. Backend Setup

The backend adapter is already integrated into Kor'tana's main application.

#### Start the Backend

```bash
# From the repository root
python -m uvicorn src.kortana.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

#### Verify Backend

```bash
curl http://localhost:8000/copilotkit/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Kor'tana CopilotKit Adapter",
  "version": "1.0.0"
}
```

### 2. Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

#### Build for Production

```bash
npm run build
```

Built files will be in `frontend/dist/`

## API Format

### Request Format

```typescript
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, Kor'tana!"
    }
  ],
  "context": {}, // Optional additional context
  "stream": false // Optional streaming flag
}
```

### Response Format

```typescript
{
  "id": "uuid-string",
  "role": "assistant",
  "content": "Response from Kor'tana...",
  "metadata": {
    "model_used": "gpt-4",
    "memory_context": [...],
    "ethical_evaluation": {...}
  }
}
```

## Configuration

### Environment Variables

Create a `.env` file in the repository root:

```env
# Kor'tana Configuration
KORTANA_API_KEY=your_api_key_here

# LLM Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database
MEMORY_DB_URL=sqlite:///./kortana_memory_dev.db
```

### CORS Configuration

The backend is configured to allow all origins for development. For production, update the CORS settings in `src/kortana/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend Configuration

To change the backend URL, edit `frontend/src/App.tsx`:

```tsx
<CopilotKit runtimeUrl="http://your-backend-url:port/copilotkit">
```

## Features

### 1. Memory-Aware Conversations

Kor'tana uses its memory system to provide context-aware responses. Previous conversations and important information are automatically retrieved and considered.

### 2. Ethical Discernment

All responses pass through Kor'tana's ethical evaluation module, ensuring thoughtful and reflective answers.

### 3. Multi-Model Support

The backend can route queries to different LLM models based on the task and user preferences.

### 4. Customizable UI

CopilotKit provides extensive customization options. Modify `frontend/src/App.tsx` to:
- Change theme colors
- Adjust sidebar behavior
- Customize message formats
- Add custom actions

Example:

```tsx
<CopilotSidebar
  defaultOpen={true}
  labels={{
    title: "Custom Title",
    initial: "Custom greeting message",
  }}
  icons={{
    // Custom icons
  }}
/>
```

## Security Considerations

### Authentication

For production deployment:

1. **Enable API Key Validation**: Update the `verify_api_key` function in `copilotkit_adapter.py` to enforce authentication
2. **Use HTTPS**: Always use secure connections in production
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Input Validation**: The adapter validates all input before processing

### Best Practices

- Never commit API keys to the repository
- Use environment variables for all sensitive configuration
- Implement proper CORS policies for production
- Regular security audits of dependencies

### Known Security Notes

**CopilotKit Dependencies (as of January 2026)**:
- CopilotKit includes dependencies (prismjs, react-syntax-highlighter) with moderate security advisories related to DOM clobbering
- These vulnerabilities are in optional syntax highlighting features
- Impact is limited as these features are not directly exposed in the basic chat interface
- Monitor CopilotKit releases for updates that address these dependencies
- Consider running `npm audit fix --force` if syntax highlighting is not needed (may introduce breaking changes)

For the latest security status: `cd frontend && npm audit`

## Troubleshooting

### Frontend Can't Connect to Backend

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check Vite proxy configuration in `vite.config.ts`
3. Look at browser console for CORS errors
4. Ensure firewall isn't blocking connections

### No Response from Kor'tana

1. Check backend logs for errors
2. Verify database is initialized
3. Ensure LLM API keys are configured
4. Test orchestrator directly: `curl -X POST http://localhost:8000/core/query -H "Content-Type: application/json" -d '{"query": "test"}'`

### CopilotKit UI Issues

1. Clear browser cache
2. Check for JavaScript errors in console
3. Verify CopilotKit packages are installed correctly: `npm list @copilotkit/react-core`
4. Try rebuilding: `npm run build`

## Development Tips

### Hot Reload

Both frontend and backend support hot reload:
- **Frontend**: Vite automatically reloads on file changes
- **Backend**: Use `--reload` flag with uvicorn

### Testing

Test the integration end-to-end:

```bash
# Terminal 1: Start backend
python -m uvicorn src.kortana.main:app --reload

# Terminal 2: Start frontend
cd frontend && npm run dev

# Open browser to http://localhost:5173
```

### Debugging

Enable debug logging in the backend:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

View network requests in browser DevTools to see API calls.

## Comparison: CopilotKit vs LobeChat

| Feature | CopilotKit | LobeChat |
|---------|-----------|----------|
| Framework | React (embedded) | Standalone Next.js app |
| Integration | Direct component | External service |
| Customization | High (React components) | Medium (configuration) |
| Deployment | Bundled with app | Separate deployment |
| UI Flexibility | Full control | Fixed layout |
| Setup Complexity | Low | Medium |

## Future Enhancements

Potential improvements to the integration:

1. **Streaming Responses**: Implement real-time streaming for longer responses
2. **Custom Actions**: Add CopilotKit actions for specific Kor'tana features
3. **Conversation History**: Persist conversation history across sessions
4. **Multi-User Support**: Add user authentication and isolation
5. **Advanced Context**: Pass additional context (file contents, system state) to the chat

## Learn More

- [CopilotKit Documentation](https://docs.copilotkit.ai/)
- [Kor'tana API Endpoints](./API_ENDPOINTS.md)
- [Kor'tana Architecture](./ARCHITECTURE.md)
