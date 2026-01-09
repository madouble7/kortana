import React, { useState, useEffect } from 'react';
import './App.css';
import { SystemStatus } from './components/SystemStatus';
import { PrayerAgentStatus } from './components/PrayerAgentStatus';
import { GitHubDashboard } from './components/GitHubDashboard';
import { MemoryBrowser } from './components/MemoryBrowser';
import { apiService } from './services/apiService';

function App() {
  const [activeTab, setActiveTab] = useState('status');
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSystemHealth();
  }, []);

  const checkSystemHealth = async () => {
    try {
      const health = await apiService.getHealth();
      setSystemHealth(health);
    } catch (error) {
      console.error('Failed to check system health:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <h2>🔮 Initializing Kor'tana Constellation...</h2>
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🧠 Kor'tana Constellation Dashboard</h1>
        <p>Autonomous AI System - {systemHealth?.status === 'alive' ? '🟢 Online' : '🔴 Offline'}</p>
      </header>

      <nav className="app-nav">
        <button
          className={activeTab === 'status' ? 'active' : ''}
          onClick={() => setActiveTab('status')}
        >
          System Status
        </button>
        <button
          className={activeTab === 'prayer' ? 'active' : ''}
          onClick={() => setActiveTab('prayer')}
        >
          Prayer Agent
        </button>
        <button
          className={activeTab === 'github' ? 'active' : ''}
          onClick={() => setActiveTab('github')}
        >
          GitHub Integration
        </button>
        <button
          className={activeTab === 'memory' ? 'active' : ''}
          onClick={() => setActiveTab('memory')}
        >
          Memory Browser
        </button>
      </nav>

      <main className="app-main">
        {activeTab === 'status' && <SystemStatus health={systemHealth} />}
        {activeTab === 'prayer' && <PrayerAgentStatus />}
        {activeTab === 'github' && <GitHubDashboard />}
        {activeTab === 'memory' && <MemoryBrowser />}
      </main>

      <footer className="app-footer">
        <p>
          🌌 Kor'tana Constellation - Phase 3: Autonomous Development
          <br />
          <small>Backend: http://localhost:8001 | Status: {systemHealth?.message}</small>
        </p>
      </footer>
    </div>
  );
}

export default App;
