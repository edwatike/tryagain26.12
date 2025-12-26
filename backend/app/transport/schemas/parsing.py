"""Pydantic schemas for parsing."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

from app.transport.schemas.common import BaseDTO


class StartParsingRequestDTO(BaseModel):
    """Request DTO for starting parsing."""
    keyword: str
    maxUrls: int = Field(default=10, alias="max_urls")


class StartParsingResponseDTO(BaseModel):
    """Response DTO for parsing start."""
    runId: str = Field(alias="run_id")
    keyword: str
    status: str


class ParsingStatusResponseDTO(BaseModel):
    """Response DTO for parsing status."""
    runId: str = Field(alias="run_id")
    keyword: str
    status: str
    startedAt: datetime = Field(alias="started_at")
    finishedAt: Optional[datetime] = Field(None, alias="finished_at")
    error: Optional[str] = None
    resultsCount: Optional[int] = Field(None, alias="results_count")


class ParsingRunDTO(BaseDTO):
    """Parsing run DTO."""
    runId: str = Field(alias="run_id")
    keyword: str
    status: str
    startedAt: datetime = Field(alias="started_at")
    finishedAt: Optional[datetime] = Field(None, alias="finished_at")
    error: Optional[str] = None
    resultsCount: Optional[int] = Field(None, alias="results_count")
    createdAt: datetime = Field(alias="created_at")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class ParsingRunsListResponseDTO(BaseModel):
    """Response DTO for parsing runs list."""
    runs: List[ParsingRunDTO]
    total: int
    limit: int
    offset: int

