import * as assert from "assert";

import {
    createButtonGroup,
    createEmptyStateBlock,
    createHeroSection,
    createLabeledValueRow,
    createMetricCard,
    createPanel,
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
        createHeroSection({
            description: "Live control surface",
            kicker: "Always-On Companion",
            signals: [
                {
                    label: "Runtime",
                    valueHtml: '<span id="backend-status-text">Checking...</span>',
                },
            ],
            title: "Kor'tana Control Deck",
        }).includes('class="hero-card"')
    );
    assert.ok(
        createHeroSection({
            description: "Live control surface",
            kicker: "Always-On Companion",
            signals: [
                {
                    label: "Runtime",
                    valueHtml: '<span id="backend-status-text">Checking...</span>',
                },
            ],
            title: "Kor'tana Control Deck",
        }).includes("Always-On Companion")
    );

    assert.ok(
        createLabeledValueRow({
            label: "Tasks Processed:",
            valueHtml: '<span id="tasks-count">-</span>',
        }).includes('class="data-row"')
    );

    assert.ok(
        createMetricCard({
            label: "Tasks Completed:",
            valueHtml: '<span id="tasks-count">Loading...</span>',
        }).includes('class="metric-value"')
    );

    assert.ok(
        createButtonGroup([{ id: "action-metrics", label: "Metrics & Audit" }]).includes(
            'class="action-grid"'
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
