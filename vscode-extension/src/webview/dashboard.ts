import * as vscode from "vscode";

import { createNonce, renderHtmlDocument } from "./html";
import { REQUEST_DASHBOARD_STATE } from "./messages";

export function getDashboardContent(webview: vscode.Webview): string {
    const nonce = createNonce();

    return renderHtmlDocument({
        body: getDashboardBody(),
        nonce,
        script: getDashboardScript(),
        title: "Kor'tana Control Panel",
        webview,
    });
}

function getDashboardBody(): string {
    return `
<style>
    body { font-family: var(--vscode-font-family); padding: 15px; color: var(--vscode-foreground); background: var(--vscode-editor-background); }
    .dashboard-card { margin: 10px 0; padding: 15px; background: var(--vscode-editorWidget-background); border: 1px solid var(--vscode-panel-border); border-radius: 4px; }
    .status-indicator { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; }
    .status-alive { background: #28a745; }
    .status-offline { background: #dc3545; }
    button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 6px 12px; border-radius: 2px; cursor: pointer; margin: 2px; }
    button:hover { background: var(--vscode-button-hoverBackground); }
</style>
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
    <button id="action-ai-studio">AI Studio</button>
    <button id="action-deploy-page">Deploy Page</button>
    <button id="action-health-check">Health Check</button>
    <button id="action-unseal-runtime">Unseal Runtime</button>
    <button id="action-metrics">Metrics</button>
    <button id="action-audit">Audit</button>
</div>

<div class="dashboard-card">
    <h4>Autonomy Metrics</h4>
    <p>Tasks Processed: <span id="tasks-count">-</span></p>
    <p>Last Sync: <span id="last-sync">-</span></p>
</div>
    `;
}

function getDashboardScript(): string {
    return `
const vscodeApi = acquireVsCodeApi();

function postCommand(command) {
    vscodeApi.postMessage({ command });
}

function requestDashboardState() {
    vscodeApi.postMessage({ type: "${REQUEST_DASHBOARD_STATE}" });
}

function updateDashboardState(payload) {
    const indicator = document.getElementById("backend-status-indicator");
    const text = document.getElementById("backend-status-text");
    const tasksCount = document.getElementById("tasks-count");
    const lastSync = document.getElementById("last-sync");

    indicator.style.background = payload.backendOnline ? "#28a745" : "#dc3545";
    text.textContent = payload.backendOnline ? "Backend: " + payload.backendMessage : "Backend: Offline";
    tasksCount.textContent = payload.tasksCount;
    lastSync.textContent = payload.lastSync;
}

window.addEventListener("message", (event) => {
    const message = event.data;
    if (message.type === "dashboardState") {
        updateDashboardState(message.payload);
    }
});

document.getElementById("action-ai-studio").addEventListener("click", () => postCommand("openAIStudio"));
document.getElementById("action-deploy-page").addEventListener("click", () => postCommand("openDeployPage"));
document.getElementById("action-health-check").addEventListener("click", () => postCommand("checkHealth"));
document.getElementById("action-unseal-runtime").addEventListener("click", () => postCommand("unsealRuntime"));
document.getElementById("action-metrics").addEventListener("click", () => postCommand("viewMetrics"));
document.getElementById("action-audit").addEventListener("click", () => postCommand("openAutonomyAudit"));

requestDashboardState();
setInterval(requestDashboardState, 10000);
    `;
}
