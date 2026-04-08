/**
 * KOR'TANA Dashboard Component
 * Main dashboard for system interaction and monitoring
 */

import React, { useCallback, useEffect, useState } from 'react';
import { AgentInfo, apiService, HealthResponse, SystemMetrics, TaskInfo } from '../services/apiService';
import './Dashboard.css';

interface DashboardProps {
  apiUrl?: string;
}

export const Dashboard: React.FC<DashboardProps> = () => {
  const [activeSection, setActiveSection] = useState('overview');
  const [systemInfo, setSystemInfo] = useState<HealthResponse | null>(null);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all dashboard data in parallel
      const [health, agentList, taskList, metricsData] = await Promise.all([
        apiService.getHealth().catch(() => null),
        apiService.listAgents().catch(() => []),
        apiService.getTasks().catch(() => []),
        apiService.getMetrics().catch(() => null),
      ]);

      setSystemInfo(health);
      setAgents(agentList || []);
      setTasks(taskList || []);
      setMetrics(metricsData);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();

    // Refresh data every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, [loadDashboardData]);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner-large"></div>
        <p>🔮 Loading Kor'tana Constellation...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <h2>⚠️ Connection Error</h2>
        <p>{error}</p>
        <button onClick={loadDashboardData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="dashboard-logo">
          <h1>🧠 KOR'TANA</h1>
          <span className="version">v1.0.0</span>
        </div>
        <div className="dashboard-status">
          <span className={`status-indicator ${systemInfo?.status === 'alive' ? 'online' : 'offline'}`}>
            {systemInfo?.status === 'alive' ? '● Online' : '○ Offline'}
          </span>
          <span className="timestamp">{new Date().toLocaleTimeString()}</span>
        </div>
      </header>

      {/* Navigation */}
      <nav className="dashboard-nav">
        {['overview', 'agents', 'tasks', 'memory', 'github', 'settings'].map((section) => (
          <button
            key={section}
            className={`nav-button ${activeSection === section ? 'active' : ''}`}
            onClick={() => setActiveSection(section)}
          >
            {getSectionIcon(section)}
            <span>{section.charAt(0).toUpperCase() + section.slice(1)}</span>
          </button>
        ))}
      </nav>

      {/* Main Content */}
      <main className="dashboard-main">
        {activeSection === 'overview' && (
          <OverviewSection
            systemInfo={systemInfo}
            agents={agents}
            tasks={tasks}
            metrics={metrics}
          />
        )}
        {activeSection === 'agents' && <AgentsSection agents={agents} onRefresh={loadDashboardData} />}
        {activeSection === 'tasks' && <TasksSection tasks={tasks} onRefresh={loadDashboardData} />}
        {activeSection === 'memory' && <MemorySection />}
        {activeSection === 'github' && <GitHubSection />}
        {activeSection === 'settings' && <SettingsSection />}
      </main>

      {/* Footer */}
      <footer className="dashboard-footer">
        <p>🌌 Kor'tana Constellation Dashboard - Phase 5: Frontend Integration</p>
      </footer>
    </div>
  );
};

// Section Components
const OverviewSection: React.FC<{
  systemInfo: HealthResponse | null;
  agents: AgentInfo[];
  tasks: TaskInfo[];
  metrics: SystemMetrics | null;
}> = ({ systemInfo, agents, tasks, metrics }) => (
  <div className="overview-section">
    <div className="stats-grid">
      <StatCard
        title="System Status"
        value={systemInfo?.status === 'alive' ? 'Healthy' : 'Unknown'}
        icon="💚"
        color="green"
      />
      <StatCard title="Active Agents" value={agents.length} icon="🤖" color="blue" />
      <StatCard title="Pending Tasks" value={tasks.filter(t => t.status === 'pending').length} icon="📋" color="yellow" />
      <StatCard title="Running Tasks" value={tasks.filter(t => t.status === 'running').length} icon="⚡" color="purple" />
    </div>

    <div className="overview-grid">
      <div className="card">
        <h3>🤖 Active Agents</h3>
        <AgentList agents={agents.slice(0, 5)} />
      </div>
      <div className="card">
        <h3>📋 Recent Tasks</h3>
        <TaskList tasks={tasks.slice(0, 5)} />
      </div>
    </div>

    {metrics && (
      <div className="card">
        <h3>📊 Performance Metrics</h3>
        <MetricsDisplay metrics={metrics} />
      </div>
    )}
  </div>
);

const AgentsSection: React.FC<{ agents: AgentInfo[]; onRefresh: () => void }> = ({ agents, onRefresh }) => (
  <div className="agents-section">
    <div className="section-header">
      <h2>🤖 Agent Management</h2>
      <div className="actions">
        <button className="btn-primary" onClick={onRefresh}>Refresh</button>
        <button className="btn-secondary">Create Agent</button>
      </div>
    </div>
    <AgentGrid agents={agents} />
  </div>
);

