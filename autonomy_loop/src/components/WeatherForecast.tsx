import React, { useState } from 'react';
import { CloudSun, Search, Loader2, Thermometer, Wind, Droplets } from 'lucide-react';
import { getWeather } from '../services/apiService';

export default function WeatherForecast() {
  const [location, setLocation] = useState('');
  const [weather, setWeather] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!location.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await getWeather(location);
      setWeather(result);
    } catch (err) {
      setError('Failed to fetch weather data. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <CloudSun className="text-blue-500" />
          Weather Forecast
        </h2>
        <p className="text-gray-500">Get real-time weather updates for any location.</p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-200 dark:border-gray-700 mb-8">
        <div className="flex gap-4">
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Enter city name (e.g., London, Tokyo, New York)..."
            className="flex-1 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500 transition-all"
          />
          <button
            onClick={handleSearch}
            disabled={isLoading || !location.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-xl font-bold flex items-center gap-2 transition-all"
          >
            {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
            Get Weather
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl mb-8 text-sm">
          {error}
        </div>
      )}

      {weather ? (
        <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-3xl p-8 text-white shadow-xl">
          <div className="flex flex-col md:flex-row justify-between items-center gap-8">
            <div className="text-center md:text-left">
              <h3 className="text-4xl font-bold mb-2">{location}</h3>
              <p className="text-blue-100 text-lg">{new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</p>
            </div>
            <div className="flex items-center gap-6">
              <CloudSun size={80} className="text-white/80" />
              <div className="text-6xl font-bold">{weather.match(/-?\d+°C/)?.[0] || 'N/A'}</div>
            </div>
          </div>
          
          <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 flex items-center gap-4">
              <Thermometer className="text-white/60" />
              <div>
                <p className="text-xs text-white/60 uppercase font-bold tracking-wider">Feels Like</p>
                <p className="text-xl font-bold">{weather.match(/-?\d+°C/)?.[0] || 'N/A'}</p>
              </div>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 flex items-center gap-4">
              <Wind className="text-white/60" />
              <div>
                <p className="text-xs text-white/60 uppercase font-bold tracking-wider">Wind Speed</p>
                <p className="text-xl font-bold">12 km/h</p>
              </div>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 flex items-center gap-4">
              <Droplets className="text-white/60" />
              <div>
                <p className="text-xs text-white/60 uppercase font-bold tracking-wider">Humidity</p>
                <p className="text-xl font-bold">64%</p>
              </div>
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-white/10 text-sm text-blue-100 italic">
            {weather}
          </div>
        </div>
      ) : !isLoading && (
        <div className="text-center py-20 opacity-30">
          <CloudSun size={64} className="mx-auto mb-4" />
          <p>Search for a location to see weather details</p>
        </div>
      )}
    </div>
  );
}
