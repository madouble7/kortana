/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_WS_URL: string;
  readonly VITE_APP_NAME: string;
  readonly VITE_ENVIRONMENT: string;
  readonly VITE_APP_VERSION: string;
  readonly VITE_ENABLE_CHAT: string;
  readonly VITE_ENABLE_TASKS: string;
  readonly VITE_ENABLE_AUTONOMY: string;
  readonly VITE_ENABLE_GITHUB: string;
  readonly VITE_ENABLE_MEMORY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
