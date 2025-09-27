# Kor'tana Auth Mock Prototype

End-to-end miniature of the capability token (short‑lived JWT) pattern for the hybrid integration design.

## Features

- Client credentials style token issuance (`/token`)
- RS256 signing with ephemeral in-memory key(s)
- JWKS discovery (`/jwks.json`)
- Protected endpoint (`/v1/infer`) requiring Bearer token
- Revocation (`/revoke`) via in-memory jti blacklist
- Key rotation simulation (`/secrets/refresh`) supporting soft & hard rotation

## File Map

| File | Purpose |
|------|---------|
| `auth_mock.py` | FastAPI mock auth & protected API service |
| `client.py` | Demonstration client exercising flow, revocation, rotation |
| `README.md` | This guide |

## Install Dependencies

```powershell
python -m pip install fastapi uvicorn pyjwt cryptography requests
```

## Run Server

```powershell
python services\local-api-v2\prototype\auth_mock.py
# Server on http://127.0.0.1:9000
```

## Run Client Demo

```powershell
python services\local-api-v2\prototype\client.py
```

## Environment Overrides (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_MOCK_HOST` | 127.0.0.1 | Bind host |
| `AUTH_MOCK_PORT` | 9000 | Bind port |
| `AUTH_CLIENT_ID` | kortana-node-abc | Client id used by client.py |
| `AUTH_CLIENT_SECRET` | super-secret-local | Client secret |
| `AUTH_CLIENTS_JSON` | (unset) | JSON map of extra clients `{ "id": "secret" }` |

## Flow Diagram (Text)

```
client -> POST /token -> {access_token}
client -> POST /v1/infer (Authorization: Bearer ...) -> { echo + claims }
admin  -> POST /revoke -> { revoked }
admin  -> POST /secrets/refresh (soft) -> add new signing key (old still valid)
admin  -> POST /secrets/refresh (hard) -> replace keys (old tokens invalid)
```

## Example Output (Client)

```
Requesting token...
Got token len: 752
Calling protected infer...
Infer response:
{
  "ok": true,
  "prompt": "Hello from Kor'tana PoC",
  "sub": "kortana-node-abc",
  "scope": "model:invoke sync:write",
  "jti": "...",
  "kid": "...",
  "exp": 1730000000
}
Revoking token and retrying (expect 401)...
Infer unauthorized: {"detail":"revoked_token"}
Soft rotating signing key (old token should remain valid if not revoked)...
Hard rotating signing key (old tokens invalid)...
Old token invalid after hard rotate (expected): 401 Client Error: Unauthorized for url: ...
Final token works after hard rotate:
{
  "ok": true,
  "prompt": "Hello from Kor'tana PoC",
  "sub": "kortana-node-abc",
  "scope": "model:invoke sync:write",
  "jti": "...",
  "kid": "...",
  "exp": 1730000500
}
```

## Hardening Checklist (Next)

- Move signing to KMS or dedicated signing microservice
- Persist revocations + rolling window TTL storage (e.g. Redis) instead of memory
- Add audience (aud) & issuer (iss) validation + structured scopes / capabilities
- Introduce refresh / exchange if needed for long-running sessions
- Add rate limiting & structured audit logging
- Consider detached JWS or payload canonicalization for high-integrity operations

## License

Prototype code – adapt freely within the repository constraints.
Kor'tana Auth PoC
==================

This tiny prototype provides a mock Auth Service that mints short-lived JWTs and a protected API endpoint, plus a client to exercise the flow.

Files
- `auth_mock.py` — FastAPI app that implements `/token` and `/v1/infer` (protected).
- `client.py` — requests a token and calls the protected endpoint.

Requirements
- Python 3.9+
- pip install fastapi uvicorn pyjwt cryptography requests

Run server
```
python services/local-api-v2/prototype/auth_mock.py
```

Run client (in another shell)
```
python services/local-api-v2/prototype/client.py
```

What to expect
- The client will print the token length and the echoed response with token claims.

Notes
- This is a PoC for local testing only. Do not use the in-memory keys/secrets in production.
- Replace the RSA key handling with a proper KMS-backed signing key for production.
