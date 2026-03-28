# Kor'tana Rate-Limit and Proxy-Trust Observability

## Overview

This dashboard visualizes the behavior of Kor'tana's hardened rate-limit middleware and proxy-trust model. It answers the operational questions:

- Who is being rate-limited?
- Is the proxy path injecting `X-Forwarded-For` correctly?
- Are spoof attempts happening?
- Are any routes being unexpectedly throttled?
- Is the health probe ever impacted?
- Is proxy mode behaving as intended?

It is built around the metric:

```text
kortana_rate_limit_events_total{
    route="...",
    client_ip="...",
    forwarded_ip="...",
    status="limited|allowed|spoof-ignored"
}
```

## Panels

### Panel 1: Rate-Limit Events Over Time

Type: Time series

Query:

```promql
sum by (status) (rate(kortana_rate_limit_events_total[5m]))
```

Interpretation:

- `limited` rising indicates real traffic pressure.
- `spoof-ignored` rising indicates spoof attempts or a misconfigured proxy.
- `allowed` provides the normal-flow baseline.

### Panel 2: Spoof-Ignored Heatmap

Type: Heatmap

Query:

```promql
sum by (forwarded_ip) (rate(kortana_rate_limit_events_total{status="spoof-ignored"}[5m]))
```

Interpretation:

- A single forwarded IP repeating suggests targeted spoofing.
- Many forwarded IPs suggest botnet activity or broad scanning.
- Any non-zero value in staging points to a misconfigured proxy unless generated intentionally during validation.

### Panel 3: Rate-Limited Routes

Type: Bar chart

Query:

```promql
sum by (route) (rate(kortana_rate_limit_events_total{status="limited"}[5m]))
```

Interpretation:

- `/api/gemini/chat` spikes usually indicate heavy LLM usage.
- `/api/info` spikes usually indicate a client bug or runaway polling.
- Any `/api/health` entry is a critical regression.

### Panel 4: Effective Client IP Distribution

Type: Table

Query:

```promql
topk(20, sum by (client_ip) (rate(kortana_rate_limit_events_total[5m])))
```

Interpretation:

- Identifies abusive clients.
- Confirms that forwarded IPs are being resolved correctly.
- Detects proxy-mode misbehavior when all traffic collapses to the proxy IP.

### Panel 5: Proxy-Path Sanity

Type: Table

Query:

```promql
sum by (client_ip, forwarded_ip, status)
    (rate(kortana_rate_limit_events_total[5m]))
```

Interpretation:

- `client_ip == forwarded_ip` usually means direct client traffic.
- `client_ip == proxy_ip` with `forwarded_ip != ""` suggests the proxy path should be examined carefully.
- `status="spoof-ignored"` indicates a spoof attempt or an untrusted proxy.
- `status="limited"` with an unexpected forwarded IP warrants investigation.

## Alerts

### Alert 1: Unexpected Health Endpoint Rate-Limit

Severity: Critical

Query:

```promql
sum(rate(kortana_rate_limit_events_total{route="/api/health"}[2m])) > 0
```

Meaning:

The health probe is being rate-limited. This should never happen.

### Alert 2: Proxy Misconfiguration or Spoof Spike

Severity: High

Query:

```promql
sum(rate(kortana_rate_limit_events_total{status="spoof-ignored"}[5m])) > 5
```

Meaning:

One of these is true:

- The proxy is not in `RATE_LIMIT_TRUSTED_PROXIES`.
- Clients are bypassing the proxy.
- Someone is actively spoofing `X-Forwarded-For`.

### Alert 3: Proxy-Mode Collapse

Severity: High

Query:

```promql
count(count by (client_ip) (rate(kortana_rate_limit_events_total{status!="spoof-ignored"}[5m]))) < 2
```

Meaning:

All traffic is resolving to a single IP, likely the proxy. This indicates:

- `RATE_LIMIT_PROXY_MODE` may be enabled incorrectly.
- The proxy may be stripping `X-Forwarded-For`.
- The load balancer may be misconfigured.

### Alert 4: Sudden Rate-Limit Surge

Severity: Medium

Query:

```promql
sum(rate(kortana_rate_limit_events_total{status="limited"}[5m])) > 20
```

Meaning:

Traffic spike, client bug, or abusive client behavior.

### Alert 5: Missing Forwarded IP When Proxy Should Provide It

Severity: Medium

Query:

```promql
sum(rate(kortana_rate_limit_events_total{forwarded_ip=""}[5m])) > 10
```

Meaning:

The proxy is not injecting `X-Forwarded-For` consistently.

## Operator Notes

- Staging should show zero `spoof-ignored` unless intentionally testing.
- Production should show a stable baseline of `allowed` and occasional `limited`.
- Any `spoof-ignored` in production is worth investigating.
- Any `health` route entry is a red alert.
- Proxy mode should remain off unless the network path is fully controlled.

## Sign-Off Criteria

- [ ] All panels render correctly in staging.
- [ ] Alerts fire under simulated conditions.
- [ ] Proxy-path correctness is visible at a glance.
- [ ] Operators can identify spoof attempts.
- [ ] The health endpoint remains clean.
- [ ] Rate-limit behavior is transparent and predictable.

## Next Artifact

If direct Grafana import is needed later, add a native dashboard JSON export that mirrors these panels and alert rules exactly. Keep the Markdown plan as the operator-readable source of truth.
