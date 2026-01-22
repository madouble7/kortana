# Kor'tana CopilotKit Frontend

This is the React-based frontend for Kor'tana, integrated with CopilotKit to provide an AI-powered chat interface.

## Features

- 🤖 **CopilotKit Integration**: Seamless AI chat interface with sidebar
- 💬 **Real-time Communication**: Direct connection to Kor'tana backend
- 🎨 **Modern UI**: Built with React, TypeScript, and Vite
- 🔄 **Hot Module Replacement**: Fast development with instant feedback

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Kor'tana backend running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Configuration

The frontend is configured to connect to the Kor'tana backend at `http://localhost:8000/copilotkit`.

To change the backend URL, update the `runtimeUrl` prop in `src/App.tsx`:

```tsx
<CopilotKit runtimeUrl="http://your-backend-url/copilotkit">
```

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx          # Main application component with CopilotKit
│   ├── App.css          # Application styles
│   ├── main.tsx         # Application entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── package.json         # Dependencies and scripts
└── vite.config.ts       # Vite configuration
```

## CopilotKit Features

This frontend uses CopilotKit's components:

- **CopilotKit**: Main provider component
- **CopilotSidebar**: Sidebar chat interface

The integration provides:

- Contextual AI assistance
- Memory-aware conversations through Kor'tana's backend
- Ethical discernment in responses
- Seamless user experience

## Development Tips

- The Vite dev server proxies `/copilotkit` requests to the backend
- Changes to React components hot-reload automatically
- TypeScript provides type safety throughout the application

## Learn More

- [CopilotKit Documentation](https://docs.copilotkit.ai/)
- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
