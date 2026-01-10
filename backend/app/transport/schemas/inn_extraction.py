"""Pydantic schemas for INN extraction."""
from typing import List, Optional
from pydantic import BaseModel, Field


class INNExtractionProofDTO(BaseModel):
    """Proof (context) for extracted INN."""
    url: str = Field(..., description="URL where INN was found")
    context: str = Field(..., description="Text fragment (50-100 chars) around INN")
    method: str = Field(..., description="Extraction method: 'regex' or 'ollama'")
    confidence: Optional[str] = Field(None, description="Confidence level: 'high', 'medium', or 'low'")


class INNExtractionResultDTO(BaseModel):
    """Result of INN extraction for a domain."""
    domain: str = Field(..., description="Domain name")
    status: str = Field(..., description="Status: 'success', 'not_found', or 'error'")
    inn: Optional[str] = Field(None, description="Extracted INN (10 or 12 digits)")
    proof: Optional[INNExtractionProofDTO] = Field(None, description="Proof (context) for extracted INN")
    error: Optional[str] = Field(None, description="Error message if status is 'error'")
    processingTime: Optional[int] = Field(None, description="Processing time in milliseconds")


class ExtractINNBatchRequestDTO(BaseModel):
    """Request for batch INN extraction."""
    domains: List[str] = Field(..., description="List of domain names to extract INN from", min_length=1)


class ExtractINNBatchResponseDTO(BaseModel):
    """Response for batch INN extraction."""
    results: List[INNExtractionResultDTO] = Field(..., description="List of extraction results")
    total: int = Field(..., description="Total number of domains")
    processed: int = Field(..., description="Number of processed domains")
    successful: int = Field(..., description="Number of successful extractions")
    failed: int = Field(..., description="Number of failed extractions")
    notFound: int = Field(..., description="Number of domains where INN was not found")





