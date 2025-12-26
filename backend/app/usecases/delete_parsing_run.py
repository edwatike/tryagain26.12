"""Use case for deleting parsing run."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.db.repositories import ParsingRunRepository


async def execute(db: AsyncSession, run_id: str) -> bool:
    """Delete parsing run by run_id."""
    repo = ParsingRunRepository(db)
    return await repo.delete(run_id)

