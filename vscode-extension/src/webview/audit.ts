import * as vscode from "vscode";

import { createNonce, renderHtmlDocument } from "./html";
import {
    createRequestMessage,
    REQUEST_AUDIT_LOG,
    RESPONSE_AUDIT_LOG,
} from "./messages";

export function getAutonomyAuditContent(webview: vscode.Webview): string {
    const nonce = createNonce();

    return renderHtmlDocument({
        body: getAuditBody(),
        nonce,
        script: getAuditScript(),
        title: "Kor'tana Autonomy Audit",
        webview,
    });
}

function getAuditBody(): string {
    return `
<style>
    body { font-family: var(--vscode-font-family); padding: 20px; color: var(--vscode-foreground); background: var(--vscode-editor-background); }
    h1 { color: var(--vscode-textLink-foreground); }
    .audit-item { margin: 10px 0; padding: 10px; background: var(--vscode-list-inactiveSelectionBackground); border-radius: 4px; }
    .status-success { border-left: 3px solid #28a745; }
    .status-failed { border-left: 3px solid #dc3545; }
    .status-pending { border-left: 3px solid #ffc107; }
</style>
<h1>Kor'tana Autonomy Audit</h1>
<p>Real-time monitoring of autonomous operations...</p>
<div id="audit-log">
    <div class="audit-item status-pending">
        <strong>Initializing audit system...</strong><br />
        <small>Loading recent actions...</small>
    </div>
</div>
    `;
}

function getAuditScript(): string {
    const requestAuditLogMessage = JSON.stringify(
        createRequestMessage(REQUEST_AUDIT_LOG)
    );

    return `
const vscodeApi = acquireVsCodeApi();

function requestAuditLog() {
    vscodeApi.postMessage(${requestAuditLogMessage});
}

function formatTimestamp(value) {
    if (!value) {
        return "";
    }

    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString();
}

function renderAuditLog(actions) {
    const log = document.getElementById("audit-log");
    log.replaceChildren();

    if (!actions.length) {
        const empty = document.createElement("div");
        empty.className = "audit-item status-pending";
        const strong = document.createElement("strong");
        strong.textContent = "No audit actions available";
        empty.appendChild(strong);
        log.appendChild(empty);
        return;
    }

    for (const action of actions) {
        const item = document.createElement("div");
        item.className = "audit-item status-" + action.status;

        const title = document.createElement("strong");
        title.textContent = action.type + ": " + action.description;
        item.appendChild(title);
        item.appendChild(document.createElement("br"));

        const timestamp = document.createElement("small");
        timestamp.textContent = formatTimestamp(action.timestamp);
        item.appendChild(timestamp);

        log.appendChild(item);
    }
}

window.addEventListener("message", (event) => {
    const message = event.data;
    if (message.type === "${RESPONSE_AUDIT_LOG}") {
        renderAuditLog(message.payload);
    }
});

requestAuditLog();
setInterval(requestAuditLog, 5000);
    `;
}
