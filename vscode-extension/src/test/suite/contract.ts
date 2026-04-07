import * as assert from "assert";

import {
    createAuditLogEnvelope,
    createCommandMessage,
    createDashboardStateEnvelope,
    createMetricsStateEnvelope,
    createRequestMessage,
    REQUEST_AUDIT_LOG,
    REQUEST_DASHBOARD_STATE,
    REQUEST_METRICS_STATE,
    RESPONSE_AUDIT_LOG,
    RESPONSE_DASHBOARD_STATE,
    RESPONSE_METRICS_STATE,
    resolveWebviewMessage,
} from "../../webview/messages";

export function runContractTests(): void {
    assert.deepStrictEqual(createCommandMessage("openAIStudio"), {
        command: "openAIStudio",
    });
    assert.deepStrictEqual(createCommandMessage("kortana.openAIStudio"), {
        command: "kortana.openAIStudio",
    });

    assert.deepStrictEqual(createRequestMessage(REQUEST_DASHBOARD_STATE), {
        type: REQUEST_DASHBOARD_STATE,
    });
    assert.deepStrictEqual(createRequestMessage(REQUEST_METRICS_STATE), {
        type: REQUEST_METRICS_STATE,
    });
    assert.deepStrictEqual(createRequestMessage(REQUEST_AUDIT_LOG), {
        type: REQUEST_AUDIT_LOG,
    });

    assert.deepStrictEqual(
        createDashboardStateEnvelope({
            backendOnline: true,
            backendMessage: "Awake",
            tasksCount: "108",
            lastSync: "2026-03-27T12:00:00Z",
        }),
        {
            type: RESPONSE_DASHBOARD_STATE,
            payload: {
                backendOnline: true,
                backendMessage: "Awake",
                tasksCount: "108",
                lastSync: "2026-03-27T12:00:00Z",
            },
        }
    );

    assert.deepStrictEqual(
        createMetricsStateEnvelope({
            backendOnline: true,
            backendMessage: "Nominal",
            lastDeployment: "2026-03-27T12:34:56Z",
            tasksCount: "42",
        }),
        {
            type: RESPONSE_METRICS_STATE,
            payload: {
                backendOnline: true,
                backendMessage: "Nominal",
                lastDeployment: "2026-03-27T12:34:56Z",
                tasksCount: "42",
            },
        }
    );

    assert.deepStrictEqual(
        createAuditLogEnvelope([
            {
                type: "deploy",
                description: "Runtime promoted",
                timestamp: "2026-03-27T12:34:56Z",
                status: "success",
            },
        ]),
        {
            type: RESPONSE_AUDIT_LOG,
            payload: [
                {
                    type: "deploy",
                    description: "Runtime promoted",
                    timestamp: "2026-03-27T12:34:56Z",
                    status: "success",
                },
            ],
        }
    );

    assert.deepStrictEqual(
        resolveWebviewMessage(createRequestMessage(REQUEST_DASHBOARD_STATE)),
        { kind: "dashboardState" }
    );
    assert.deepStrictEqual(
        resolveWebviewMessage(createRequestMessage(REQUEST_METRICS_STATE)),
        { kind: "metricsState" }
    );
    assert.deepStrictEqual(
        resolveWebviewMessage(createRequestMessage(REQUEST_AUDIT_LOG)),
        { kind: "auditLog" }
    );
    assert.deepStrictEqual(resolveWebviewMessage(createCommandMessage("openAIStudio")), {
        kind: "command",
        command: "kortana.openAIStudio",
    });
}
