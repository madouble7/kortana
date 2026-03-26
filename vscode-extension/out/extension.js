"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const BACKEND_URL = "http://localhost:8000";
const OPERATOR_INBOX_RELATIVE_PATH = ".kortana/operator_inbox.md";
function activate(context) {
    const openAIStudio = async () => {
        const aiStudioUrl = "https://aistudio.google.com/app/prompts/create/1T7Nh4cq1IwCwhHq5u8ZETDb6fY4qVkH3";
        openExternalPanel("kortanaAIStudio", "Kor'tana AI Studio", aiStudioUrl);
    };
    const openDeployPage = async () => {
        const deployUrl = "https://kor-tana-780422883904.us-west1.run.app";
        openExternalPanel("kortanaDeployPage", "Kor'tana Deploy Page", deployUrl);
    };
    const unsealRuntime = async () => {
        vscode.window.showInformationMessage("Unsealing Kor'tana runtime...");
        try {
            const { execSync } = require("child_process");
            const result = execSync("node scripts/unseal-kortana.js", {
                encoding: "utf-8",
            });
            console.log(result);
            vscode.window.showInformationMessage("Kor'tana runtime unsealed successfully.");
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to unseal runtime: ${String(error)}`);
        }
    };
    const checkHealth = async () => {
        try {
            const axios = require("axios");
            const response = await axios.get(`${BACKEND_URL}/api/daemon/status`);
            const data = response.data || {};
            const state = data.system_state || "unknown";
            const mode = data.control_mode || "unknown";
            vscode.window.showInformationMessage(`Kor'tana daemon is ${data.running ? "running" : "stopped"} (${state}, ${mode}).`);
        }
        catch (error) {
            vscode.window.showWarningMessage("Kor'tana backend is offline. Start it with: cd backend && python -m uvicorn src.kortana.main:app --reload");
        }
    };
    const startAlwaysOn = async () => {
        try {
            const axios = require("axios");
            const response = await axios.post(`${BACKEND_URL}/api/always-on/start`);
            const status = response.data?.status || "starting";
            vscode.window.showInformationMessage(`Always-on monitor ${status}.`);
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to start always-on monitor: ${String(error)}`);
        }
    };
    const openOperatorInbox = async () => {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showWarningMessage("Open a workspace folder before using the Kor'tana operator inbox.");
            return;
        }
        const inboxUri = vscode.Uri.joinPath(workspaceFolder.uri, ...OPERATOR_INBOX_RELATIVE_PATH.split("/"));
        const encoder = new TextEncoder();
        try {
            await vscode.workspace.fs.createDirectory(vscode.Uri.joinPath(workspaceFolder.uri, ".kortana"));
            try {
                await vscode.workspace.fs.stat(inboxUri);
            }
            catch {
                await vscode.workspace.fs.writeFile(inboxUri, encoder.encode([
                    "# Kor'tana Operator Inbox",
                    "# Add one steering note per line.",
                    "# focus: backend reliability and tests",
                    "# avoid: billing",
                    "# pause",
                    "# max tasks 1",
                    "",
                ].join("\n")));
            }
            const document = await vscode.workspace.openTextDocument(inboxUri);
            await vscode.window.showTextDocument(document, {
                preview: false,
                preserveFocus: false,
            });
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to open operator inbox: ${String(error)}`);
        }
    };
    const submitDirection = async (prefill) => {
        const content = prefill?.trim() ||
            (await vscode.window.showInputBox({
                title: "Redirect Kor'tana",
                prompt: "Describe what Kor'tana should prioritize, avoid, or change course toward.",
                placeHolder: "Focus on tests and reliability. De-prioritize docs until the backend is stable.",
                ignoreFocusOut: true,
            }))?.trim();
        if (!content) {
            return;
        }
        try {
            const axios = require("axios");
            await axios.post(`${BACKEND_URL}/api/always-on/prompt`, {
                content,
                priority: 80,
            });
            vscode.window.showInformationMessage("Kor'tana course updated.");
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to submit direction: ${String(error)}`);
        }
    };
    context.subscriptions.push(vscode.commands.registerCommand("kortana.openAIStudio", openAIStudio), vscode.commands.registerCommand("kortana.openDeployPage", openDeployPage), vscode.commands.registerCommand("kortana.unsealRuntime", unsealRuntime), vscode.commands.registerCommand("kortana.checkHealth", checkHealth), vscode.commands.registerCommand("kortana.direction.submit", submitDirection), vscode.commands.registerCommand("kortana.operatorInbox.open", openOperatorInbox), vscode.commands.registerCommand("kortana.alwaysOn.start", startAlwaysOn), vscode.commands.registerCommand("kortana.autonomy.audit.open", async () => {
        const panel = vscode.window.createWebviewPanel("kortanaAutonomyAudit", "Kor'tana Autonomy Audit", vscode.ViewColumn.Two, {
            enableScripts: true,
        });
        panel.webview.html = getAutonomyAuditContent();
    }));
    context.subscriptions.push(vscode.workspace.onDidSaveTextDocument((document) => {
        const normalized = document.uri.fsPath.replace(/\\/g, "/").toLowerCase();
        if (normalized.endsWith(OPERATOR_INBOX_RELATIVE_PATH.toLowerCase())) {
            vscode.window.setStatusBarMessage("Kor'tana inbox updated. The backend will ingest the new guidance automatically.", 4000);
        }
    }));
    context.subscriptions.push(vscode.window.registerWebviewViewProvider("kortana-dashboard", {
        resolveWebviewView(webviewView) {
            webviewView.webview.options = {
                enableScripts: true,
            };
            webviewView.webview.onDidReceiveMessage(async (message) => {
                switch (message.command) {
                    case "openAIStudio":
                        await openAIStudio();
                        break;
                    case "openDeployPage":
                        await openDeployPage();
                        break;
                    case "checkHealth":
                        await checkHealth();
                        break;
                    case "unsealRuntime":
                        await unsealRuntime();
                        break;
                    case "submitDirection":
                        await submitDirection(message.content);
                        break;
                    case "startAlwaysOn":
                        await startAlwaysOn();
                        break;
                    case "openOperatorInbox":
                        await openOperatorInbox();
                        break;
                    default:
                        break;
                }
            });
            webviewView.webview.html = getDashboardContent();
        },
    }));
    vscode.window.showInformationMessage("Kor'tana control surface is online.");
}
function openExternalPanel(viewType, title, url) {
    const panel = vscode.window.createWebviewPanel(viewType, title, vscode.ViewColumn.One, {
        enableScripts: true,
        enableCommandUris: true,
    });
    panel.webview.html = getExternalPanelContent(url);
}
function getAutonomyAuditContent() {
    return `
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: var(--vscode-font-family); padding: 20px; color: var(--vscode-foreground); background: var(--vscode-editor-background); }
        h1 { color: var(--vscode-textLink-foreground); }
        .audit-item { margin: 10px 0; padding: 10px; background: var(--vscode-list-inactiveSelectionBackground); border-radius: 4px; }
    </style>
</head>
<body>
    <h1>Kor'tana Autonomy Audit</h1>
    <p>Polling daemon and course state from the local backend.</p>
    <div id="audit-log">Loading...</div>
    <script>
        async function loadAudit() {
            try {
                const [daemonResponse, courseResponse] = await Promise.all([
                    fetch("${BACKEND_URL}/api/daemon/status"),
                    fetch("${BACKEND_URL}/api/always-on/course")
                ]);
                const daemon = await daemonResponse.json();
                const course = await courseResponse.json();
                document.getElementById("audit-log").innerHTML = [
                    "<div class='audit-item'><strong>Daemon:</strong> " + (daemon.running ? "running" : "stopped") + " | mode=" + (daemon.control_mode || "unknown") + "</div>",
                    "<div class='audit-item'><strong>System state:</strong> " + (daemon.system_state || "unknown") + "</div>",
                    "<div class='audit-item'><strong>Current course:</strong> " + (course.summary?.prompt_preamble || "No active course corrections") + "</div>"
                ].join("");
            } catch (error) {
                document.getElementById("audit-log").textContent = "Backend unavailable.";
            }
        }

        loadAudit();
        setInterval(loadAudit, 5000);
    </script>
</body>
</html>
    `;
}
function getDashboardContent() {
    return `
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: var(--vscode-font-family); padding: 15px; color: var(--vscode-foreground); background: var(--vscode-editor-background); }
        .dashboard-card { margin: 10px 0; padding: 15px; background: var(--vscode-editorWidget-background); border: 1px solid var(--vscode-panel-border); border-radius: 4px; }
        .status-line { margin: 6px 0; }
        textarea { width: 100%; min-height: 90px; resize: vertical; padding: 8px; color: var(--vscode-input-foreground); background: var(--vscode-input-background); border: 1px solid var(--vscode-input-border); border-radius: 4px; }
        button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 6px 12px; border-radius: 2px; cursor: pointer; margin: 2px 4px 2px 0; }
        button:hover { background: var(--vscode-button-hoverBackground); }
        .course { white-space: pre-wrap; line-height: 1.4; }
        .muted { opacity: 0.8; }
    </style>
