import * as vscode from "vscode";

import { createWebviewDomHelpersScript } from "./dom";
import { createNonce, renderHtmlDocument } from "./html";
import {
    createRequestMessage,
    REQUEST_METRICS_STATE,
    RESPONSE_METRICS_STATE,
} from "./messages";
import { createWebviewRuntimeScript } from "./runtime";

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
    return `
${createWebviewDomHelpersScript()}
function updateMetricsState(payload) {
    setElementText(
        "backend-status",
        payload.backendOnline ? payload.backendMessage : "Offline"
    );
    setElementClassName(
        "backend-status",
        payload.backendOnline ? "status-alive" : "status-offline"
    );
    setElementText("deploy-time", payload.lastDeployment);
    setElementText("tasks-count", payload.tasksCount);
}
${createWebviewRuntimeScript({
        requestPollers: [
            {
                functionName: "requestMetricsState",
                message: createRequestMessage(REQUEST_METRICS_STATE),
                intervalMs: 15000,
                invokeImmediately: true,
            },
        ],
        responseBindings: [
            {
                type: RESPONSE_METRICS_STATE,
                handlerName: "updateMetricsState",
            },
        ],
    })}
    `;
}
