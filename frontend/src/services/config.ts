/**
 * Kor'tana Configuration Service
 * Handles unified environment variable access across runtime and build-time
 */

declare global {
    interface Window {
        __KORTANA__?: {
            VITE_API_URL?: string;
            ENVIRONMENT?: string;
            VERSION?: string;
        };
    }
}

const getEnv = (key: string, defaultValue: string = ''): string => {
    // 1. Check Runtime Injection (window.__KORTANA__)
    if (window.__KORTANA__ && (window.__KORTANA__ as any)[key]) {
        return (window.__KORTANA__ as any)[key];
    }

    // 2. Check Build-time Injection (import.meta.env)
    // Vite prefixes env vars with VITE_
    const viteKey = key.startsWith('VITE_') ? key : `VITE_${key}`;
    if (import.meta.env[viteKey]) {
        return import.meta.env[viteKey];
    }

    return defaultValue;
};

export const config = {
    apiUrl: getEnv('VITE_API_URL', ''),
    environment: getEnv('ENVIRONMENT', 'development'),
    version: getEnv('VERSION', '0.1.0'),
    isDevelopment: getEnv('ENVIRONMENT', 'development') === 'development',
};

export default config;