const TasksSection: React.FC<{ tasks: TaskInfo[]; onRefresh: () => void }> = ({ tasks, onRefresh }) => (
  <div className="tasks-section">
    <div className="section-header">
      <h2>📋 Task Queue</h2>
      <div className="actions">
        <button className="btn-primary" onClick={onRefresh}>Refresh</button>
        <button className="btn-secondary">New Task</button>
      </div>
    </div>
    <TaskBoard tasks={tasks} />
  </div>
);

const MemorySection: React.FC = () => (
  <div className="memory-section">
    <h2>🧠 Memory Browser</h2>
    <p>Explore and manage the knowledge base...</p>
    {/* Memory browser component */}
  </div>
);

const GitHubSection: React.FC = () => (
  <div className="github-section">
    <h2>🐙 GitHub Integration</h2>
    <p>Manage repositories, issues, and pull requests...</p>
    {/* GitHub dashboard component */}
  </div>
);

const SettingsSection: React.FC = () => (
  <div className="settings-section">
    <h2>⚙️ Settings</h2>
    <p>Configure API keys, preferences, and more...</p>
    {/* Settings component */}
  </div>
);

// Helper Components
const StatCard: React.FC<{ title: string; value: string | number; icon: string; color: string }> = ({
  title, value, icon, color
}) => (
  <div className={`stat-card ${color}`}>
    <span className="stat-icon">{icon}</span>
    <div className="stat-info">
      <span className="stat-value">{value}</span>
      <span className="stat-title">{title}</span>
    </div>
  </div>
);

const AgentList: React.FC<{ agents: AgentInfo[] }> = ({ agents }) => (
  <ul className="agent-list">
    {agents.map((agent) => (
      <li key={agent.id} className="agent-item">
        <span className="agent-name">{agent.name}</span>
        <span className={`agent-status ${agent.status}`}>{agent.status}</span>
      </li>
    ))}
    {agents.length === 0 && <li className="empty">No active agents</li>}
  </ul>
);

const TaskList: React.FC<{ tasks: TaskInfo[] }> = ({ tasks }) => (
  <ul className="task-list">
    {tasks.map((task) => (
      <li key={task.id} className="task-item">
        <span className="task-name">{task.name}</span>
        <span className={`task-status ${task.status}`}>{task.status}</span>
      </li>
    ))}
    {tasks.length === 0 && <li className="empty">No recent tasks</li>}
  </ul>
);

const AgentGrid: React.FC<{ agents: AgentInfo[] }> = ({ agents }) => (
  <div className="agent-grid">
    {agents.map((agent) => (
      <div key={agent.id} className="agent-card">
        <h4>{agent.name}</h4>
        <p>{agent.description}</p>
        <span className={`agent-badge ${agent.status}`}>{agent.status}</span>
      </div>
    ))}
    {agents.length === 0 && <p className="empty">No agents found</p>}
  </div>
);

const TaskBoard: React.FC<{ tasks: TaskInfo[] }> = ({ tasks }) => (
  <div className="task-board">
    {['pending', 'running', 'completed'].map((status) => (
      <div key={status} className={`task-column ${status}`}>
        <h4>{status.charAt(0).toUpperCase() + status.slice(1)}</h4>
        {tasks.filter(t => t.status === status).map((task) => (
          <div key={task.id} className="task-card">
            <span className="task-name">{task.name}</span>
          </div>
        ))}
      </div>
    ))}
  </div>
);

const MetricsDisplay: React.FC<{ metrics: SystemMetrics }> = ({ metrics }) => (
  <div className="metrics-display">
    <div className="metric">
      <span className="metric-label">CPU Usage</span>
      <div className="metric-bar">
        <div className="metric-fill" style={{ width: `${metrics.cpu_percent}%` }}></div>
      </div>
      <span className="metric-value">{metrics.cpu_percent}%</span>
    </div>
    <div className="metric">
      <span className="metric-label">Memory Usage</span>
      <div className="metric-bar">
        <div className="metric-fill" style={{ width: `${metrics.memory_percent}%` }}></div>
      </div>
      <span className="metric-value">{metrics.memory_percent}%</span>
    </div>
  </div>
);

function getSectionIcon(section: string): string {
  const icons: Record<string, string> = {
    overview: '📊',
    agents: '🤖',
    tasks: '📋',
    memory: '🧠',
    github: '🐙',
    settings: '⚙️',
  };
  return icons[section] || '•';
}

export default Dashboard;
