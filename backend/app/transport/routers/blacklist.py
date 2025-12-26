"""Router for blacklist."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.session import get_db
from app.transport.schemas.blacklist import (
    BlacklistEntryDTO,
    AddToBlacklistRequestDTO,
    BlacklistResponseDTO,
)
from app.usecases import (
    add_to_blacklist,
    list_blacklist,
    remove_from_blacklist,
)

router = APIRouter()


@router.get("/blacklist", response_model=BlacklistResponseDTO)
async def list_blacklist_endpoint(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List blacklist entries with pagination."""
    entries, total = await list_blacklist.execute(
        db=db,
        limit=limit,
        offset=offset
    )
    
    return BlacklistResponseDTO(
        entries=[BlacklistEntryDTO.model_validate(e) for e in entries],
        total=total,
        limit=limit,
        offset=offset
    )


@router.post("/blacklist", response_model=BlacklistEntryDTO, status_code=201)
async def add_to_blacklist_endpoint(
    request: AddToBlacklistRequestDTO,
    db: AsyncSession = Depends(get_db)
):
    """Add domain to blacklist."""
    blacklist_data = request.model_dump()
    # Convert camelCase to snake_case
    if "addedBy" in blacklist_data:
        blacklist_data["added_by"] = blacklist_data.pop("addedBy")
    if "parsingRunId" in blacklist_data:
        blacklist_data["parsing_run_id"] = blacklist_data.pop("parsingRunId")
    
    entry = await add_to_blacklist.execute(db=db, blacklist_data=blacklist_data)
    await db.commit()
    return BlacklistEntryDTO.model_validate(entry)


@router.delete("/blacklist/{domain}", status_code=204)
async def remove_from_blacklist_endpoint(
    domain: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove domain from blacklist."""
    success = await remove_from_blacklist.execute(db=db, domain=domain)
    if not success:
        raise HTTPException(status_code=404, detail="Domain not found in blacklist")
    
    await db.commit()

