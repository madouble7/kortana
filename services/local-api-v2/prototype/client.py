"""Minimal client exercising the mock auth flow.

Steps:
1. POST /token with client credentials -> receive JWT
2. POST /v1/infer with Bearer token -> receive echo w/claims
3. (Optional) POST /revoke then retry infer to demonstrate revocation
4. (Optional) POST /secrets/refresh to rotate signing key

Run: python services/local-api-v2/prototype/client.py
"""

from __future__ import annotations

import json
import os
from typing import Any, cast
import requests


BASE = os.getenv("AUTH_MOCK_BASE", "http://127.0.0.1:9000")
CLIENT_ID = os.getenv("AUTH_CLIENT_ID", "kortana-node-abc")
CLIENT_SECRET = os.getenv("AUTH_CLIENT_SECRET", "super-secret-local")


def request_token(scope: str = "model:invoke sync:write", ttl_seconds: int = 300) -> dict[str, Any]:
    r = requests.post(
        f"{BASE}/token",
        json={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": scope,
            "ttl_seconds": ttl_seconds,
        },
        timeout=10,
    )
    r.raise_for_status()
    return cast(dict[str, Any], r.json())


def call_infer(token: str, prompt: str = "Hello from Kor'tana PoC") -> dict[str, Any]:
    r = requests.post(
        f"{BASE}/v1/infer",
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt": prompt},
        timeout=10,
    )
    if r.status_code == 401:
        print("Infer unauthorized:", r.text)
    r.raise_for_status()
    return cast(dict[str, Any], r.json())


def revoke(jti: str):
    r = requests.post(f"{BASE}/revoke", json={"jti": jti}, timeout=5)
    r.raise_for_status()
    return r.json()


def rotate(hard: bool = False):
    r = requests.post(f"{BASE}/secrets/refresh", json={"hard": hard}, timeout=5)
    r.raise_for_status()
    return r.json()


def main():  # pragma: no cover - demo
    print("Requesting token...")
    token_resp = request_token()
    token = token_resp["access_token"]
    print("Got token len:", len(token))
    print("Claims (header snippet):", token.split(".")[0][:32], "...")

    print("Calling protected infer...")
    infer_resp = call_infer(token)
    print("Infer response:")
    print(json.dumps(infer_resp, indent=2))

    # Demonstrate revocation
    print("Revoking token and retrying (expect 401)...")
    revoke(infer_resp["jti"])
    try:
        call_infer(token)
    except Exception as e:  # broad for demo
        print("As expected, call after revocation failed:", e)

    # Soft rotate: old token should still verify
    print("Soft rotating signing key (old token should remain valid if not revoked)...")
    rotate(hard=False)
    # Request a new token post-rotation
    new_token = request_token()["access_token"]
    print("New token len:", len(new_token))

    # Hard rotate: new keys only (old token invalid)
    print("Hard rotating signing key (old tokens invalid)...")
    rotate(hard=True)
    try:
        call_infer(new_token)
    except Exception as e:  # old key removed
        print("Old token invalid after hard rotate (expected):", e)

    final_token = request_token()["access_token"]
    print("Final token works after hard rotate:")
    print(json.dumps(call_infer(final_token), indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
