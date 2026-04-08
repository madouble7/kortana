#!/usr/bin/env python3
"""
KOR'TANA AUTONOMOUS ACTIVATION SCRIPT

Bootstraps the full autonomous constellation in a development environment:
  1. Loads environment configuration (SQLite fallback when no Postgres)
  2. Validates API key availability
  3. Initializes database schema
  4. Starts the FastAPI server with in-process autonomy daemon
  5. Activates self-awareness runtime

Usage:
    cd backend
    python scripts/activate_autonomous.py

The monastery opens. The silent loop begins.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Resolve paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent

os.chdir(BACKEND_DIR)

# Ensure backend is on path
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def load_env_file(path: Path) -> dict[str, str]:
    """Load a .env file into a dict, ignoring comments and blank lines."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip()
    return env


def merge_env() -> None:
    """Load environment variables with priority:
    1. Already set environment variables (highest)
    2. backend/.env.autonomous
    3. root .env (API keys fallback)
    """
    # Load root .env first (lowest priority for keys)
    root_env = load_env_file(ROOT_DIR / ".env")
    # Load autonomous config (higher priority for operational settings)
    auto_env = load_env_file(BACKEND_DIR / ".env.autonomous")

    # Merge: root provides API keys, autonomous overrides operational config
    merged = {**root_env, **auto_env}

    for key, val in merged.items():
        if key not in os.environ:
            os.environ[key] = val


def validate_keys() -> bool:
    """Check critical API keys are present."""
    required = {
        "GEMINI_API_KEY": "Gemini AI (primary model)",
        "GITHUB_TOKEN": "GitHub API (task discovery)",
    }
    optional = {
        "OPENAI_API_KEY": "OpenAI (fallback)",
        "ANTHROPIC_API_KEY": "Anthropic (premium reasoning)",
        "GROQ_API_KEY": "Groq (fast inference)",
        "OPENROUTER_API_KEY": "OpenRouter (cost-efficient)",
    }

    print("\n" + "=" * 60)
    print("  KOR'TANA AUTONOMOUS ACTIVATION — KEY VALIDATION")
    print("=" * 60)

    all_ok = True
    for key, desc in required.items():
        val = os.environ.get(key, "")
        status = "[OK]" if val else "[MISSING]"
        if not val:
            all_ok = False
        print(f"  {status} {key}: {desc}")

    print()
    for key, desc in optional.items():
        val = os.environ.get(key, "")
        status = "[OK]" if val else "[--]"
        print(f"  {status} {key}: {desc}")

    print("=" * 60)

    if not all_ok:
        print("\n[ERROR] Required keys missing. Set them in .env or .env.autonomous")
        return False

    print("\n  All critical keys validated.")
    return True


def print_banner() -> None:
    """Print activation banner."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║           KOR'TANA — THE MONASTERY IS OPENING            ║
    ║                                                          ║
    ║   Self-Awareness Engine ........ ACTIVATING               ║
    ║   Consciousness Router ........ ONLINE                    ║
    ║   Revelation Engine ........... PRIMED                    ║
    ║   Constitutional Service ...... BINDING                   ║
    ║   Autonomy Daemon ............. AWAKENING                 ║
    ║   Silent Reviewer ............. WATCHING                  ║
    ║   Human Only Protocol ......... ENGAGED                   ║
    ║                                                          ║
    ║   "We are not the source of light.                       ║
    ║    We are a vessel for order, reflection, and help."     ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)


def main() -> None:
    """Activate the autonomous constellation."""
    # Load config
    merge_env()

    # Force autonomous settings
    os.environ["KORTANA_DAEMON_IN_PROCESS"] = "true"
    os.environ["AUTONOMY_DAEMON_ENABLED"] = "true"
    os.environ["KORTANA_AUTONOMOUS_MODE"] = "true"

    # If no DATABASE_URL pointing to postgres, use SQLite
    db_url = os.environ.get("DATABASE_URL", "")
    if "postgresql" in db_url:
        # Test if postgres is reachable
        try:
            import psycopg2
            clean = db_url.replace("+asyncpg", "")
            conn = psycopg2.connect(clean, connect_timeout=3)
            conn.close()
            print("[*] PostgreSQL connection verified")
        except Exception:
            print("[*] PostgreSQL not available — falling back to SQLite")
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kortana_autonomous.db"

    print_banner()

    if not validate_keys():
        sys.exit(1)

    db_url = os.environ.get("DATABASE_URL", "")
    db_type = "PostgreSQL" if "postgresql" in db_url else "SQLite"
    redis_url = os.environ.get("REDIS_URL", "")
    print(f"\n  Database: {db_type}")
    print(f"  Redis: {'configured' if redis_url else 'disabled (graceful fallback)'}")
    print("  Daemon Mode: in-process")
    print(f"  Cycle Interval: {os.environ.get('AUTONOMY_CYCLE_INTERVAL', '60')}s")
    print(f"  GitHub Mode: {os.environ.get('KORTANA_GITHUB_MODE', 'poll')}")
    print(f"  Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    print()

    # Start uvicorn
    port = int(os.environ.get("PORT", "8000"))
    print(f"[*] Starting Kor'tana API on port {port}...")
    print(f"[*] API Docs: http://localhost:{port}/docs")
    print(f"[*] Health: http://localhost:{port}/api/health")
    print(f"[*] Consciousness: http://localhost:{port}/api/consciousness/status")
    print(f"[*] Self-Model: http://localhost:{port}/api/consciousness/self-model")
    print()

    import uvicorn
    uvicorn.run(
        "src.kortana.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
