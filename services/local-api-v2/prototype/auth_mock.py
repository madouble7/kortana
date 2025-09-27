"""Mock Auth & Protected API Service

Purpose
-------
Lightweight FastAPI service to prototype the short‑lived JWT capability token
flow described in the hybrid auth blueprint. Provides:

Endpoints
---------
POST /token
    Client credentials style exchange -> short‑lived RS256 JWT (default 5m)
GET /jwks.json
    JWKS (public keys) for verification (rotated keys retained until hard rotate)
POST /v1/infer
    Protected endpoint requiring valid bearer token; echoes prompt & claims
POST /revoke
    (Admin) revoke a token by jti (adds to in‑memory blacklist)
POST /secrets/refresh
    Simulate signing key rotation (soft: add new key, keep old; hard: replace)

NOT FOR PRODUCTION. In production replace in‑memory state with durable stores,
use KMS/HSM for signing, and authenticated admin endpoints.
"""

from __future__ import annotations

import base64
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any

import jwt  # PyJWT
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI, HTTPException, Header
from jwt import PyJWTError
from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    grant_type: str = Field("client_credentials", pattern="client_credentials")
    client_id: str
    client_secret: str
    scope: str | None = Field(default="model:invoke sync:write")
    ttl_seconds: int | None = Field(default=300, ge=60, le=3600)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str
    issued_at: int
    kid: str


class InferRequest(BaseModel):
    prompt: str = Field(..., max_length=4000)


class RevokeRequest(BaseModel):
    jti: str


class RefreshRequest(BaseModel):
    hard: bool = False


app = FastAPI(title="Kor'tana Auth Mock", version="0.1.0")


# ----------------------------------------------------------------------------------
# In-memory state (NOT production safe)
# ----------------------------------------------------------------------------------
ALLOWED_CLIENTS: dict[str, str] = {
    # id: secret (override via env: AUTH_CLIENTS_JSON = {"id":"secret"...})
    "kortana-node-abc": "super-secret-local"
}

if os.getenv("AUTH_CLIENTS_JSON"):
    try:
        ALLOWED_CLIENTS.update(json.loads(os.getenv("AUTH_CLIENTS_JSON", "{}")))
    except json.JSONDecodeError:  # pragma: no cover - dev convenience
        pass

KEYS: list[dict[str, Any]] = []  # each: {kid, private_key_obj, public_pem, public_jwk}
CURRENT_KID: str | None = None
REVOKED_JTIS: set[str] = set()


def _generate_rsa_keypair() -> dict[str, Any]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    e = public_numbers.e
    n = public_numbers.n
    # Convert to base64url without padding per JWK spec
    def b64u(val: int) -> str:
        byte_length = (val.bit_length() + 7) // 8
        return base64.urlsafe_b64encode(val.to_bytes(byte_length, "big")).rstrip(b"=").decode()

    kid = uuid.uuid4().hex[:16]
    public_jwk = {
        "kty": "RSA",
        "alg": "RS256",
        "use": "sig",
        "kid": kid,
        "n": b64u(n),
        "e": b64u(e),
    }
    public_pem = public_key.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    return {
        "kid": kid,
        "private": private_key,
        "public_pem": public_pem,
        "public_jwk": public_jwk,
    }


def _ensure_initial_key():
    global CURRENT_KID
    if not KEYS:
        key = _generate_rsa_keypair()
        KEYS.append(key)
        CURRENT_KID = key["kid"]


_ensure_initial_key()


# ----------------------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------------------
def _get_current_key() -> dict[str, Any]:
    for k in KEYS:
        if k["kid"] == CURRENT_KID:
            return k
    raise RuntimeError("Current signing key not found")


def _find_key(kid: str) -> dict[str, Any] | None:
    return next((k for k in KEYS if k["kid"] == kid), None)


def _issue_token(data: TokenRequest) -> TokenResponse:
    if ALLOWED_CLIENTS.get(data.client_id) != data.client_secret:
        raise HTTPException(status_code=401, detail="invalid_client")

    key = _get_current_key()
    now = datetime.now(datetime.UTC)
    ttl = data.ttl_seconds or 300
    exp = now + timedelta(seconds=ttl)
    jti = uuid.uuid4().hex
    claims = {
        "iss": "kortana-auth-mock",
        "sub": data.client_id,
        "scope": data.scope or "",
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": jti,
    }
    private_key = key["private"]
    token = jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": key["kid"]})
    return TokenResponse(
        access_token=token,
        expires_in=ttl,
        scope=claims["scope"],
        issued_at=claims["iat"],
        kid=key["kid"],
    )


def _verify_token(auth_header: str | None) -> dict[str, Any]:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing_authorization")
    token = auth_header.split(" ", 1)[1].strip()
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")
    key = _find_key(kid) if kid else None
    if not key:
        raise HTTPException(status_code=401, detail="unknown_kid")
    public_key = key["public_pem"]
    try:
        claims = jwt.decode(token, public_key, algorithms=["RS256"], options={"require": ["exp", "iat", "sub"]})
    except PyJWTError as e:  # broad but fine for PoC
        raise HTTPException(status_code=401, detail=f"invalid_token: {e}") from None
    if claims.get("jti") in REVOKED_JTIS:
        raise HTTPException(status_code=401, detail="revoked_token")
    return claims


# ----------------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------------
@app.post("/token", response_model=TokenResponse)
def create_token(req: TokenRequest):
    return _issue_token(req)


@app.get("/jwks.json")
def jwks():
    return {"keys": [k["public_jwk"] for k in KEYS]}


@app.post("/v1/infer")
def infer(req: InferRequest, authorization: str | None = Header(default=None)):
    claims = _verify_token(authorization)
    return {
        "ok": True,
        "prompt": req.prompt,
        "sub": claims.get("sub"),
        "scope": claims.get("scope"),
        "jti": claims.get("jti"),
        "kid": claims.get("kid"),
        "exp": claims.get("exp"),
    }


@app.post("/revoke")
def revoke(req: RevokeRequest):
    REVOKED_JTIS.add(req.jti)
    return {"revoked": True, "jti": req.jti, "count": len(REVOKED_JTIS)}


@app.post("/secrets/refresh")
def refresh(req: RefreshRequest):
    global CURRENT_KID
    new_key = _generate_rsa_keypair()
    if req.hard:
        # Hard rotate: discard old keys (revoking previous tokens implicitly)
        KEYS.clear()
        KEYS.append(new_key)
    else:
        KEYS.append(new_key)
    CURRENT_KID = new_key["kid"]
    return {"rotated": True, "hard": req.hard, "current_kid": CURRENT_KID, "key_count": len(KEYS)}


@app.get("/healthz")
def health():
    return {"status": "ok", "kid": CURRENT_KID, "keys": len(KEYS), "revoked": len(REVOKED_JTIS)}


# ----------------------------------------------------------------------------------
# Local dev entrypoint
# ----------------------------------------------------------------------------------
def _main():  # pragma: no cover - convenience
    import uvicorn

    host = os.getenv("AUTH_MOCK_HOST", "127.0.0.1")
    port = int(os.getenv("AUTH_MOCK_PORT", "9000"))
    uvicorn.run("services.local-api-v2.prototype.auth_mock:app", host=host, port=port, reload=False)


if __name__ == "__main__":  # pragma: no cover
    _main()
