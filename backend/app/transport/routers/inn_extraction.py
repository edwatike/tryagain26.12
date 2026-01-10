"""Router for INN extraction."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.session import get_db
from app.transport.schemas.inn_extraction import (
    ExtractINNBatchRequestDTO,
    ExtractINNBatchResponseDTO,
)
from app.usecases.extract_inn_batch import execute

router = APIRouter()


@router.post("/extract-batch", response_model=ExtractINNBatchResponseDTO)
async def extract_inn_batch_endpoint(
    request: ExtractINNBatchRequestDTO,
    db: AsyncSession = Depends(get_db)
):
    """Extract INN for multiple domains in parallel.
    
    Args:
        request: Request with list of domains
        db: Database session
        
    Returns:
        Response with extraction results for each domain
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not request.domains:
        raise HTTPException(status_code=400, detail="At least one domain is required")
    
    if len(request.domains) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 domains allowed per request")
    
    try:
        logger.info(f"Received INN extraction request for {len(request.domains)} domains: {request.domains}")
        result = await execute(db=db, domains=request.domains)
        logger.info(f"INN extraction completed: processed={result.get('processed')}, successful={result.get('successful', 0)}, failed={result.get('failed', 0)}")
        return ExtractINNBatchResponseDTO(**result)
    except Exception as e:
        logger.error(f"Error in extract_inn_batch_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to extract INN: {str(e)}")

