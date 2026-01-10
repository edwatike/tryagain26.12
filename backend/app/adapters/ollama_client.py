"""Client for Ollama INN Extractor Service."""
import httpx
import logging
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama INN Extractor Service."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        """Initialize Ollama client.
        
        Args:
            base_url: Ollama service base URL (defaults to OLLAMA_SERVICE_URL from settings)
            timeout: Request timeout in seconds (defaults to 60)
        """
        self.base_url = base_url or getattr(settings, "OLLAMA_SERVICE_URL", "http://127.0.0.1:9004")
        self.timeout = timeout or 60
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def extract_inn_from_text(self, text: str) -> Dict[str, Any]:
        """Extract INN from text using Ollama service.
        
        Args:
            text: Text to extract INN from
            
        Returns:
            Dict with structure:
            {
                "inn": str | None,
                "proof": {
                    "url": str,
                    "context": str,
                    "method": "regex" | "ollama",
                    "confidence": "high" | "medium" | "low" | None
                } | None
            }
            
        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}/extract-inn"
        
        payload = {
            "text": text
        }
        
        try:
            logger.debug(f"Extracting INN from text via Ollama service: {url}")
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            # Ollama service returns {inn, proof} where proof is {context, method, confidence}
            # We need to merge this properly
            proof = result.get("proof")
            if proof and isinstance(proof, dict):
                return {
                    "inn": result.get("inn"),
                    "proof": proof,
                    "context": proof.get("context"),  # For backward compatibility
                    "method": proof.get("method"),
                    "confidence": proof.get("confidence")
                }
            else:
                return {
                    "inn": result.get("inn"),
                    "proof": proof,
                    "context": None,
                    "method": None,
                    "confidence": None
                }
            
        except httpx.TimeoutException as e:
            logger.error(f"Timeout while requesting Ollama service: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Ollama service: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while calling Ollama service: {e}")
            raise
    
    async def extract_inn_from_html(self, html: str) -> Dict[str, Any]:
        """Extract INN from HTML using Ollama service.
        
        Args:
            html: HTML content to extract INN from
            
        Returns:
            Dict with structure:
            {
                "inn": str | None,
                "proof": {
                    "url": str,
                    "context": str,
                    "method": "regex" | "ollama",
                    "confidence": "high" | "medium" | "low" | None
                } | None
            }
            
        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}/extract-inn"
        
        payload = {
            "html": html
        }
        
        try:
            logger.info(f"Calling Ollama service to extract INN from HTML (length: {len(html)} chars)")
            logger.debug(f"Ollama service URL: {url}")
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Ollama service response: inn={result.get('inn')}, method={result.get('proof', {}).get('method') if result.get('proof') else 'unknown'}, confidence={result.get('proof', {}).get('confidence') if result.get('proof') else 'unknown'}")
            # Ollama service returns {inn, proof} where proof is {context, method, confidence}
            # We need to merge this properly
            proof = result.get("proof")
            if proof and isinstance(proof, dict):
                return {
                    "inn": result.get("inn"),
                    "proof": proof,
                    "context": proof.get("context"),  # For backward compatibility
                    "method": proof.get("method"),
                    "confidence": proof.get("confidence")
                }
            else:
                return {
                    "inn": result.get("inn"),
                    "proof": proof,
                    "context": None,
                    "method": None,
                    "confidence": None
                }
            
        except httpx.TimeoutException as e:
            logger.error(f"Timeout while requesting Ollama service: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Ollama service: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while calling Ollama service: {e}")
            raise
    
    async def check_health(self) -> bool:
        """Check if Ollama service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            url = f"{self.base_url}/health"
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama service health check failed: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

