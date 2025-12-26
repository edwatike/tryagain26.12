"""Router for domains queue."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.session import get_db
from app.transport.schemas.domain import (
    DomainQueueEntryDTO,
    DomainsQueueResponseDTO,
)
from app.usecases import (
    list_domains_queue,
    remove_from_domains_queue,
)

router = APIRouter()


@router.get("/queue", response_model=DomainsQueueResponseDTO)
async def list_domains_queue_endpoint(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """List domains queue entries with pagination."""
    entries, total = await list_domains_queue.execute(
        db=db,
        limit=limit,
        offset=offset,
        status=status
    )
    
    return DomainsQueueResponseDTO(
        entries=[DomainQueueEntryDTO.model_validate(e) for e in entries],
        total=total,
        limit=limit,
        offset=offset
    )


@router.delete("/queue/{domain}", status_code=204)
async def remove_from_domains_queue_endpoint(
    domain: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove domain from queue."""
    success = await remove_from_domains_queue.execute(db=db, domain=domain)
    if not success:
        raise HTTPException(status_code=404, detail="Domain not found in queue")
    
    await db.commit()

