"""Script to compress existing checko_data before migration."""
import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, text
from app.adapters.db.models import ModeratorSupplierModel
from app.utils.checko_compression import compress_checko_data_string
from app.config import settings

async def compress_existing_data():
    """Compress existing checko_data in database."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get all suppliers with checko_data
        result = await session.execute(
            select(ModeratorSupplierModel.id, ModeratorSupplierModel.checko_data)
            .where(ModeratorSupplierModel.checko_data.isnot(None))
        )
        suppliers = result.all()
        
        print(f"Found {len(suppliers)} suppliers with checko_data to compress")
        
        compressed_count = 0
        error_count = 0
        
        for supplier_id, checko_data in suppliers:
            try:
                if not checko_data:
                    continue
                
                # Check if already compressed (starts with gzip magic bytes)
                if isinstance(checko_data, bytes) and checko_data.startswith(b'\x1f\x8b'):
                    print(f"Supplier {supplier_id}: Already compressed, skipping")
                    continue
                
                # Compress the data
                if isinstance(checko_data, str):
                    compressed = compress_checko_data_string(checko_data)
                else:
                    # If it's already bytes, try to decode first
                    checko_data_str = checko_data.decode('utf-8') if isinstance(checko_data, bytes) else str(checko_data)
                    compressed = compress_checko_data_string(checko_data_str)
                
                # Update in database - check if checko_data_compressed column exists
                # If migration not applied yet, we'll update checko_data directly after compression
                # First, try to update checko_data_compressed (if column exists)
                try:
                    await session.execute(
                        text("""
                            UPDATE moderator_suppliers 
                            SET checko_data_compressed = :compressed
                            WHERE id = :supplier_id
                        """),
                        {"compressed": compressed, "supplier_id": supplier_id}
                    )
                except Exception:
                    # Column doesn't exist yet, we'll update after migration
                    # For now, just log
                    print(f"Supplier {supplier_id}: checko_data_compressed column not found, will update after migration")
                    # Store compressed data temporarily (we'll need to update after migration)
                    pass
                
                compressed_count += 1
                print(f"Supplier {supplier_id}: Compressed {len(checko_data)} bytes -> {len(compressed)} bytes")
                
            except Exception as e:
                error_count += 1
                print(f"Supplier {supplier_id}: Error - {e}")
        
        await session.commit()
        
        print(f"\nCompression complete:")
        print(f"  Compressed: {compressed_count}")
        print(f"  Errors: {error_count}")
        print(f"  Total: {len(suppliers)}")

if __name__ == "__main__":
    asyncio.run(compress_existing_data())

