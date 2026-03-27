import * as assert from "assert";

import {
    createButtonGroup,
    createEmptyStateBlock,
    createLabeledValueRow,
    createMetricCard,
    createPanel,
    createStatusLine,
    createTextSpan,
} from "../../webview/fragments";

export function runFragmentTests(): void {
    assert.ok(
        createPanel({
            body: "<p>Ready</p>",
            className: "dashboard-card",
            title: "System Status",
        }).includes('<div class="dashboard-card">')
    );
    assert.ok(
        createPanel({
            body: "<p>Ready</p>",
            className: "dashboard-card",
            title: "System Status",
        }).includes("<h4>System Status</h4>")
    );

    assert.strictEqual(
        createTextSpan({ id: "tasks-count", text: "108" }),
        '<span id="tasks-count">108</span>'
    );

    assert.ok(
        createStatusLine({
            contentHtml: "<span>Checking...</span>",
            indicatorId: "backend-status-indicator",
            indicatorStyle: "background: #ffc107;",
        }).includes('id="backend-status-indicator"')
    );
    assert.ok(
        createStatusLine({
            contentHtml: "<span>Checking...</span>",
            indicatorId: "backend-status-indicator",
            indicatorStyle: "background: #ffc107;",
        }).includes('style="background: #ffc107;"')
    );

    assert.ok(
        createLabeledValueRow({
            label: "Tasks Processed:",
            valueHtml: '<span id="tasks-count">-</span>',
        }).includes("Tasks Processed:")
    );

    assert.ok(
        createMetricCard({
            label: "Tasks Completed:",
            valueHtml: '<span id="tasks-count">Loading...</span>',
        }).includes("<strong>Tasks Completed:</strong>")
    );

    assert.ok(
        createButtonGroup([{ id: "action-metrics", label: "Metrics & Audit" }]).includes(
            "Metrics &amp; Audit"
        )
    );

    assert.ok(
        createEmptyStateBlock({
            className: "audit-item status-pending",
            detail: "Loading recent actions...",
            title: "Initializing audit system...",
        }).includes("Loading recent actions...")
    );
}
