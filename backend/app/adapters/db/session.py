"""Database session factory."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.log_sql,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """Dependency for getting database session."""
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                # Commit any pending changes if no exception occurred
                # Note: Individual endpoints should handle their own commits/rollbacks
                # This is a safety net for uncommitted changes
                if session.in_transaction():
                    try:
                        await session.commit()
                    except Exception:
                        await session.rollback()
            finally:
                await session.close()
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_db dependency: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}")
        raise

