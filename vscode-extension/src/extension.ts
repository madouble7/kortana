import { execSync } from "child_process";
import { randomBytes } from "crypto";

import axios from "axios";
import * as vscode from "vscode";

const BACKEND_BASE_URL = "http://localhost:8000";

const COMMAND_OPEN_AI_STUDIO = "kortana.openAIStudio";
const COMMAND_OPEN_DEPLOY_PAGE = "kortana.openDeployPage";
const COMMAND_UNSEAL_RUNTIME = "kortana.unsealRuntime";
const COMMAND_CHECK_HEALTH = "kortana.checkHealth";
const COMMAND_VIEW_METRICS = "kortana.viewMetrics";
const COMMAND_OPEN_AUTONOMY_AUDIT = "kortana.autonomy.audit.open";

const REQUEST_DASHBOARD_STATE = "requestDashboardState";
const REQUEST_METRICS_STATE = "requestMetricsState";
const REQUEST_AUDIT_LOG = "requestAuditLog";

const DASHBOARD_COMMAND_MAP: Record<string, string> = {
    openAIStudio: COMMAND_OPEN_AI_STUDIO,
    openDeployPage: COMMAND_OPEN_DEPLOY_PAGE,
    unsealRuntime: COMMAND_UNSEAL_RUNTIME,
    checkHealth: COMMAND_CHECK_HEALTH,
    viewMetrics: COMMAND_VIEW_METRICS,
    openAutonomyAudit: COMMAND_OPEN_AUTONOMY_AUDIT,
    [COMMAND_OPEN_AI_STUDIO]: COMMAND_OPEN_AI_STUDIO,
    [COMMAND_OPEN_DEPLOY_PAGE]: COMMAND_OPEN_DEPLOY_PAGE,
    [COMMAND_UNSEAL_RUNTIME]: COMMAND_UNSEAL_RUNTIME,
    [COMMAND_CHECK_HEALTH]: COMMAND_CHECK_HEALTH,
    [COMMAND_VIEW_METRICS]: COMMAND_VIEW_METRICS,
    [COMMAND_OPEN_AUTONOMY_AUDIT]: COMMAND_OPEN_AUTONOMY_AUDIT,
};

type WebviewMessage = {
    command?: string;
    type?: string;
};

type ResolvedWebviewMessage =
    | { kind: "command"; command: string }
    | { kind: "dashboardState" }
    | { kind: "metricsState" }
    | { kind: "auditLog" };

type BackendHealthResponse = {
    message?: unknown;
};

type MetricsDashboardResponse = {
    completed_tasks?: unknown;
    tasks_processed?: unknown;
    last_deployment?: unknown;
    last_sync?: unknown;
};

type DashboardStatePayload = {
    backendOnline: boolean;
    backendMessage: string;
    tasksCount: string;
    lastSync: string;
};

type MetricsStatePayload = {
    backendOnline: boolean;
    backendMessage: string;
    lastDeployment: string;
    tasksCount: string;
};

type AuditAction = {
    type: string;
    description: string;
    timestamp: string;
    status: string;
};

type HtmlDocumentOptions = {
    body: string;
    nonce?: string;
    script?: string;
    title: string;
    webview: vscode.Webview;
    frameSources?: string[];
};

export function resolveDashboardCommand(
    message: WebviewMessage
): string | undefined {
    const candidate = message.command?.trim();

    if (!candidate) {
        return undefined;
    }

    return DASHBOARD_COMMAND_MAP[candidate];
}

export function resolveWebviewMessage(
    message: WebviewMessage
): ResolvedWebviewMessage | undefined {
    const type = message.type?.trim();

    if (type === REQUEST_DASHBOARD_STATE) {
        return { kind: "dashboardState" };
    }

    if (type === REQUEST_METRICS_STATE) {
        return { kind: "metricsState" };
    }

    if (type === REQUEST_AUDIT_LOG) {
        return { kind: "auditLog" };
    }

    const command = resolveDashboardCommand(message);
    if (!command) {
        return undefined;
    }

    return { kind: "command", command };
}

