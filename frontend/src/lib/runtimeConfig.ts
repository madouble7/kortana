interface KortanaRuntimeConfig {
  VITE_API_URL?: string;
  ENVIRONMENT?: string;
  VERSION?: string;
}

type KortanaWindow = Window & {
  __KORTANA__?: KortanaRuntimeConfig;
};

const getRuntimeConfig = (): KortanaRuntimeConfig | undefined => {
  if (typeof window === 'undefined') {
    return undefined;
  }

  return (window as KortanaWindow).__KORTANA__;
};

const getSameOriginHttpBase = () => {
  if (typeof window === 'undefined') {
    return '';
  }

  return window.location.origin;
};

const getSameOriginWebSocketBase = () => {
  if (typeof window === 'undefined') {
    return '';
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}`;
};

export const getApiBaseUrl = () => {
  const runtimeConfig = getRuntimeConfig();

  // Backend-injected runtime config is authoritative, including explicit same-origin "".
  if (runtimeConfig && runtimeConfig.VITE_API_URL !== undefined) {
    return runtimeConfig.VITE_API_URL;
  }

  // Build-time API URLs are only respected during local Vite development.
  if (import.meta.env.DEV && import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // When running locally under Vite dev proxy, prefer same-origin
  // so we avoid CORS. Vite proxies /api -> :8000 automatically.
  if (typeof window !== 'undefined' && window.location.port === '5173') {
    return '';
  }

  return '';
};

export const getWebSocketBaseUrl = () => {
  const apiBaseUrl = getApiBaseUrl();

  if (apiBaseUrl) {
    return apiBaseUrl.replace(/^http/, 'ws');
  }

  if (typeof window !== 'undefined' && window.location.port === '5173') {
    return `ws://${window.location.hostname}:8000`;
  }

  return getSameOriginWebSocketBase();
};

export const getDisplayApiBaseUrl = () => {
  const apiBaseUrl = getApiBaseUrl();

  if (apiBaseUrl) {
    return apiBaseUrl;
  }

  return `${getSameOriginHttpBase()} (same-origin)`;
};

export const getRuntimeEnvironment = () => {
  const runtimeConfig = getRuntimeConfig();

  if (runtimeConfig?.ENVIRONMENT) {
    return runtimeConfig.ENVIRONMENT;
  }

  return import.meta.env.VITE_ENVIRONMENT || (import.meta.env.DEV ? 'development' : 'production');
};
