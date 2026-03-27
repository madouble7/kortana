import * as vscode from "vscode";

import { createWebviewDomHelpersScript } from "./dom";
import { createWebviewFormattingHelpersScript } from "./formatting";
import { createEmptyStateBlock } from "./fragments";
import { createNonce, renderHtmlDocument } from "./html";
import {
    createRequestMessage,
    REQUEST_AUDIT_LOG,
    RESPONSE_AUDIT_LOG,
} from "./messages";
import { createWebviewRuntimeScript } from "./runtime";

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
    ${createEmptyStateBlock({
        className: "audit-item status-pending",
        detail: "Loading recent actions...",
        title: "Initializing audit system...",
    })}
</div>
    `;
}

function getAuditScript(): string {
    return `
${createWebviewDomHelpersScript()}
${createWebviewFormattingHelpersScript()}

function renderAuditLog(actions) {
    renderAuditActionList("audit-log", actions);
}
${createWebviewRuntimeScript({
        requestPollers: [
            {
                functionName: "requestAuditLog",
                message: createRequestMessage(REQUEST_AUDIT_LOG),
                intervalMs: 5000,
                invokeImmediately: true,
            },
        ],
        responseBindings: [
            {
                type: RESPONSE_AUDIT_LOG,
                handlerName: "renderAuditLog",
            },
        ],
    })}
    `;
}
