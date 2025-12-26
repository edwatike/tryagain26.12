"""Router for moderator suppliers."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.session import get_db
from app.config import settings
from app.adapters.db.repositories import ModeratorSupplierRepository
from app.transport.schemas.moderator_suppliers import (
    ModeratorSupplierDTO,
    CreateModeratorSupplierRequestDTO,
    UpdateModeratorSupplierRequestDTO,
    SupplierKeywordsResponseDTO,
    ModeratorSuppliersListResponseDTO,
)
from app.usecases import (
    create_moderator_supplier,
    get_moderator_supplier,
    list_moderator_suppliers,
    update_moderator_supplier,
    delete_moderator_supplier,
    get_supplier_keywords,
)

router = APIRouter()

# Абсолютно минимальный endpoint для проверки
@router.get("/suppliers-empty")
async def suppliers_empty():
    """Absolute minimum endpoint - no parameters, no dependencies."""
    import sys
    print("=== EMPTY ENDPOINT CALLED ===", file=sys.stderr, flush=True)
    return {"ok": True}


@router.get("/suppliers-debug")
async def debug_suppliers():
    """Debug endpoint without dependencies."""
    import sys
    print("=== DEBUG ENDPOINT CALLED ===", file=sys.stderr, flush=True)
    return {"status": "ok", "message": "Debug endpoint works"}

@router.get("/suppliers-minimal")
async def minimal_suppliers():
    """Minimal endpoint without any parameters."""
    import sys
    print("=== MINIMAL ENDPOINT CALLED ===", file=sys.stderr, flush=True)
    return {"status": "ok", "suppliers": []}

@router.get("/suppliers-simple")
async def simple_suppliers():
    """Simple endpoint - absolute minimum."""
    import sys
    print("=== SIMPLE ENDPOINT CALLED ===", file=sys.stderr, flush=True)
    return {"ok": True}

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify router works."""
    import sys
    print("=== TEST ENDPOINT CALLED ===", file=sys.stderr, flush=True)
    return {"status": "ok", "message": "Router works"}

@router.get("/suppliers-test")
async def test_suppliers(db: AsyncSession = Depends(get_db)):
    """Test endpoint with DB dependency."""
    print("=== TEST ENDPOINT CALLED ===")
    try:
        print("=== DB session obtained ===")
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        print(f"=== TEST ERROR: {e} ===")
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


# Временно переименуем endpoint для проверки
@router.get("/suppliers-new")
async def list_suppliers_new(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    supplier_type: Optional[str] = Query(default=None, alias="type"),
):
    """List suppliers - new version for testing."""
    import sys
    try:
        print("=== SUPPLIERS-NEW ENDPOINT CALLED ===", file=sys.stderr, flush=True)
        print(f"=== Parameters: limit={limit}, offset={offset}, type={supplier_type} ===", file=sys.stderr, flush=True)
        
        result = {
            "suppliers": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "status": "test_mode"
        }
        print("=== Returning result ===", file=sys.stderr, flush=True)
        return result
    except Exception as e:
        import traceback
        print(f"=== ENDPOINT EXCEPTION: {type(e).__name__}: {e} ===", file=sys.stderr, flush=True)
        print(f"=== ENDPOINT TRACEBACK:\n{traceback.format_exc()} ===", file=sys.stderr, flush=True)
        raise

# Старый endpoint - ВРЕМЕННО УПРОЩАЕМ ДО МИНИМУМА
@router.get("/suppliers")
async def list_suppliers():
    """List suppliers - ABSOLUTE MINIMUM for testing."""
    import sys
    print("=== SUPPLIERS ENDPOINT CALLED (NO PARAMS) ===", file=sys.stderr, flush=True)
    return {"suppliers": [], "total": 0, "status": "minimal_test"}


@router.get("/suppliers/{supplier_id}", response_model=ModeratorSupplierDTO)
async def get_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get supplier by ID."""
    supplier = await get_moderator_supplier.execute(db=db, supplier_id=supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return ModeratorSupplierDTO.model_validate(supplier)


@router.post("/suppliers", response_model=ModeratorSupplierDTO, status_code=201)
async def create_supplier(
    request: CreateModeratorSupplierRequestDTO,
    db: AsyncSession = Depends(get_db)
):
    """Create a new supplier."""
    supplier = await create_moderator_supplier.execute(
        db=db,
        supplier_data=request.model_dump()
    )
    await db.commit()
    
    return ModeratorSupplierDTO.model_validate(supplier)


@router.put("/suppliers/{supplier_id}", response_model=ModeratorSupplierDTO)
async def update_supplier(
    supplier_id: int,
    request: UpdateModeratorSupplierRequestDTO,
    db: AsyncSession = Depends(get_db)
):
    """Update supplier."""
    # Convert camelCase to snake_case for database fields
    update_data = request.model_dump(exclude_unset=True)
    snake_case_data = {}
    field_mapping = {
        "companyStatus": "company_status",
        "registrationDate": "registration_date",
        "legalAddress": "legal_address",
        "authorizedCapital": "authorized_capital",
        "financeYear": "finance_year",
        "legalCasesCount": "legal_cases_count",
        "legalCasesSum": "legal_cases_sum",
        "legalCasesAsPlaintiff": "legal_cases_as_plaintiff",
        "legalCasesAsDefendant": "legal_cases_as_defendant",
        "checkoData": "checko_data",
    }
    
    for key, value in update_data.items():
        db_key = field_mapping.get(key, key)
        snake_case_data[db_key] = value
    
    supplier = await update_moderator_supplier.execute(
        db=db,
        supplier_id=supplier_id,
        supplier_data=snake_case_data
    )
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    await db.commit()
    return ModeratorSupplierDTO.model_validate(supplier)


@router.delete("/suppliers/{supplier_id}", status_code=204)
async def delete_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete supplier."""
    success = await delete_moderator_supplier.execute(db=db, supplier_id=supplier_id)
    if not success:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    await db.commit()


@router.get("/suppliers/{supplier_id}/keywords", response_model=SupplierKeywordsResponseDTO)
async def get_supplier_keywords_endpoint(
    supplier_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get supplier keywords."""
    keywords = await get_supplier_keywords.execute(db=db, supplier_id=supplier_id)
    return SupplierKeywordsResponseDTO(keywords=keywords)

