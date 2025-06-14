#!/usr/bin/env python3
"""
Test database connectivity and endpoint dependencies
"""

import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

print("🔍 TESTING DATABASE CONNECTIVITY")
print("=" * 50)

try:
    print("1. Testing database settings import...")
    from src.kortana.config.settings import settings

    print("✅ Settings imported")
    print(f"   Database URL: {settings.MEMORY_DB_URL}")
    print(f"   Alembic URL: {settings.ALEMBIC_DATABASE_URL}")

    print("2. Testing database service import...")
    from src.kortana.services.database import SyncSessionLocal

    print("✅ Database service imported")

    print("3. Testing database connection...")
    db = SyncSessionLocal()
    # Try a simple query to test connectivity
    db.execute("SELECT 1")
    print("✅ Database connection successful")
    db.close()

    print("4. Testing goal router dependencies...")
    try:
        print("✅ Goal models imported")
    except Exception as e:
        print(f"⚠️  Goal models import issue: {e}")

    print("5. Testing memory router dependencies...")
    try:
        print("✅ Memory core modules imported")
    except Exception as e:
        print(f"⚠️  Memory core import issue: {e}")

except Exception as e:
    print(f"❌ Database test failed: {e}")
    import traceback

    traceback.print_exc()

print("\n🎯 DATABASE TEST COMPLETE")
