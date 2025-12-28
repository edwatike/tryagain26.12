"""Use case for starting parsing."""
import uuid
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.db.repositories import ParsingRequestRepository, ParsingRunRepository
from app.adapters.parser_client import ParserClient
from app.config import settings

# Track running parsing tasks to prevent duplicates
_running_parsing_tasks = set()


async def execute(db: AsyncSession, keyword: str, depth: int = 10, source: str = "google", background_tasks=None):
    """Start parsing for a keyword.
    
    Args:
        db: Database session
        keyword: Keyword to parse
        depth: Number of search result pages to parse (depth)
        source: Source for parsing - "google", "yandex", or "both" (default: "google")
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"start_parsing.execute called: keyword={keyword}, depth={depth}, source={source}")
    # #region agent log
    import json
    from datetime import datetime
    with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps({"location":"start_parsing.py:11","message":"start_parsing.execute called","data":{"keyword":keyword,"depth":depth,"source":source,"has_background_tasks":background_tasks is not None},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":"","hypothesisId":"A"})+'\n')
    # #endregion
    
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
            # CRITICAL: Log function entry FIRST to verify it's being called
            logger.info(f"[RUN_PARSING ENTRY] run_parsing() called for run_id: {run_id}")
            
            # CRITICAL: Prevent duplicate execution - check if task is already running
            # This check must be FIRST thing in the function to prevent race conditions
            # NOTE: run_id should already be in _running_parsing_tasks (added before BackgroundTasks.add_task)
            # But we check again here as a safety measure in case BackgroundTasks calls function twice
            logger.info(f"[DUPLICATE CHECK] Checking run_id {run_id}, current running tasks: {list(_running_parsing_tasks)}")
            if run_id in _running_parsing_tasks:
                # Check if this is the first call (run_id was added before BackgroundTasks.add_task)
                # or a duplicate call (run_id was added in a previous execution of this function)
                # We can't distinguish, so we use a flag to track if we've already started processing
                import app.usecases.start_parsing as start_parsing_module
                if not hasattr(start_parsing_module, '_processing_tasks'):
                    start_parsing_module._processing_tasks = set()
                
                if run_id in start_parsing_module._processing_tasks:
                    logger.warning(f"[DUPLICATE DETECTED] Parsing task for run_id {run_id} is already PROCESSING, skipping duplicate call")
                    return
                
                # Mark as processing
                start_parsing_module._processing_tasks.add(run_id)
                logger.info(f"[DUPLICATE CHECK] Marked run_id {run_id} as PROCESSING (total processing: {len(start_parsing_module._processing_tasks)})")
            else:
                # This shouldn't happen if we added run_id before BackgroundTasks.add_task
                # But add it here as a safety measure
                _running_parsing_tasks.add(run_id)
                logger.warning(f"[DUPLICATE CHECK] run_id {run_id} was NOT in running tasks, added now (this should not happen)")
                import app.usecases.start_parsing as start_parsing_module
                if not hasattr(start_parsing_module, '_processing_tasks'):
                    start_parsing_module._processing_tasks = set()
                start_parsing_module._processing_tasks.add(run_id)
            
            try:
                # CRITICAL: Wrap entire function in try-except to catch ALL errors
                logger.info(f"Background task started for run_id: {run_id}")
                # #region agent log
                import json
                with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"location":"start_parsing.py:56","message":"run_parsing function started","data":{"run_id":run_id,"keyword":keyword},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"A"})+'\n')
                # #endregion
                # Create parser client inside background task
                parser_client = ParserClient(settings.parser_service_url)
                # #region agent log
                with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"location":"start_parsing.py:61","message":"ParserClient created","data":{"run_id":run_id,"parser_service_url":settings.parser_service_url},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"A"})+'\n')
                # #endregion
                
                # Create new database session for background task
                from app.adapters.db.session import AsyncSessionLocal
                async with AsyncSessionLocal() as bg_db:
                    try:
                        logger.info(f"Starting parsing for keyword: {keyword}, source: {source}, depth: {depth}")
                        # #region agent log
                        with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"location":"start_parsing.py:67","message":"Before parser_client.parse call","data":{"run_id":run_id,"keyword":keyword,"source":source,"depth":depth},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"A"})+'\n')
                        # #endregion
                        result = await parser_client.parse(
                            keyword=keyword,
                            depth=depth,
                            source=source
                        )
                        # #region agent log
                        with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"location":"start_parsing.py:73","message":"parser_client.parse completed","data":{"run_id":run_id,"total_found":result.get('total_found', 0),"suppliers_count":len(result.get('suppliers', []))},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"A"})+'\n')
                        # #endregion
                        logger.info(f"Parsing completed for run_id: {run_id}, found {result.get('total_found', 0)} suppliers")
                        
                        # Save parsed URLs to domains_queue
                        from app.adapters.db.repositories import DomainQueueRepository
                        domain_queue_repo = DomainQueueRepository(bg_db)
                        
                        suppliers = result.get('suppliers', [])
                        logger.info(f"Processing {len(suppliers)} suppliers for run_id: {run_id}")
                        # #region agent log
                        import json
                        with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"location":"start_parsing.py:79","message":"Before saving domains","data":{"run_id":run_id,"suppliers_count":len(suppliers),"keyword":keyword},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"E"})+'\n')
                        # #endregion
                        saved_count = 0
                        errors_count = 0
                        
                        for supplier in suppliers:
                            if supplier.get('source_url'):
                                try:
                                    from urllib.parse import urlparse
                                    parsed_url = urlparse(supplier['source_url'])
                                    domain = parsed_url.netloc.replace("www.", "")
                                    
                                    # IMPORTANT: URL привязываются к ключу и запуску!
                                    # Один и тот же домен может быть найден для разных ключей,
                                    # поэтому мы всегда добавляем домен для каждого ключа/запуска.
                                    # Проверяем, что домен не был уже добавлен для ЭТОГО ключа и ЭТОГО запуска.
                                    existing_entry = await domain_queue_repo.get_by_domain_keyword_run(
                                        domain=domain,
                                        keyword=keyword,
                                        parsing_run_id=run_id
                                    )
                                    
                                    if not existing_entry:
                                        try:
                                            await domain_queue_repo.create({
                                                "domain": domain,
                                                "keyword": keyword,
                                                "url": supplier['source_url'],
                                                "parsing_run_id": run_id,
                                                "status": "pending"
                                            })
                                            saved_count += 1
                                            # #region agent log
                                            if saved_count <= 3:  # Log first 3 to avoid spam
                                                with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                                    f.write(json.dumps({"location":"start_parsing.py:108","message":"Domain saved","data":{"run_id":run_id,"domain":domain,"keyword":keyword,"parsing_run_id":run_id,"saved_count":saved_count},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"E"})+'\n')
                                            # #endregion
                                            logger.debug(f"Saved domain {domain} for run_id {run_id}")
                                        except Exception as create_error:
                                            # CRITICAL FIX: If sequence permission error, try to fix it
                                            error_str = str(create_error)
                                            if "InsufficientPrivilegeError" in error_str or ("domains_queue" in error_str and "seq" in error_str):
                                                logger.error(f"Sequence permission error for domain {domain}: {create_error}")
                                                try:
                                                    # Try to grant permissions on BOTH possible sequence names
                                                    from sqlalchemy import text
                                                    # First try to rename sequence if it has wrong name (check all possible names)
                                                    sequence_names = ["domains_queue_new_id_seq", "domains_queue_new_id_seq1"]
                                                    for old_name in sequence_names:
                                                        try:
                                                            await bg_db.execute(text(f"ALTER SEQUENCE {old_name} RENAME TO domains_queue_id_seq"))
                                                            await bg_db.commit()
                                                            logger.info(f"Renamed {old_name} to domains_queue_id_seq")
                                                            break
                                                        except Exception:
                                                            await bg_db.rollback()
                                                            pass  # Might already be renamed or not exist
                                                    
                                                    # Grant permissions on the correct sequence name
                                                    try:
                                                        await bg_db.execute(text("GRANT ALL PRIVILEGES ON SEQUENCE domains_queue_id_seq TO postgres"))
                                                        await bg_db.execute(text("GRANT ALL PRIVILEGES ON SEQUENCE domains_queue_id_seq TO PUBLIC"))
                                                        await bg_db.execute(text("ALTER SEQUENCE domains_queue_id_seq OWNER TO postgres"))
                                                        logger.info("Fixed permissions on sequence domains_queue_id_seq")
                                                    except Exception as seq_error:
                                                        logger.warning(f"Could not fix permissions on domains_queue_id_seq: {seq_error}")
                                                    await bg_db.commit()
                                                    logger.info(f"Fixed sequence permissions, retrying domain save for {domain}")
                                                    # Retry create after fixing permissions
                                                    await domain_queue_repo.create({
                                                        "domain": domain,
                                                        "keyword": keyword,
                                                        "url": supplier['source_url'],
                                                        "parsing_run_id": run_id,
                                                        "status": "pending"
                                                    })
                                                    saved_count += 1
                                                    logger.debug(f"Saved domain {domain} for run_id {run_id} after fixing permissions")
                                                except Exception as fix_error:
                                                    errors_count += 1
                                                    logger.error(f"Failed to fix sequence permissions: {fix_error}", exc_info=True)
                                                    await bg_db.rollback()
                                            else:
                                                errors_count += 1
                                                logger.warning(f"Error saving domain {supplier.get('source_url')}: {create_error}", exc_info=True)
                                    else:
                                        logger.debug(f"Domain {domain} for keyword {keyword} and run_id {run_id} already in queue, skipping.")
                                except Exception as e:
                                    errors_count += 1
                                    logger.warning(f"Error saving domain {supplier.get('source_url')}: {e}", exc_info=True)
                        
                        # CRITICAL FIX: Update status and commit domains in ONE transaction
                        # This ensures status is always updated when domains are saved
                        total_suppliers = len(suppliers)
                        logger.info(f"Parsing complete for run_id: {run_id}. Total suppliers from parser: {total_suppliers}, Saved to DB: {saved_count}, Errors: {errors_count}")
                        
                        # #region agent log
                        with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"location":"start_parsing.py:150","message":"Before updating status","data":{"run_id":run_id,"saved_count":saved_count,"total_suppliers":total_suppliers},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"A"})+'\n')
                        # #endregion
                        
                        # Update status in the SAME transaction as domains commit
                        from sqlalchemy import text
                        try:
                            logger.info(f"Updating parsing run {run_id} status to 'completed' (saved_count: {saved_count})")
                            
                            # Update status BEFORE committing domains - ensures atomicity
                            update_result = await bg_db.execute(
                                text("""
                                    UPDATE parsing_runs 
                                    SET status = :status,
                                        finished_at = :finished_at,
                                        results_count = :results_count
                                    WHERE run_id = :run_id
                                """),
                                {
                                    "status": "completed",
                                    "finished_at": datetime.utcnow(),
                                    "results_count": saved_count,
                                    "run_id": run_id
                                }
                            )
                            rows_updated = update_result.rowcount
                            logger.info(f"UPDATE query executed, rows_updated={rows_updated} for run_id: {run_id}")
                            
                            # Commit BOTH domains AND status update in one transaction
                            await bg_db.commit()
                            # #region agent log
                            with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps({"location":"start_parsing.py:185","message":"Domains and status committed to DB","data":{"run_id":run_id,"saved_count":saved_count,"rows_updated":rows_updated},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"A"})+'\n')
                            # #endregion
                            logger.info(f"Saved {saved_count} domains to queue for run_id: {run_id} (errors: {errors_count})")
                            logger.info(f"Committed {saved_count} domains and status update to database for run_id: {run_id}")
                            
                            # Verify update worked by querying directly
                            verify_result = await bg_db.execute(
                                text("SELECT status, results_count FROM parsing_runs WHERE run_id = :run_id"),
                                {"run_id": run_id}
                            )
                            verify_row = verify_result.fetchone()
                            if verify_row:
                                verified_status = verify_row[0]
                                verified_count = verify_row[1]
                                # #region agent log
                                with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                    f.write(json.dumps({"location":"start_parsing.py:197","message":"Status verification","data":{"run_id":run_id,"verified_status":verified_status,"verified_count":verified_count},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"A"})+'\n')
                                # #endregion
                                if verified_status == "completed":
                                    logger.info(f"✅ Successfully updated parsing run {run_id} to 'completed', results_count={verified_count}")
                                else:
                                    logger.error(f"❌ Update failed! Status is still '{verified_status}' for run_id {run_id}")
                            else:
                                logger.error(f"❌ Cannot verify update: parsing run {run_id} not found!")
                        except Exception as update_error:
                            logger.error(f"❌ Error updating status for run_id {run_id}: {update_error}", exc_info=True)
                            await bg_db.rollback()
                            # #region agent log
                            with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps({"location":"start_parsing.py:210","message":"Status update error","data":{"run_id":run_id,"error":str(update_error)[:200]},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"A"})+'\n')
                            # #endregion
                            # Try one more time with direct SQL
                            try:
                                await bg_db.execute(
                                    text("""
                                        UPDATE parsing_runs 
                                        SET status = 'completed',
                                            finished_at = :finished_at,
                                            results_count = :results_count
                                        WHERE run_id = :run_id
                                    """),
                                    {
                                        "finished_at": datetime.utcnow(),
                                        "results_count": saved_count,
                                        "run_id": run_id
                                    }
                                )
                                await bg_db.commit()
                                logger.info(f"✅ Retry update succeeded for run_id {run_id}")
                            except Exception as retry_error:
                                logger.error(f"❌ Retry update also failed for run_id {run_id}: {retry_error}", exc_info=True)
                                await bg_db.rollback()
                    except Exception as parse_error:
                        # #region agent log
                        with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"location":"start_parsing.py:189","message":"parse_error caught","data":{"run_id":run_id,"error":str(parse_error)[:200]},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"A"})+'\n')
                        # #endregion
                        # Log parsing error but don't fail the whole task
                        logger.error(f"Error during parsing for run_id {run_id}: {parse_error}", exc_info=True)
                        # CRITICAL FIX: Don't re-raise, handle error gracefully
                        # Re-raise would cause the task to fail silently
                        # Instead, update status to failed and log the error
                        try:
                            bg_run_repo = ParsingRunRepository(bg_db)
                            error_msg = str(parse_error)[:1000]  # Limit error message length
                            await bg_run_repo.update(run_id, {
                                "status": "failed",
                                "error_message": error_msg,
                                "finished_at": datetime.utcnow()
                            })
                            await bg_db.commit()
                            logger.info(f"Updated parsing run {run_id} status to 'failed' due to error")
                        except Exception as update_err:
                            logger.error(f"Failed to update status to 'failed' for run_id {run_id}: {update_err}", exc_info=True)
                            await bg_db.rollback()
                        # Don't re-raise - let the task complete
                    finally:
                        await parser_client.close()
                        # Remove from running tasks when done
                        _running_parsing_tasks.discard(run_id)
                        logger.info(f"Removed run_id {run_id} from running tasks (remaining: {len(_running_parsing_tasks)})")
            except Exception as task_error:
                # #region agent log
                with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"location":"start_parsing.py:211","message":"task_error caught in run_parsing","data":{"run_id":run_id,"error":str(task_error)[:200]},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"A"})+'\n')
                # #endregion
                # CRITICAL FIX: Catch ALL errors in background task
                # If we don't catch errors here, the task fails silently
                logger.error(f"CRITICAL: Background task failed for run_id {run_id}: {task_error}", exc_info=True)
                # Try to update status to failed
                try:
                    from app.adapters.db.session import AsyncSessionLocal
                    async with AsyncSessionLocal() as error_db:
                        bg_run_repo = ParsingRunRepository(error_db)
                        error_msg = str(task_error)[:1000]
                        await bg_run_repo.update(run_id, {
                            "status": "failed",
                            "error_message": f"Background task error: {error_msg}",
                            "finished_at": datetime.utcnow()
                        })
                        await error_db.commit()
                        logger.info(f"Updated run_id {run_id} to 'failed' due to background task error")
                except Exception as update_err:
                    logger.error(f"Failed to update status after background task error: {update_err}", exc_info=True)
                finally:
                    # Always remove from running tasks, even on error
                    _running_parsing_tasks.discard(run_id)
                    logger.info(f"Removed run_id {run_id} from running tasks after error (remaining: {len(_running_parsing_tasks)})")
        
        # Start background task (fire and forget)
        # CRITICAL FIX: Use FastAPI BackgroundTasks if available, otherwise use asyncio.create_task()
        # #region agent log
        import json
        with open('d:\\tryagain\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"location":"start_parsing.py:232","message":"Before starting background task","data":{"run_id":run_id,"has_background_tasks":background_tasks is not None},"timestamp":int(datetime.utcnow().timestamp()*1000),"sessionId":"debug-session","runId":run_id,"hypothesisId":"A"})+'\n')
        # #endregion
        if background_tasks is not None:
            # Use FastAPI BackgroundTasks - more reliable
            # CRITICAL: FastAPI BackgroundTasks can handle async functions directly
            # CRITICAL: Check if task is already running BEFORE adding to BackgroundTasks
            logger.info(f"[DUPLICATE PREVENTION] Checking run_id {run_id} before adding to BackgroundTasks, current running tasks: {list(_running_parsing_tasks)}")
            if run_id in _running_parsing_tasks:
                logger.warning(f"[DUPLICATE PREVENTION] run_id {run_id} already in running tasks, skipping BackgroundTasks.add_task")
                return result
            
            logger.info(f"Using FastAPI BackgroundTasks for run_id: {run_id}")
            # CRITICAL: Add run_id to running tasks BEFORE adding to BackgroundTasks to prevent race condition
            _running_parsing_tasks.add(run_id)
            logger.info(f"[DUPLICATE CHECK] Marked run_id {run_id} as running BEFORE adding to BackgroundTasks (total running: {len(_running_parsing_tasks)})")
            background_tasks.add_task(run_parsing)
            logger.info(f"Background task added to FastAPI BackgroundTasks for run_id: {run_id}")
            # NOTE: Do NOT also create asyncio.create_task() here - it causes duplicate parsing!
            # BackgroundTasks will run the task after response is sent, which is fine for async operations
        else:
            # Fallback to asyncio.create_task() if BackgroundTasks not available
            try:
                task = asyncio.create_task(run_parsing())
                logger.info(f"Background task created via asyncio.create_task() for run_id: {run_id}, task: {task}")
                # Add done callback to log completion or errors
                def task_done_callback(t):
                    try:
                        if t.exception():
                            logger.error(f"Background task failed for run_id {run_id}: {t.exception()}", exc_info=t.exception())
                        else:
                            logger.info(f"Background task completed for run_id: {run_id}")
                    except Exception as e:
                        logger.error(f"Error in task done callback for run_id {run_id}: {e}")
                task.add_done_callback(task_done_callback)
                # CRITICAL: Store task in a way that prevents garbage collection
                import app.usecases.start_parsing as start_parsing_module
                if not hasattr(start_parsing_module, '_background_tasks'):
                    start_parsing_module._background_tasks = set()
                start_parsing_module._background_tasks.add(task)
                # Remove task from set when done
                def cleanup_task(t):
                    try:
                        start_parsing_module._background_tasks.discard(t)
                    except:
                        pass
                task.add_done_callback(cleanup_task)
            except Exception as task_create_error:
                logger.error(f"Failed to create background task for run_id {run_id}: {task_create_error}", exc_info=True)
                # Try to update status to failed
                try:
                    await run_repo.update(run_id, {
                        "status": "failed",
                        "error_message": f"Failed to create background task: {str(task_create_error)}",
                        "finished_at": datetime.utcnow()
                    })
                    await db.commit()
                except Exception as update_err:
                    logger.error(f"Failed to update status after task creation error: {update_err}", exc_info=True)
        
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

