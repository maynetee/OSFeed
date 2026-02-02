from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
from app.config import get_settings
import os
import logging
import asyncio

logger = logging.getLogger(__name__)
settings = get_settings()


def create_engine_for_database():
    """Create the appropriate async engine based on database configuration."""
    if settings.use_sqlite:
        # SQLite configuration (for local development and testing)
        is_memory = ":memory:" in settings.database_url
        if not is_memory:
            os.makedirs("data", exist_ok=True)
        logger.info("Using SQLite database for local development")
        engine_kwargs = dict(
            echo=settings.app_debug,
            future=True,
            connect_args={
                "check_same_thread": False,
            },
        )
        if is_memory:
            # In-memory SQLite needs StaticPool so all connections share
            # the same database (otherwise each connection gets its own).
            engine_kwargs["poolclass"] = StaticPool
        else:
            engine_kwargs["connect_args"]["timeout"] = 30
        return create_async_engine(settings.database_url, **engine_kwargs)
    else:
        # PostgreSQL configuration (production)
        logger.info(f"Connecting to PostgreSQL at {settings.postgres_host}:{settings.postgres_port}")
        return create_async_engine(
            settings.database_url,
            echo=settings.app_debug,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=settings.db_pool_recycle,
        )


# Lazy engine initialization
_engine = None


def get_engine():
    """Get or create the database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        _engine = create_engine_for_database()

        # SQLite-specific pragmas (only applied when using SQLite)
        if settings.use_sqlite:
            is_memory = ":memory:" in settings.database_url

            @event.listens_for(_engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                if not is_memory:
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA busy_timeout=30000")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()

    return _engine


# Session maker cache for lazy initialization
_session_maker = None


def _get_session_maker():
    """Get or create the async session maker (lazy initialization)."""
    global _session_maker
    if _session_maker is None:
        _session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_maker


# Backward-compatible alias for AsyncSessionLocal (used by many modules)
def AsyncSessionLocal():
    """Get a new async session (lazy initialization).

    Usage: async with AsyncSessionLocal() as session: ...
    """
    return _get_session_maker()()


# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency to get database session."""
    session_maker = _get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables with retry logic.

    Note: In production with PostgreSQL, prefer using Alembic migrations.
    This function is kept for development and initial setup.
    """
    max_retries = 5
    base_delay = 2

    for attempt in range(max_retries):
        try:
            engine = get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables initialized")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Database initialization failed after {max_retries} attempts: {e}")
                raise
