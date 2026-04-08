#!/usr/bin/env python3
"""Setup Alembic migrations for database schema management"""

import os
import subprocess
import sys

try:
    # Compatibility hook for callers and tests that patch the session factory.
    from src.kortana.database import SessionLocal
except Exception:  # pragma: no cover - defensive import for script usage
    SessionLocal = None


def setup_alembic():
    """Initialize Alembic migration system"""

    print("\n" + "=" * 60)
    print("ALEMBIC MIGRATION SETUP")
    print("=" * 60)

    # Check if alembic directory exists
    if os.path.exists("alembic"):
        print("\n[✓] Alembic already initialized")
        return True

    print("\n[1] Initializing Alembic...")
    try:
        result = subprocess.run(
            ["alembic", "init", "alembic"], cwd=".", capture_output=True, text=True
        )

        if result.returncode == 0:
            print("    ✓ Alembic initialized")
        else:
            print(f"    ✗ Error: {result.stderr}")
            return False

    except FileNotFoundError:
        print("    ✗ alembic command not found")
        print("    Install with: pip install alembic")
        return False

    print("\n[2] Updating alembic.ini...")
    alembic_ini = "alembic.ini"

    if os.path.exists(alembic_ini):
        with open(alembic_ini, "r") as f:
            content = f.read()

        # Update sqlalchemy.url
        old_url = "sqlalchemy.url = driver://user:password@localhost/dbname"
        new_url = "sqlalchemy.url = postgresql://postgres:supersecretpassword@localhost:5432/kortana"

        if old_url in content:
            content = content.replace(old_url, new_url)
            with open(alembic_ini, "w") as f:
                f.write(content)
            print("    ✓ alembic.ini updated")
        else:
            print("    ⓘ alembic.ini already configured")

    print("\n[3] Creating initial migration...")
    try:
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", "Initial schema"],
            cwd=".",
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("    ✓ Migration created")
            # Extract migration filename from output
            for line in result.stdout.split("\n"):
                if "Generating" in line:
                    print(f"    {line.strip()}")
        else:
            print(f"    ⓘ {result.stderr}")

    except FileNotFoundError:
        print("    ⚠ Could not auto-generate migration")
        print("    Will need to be done after database setup")

    print("\n" + "=" * 60)
    print("MIGRATION WORKFLOW")
    print("=" * 60)
    print(
        """
[1] When PostgreSQL is running, execute migration:
    alembic upgrade head

[2] To create new schema changes:
    Make changes to models.py
    alembic revision --autogenerate -m "describe change"
    alembic upgrade head

[3] To downgrade:
    alembic downgrade -1

[4] View migration history:
    alembic current
    alembic history
    """
    )

    return True


async def setup_migrations() -> bool:
    """Async wrapper for migration setup.

    The migration bootstrap remains CLI-driven, but we keep the database session
    factory importable here so async callers and tests can patch it consistently
    with the rest of the backend.
    """
    return setup_alembic()


if __name__ == "__main__":
    if setup_alembic():
        print("\n✓ Alembic setup complete!")
        print("  Ready to run migrations when PostgreSQL is available")
    else:
        print("\n✗ Alembic setup failed")
        sys.exit(1)
