import React, { useState, useEffect } from 'react';
import { Heart, Send, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function PrayerAgentStatus() {
  const [prayerStatus, setPrayerStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [customRequest, setCustomRequest] = useState('');
  const [selectedPerson, setSelectedPerson] = useState('both');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    checkPrayerStatus();
  }, []);

  const checkPrayerStatus = async () => {
    try {
      // Mocking the API call for now, since we don't have the backend endpoint
      setTimeout(() => {
        setPrayerStatus({
          status: 'active',
          lastPrayerTime: new Date().toISOString(),
          totalPrayers: 42,
          recentRequests: [
            { id: 1, person: 'both', request: 'Guidance and wisdom', time: new Date().toISOString() }
          ]
        });
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to check prayer status:', error);
      setError('Failed to load prayer status');
      setLoading(false);
    }
  };

  const handleCustomPrayer = async () => {
    if (!customRequest.trim()) return;

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      // Mocking the API call
      setTimeout(() => {
        setSuccess('Prayer request submitted successfully');
        setCustomRequest('');
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to submit prayer request:', error);
      setError('Failed to submit prayer request');
      setLoading(false);
    }
  };

  if (loading && !prayerStatus) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="animate-spin text-indigo-500" size={32} />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Heart className="text-rose-500" />
          Prayer Agent Status
        </h2>
        <p className="text-gray-500">Monitor and submit requests to the autonomous prayer agent.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm text-gray-500 mb-1">Agent Status</h3>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${prayerStatus?.status === 'active' ? 'bg-emerald-500' : 'bg-red-500'}`} />
            <span className="text-xl font-bold">{prayerStatus?.status === 'active' ? 'Active' : 'Inactive'}</span>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm text-gray-500 mb-1">Total Prayers</h3>
          <p className="text-xl font-bold">{prayerStatus?.totalPrayers || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm text-gray-500 mb-1">Last Prayer Time</h3>
          <p className="text-xl font-bold">
            {prayerStatus?.lastPrayerTime ? new Date(prayerStatus.lastPrayerTime).toLocaleTimeString() : 'N/A'}
          </p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-200 dark:border-gray-700 mb-8">
        <h3 className="text-lg font-semibold mb-4">Submit Custom Prayer Request</h3>
        
        <div className="flex flex-col gap-4">
          <select
            value={selectedPerson}
            onChange={(e) => setSelectedPerson(e.target.value)}
            className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="both">Both</option>
            <option value="self">Self</option>
            <option value="others">Others</option>
          </select>
          
          <textarea
            value={customRequest}
            onChange={(e) => setCustomRequest(e.target.value)}
            placeholder="Enter your prayer request here..."
            className="w-full bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500 min-h-[120px] resize-y"
          />
          
          <button
            onClick={handleCustomPrayer}
            disabled={loading || !customRequest.trim()}
            className="bg-rose-600 hover:bg-rose-700 disabled:bg-rose-400 text-white px-6 py-3 rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
            Submit Request
          </button>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl flex items-start gap-3">
            <AlertCircle className="shrink-0 mt-0.5" size={20} />
            <p>{error}</p>
          </div>
        )}

        {success && (
          <div className="mt-4 p-4 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-xl flex items-start gap-3">
            <CheckCircle2 className="shrink-0 mt-0.5" size={20} />
            <p>{success}</p>
          </div>
        )}
      </div>
    </div>
  );
}
