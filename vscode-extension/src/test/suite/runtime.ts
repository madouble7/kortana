import * as assert from "assert";

import {
    createCommandMessage,
    createRequestMessage,
    REQUEST_DASHBOARD_STATE,
    RESPONSE_DASHBOARD_STATE,
} from "../../webview/messages";
import { createWebviewRuntimeScript } from "../../webview/runtime";

export function runRuntimeTests(): void {
    const script = createWebviewRuntimeScript({
        commandBindings: [
            {
                elementId: "action-ai-studio",
                message: createCommandMessage("openAIStudio"),
            },
        ],
        responseBindings: [
            {
                type: RESPONSE_DASHBOARD_STATE,
                handlerName: "updateDashboardState",
            },
        ],
        requestPollers: [
            {
                functionName: "requestDashboardState",
                message: createRequestMessage(REQUEST_DASHBOARD_STATE),
                invokeImmediately: true,
                intervalMs: 10000,
            },
        ],
    });

    assert.ok(script.includes("const vscodeApi = acquireVsCodeApi();"));
    assert.ok(script.includes("function postHostMessage(message) {"));
    assert.ok(script.includes("function requestDashboardState() {"));
    assert.ok(
        script.includes(
            'postHostMessage({"type":"requestDashboardState"});'
        )
    );
    assert.ok(script.includes('case "dashboardState":'));
    assert.ok(script.includes("updateDashboardState(message.payload);"));
    assert.ok(
        script.includes(
            'document.getElementById("action-ai-studio").addEventListener("click", () => postHostMessage({"command":"openAIStudio"}));'
        )
    );
    assert.ok(script.includes("requestDashboardState();"));
    assert.ok(script.includes("setInterval(requestDashboardState, 10000);"));
}
