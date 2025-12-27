"""Use case for getting parsing run."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.db.repositories import ParsingRunRepository, DomainQueueRepository


async def execute(db: AsyncSession, run_id: str):
    """Get parsing run by ID."""
    repo = ParsingRunRepository(db)
    run = await repo.get_by_id(run_id)
    
    # If run exists and results_count is None, calculate it from domains_queue
    if run and run.results_count is None:
        domain_queue_repo = DomainQueueRepository(db)
        entries, count = await domain_queue_repo.list(
            limit=1,
            offset=0,
            parsing_run_id=run_id
        )
        # Update results_count if we found domains
        if count > 0:
            await repo.update(run_id, {"results_count": count})
            await db.commit()
            # Refresh run to get updated results_count
            run = await repo.get_by_id(run_id)
    
    return run

