"""Use case for listing domains queue."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.db.repositories import DomainQueueRepository


async def execute(
    db: AsyncSession,
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None
):
    """List domains queue entries with pagination."""
    repo = DomainQueueRepository(db)
    return await repo.list(limit=limit, offset=offset, status=status)

