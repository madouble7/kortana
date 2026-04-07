/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React, { useState } from 'react';
import { Loader, AlertTriangle, Search, Globe, ExternalLink, BookOpen } from 'lucide-react';
import { searchGrounding } from '../services/apiService';
import { GroundingSource } from '../types';

export default function SearchGrounding() {
    const [query, setQuery] = useState('');
    const [response, setResponse] = useState<string | null>(null);
    const [sources, setSources] = useState<GroundingSource[]>([]);
    const [isThinking, setIsThinking] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async () => {
        if (!query.trim() || isThinking) return;

        setIsThinking(true);
        setError(null);
        setResponse(null);
        setSources([]);

        try {
            const result = await searchGrounding(query);
            setResponse(result.reply || "No response generated.");
            setSources(result.sources || []);
        } catch (e) {
            console.error("Search Grounding Error:", e);
            setError(e instanceof Error ? e.message : "An error occurred while fetching the answer.");
        } finally {
            setIsThinking(false);
        }
    };

    return (
        <div className="p-4 sm:p-8 max-w-4xl mx-auto">
            <div className="text-center mb-10">
                <h2 className="text-3xl sm:text-4xl font-bold mb-2">Search Grounding</h2>
                <p className="text-md sm:text-lg text-gray-600 dark:text-gray-400">
                    Get up-to-date, fact-checked answers using Google Search.
                </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-2 mb-8 flex items-center gap-2 focus-within:ring-2 focus-within:ring-indigo-500 transition-all">
                <div className="p-3 text-indigo-500">
                    <Globe size={24} />
                </div>
                <input
                    className="flex-1 bg-transparent border-none outline-none text-gray-900 dark:text-white placeholder-gray-400 py-3"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask about current events, facts, or news..."
                    disabled={isThinking}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(); }}
                />
                <button
                    onClick={handleSearch}
                    disabled={!query.trim() || isThinking}
                    className="p-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {isThinking ? <Loader size={20} className="animate-spin" /> : <Search size={20} />}
                </button>
            </div>

            {error && (
                <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-xl flex items-start gap-3">
                    <AlertTriangle size={20} className="shrink-0 mt-0.5" />
                    <div>
                        <p className="font-semibold">Search Failed</p>
                        <p className="text-sm opacity-90">{error}</p>
                    </div>
                </div>
            )}

            {response && (
                <div className="space-y-6 animate-fade-in">
                    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
                        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                            <BookOpen size={16} /> Answer
                        </h3>
                        <div className="prose dark:prose-invert max-w-none text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">
                            {response}
                        </div>
                    </div>

                    {sources.length > 0 && (
                        <div>
                            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4 px-2">
                                Sources & Citations
                            </h3>
                            <div className="grid gap-3 sm:grid-cols-2">
                                {sources.map((source, idx) => {
                                    return (
                                        <a 
                                            key={idx} 
                                            href={source.uri} 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            className="group block p-4 bg-gray-50 dark:bg-gray-900/50 hover:bg-white dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-700 rounded-xl transition-all"
                                        >
                                            <div className="flex items-start justify-between">
                                                <h4 className="font-semibold text-gray-900 dark:text-gray-100 line-clamp-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                                                    {source.title || "Source"}
                                                </h4>
                                                <ExternalLink size={14} className="text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </div>
                                            <p className="text-xs text-gray-500 mt-1 truncate font-mono opacity-70">
                                                {source.uri}
                                            </p>
                                        </a>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}