"""Router for parsing operations."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.session import get_db
from app.transport.schemas.parsing import (
    StartParsingRequestDTO,
    StartParsingResponseDTO,
    ParsingStatusResponseDTO,
)
from app.usecases import (
    start_parsing,
    get_parsing_status,
)

router = APIRouter()


@router.post("/start", response_model=StartParsingResponseDTO, status_code=201)
async def start_parsing_endpoint(
    request: StartParsingRequestDTO,
    db: AsyncSession = Depends(get_db)
):
    """Start parsing for a keyword."""
    result = await start_parsing.execute(
        db=db,
        keyword=request.keyword,
        max_urls=request.maxUrls
    )
    await db.commit()
    
    return StartParsingResponseDTO(
        runId=result["run_id"],
        keyword=result["keyword"],
        status=result["status"]
    )


@router.get("/status/{run_id}", response_model=ParsingStatusResponseDTO)
async def get_parsing_status_endpoint(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get parsing status by run ID."""
    status = await get_parsing_status.execute(db=db, run_id=run_id)
    if not status:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Parsing run not found")
    
    return ParsingStatusResponseDTO.model_validate(status)

