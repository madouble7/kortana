import { DASHBOARD_COMMAND_MAP } from "../commands";

export const REQUEST_DASHBOARD_STATE = "requestDashboardState";
export const REQUEST_METRICS_STATE = "requestMetricsState";
export const REQUEST_AUDIT_LOG = "requestAuditLog";

export type WebviewMessage = {
    command?: string;
    type?: string;
};

export type ResolvedWebviewMessage =
    | { kind: "command"; command: string }
    | { kind: "dashboardState" }
    | { kind: "metricsState" }
    | { kind: "auditLog" };

const REQUEST_KIND_MAP: Record<string, ResolvedWebviewMessage["kind"]> = {
    [REQUEST_DASHBOARD_STATE]: "dashboardState",
    [REQUEST_METRICS_STATE]: "metricsState",
    [REQUEST_AUDIT_LOG]: "auditLog",
};

export function resolveDashboardCommand(
    message: WebviewMessage
): string | undefined {
    const candidate = message.command?.trim();

    if (!candidate) {
        return undefined;
    }

    return DASHBOARD_COMMAND_MAP[candidate];
}

export function resolveWebviewMessage(
    message: WebviewMessage
): ResolvedWebviewMessage | undefined {
    const type = message.type?.trim();

    if (type) {
        switch (REQUEST_KIND_MAP[type]) {
            case "dashboardState":
                return { kind: "dashboardState" };
            case "metricsState":
                return { kind: "metricsState" };
            case "auditLog":
                return { kind: "auditLog" };
        }
    }

    const command = resolveDashboardCommand(message);
    if (!command) {
        return undefined;
    }

    return { kind: "command", command };
}
