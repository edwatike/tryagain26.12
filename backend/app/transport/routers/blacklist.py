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


@router.get("/blacklist-debug", tags=["Debug"])
async def debug_blacklist_endpoint(
    db: AsyncSession = Depends(get_db)
):
    """Debug endpoint to check blacklist data directly from database."""
    from app.adapters.db.repositories import BlacklistRepository
    from sqlalchemy import select, func
    from app.adapters.db.models import BlacklistModel
    
    repo = BlacklistRepository(db)
    
    # Получаем данные напрямую
    entries, total = await repo.list(limit=100, offset=0)
    
    # Получаем сырые данные для отладки
    result = await db.execute(select(BlacklistModel))
    raw_entries = result.scalars().all()
    
    # Count query
    count_result = await db.execute(select(func.count()).select_from(BlacklistModel))
    count = count_result.scalar() or 0
    
    return {
        "total_from_repo": total,
        "entries_count_from_repo": len(entries),
        "raw_entries_count": len(raw_entries),
        "count_query": count,
        "raw_entries": [
            {
                "domain": e.domain,
                "reason": e.reason,
                "added_by": e.added_by,
                "added_at": str(e.added_at) if e.added_at else None,
                "parsing_run_id": e.parsing_run_id,
            }
            for e in raw_entries[:10]  # Первые 10 для отладки
        ],
        "repo_entries": [
            {
                "domain": e.domain,
                "reason": e.reason,
                "added_by": e.added_by,
                "added_at": str(e.added_at) if e.added_at else None,
                "parsing_run_id": e.parsing_run_id,
            }
            for e in entries[:10]  # Первые 10 для отладки
        ]
    }


@router.get("/blacklist", response_model=BlacklistResponseDTO)
async def list_blacklist_endpoint(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List blacklist entries with pagination."""
    import logging
    logger = logging.getLogger(__name__)
    
    entries, total = await list_blacklist.execute(
        db=db,
        limit=limit,
        offset=offset
    )
    
    logger.info(f"Blacklist query: found {total} total entries, returning {len(entries)} entries")
    
    # Конвертируем entries в DTO, обрабатывая datetime
    entry_dtos = []
    for e in entries:
        try:
            entry_dict = {
                "domain": e.domain,
                "reason": e.reason,
                "added_by": e.added_by,
                "added_at": e.added_at.isoformat() if e.added_at else None,  # Конвертируем datetime в строку
                "parsing_run_id": e.parsing_run_id,
            }
            entry_dto = BlacklistEntryDTO.model_validate(entry_dict)
            entry_dtos.append(entry_dto)
            logger.debug(f"Converted entry: {e.domain}")
        except Exception as ex:
            logger.error(f"Error converting entry {e.domain}: {ex}")
            # Пропускаем проблемную запись, но продолжаем обработку остальных
            continue
    
    logger.info(f"Returning {len(entry_dtos)} DTOs")
    
    return BlacklistResponseDTO(
        entries=entry_dtos,
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
    import logging
    logger = logging.getLogger(__name__)
    
    # Валидация данных через Pydantic (уже выполнена, но добавим дополнительную проверку)
    blacklist_data = request.model_dump()
    domain = blacklist_data.get("domain", "unknown")
    
    # Дополнительная валидация на уровне endpoint
    if not domain or len(domain.strip()) < 3:
        logger.error(f"Invalid domain format: {domain}")
        raise HTTPException(status_code=400, detail="Invalid domain format")
    
    logger.info(f"Adding domain to blacklist: {domain}")
    
    # Convert camelCase to snake_case
    if "addedBy" in blacklist_data:
        blacklist_data["added_by"] = blacklist_data.pop("addedBy")
    if "parsingRunId" in blacklist_data:
        blacklist_data["parsing_run_id"] = blacklist_data.pop("parsingRunId")
    
    try:
        entry = await add_to_blacklist.execute(db=db, blacklist_data=blacklist_data)
        
        # Логируем в audit_log (перед commit, чтобы быть частью транзакции)
        from app.adapters.audit import log_audit
        await log_audit(
            db=db,
            table_name="blacklist",
            operation="INSERT",
            record_id=entry.domain,
            new_data={
                "domain": entry.domain,
                "reason": entry.reason,
                "added_by": entry.added_by,
                "parsing_run_id": entry.parsing_run_id
            },
            changed_by=entry.added_by or "system"
        )
        
        await db.commit()
        logger.info(f"Successfully added domain to blacklist: {domain} (added_at: {entry.added_at})")
        
        # Конвертируем entry в DTO с правильной обработкой datetime
        entry_dict = {
            "domain": entry.domain,
            "reason": entry.reason,
            "added_by": entry.added_by,
            "added_at": entry.added_at.isoformat() if entry.added_at else None,
            "parsing_run_id": entry.parsing_run_id,
        }
        return BlacklistEntryDTO.model_validate(entry_dict)
    except Exception as e:
        logger.error(f"Error adding domain {domain} to blacklist: {e}", exc_info=True)
        await db.rollback()
        raise


@router.delete("/blacklist/{domain}", status_code=204)
async def remove_from_blacklist_endpoint(
    domain: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove domain from blacklist."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Removing domain from blacklist: {domain}")
    
    try:
        # Получаем данные перед удалением для audit_log
        from app.adapters.db.repositories import BlacklistRepository
        repo = BlacklistRepository(db)
        existing_entry = await repo.get_by_domain(domain)
        
        success = await remove_from_blacklist.execute(db=db, domain=domain)
        if not success:
            logger.warning(f"Domain not found in blacklist: {domain}")
            raise HTTPException(status_code=404, detail="Domain not found in blacklist")
        
        # Логируем в audit_log
        if existing_entry:
            from app.adapters.audit import log_audit
            await log_audit(
                db=db,
                table_name="blacklist",
                operation="DELETE",
                record_id=domain,
                old_data={
                    "domain": existing_entry.domain,
                    "reason": existing_entry.reason,
                    "added_by": existing_entry.added_by,
                    "parsing_run_id": existing_entry.parsing_run_id
                },
                changed_by="system"
            )
        
        await db.commit()
        logger.info(f"Successfully removed domain from blacklist: {domain}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing domain {domain} from blacklist: {e}", exc_info=True)
        await db.rollback()
        raise

