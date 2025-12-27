"""Database repositories for data access."""
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.adapters.db.models import (
    ModeratorSupplierModel,
    KeywordModel,
    SupplierKeywordModel,
    BlacklistModel,
    ParsingRequestModel,
    ParsingRunModel,
    DomainQueueModel,
)


class ModeratorSupplierRepository:
    """Repository for moderator suppliers."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, supplier_data: dict) -> ModeratorSupplierModel:
        """Create a new supplier."""
        supplier = ModeratorSupplierModel(**supplier_data)
        self.session.add(supplier)
        await self.session.flush()
        await self.session.refresh(supplier)
        return supplier
    
    async def get_by_id(self, supplier_id: int) -> Optional[ModeratorSupplierModel]:
        """Get supplier by ID."""
        result = await self.session.execute(
            select(ModeratorSupplierModel)
            .where(ModeratorSupplierModel.id == supplier_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_domain(self, domain: str) -> Optional[ModeratorSupplierModel]:
        """Get supplier by domain."""
        result = await self.session.execute(
            select(ModeratorSupplierModel)
            .where(ModeratorSupplierModel.domain == domain)
        )
        return result.scalar_one_or_none()
    
    async def get_by_inn(self, inn: str) -> Optional[ModeratorSupplierModel]:
        """Get supplier by INN."""
        result = await self.session.execute(
            select(ModeratorSupplierModel)
            .where(ModeratorSupplierModel.inn == inn)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        type_filter: Optional[str] = None
    ) -> tuple[List[ModeratorSupplierModel], int]:
        """List suppliers with pagination."""
        query = select(ModeratorSupplierModel)
        count_query = select(func.count()).select_from(ModeratorSupplierModel)
        
        if type_filter:
            query = query.where(ModeratorSupplierModel.type == type_filter)
            count_query = count_query.where(ModeratorSupplierModel.type == type_filter)
        
        query = query.order_by(ModeratorSupplierModel.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        suppliers = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return list(suppliers), total
    
    async def update(self, supplier_id: int, supplier_data: dict) -> Optional[ModeratorSupplierModel]:
        """Update supplier."""
        supplier = await self.get_by_id(supplier_id)
        if not supplier:
            return None
        
        for key, value in supplier_data.items():
            setattr(supplier, key, value)
        
        await self.session.flush()
        await self.session.refresh(supplier)
        return supplier
    
    async def delete(self, supplier_id: int) -> bool:
        """Delete supplier."""
        supplier = await self.get_by_id(supplier_id)
        if not supplier:
            return False
        
        await self.session.delete(supplier)
        await self.session.flush()
        return True
    
    async def get_keywords(self, supplier_id: int) -> List[dict]:
        """Get supplier keywords with metadata."""
        result = await self.session.execute(
            select(SupplierKeywordModel, KeywordModel)
            .join(KeywordModel, SupplierKeywordModel.keyword_id == KeywordModel.id)
            .where(SupplierKeywordModel.supplier_id == supplier_id)
        )
        
        keywords = []
        for supplier_keyword, keyword in result.all():
            keywords.append({
                "keyword": keyword.keyword,
                "urlCount": supplier_keyword.url_count,
                "runId": supplier_keyword.parsing_run_id,
                "firstUrl": supplier_keyword.first_url,
            })
        
        return keywords


class KeywordRepository:
    """Repository for keywords."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, keyword: str) -> KeywordModel:
        """Create a new keyword."""
        keyword_model = KeywordModel(keyword=keyword)
        self.session.add(keyword_model)
        await self.session.flush()
        await self.session.refresh(keyword_model)
        return keyword_model
    
    async def get_by_id(self, keyword_id: int) -> Optional[KeywordModel]:
        """Get keyword by ID."""
        result = await self.session.execute(
            select(KeywordModel).where(KeywordModel.id == keyword_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_keyword(self, keyword: str) -> Optional[KeywordModel]:
        """Get keyword by keyword string."""
        result = await self.session.execute(
            select(KeywordModel).where(KeywordModel.keyword == keyword)
        )
        return result.scalar_one_or_none()
    
    async def list(self) -> List[KeywordModel]:
        """List all keywords."""
        result = await self.session.execute(
            select(KeywordModel).order_by(KeywordModel.keyword)
        )
        return list(result.scalars().all())
    
    async def delete(self, keyword_id: int) -> bool:
        """Delete keyword."""
        keyword = await self.get_by_id(keyword_id)
        if not keyword:
            return False
        
        await self.session.delete(keyword)
        await self.session.flush()
        return True
    
    async def attach_to_supplier(
        self,
        supplier_id: int,
        keyword_id: int,
        url_count: int = 1,
        parsing_run_id: Optional[str] = None,
        first_url: Optional[str] = None
    ) -> SupplierKeywordModel:
        """Attach keyword to supplier."""
        supplier_keyword = SupplierKeywordModel(
            supplier_id=supplier_id,
            keyword_id=keyword_id,
            url_count=url_count,
            parsing_run_id=parsing_run_id,
            first_url=first_url
        )
        self.session.add(supplier_keyword)
        await self.session.flush()
        return supplier_keyword


class BlacklistRepository:
    """Repository for blacklist."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, blacklist_data: dict) -> BlacklistModel:
        """Add domain to blacklist."""
        blacklist_entry = BlacklistModel(**blacklist_data)
        self.session.add(blacklist_entry)
        await self.session.flush()
        await self.session.refresh(blacklist_entry)
        return blacklist_entry
    
    async def get_by_domain(self, domain: str) -> Optional[BlacklistModel]:
        """Get blacklist entry by domain."""
        result = await self.session.execute(
            select(BlacklistModel).where(BlacklistModel.domain == domain)
        )
        return result.scalar_one_or_none()
    
    async def list(self, limit: int = 100, offset: int = 0) -> tuple[List[BlacklistModel], int]:
        """List blacklist entries with pagination."""
        query = select(BlacklistModel).order_by(BlacklistModel.added_at.desc())
        count_query = select(func.count()).select_from(BlacklistModel)
        
        result = await self.session.execute(
            query.limit(limit).offset(offset)
        )
        entries = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return list(entries), total
    
    async def delete(self, domain: str) -> bool:
        """Remove domain from blacklist."""
        entry = await self.get_by_domain(domain)
        if not entry:
            return False
        
        await self.session.delete(entry)
        await self.session.flush()
        return True
    
    async def is_blacklisted(self, domain: str) -> bool:
        """Check if domain is blacklisted."""
        entry = await self.get_by_domain(domain)
        return entry is not None


class ParsingRequestRepository:
    """Repository for parsing requests."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, request_data: dict) -> ParsingRequestModel:
        """Create a new parsing request."""
        # Remove any invalid fields that might be passed by mistake
        valid_fields = {
            'id', 'created_at', 'updated_at', 'created_by', 'raw_keys_json',
            'depth', 'source', 'comment', 'title'
        }
        filtered_data = {k: v for k, v in request_data.items() if k in valid_fields}
        
        # Log if invalid fields were filtered out
        invalid_fields = set(request_data.keys()) - valid_fields
        if invalid_fields:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Filtered out invalid fields from request_data: {invalid_fields}")
        
        request = ParsingRequestModel(**filtered_data)
        self.session.add(request)
        await self.session.flush()
        await self.session.refresh(request)
        return request


class ParsingRunRepository:
    """Repository for parsing runs."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, run_data: dict) -> ParsingRunModel:
        """Create a new parsing run."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Remove any invalid fields that might be passed by mistake
        valid_fields = {
            'id', 'run_id', 'request_id', 'parser_task_id', 'status', 
            'depth', 'source', 'created_at', 'started_at', 'finished_at', 'error_message'
        }
        
        # Log input data for debugging
        logger.debug(f"ParsingRunRepository.create called with: {run_data}")
        
        filtered_data = {k: v for k, v in run_data.items() if k in valid_fields}
        
        # Log if invalid fields were filtered out
        invalid_fields = set(run_data.keys()) - valid_fields
        if invalid_fields:
            logger.warning(f"Filtered out invalid fields from run_data: {invalid_fields}. Original data: {run_data}")
        
        # Double check - explicitly remove keyword if it somehow got through
        if 'keyword' in filtered_data:
            logger.error(f"ERROR: 'keyword' field found in filtered_data! This should not happen. filtered_data: {filtered_data}")
            del filtered_data['keyword']
        
        logger.debug(f"Creating ParsingRunModel with filtered_data: {filtered_data}")
        
        try:
            run = ParsingRunModel(**filtered_data)
            self.session.add(run)
            await self.session.flush()
            await self.session.refresh(run)
            return run
        except TypeError as e:
            logger.error(f"TypeError creating ParsingRunModel. filtered_data: {filtered_data}, error: {e}")
            raise
    
    async def get_by_id(self, run_id: str) -> Optional[ParsingRunModel]:
        """Get parsing run by ID."""
        from app.adapters.db.models import ParsingRequestModel
        
        # Join with parsing_requests and eager load relationship
        result = await self.session.execute(
            select(ParsingRunModel)
            .join(ParsingRequestModel, ParsingRunModel.request_id == ParsingRequestModel.id)
            .options(selectinload(ParsingRunModel.request))
            .where(ParsingRunModel.run_id == run_id)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[ParsingRunModel], int]:
        """List parsing runs with pagination, filtering, and sorting."""
        from app.adapters.db.models import ParsingRequestModel
        
        # Join with parsing_requests and eager load relationship
        query = (
            select(ParsingRunModel)
            .join(ParsingRequestModel, ParsingRunModel.request_id == ParsingRequestModel.id)
            .options(selectinload(ParsingRunModel.request))
        )
        
        # Фильтрация по статусу
        if status:
            query = query.where(ParsingRunModel.status == status)
        
        # Фильтрация по keyword (через parsing_requests)
        if keyword:
            query = query.where(
                (ParsingRequestModel.title.ilike(f"%{keyword}%")) |
                (ParsingRequestModel.raw_keys_json.ilike(f"%{keyword}%"))
            )
        
        # Сортировка
        sort_column = getattr(ParsingRunModel, sort_by, ParsingRunModel.created_at)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc().nulls_last())
        else:
            query = query.order_by(sort_column.desc().nulls_last())
        
        # Count query с теми же фильтрами
        count_query = (
            select(func.count())
            .select_from(ParsingRunModel)
            .join(ParsingRequestModel, ParsingRunModel.request_id == ParsingRequestModel.id)
        )
        if status:
            count_query = count_query.where(ParsingRunModel.status == status)
        if keyword:
            count_query = count_query.where(
                (ParsingRequestModel.title.ilike(f"%{keyword}%")) |
                (ParsingRequestModel.raw_keys_json.ilike(f"%{keyword}%"))
            )
        
        result = await self.session.execute(
            query.limit(limit).offset(offset)
        )
        runs = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return list(runs), total
    
    async def update(self, run_id: str, run_data: dict) -> Optional[ParsingRunModel]:
        """Update parsing run."""
        run = await self.get_by_id(run_id)
        if not run:
            return None
        
        for key, value in run_data.items():
            setattr(run, key, value)
        
        await self.session.flush()
        await self.session.refresh(run)
        return run
    
    async def delete(self, run_id: str) -> bool:
        """Delete parsing run by run_id."""
        run = await self.get_by_id(run_id)
        if not run:
            return False
        
        await self.session.delete(run)
        await self.session.flush()
        return True


class DomainQueueRepository:
    """Repository for domains queue."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, queue_data: dict) -> DomainQueueModel:
        """Add domain to queue."""
        queue_entry = DomainQueueModel(**queue_data)
        self.session.add(queue_entry)
        await self.session.flush()
        await self.session.refresh(queue_entry)
        return queue_entry
    
    async def get_by_domain(self, domain: str) -> Optional[DomainQueueModel]:
        """Get queue entry by domain."""
        result = await self.session.execute(
            select(DomainQueueModel).where(DomainQueueModel.domain == domain)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        parsing_run_id: Optional[str] = None  # Added parsing_run_id filter
    ) -> tuple[List[DomainQueueModel], int]:
        """List queue entries with pagination."""
        query = select(DomainQueueModel)
        count_query = select(func.count()).select_from(DomainQueueModel)
        
        if status:
            query = query.where(DomainQueueModel.status == status)
            count_query = count_query.where(DomainQueueModel.status == status)
        
        if keyword:
            query = query.where(DomainQueueModel.keyword.ilike(f"%{keyword}%"))
            count_query = count_query.where(DomainQueueModel.keyword.ilike(f"%{keyword}%"))
        
        if parsing_run_id:  # Filter by parsing_run_id
            query = query.where(DomainQueueModel.parsing_run_id == parsing_run_id)
            count_query = count_query.where(DomainQueueModel.parsing_run_id == parsing_run_id)
        
        query = query.order_by(DomainQueueModel.created_at.desc())
        
        result = await self.session.execute(
            query.limit(limit).offset(offset)
        )
        entries = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return list(entries), total
    
    async def delete(self, domain: str) -> bool:
        """Remove domain from queue."""
        entry = await self.get_by_domain(domain)
        if not entry:
            return False
        
        await self.session.delete(entry)
        await self.session.flush()
        return True

