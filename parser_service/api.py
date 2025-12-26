"""FastAPI application for Parser Service."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from src.parser import Parser
from src.config import settings

app = FastAPI(
    title="Parser Service API",
    version="1.0.0",
    description="Web parsing service using Chrome CDP"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseRequest(BaseModel):
    """Request model for parsing."""
    keyword: str
    max_urls: int = 10


class ParsedSupplier(BaseModel):
    """Parsed supplier data."""
    name: str
    domain: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    inn: Optional[str] = None
    source_url: str


class ParseResponse(BaseModel):
    """Response model for parsing."""
    keyword: str
    suppliers: List[ParsedSupplier]
    total_found: int


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse)
async def parse_keyword(request: ParseRequest):
    """Parse suppliers for a keyword."""
    try:
        parser = Parser(settings.CHROME_CDP_URL)
        suppliers = await parser.parse_keyword(
            keyword=request.keyword,
            max_urls=request.max_urls
        )
        
        return ParseResponse(
            keyword=request.keyword,
            suppliers=suppliers,
            total_found=len(suppliers)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

