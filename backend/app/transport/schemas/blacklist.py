"""Pydantic schemas for blacklist."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

from app.transport.schemas.common import BaseDTO


class BlacklistEntryDTO(BaseDTO):
    """Blacklist entry DTO."""
    domain: str
    reason: Optional[str] = None
    addedBy: Optional[str] = Field(None, alias="added_by")
    addedAt: datetime = Field(alias="added_at")
    parsingRunId: Optional[str] = Field(None, alias="parsing_run_id")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class AddToBlacklistRequestDTO(BaseModel):
    """Request DTO for adding to blacklist."""
    domain: str
    reason: Optional[str] = None
    addedBy: Optional[str] = None
    parsingRunId: Optional[str] = None


class BlacklistResponseDTO(BaseModel):
    """Response DTO for blacklist."""
    entries: List[BlacklistEntryDTO]
    total: int
    limit: int
    offset: int

