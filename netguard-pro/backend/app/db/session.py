"""
NetGuard Pro - Database Layer

Database configuration and session management with:
- Async SQLAlchemy 2.0
- Connection pooling
- Transaction management
- TimescaleDB support for time-series data
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import MetaData, text

from app.config import settings


# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all models."""
    
    metadata = MetaData(naming_convention=convention)
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[Optional[str]]
    updated_at: Mapped[Optional[str]]


# Engine and session factory
engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def init_db_engine() -> None:
    """Initialize database engine and session factory."""
    global engine, async_session_factory
    
    engine = create_async_engine(
        settings.database.async_url,
        pool_size=settings.database.pool_size,
        max_overflow=10,
        pool_timeout=settings.database.pool_timeout,
        pool_pre_ping=True,
        echo=settings.database.echo,
        future=True,
    )
    
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.
    
    Usage in FastAPI endpoints:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    if async_session_factory is None:
        init_db_engine()
    
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of request context.
    
    Usage:
        async with get_db_context() as db:
            users = await db.execute(select(User))
    """
    if async_session_factory is None:
        init_db_engine()
    
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables."""
    if engine is None:
        init_db_engine()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all database tables."""
    if engine is None:
        init_db_engine()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def check_connection() -> bool:
    """Check database connection health."""
    if engine is None:
        init_db_engine()
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False


async def get_database_stats() -> dict:
    """Get database statistics."""
    if engine is None:
        init_db_engine()
    
    stats = {
        "pool_size": 0,
        "checked_out": 0,
        "overflow": 0,
        "invalid": 0,
    }
    
    try:
        async with engine.connect() as conn:
            # Get pool stats
            pool = engine.pool
            stats["pool_size"] = pool.size() if hasattr(pool, 'size') else 0
            stats["checked_out"] = pool.checkedout() if hasattr(pool, 'checkedout') else 0
            stats["overflow"] = pool.overflow() if hasattr(pool, 'overflow') else 0
    except Exception:
        pass
    
    return stats


# Import models to ensure they're registered with Base.metadata
# This should be called after all models are defined
def import_models():
    """Import all models to register them with Base.metadata."""
    from app.models import user, group, policy, tariff, account, traffic_log, audit_log
    # Force import to register models
    _ = user.User
    _ = group.Group
    _ = policy.Policy
    _ = tariff.Tariff
    _ = account.Account
    _ = traffic_log.TrafficLog
    _ = audit_log.AuditLog
