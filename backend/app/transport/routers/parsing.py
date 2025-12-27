"""Router for parsing operations."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
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


@router.post("/start", status_code=201)
async def start_parsing_endpoint(
    request: StartParsingRequestDTO,
    db: AsyncSession = Depends(get_db)
):
    """Start parsing for a keyword."""
    # Validate source
    valid_sources = ["google", "yandex", "both"]
    source = request.source.lower() if request.source else "google"
    if source not in valid_sources:
        source = "google"
    
    result = await start_parsing.execute(
        db=db,
        keyword=request.keyword,
        depth=request.depth,
        source=source
    )
    await db.commit()
    
    # Return response with camelCase field names for frontend
    # Using JSONResponse directly to bypass any FastAPI response validation
    return JSONResponse(
        status_code=201,
        content={
            "runId": result["run_id"],
            "keyword": result["keyword"],
            "status": result["status"]
        }
    )


@router.get("/status/{run_id}", response_model=ParsingStatusResponseDTO)
async def get_parsing_status_endpoint(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get parsing status by run ID."""
    import json
    import logging
    from fastapi import HTTPException
    
    logger = logging.getLogger(__name__)
    
    run = await get_parsing_status.execute(db=db, run_id=run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Parsing run not found")
    
    try:
        # Extract keyword from request.title or raw_keys_json
        keyword = "Unknown"
        if run.request:
            if run.request.title:
                keyword = run.request.title
            elif run.request.raw_keys_json:
                try:
                    keys_data = json.loads(run.request.raw_keys_json)
                    if isinstance(keys_data, list) and len(keys_data) > 0:
                        keyword = keys_data[0] if isinstance(keys_data[0], str) else str(keys_data[0])
                    elif isinstance(keys_data, dict) and "keys" in keys_data:
                        keys = keys_data["keys"]
                        if isinstance(keys, list) and len(keys) > 0:
                            keyword = keys[0] if isinstance(keys[0], str) else str(keys[0])
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
        
        # Create DTO with extracted keyword
        # Используем camelCase для соответствия DTO
        status_dict = {
            "runId": run.run_id,  # Используем camelCase для соответствия DTO
            "keyword": keyword,
            "status": run.status,
            "startedAt": run.started_at.isoformat() if run.started_at else None,
            "finishedAt": run.finished_at.isoformat() if run.finished_at else None,
            "error": run.error_message,  # Маппим error_message на error
            "resultsCount": None,  # Можно вычислить из parsing_hits, но пока null
        }
        return ParsingStatusResponseDTO.model_validate(status_dict)
    except Exception as e:
        logger.error(f"Error converting parsing status {run_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing parsing status: {str(e)}")

