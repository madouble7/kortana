import asyncio
import sys

from sqlalchemy import text

# Add src to path
sys.path.append("src")

from kortana.database import get_db_manager


async def test_db():
    print("Initializing DatabaseManager...")
    manager = get_db_manager()
    try:
        await manager.initialize()
        print("Manager initialized.")

        async for db in manager.get_session():
            print("Session acquired. Executing SELECT 1...")
            result = await db.execute(text("SELECT 1"))
            row = result.all()
            print(f"Result: {row}")
            break
    except Exception as e:
        print(f"Error during DB test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_db())
