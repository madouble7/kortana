import * as assert from "assert";

import { createWebviewDomHelpersScript } from "../../webview/dom";

export function runDomHelperTests(): void {
    const script = createWebviewDomHelpersScript();

    assert.ok(script.includes("function getRequiredElement(id) {"));
    assert.ok(script.includes("throw new Error(\"Missing required element: \" + id);"));
    assert.ok(script.includes("function setElementText(id, value) {"));
    assert.ok(script.includes("function setElementClassName(id, className) {"));
    assert.ok(script.includes("function setElementStyle(id, property, value) {"));
    assert.ok(script.includes("function replaceElementChildren(id, ...children) {"));
    assert.ok(script.includes("function createDomElement(tagName, options = {}) {"));
    assert.ok(script.includes("function renderStateBlock(containerId, title, detail = \"\", className = \"\") {"));
}
