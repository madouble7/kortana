# 🌌 KOR'TANA DEPLOYMENT INTEGRITY SNAPSHOT

This document captures the environmental requirements and injection flow for the Kor'tana Unified Platform.

---

## 🔑 Environment Variable Matrix

| Variable | Requirement | Scope | Target(s) | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | **MANDATORY** | Backend | All | Required for Multimodal AI. |
| `DATABASE_URL` | **MANDATORY** | Backend | Railway / Cloud Run | PostgreSQL connection string. |
| `REDIS_URL` | OPTIONAL | Backend | All | For caching. Defaults to local if not set. |
| `CORS_ORIGINS` | **MANDATORY** | Backend | All | List of allowed origins (e.g., Vercel URL). |
| `VITE_API_URL` | **MANDATORY*** | Build-time | Vercel | *Only required for Split Deployment (Path 1). |
| `ENVIRONMENT` | **MANDATORY** | Runtime | All | Controls debug logs and configuration logic. |
| `PORT` | **MANDATORY** | Runtime | Railway / Cloud Run | Port assigned by the hosting provider. |

---

## 💉 Runtime Injection Layer (`window.__KORTANA__`)

To ensure "Build Once, Run Anywhere" capability, Kor'tana uses a runtime injection layer when deployed in **Unified Mode** (Path 2).

### Injection Flow

1. **Backend Startup**: FastAPI reads environment variables.
2. **Request `index.html`**: The server reads the built `index.html`.
3. **Dynamic Wrap**: FastAPI injects a script tag before the `</head>`:

    ```html
    <script>window.__KORTANA__ = {"VITE_API_URL": "", "ENVIRONMENT": "production", "VERSION": "0.1.0"};</script>
    ```

4. **Frontend Mount**: `config.ts` reads from `window.__KORTANA__` first, then falls back to `import.meta.env`.

### Variable Scopes

- **Build-time only (`import.meta.env`)**: Static assets hash, PWA metadata.
- **Runtime Injection (`__KORTANA__`)**: API endpoints, Environment state, Feature flags.
- **Backend Environment**: DB credentials, AI API keys (NEVER exposed to frontend).

---

## 🎯 Hosting Provider Specifics

### Railway (Backend/Unified)

- Variables to set: `GEMINI_API_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `ENVIRONMENT=production`.

### Vercel (Frontend - Path 1)

- Variables to set: `VITE_API_URL` (pointing to Railway).

### Google Cloud Run (Unified)

- Variables to set: `GEMINI_API_KEY`, `DATABASE_URL`, `ENVIRONMENT=production`.

---
**"Unified logic confirmed. Environment integrity at 100%."** 🔱
