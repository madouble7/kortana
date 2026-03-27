import { execSync } from "child_process";

import * as vscode from "vscode";
import {
    COMMAND_CHECK_HEALTH,
    COMMAND_OPEN_AI_STUDIO,
    COMMAND_OPEN_AUTONOMY_AUDIT,
    COMMAND_OPEN_DEPLOY_PAGE,
    COMMAND_UNSEAL_RUNTIME,
    COMMAND_VIEW_METRICS,
} from "./commands";
import {
    getAuditLogPayload,
    getDashboardStatePayload,
    getMetricsStatePayload,
} from "./webview/backend";
import { getAutonomyAuditContent } from "./webview/audit";
import { getDashboardContent } from "./webview/dashboard";
import { getFrameWebviewContent } from "./webview/html";
import {
    resolveDashboardCommand,
    resolveWebviewMessage,
    type WebviewMessage,
} from "./webview/messages";
import { getMetricsContent } from "./webview/metrics";

export { resolveDashboardCommand, resolveWebviewMessage } from "./webview/messages";
export {
    buildAuditLogPayload,
    buildDashboardStatePayload,
    buildMetricsStatePayload,
} from "./webview/payloads";

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

export function deactivate() {
    console.log("Kor'tana VS Code Extension deactivated");
}
