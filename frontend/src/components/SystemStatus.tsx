import React, { useState, useEffect } from 'react';
import { apiService, HealthResponse } from '../services/apiService';

interface SystemStatusProps {
  health: HealthResponse | null;
}

export const SystemStatus: React.FC<SystemStatusProps> = ({ health }) => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="system-status">
      <h2>🔮 System Status Overview</h2>

      <div className="status-grid">
        <div className="status-card">
          <h3>Backend Health</h3>
          <div className={`status-indicator ${health?.status === 'alive' ? 'online' : 'offline'}`}>
            {health?.status === 'alive' ? '🟢 Online' : '🔴 Offline'}
          </div>
          <p>{health?.message || 'Checking...'}</p>
        </div>

        <div className="status-card">
          <h3>Current Time</h3>
          <div className="time-display">
            {currentTime.toLocaleString()}
          </div>
          <p>System synchronized</p>
        </div>

        <div className="status-card">
          <h3>Constellation Phase</h3>
          <div className="phase-indicator">
            Phase 3: Autonomous Development
          </div>
          <p>Genesis protocols active</p>
        </div>

        <div className="status-card">
          <h3>API Endpoints</h3>
          <div className="endpoint-list">
            <div>✅ /api/health</div>
            <div>✅ /api/prayer</div>
            <div>✅ /api/gemini</div>
            <div>✅ /api/github</div>
            <div>✅ /api/memory</div>
            <div>✅ /api/agents</div>
          </div>
        </div>
      </div>

      <div className="system-info">
        <h3>System Information</h3>
        <div className="info-grid">
          <div>
            <strong>Backend URL:</strong> http://localhost:8001
          </div>
          <div>
            <strong>Frontend:</strong> React + TypeScript
          </div>
          <div>
            <strong>Database:</strong> SQLite (Memory persistence)
          </div>
          <div>
            <strong>Autonomous Files:</strong> 300+ generated
          </div>
          <div>
            <strong>Prayer Cycles:</strong> Every 3 hours
          </div>
          <div>
            <strong>VS Code Extension:</strong> Framework active
          </div>
        </div>
      </div>
    </div>
  );
};
