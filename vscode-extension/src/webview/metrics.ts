import * as vscode from "vscode";

import { createWebviewDomHelpersScript } from "./dom";
import { createWebviewFormattingHelpersScript } from "./formatting";
import { createHeroSection, createMetricCard, createTextSpan } from "./fragments";
import { createNonce, renderHtmlDocument } from "./html";
import {
    createRequestMessage,
    REQUEST_METRICS_STATE,
    RESPONSE_METRICS_STATE,
} from "./messages";
import { createWebviewRuntimeScript } from "./runtime";
import { createMetricsStyles } from "./styles";

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
${createMetricsStyles()}
<div class="page-shell">
${createHeroSection({
        description:
            "A tighter read on runtime heartbeat, delivery velocity, and recent deployment cadence.",
        kicker: "Telemetry Feed",
        signals: [
            {
                label: "Link",
                valueHtml: createTextSpan({
                    className: "signal-accent",
                    text: "Host-mediated telemetry",
                }),
            },
            {
                label: "Cadence",
                valueHtml: createTextSpan({
                    className: "signal-accent",
                    text: "15s refresh",
                }),
            },
        ],
        title: "Kor'tana Metrics",
    })}
<div class="metric-grid">
${createMetricCard({
        label: "Backend Status:",
        valueHtml: createTextSpan({
            className: "status-offline",
            id: "backend-status",
            text: "Checking...",
        }),
    })}
${createMetricCard({
        label: "Last Deployment:",
        valueHtml: createTextSpan({ id: "deploy-time", text: "Loading..." }),
    })}
${createMetricCard({
        label: "Tasks Completed:",
        valueHtml: createTextSpan({
            className: "mono-value",
            id: "tasks-count",
            text: "Loading...",
        }),
    })}
${createMetricCard({
        label: "Signal Path:",
        valueHtml: createTextSpan({
            className: "signal-accent",
            text: "Daemon -> runtime -> webview",
        }),
    })}
</div>
</div>
    `;
}

function getMetricsScript(): string {
    return `
${createWebviewDomHelpersScript()}
${createWebviewFormattingHelpersScript()}
function updateMetricsState(payload) {
    applyStatusText(
        "backend-status",
        payload.backendOnline,
        payload.backendMessage
    );
    applyStatusClassName("backend-status", payload.backendOnline);
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
