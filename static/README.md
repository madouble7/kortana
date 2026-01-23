# Kor'tana Static Assets

This directory contains static files served by the FastAPI application.

## Files

### chat.html
The main web-based chat interface for Kor'tana.

**Features:**
- Modern gradient design
- Conversation history sidebar
- Memory visualization
- Streaming mode toggle
- Health status indicator
- Responsive layout

**Access:**
Open `http://localhost:8000/` in your browser after starting the server.

## Development

To modify the chat interface:

1. Edit `chat.html` in this directory
2. Reload the page in your browser (FastAPI serves static files directly)
3. Changes are visible immediately (no build step required)

## Deployment

The static files are automatically served by FastAPI when the server starts:
- Mounted at `/static` route
- Root `/` serves `chat.html`
- CORS enabled for cross-origin requests

## Assets Structure

```
static/
├── README.md       # This file
└── chat.html      # Main chat interface
```

Future additions may include:
- `css/` - Separate stylesheets
- `js/` - JavaScript modules
- `images/` - Icons and logos
- `fonts/` - Custom fonts
