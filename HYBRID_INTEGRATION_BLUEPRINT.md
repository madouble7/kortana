# Kor'tana Hybrid Local ↔ Cloud Integration Blueprint

Status: Draft (Foundations Phase)
Owner: Platform Architecture
Related Docs: `BLUEPRINT.md` (summary section), `specs/hybrid-auth-sync.openapi.yaml`

## 1. Objectives & Non-Goals

### Objectives

- Provide a secure, revocable identity & delegation model for local (developer or edge) Kor'tana nodes.
- Enable short-lived, minimally scoped capability tokens for model execution, sync, and telemetry submission.
- Support bidirectional state exchange (events + mutable preference docs) with deterministic conflict handling.
- Preserve operation during network partitions with bounded risk and later reconciliation.
- Centralize provider/model routing logic in the cloud while allowing local caching of an approved manifest.
- Establish audit/telemetry contracts that enable cost & anomaly analysis without exposing raw sensitive content.

### Non-Goals (Current Phase)

- Full CRDT-based multi-master editing of large documents.
- End-to-end encryption of all payloads (can be future enhancement).
- Multi-tenant isolation across organizational boundaries (assumed single-tenant / single security domain initial phase).

## 2. Actors

| Actor | Description |
|-------|-------------|
| Local Node | Developer machine or edge runtime process (FastAPI + orchestrator) |
| Cloud Authority (CA) | Enrollment & token signing service (auth microservice) |
| Routing Service | Chooses provider/model chain for execution requests |
| Sync Service | Stores canonical append-only event log + mutable preferences |
| Telemetry Sink | Collects anonymized operational metrics |

## 3. Artifact Schemas

### 3.1 Enrollment Bundle (Signed JSON)

```json
{
  "device_id": "uuidv7",
  "public_key": "base64(ed25519)",
  "scopes": ["sync:read","sync:write","exec:models"],
  "env": "prod|dev",
  "issued_at": 1732740000,
  "expires_at": 1735332000,
  "signature": "base64(ed25519_sig)"
}
```

### 3.2 Capability Token (Ephemeral)

```json
{
  "typ": "kortana.cap",
  "ver": "1",
  "device": "<device_id>",
  "scopes": ["exec:gemini","sync:submit"],
  "route_hints": {"allow_stream": true, "max_model_tier": "standard"},
  "iat": 1732755600,
  "exp": 1732756200,
  "jti": "uuidv7",
  "signature": "base64(ed25519_sig)"
}
```

### 3.3 Routing Manifest

```json
{
  "manifest_id": "uuidv7",
  "issued_at": 1732755600,
  "expires_at": 1732758300,
  "models": [
    {"capability": "chat", "primary": "gemini-pro", "fallbacks": ["gpt-4o-mini","claude-3-haiku"], "max_tokens": 8192},
    {"capability": "embedding", "primary": "text-embedding-3-large", "fallbacks": ["voyage-large"], "dim": 3072}
  ],
  "policy": {"deny_vision": false, "cost_ceiling_usd": 0.25},
  "signature": "base64(ed25519_sig)"
}
```

## 4. Endpoint Surface (Initial Slice)

(Full request/response + error codes in OpenAPI spec.)

| Method | Path | Purpose |
|--------|------|---------|
| POST | /v1/auth/enroll | Register new local device (admin approved) |
| POST | /v1/auth/capability | Issue ephemeral capability token |
| GET  | /v1/auth/revocations | Retrieve revocation digest |
| POST | /v1/auth/manifest | (Phase 2) Get routing manifest |
| POST | /v1/sync/submit | Submit batched append-only + pref patches |
| GET  | /v1/sync/pull | Pull incremental events (cursor) |
| POST | /v1/execute/model | Delegated model execution |
| POST | /v1/telemetry/ingest | (Phase 3) Structured metrics ingestion |

## 5. Sequence Flows

### 5.1 Enrollment

1. Local generates ed25519 keypair.
2. Local POST /v1/auth/enroll {public_key, env, agent_meta} (authenticated by an enrollment token or admin session).
3. Cloud returns signed enrollment bundle.
4. Local stores bundle (secure storage) & retains private key offline.

### 5.2 Capability Token

1. Local builds challenge = SHA256(device_id || minute_epoch || nonce).
2. Signs challenge with private key.
3. POST /v1/auth/capability {device_id, challenge, signature, requested_scopes}.
4. Server validates & returns signed capability token.
5. Local caches until exp - 60s, then refresh.

