// Public no-auth API adapters with light caching + safe fetch
// Single normalized implementation.

type Json = any;

interface CacheEntry { exp: number; data: any }
const cache = new Map<string, CacheEntry>();

function getCached<T>(k: string): T | null {
    const hit = cache.get(k);
    if (!hit) return null;
    if (hit.exp < Date.now()) { cache.delete(k); return null; }
    return hit.data as T;
}
function setCached<T>(k: string, data: T, ttlMs: number) {
    cache.set(k, { exp: Date.now() + ttlMs, data });
}

async function getJSON<T = Json>(url: string, ttlMs?: number): Promise<T> {
    if (ttlMs) {
        const c = getCached<T>(url);
        if (c) return c;
    }
    const r = await fetch(url, { method: 'GET' });
    if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
    const data = await r.json() as T;
    if (ttlMs) setCached(url, data, ttlMs);
    return data;
}

const PROXY_BASE = (import.meta as any)?.env?.VITE_PROXY_BASE || (globalThis as any)?.process?.env?.VITE_PROXY_BASE || '';
export const viaProxy = (u: string) => PROXY_BASE ? `${PROXY_BASE.replace(/\/$/, '')}/proxy?url=${encodeURIComponent(u)}` : u;

const PublicAPIs = {
    weatherOpenMeteo(lat: number, lon: number) {
        const u = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&hourly=temperature_2m,relativehumidity_2m&current_weather=true`;
        return getJSON<any>(viaProxy(u), 15 * 60_000);
    },
    holidays(year: number, country = 'US') {
        const u = `https://date.nager.at/api/v3/PublicHolidays/${year}/${country}`;
        return getJSON<any[]>(viaProxy(u), 7 * 24 * 60 * 60_000);
    },
    openLibrarySearch(q: string, limit = 10) {
        const u = `https://openlibrary.org/search.json?q=${encodeURIComponent(q)}&limit=${limit}`;
        return getJSON<{ docs: any[] }>(viaProxy(u), 5 * 60_000);
    },
    async hackerNewsTop(limit = 10) {
        const ids = await getJSON<number[]>(viaProxy('https://hacker-news.firebaseio.com/v0/topstories.json'), 60_000);
        const slice = (ids || []).slice(0, limit);
        const items = await Promise.all(slice.map(id => getJSON<any>(viaProxy(`https://hacker-news.firebaseio.com/v0/item/${id}.json`), 5 * 60_000)));
        return items.filter(Boolean);
    },
    nominatimSearch(q: string) {
        const raw = `https://nominatim.openstreetmap.org/search?format=jsonv2&q=${encodeURIComponent(q)}`;
        return getJSON<any[]>(viaProxy(raw));
    }
};

export default PublicAPIs;
