"""Comet extraction API router."""

import asyncio
import json
import logging
import os
import subprocess
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.session import get_db
from app.transport.schemas.comet import (
    CometExtractBatchRequestDTO,
    CometExtractBatchResponseDTO,
    CometExtractionResultDTO,
    CometStatusResponseDTO,
    CometManualBatchRequestDTO,
    CometManualResultDTO,
)
from app.usecases import get_parsing_run

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for Comet runs (in production, use Redis or DB)
_comet_runs: Dict[str, Dict] = {}


@router.post("/extract-batch", response_model=CometExtractBatchResponseDTO)
async def start_comet_extract_batch(
    request: CometExtractBatchRequestDTO,
    db: AsyncSession = Depends(get_db)
):
    """Start batch Comet extraction for domains."""
    run_id = request.runId
    domains = request.domains
    
    logger.info(f"=== COMET EXTRACT BATCH REQUEST ===")
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Domains: {domains}")
    logger.info(f"Request object: {request}")
    
    try:
        logger.info(f"Starting Comet extraction for run {run_id}, {len(domains)} domains")
        
        # Verify parsing run exists
        parsing_run = await get_parsing_run.execute(db=db, run_id=run_id)
        if not parsing_run:
            raise HTTPException(status_code=404, detail="Parsing run not found")
        
        # Generate unique Comet run ID
        comet_run_id = f"comet_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Initialize Comet run status
        _comet_runs[comet_run_id] = {
            "runId": run_id,
            "cometRunId": comet_run_id,
            "status": "running",
            "processed": 0,
            "total": len(domains),
            "results": [],
            "domains": domains,
        }
        
        # Start background task to process domains
        # Don't pass db session to background task - it will create its own
        task = asyncio.create_task(_process_comet_batch(comet_run_id, run_id, domains))
        
        # Add error handler for background task
        def task_done_callback(t):
            try:
                t.result()
            except Exception as e:
                logger.error(f"Background task error for {comet_run_id}: {e}", exc_info=True)
        
        task.add_done_callback(task_done_callback)
        
        logger.info(f"Comet batch started: {comet_run_id}")
        
        return CometExtractBatchResponseDTO(
            runId=run_id,
            cometRunId=comet_run_id
        )
        
    except Exception as e:
        logger.error(f"Error in start_comet_extract_batch: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/status/{run_id}", response_model=CometStatusResponseDTO)
async def get_comet_status(
    run_id: str,
    cometRunId: str,
    db: AsyncSession = Depends(get_db)
):
    """Get status of Comet extraction run."""
    
    # Check in-memory storage first
    if cometRunId in _comet_runs:
        run_data = _comet_runs[cometRunId]
        return CometStatusResponseDTO(
            runId=run_data["runId"],
            cometRunId=run_data["cometRunId"],
            status=run_data["status"],
            processed=run_data["processed"],
            total=run_data["total"],
            results=[CometExtractionResultDTO(**r) for r in run_data["results"]]
        )
    
    # If not in memory, check process_log in database
    parsing_run = await get_parsing_run.execute(db=db, run_id=run_id)
    if not parsing_run:
        raise HTTPException(status_code=404, detail="Parsing run not found")
    
    process_log = getattr(parsing_run, 'process_log', None)
    if not process_log:
        raise HTTPException(status_code=404, detail="Comet run not found")
    
    # Parse process_log to find Comet run
    if isinstance(process_log, str):
        try:
            process_log = json.loads(process_log)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid process_log format")
    
    comet_data = process_log.get("comet", {})
    runs = comet_data.get("runs", {})
    
    if cometRunId not in runs:
        raise HTTPException(status_code=404, detail="Comet run not found")
    
    run_data = runs[cometRunId]
    
    return CometStatusResponseDTO(
        runId=run_id,
        cometRunId=cometRunId,
        status=run_data.get("status", "completed"),
        processed=len(run_data.get("results", [])),
        total=len(run_data.get("results", [])),
        results=[CometExtractionResultDTO(**r) for r in run_data.get("results", [])]
    )


