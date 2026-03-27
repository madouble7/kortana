import * as vscode from "vscode";

import { createWebviewDomHelpersScript } from "./dom";
import { createWebviewFormattingHelpersScript } from "./formatting";
import {
    createButtonGroup,
    createLabeledValueRow,
    createPanel,
    createStatusLine,
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

${createPanel({
        body: `
    ${createStatusLine({
            contentHtml: "Extension Active",
            indicatorClassName: "status-indicator status-alive",
        })}
    ${createStatusLine({
            contentHtml: createTextSpan({
                id: "backend-status-text",
                text: "Backend: Checking...",
            }),
            indicatorId: "backend-status-indicator",
            indicatorStyle: "background: #ffc107;",
        })}
        `,
        className: "dashboard-card",
        title: "System Status",
    })}

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
        title: "Quick Actions",
    })}

${createPanel({
        body: `
    ${createLabeledValueRow({
            label: "Tasks Processed:",
            valueHtml: createTextSpan({ id: "tasks-count", text: "-" }),
        })}
    ${createLabeledValueRow({
            label: "Last Sync:",
            valueHtml: createTextSpan({ id: "last-sync", text: "-" }),
        })}
        `,
        className: "dashboard-card",
        title: "Autonomy Metrics",
    })}
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
