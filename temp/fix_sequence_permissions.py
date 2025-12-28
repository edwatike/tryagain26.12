import asyncio
from sqlalchemy import text
from app.adapters.db.session import AsyncSessionLocal

async def fix_permissions():
    async with AsyncSessionLocal() as db:
        try:
            # Grant permissions on sequence
            await db.execute(text("GRANT ALL PRIVILEGES ON SEQUENCE domains_queue_id_seq TO postgres"))
            await db.execute(text("GRANT ALL PRIVILEGES ON SEQUENCE domains_queue_id_seq TO PUBLIC"))
            await db.execute(text("ALTER SEQUENCE domains_queue_id_seq OWNER TO postgres"))
            await db.commit()
            print("✅ Permissions granted on domains_queue_id_seq")
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(fix_permissions())

