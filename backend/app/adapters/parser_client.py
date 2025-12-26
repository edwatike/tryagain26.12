"""HTTP client for Parser Service."""
import httpx
from typing import List, Dict, Any
from app.config import settings


class ParserClient:
    """Client for communicating with Parser Service."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.parser_service_url
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=300.0  # 5 minutes for parsing operations
        )
    
    async def parse(self, keyword: str, max_urls: int = 10) -> Dict[str, Any]:
        """
        Start parsing for a keyword.
        
        Args:
            keyword: Search keyword
            max_urls: Maximum number of URLs to parse
            
        Returns:
            Dictionary with parsing results
        """
        response = await self.client.post(
            "/parse",
            json={
                "keyword": keyword,
                "max_urls": max_urls
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Parser Service health."""
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