</head>
<body>
    <h3>Kor'tana Control Panel</h3>

    <div class="dashboard-card">
        <h4>Runtime</h4>
        <div class="status-line" id="daemon-status">Daemon: checking...</div>
        <div class="status-line" id="runtime-mode">Mode: -</div>
        <div class="status-line" id="runtime-state">System state: -</div>
        <div class="status-line" id="workspace-status">Workspace: -</div>
        <button onclick="startAlwaysOn()">Start Always-On Monitor</button>
        <button onclick="openOperatorInbox()">Open Operator Inbox</button>
        <button onclick="checkHealth()">Refresh Health</button>
    </div>

    <div class="dashboard-card">
        <h4>Steer Kor'tana</h4>
        <textarea id="direction-input" placeholder="Change Kor'tana's course. Example: Focus on backend reliability and tests. Avoid new UI work until the daemon is stable."></textarea>
        <div style="margin-top: 8px;">
            <button onclick="submitDirection()">Send Direction</button>
            <button onclick="clearDirection()">Clear</button>
        </div>
        <p class="muted">This posts to the always-on directive system so the daemon can keep working without waiting for a new prompt.</p>
    </div>

    <div class="dashboard-card">
        <h4>Current Course</h4>
        <div id="course-summary" class="course">Loading current course...</div>
    </div>

    <div class="dashboard-card">
        <h4>Quick Actions</h4>
        <button onclick="openAIStudio()">AI Studio</button>
        <button onclick="openDeployPage()">Deploy Page</button>
        <button onclick="unsealRuntime()">Unseal Runtime</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        function openAIStudio() {
            vscode.postMessage({ command: "openAIStudio" });
        }

        function openDeployPage() {
            vscode.postMessage({ command: "openDeployPage" });
        }

        function checkHealth() {
            vscode.postMessage({ command: "checkHealth" });
            refreshRuntime();
        }

        function unsealRuntime() {
            vscode.postMessage({ command: "unsealRuntime" });
        }

        function startAlwaysOn() {
            vscode.postMessage({ command: "startAlwaysOn" });
        }

        function openOperatorInbox() {
            vscode.postMessage({ command: "openOperatorInbox" });
        }

        function submitDirection() {
            const input = document.getElementById("direction-input");
            const content = input.value.trim();
            if (!content) {
                return;
            }
            vscode.postMessage({ command: "submitDirection", content });
            input.value = "";
            setTimeout(refreshCourse, 750);
        }

        function clearDirection() {
            document.getElementById("direction-input").value = "";
        }

        async function refreshRuntime() {
            try {
                const [daemonResponse, workspaceResponse] = await Promise.all([
                    fetch("${BACKEND_URL}/api/daemon/status"),
                    fetch("${BACKEND_URL}/api/always-on/workspace")
                ]);
                const data = await daemonResponse.json();
                const workspace = await workspaceResponse.json();
                document.getElementById("daemon-status").textContent =
                    "Daemon: " + (data.running ? "running" : "stopped");
                document.getElementById("runtime-mode").textContent =
                    "Mode: " + (data.control_mode || "unknown");
                document.getElementById("runtime-state").textContent =
                    "System state: " + (data.system_state || "unknown");
                const ws = workspace.workspace || {};
                document.getElementById("workspace-status").textContent =
                    "Workspace: branch=" + (ws.branch || "unknown") +
                    " | dirty=" + (ws.dirty ? "yes" : "no") +
                    " | changed=" + (ws.changed_count || 0);
            } catch (error) {
                document.getElementById("daemon-status").textContent = "Daemon: offline";
                document.getElementById("runtime-mode").textContent = "Mode: -";
                document.getElementById("runtime-state").textContent = "System state: -";
                document.getElementById("workspace-status").textContent = "Workspace: -";
            }
        }

        async function refreshCourse() {
            try {
                const response = await fetch("${BACKEND_URL}/api/always-on/course");
                const data = await response.json();
                const summary = data.summary || {};
                const lines = [];
                if (summary.prompt_preamble) {
                    lines.push(summary.prompt_preamble);
                } else {
                    lines.push("No active course corrections.");
                }
                lines.push("Active directives: " + (summary.active_count || 0));
                if (summary.focus_topics && summary.focus_topics.length) {
                    lines.push("Focus: " + summary.focus_topics.join(", "));
                }
                if (summary.avoid_topics && summary.avoid_topics.length) {
                    lines.push("Avoid: " + summary.avoid_topics.join(", "));
                }
                document.getElementById("course-summary").textContent = lines.join("\\n");
            } catch (error) {
                document.getElementById("course-summary").textContent = "Backend unavailable.";
            }
        }

        refreshRuntime();
        refreshCourse();
        setInterval(refreshRuntime, 10000);
        setInterval(refreshCourse, 10000);
    </script>
</body>
</html>
    `;
}
function getExternalPanelContent(url) {
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kor'tana</title>
    <style>
        body { margin: 0; padding: 0; overflow: hidden; }
        iframe { width: 100%; height: 100vh; border: none; }
    </style>
</head>
<body>
    <iframe src="${url}" allow="camera *; microphone *; geolocation *; clipboard-write *;"></iframe>
</body>
</html>
    `;
}
function deactivate() {
    console.log("Kor'tana VS Code Extension deactivated");
}
//# sourceMappingURL=extension.js.map