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
            selector: ":root",
            declarations: {
                "--kortana-accent": STATUS_ALIVE_COLOR,
                "--kortana-glow": "rgba(73, 164, 247, 0.18)",
                "--kortana-surface": "rgba(255, 255, 255, 0.03)",
                "--kortana-warm": "rgba(255, 193, 107, 0.16)",
            },
        },
        {
            selector: "body",
            declarations: {
                "background": "var(--vscode-editor-background)",
                "color": "var(--vscode-foreground)",
                "font-family": "var(--vscode-font-family)",
                "margin": "0",
                "min-height": "100vh",
                "padding": `${paddingPx}px`,
                "position": "relative",
            },
        },
        {
            selector: "body::before",
            declarations: {
                "background": "radial-gradient(circle at top left, var(--kortana-glow), transparent 36%), radial-gradient(circle at 85% 15%, var(--kortana-warm), transparent 24%)",
                "content": "\"\"",
                "inset": "0",
                "pointer-events": "none",
                "position": "fixed",
                "z-index": "0",
            },
        },
        {
            selector: ".page-shell",
            declarations: {
                "display": "grid",
                "gap": "16px",
                "position": "relative",
                "z-index": "1",
            },
        },
        {
            selector: ".hero-card",
            declarations: {
                "background": "linear-gradient(135deg, rgba(28, 58, 86, 0.42), rgba(120, 79, 35, 0.18)), var(--vscode-editorWidget-background)",
                "border": "1px solid rgba(255, 255, 255, 0.08)",
                "border-radius": "18px",
                "box-shadow": "0 18px 42px rgba(0, 0, 0, 0.16)",
                "overflow": "hidden",
                "padding": "20px 22px",
                "position": "relative",
            },
        },
        {
            selector: ".hero-card::after",
            declarations: {
                "background": "linear-gradient(90deg, rgba(255, 255, 255, 0.22), transparent)",
                "content": "\"\"",
                "height": "1px",
                "left": "20px",
                "position": "absolute",
                "right": "20px",
                "top": "0",
            },
        },
        {
            selector: ".eyebrow",
            declarations: {
                "color": "var(--vscode-descriptionForeground)",
                "display": "inline-block",
                "font-size": "11px",
                "font-weight": "700",
                "letter-spacing": "0.18em",
                "margin-bottom": "10px",
                "text-transform": "uppercase",
            },
        },
        {
            selector: ".hero-title",
            declarations: {
                "font-size": "24px",
                "font-weight": "700",
                "letter-spacing": "-0.03em",
                "line-height": "1.05",
                "margin": "0 0 8px",
            },
        },
        {
            selector: ".hero-copy",
            declarations: {
                "color": "var(--vscode-descriptionForeground)",
                "line-height": "1.55",
                "margin": "0",
                "max-width": "64ch",
            },
        },
        {
            selector: ".signal-strip",
            declarations: {
                "display": "grid",
                "gap": "10px",
                "grid-template-columns": "repeat(auto-fit, minmax(160px, 1fr))",
                "margin-top": "18px",
            },
        },
        {
            selector: ".signal-chip",
            declarations: {
                "background": "rgba(9, 12, 19, 0.22)",
                "border": "1px solid rgba(255, 255, 255, 0.08)",
                "border-radius": "14px",
                "min-height": "72px",
                "padding": "12px 14px",
            },
        },
        {
            selector: ".signal-label",
            declarations: {
                "color": "var(--vscode-descriptionForeground)",
                "display": "block",
                "font-size": "11px",
                "font-weight": "700",
                "letter-spacing": "0.12em",
                "margin-bottom": "8px",
                "text-transform": "uppercase",
            },
        },
        {
            selector: ".signal-value",
            declarations: {
                "font-size": "14px",
                "font-weight": "600",
                "line-height": "1.4",
            },
        },
        {
            selector: ".signal-inline",
            declarations: {
                "align-items": "center",
                "display": "inline-flex",
                "gap": "8px",
            },
        },
        {
            selector: ".signal-accent",
            declarations: {
                "color": "rgba(255, 208, 131, 0.92)",
                "font-weight": "700",
            },
        },
        {
            selector: ".panel-grid",
            declarations: {
                "display": "grid",
                "gap": "14px",
            },
        },
        {
            selector: ".panel-grid.two-up",
            declarations: {
                "grid-template-columns": "repeat(auto-fit, minmax(250px, 1fr))",
            },
        },
        {
            selector: ".panel-heading",
            declarations: {
                "align-items": "baseline",
                "display": "flex",
                "gap": "10px",
                "justify-content": "space-between",
                "margin-bottom": "14px",
            },
        },
        {
            selector: ".panel-title",
            declarations: {
                "font-size": "14px",
                "font-weight": "700",
                "letter-spacing": "0.06em",
                "margin": "0",
                "text-transform": "uppercase",
            },
        },
        {
            selector: ".panel-body",
            declarations: {
                "display": "grid",
                "gap": "10px",
            },
        },
        {
            selector: ".panel-note",
            declarations: {
                "color": "var(--vscode-descriptionForeground)",
                "font-size": "12px",
            },
        },
        {
            selector: ".data-stack",
            declarations: {
                "display": "grid",
                "gap": "10px",
            },
        },
        {
            selector: ".data-row",
            declarations: {
                "align-items": "center",
                "display": "flex",
                "gap": "12px",
                "justify-content": "space-between",
            },
        },
        {
            selector: ".data-label",
            declarations: {
                "color": "var(--vscode-descriptionForeground)",
                "font-size": "12px",
                "letter-spacing": "0.08em",
                "text-transform": "uppercase",
            },
        },
        {
            selector: ".data-value",
            declarations: {
                "font-size": "14px",
                "font-weight": "600",
            },
        },
        {
            selector: ".mono-value",
            declarations: {
                "font-family": "var(--vscode-editor-font-family)",
                "font-size": "13px",
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
                "background": "linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent), var(--vscode-editorWidget-background)",
                "border": "1px solid rgba(255, 255, 255, 0.08)",
                "border-radius": "16px",
                "box-shadow": "0 12px 30px rgba(0, 0, 0, 0.12)",
                "padding": "16px",
            },
        },
        {
            selector: ".status-indicator",
            declarations: {
                "border-radius": "50%",
                "display": "inline-block",
                "height": "10px",
                "margin-right": "8px",
                "width": "10px",
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
                "align-items": "center",
                "background": "linear-gradient(135deg, rgba(86, 160, 224, 0.28), rgba(255, 193, 107, 0.12)), var(--vscode-button-background)",
                "border": "1px solid rgba(255, 255, 255, 0.08)",
                "border-radius": "12px",
                "color": "var(--vscode-button-foreground)",
                "cursor": "pointer",
                "display": "inline-flex",
                "font-weight": "600",
                "justify-content": "flex-start",
                "letter-spacing": "0.01em",
                "margin": "0",
                "min-height": "48px",
                "padding": "12px 14px",
                "transition": "transform 120ms ease, border-color 120ms ease, background 120ms ease",
                "width": "100%",
            },
        },
        {
            selector: "button:hover",
            declarations: {
                "background": "linear-gradient(135deg, rgba(96, 182, 242, 0.38), rgba(255, 193, 107, 0.2)), var(--vscode-button-hoverBackground)",
                "border-color": "rgba(255, 255, 255, 0.18)",
                "transform": "translateY(-1px)",
            },
        },
        {
            selector: ".action-grid",
            declarations: {
                "display": "grid",
                "gap": "10px",
                "grid-template-columns": "repeat(auto-fit, minmax(150px, 1fr))",
            },
        },
    ]);
}

