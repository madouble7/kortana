import * as vscode from "vscode";

const COMMAND_OPEN_AI_STUDIO = "kortana.openAIStudio";
const COMMAND_OPEN_DEPLOY_PAGE = "kortana.openDeployPage";
const COMMAND_UNSEAL_RUNTIME = "kortana.unsealRuntime";
const COMMAND_CHECK_HEALTH = "kortana.checkHealth";
const COMMAND_VIEW_METRICS = "kortana.viewMetrics";
const COMMAND_OPEN_AUTONOMY_AUDIT = "kortana.autonomy.audit.open";

const DASHBOARD_COMMAND_MAP: Record<string, string> = {
    openAIStudio: COMMAND_OPEN_AI_STUDIO,
    openDeployPage: COMMAND_OPEN_DEPLOY_PAGE,
    unsealRuntime: COMMAND_UNSEAL_RUNTIME,
    checkHealth: COMMAND_CHECK_HEALTH,
    viewMetrics: COMMAND_VIEW_METRICS,
    openAutonomyAudit: COMMAND_OPEN_AUTONOMY_AUDIT,
    [COMMAND_OPEN_AI_STUDIO]: COMMAND_OPEN_AI_STUDIO,
    [COMMAND_OPEN_DEPLOY_PAGE]: COMMAND_OPEN_DEPLOY_PAGE,
    [COMMAND_UNSEAL_RUNTIME]: COMMAND_UNSEAL_RUNTIME,
    [COMMAND_CHECK_HEALTH]: COMMAND_CHECK_HEALTH,
    [COMMAND_VIEW_METRICS]: COMMAND_VIEW_METRICS,
    [COMMAND_OPEN_AUTONOMY_AUDIT]: COMMAND_OPEN_AUTONOMY_AUDIT,
};

type DashboardMessage = {
    command?: string;
};

export function resolveDashboardCommand(
    message: DashboardMessage
): string | undefined {
    const candidate = message.command?.trim();

    if (!candidate) {
        return undefined;
    }

    return DASHBOARD_COMMAND_MAP[candidate];
}

async function handleDashboardMessage(message: DashboardMessage): Promise<void> {
    const command = resolveDashboardCommand(message);

    if (!command) {
        vscode.window.showWarningMessage(
            `Kor'tana received an unknown dashboard action: ${message.command ?? "<missing>"}`
        );
        return;
    }

    await vscode.commands.executeCommand(command);
}

