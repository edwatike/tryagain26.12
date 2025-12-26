"""Use case for updating a moderator supplier."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.db.repositories import ModeratorSupplierRepository


async def execute(db: AsyncSession, supplier_id: int, supplier_data: dict):
    """Update moderator supplier."""
    repo = ModeratorSupplierRepository(db)
    return await repo.update(supplier_id, supplier_data)

