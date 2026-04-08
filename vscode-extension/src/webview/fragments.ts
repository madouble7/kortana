type PanelOptions = {
    body: string;
    className?: string;
    headingLevel?: 1 | 2 | 3 | 4 | 5 | 6;
    title: string;
};

type HeroSignalOptions = {
    className?: string;
    label: string;
    valueHtml: string;
};

type HeroSectionOptions = {
    className?: string;
    description: string;
    kicker: string;
    signals?: HeroSignalOptions[];
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
    <div class="panel-heading">
        <h${headingLevel} class="panel-title">${escapeHtml(options.title)}</h${headingLevel}>
    </div>
    <div class="panel-body">
        ${options.body}
    </div>
</div>`;
}

export function createHeroSection(options: HeroSectionOptions): string {
    const className = options.className ?? "hero-card";
    const signals =
        options.signals && options.signals.length > 0
            ? `<div class="signal-strip">
${options.signals.map((signal) => createHeroSignal(signal)).join("\n")}
</div>`
            : "";

    return `
<section class="${escapeHtml(className)}">
    <span class="eyebrow">${escapeHtml(options.kicker)}</span>
    <h1 class="hero-title">${escapeHtml(options.title)}</h1>
    <p class="hero-copy">${escapeHtml(options.description)}</p>
    ${signals}
</section>`;
}

export function createTextSpan(options: TextSpanOptions): string {
    return `<span${renderAttribute("id", options.id)}${renderAttribute("class", options.className)}>${escapeHtml(options.text)}</span>`;
}

export function createStatusLine(options: StatusLineOptions): string {
    const indicatorClassName = options.indicatorClassName ?? "status-indicator";

    return `<p><span class="${escapeHtml(indicatorClassName)}"${renderAttribute("id", options.indicatorId)}${renderAttribute("style", options.indicatorStyle)}></span>${options.contentHtml}</p>`;
}

export function createLabeledValueRow(options: LabeledValueOptions): string {
    return `<div class="data-row"><span class="data-label">${escapeHtml(options.label)}</span><span class="data-value">${options.valueHtml}</span></div>`;
}

export function createMetricCard(options: MetricCardOptions): string {
    const className = options.className ?? "metric";
    return `
<div class="${escapeHtml(className)}">
    <span class="metric-label">${escapeHtml(options.label)}</span>
    <div class="metric-value">${options.valueHtml}</div>
</div>`;
}

export function createButtonGroup(buttons: ButtonDefinition[]): string {
    return `<div class="action-grid">
${buttons
    .map(
        (button) =>
            `<button id="${escapeHtml(button.id)}">${escapeHtml(button.label)}</button>`
    )
    .join("\n")}
</div>`;
}

export function createEmptyStateBlock(options: EmptyStateOptions): string {
    return `
<div class="empty-state ${escapeHtml(options.className ?? "")}">
    <strong>${escapeHtml(options.title)}</strong>${options.detail ? `<br />
    <small>${escapeHtml(options.detail)}</small>` : ""}
</div>`;
}

function createHeroSignal(options: HeroSignalOptions): string {
    const className = options.className ? ` signal-chip ${escapeHtml(options.className)}` : " signal-chip";

    return `<div class="${className.trim()}">
    <span class="signal-label">${escapeHtml(options.label)}</span>
    <div class="signal-value">${options.valueHtml}</div>
</div>`;
}
