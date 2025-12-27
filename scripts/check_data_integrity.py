"""Script to check data integrity in the database."""
import asyncio
import sys
import os

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_dir)

from app.adapters.db.session import get_db
from sqlalchemy import text, select, func
from app.adapters.db.models import (
    ModeratorSupplierModel,
    BlacklistModel,
    ParsingRunModel,
    DomainQueueModel
)
from sqlalchemy import Table, Column, Integer, ForeignKey


async def check_integrity():
    """Check data integrity in the database."""
    issues = []
    
    async for db in get_db():
        try:
            print("Checking data integrity...\n")
            
            # Check suppliers
            result = await db.execute(select(func.count()).select_from(ModeratorSupplierModel))
            supplier_count = result.scalar() or 0
            print(f"✓ Suppliers: {supplier_count}")
            
            # Check for suppliers without name
            result = await db.execute(
                select(func.count()).select_from(ModeratorSupplierModel).where(
                    ModeratorSupplierModel.name.is_(None) | (ModeratorSupplierModel.name == "")
                )
            )
            invalid_suppliers = result.scalar() or 0
            if invalid_suppliers > 0:
                issues.append(f"⚠ Found {invalid_suppliers} suppliers without name")
            
            # Check keywords (using raw SQL since we don't have KeywordModel imported)
            result = await db.execute(text("SELECT COUNT(*) FROM keywords"))
            keyword_count = result.scalar() or 0
            print(f"✓ Keywords: {keyword_count}")
            
            # Check blacklist
            result = await db.execute(select(func.count()).select_from(BlacklistModel))
            blacklist_count = result.scalar() or 0
            print(f"✓ Blacklist entries: {blacklist_count}")
            
            # Check for invalid domains in blacklist
            result = await db.execute(
                select(BlacklistModel.domain).where(
                    (BlacklistModel.domain.is_(None)) | 
                    (func.length(BlacklistModel.domain) < 3)
                )
            )
            invalid_domains = result.scalars().all()
            if invalid_domains:
                issues.append(f"⚠ Found {len(invalid_domains)} invalid domains in blacklist")
            
            # Check parsing runs
            result = await db.execute(select(func.count()).select_from(ParsingRunModel))
            parsing_runs_count = result.scalar() or 0
            print(f"✓ Parsing runs: {parsing_runs_count}")
            
            # Check domains queue
            result = await db.execute(select(func.count()).select_from(DomainQueueModel))
            domains_queue_count = result.scalar() or 0
            print(f"✓ Domains queue: {domains_queue_count}")
            
            # Check foreign keys integrity (supplier_keywords)
            result = await db.execute(
                text("""
                    SELECT COUNT(*) FROM supplier_keywords sk
                    LEFT JOIN moderator_suppliers ms ON sk.supplier_id = ms.id
                    LEFT JOIN keywords k ON sk.keyword_id = k.id
                    WHERE ms.id IS NULL OR k.id IS NULL
                """)
            )
            orphaned_records = result.scalar() or 0
            if orphaned_records > 0:
                issues.append(f"⚠ Found {orphaned_records} orphaned supplier_keywords records")
            
            print("\n" + "="*50)
            if issues:
                print("⚠ Integrity issues found:")
                for issue in issues:
                    print(f"  {issue}")
                return 1
            else:
                print("✓ No integrity issues found!")
                return 0
                
        except Exception as e:
            print(f"Error checking integrity: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            break


if __name__ == "__main__":
    exit_code = asyncio.run(check_integrity())
    sys.exit(exit_code)

