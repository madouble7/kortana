import React, { useEffect, useState } from 'react';
import PublicAPIs from '../services/publicApis';

export default function HNCard() {
    const [items, setItems] = useState<any[] | null>(null);
    const [err, setErr] = useState<string | null>(null);

    const run = async () => {
        try {
            setErr(null);
            setItems(null);
            const d = await PublicAPIs.hackerNewsTop(10);
            setItems(d);
        } catch (e: any) {
            setErr(String(e));
        }
    };

    useEffect(() => { run(); }, []);

    return (
        <div className="p-4 rounded-2xl shadow-sm border bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <div className="flex justify-between items-center">
                <h3 className="font-semibold">Hacker News — Top</h3>
                <button onClick={run} className="text-xs px-2 py-1 rounded bg-black text-white dark:bg-indigo-600">Refresh</button>
            </div>
            <div className="mt-2 text-sm">
                {err && <div className="text-red-600">{err}</div>}
                {!err && !items && <div className="opacity-60">Loading…</div>}
                {items && (
                    <ol className="space-y-1 list-decimal pl-4">
                        {items.map(item => (
                            <li key={item.id}>
                                <a
                                    href={item.url || `https://news.ycombinator.com/item?id=${item.id}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="underline"
                                >
                                    {item.title}
                                </a>
                            </li>
                        ))}
                    </ol>
                )}
            </div>
        </div>
    );
}
