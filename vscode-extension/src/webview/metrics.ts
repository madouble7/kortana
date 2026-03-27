import * as vscode from "vscode";

import { createNonce, renderHtmlDocument } from "./html";
import {
    createRequestMessage,
    REQUEST_METRICS_STATE,
    RESPONSE_METRICS_STATE,
} from "./messages";

export function getMetricsContent(webview: vscode.Webview): string {
    const nonce = createNonce();

    return renderHtmlDocument({
        body: getMetricsBody(),
        nonce,
        script: getMetricsScript(),
        title: "Kor'tana Metrics",
        webview,
    });
}

function getMetricsBody(): string {
    return `
<style>
    body { font-family: var(--vscode-font-family); padding: 20px; color: var(--vscode-foreground); background: var(--vscode-editor-background); }
    h1 { color: var(--vscode-textLink-foreground); }
    .metric { margin: 10px 0; padding: 10px; background: var(--vscode-editorWidget-background); border-left: 3px solid var(--vscode-textLink-foreground); }
    .status-alive { color: #28a745; }
    .status-offline { color: #dc3545; }
</style>
<h1>Kor'tana Autonomy Metrics</h1>
<div class="metric">
    <strong>Backend Status:</strong> <span id="backend-status" class="status-offline">Checking...</span>
</div>
<div class="metric">
    <strong>Last Deployment:</strong> <span id="deploy-time">Loading...</span>
</div>
<div class="metric">
    <strong>Tasks Completed:</strong> <span id="tasks-count">Loading...</span>
</div>
    `;
}

function getMetricsScript(): string {
    const requestMetricsStateMessage = JSON.stringify(
        createRequestMessage(REQUEST_METRICS_STATE)
    );

    return `
const vscodeApi = acquireVsCodeApi();

function requestMetricsState() {
    vscodeApi.postMessage(${requestMetricsStateMessage});
}

function updateMetricsState(payload) {
    const backendStatus = document.getElementById("backend-status");
    backendStatus.textContent = payload.backendOnline ? payload.backendMessage : "Offline";
    backendStatus.className = payload.backendOnline ? "status-alive" : "status-offline";
    document.getElementById("deploy-time").textContent = payload.lastDeployment;
    document.getElementById("tasks-count").textContent = payload.tasksCount;
}

window.addEventListener("message", (event) => {
    const message = event.data;
    if (message.type === "${RESPONSE_METRICS_STATE}") {
        updateMetricsState(message.payload);
    }
});

requestMetricsState();
setInterval(requestMetricsState, 15000);
    `;
}