export function activate(context: vscode.ExtensionContext) {
    console.log("Kor'tana VS Code Extension activated");

    // Command: Open AI Studio
    context.subscriptions.push(
        vscode.commands.registerCommand(COMMAND_OPEN_AI_STUDIO, async () => {
            const aiStudioUrl =
                "https://aistudio.google.com/app/prompts/create/1T7Nh4cq1IwCwhHq5u8ZETDb6fY4qVkH3";

            const panel = vscode.window.createWebviewPanel(
                "kortanaAIStudio",
                "Kor'tana AI Studio",
                vscode.ViewColumn.One,
                {
                    enableScripts: true,
                    enableCommandUris: true,
                }
            );

            panel.webview.html = getWebviewContent(aiStudioUrl);
        })
    );

    // Command: Open Deploy Page
    context.subscriptions.push(
        vscode.commands.registerCommand(COMMAND_OPEN_DEPLOY_PAGE, async () => {
            const deployUrl =
                "https://kor-tana-780422883904.us-west1.run.app";

            const panel = vscode.window.createWebviewPanel(
                "kortanaDeployPage",
                "Kor'tana Deploy Page",
                vscode.ViewColumn.One,
                {
                    enableScripts: true,
                    enableCommandUris: true,
                }
            );

            panel.webview.html = getWebviewContent(deployUrl);
        })
    );

    // Command: Unseal Runtime
    context.subscriptions.push(
        vscode.commands.registerCommand(COMMAND_UNSEAL_RUNTIME, async () => {
            vscode.window.showInformationMessage(
                "Unsealing Kor'tana runtime..."
            );

            try {
                const { execSync } = require("child_process");
                const result = execSync(
                    "node scripts/unseal-kortana.js",
                    { encoding: "utf-8" }
                );

                vscode.window.showInformationMessage(
                    "✓ Runtime unsealed successfully!"
                );
                console.log(result);
            } catch (error) {
                vscode.window.showErrorMessage(
                    `Failed to unseal runtime: ${error}`
                );
            }
        })
    );

    // Command: Check Health
    context.subscriptions.push(
        vscode.commands.registerCommand(COMMAND_CHECK_HEALTH, async () => {
            try {
                const axios = require("axios");
                const response = await axios.get(
                    "http://localhost:8000/api/health"
                );

                if (response.status === 200) {
                    vscode.window.showInformationMessage(
                        `✓ Backend is alive: ${response.data.message}`
                    );
                }
            } catch (error) {
                vscode.window.showWarningMessage(
                    "Backend is offline. Start it with: cd backend && python -m uvicorn src.kortana.main:app --reload"
                );
            }
        })
    );

    // Command: Open Autonomy Audit
    context.subscriptions.push(
        vscode.commands.registerCommand(COMMAND_OPEN_AUTONOMY_AUDIT, async () => {
            const panel = vscode.window.createWebviewPanel(
                "kortanaAutonomyAudit",
                "Kor'tana Autonomy Audit",
                vscode.ViewColumn.Two,
                {
                    enableScripts: true,
                    localResourceRoots: [
                        vscode.Uri.joinPath(context.extensionUri, 'media'),
                        vscode.Uri.joinPath(context.extensionUri, 'out')
                    ]
                }
            );

            // Get the autonomy audit HTML content
            panel.webview.html = await getAutonomyAuditContent(context, panel.webview);
        })
    );

    // Register WebView provider for the dashboard
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('kortana-dashboard', {
            resolveWebviewView(webviewView) {
                webviewView.webview.options = {
                    enableScripts: true,
                    localResourceRoots: [
                        vscode.Uri.joinPath(context.extensionUri, 'media'),
                        vscode.Uri.joinPath(context.extensionUri, 'out')
                    ]
                };

                webviewView.webview.onDidReceiveMessage(async (message: DashboardMessage) => {
                    try {
                        await handleDashboardMessage(message);
                    } catch (error) {
                        const detail = error instanceof Error ? error.message : String(error);
                        vscode.window.showErrorMessage(
                            `Kor'tana dashboard action failed: ${detail}`
                        );
                    }
                });

                webviewView.webview.html = getDashboardContent();
            }
        })
    );

    // Command: View Metrics
    context.subscriptions.push(
        vscode.commands.registerCommand(COMMAND_VIEW_METRICS, async () => {
            const panel = vscode.window.createWebviewPanel(
                "kortanaMetrics",
                "Kor'tana Metrics",
                vscode.ViewColumn.Two,
                { enableScripts: true }
            );

            panel.webview.html = `
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial; padding: 20px; color: #eee; background: #1e1e1e; }
        h1 { color: #00ff00; }
        .metric { margin: 10px 0; padding: 10px; background: #333; border-left: 3px solid #00ff00; }
        .status-alive { color: #00ff00; }
        .status-offline { color: #ff0000; }
    </style>
</head>
<body>
    <h1>🌌 Kor'tana Autonomy Metrics</h1>
    <div class="metric">
        <strong>Backend Status:</strong> <span class="status-alive">Checking...</span>
    </div>
    <div class="metric">
        <strong>Last Deployment:</strong> <span id="deploy-time">Loading...</span>
    </div>
    <div class="metric">
        <strong>Tasks Completed:</strong> <span id="tasks-count">Loading...</span>
    </div>
    <script>
        // Load metrics from backend
        fetch('http://localhost:8000/api/metrics/dashboard')
            .then(r => r.json())
            .then(data => {
                document.getElementById('deploy-time').textContent = data.last_deployment || 'N/A';
                document.getElementById('tasks-count').textContent = data.completed_tasks || 0;
            })
            .catch(() => {
                document.querySelector('.status-alive').textContent = 'Offline';
                document.querySelector('.status-alive').className = 'status-offline';
            });
    </script>
</body>
</html>
            `;
        })
    );

    vscode.window.showInformationMessage(
        "Kor'tana is online. Use Ctrl+Shift+A for AI Studio, Ctrl+Shift+D for Deploy."
    );
}

