type CssDeclarations = Record<string, string>;

type CssRule = {
    declarations: CssDeclarations;
    selector: string;
};

export const STATUS_ALIVE_CLASS = "status-alive";
export const STATUS_OFFLINE_CLASS = "status-offline";
export const STATUS_ALIVE_COLOR = "#28a745";
export const STATUS_OFFLINE_COLOR = "#dc3545";
export const STATUS_PENDING_COLOR = "#ffc107";
export const STATUS_SUCCESS_COLOR = STATUS_ALIVE_COLOR;
export const STATUS_FAILED_COLOR = STATUS_OFFLINE_COLOR;

function renderCssRule(rule: CssRule): string {
    const declarations = Object.entries(rule.declarations)
        .map(([property, value]) => `        ${property}: ${value};`)
        .join("\n");

    return `    ${rule.selector} {\n${declarations}\n    }`;
}

function createStyleBlock(rules: CssRule[]): string {
    return `<style>
${rules.map(renderCssRule).join("\n")}
</style>`;
}

function createBaseBodyRules(paddingPx: number): CssRule[] {
    return [
        {
            selector: "body",
            declarations: {
                "background": "var(--vscode-editor-background)",
                "color": "var(--vscode-foreground)",
                "font-family": "var(--vscode-font-family)",
                "padding": `${paddingPx}px`,
            },
        },
    ];
}

function createAccentHeadingRule(selector: string): CssRule {
    return {
        selector,
        declarations: {
            "color": "var(--vscode-textLink-foreground)",
        },
    };
}

export function createDashboardStyles(): string {
    return createStyleBlock([
        ...createBaseBodyRules(15),
        {
            selector: ".dashboard-card",
            declarations: {
                "background": "var(--vscode-editorWidget-background)",
                "border": "1px solid var(--vscode-panel-border)",
                "border-radius": "4px",
                "margin": "10px 0",
                "padding": "15px",
            },
        },
        {
            selector: ".status-indicator",
            declarations: {
                "border-radius": "50%",
                "display": "inline-block",
                "height": "8px",
                "margin-right": "8px",
                "width": "8px",
            },
        },
        {
            selector: `.${STATUS_ALIVE_CLASS}`,
            declarations: {
                "background": STATUS_ALIVE_COLOR,
            },
        },
        {
            selector: `.${STATUS_OFFLINE_CLASS}`,
            declarations: {
                "background": STATUS_OFFLINE_COLOR,
            },
        },
        {
            selector: "button",
            declarations: {
                "background": "var(--vscode-button-background)",
                "border": "none",
                "border-radius": "2px",
                "color": "var(--vscode-button-foreground)",
                "cursor": "pointer",
                "margin": "2px",
                "padding": "6px 12px",
            },
        },
        {
            selector: "button:hover",
            declarations: {
                "background": "var(--vscode-button-hoverBackground)",
            },
        },
    ]);
}

export function createMetricsStyles(): string {
    return createStyleBlock([
        ...createBaseBodyRules(20),
        createAccentHeadingRule("h1"),
        {
            selector: ".metric",
            declarations: {
                "background": "var(--vscode-editorWidget-background)",
                "border-left": "3px solid var(--vscode-textLink-foreground)",
                "margin": "10px 0",
                "padding": "10px",
            },
        },
        {
            selector: `.${STATUS_ALIVE_CLASS}`,
            declarations: {
                "color": STATUS_ALIVE_COLOR,
            },
        },
        {
            selector: `.${STATUS_OFFLINE_CLASS}`,
            declarations: {
                "color": STATUS_OFFLINE_COLOR,
            },
        },
    ]);
}

export function createAuditStyles(): string {
    return createStyleBlock([
        ...createBaseBodyRules(20),
        createAccentHeadingRule("h1"),
        {
            selector: ".audit-item",
            declarations: {
                "background": "var(--vscode-list-inactiveSelectionBackground)",
                "border-radius": "4px",
                "margin": "10px 0",
                "padding": "10px",
            },
        },
        {
            selector: ".status-success",
            declarations: {
                "border-left": `3px solid ${STATUS_SUCCESS_COLOR}`,
            },
        },
        {
            selector: ".status-failed",
            declarations: {
                "border-left": `3px solid ${STATUS_FAILED_COLOR}`,
            },
        },
        {
            selector: ".status-pending",
            declarations: {
                "border-left": `3px solid ${STATUS_PENDING_COLOR}`,
            },
        },
    ]);
}

export function createFrameStyles(): string {
    return createStyleBlock([
        {
            selector: "body",
            declarations: {
                "background": "var(--vscode-editor-background)",
                "margin": "0",
                "overflow": "hidden",
                "padding": "0",
            },
        },
        {
            selector: "iframe",
            declarations: {
                "border": "none",
                "height": "100vh",
                "width": "100%",
            },
        },
    ]);
}