### 5.3 Sync Submit
1. Local collects events in queue.sqlite.
2. Forms batch: {batch_id, cursor, events[], prefs_patches[] (optional)}.
3. POST /v1/sync/submit with Authorization (cap token).
4. Server validates idempotency (batch_id hash) → appends events → returns new cursor & any merge advisories.

### 5.4 Sync Pull
1. Local GET /v1/sync/pull?after_cursor=XYZ&limit=500.
2. Server returns ordered events + latest preferences snapshot version.

### 5.5 Model Execution
1. Local POST /v1/execute/model {prompt|messages, options} + Authorization.
2. Server chooses route via routing service or manifest guidance (validates hints subset).
3. Streams or returns completion (depending on allow_stream flag).

## 6. Conflict Handling
- **Events**: Identified by (hash(payload), ts, device_seq). Duplicate hash + same device_seq ignored.
- **Preferences**: Vector clock { device_id: counter }. On conflict: server returns 409 with { server_value, client_value, merged_candidate }. Client may accept or re-submit with override flag.
- **Summaries**: Mark stale & recompute rather than merging.

## 7. Offline Strategy
| Aspect | Behavior |
|--------|----------|
| Capability expiry | Enter degraded mode (no remote exec) until refresh possible |
| Event accumulation | Unlimited append until max_local_events (config) then backpressure (drop oldest non-critical) |
| Manifest expiry | Fall back to locally supported providers or queue exec requests |

## 8. Security & Threat Mitigations
| Threat | Mitigation |
|--------|-----------|
| Token theft | Short TTL, scopes minimal, no refresh scope embedded |
| Device key exfiltration | Revocation list + forced re-enrollment path |
| Replay attacks | Nonce + time-bounded challenge, batch_id dedupe |
| Tampered batches | Event hash verification + optional future HMAC per event |
| Routing escalation | Server recomputes final model irrespective of hints |
| Silent revocation | Clients poll revocations + receive 401 device_revoked |

## 9. Telemetry Contract (Phase 2+)
```
{
  "trace_id": "uuidv7",
  "device_id": "...",
  "cap_jti": "...",
  "op": "model.exec|sync.submit",
  "model": "gemini-pro",
  "tokens_in": 123,
  "tokens_out": 456,
  "latency_ms": 842,
  "policy_route": "tier:standard",
  "ts": "2025-09-27T15:42:11.382Z",
  "status": "ok|error",
  "cost_estimate_usd": 0.00042
}
```
Redaction: prompts hashed with rotating salt; full capture requires explicit audit=true flag & elevated scope.

## 10. Revocation Process
1. Admin POST /admin/revoke {device_id, reason}.
2. Server updates revocation set & increments revocation_digest version.
3. GET /v1/auth/revocations returns { version, revoked_devices[], revoked_cap_jtis[], signature }.
4. Clients: if device_id present → disable capability requests & prompt re-enrollment.

## 11. Rollout Phasing (Detailed)
| Phase | Scope | Exit Criteria |
|-------|-------|---------------|
| 1 | Enrollment + capability + model exec (chat only) | ≥1 local node stable 24h |
| 2 | Append-only sync + pull | Event replay deterministic & idempotent |
| 3 | Preferences w/ vector clocks | Conflict resolution accuracy ≥95% test cases |
| 4 | Routing manifest caching + offline degrade | Manifest reuse saves ≥30% route RTT |
| 5 | mTLS + revocation digest + structured telemetry | Revocation propagation <10m |
| 6 | Optional per-event MAC + selective encryption | Performance overhead <5% baseline |

## 12. Open Issues
- Decision: Do we embed model usage quotas inside capability token or fetch separate `/v1/quota`? (Pending cost modeling.)
- Evaluate chunked streaming protocol for >2MB sync batches.
- Potential adoption of JOSE (JWS) vs custom signature framing (trade-off: library support vs minimal bytes).

## 13. Future Enhancements
- Multi-tenant device partitioning (per-tenant CA keys).
- End-to-end encrypted preference subsets (client-hold key).
- Adaptive manifest refresh (server push via WebSocket if available).
- Differential privacy noise injection for telemetry aggregates.

## 14. Appendix: Error Codes (Excerpt)
| Code | HTTP | Meaning |
|------|------|---------|
| device_revoked | 401 | Device revoked – re-enroll required |
| cap_expired | 401 | Capability token expired |
| scope_denied | 403 | Scope not permitted for operation |
| conflict_merge_required | 409 | Preferences conflict; merge cycle needed |
| batch_duplicate | 200 | Batch already applied (idempotent) |

---
This blueprint is versioned; changes require referencing rationale & threat model adjustments.
