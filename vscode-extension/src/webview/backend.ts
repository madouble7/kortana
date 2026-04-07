import axios from "axios";

import {
    buildAuditLogPayload,
    buildDashboardStatePayload,
    buildMetricsStatePayload,
    type AuditAction,
    type BackendHealthResponse,
    type BackendSummary,
    type DashboardStatePayload,
    type MetricsDashboardResponse,
    type MetricsStatePayload,
} from "./payloads";

const BACKEND_BASE_URL = "http://localhost:8000";

export async function getDashboardStatePayload(): Promise<DashboardStatePayload> {
    return buildDashboardStatePayload(await getBackendSummary());
}

export async function getMetricsStatePayload(): Promise<MetricsStatePayload> {
    return buildMetricsStatePayload(await getBackendSummary());
}

export async function getAuditLogPayload(): Promise<AuditAction[]> {
    try {
        return buildAuditLogPayload(
            await fetchBackendJson<unknown>("/api/autonomy/actions")
        );
    } catch {
        return [];
    }
}

async function fetchBackendJson<T>(path: string): Promise<T> {
    const response = await axios.get(`${BACKEND_BASE_URL}${path}`);
    return response.data as T;
}

async function getBackendSummary(): Promise<BackendSummary> {
    const [health, metrics] = await Promise.allSettled([
        fetchBackendJson<BackendHealthResponse>("/api/health"),
        fetchBackendJson<MetricsDashboardResponse>("/api/metrics/dashboard"),
    ]);

    return {
        health: health.status === "fulfilled" ? health.value : undefined,
        metrics: metrics.status === "fulfilled" ? metrics.value : undefined,
    };
}
