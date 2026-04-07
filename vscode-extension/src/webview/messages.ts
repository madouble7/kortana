import { DASHBOARD_COMMAND_MAP } from "../commands";
import {
    type AuditAction,
    type DashboardStatePayload,
    type MetricsStatePayload,
} from "./payloads";

export const REQUEST_DASHBOARD_STATE = "requestDashboardState";
export const REQUEST_METRICS_STATE = "requestMetricsState";
export const REQUEST_AUDIT_LOG = "requestAuditLog";
export const RESPONSE_DASHBOARD_STATE = "dashboardState";
export const RESPONSE_METRICS_STATE = "metricsState";
export const RESPONSE_AUDIT_LOG = "auditLog";

export type WebviewCommandMessage = {
    command: string;
};

export type WebviewRequestType =
    | typeof REQUEST_DASHBOARD_STATE
    | typeof REQUEST_METRICS_STATE
    | typeof REQUEST_AUDIT_LOG;

export type WebviewRequestMessage = {
    type: WebviewRequestType;
};

export type WebviewMessage = {
    command?: string;
    type?: string;
};

export type DashboardStateEnvelope = {
    type: typeof RESPONSE_DASHBOARD_STATE;
    payload: DashboardStatePayload;
};

export type MetricsStateEnvelope = {
    type: typeof RESPONSE_METRICS_STATE;
    payload: MetricsStatePayload;
};

export type AuditLogEnvelope = {
    type: typeof RESPONSE_AUDIT_LOG;
    payload: AuditAction[];
};

export type HostResponseEnvelope =
    | DashboardStateEnvelope
    | MetricsStateEnvelope
    | AuditLogEnvelope;

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

export function createCommandMessage(command: string): WebviewCommandMessage {
    return { command };
}

export function createRequestMessage(
    type: WebviewRequestType
): WebviewRequestMessage {
    return { type };
}

export function createDashboardStateEnvelope(
    payload: DashboardStatePayload
): DashboardStateEnvelope {
    return {
        type: RESPONSE_DASHBOARD_STATE,
        payload,
    };
}

export function createMetricsStateEnvelope(
    payload: MetricsStatePayload
): MetricsStateEnvelope {
    return {
        type: RESPONSE_METRICS_STATE,
        payload,
    };
}

export function createAuditLogEnvelope(
    payload: AuditAction[]
): AuditLogEnvelope {
    return {
        type: RESPONSE_AUDIT_LOG,
        payload,
    };
}

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
