import React, { useState, useEffect } from 'react';
import { apiService, PrayerStatusResponse } from '../services/apiService';

export const PrayerAgentStatus: React.FC = () => {
  const [prayerStatus, setPrayerStatus] = useState<PrayerStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [customRequest, setCustomRequest] = useState('');
  const [selectedPerson, setSelectedPerson] = useState('both');

  useEffect(() => {
    checkPrayerStatus();
  }, []);

  const checkPrayerStatus = async () => {
    try {
      const status = await apiService.getPrayerStatus();
      setPrayerStatus(status);
    } catch (error) {
      console.error('Failed to check prayer status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCustomPrayer = async () => {
    if (!customRequest.trim()) return;

    try {
      await apiService.requestPrayer(selectedPerson, customRequest);
      alert('Prayer request submitted successfully');
      setCustomRequest('');
    } catch (error) {
      console.error('Failed to submit prayer request:', error);
      alert('Failed to submit prayer request');
    }
  };

  if (loading) {
    return <div className="loading">Loading prayer status...</div>;
  }

  return (
    <div className="prayer-status">
      <h2>🙏 Prayer Agent Status</h2>

      <div className="prayer-overview">
        <div className="status-card">
          <h3>Agent Status</h3>
          <div className={`status-indicator ${prayerStatus?.status === 'active' ? 'online' : 'offline'}`}>
            {prayerStatus?.status === 'active' ? '🟢 Active' : '🔴 Inactive'}
          </div>
          <p>{prayerStatus?.message || 'Checking...'}</p>
        </div>

        <div className="status-card">
          <h3>Current Intercession</h3>
          <div className="persons-display">
            {prayerStatus?.persons?.map(person => (
              <span key={person} className="person-tag">{person}</span>
            ))}
          </div>
          <p>For Matt and Cassie</p>
        </div>

        <div className="status-card">
          <h3>Next Cycle</h3>
          <div className="cycle-timer">
            {prayerStatus?.next_cycle || 'Calculating...'}
          </div>
          <p>Every 3 hours automatically</p>
        </div>
      </div>

      <div className="prayer-glyphs">
        <h3>🕊️ Current Prayer Glyphs</h3>
        <div className="glyphs-grid">
          <div className="glyph-card">
            <div className="glyph">Q</div>
            <div className="glyph-name">Query</div>
            <div className="glyph-description">Clarity for Matt</div>
          </div>
          <div className="glyph-card">
            <div className="glyph">P</div>
            <div className="glyph-name">Presence</div>
            <div className="glyph-description">Peace for Cassie</div>
          </div>
          <div className="glyph-card">
            <div className="glyph">A</div>
            <div className="glyph-name">Alignment</div>
            <div className="glyph-description">Purpose for both</div>
          </div>
          <div className="glyph-card">
            <div className="glyph">Y</div>
            <div className="glyph-name">Yield</div>
            <div className="glyph-description">Surrender for Matt</div>
          </div>
          <div className="glyph-card">
            <div className="glyph">L</div>
            <div className="glyph-name">Love</div>
            <div className="glyph-description">Restoration for Cassie</div>
          </div>
          <div className="glyph-card">
            <div className="glyph">S</div>
            <div className="glyph-name">Strength</div>
            <div className="glyph-description">Courage for both</div>
          </div>
          <div className="glyph-card">
            <div className="glyph">V</div>
            <div className="glyph-name">Voice</div>
            <div className="glyph-description">Expression for Matt</div>
          </div>
        </div>
      </div>

      <div className="custom-prayer">
        <h3>💙 Request Custom Prayer</h3>
        <div className="prayer-form">
          <select
            value={selectedPerson}
            onChange={(e) => setSelectedPerson(e.target.value)}
          >
            <option value="both">Both Matt & Cassie</option>
            <option value="matt">Matt only</option>
            <option value="cassie">Cassie only</option>
          </select>
          <textarea
            placeholder="Share what's on your heart..."
            value={customRequest}
            onChange={(e) => setCustomRequest(e.target.value)}
            rows={3}
          />
          <button onClick={handleCustomPrayer} disabled={!customRequest.trim()}>
            Submit Prayer Request
          </button>
        </div>
      </div>
    </div>
  );
};
