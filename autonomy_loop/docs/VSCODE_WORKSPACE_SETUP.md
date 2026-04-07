# Kor'tana VS Code Workspace Setup

This document outlines the enhanced developer experience features configured in this VS Code workspace. These tasks, debuggers, and extensions are designed to streamline development for the Kor'tana project.

## 🚀 One-Click Actions (Tasks)

The workspace includes several pre-configured tasks to automate common workflows. You can access them via `Terminal > Run Task...` or `Ctrl+Shift+P` -> `Tasks: Run Task`.

-   **Start Full Stack**: This is the default build task (`Ctrl+Shift+B`). It starts both the Python backend and the Vite frontend dev server in separate integrated terminals.
-   **Start Backend (Python/FastAPI)**: Runs `docker compose up --build` for the backend service defined in `services/local-api-v2`.
-   **Start Frontend (Vite)**: Runs `npm run dev` to start the frontend development server.

### Covenant-Specific Tasks

These are placeholder tasks mentioned in the covenant protocols. Their functionality can be expanded later.

-   **✨ Run SSP (Session Start Protocol)**
-   **📜 Start Ritual Manager**
-   **🌀 Load Roo Identity**

## 🐛 Debugging Profiles

The workspace is configured for full-stack debugging. Press `F5` or go to the "Run and Debug" panel (`Ctrl+Shift+D`) to select a launch configuration.

-   **🌌 Debug Full Stack**: This is a compound configuration that launches both the Python backend and a Chrome instance for frontend debugging simultaneously. This is the recommended way to debug the entire application.
-   **Debug Backend (Python/FastAPI)**: Starts a debug session for the Python FastAPI server. Breakpoints can be set in the Python code under `services/local-api-v2/app`.
-   **Debug Frontend (Chrome)**: Launches a debug-ready Chrome instance connected to the Vite dev server (`http://localhost:5173`). You can set breakpoints and inspect your React components in the browser's developer tools.
-   **✨ Debug Constellation Dashboard**: A shortcut to launch a Chrome debugger for the frontend. You will need to navigate to the Constellation Dashboard from the main dashboard to debug it.
-   **📜 Debug Ritual Manager**: A placeholder debug profile that launches the frontend.

## 🧩 Recommended Extensions

The `.vscode/extensions.json` file contains a list of recommended extensions for this project. When you open the workspace, VS Code will prompt you to install them. This ensures a consistent development environment for all agents and contributors.

The list includes essential tools for Python, TypeScript/React, Docker, Git, Tailwind CSS, and more.
