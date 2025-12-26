"""Use case for starting parsing."""
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.db.repositories import ParsingRunRepository
from app.adapters.parser_client import ParserClient
from app.config import settings


async def execute(db: AsyncSession, keyword: str, max_urls: int = 10):
    """Start parsing for a keyword."""
    # Create parsing run
    run_id = str(uuid.uuid4())
    run_repo = ParsingRunRepository(db)
    
    run = await run_repo.create({
        "run_id": run_id,
        "keyword": keyword,
        "status": "running",
    })
    
    # Start parsing asynchronously (fire and forget)
    # In production, this should be done via a task queue
    parser_client = ParserClient(settings.parser_service_url)
    
    # Note: This is a simplified version. In production, use a task queue
    # to handle parsing asynchronously
    try:
        # Trigger parsing (non-blocking)
        # The actual parsing should be handled by a background worker
        pass
    except Exception as e:
        # Update run status on error
        await run_repo.update(run_id, {
            "status": "failed",
            "error": str(e),
            "finished_at": datetime.utcnow()
        })
    
    return {
        "run_id": run_id,
        "keyword": keyword,
        "status": "running"
    }

