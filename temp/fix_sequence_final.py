import asyncio
from sqlalchemy import text
from app.adapters.db.session import AsyncSessionLocal

async def fix_sequence():
    async with AsyncSessionLocal() as db:
        try:
            # Try to rename sequence
            try:
                await db.execute(text("ALTER SEQUENCE domains_queue_new_id_seq RENAME TO domains_queue_id_seq"))
                await db.commit()
                print("✅ Renamed domains_queue_new_id_seq to domains_queue_id_seq")
            except Exception as e:
                await db.rollback()
                print(f"⚠️ Could not rename (might already be renamed): {e}")
            
            # Grant permissions
            try:
                await db.execute(text("GRANT ALL PRIVILEGES ON SEQUENCE domains_queue_id_seq TO postgres"))
                await db.execute(text("GRANT ALL PRIVILEGES ON SEQUENCE domains_queue_id_seq TO PUBLIC"))
                await db.execute(text("ALTER SEQUENCE domains_queue_id_seq OWNER TO postgres"))
                await db.commit()
                print("✅ Fixed permissions on domains_queue_id_seq")
            except Exception as e:
                await db.rollback()
                print(f"❌ Error fixing permissions: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_sequence())