export function createMetricsStyles(): string {
    return createStyleBlock([
        ...createBaseBodyRules(20),
        {
            selector: ".metric-grid",
            declarations: {
                "display": "grid",
                "gap": "12px",
                "grid-template-columns": "repeat(auto-fit, minmax(180px, 1fr))",
            },
        },
        {
            selector: ".metric",
            declarations: {
                "background": "linear-gradient(180deg, rgba(255, 255, 255, 0.025), transparent), var(--vscode-editorWidget-background)",
                "border": "1px solid rgba(255, 255, 255, 0.08)",
                "border-radius": "16px",
                "box-shadow": "0 12px 28px rgba(0, 0, 0, 0.12)",
                "display": "grid",
                "gap": "8px",
                "min-height": "110px",
                "padding": "16px",
            },
        },
        {
            selector: ".metric-label",
            declarations: {
                "color": "var(--vscode-descriptionForeground)",
                "font-size": "12px",
                "font-weight": "700",
                "letter-spacing": "0.1em",
                "text-transform": "uppercase",
            },
        },
        {
            selector: ".metric-value",
            declarations: {
                "font-size": "18px",
                "font-weight": "700",
                "line-height": "1.25",
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
        {
            selector: ".audit-log-card",
            declarations: {
                "background": "linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent), var(--vscode-editorWidget-background)",
                "border": "1px solid rgba(255, 255, 255, 0.08)",
                "border-radius": "16px",
                "box-shadow": "0 12px 28px rgba(0, 0, 0, 0.12)",
                "padding": "16px",
            },
        },
        {
            selector: ".audit-log-list",
            declarations: {
                "display": "grid",
                "gap": "10px",
            },
        },
        {
            selector: ".audit-item",
            declarations: {
                "background": "rgba(255, 255, 255, 0.025)",
                "border-radius": "14px",
                "padding": "12px 14px",
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
        {
            selector: ".empty-state",
            declarations: {
                "background": "rgba(255, 255, 255, 0.02)",
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
