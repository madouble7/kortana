#!/usr/bin/env python
"""
Comprehensive KOR'TANA System Health Verification
Validates: Database, API, Configuration, Dependencies, HOP Engine
"""

import asyncio
import sys


async def verify_database():
    """Verify SQLite database operational status."""
    try:
        import sqlite3

        conn = sqlite3.connect("kortana.db")
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        conn.close()

        required_tables = {
            "users",
            "agents",
            "tasks",
            "api_keys",
            "audit_logs",
            "github_tasks",
            "agent_executions",
            "memories",
            "alembic_version",
        }
        present = set(tables)

        return {
            "status": "healthy" if required_tables.issubset(present) else "degraded",
            "tables_found": len(tables),
            "tables_required": len(required_tables),
            "missing": required_tables - present,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def verify_configuration():
    """Verify environment configuration loaded correctly."""
    try:
        from src.kortana.config import get_settings

        settings = get_settings()

        checks = {
            "database_url": "sqlite" in settings.DATABASE_URL,
            "environment": settings.ENVIRONMENT == "development",
            "autonomous_mode": settings.AUTONOMOUS_MODE,
            "api_keys_loaded": all(
                [
                    settings.GEMINI_API_KEY,
                    settings.GITHUB_TOKEN,
                    settings.OPENAI_API_KEY,
                    settings.ANTHROPIC_API_KEY,
                ]
            ),
        }

        return {
            "status": "healthy" if all(checks.values()) else "degraded",
            "checks": checks,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def verify_hop_engine():
    """Verify HumanOnlyProtocol classification engine."""
    try:
        from src.kortana.human_only_protocol import HumanOnlyProtocol

        hop = HumanOnlyProtocol()

        # Test known task
        result = hop.classify_task("github_token_rotation", {})

        return {
            "status": "healthy",
            "engine_loaded": True,
            "sample_classification": str(result),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def verify_fastapi_import():
    """Verify FastAPI application can be imported."""
    try:
        from src.kortana.main import app

        return {"status": "healthy", "app_loaded": True, "app_type": type(app).__name__}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def main():
    """Run all verification checks."""
    print("=" * 60)
    print("🔍 KOR'TANA SYSTEM HEALTH VERIFICATION")
    print("=" * 60)

    checks = {
        "Database": await verify_database(),
        "Configuration": await verify_configuration(),
        "HOP Engine": await verify_hop_engine(),
        "FastAPI": await verify_fastapi_import(),
    }

    all_healthy = True
    for check_name, result in checks.items():
        status = result.get("status", "unknown")
        status_symbol = "✅" if status == "healthy" else "❌" if status == "error" else "⚠️"
        all_healthy = all_healthy and (status == "healthy")

        print(f"\n{status_symbol} {check_name}: {status.upper()}")
        for key, value in result.items():
            if key != "status":
                if isinstance(value, dict):
                    for k, v in value.items():
                        print(f"   {k}: {v}")
                elif isinstance(value, set):
                    if value:
                        print(f"   {key}: {value}")
                else:
                    print(f"   {key}: {value}")

    print("\n" + "=" * 60)
    if all_healthy:
        print("🚀 SYSTEM STATUS: ALL SYSTEMS OPERATIONAL")
        print("Ready for autonomous evolution cycles")
    else:
        print("⚠️  SYSTEM STATUS: DEGRADED - REVIEW ABOVE")
    print("=" * 60)

    return 0 if all_healthy else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
