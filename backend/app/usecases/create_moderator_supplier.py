"""Use case for creating a moderator supplier."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.db.repositories import ModeratorSupplierRepository


async def execute(db: AsyncSession, supplier_data: dict):
    """Create a new moderator supplier."""
    repo = ModeratorSupplierRepository(db)
    return await repo.create(supplier_data)

