import React, { useState } from 'react';
import PublicAPIs from '../services/publicApis';

export default function WeatherCard() {
    const [place, setPlace] = useState('New York');
    const [out, setOut] = useState<{ temp?: number; hum?: number; label?: string; err?: string; loading?: boolean }>({});

    const run = async () => {
        try {
            setOut({ loading: true });
            const hits = await PublicAPIs.nominatimSearch(place);
            if (!hits?.length) return setOut({ err: 'No results' });
            const { lat, lon, display_name } = hits[0];
            const wx = await PublicAPIs.weatherOpenMeteo(parseFloat(lat), parseFloat(lon));
            const t = wx?.hourly?.temperature_2m?.[0];
            const h = wx?.hourly?.relative_humidity_2m?.[0];
            setOut({ temp: t, hum: h, label: display_name });
        } catch (e: any) {
            setOut({ err: String(e) });
        }
    };

    return (
        <div className="p-4 rounded-2xl shadow-sm border bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold">Weather</h3>
            <div className="mt-2 flex gap-2">
                <input
                    className="border rounded px-2 py-1 flex-1 bg-white dark:bg-gray-900"
                    value={place}
                    onChange={e => setPlace(e.target.value)}
                />
                <button onClick={run} className="px-3 py-1 rounded bg-black text-white dark:bg-indigo-600">
                    Get
                </button>
            </div>
            <div className="mt-3 text-sm">
                {out.err && <div className="text-red-600">{out.err}</div>}
                {out.loading && !out.err && <div className="opacity-60">Loading…</div>}
                {out.label && <div className="opacity-70">{out.label}</div>}
                {'temp' in out && out.temp !== undefined && (
                    <div>Temp: {out.temp}°C &nbsp; RH: {out.hum ?? '—'}%</div>
                )}
            </div>
        </div>
    );
}
