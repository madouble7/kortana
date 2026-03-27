import * as assert from "assert";
import * as vscode from "vscode";
import { runContractTests } from "./contract";

import {
    buildAuditLogPayload,
    buildDashboardStatePayload,
    buildMetricsStatePayload,
    resolveDashboardCommand,
    resolveWebviewMessage,
} from "../../extension";

const EXPECTED_COMMANDS = [
    "kortana.openAIStudio",
    "kortana.openDeployPage",
    "kortana.unsealRuntime",
    "kortana.checkHealth",
    "kortana.viewMetrics",
    "kortana.autonomy.audit.open",
];

const EXPECTED_DASHBOARD_MAPPINGS: Record<string, string> = {
    openAIStudio: "kortana.openAIStudio",
    openDeployPage: "kortana.openDeployPage",
    unsealRuntime: "kortana.unsealRuntime",
    checkHealth: "kortana.checkHealth",
    viewMetrics: "kortana.viewMetrics",
    openAutonomyAudit: "kortana.autonomy.audit.open",
};

const EXPECTED_REQUEST_TYPES: Record<string, string> = {
    requestDashboardState: "dashboardState",
    requestMetricsState: "metricsState",
    requestAuditLog: "auditLog",
};

export async function run(): Promise<void> {
    runContractTests();

    const extension = vscode.extensions.all.find(
        (candidate) => candidate.packageJSON.name === "kortana-vscode"
    );

    assert.ok(extension, "Expected the Kor'tana extension to be available");

    if (!extension.isActive) {
        await extension.activate();
    }

    const registeredCommands = await vscode.commands.getCommands(true);
    const contributedCommands: string[] =
        extension.packageJSON.contributes?.commands?.map(
            (command: { command: string }) => command.command
        ) ?? [];

    for (const command of EXPECTED_COMMANDS) {
        assert.ok(
            registeredCommands.includes(command),
            `Expected command to be registered: ${command}`
        );
        assert.ok(
            contributedCommands.includes(command),
            `Expected command to be contributed: ${command}`
        );
    }

    for (const [action, command] of Object.entries(EXPECTED_DASHBOARD_MAPPINGS)) {
        assert.strictEqual(
            resolveDashboardCommand({ command: action }),
            command,
            `Expected dashboard action ${action} to resolve to ${command}`
        );
        assert.deepStrictEqual(
            resolveWebviewMessage({ command: action }),
            { kind: "command", command },
            `Expected webview command ${action} to resolve to ${command}`
        );
    }

    for (const [requestType, kind] of Object.entries(EXPECTED_REQUEST_TYPES)) {
        assert.deepStrictEqual(resolveWebviewMessage({ type: requestType }), {
            kind,
        });
    }

    assert.strictEqual(
        resolveDashboardCommand({ command: "kortana.openAIStudio" }),
        "kortana.openAIStudio"
    );
    assert.deepStrictEqual(resolveWebviewMessage({ command: "kortana.openAIStudio" }), {
        kind: "command",
        command: "kortana.openAIStudio",
    });
    assert.strictEqual(resolveDashboardCommand({ command: "unknown" }), undefined);
    assert.strictEqual(resolveWebviewMessage({ command: "unknown" }), undefined);
    assert.strictEqual(resolveDashboardCommand({}), undefined);
    assert.strictEqual(resolveWebviewMessage({}), undefined);

    assert.deepStrictEqual(buildDashboardStatePayload({}), {
        backendOnline: false,
        backendMessage: "Offline",
        tasksCount: "-",
        lastSync: "N/A",
    });
    assert.deepStrictEqual(
        buildDashboardStatePayload({
            health: { message: "Awake" },
            metrics: {
                tasks_processed: 108,
                last_sync: "2026-03-27T12:00:00Z",
            },
        }),
        {
            backendOnline: true,
            backendMessage: "Awake",
            tasksCount: "108",
            lastSync: "2026-03-27T12:00:00Z",
        }
    );

    assert.deepStrictEqual(buildMetricsStatePayload({}), {
        backendOnline: false,
        backendMessage: "Offline",
        lastDeployment: "N/A",
        tasksCount: "0",
    });
    assert.deepStrictEqual(
        buildMetricsStatePayload({
            health: { message: "Nominal" },
            metrics: {
                completed_tasks: 42,
                last_deployment: "2026-03-27T12:34:56Z",
            },
        }),
        {
            backendOnline: true,
            backendMessage: "Nominal",
            lastDeployment: "2026-03-27T12:34:56Z",
            tasksCount: "42",
        }
    );

    assert.deepStrictEqual(buildAuditLogPayload("not-an-array"), []);
    assert.deepStrictEqual(
        buildAuditLogPayload([
            {
                type: "deploy",
                description: "Runtime promoted",
                timestamp: "2026-03-27T12:34:56Z",
                status: "success",
            },
            {
                description: "Missing type falls back",
            },
            "noise",
        ]),
        [
            {
                type: "deploy",
                description: "Runtime promoted",
                timestamp: "2026-03-27T12:34:56Z",
                status: "success",
            },
            {
                type: "Action",
                description: "Missing type falls back",
                timestamp: "",
                status: "pending",
            },
            {
                type: "Action",
                description: "No details",
                timestamp: "",
                status: "pending",
            },
        ]
    );
}
