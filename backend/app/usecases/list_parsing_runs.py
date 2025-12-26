"""Use case for listing parsing runs."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.db.repositories import ParsingRunRepository


async def execute(db: AsyncSession, limit: int = 100, offset: int = 0):
    """List parsing runs with pagination."""
    repo = ParsingRunRepository(db)
    return await repo.list(limit=limit, offset=offset)

