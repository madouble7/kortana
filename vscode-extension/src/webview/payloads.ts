export type BackendHealthResponse = {
    message?: unknown;
};

export type MetricsDashboardResponse = {
    completed_tasks?: unknown;
    tasks_processed?: unknown;
    last_deployment?: unknown;
    last_sync?: unknown;
};

export type BackendSummary = {
    health?: BackendHealthResponse;
    metrics?: MetricsDashboardResponse;
};

export type DashboardStatePayload = {
    backendOnline: boolean;
    backendMessage: string;
    tasksCount: string;
    lastSync: string;
};

export type MetricsStatePayload = {
    backendOnline: boolean;
    backendMessage: string;
    lastDeployment: string;
    tasksCount: string;
};

export type AuditAction = {
    type: string;
    description: string;
    timestamp: string;
    status: string;
};

export function buildDashboardStatePayload(
    summary: BackendSummary
): DashboardStatePayload {
    return {
        backendOnline: Boolean(summary.health),
        backendMessage: toDisplayValue(summary.health?.message, "Offline"),
        tasksCount: toDisplayValue(
            summary.metrics?.tasks_processed ?? summary.metrics?.completed_tasks,
            "-"
        ),
        lastSync: toDisplayValue(
            summary.metrics?.last_sync ?? summary.metrics?.last_deployment,
            "N/A"
        ),
    };
}

export function buildMetricsStatePayload(
    summary: BackendSummary
): MetricsStatePayload {
    return {
        backendOnline: Boolean(summary.health),
        backendMessage: toDisplayValue(summary.health?.message, "Offline"),
        lastDeployment: toDisplayValue(
            summary.metrics?.last_deployment ?? summary.metrics?.last_sync,
            "N/A"
        ),
        tasksCount: toDisplayValue(summary.metrics?.completed_tasks, "0"),
    };
}

export function buildAuditLogPayload(actions: unknown): AuditAction[] {
    if (!Array.isArray(actions)) {
        return [];
    }

    return actions.map((action) => {
        const record =
            action && typeof action === "object"
                ? (action as Record<string, unknown>)
                : {};

        return {
            type: toDisplayValue(record.type, "Action"),
            description: toDisplayValue(record.description, "No details"),
            timestamp: toDisplayValue(record.timestamp, ""),
            status: toDisplayValue(record.status, "pending"),
        };
    });
}

function toDisplayValue(value: unknown, fallback: string): string {
    if (value === undefined || value === null || value === "") {
        return fallback;
    }

    return String(value);
}
