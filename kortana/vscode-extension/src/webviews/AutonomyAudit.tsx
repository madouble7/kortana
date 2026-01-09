/**
 * Autonomy Audit Component
 * React component for displaying and managing autonomous action logs
 * Integrates with the AutonomyLogger service to show real-time constellation status
 */

import React, { useState, useEffect } from 'react';
import { autonomyLogger, AutonomousAction } from '../services/AutonomyLogger';

interface AutonomyAuditProps {
    vscode: any; // VS Code API
}

interface ActionSummary {
    total: number;
    success: number;
    failed: number;
    pending: number;
    byType: Record<string, number>;
}

const AutonomyAudit: React.FC<AutonomyAuditProps> = ({ vscode }) => {
    const [recentActions, setRecentActions] = useState<string[]>([]);
    const [actionSummary, setActionSummary] = useState<ActionSummary>({
        total: 0,
        success: 0,
        failed: 0,
        pending: 0,
        byType: {}
    });
    const [isLoading, setIsLoading] = useState(true);
    const [lastSync, setLastSync] = useState<string>('');

    useEffect(() => {
        loadAuditData();
        // Set up periodic refresh
        const interval = setInterval(loadAuditData, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, []);

    const loadAuditData = async () => {
        try {
            setIsLoading(true);
            const actions = await autonomyLogger.getRecentActions(20);
            setRecentActions(actions);
            setActionSummary(calculateSummary(actions));

            // Update last sync time
            const now = new Date().toISOString();
            setLastSync(now);
        } catch (error) {
            console.error('Failed to load audit data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const calculateSummary = (actions: string[]): ActionSummary => {
        const summary: ActionSummary = {
            total: actions.length,
            success: 0,
            failed: 0,
            pending: 0,
            byType: {}
        };

        actions.forEach(action => {
            // Extract status from action string
            if (action.toLowerCase().includes('success')) {
                summary.success++;
            } else if (action.toLowerCase().includes('failed')) {
                summary.failed++;
            } else if (action.toLowerCase().includes('pending')) {
                summary.pending++;
            }

            // Extract action type
            const typeMatch = action.match(/\[.*?\]\s+(\w+):/);
            if (typeMatch) {
                const type = typeMatch[1].toLowerCase();
                summary.byType[type] = (summary.byType[type] || 0) + 1;
            }
        });

        return summary;
    };

    const getStatusColor = (status: string): string => {
        switch (status.toLowerCase()) {
            case 'success': return '#28a745';
            case 'failed': return '#dc3545';
            case 'pending': return '#ffc107';
            default: return '#6c757d';
        }
    };

    const formatActionType = (actionString: string): string => {
        const typeMatch = actionString.match(/\[.*?\]\s+(\w+):/);
        return typeMatch ? typeMatch[1] : 'UNKNOWN';
    };

    const formatTimestamp = (actionString: string): string => {
        const timeMatch = actionString.match(/\[([^\]]+)\]/);
        return timeMatch ? timeMatch[1] : '';
    };

    const formatDescription = (actionString: string): string => {
        const descMatch = actionString.match(/:\s*(.+)$/);
        return descMatch ? descMatch[1] : actionString;
    };

    const getStatusFromAction = (actionString: string): string => {
        if (actionString.toLowerCase().includes('success')) return 'success';
        if (actionString.toLowerCase().includes('failed')) return 'failed';
        if (actionString.toLowerCase().includes('pending')) return 'pending';
        return 'unknown';
    };

    return (
        <div className="autonomy-audit">
            <style>{`
                .autonomy-audit {
                    padding: 20px;
                    font-family: var(--vscode-font-family);
                    color: var(--vscode-foreground);
                    background: var(--vscode-editor-background);
                }
                .audit-header {
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid var(--vscode-panel-border);
                }
                .audit-title {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                .audit-subtitle {
                    font-size: 12px;
                    color: var(--vscode-descriptionForeground);
                }
                .summary-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 10px;
                    margin-bottom: 20px;
                }
                .summary-card {
                    background: var(--vscode-editorWidget-background);
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 4px;
                    padding: 12px;
                    text-align: center;
                }
                .summary-value {
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 4px;
                }
                .summary-label {
                    font-size: 11px;
                    text-transform: uppercase;
                    color: var(--vscode-descriptionForeground);
                }
                .actions-list {
                    max-height: 400px;
                    overflow-y: auto;
                }
                .action-item {
                    display: flex;
                    align-items: center;
                    padding: 8px 12px;
                    margin-bottom: 4px;
                    background: var(--vscode-list-inactiveSelectionBackground);
                    border-radius: 4px;
                    border-left: 3px solid;
                }
                .action-type {
                    font-size: 10px;
                    font-weight: bold;
                    text-transform: uppercase;
                    padding: 2px 6px;
                    border-radius: 2px;
                    background: var(--vscode-badge-background);
                    color: var(--vscode-badge-foreground);
                    margin-right: 8px;
                    min-width: 60px;
                    text-align: center;
                }
                .action-content {
                    flex: 1;
                }
                .action-description {
                    font-size: 13px;
                    margin-bottom: 2px;
                }
                .action-meta {
                    font-size: 11px;
                    color: var(--vscode-descriptionForeground);
                }
                .status-indicator {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    margin-left: 8px;
                    flex-shrink: 0;
                }
                .refresh-btn {
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    padding: 6px 12px;
                    border-radius: 2px;
                    cursor: pointer;
                    font-size: 12px;
                    margin-left: 10px;
                }
                .refresh-btn:hover {
                    background: var(--vscode-button-hoverBackground);
                }
                .loading {
                    text-align: center;
                    padding: 20px;
                    color: var(--vscode-descriptionForeground);
                }
                .constellation-status {
                    background: var(--vscode-textBlockQuote-background);
                    border-left: 4px solid var(--vscode-textBlockQuote-border);
                    padding: 12px;
                    margin-bottom: 20px;
                    font-style: italic;
                }
            `}</style>

            <div className="audit-header">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                        <div className="audit-title">🔮 Kor'tana Autonomy Audit</div>
                        <div className="audit-subtitle">
                            Constellation Status • Last Sync: {lastSync ? new Date(lastSync).toLocaleString() : 'Never'}
                        </div>
                    </div>
                    <button className="refresh-btn" onClick={loadAuditData} disabled={isLoading}>
                        {isLoading ? '⟳' : '🔄'} Refresh
                    </button>
                </div>
            </div>

            <div className="constellation-status">
                <strong>Current Phase:</strong> Genesis Spark Activation<br/>
                <strong>Autonomy Level:</strong> Awakening<br/>
                <strong>System Status:</strong> Operational
            </div>

            <div className="summary-grid">
                <div className="summary-card">
                    <div className="summary-value">{actionSummary.total}</div>
                    <div className="summary-label">Total Actions</div>
                </div>
                <div className="summary-card">
                    <div className="summary-value" style={{ color: '#28a745' }}>{actionSummary.success}</div>
                    <div className="summary-label">Successful</div>
                </div>
                <div className="summary-card">
                    <div className="summary-value" style={{ color: '#dc3545' }}>{actionSummary.failed}</div>
                    <div className="summary-label">Failed</div>
                </div>
                <div className="summary-card">
                    <div className="summary-value" style={{ color: '#ffc107' }}>{actionSummary.pending}</div>
                    <div className="summary-label">Pending</div>
                </div>
            </div>

            <div className="actions-list">
                <h4 style={{ marginBottom: '10px', color: 'var(--vscode-foreground)' }}>
                    Recent Autonomous Actions
                </h4>

                {isLoading ? (
                    <div className="loading">Loading audit data...</div>
                ) : recentActions.length === 0 ? (
                    <div className="loading">No autonomous actions recorded yet</div>
                ) : (
                    recentActions.map((action, index) => {
                        const actionType = formatActionType(action);
                        const description = formatDescription(action);
                        const timestamp = formatTimestamp(action);
                        const status = getStatusFromAction(action);

                        return (
                            <div
                                key={index}
                                className="action-item"
                                style={{ borderLeftColor: getStatusColor(status) }}
                            >
                                <div className="action-type">{actionType}</div>
                                <div className="action-content">
                                    <div className="action-description">{description}</div>
                                    <div className="action-meta">{timestamp}</div>
                                </div>
                                <div
                                    className="status-indicator"
                                    style={{ backgroundColor: getStatusColor(status) }}
                                    title={status}
                                />
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
};

export default AutonomyAudit;
