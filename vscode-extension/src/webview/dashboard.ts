import * as vscode from "vscode";

import { createWebviewDomHelpersScript } from "./dom";
import { createNonce, renderHtmlDocument } from "./html";
import {
    createCommandMessage,
    createRequestMessage,
    REQUEST_DASHBOARD_STATE,
    RESPONSE_DASHBOARD_STATE,
} from "./messages";
import { createWebviewRuntimeScript } from "./runtime";

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
${createWebviewDomHelpersScript()}
function updateDashboardState(payload) {
    setElementStyle(
        "backend-status-indicator",
        "background",
        payload.backendOnline ? "#28a745" : "#dc3545"
    );
    setElementText(
        "backend-status-text",
        payload.backendOnline
            ? "Backend: " + payload.backendMessage
            : "Backend: Offline"
    );
    setElementText("tasks-count", payload.tasksCount);
    setElementText("last-sync", payload.lastSync);
}
${createWebviewRuntimeScript({
        commandBindings: [
            {
                elementId: "action-ai-studio",
                message: createCommandMessage("openAIStudio"),
            },
            {
                elementId: "action-deploy-page",
                message: createCommandMessage("openDeployPage"),
            },
            {
                elementId: "action-health-check",
                message: createCommandMessage("checkHealth"),
            },
            {
                elementId: "action-unseal-runtime",
                message: createCommandMessage("unsealRuntime"),
            },
            {
                elementId: "action-metrics",
                message: createCommandMessage("viewMetrics"),
            },
            {
                elementId: "action-audit",
                message: createCommandMessage("openAutonomyAudit"),
            },
        ],
        requestPollers: [
            {
                functionName: "requestDashboardState",
                message: createRequestMessage(REQUEST_DASHBOARD_STATE),
                intervalMs: 10000,
                invokeImmediately: true,
            },
        ],
        responseBindings: [
            {
                type: RESPONSE_DASHBOARD_STATE,
                handlerName: "updateDashboardState",
            },
        ],
    })}
    `;
}
