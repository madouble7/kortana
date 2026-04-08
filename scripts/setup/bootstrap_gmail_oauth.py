"""Bootstrap a Gmail OAuth refresh token for Kor'tana."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root containing backend/src/kortana.",
    )
    parser.add_argument(
        "--redirect-uri",
        default=None,
        help="Override GOOGLE_REDIRECT_URI for this authorization flow.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Print the consent URL without opening the system browser.",
    )
    parser.add_argument(
        "--write-env",
        action="store_true",
        help="Write the resulting GOOGLE_REFRESH_TOKEN into the repo-root .env file.",
    )
    return parser.parse_args()


def _extract_code(raw_input: str) -> str:
    value = raw_input.strip()
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme and parsed.netloc:
        query = urllib.parse.parse_qs(parsed.query)
        code = query.get("code", [None])[0]
        if code:
            return code
    return value


def _upsert_env_value(env_path: Path, key: str, value: str) -> None:
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    updated = False
    for index, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[index] = f"{key}={value}"
            updated = True
            break

    if not updated:
        lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    repo_root = args.repo_root.resolve()
    backend_root = repo_root / "backend"
    sys.path.insert(0, str(backend_root))

    from src.kortana.config import get_settings

    settings = get_settings()
    redirect_uri = args.redirect_uri or settings.GOOGLE_REDIRECT_URI
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET

    if not client_id or not client_secret:
        print(
            "[error] GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set before "
            "running Gmail OAuth bootstrap."
        )
        return 1

    state = secrets.token_urlsafe(24)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "scope": " ".join(settings.GMAIL_SCOPES),
        "state": state,
    }
    consent_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
        params
    )

    print("[info] Open this URL and authorize madouble7@gmail.com:")
    print(consent_url)
    if not args.no_browser:
        webbrowser.open(consent_url)

    raw_code = input(
        "\nPaste the full redirected URL or the `code` query parameter here:\n> "
    ).strip()
    code = _extract_code(raw_code)
    if not code:
        print("[error] No authorization code provided.")
        return 1

    token_request = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=urllib.parse.urlencode(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(token_request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"[error] Google token exchange failed: {exc}")
        return 1

    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        print("[error] Google did not return a refresh token.")
        print(
            "[hint] Re-run with prompt=consent, or revoke the existing app grant in "
            "your Google account before retrying."
        )
        print(json.dumps(payload, indent=2))
        return 1

    print("\n[ok] Gmail refresh token acquired.")
    print(f"GOOGLE_REFRESH_TOKEN={refresh_token}")
    print(f"GMAIL_SCOPES={','.join(settings.GMAIL_SCOPES)}")

    if args.write_env:
        env_path = repo_root / ".env"
        _upsert_env_value(env_path, "GOOGLE_REFRESH_TOKEN", str(refresh_token))
        _upsert_env_value(env_path, "GMAIL_SCOPES", ",".join(settings.GMAIL_SCOPES))
        print(f"[ok] Updated {env_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