export function activate(context: vscode.ExtensionContext) {
    console.log("Kor'tana VS Code Extension activated");

    context.subscriptions.push(
        vscode.commands.registerCommand(COMMAND_OPEN_AI_STUDIO, async () => {
            const aiStudioUrl =
                "https://aistudio.google.com/app/prompts/create/1T7Nh4cq1IwCwhHq5u8ZETDb6fY4qVkH3";

            const panel = vscode.window.createWebviewPanel(
                "kortanaAIStudio",
                "Kor'tana AI Studio",
                vscode.ViewColumn.One,
                {
                    enableScripts: false,
                }
            );

            panel.webview.html = getFrameWebviewContent(
                panel.webview,
                aiStudioUrl,
                "Kor'tana AI Studio"
            );
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand(COMMAND_OPEN_DEPLOY_PAGE, async () => {
            const deployUrl =
                "https://kor-tana-780422883904.us-west1.run.app";

            const panel = vscode.window.createWebviewPanel(
                "kortanaDeployPage",
                "Kor'tana Deploy Page",
                vscode.ViewColumn.One,
                {
                    enableScripts: false,
                }
            );

            panel.webview.html = getFrameWebviewContent(
                panel.webview,
                deployUrl,
                "Kor'tana Deploy Page"
            );
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand(COMMAND_UNSEAL_RUNTIME, async () => {
            vscode.window.showInformationMessage(
                "Unsealing Kor'tana runtime..."
            );

            try {
                const result = execSync("node scripts/unseal-kortana.js", {
                    encoding: "utf-8",
                });

                vscode.window.showInformationMessage(
                    "✓ Runtime unsealed successfully!"
                );
                console.log(result);
            } catch (error) {
                vscode.window.showErrorMessage(
                    `Failed to unseal runtime: ${error}`
                );
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand(COMMAND_CHECK_HEALTH, async () => {
            const state = await getDashboardStatePayload();

            if (state.backendOnline) {
                vscode.window.showInformationMessage(
                    `✓ Backend is alive: ${state.backendMessage}`
                );
                return;
            }

            vscode.window.showWarningMessage(
                "Backend is offline. Start it with: cd backend && python -m uvicorn src.kortana.main:app --reload"
            );
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand(COMMAND_OPEN_AUTONOMY_AUDIT, async () => {
            const panel = vscode.window.createWebviewPanel(
                "kortanaAutonomyAudit",
                "Kor'tana Autonomy Audit",
                vscode.ViewColumn.Two,
                {
                    enableScripts: true,
                    localResourceRoots: getLocalResourceRoots(context),
                }
            );

            registerWebviewMessageHandler(panel.webview);
            panel.webview.html = getAutonomyAuditContent(panel.webview);
        })
    );

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider("kortana-dashboard", {
            resolveWebviewView(webviewView) {
                webviewView.webview.options = {
                    enableScripts: true,
                    localResourceRoots: getLocalResourceRoots(context),
                };

                registerWebviewMessageHandler(webviewView.webview);
                webviewView.webview.html = getDashboardContent(
                    webviewView.webview
                );
            },
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand(COMMAND_VIEW_METRICS, async () => {
            const panel = vscode.window.createWebviewPanel(
                "kortanaMetrics",
                "Kor'tana Metrics",
                vscode.ViewColumn.Two,
                {
                    enableScripts: true,
                }
            );

            registerWebviewMessageHandler(panel.webview);
            panel.webview.html = getMetricsContent(panel.webview);
        })
    );

    vscode.window.showInformationMessage(
        "Kor'tana is online. Use Ctrl+Shift+A for AI Studio, Ctrl+Shift+D for Deploy."
    );
}

function getLocalResourceRoots(
    context: vscode.ExtensionContext
): vscode.Uri[] {
    return [
        vscode.Uri.joinPath(context.extensionUri, "media"),
        vscode.Uri.joinPath(context.extensionUri, "out"),
    ];
}

function registerWebviewMessageHandler(webview: vscode.Webview): void {
    webview.onDidReceiveMessage(async (message: WebviewMessage) => {
        try {
            await handleWebviewMessage(webview, message);
        } catch (error) {
            const detail = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(
                `Kor'tana webview action failed: ${detail}`
            );
        }
    });
}

async function handleWebviewMessage(
    webview: vscode.Webview,
    message: WebviewMessage
): Promise<void> {
    const route = resolveWebviewMessage(message);

    if (!route) {
        vscode.window.showWarningMessage(
            `Kor'tana received an unknown webview action: ${message.command ?? message.type ?? "<missing>"}`
        );
        return;
    }

    switch (route.kind) {
        case "command":
            await vscode.commands.executeCommand(route.command);
            return;
        case "dashboardState":
            await webview.postMessage({
                type: "dashboardState",
                payload: await getDashboardStatePayload(),
            });
            return;
        case "metricsState":
            await webview.postMessage({
                type: "metricsState",
                payload: await getMetricsStatePayload(),
            });
            return;
        case "auditLog":
            await webview.postMessage({
                type: "auditLog",
                payload: await getAuditLogPayload(),
            });
            return;
    }
}

async function fetchBackendJson<T>(path: string): Promise<T> {
    const response = await axios.get(`${BACKEND_BASE_URL}${path}`);
    return response.data as T;
}

async function getBackendSummary(): Promise<{
    health?: BackendHealthResponse;
    metrics?: MetricsDashboardResponse;
}> {
    const [health, metrics] = await Promise.allSettled([
        fetchBackendJson<BackendHealthResponse>("/api/health"),
        fetchBackendJson<MetricsDashboardResponse>("/api/metrics/dashboard"),
    ]);

    return {
        health: health.status === "fulfilled" ? health.value : undefined,
        metrics: metrics.status === "fulfilled" ? metrics.value : undefined,
    };
}

async function getDashboardStatePayload(): Promise<DashboardStatePayload> {
    const summary = await getBackendSummary();
    return {
        backendOnline: Boolean(summary.health),
        backendMessage: toDisplayValue(summary.health?.message, "Offline"),
        tasksCount: toDisplayValue(
            summary.metrics?.tasks_processed ?? summary.metrics?.completed_tasks,
            "-"
        ),
        lastSync: toDisplayValue(
            summary.metrics?.last_sync ?? summary.metrics?.last_deployment,
            "N/A"
        ),
    };
}

async function getMetricsStatePayload(): Promise<MetricsStatePayload> {
    const summary = await getBackendSummary();
    return {
        backendOnline: Boolean(summary.health),
        backendMessage: toDisplayValue(summary.health?.message, "Offline"),
        lastDeployment: toDisplayValue(
            summary.metrics?.last_deployment ?? summary.metrics?.last_sync,
            "N/A"
        ),
        tasksCount: toDisplayValue(summary.metrics?.completed_tasks, "0"),
    };
}

async function getAuditLogPayload(): Promise<AuditAction[]> {
    try {
        const actions = await fetchBackendJson<unknown>("/api/autonomy/actions");
        if (!Array.isArray(actions)) {
            return [];
        }

        return actions.map((action) => {
            const record =
                action && typeof action === "object"
                    ? (action as Record<string, unknown>)
                    : {};

            return {
                type: toDisplayValue(record.type, "Action"),
                description: toDisplayValue(record.description, "No details"),
                timestamp: toDisplayValue(record.timestamp, ""),
                status: toDisplayValue(record.status, "pending"),
            };
        });
    } catch {
        return [];
    }
}

function toDisplayValue(value: unknown, fallback: string): string {
    if (value === undefined || value === null || value === "") {
        return fallback;
    }

    return String(value);
}

function createNonce(): string {
    return randomBytes(16).toString("base64");
}

function getWebviewContentSecurityPolicy(
    webview: vscode.Webview,
    nonce?: string,
    frameSources: string[] = []
): string {
    const directives = [
        "default-src 'none'",
        `img-src ${webview.cspSource} https: data:`,
        `style-src ${webview.cspSource} 'unsafe-inline'`,
        `font-src ${webview.cspSource}`,
        nonce ? `script-src 'nonce-${nonce}'` : "script-src 'none'",
    ];

    if (frameSources.length > 0) {
        directives.push(`frame-src ${frameSources.join(" ")}`);
    }

    return directives.join("; ");
}

function renderHtmlDocument(options: HtmlDocumentOptions): string {
    const csp = getWebviewContentSecurityPolicy(
        options.webview,
        options.nonce,
        options.frameSources ?? []
    );
    const scriptTag =
        options.script && options.nonce
            ? `<script nonce="${options.nonce}">${options.script}</script>`
            : "";

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="${csp}">
    <title>${options.title}</title>
</head>
<body>
    ${options.body}
    ${scriptTag}
</body>
</html>`;
}

function getFrameWebviewContent(
    webview: vscode.Webview,
    url: string,
    title: string
): string {
    const frameOrigin = new URL(url).origin;

    return renderHtmlDocument({
        body: `
<style>
    body { margin: 0; padding: 0; overflow: hidden; background: var(--vscode-editor-background); }
    iframe { width: 100%; height: 100vh; border: none; }
</style>
<iframe src="${url}" title="${title}" allow="camera *; microphone *; geolocation *; clipboard-write *;"></iframe>
        `,
        frameSources: [frameOrigin],
        title,
        webview,
    });
}

function getDashboardContent(webview: vscode.Webview): string {
    const nonce = createNonce();

    return renderHtmlDocument({
        body: `
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

<div class="dashboard-card">
    <h4>System Status</h4>
    <p><span class="status-indicator status-alive"></span>Extension Active</p>
    <p>
        <span class="status-indicator" id="backend-status-indicator" style="background: #ffc107;"></span>
        <span id="backend-status-text">Backend: Checking...</span>
    </p>
</div>

<div class="dashboard-card">
    <h4>Quick Actions</h4>
    <button id="action-ai-studio">AI Studio</button>
    <button id="action-deploy-page">Deploy Page</button>
    <button id="action-health-check">Health Check</button>
    <button id="action-unseal-runtime">Unseal Runtime</button>
    <button id="action-metrics">Metrics</button>
    <button id="action-audit">Audit</button>
</div>

<div class="dashboard-card">
    <h4>Autonomy Metrics</h4>
    <p>Tasks Processed: <span id="tasks-count">-</span></p>
    <p>Last Sync: <span id="last-sync">-</span></p>
</div>
        `,
        nonce,
        script: `
const vscodeApi = acquireVsCodeApi();

function postCommand(command) {
    vscodeApi.postMessage({ command });
}

function requestDashboardState() {
    vscodeApi.postMessage({ type: "${REQUEST_DASHBOARD_STATE}" });
}

function updateDashboardState(payload) {
    const indicator = document.getElementById("backend-status-indicator");
    const text = document.getElementById("backend-status-text");
    const tasksCount = document.getElementById("tasks-count");
    const lastSync = document.getElementById("last-sync");

    indicator.style.background = payload.backendOnline ? "#28a745" : "#dc3545";
    text.textContent = payload.backendOnline ? "Backend: " + payload.backendMessage : "Backend: Offline";
    tasksCount.textContent = payload.tasksCount;
    lastSync.textContent = payload.lastSync;
}

window.addEventListener("message", (event) => {
    const message = event.data;
    if (message.type === "dashboardState") {
        updateDashboardState(message.payload);
    }
});

document.getElementById("action-ai-studio").addEventListener("click", () => postCommand("openAIStudio"));
document.getElementById("action-deploy-page").addEventListener("click", () => postCommand("openDeployPage"));
document.getElementById("action-health-check").addEventListener("click", () => postCommand("checkHealth"));
document.getElementById("action-unseal-runtime").addEventListener("click", () => postCommand("unsealRuntime"));
document.getElementById("action-metrics").addEventListener("click", () => postCommand("viewMetrics"));
document.getElementById("action-audit").addEventListener("click", () => postCommand("openAutonomyAudit"));

requestDashboardState();
setInterval(requestDashboardState, 10000);
        `,
        title: "Kor'tana Control Panel",
        webview,
    });
}

function getMetricsContent(webview: vscode.Webview): string {
    const nonce = createNonce();

    return renderHtmlDocument({
        body: `
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
        `,
        nonce,
        script: `
const vscodeApi = acquireVsCodeApi();

function requestMetricsState() {
    vscodeApi.postMessage({ type: "${REQUEST_METRICS_STATE}" });
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
    if (message.type === "metricsState") {
        updateMetricsState(message.payload);
    }
});

requestMetricsState();
setInterval(requestMetricsState, 15000);
        `,
        title: "Kor'tana Metrics",
        webview,
    });
}

function getAutonomyAuditContent(webview: vscode.Webview): string {
    const nonce = createNonce();

    return renderHtmlDocument({
        body: `
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
        `,
        nonce,
        script: `
const vscodeApi = acquireVsCodeApi();

function requestAuditLog() {
    vscodeApi.postMessage({ type: "${REQUEST_AUDIT_LOG}" });
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
    if (message.type === "auditLog") {
        renderAuditLog(message.payload);
    }
});

requestAuditLog();
setInterval(requestAuditLog, 5000);
        `,
        title: "Kor'tana Autonomy Audit",
        webview,
    });
}

export function deactivate() {
    console.log("Kor'tana VS Code Extension deactivated");
}
