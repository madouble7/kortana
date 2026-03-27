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
import { createAuditStyles } from "./styles";

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
${createAuditStyles()}
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
