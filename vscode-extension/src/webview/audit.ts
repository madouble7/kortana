import * as vscode from "vscode";

import { createWebviewDomHelpersScript } from "./dom";
import { createWebviewFormattingHelpersScript } from "./formatting";
import { createEmptyStateBlock, createHeroSection, createTextSpan } from "./fragments";
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
<div class="page-shell">
${createHeroSection({
        description:
            "A live trace of what Kor'tana is doing, what completed cleanly, and where the next intervention point lives.",
        kicker: "Trace Feed",
        signals: [
            {
                label: "Refresh",
                valueHtml: createTextSpan({
                    className: "signal-accent",
                    text: "5s cadence",
                }),
            },
            {
                label: "Scope",
                valueHtml: createTextSpan({
                    className: "signal-accent",
                    text: "Runtime + operator actions",
                }),
            },
        ],
        title: "Kor'tana Audit",
    })}
<section class="audit-log-card">
    <div class="panel-heading audit-heading">
        <h2 class="panel-title">Recent Actions</h2>
        <span class="panel-note">Newest activity appears at the top of the feed.</span>
    </div>
    <div class="audit-log-list" id="audit-log">
        ${createEmptyStateBlock({
        className: "audit-item status-pending",
        detail: "Loading recent actions...",
        title: "Initializing audit system...",
    })}
    </div>
</section>
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
