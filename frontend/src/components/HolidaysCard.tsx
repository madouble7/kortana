import React, { useEffect, useState } from 'react';
import PublicAPIs from '../services/publicApis';

export default function HolidaysCard() {
    const [country, setCountry] = useState('US');
    const [year, setYear] = useState(new Date().getFullYear());
    const [days, setDays] = useState<any[] | null>(null);
    const [err, setErr] = useState<string | null>(null);

    const run = async () => {
        try {
            setErr(null);
            setDays(null);
            const d = await PublicAPIs.holidays(year, country);
            setDays(d.slice(0, 10));
        } catch (e: any) {
            setErr(String(e));
        }
    };

    useEffect(() => { run(); }, []);

    return (
        <div className="p-4 rounded-2xl shadow-sm border bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold">Public Holidays</h3>
            <div className="mt-2 flex gap-2">
                <input
                    className="border rounded px-2 py-1 w-20 bg-white dark:bg-gray-900"
                    value={country}
                    onChange={e => setCountry(e.target.value.toUpperCase())}
                />
                <input
                    className="border rounded px-2 py-1 w-24 bg-white dark:bg-gray-900"
                    type="number"
                    value={year}
                    onChange={e => setYear(parseInt(e.target.value || `${new Date().getFullYear()}`, 10))}
                />
                <button onClick={run} className="px-3 py-1 rounded bg-black text-white dark:bg-indigo-600">
                    Load
                </button>
            </div>
            <div className="mt-3 text-sm">
                {err && <div className="text-red-600">{err}</div>}
                {!err && !days && <div className="opacity-60">Loading…</div>}
                {days && (
                    <ul className="space-y-1">
                        {days.map(d => (
                            <li key={d.date}>
                                <span className="font-medium">{d.date}</span> — {d.localName || d.name}
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}
