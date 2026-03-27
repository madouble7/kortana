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
            indicatorStyle: `background: ${STATUS_PENDING_COLOR};`,
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
