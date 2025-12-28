import asyncio
from sqlalchemy import text
from app.adapters.db.session import AsyncSessionLocal

async def check_status():
    run_id = "d5eb320c-2e20-4be7-a8d6-6335535ccbb2"
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT status, results_count, finished_at FROM parsing_runs WHERE run_id = :run_id"),
            {"run_id": run_id}
        )
        row = result.fetchone()
        if row:
            print(f"Status: {row[0]}")
            print(f"Results Count: {row[1]}")
            print(f"Finished At: {row[2]}")
        else:
            print("Not found")

if __name__ == "__main__":
    asyncio.run(check_status())

