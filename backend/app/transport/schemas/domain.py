"""Pydantic schemas for domains queue."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.transport.schemas.common import BaseDTO


class DomainQueueEntryDTO(BaseDTO):
    """Domain queue entry DTO."""
    domain: str
    keyword: str
    url: str
    parsingRunId: Optional[str] = Field(None, alias="parsing_run_id")
    status: str
    createdAt: datetime = Field(alias="created_at")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class DomainsQueueResponseDTO(BaseModel):
    """Response DTO for domains queue."""
    entries: List[DomainQueueEntryDTO]
    total: int
    limit: int
    offset: int