@router.post("/manual-batch", response_model=CometExtractBatchResponseDTO)
async def add_manual_comet_results(
    request: CometManualBatchRequestDTO,
    db: AsyncSession = Depends(get_db)
):
    """Manually add Comet results without running assistant (saves limits)."""
    run_id = request.runId
    manual_results = request.results
    
    logger.info(f"=== MANUAL COMET RESULTS ===")
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Manual results: {len(manual_results)} domains")
    
    try:
        # Verify parsing run exists
        parsing_run = await get_parsing_run.execute(db=db, run_id=run_id)
        if not parsing_run:
            raise HTTPException(status_code=404, detail="Parsing run not found")
        
        # Generate unique Comet run ID
        comet_run_id = f"comet_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Convert manual results to standard format
        results = []
        for manual_result in manual_results:
            result = {
                "domain": manual_result.domain,
                "status": "success",
                "inn": manual_result.inn,
                "email": manual_result.email,
                "sourceUrls": manual_result.sourceUrls,
                "error": None
            }
            results.append(result)
        
        # Save directly to database
        await _save_comet_results_to_db(run_id, comet_run_id, results, None)
        
        logger.info(f"Manual Comet results saved: {comet_run_id}")
        
        return CometExtractBatchResponseDTO(
            runId=run_id,
            cometRunId=comet_run_id
        )
        
    except Exception as e:
        logger.error(f"Error in add_manual_comet_results: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def _process_comet_batch(comet_run_id: str, run_id: str, domains: List[str]):
    """Background task to process Comet extraction for multiple domains."""
    logger.info(f"Processing Comet batch {comet_run_id} for {len(domains)} domains")
    
    results = []
    
    for i, domain in enumerate(domains):
        try:
            logger.info(f"Processing domain {i+1}/{len(domains)}: {domain}")
            
            # Run Comet extraction script
            result = await _run_comet_for_domain(domain)
            results.append(result)
            
            # Update in-memory status
            if comet_run_id in _comet_runs:
                _comet_runs[comet_run_id]["processed"] = i + 1
                _comet_runs[comet_run_id]["results"] = results
            
        except Exception as e:
            logger.error(f"Error processing domain {domain}: {e}")
            results.append({
                "domain": domain,
                "status": "error",
                "inn": None,
                "email": None,
                "sourceUrls": [],
                "error": str(e)
            })
    
    # Mark as completed
    if comet_run_id in _comet_runs:
        _comet_runs[comet_run_id]["status"] = "completed"
        _comet_runs[comet_run_id]["processed"] = len(domains)
    
    # Save results to process_log in database (creates its own session)
    await _save_comet_results_to_db(run_id, comet_run_id, results, None)
    
    logger.info(f"Comet batch {comet_run_id} completed: {len(results)} results")


async def _run_comet_for_domain(domain: str) -> Dict:
    """Run Comet extraction script for a single domain."""
    # Get absolute path to project root
    # __file__ is in backend/app/transport/routers/comet.py
    # So we need to go up 4 levels to get to project root
    current_file = os.path.abspath(__file__)
    # backend/app/transport/routers/comet.py -> backend/app/transport/routers -> backend/app/transport -> backend/app -> backend -> project_root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file)))))
    script_path = os.path.join(project_root, "experiments", "comet-integration", "test_single_domain.py")
    
    logger.info(f"Looking for Comet script at: {script_path}")
    
    if not os.path.exists(script_path):
        logger.error(f"Comet script not found: {script_path}")
        return {
            "domain": domain,
            "status": "error",
            "inn": None,
            "email": None,
            "sourceUrls": [],
            "error": f"Comet script not found at {script_path}"
        }
    
    try:
        # Run script with timeout
        # Use sys.executable to get the current Python interpreter
        import sys
        python_exe = sys.executable
        
        logger.info(f"Running Comet script with Python: {python_exe}")
        
        process = await asyncio.create_subprocess_exec(
            python_exe,
            script_path,
            "--domain", domain,
            "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for completion with timeout (3 minutes)
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180)
            
            # Log raw output for debugging
            # Use cp1251 for Windows (Cyrillic) instead of utf-8
            try:
                stdout_str = stdout.decode('utf-8')
            except UnicodeDecodeError:
                stdout_str = stdout.decode('cp1251', errors='ignore')
            
            try:
                stderr_str = stderr.decode('utf-8')
            except UnicodeDecodeError:
                stderr_str = stderr.decode('cp1251', errors='ignore')
            
            logger.info(f"Comet script completed for {domain}")
            logger.info(f"stdout length: {len(stdout_str)} chars")
            logger.info(f"stderr length: {len(stderr_str)} chars")
            
            # Log stderr if present (for debugging)
            if stderr_str:
                logger.warning(f"stderr output: {stderr_str[:500]}")
            
            # Find JSON in stdout (last line should be JSON)
            lines = stdout_str.strip().split('\n')
            json_line = lines[-1] if lines else ""
            
            logger.info(f"Last line (JSON): {json_line[:200]}...")
            
        except asyncio.TimeoutError:
            process.kill()
            logger.error(f"Comet script timeout for domain {domain}")
            return {
                "domain": domain,
                "status": "error",
                "inn": None,
                "email": None,
                "sourceUrls": [],
                "error": "Timeout after 3 minutes"
            }
        
        # Parse JSON output
        try:
            result = json.loads(json_line)
            
            logger.info(f"Parsed Comet result for {domain}: status={result.get('status')}, inn={result.get('inn')}, email={result.get('email')}")
            
            # Ensure all required fields are present
            return {
                "domain": result.get("domain", domain),
                "status": result.get("status", "error"),
                "inn": result.get("inn") or None,  # Convert empty string to None
                "email": result.get("email") or None,  # Convert empty string to None
                "sourceUrls": result.get("source_urls", []),
                "error": result.get("error")
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Comet output for {domain}: {e}")
            logger.error(f"JSON line: {json_line[:500]}")
            return {
                "domain": domain,
                "status": "error",
                "inn": None,
                "email": None,
                "sourceUrls": [],
                "error": f"Failed to parse JSON output: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Error running Comet script for {domain}: {e}")
        return {
            "domain": domain,
            "status": "error",
            "inn": None,
            "email": None,
            "sourceUrls": [],
            "error": str(e)
        }


async def _save_comet_results_to_db(run_id: str, comet_run_id: str, results: List[Dict], db: AsyncSession):
    """Save Comet results to parsing run's process_log."""
    try:
        from app.adapters.db.repositories import ParsingRunRepository
        from app.adapters.db.session import AsyncSessionLocal
        
        # Create a new session to avoid transaction conflicts
        async with AsyncSessionLocal() as new_session:
            try:
                repo = ParsingRunRepository(new_session)
                parsing_run = await repo.get_by_id(run_id)
                
                if not parsing_run:
                    logger.error(f"Parsing run {run_id} not found when saving Comet results")
                    return
                
                # Get existing process_log
                process_log = getattr(parsing_run, 'process_log', None)
                if isinstance(process_log, str):
                    try:
                        process_log = json.loads(process_log)
                    except json.JSONDecodeError:
                        process_log = {}
                elif not process_log:
                    process_log = {}
                
                # Ensure comet structure exists
                if "comet" not in process_log:
                    process_log["comet"] = {"runs": {}}
                if "runs" not in process_log["comet"]:
                    process_log["comet"]["runs"] = {}
                
                # Save Comet run results
                process_log["comet"]["runs"][comet_run_id] = {
                    "status": "completed",
                    "started_at": datetime.now().isoformat(),
                    "finished_at": datetime.now().isoformat(),
                    "results": results
                }
                
                # Update parsing run
                parsing_run.process_log = json.dumps(process_log, ensure_ascii=False)
                await new_session.commit()
                
                logger.info(f"Saved Comet results for run {run_id}, comet_run_id {comet_run_id}")
            except Exception as e:
                logger.error(f"Error in save transaction: {e}")
                await new_session.rollback()
                raise
        
    except Exception as e:
        logger.error(f"Error saving Comet results to DB: {e}")
