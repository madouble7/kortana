import React, { useState } from 'react';
import { MapPin, Search, Loader2, Navigation, Star } from 'lucide-react';
import { getAI } from '../services/apiService';

export default function MapsGrounding() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const ai = getAI();
      const response = await ai.models.generateContent({
        model: "gemini-2.5-flash",
        contents: query,
        config: {
          tools: [{ googleMaps: {} }],
        },
      });

      const chunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks;
      if (chunks) {
        setResults(chunks.filter((c: any) => c.maps).map((c: any) => c.maps));
      } else {
        setResults([]);
      }
    } catch (err) {
      setError('Failed to search maps. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2">Maps Grounding</h2>
        <p className="text-gray-500">Find real-world places with AI precision.</p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-200 dark:border-gray-700 mb-8">
        <div className="flex gap-4">
          <div className="relative flex-1">
            <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Best coffee shops in San Francisco..."
              className="w-full bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={isLoading || !query.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-6 py-3 rounded-xl font-bold flex items-center gap-2 transition-all"
          >
            {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
            Search
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl mb-8">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {results.length > 0 ? (
          results.map((place, idx) => (
            <div key={idx} className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-indigo-500 transition-all shadow-sm">
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-bold">{place.title}</h3>
                <a 
                  href={place.uri} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-indigo-600 hover:text-indigo-700"
                >
                  <Navigation size={20} />
                </a>
              </div>
              <p className="text-sm text-gray-500 mb-4">{place.address || 'No address provided'}</p>
              <div className="flex items-center gap-4 text-sm">
                {place.rating && (
                  <div className="flex items-center gap-1 text-amber-500">
                    <Star size={14} fill="currentColor" />
                    <span className="font-bold">{place.rating}</span>
                  </div>
                )}
                <span className="text-gray-400">|</span>
                <span className="text-gray-500">{place.category || 'Place'}</span>
              </div>
            </div>
          ))
        ) : !isLoading && (
          <div className="text-center py-20 opacity-30">
            <Search size={48} className="mx-auto mb-4" />
            <p>Search for places to see results</p>
          </div>
        )}
      </div>
    </div>
  );
}
