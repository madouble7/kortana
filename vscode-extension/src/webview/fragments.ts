type PanelOptions = {
    body: string;
    className?: string;
    headingLevel?: 1 | 2 | 3 | 4 | 5 | 6;
    title: string;
};

type TextSpanOptions = {
    className?: string;
    id?: string;
    text: string;
};

type StatusLineOptions = {
    contentHtml: string;
    indicatorClassName?: string;
    indicatorId?: string;
    indicatorStyle?: string;
};

type LabeledValueOptions = {
    label: string;
    valueHtml: string;
};

type MetricCardOptions = {
    className?: string;
    label: string;
    valueHtml: string;
};

type ButtonDefinition = {
    id: string;
    label: string;
};

type EmptyStateOptions = {
    className?: string;
    detail?: string;
    title: string;
};

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function renderAttribute(name: string, value?: string): string {
    return value ? ` ${name}="${escapeHtml(value)}"` : "";
}

export function createPanel(options: PanelOptions): string {
    const headingLevel = options.headingLevel ?? 4;
    const className = options.className ?? "panel";

    return `
<div class="${escapeHtml(className)}">
    <h${headingLevel}>${escapeHtml(options.title)}</h${headingLevel}>
    ${options.body}
</div>`;
}

export function createTextSpan(options: TextSpanOptions): string {
    return `<span${renderAttribute("id", options.id)}${renderAttribute("class", options.className)}>${escapeHtml(options.text)}</span>`;
}

export function createStatusLine(options: StatusLineOptions): string {
    const indicatorClassName = options.indicatorClassName ?? "status-indicator";

    return `<p><span class="${escapeHtml(indicatorClassName)}"${renderAttribute("id", options.indicatorId)}${renderAttribute("style", options.indicatorStyle)}></span>${options.contentHtml}</p>`;
}

export function createLabeledValueRow(options: LabeledValueOptions): string {
    return `<p>${escapeHtml(options.label)} ${options.valueHtml}</p>`;
}

export function createMetricCard(options: MetricCardOptions): string {
    const className = options.className ?? "metric";
    return `
<div class="${escapeHtml(className)}">
    <strong>${escapeHtml(options.label)}</strong> ${options.valueHtml}
</div>`;
}

export function createButtonGroup(buttons: ButtonDefinition[]): string {
    return buttons
        .map(
            (button) =>
                `<button id="${escapeHtml(button.id)}">${escapeHtml(button.label)}</button>`
        )
        .join("\n");
}

export function createEmptyStateBlock(options: EmptyStateOptions): string {
    return `
<div class="${escapeHtml(options.className ?? "")}">
    <strong>${escapeHtml(options.title)}</strong>${options.detail ? `<br />
    <small>${escapeHtml(options.detail)}</small>` : ""}
</div>`;
}