async function getAutonomyAuditContent(context: vscode.ExtensionContext, webview: vscode.Webview): Promise<string> {
    // For now, return a simple audit interface
    // In a real implementation, this would load the AutonomyAudit React component
    return `
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: var(--vscode-font-family); padding: 20px; color: var(--vscode-foreground); background: var(--vscode-editor-background); }
        h1 { color: var(--vscode-textLink-foreground); }
        .audit-item { margin: 10px 0; padding: 10px; background: var(--vscode-list-inactiveSelectionBackground); border-radius: 4px; }
        .status-success { border-left: 3px solid #28a745; }
        .status-failed { border-left: 3px solid #dc3545; }
        .status-pending { border-left: 3px solid #ffc107; }
    </style>
</head>
<body>
    <h1>🔮 Kor'tana Autonomy Audit</h1>
    <p>Real-time monitoring of autonomous operations...</p>
    <div id="audit-log">
        <div class="audit-item status-pending">
            <strong>Initializing audit system...</strong><br/>
            <small>Loading recent actions...</small>
        </div>
    </div>
    <script>
        // Simple polling for audit data
        setInterval(async () => {
            try {
                const response = await fetch('http://localhost:8000/api/autonomy/actions');
                const actions = await response.json();
                const logDiv = document.getElementById('audit-log');
                logDiv.innerHTML = actions.map(action =>
                    \`<div class="audit-item status-\${action.status}">
                        <strong>\${action.type}: \${action.description}</strong><br/>
                        <small>\${new Date(action.timestamp).toLocaleString()}</small>
                    </div>\`
                ).join('');
            } catch (e) {
                // Backend not available
            }
        }, 5000);
    </script>
</body>
</html>
    `;
}

function getDashboardContent(): string {
    return `
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: var(--vscode-font-family); padding: 15px; color: var(--vscode-foreground); background: var(--vscode-editor-background); }
        .dashboard-card { margin: 10px 0; padding: 15px; background: var(--vscode-editorWidget-background); border: 1px solid var(--vscode-panel-border); border-radius: 4px; }
        .status-indicator { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; }
        .status-alive { background: #28a745; }
        .status-offline { background: #dc3545; }
        button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 6px 12px; border-radius: 2px; cursor: pointer; margin: 2px; }
        button:hover { background: var(--vscode-button-hoverBackground); }
    </style>
</head>
<body>
    <h3>Kor'tana Control Panel</h3>

    <div class="dashboard-card">
        <h4>System Status</h4>
        <p><span class="status-indicator status-alive"></span>Extension Active</p>
        <p>
            <span class="status-indicator" id="backend-status-indicator" style="background: #ffc107;"></span>
            <span id="backend-status-text">Backend: Checking...</span>
        </p>
    </div>

    <div class="dashboard-card">
        <h4>Quick Actions</h4>
        <button onclick="openAIStudio()">🧠 AI Studio</button>
        <button onclick="openDeployPage()">🚀 Deploy Page</button>
        <button onclick="checkHealth()">💚 Health Check</button>
        <button onclick="unsealRuntime()">🔓 Unseal Runtime</button>
        <button onclick="viewMetrics()">📊 Metrics</button>
        <button onclick="openAutonomyAudit()">🔮 Audit</button>
    </div>

    <div class="dashboard-card">
        <h4>Autonomy Metrics</h4>
        <p>Tasks Processed: <span id="tasks-count">-</span></p>
        <p>Last Sync: <span id="last-sync">-</span></p>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        function openAIStudio() {
            vscode.postMessage({ command: 'openAIStudio' });
        }

        function openDeployPage() {
            vscode.postMessage({ command: 'openDeployPage' });
        }

        function checkHealth() {
            vscode.postMessage({ command: 'checkHealth' });
        }

        function unsealRuntime() {
            vscode.postMessage({ command: 'unsealRuntime' });
        }

        function viewMetrics() {
            vscode.postMessage({ command: 'viewMetrics' });
        }

        function openAutonomyAudit() {
            vscode.postMessage({ command: 'openAutonomyAudit' });
        }

        // Check backend status periodically
        async function checkBackend() {
            const indicator = document.getElementById('backend-status-indicator');
            const text = document.getElementById('backend-status-text');

            try {
                const response = await fetch('http://localhost:8000/api/health');
                if (response.ok) {
                    indicator.style.background = '#28a745';
                    text.textContent = 'Backend: Online';
                } else {
                    throw new Error();
                }
            } catch (e) {
                indicator.style.background = '#dc3545';
                text.textContent = 'Backend: Offline';
            }
        }

        checkBackend();
        setInterval(checkBackend, 10000);
    </script>
</body>
</html>
    `;
}

function getWebviewContent(url: string): string {
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kor'tana</title>
    <style>
        body { margin: 0; padding: 0; overflow: hidden; }
        iframe { width: 100%; height: 100vh; border: none; }
    </style>
</head>
<body>
    <iframe src="${url}" allow="camera *; microphone *; geolocation *; clipboard-write *;"></iframe>
</body>
</html>
    `;
}

export function deactivate() {
    console.log("Kor'tana VS Code Extension deactivated");
}

