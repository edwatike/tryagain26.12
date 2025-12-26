"""Router for parsing runs."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.session import get_db
from app.transport.schemas.parsing import (
    ParsingRunDTO,
    ParsingRunsListResponseDTO,
)
from app.usecases import (
    list_parsing_runs,
    get_parsing_run,
)

router = APIRouter()


@router.get("/runs", response_model=ParsingRunsListResponseDTO)
async def list_parsing_runs_endpoint(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List parsing runs with pagination."""
    runs, total = await list_parsing_runs.execute(
        db=db,
        limit=limit,
        offset=offset
    )
    
    return ParsingRunsListResponseDTO(
        runs=[ParsingRunDTO.model_validate(r) for r in runs],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/runs/{run_id}", response_model=ParsingRunDTO)
async def get_parsing_run_endpoint(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get parsing run by ID."""
    run = await get_parsing_run.execute(db=db, run_id=run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Parsing run not found")
    
    return ParsingRunDTO.model_validate(run)

