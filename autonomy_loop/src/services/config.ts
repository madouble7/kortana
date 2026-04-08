/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/

// Configuration is sourced from three places, in order of precedence:
// 1. A global __KORTANA__ object on the window (for production deployments/runtime injection)
// 2. Vite environment variables (for local development)
// 3. Sensible defaults

const windowConfig = (window as any).__KORTANA__ || {};
// Fallback to an empty object if import.meta.env is undefined to prevent runtime errors.
const env = (import.meta as any).env || {};

let apiBase = windowConfig.apiBase || env.VITE_API_BASE || '/api';
if (apiBase.includes('localhost') && typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
  apiBase = '/api';
}

export const API_BASE = apiBase;
// @ts-ignore
export const API_KEY = windowConfig.apiKey || process.env.API_KEY || import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.VITE_KORTANA_API_KEY || process.env.GEMINI_API_KEY || '';

if (!API_KEY && typeof window !== 'undefined' && !window.location.hostname.includes('localhost')) {
  // In production-like environments, we should be loud about missing keys
  console.error('CRITICAL: No API key provided for Gemini services. Application will fail to function correctly.');
}
