"""Script to check blacklist data in database."""
import asyncio
import sys
import os

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, backend_dir)

from app.adapters.db.session import get_db
from app.adapters.db.repositories import BlacklistRepository
from sqlalchemy import select, func
from app.adapters.db.models import BlacklistModel


async def check_blacklist():
    """Check blacklist data in database."""
    async for db in get_db():
        try:
            repo = BlacklistRepository(db)
            
            # Get data through repository
            entries, total = await repo.list(limit=100, offset=0)
            print(f"Repository query: total={total}, entries={len(entries)}")
            
            # Get raw data directly
            result = await db.execute(select(BlacklistModel))
            raw_entries = result.scalars().all()
            print(f"Direct query: found {len(raw_entries)} entries")
            
            # Count query
            count_result = await db.execute(select(func.count()).select_from(BlacklistModel))
            count = count_result.scalar() or 0
            print(f"Count query: {count} entries")
            
            if raw_entries:
                print("\nFirst 5 entries:")
                for i, e in enumerate(raw_entries[:5], 1):
                    print(f"  {i}. Domain: {e.domain}")
                    print(f"     Reason: {e.reason}")
                    print(f"     Added by: {e.added_by}")
                    print(f"     Added at: {e.added_at}")
                    print(f"     Parsing run ID: {e.parsing_run_id}")
                    print()
            else:
                print("\nNo entries found in database!")
            
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            break


if __name__ == "__main__":
    asyncio.run(check_blacklist())

