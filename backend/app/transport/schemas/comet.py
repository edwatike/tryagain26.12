"""Pydantic schemas for Comet extraction."""

from typing import List, Optional
from pydantic import BaseModel, Field


class CometExtractionResultDTO(BaseModel):
    """Result of Comet extraction for a domain."""

    domain: str = Field(..., description="Domain name")
    status: str = Field(..., description="Status: 'pending', 'running', 'success', 'not_found', or 'error'")
    inn: Optional[str] = Field(None, description="Extracted INN (10 or 12 digits)")
    email: Optional[str] = Field(None, description="Extracted email")
    sourceUrls: List[str] = Field(default_factory=list, description="Up to 2 assistant-provided source URLs")
    error: Optional[str] = Field(None, description="Error message if status is 'error'")


class CometExtractBatchRequestDTO(BaseModel):
    """Request for batch Comet extraction."""

    runId: str = Field(..., description="Parsing run id")
    domains: List[str] = Field(..., description="List of domain names", min_length=1)


class CometExtractBatchResponseDTO(BaseModel):
    """Response for starting batch Comet extraction."""

    runId: str = Field(..., description="Parsing run id")
    cometRunId: str = Field(..., description="Comet extraction run id")


class CometStatusResponseDTO(BaseModel):
    """Response for Comet extraction status."""

    runId: str = Field(..., description="Parsing run id")
    cometRunId: str = Field(..., description="Comet extraction run id")
    status: str = Field(..., description="Run status: 'running', 'completed', or 'failed'")
    processed: int = Field(..., description="Number of processed domains")
    total: int = Field(..., description="Total number of domains")
    results: List[CometExtractionResultDTO] = Field(default_factory=list)
