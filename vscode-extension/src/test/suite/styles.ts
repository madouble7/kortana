import * as assert from "assert";

import {
    createAuditStyles,
    createDashboardStyles,
    createFrameStyles,
    createMetricsStyles,
    STATUS_ALIVE_COLOR,
    STATUS_OFFLINE_COLOR,
    STATUS_PENDING_COLOR,
} from "../../webview/styles";

export function runStyleTests(): void {
    const dashboardStyles = createDashboardStyles();
    assert.ok(dashboardStyles.includes("font-family: var(--vscode-font-family);"));
    assert.ok(dashboardStyles.includes(".dashboard-card {"));
    assert.ok(dashboardStyles.includes(`background: ${STATUS_ALIVE_COLOR};`));
    assert.ok(dashboardStyles.includes("button:hover {"));

    const metricsStyles = createMetricsStyles();
    assert.ok(metricsStyles.includes("h1 {"));
    assert.ok(metricsStyles.includes(".metric {"));
    assert.ok(metricsStyles.includes(`color: ${STATUS_OFFLINE_COLOR};`));

    const auditStyles = createAuditStyles();
    assert.ok(auditStyles.includes(".audit-item {"));
    assert.ok(
        auditStyles.includes(`border-left: 3px solid ${STATUS_PENDING_COLOR};`)
    );

    const frameStyles = createFrameStyles();
    assert.ok(frameStyles.includes("overflow: hidden;"));
    assert.ok(frameStyles.includes("height: 100vh;"));
}
