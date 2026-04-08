import * as vscode from "vscode";

import { createWebviewDomHelpersScript } from "./dom";
import { createWebviewFormattingHelpersScript } from "./formatting";
import {
    createButtonGroup,
    createHeroSection,
    createLabeledValueRow,
    createPanel,
    createTextSpan,
} from "./fragments";
import { createNonce, renderHtmlDocument } from "./html";
import {
    createCommandMessage,
    createRequestMessage,
    REQUEST_DASHBOARD_STATE,
    RESPONSE_DASHBOARD_STATE,
} from "./messages";
import { createWebviewRuntimeScript } from "./runtime";
import { createDashboardStyles, STATUS_PENDING_COLOR } from "./styles";

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
${createDashboardStyles()}
<div class="page-shell">
${createHeroSection({
        description:
            "Steer the live runtime, inspect the machine state, and jump into the highest-signal actions without leaving the editor.",
        kicker: "Always-On Companion",
        signals: [
            {
                label: "Runtime",
                valueHtml: `<span class="signal-inline"><span class="status-indicator" id="backend-status-indicator" style="background: ${STATUS_PENDING_COLOR};"></span>${createTextSpan({
                    id: "backend-status-text",
                    text: "Backend: Checking...",
                })}</span>`,
            },
            {
                label: "Steering",
                valueHtml: createTextSpan({
                    className: "signal-accent",
                    text: "Live + local-first",
                }),
            },
            {
                label: "Operator",
                valueHtml: createTextSpan({
                    className: "signal-accent",
                    text: "Override ready",
                }),
            },
        ],
        title: "Kor'tana Control Deck",
    })}

<div class="panel-grid two-up">
${createPanel({
        body: createButtonGroup([
            { id: "action-ai-studio", label: "AI Studio" },
            { id: "action-deploy-page", label: "Deploy Page" },
            { id: "action-health-check", label: "Health Check" },
            { id: "action-unseal-runtime", label: "Unseal Runtime" },
            { id: "action-metrics", label: "Metrics" },
            { id: "action-audit", label: "Audit" },
        ]),
        className: "dashboard-card",
        title: "Launch Surfaces",
    })}

${createPanel({
        body: `
    <div class="data-stack">
        ${createLabeledValueRow({
            label: "Tasks Processed",
            valueHtml: createTextSpan({
                className: "mono-value",
                id: "tasks-count",
                text: "-",
            }),
        })}
        ${createLabeledValueRow({
            label: "Last Sync",
            valueHtml: createTextSpan({
                className: "mono-value",
                id: "last-sync",
                text: "-",
            }),
        })}
    </div>
        `,
        className: "dashboard-card",
        title: "Runtime Pulse",
    })}
</div>
</div>
    `;
}

function getDashboardScript(): string {
    return `
${createWebviewDomHelpersScript()}
${createWebviewFormattingHelpersScript()}
function updateDashboardState(payload) {
    applyStatusIndicatorColor("backend-status-indicator", payload.backendOnline);
    applyStatusText(
        "backend-status-text",
        payload.backendOnline,
        payload.backendMessage,
        "Offline",
        "Backend: "
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
