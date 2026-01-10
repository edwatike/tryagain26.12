"""HTTP client for Checko API."""
import httpx
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class CheckoClient:
    """Client for Checko API v2."""
    
    BASE_URL = "https://api.checko.ru/v2"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Checko client.
        
        Args:
            api_key: Checko API key. If not provided, uses settings.CHECKO_API_KEY.
        """
        self.api_key = api_key or settings.CHECKO_API_KEY
        if not self.api_key:
            raise ValueError("Checko API key is required")
    
    async def get_company(self, inn: str) -> Dict[str, Any]:
        """Get company information by INN.
        
        Args:
            inn: Company INN (10 or 12 digits)
            
        Returns:
            Company data from Checko API
            
        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.BASE_URL}/company"
        params = {"key": self.api_key, "inn": inn}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_finances(self, inn: str) -> Dict[str, Any]:
        """Get company financial data by INN.
        
        Args:
            inn: Company INN (10 or 12 digits)
            
        Returns:
            Financial data from Checko API
            
        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.BASE_URL}/finances"
        params = {"key": self.api_key, "inn": inn}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_legal_cases(self, inn: str) -> Dict[str, Any]:
        """Get company legal cases by INN.
        
        Args:
            inn: Company INN (10 or 12 digits)
            
        Returns:
            Legal cases data from Checko API
            
        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.BASE_URL}/legal-cases"
        params = {"key": self.api_key, "inn": inn}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_inspections(self, inn: str) -> Dict[str, Any]:
        """Get company inspections by INN.
        
        Args:
            inn: Company INN (10 or 12 digits)
            
        Returns:
            Inspections data from Checko API
            
        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.BASE_URL}/inspections"
        params = {"key": self.api_key, "inn": inn}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_enforcements(self, inn: str) -> Dict[str, Any]:
        """Get company enforcements by INN.
        
        Args:
            inn: Company INN (10 or 12 digits)
            
        Returns:
            Enforcements data from Checko API
            
        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.BASE_URL}/enforcements"
        params = {"key": self.api_key, "inn": inn}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_all_data(self, inn: str) -> Dict[str, Any]:
        """Get all company data from Checko API (5 endpoints in parallel).
        
        Args:
            inn: Company INN (10 or 12 digits)
            
        Returns:
            Combined data from all Checko endpoints:
            {
                "company": {...},
                "_finances": {...},
                "_legal": {...},
                "_inspections": {...},
                "_enforcements": {...}
            }
        """
        import asyncio
        
        # Запускаем все запросы параллельно
        tasks = [
            self.get_company(inn),
            self.get_finances(inn),
            self.get_legal_cases(inn),
            self.get_inspections(inn),
            self.get_enforcements(inn),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Формируем результат
        company_data = results[0]
        if isinstance(company_data, Exception):
            raise company_data
        
        finances_data = results[1] if not isinstance(results[1], Exception) else {"data": None}
        legal_data = results[2] if not isinstance(results[2], Exception) else {"data": None}
        inspections_data = results[3] if not isinstance(results[3], Exception) else {"data": None}
        enforcements_data = results[4] if not isinstance(results[4], Exception) else {"data": None}
        
        # Логируем ошибки в дополнительных запросах (не критичны)
        for i, result in enumerate(results[1:], 1):
            if isinstance(result, Exception):
                endpoint_names = ["finances", "legal-cases", "inspections", "enforcements"]
                logger.warning(f"Failed to fetch {endpoint_names[i-1]} for INN {inn}: {result}")
        
        return {
            **company_data.get("data", {}),
            "_finances": finances_data.get("data") or {},
            "_legal": legal_data.get("data") or {},
            "_inspections": inspections_data.get("data") or {},
            "_enforcements": enforcements_data.get("data") or {},
        }









