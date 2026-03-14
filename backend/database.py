"""
Async database module for Kor'tana Backend
Provides async SQLAlchemy with connection pooling and optimization
"""

import os
import time
from collections.abc import AsyncGenerator

from config import get_settings
from logger import get_logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

logger = get_logger(__name__)


class DatabaseConfig:
    """Database configuration"""

    def __init__(self):
        settings = get_settings()
        self.host = settings.DB_HOST
        self.port = settings.DB_PORT
        self.name = settings.DB_NAME
        self.user = settings.DB_USER
        self.password = settings.DB_PASSWORD
        self.pool_size = int(os.getenv("DB_POOL_SIZE", 20))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", 30))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", 30))
        self.echo = os.getenv("DB_ECHO", "false").lower() == "true"

    def get_url(self) -> str:
        """Get async database URL"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    def get_sync_url(self) -> str:
        """Get sync database URL (for migrations)"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class DatabaseManager:
    """Manages async database connections and sessions"""

    def __init__(self, config: DatabaseConfig | None = None):
        self.config = config or DatabaseConfig()
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker | None = None
        self._connected = False

    async def initialize(self):
        """Initialize database engine and session factory"""
        if self.engine:
            return

        try:
            # Create async engine with connection pooling
            self.engine = create_async_engine(
                self.config.get_url(),
                echo=self.config.echo,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_pre_ping=True,  # Verify connections
                future=True,
            )

            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )

            # Test connection
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                await conn.commit()

            self._connected = True
            logger.info(
                f"Database connected: {self.config.host}:{self.config.port}/{self.config.name} "
                f"(pool: {self.config.pool_size})"
            )

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session"""
        if not self._connected:
            await self.initialize()

        if not self.session_factory:
            raise RuntimeError("Database not initialized")

        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            if not self.engine:
                await self.initialize()

            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def get_stats(self) -> dict:
        """Get database statistics"""
        try:
            async with self.engine.connect():
                # Get connection pool stats
                pool = self.engine.pool
                stats = {
                    "connected": self._connected,
                    "pool_size": pool.size(),
                    "checked_out": pool.checkedout(),
                    "checked_in": pool.checkedin(),
                    "overflow": pool.overflow(),
                }
                return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}

    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            self._connected = False
            logger.info("Database connections closed")


# Global database manager instance
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


# Dependency for FastAPI
async def get_db():
    """FastAPI dependency for database session"""
    db_manager = get_db_manager()
    async for session in db_manager.get_session():
        yield session


# Alias for compatibility with tests
SessionLocal = get_db


class QueryOptimizer:
    """Helper for optimizing database queries"""

    @staticmethod
    def explain_query(session: AsyncSession, query):
        """Get query execution plan"""
        # This would require sync execution for EXPLAIN
        # Implementation depends on specific query needs
        pass

    @staticmethod
    def add_indexes(model, indexes: list):
        """Add indexes to model"""
        # Would be used in models.py
        pass


# Performance monitoring
class QueryMetrics:
    """Track query performance"""

    def __init__(self):
        self.total_queries = 0
        self.slow_queries = 0
        self.total_time = 0.0
        self.errors = 0

    def record_query(self, duration: float, is_slow: bool = False):
        """Record query execution"""
        self.total_queries += 1
        self.total_time += duration
        if is_slow:
            self.slow_queries += 1

    def record_error(self):
        """Record query error"""
        self.errors += 1

    def get_stats(self) -> dict:
        """Get query statistics"""
        avg_time = self.total_time / max(self.total_queries, 1)
        return {
            "total_queries": self.total_queries,
            "slow_queries": self.slow_queries,
            "avg_query_time_ms": round(avg_time * 1000, 2),
            "error_count": self.errors,
            "slow_query_rate": round(
                self.slow_queries / max(self.total_queries, 1) * 100, 2
            ),
        }


# Global query metrics
query_metrics = QueryMetrics()


# Context manager for query timing
class QueryTimer:
    """Context manager to time database queries"""

    def __init__(self, threshold: float = 0.1):
        self.threshold = threshold
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is None:
            return

        duration = time.time() - self.start_time
        is_slow = duration > self.threshold

        if exc_type:
            query_metrics.record_error()
            logger.error(f"Query error: {exc_val}")
        else:
            query_metrics.record_query(duration, is_slow)
            if is_slow:
                logger.warning(f"Slow query detected: {duration:.3f}s")

        return False


# Async context manager
class AsyncQueryTimer:
    """Async context manager to time database queries"""

    def __init__(self, threshold: float = 0.1):
        self.threshold = threshold
        self.start_time = None

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is None:
            return

        duration = time.time() - self.start_time
        is_slow = duration > self.threshold

        if exc_type:
            query_metrics.record_error()
            logger.error(f"Async query error: {exc_val}")
        else:
            query_metrics.record_query(duration, is_slow)
            if is_slow:
                logger.warning(f"Slow async query detected: {duration:.3f}s")

        return False


# Helper functions
async def test_connection():
    """Test database connection"""
    manager = get_db_manager()
    return await manager.health_check()


async def get_connection_stats():
    """Get connection pool statistics"""
    manager = get_db_manager()
    return await manager.get_stats()


async def get_query_stats():
    """Get query performance statistics"""
    return query_metrics.get_stats()


# Migration helper (for alembic)
def get_sync_db_url():
    """Get synchronous database URL for migrations"""
    config = DatabaseConfig()
    return config.get_sync_url()
