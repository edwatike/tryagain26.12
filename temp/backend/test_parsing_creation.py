"""Test script to check parsing creation."""
import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.adapters.db.models import ParsingRequestModel, ParsingRunModel
from app.adapters.db.repositories import ParsingRequestRepository, ParsingRunRepository
from app.adapters.db.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession


async def test_creation():
    """Test creating parsing request and run."""
    async for session in get_async_session():
        try:
            # Test ParsingRequestModel
            print("Testing ParsingRequestModel...")
            request_repo = ParsingRequestRepository(session)
            request = await request_repo.create({
                "title": "test keyword",
                "raw_keys_json": '["test keyword"]',
                "source": "google",
            })
            print(f"✓ ParsingRequest created: id={request.id}, title={request.title}")
            
            # Test ParsingRunModel
            print("Testing ParsingRunModel...")
            run_repo = ParsingRunRepository(session)
            import uuid
            from datetime import datetime
            run = await run_repo.create({
                "run_id": str(uuid.uuid4()),
                "request_id": request.id,
                "status": "running",
                "source": "google",
                "started_at": datetime.utcnow(),
            })
            print(f"✓ ParsingRun created: run_id={run.run_id}, status={run.status}")
            
            # Test with keyword (should be filtered out)
            print("Testing ParsingRunModel with invalid 'keyword' field...")
            run2 = await run_repo.create({
                "run_id": str(uuid.uuid4()),
                "request_id": request.id,
                "status": "running",
                "source": "google",
                "keyword": "test",  # This should be filtered out
            })
            print(f"✓ ParsingRun created with filtered keyword: run_id={run2.run_id}")
            
            await session.rollback()  # Don't commit test data
            print("\n✅ All tests passed!")
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            return False
        finally:
            break


if __name__ == "__main__":
    result = asyncio.run(test_creation())
    sys.exit(0 if result else 1)



















