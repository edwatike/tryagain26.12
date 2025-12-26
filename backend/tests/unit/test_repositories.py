"""Unit tests for repositories."""
import pytest
from app.adapters.db.repositories import ModeratorSupplierRepository


@pytest.mark.asyncio
async def test_create_supplier(db_session):
    """Test creating a supplier."""
    repo = ModeratorSupplierRepository(db_session)
    supplier = await repo.create({
        "name": "Test Supplier",
        "inn": "1234567890",
        "type": "supplier"
    })
    
    assert supplier.id is not None
    assert supplier.name == "Test Supplier"
    assert supplier.inn == "1234567890"
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_supplier_by_id(db_session):
    """Test getting supplier by ID."""
    repo = ModeratorSupplierRepository(db_session)
    supplier = await repo.create({
        "name": "Test Supplier",
        "type": "supplier"
    })
    await db_session.commit()
    
    found = await repo.get_by_id(supplier.id)
    assert found is not None
    assert found.name == "Test Supplier"

