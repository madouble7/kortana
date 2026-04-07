import * as assert from "assert";

import { createWebviewFormattingHelpersScript } from "../../webview/formatting";

export function runFormattingHelperTests(): void {
    const script = createWebviewFormattingHelpersScript();

    assert.ok(script.includes('const STATUS_ALIVE_CLASS = "status-alive";'));
    assert.ok(script.includes('const STATUS_OFFLINE_COLOR = "#dc3545";'));
    assert.ok(script.includes("function formatStatusText(isOnline, onlineText, offlineText = \"Offline\", label = \"\") {"));
    assert.ok(script.includes("function getStatusClassName(isOnline) {"));
    assert.ok(script.includes("function getStatusIndicatorColor(isOnline) {"));
    assert.ok(script.includes("function applyStatusText(id, isOnline, onlineText, offlineText = \"Offline\", label = \"\") {"));
    assert.ok(script.includes("function applyStatusClassName(id, isOnline) {"));
    assert.ok(script.includes("function applyStatusIndicatorColor(id, isOnline) {"));
    assert.ok(script.includes("function formatTimestamp(value) {"));
    assert.ok(script.includes("function createAuditActionItem(action) {"));
    assert.ok(script.includes("function renderAuditActionList(containerId, actions) {"));
    assert.ok(script.includes('renderStateBlock('));
}
