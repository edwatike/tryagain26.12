"""Router for parsing runs."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.session import get_db
from app.transport.schemas.parsing import (
    ParsingRunDTO,
    ParsingRunsListResponseDTO,
)
from app.usecases import (
    list_parsing_runs,
    get_parsing_run,
    delete_parsing_run,
)

router = APIRouter()


@router.get("/runs", response_model=ParsingRunsListResponseDTO)
async def list_parsing_runs_endpoint(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    sort: Optional[str] = Query(default="created_at"),
    order: Optional[str] = Query(default="desc"),
    db: AsyncSession = Depends(get_db)
):
    """List parsing runs with pagination, filtering, and sorting."""
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Валидация sort и order
    valid_sort_fields = ["run_id", "status", "created_at", "started_at", "finished_at"]
    if sort not in valid_sort_fields:
        sort = "created_at"
    
    if order not in ["asc", "desc"]:
        order = "desc"
    
    runs, total = await list_parsing_runs.execute(
        db=db,
        limit=limit,
        offset=offset,
        status=status,
        keyword=keyword,
        sort_by=sort,
        sort_order=order
    )
    
    # Convert runs to DTOs, extracting keyword from request
    run_dtos = []
    for run in runs:
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
            
            # Get results_count from run or calculate from domains_queue
            results_count = run.results_count
            if results_count is None:
                # Calculate from domains_queue
                from app.adapters.db.repositories import DomainQueueRepository
                domain_queue_repo = DomainQueueRepository(db)
                _, count = await domain_queue_repo.list(
                    limit=1,
                    offset=0,
                    parsing_run_id=run.run_id
                )
                results_count = count if count > 0 else None
            
            # Create DTO with extracted keyword
            run_dict = {
                "runId": run.run_id,
                "keyword": keyword,
                "status": run.status,
                "startedAt": run.started_at.isoformat() if run.started_at else None,
                "finishedAt": run.finished_at.isoformat() if run.finished_at else None,
                "error": run.error_message,
                "resultsCount": results_count,
                "createdAt": run.created_at.isoformat() if run.created_at else None,
            }
            run_dto = ParsingRunDTO.model_validate(run_dict)
            run_dtos.append(run_dto)
        except Exception as e:
            logger.error(f"Error converting parsing run {run.run_id}: {e}", exc_info=True)
            continue
    
    # Сериализуем DTO с использованием alias для camelCase
    response_data = {
        "runs": [r.model_dump(by_alias=True, mode="json") for r in run_dtos],
        "total": total,
        "limit": limit,
        "offset": offset
    }
    return JSONResponse(content=response_data)


@router.get("/runs/{run_id}", response_model=ParsingRunDTO)
async def get_parsing_run_endpoint(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get parsing run by ID."""
    import json
    import logging
    logger = logging.getLogger(__name__)
    
    run = await get_parsing_run.execute(db=db, run_id=run_id)
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
        
        # Get results_count from run or calculate from domains_queue
        results_count = run.results_count
        if results_count is None:
            # Calculate from domains_queue
            from app.adapters.db.repositories import DomainQueueRepository
            domain_queue_repo = DomainQueueRepository(db)
            _, count = await domain_queue_repo.list(
                limit=1,
                offset=0,
                parsing_run_id=run_id
            )
            results_count = count if count > 0 else None
        
        # Create DTO with extracted keyword
        run_dict = {
            "runId": run.run_id,
            "keyword": keyword,
            "status": run.status,
            "startedAt": run.started_at.isoformat() if run.started_at else None,
            "finishedAt": run.finished_at.isoformat() if run.finished_at else None,
            "error": run.error_message,
            "resultsCount": results_count,
            "createdAt": run.created_at.isoformat() if run.created_at else None,
        }
        return ParsingRunDTO.model_validate(run_dict)
    except Exception as e:
        logger.error(f"Error converting parsing run {run_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing parsing run: {str(e)}")


@router.delete("/runs/{run_id}", status_code=204)
async def delete_parsing_run_endpoint(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete parsing run by ID."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Deleting parsing run: {run_id}")
    
    success = await delete_parsing_run.execute(db=db, run_id=run_id)
    if not success:
        logger.warning(f"Parsing run not found: {run_id}")
        raise HTTPException(status_code=404, detail="Parsing run not found")
    
    try:
        # Log to audit_log
        from app.adapters.audit import log_audit
        await log_audit(
            db=db,
            table_name="parsing_runs",
            operation="DELETE",
            record_id=run_id,
            changed_by="system"
        )
        
        await db.commit()
        logger.info(f"Successfully deleted parsing run: {run_id}")
    except Exception as e:
        logger.error(f"Error deleting parsing run {run_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting parsing run: {str(e)}")


@router.delete("/runs/bulk")
async def bulk_delete_parsing_runs_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Bulk delete parsing runs."""
    import logging
    import json
    
    logger = logging.getLogger(__name__)
    
    # Получаем run_ids из body
    try:
        body = await request.json()
        if isinstance(body, list):
            run_ids = body
        elif isinstance(body, dict) and "run_ids" in body:
            run_ids = body["run_ids"]
        else:
            raise HTTPException(status_code=400, detail="Invalid request body. Expected list of run_ids or {run_ids: [...]}")
        
        if not isinstance(run_ids, list) or len(run_ids) == 0:
            raise HTTPException(status_code=400, detail="run_ids must be a non-empty list")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    
    logger.info(f"Bulk deleting {len(run_ids)} parsing runs")
    
    deleted_count = 0
    errors = []
    
    for run_id in run_ids:
        try:
            success = await delete_parsing_run.execute(db=db, run_id=run_id)
            if success:
                deleted_count += 1
                # Log to audit_log
                from app.adapters.audit import log_audit
                await log_audit(
                    db=db,
                    table_name="parsing_runs",
                    operation="DELETE",
                    record_id=run_id,
                    changed_by="system"
                )
            else:
                errors.append(f"Run {run_id} not found")
        except Exception as e:
            logger.error(f"Error deleting parsing run {run_id}: {e}", exc_info=True)
            errors.append(f"Error deleting {run_id}: {str(e)}")
    
    try:
        await db.commit()
        logger.info(f"Successfully deleted {deleted_count} parsing runs")
        if errors:
            return JSONResponse(
                status_code=207,
                content={
                    "deleted": deleted_count,
                    "errors": errors,
                    "total": len(run_ids)
                }
            )
        return JSONResponse(
            status_code=200,
            content={
                "deleted": deleted_count,
                "total": len(run_ids)
            }
        )
    except Exception as e:
        logger.error(f"Error committing bulk delete: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error bulk deleting parsing runs: {str(e)}")
