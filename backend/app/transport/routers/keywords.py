"""Router for keywords."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.session import get_db
from app.transport.schemas.keywords import (
    KeywordDTO,
    CreateKeywordRequestDTO,
    KeywordsListResponseDTO,
)
from app.usecases import (
    create_keyword,
    list_keywords,
    delete_keyword,
)

router = APIRouter()


@router.get("", response_model=KeywordsListResponseDTO)
async def list_keywords_endpoint(
    db: AsyncSession = Depends(get_db)
):
    """List all keywords."""
    keywords = await list_keywords.execute(db=db)
    return KeywordsListResponseDTO(
        keywords=[KeywordDTO.model_validate(k) for k in keywords]
    )


@router.post("", response_model=KeywordDTO, status_code=201)
async def create_keyword_endpoint(
    request: CreateKeywordRequestDTO,
    db: AsyncSession = Depends(get_db)
):
    """Create a new keyword."""
    keyword = await create_keyword.execute(db=db, keyword=request.keyword)
    await db.commit()
    return KeywordDTO.model_validate(keyword)


@router.delete("/{keyword_id}", status_code=204)
async def delete_keyword_endpoint(
    keyword_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete keyword."""
    success = await delete_keyword.execute(db=db, keyword_id=keyword_id)
    if not success:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    await db.commit()

