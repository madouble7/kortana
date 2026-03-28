# Kor'tana Staging Validation Plan: Rate-Limit + Proxy-Trust Path

**Purpose:**  
Validate that the actual staging proxy/load-balancer sets and preserves `X-Forwarded-For` correctly, and that Kor'tana's hardened rate-limit middleware behaves exactly as intended under real network conditions.

**Scope:**  
- Proxy trust model
- Forwarded IP resolution
- Spoof-ignored behavior
- Health-check bypass
- Overlimit behavior
- Metrics and logs sanity

**Prereqs:**  
- Staging deployment reachable at `https://staging.kortana.example.com` or your actual staging host
- Access to staging logs
- Ability to set env vars for the staging deployment
- A known staging proxy IP or CIDR, for example `10.0.0.0/24`

## 1. Environment Setup

### 1.1 Set safe defaults

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_PERIOD=60
RATE_LIMIT_PROXY_MODE=false
RATE_LIMIT_TRUSTED_PROXIES=10.0.0.0/24
```

### 1.2 Confirm staging proxy IP

From staging logs or infra docs, confirm the immediate client IP that the backend sees when traffic comes through the proxy.

Example:

```text
10.0.0.12
```

This must fall inside `RATE_LIMIT_TRUSTED_PROXIES`.

## 2. Baseline: Direct Behavior (No XFF)

### 2.1 Send 5 requests to a rate-limited route

```bash
for i in {1..5}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    https://staging.kortana.example.com/api/info
done
```

Expected:
- first 5 -> `200`
- 6th -> `429` with JSON body and rate-limit headers

### 2.2 Verify health bypass

```bash
curl -i https://staging.kortana.example.com/api/health
```

Expected:
- always `200`
- no rate-limit headers

## 3. Proxy-Trusted Path: Real XFF From Proxy

### 3.1 Send requests through the real proxy

Use a single client IP. The proxy should inject the real `X-Forwarded-For`.

```bash
curl -i https://staging.kortana.example.com/api/info
```

Check response headers:
- `X-RateLimit-*` present
- no `spoof-ignored` logs
- effective client IP in logs should match your workstation IP, not the proxy IP

### 3.2 Overlimit through proxy

```bash
for i in {1..6}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    https://staging.kortana.example.com/api/info
done
```

Expected:
- 6th -> `429`
- logs show:
  - `status="limited"`
  - `client_ip="<your workstation IP>"`
  - `immediate_proxy="<proxy IP>"`

## 4. Spoof-Ignored Behavior

### 4.1 Attempt to spoof XFF from an untrusted client

```bash
curl -i \
  -H "X-Forwarded-For: 203.0.113.99" \
  https://staging.kortana.example.com/api/info
```

Expected:
- middleware ignores the spoofed header
- logs show:

```text
status="spoof-ignored"
forwarded_ip="203.0.113.99"
client_ip="<your real IP>"
```

- rate limiting counts against your real IP, not the spoofed one

### 4.2 Overlimit with spoof attempts

```bash
for i in {1..6}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "X-Forwarded-For: 203.0.113.99" \
    https://staging.kortana.example.com/api/info
done
```

Expected:
- 6th -> `429`
- logs show repeated `spoof-ignored`
- metrics increment:
  - `status="spoof-ignored"`
  - `client_ip="<your real IP>"`

## 5. Proxy-Mode Override

### 5.1 Enable proxy mode

```bash
RATE_LIMIT_PROXY_MODE=true
RATE_LIMIT_TRUSTED_PROXIES=""
```

### 5.2 Repeat spoof test

```bash
curl -i \
  -H "X-Forwarded-For: 203.0.113.99" \
  https://staging.kortana.example.com/api/info
```

Expected:
- the forwarded IP is trusted
- effective client IP becomes `203.0.113.99`
- no `spoof-ignored` logs
- overlimit counts against the spoofed IP

This proves proxy mode is a dangerous but intentional override.

## 6. Metrics Validation

Query Prometheus or scrape `/metrics`.

Look for:

```text
kortana_rate_limit_events_total{status="limited"}
kortana_rate_limit_events_total{status="spoof-ignored"}
kortana_rate_limit_events_total{route="/api/info"}
```

Expected:
- counts match your test runs
- `spoof-ignored` only increments when proxy mode is off and spoofing was attempted
- `limited` increments when overlimit is reached

## 7. Log Validation

Search logs for:
- `rate_limit_event`
- `spoof-ignored`
- `limited`
- `client_ip`
- `forwarded_ip`
- `immediate_proxy`

Confirm:
- trusted proxy path shows the correct forwarded IP
- spoof attempts show correct fallback to socket IP
- health endpoint never logs rate-limit events

## 8. Final Sign-Off Criteria

Staging is considered validated when:

- [ ] Proxy injects correct `X-Forwarded-For`
- [ ] Trusted proxy IP matches `RATE_LIMIT_TRUSTED_PROXIES`
- [ ] Spoofed XFF is ignored when proxy mode is off
- [ ] Spoofed XFF is accepted when proxy mode is on
- [ ] Overlimit behavior returns structured `429` JSON
- [ ] Health endpoint bypasses limiter
- [ ] Metrics reflect all events accurately
- [ ] Logs show correct `client_ip`, `forwarded_ip`, `immediate_proxy`, and `status`

Once all boxes are checked, the trust model is confirmed against reality.
