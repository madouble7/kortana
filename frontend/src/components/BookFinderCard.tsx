import React, { useState } from 'react';
import PublicAPIs from '../services/publicApis';

export default function BookFinderCard() {
    const [q, setQ] = useState('design patterns');
    const [hits, setHits] = useState<any[] | null>(null);
    const [err, setErr] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const run = async () => {
        try {
            if (!q.trim()) return;
            setErr(null);
            setLoading(true);
            setHits(null);
            const r = await PublicAPIs.openLibrarySearch(q, 10);
            setHits(r.docs || []);
        } catch (e: any) {
            setErr(String(e));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-4 rounded-2xl shadow-sm border bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold">Book Finder</h3>
            <div className="mt-2 flex gap-2">
                <input
                    className="border rounded px-2 py-1 flex-1 bg-white dark:bg-gray-900"
                    value={q}
                    onChange={e => setQ(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && run()}
                    placeholder="Search books..."
                />
                <button onClick={run} className="px-3 py-1 rounded bg-black text-white dark:bg-indigo-600">Search</button>
            </div>
            <div className="mt-3 text-sm">
                {err && <div className="text-red-600">{err}</div>}
                {loading && <div className="opacity-60">Loading…</div>}
                {hits && (
                    <ul className="space-y-1">
                        {hits.map((b, i) => (
                            <li key={b.key || i}>
                                <span className="font-medium">{b.title}</span>
                                {b.author_name && <span className="opacity-70"> — {b.author_name.slice(0, 3).join(', ')}</span>}
                            </li>
                        ))}
                        {!hits.length && <li className="opacity-60">No results</li>}
                    </ul>
                )}
            </div>
        </div>
    );
}
