"""Use case for starting parsing."""
import uuid
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.db.repositories import ParsingRequestRepository, ParsingRunRepository
from app.adapters.parser_client import ParserClient
from app.config import settings


async def execute(db: AsyncSession, keyword: str, depth: int = 10, source: str = "google"):
    """Start parsing for a keyword.
    
    Args:
        db: Database session
        keyword: Keyword to parse
        depth: Number of search result pages to parse (depth)
        source: Source for parsing - "google", "yandex", or "both" (default: "google")
    """
    # Create parsing request first
    request_repo = ParsingRequestRepository(db)
    request = await request_repo.create({
        "title": keyword,
        "raw_keys_json": json.dumps([keyword]),
        "source": source,
    })
    
    # Create parsing run
    run_id = str(uuid.uuid4())
    run_repo = ParsingRunRepository(db)
    
    run = await run_repo.create({
        "run_id": run_id,
        "request_id": request.id,
        "status": "running",
        "source": source,
        "depth": depth,
        "started_at": datetime.utcnow(),
    })
    
    # Start parsing asynchronously
    # Note: In production, this should be done via a task queue (Celery, RQ, etc.)
    # For now, we'll call it directly but it will run asynchronously
    try:
        # Trigger parsing - this will connect to Chrome CDP and start parsing
        # The parsing happens asynchronously, so we don't wait for completion
        import asyncio
        import logging
        logger = logging.getLogger(__name__)
        
        # Start parsing in background task
        async def run_parsing():
            # Create parser client inside background task
            parser_client = ParserClient(settings.parser_service_url)
            
            # Create new database session for background task
            from app.adapters.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as bg_db:
                try:
                    logger.info(f"Starting parsing for keyword: {keyword}, source: {source}, depth: {depth}")
                    try:
                        result = await parser_client.parse(
                            keyword=keyword,
                            depth=depth,
                            source=source
                        )
                        logger.info(f"Parsing completed for run_id: {run_id}, found {result.get('total_found', 0)} suppliers")
                        
                        # Save parsed URLs to domains_queue
                        from app.adapters.db.repositories import DomainQueueRepository
                        domain_queue_repo = DomainQueueRepository(bg_db)
                        
                        suppliers = result.get('suppliers', [])
                        logger.info(f"Processing {len(suppliers)} suppliers for run_id: {run_id}")
                        saved_count = 0
                        errors_count = 0
                        
                        for supplier in suppliers:
                            if supplier.get('source_url'):
                                try:
                                    from urllib.parse import urlparse
                                    parsed_url = urlparse(supplier['source_url'])
                                    domain = parsed_url.netloc.replace("www.", "")
                                    
                                    # Check if domain already exists in queue for this keyword
                                    # Note: We check by domain only, as the same domain can appear for different keywords
                                    existing = await domain_queue_repo.get_by_domain(domain)
                                    if not existing:
                                        await domain_queue_repo.create({
                                            "domain": domain,
                                            "keyword": keyword,
                                            "url": supplier['source_url'],
                                            "parsing_run_id": run_id,
                                            "status": "pending"
                                        })
                                        saved_count += 1
                                    else:
                                        logger.debug(f"Domain {domain} for keyword {keyword} already in queue, skipping.")
                                except Exception as e:
                                    errors_count += 1
                                    logger.warning(f"Error saving domain {supplier.get('source_url')}: {e}", exc_info=True)
                        
                        logger.info(f"Saved {saved_count} domains to queue for run_id: {run_id} (errors: {errors_count})")
                        
                        # Update run status to completed with results_count
                        bg_run_repo = ParsingRunRepository(bg_db)
                        await bg_run_repo.update(run_id, {
                            "status": "completed",
                            "finished_at": datetime.utcnow(),
                            "results_count": saved_count  # Update results_count with saved domains count
                        })
                        await bg_db.commit()
                        logger.info(f"Updated parsing run {run_id} with status=completed, results_count={saved_count}")
                    except Exception as parse_error:
                        # Log parsing error but don't fail the whole task
                        logger.error(f"Error during parsing for run_id {run_id}: {parse_error}", exc_info=True)
                        # Re-raise to be caught by outer exception handler
                        raise
                except Exception as e:
                    import traceback
                    import httpx
                    error_traceback = traceback.format_exc()
                    error_message = str(e)
                    
                    # Extract detailed error message from httpx.HTTPStatusError
                    if isinstance(e, httpx.HTTPStatusError):
                        try:
                            error_data = e.response.json()
                            error_message = error_data.get("detail", error_data.get("message", error_message))
                        except:
                            # If can't parse JSON, use status text
                            error_message = f"HTTP {e.response.status_code}: {e.response.status_text}"
                    elif isinstance(e, httpx.RequestError):
                        # Connection errors (503, connection refused, etc.)
                        error_message = f"Parser Service connection error: {str(e)}. Please ensure Parser Service is running on {settings.parser_service_url}"
                    elif hasattr(e, 'response') and hasattr(e.response, 'json'):
                        try:
                            error_data = e.response.json()
                            error_message = error_data.get("detail", error_data.get("message", error_message))
                        except:
                            pass
                    elif "Failed to connect" in error_message or "connection" in error_message.lower():
                        # Connection-related errors
                        error_message = f"{error_message}. Please ensure Parser Service is running on {settings.parser_service_url}"
                    
                    logger.error(f"Error during parsing for run_id {run_id}: {error_message}\n{error_traceback}")
                    
                    # Update run status on error with detailed message
                    bg_run_repo = ParsingRunRepository(bg_db)
                    # Limit error message length to avoid DB issues
                    error_msg_truncated = error_message[:1000] if len(error_message) > 1000 else error_message
                    await bg_run_repo.update(run_id, {
                        "status": "failed",
                        "error_message": error_msg_truncated,
                        "finished_at": datetime.utcnow()
                    })
                    await bg_db.commit()
                finally:
                    await parser_client.close()
        
        # Start background task (fire and forget)
        asyncio.create_task(run_parsing())
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error starting parsing task for run_id {run_id}: {e}", exc_info=True)
        # Update run status on error
        await run_repo.update(run_id, {
            "status": "failed",
            "error_message": str(e),
            "finished_at": datetime.utcnow()
        })
    
    return {
        "run_id": run_id,
        "keyword": keyword,
        "status": "running"
    }

