"""Use case for batch INN extraction from domains."""
import asyncio
import time
import logging
import httpx
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.db.repositories import DomainQueueRepository
from app.adapters.ollama_client import OllamaClient
from app.adapters.parser_client import ParserClient

logger = logging.getLogger(__name__)

# Add ollama_inn_extractor to path for importing InteractiveINNFinder
_project_root = Path(__file__).parent.parent.parent.parent
_ollama_service_dir = _project_root / "ollama_inn_extractor"
if _ollama_service_dir.exists():
    ollama_path_str = str(_ollama_service_dir)
    if ollama_path_str not in sys.path:
        sys.path.insert(0, ollama_path_str)
    logger.debug(f"Added ollama_inn_extractor to path: {ollama_path_str}")
else:
    logger.warning(f"ollama_inn_extractor directory not found at: {_ollama_service_dir}")

# Максимальное количество параллельных запросов
MAX_CONCURRENT_REQUESTS = 5


async def extract_inn_for_domain(
    domain: str,
    db: AsyncSession,
    ollama_client: OllamaClient
) -> Dict[str, Any]:
    """Extract INN for a single domain.
    
    Args:
        domain: Domain name
        db: Database session
        ollama_client: Ollama client
        
    Returns:
        Dict with structure:
        {
            "domain": str,
            "status": "success" | "not_found" | "error",
            "inn": str | None,
            "proof": {
                "url": str,
                "context": str,
                "method": "regex" | "ollama",
                "confidence": "high" | "medium" | "low" | None
            } | None,
            "error": str | None,
            "processingTime": int
        }
    """
    start_time = time.time()
    
    try:
        # Получаем URL для домена из domains_queue
        # Используем get_by_domain для получения первой записи с этим доменом
        repo = DomainQueueRepository(db)
        domain_entry = await repo.get_by_domain(domain)
        
        if not domain_entry:
            return {
                "domain": domain,
                "status": "error",
                "inn": None,
                "proof": None,
                "error": f"Domain {domain} not found in domains_queue",
                "processingTime": int((time.time() - start_time) * 1000)
            }
        
        # Берем URL для домена
        url = domain_entry.url
        
        # Используем интерактивного AI агента для поиска ИНН
        try:
            logger.info(f"Starting interactive INN search for domain {domain} from URL {url}")
            
            # Import InteractiveINNFinder from ollama_inn_extractor
            # Path is already added at module level (line 19-21)
            try:
                # Try importing directly (ollama_inn_extractor is in sys.path)
                from app.agents.interactive_inn_finder import InteractiveINNFinder
                from app.agents.agent_memory import AgentMemory
                from app.ollama_client import OllamaClient as OllamaINNClient
            except ImportError as e1:
                # Fallback: try importing with full path
                try:
                    from ollama_inn_extractor.app.agents.interactive_inn_finder import InteractiveINNFinder
                    from ollama_inn_extractor.app.agents.agent_memory import AgentMemory
                    from ollama_inn_extractor.app.ollama_client import OllamaClient as OllamaINNClient
                except ImportError as e2:
                    logger.error(f"Failed to import InteractiveINNFinder: {e1}, {e2}. Make sure ollama_inn_extractor is in path: {_ollama_service_dir}")
                    logger.error(f"Current sys.path: {sys.path[:5]}")
                    raise
            
            # Get Chrome CDP URL from settings (default: http://127.0.0.1:9222)
            chrome_cdp_url = os.getenv("CHROME_CDP_URL", "http://127.0.0.1:9222")
            
            # Create Ollama client for interactive agent (different from backend OllamaClient)
            ollama_inn_client = OllamaINNClient()
            
            # Create interactive finder
            finder = InteractiveINNFinder(
                chrome_cdp_url=chrome_cdp_url,
                ollama_client=ollama_inn_client,
                max_attempts=15
            )
            
            try:
                # For obi.ru and similar sites, start from homepage for better navigation
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain_name = parsed.netloc.replace("www.", "")
                
                # Start from homepage for better navigation to contacts/requisites
                if domain_name == "obi.ru" or "/strojmaterialy" in url:
                    start_url = f"https://www.{domain_name}" if not domain_name.startswith("www.") else f"https://{domain_name}"
                else:
                    start_url = url
                
                logger.info(f"Using start URL: {start_url} for domain {domain_name}")
                
                # Find INN interactively
                result = await finder.find_inn(domain=domain_name, start_url=start_url)
                
                processing_time = int((time.time() - start_time) * 1000)
                
                logger.info(
                    f"Interactive INN search result for {domain}: "
                    f"success={result.get('success')}, inn={result.get('inn')}, "
                    f"attempts={result.get('attempts')}, actions={len(result.get('actions_taken', []))}"
                )
                
                if result.get("success") and result.get("inn"):
                    # Build proof object
                    proof = {
                        "url": result.get("url", url),
                        "context": result.get("context") or "",
                        "method": "interactive_agent",
                        "confidence": "high"  # Interactive agent has high confidence
                    }
                    
                    return {
                        "domain": domain,
                        "status": "success",
                        "inn": result.get("inn"),
                        "proof": proof,
                        "error": None,
                        "processingTime": processing_time
                    }
                else:
                    return {
                        "domain": domain,
                        "status": "not_found",
                        "inn": None,
                        "proof": None,
                        "error": None,
                        "processingTime": processing_time
                    }
            finally:
                # Don't close finder - it will keep browser open
                # Just close Ollama client
                try:
                    await ollama_inn_client.close()
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Error in interactive INN search for {domain}: {e}", exc_info=True)
            return {
                "domain": domain,
                "status": "error",
                "inn": None,
                "proof": None,
                "error": f"Failed to extract INN interactively: {str(e)}",
                "processingTime": int((time.time() - start_time) * 1000)
            }
            
    except Exception as e:
        logger.error(f"Unexpected error processing domain {domain}: {e}", exc_info=True)
        return {
            "domain": domain,
            "status": "error",
            "inn": None,
            "proof": None,
            "error": f"Unexpected error: {str(e)}",
            "processingTime": int((time.time() - start_time) * 1000)
        }


async def execute(
    db: AsyncSession,
    domains: List[str]
) -> Dict[str, Any]:
    """Extract INN for multiple domains in parallel.
    
    Args:
        db: Database session
        domains: List of domain names
        
    Returns:
        Dict with structure:
        {
            "results": List[INNExtractionResult],
            "total": int,
            "processed": int,
            "successful": int,
            "failed": int,
            "notFound": int
        }
    """
    logger.info(f"=== Starting batch INN extraction for {len(domains)} domains ===")
    logger.info(f"Domains: {domains}")
    
    ollama_client = OllamaClient()
    
    try:
        # Создаем семафор для ограничения параллельных запросов
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        async def extract_with_semaphore(domain: str):
            async with semaphore:
                return await extract_inn_for_domain(domain, db, ollama_client)
        
        # Запускаем извлечение для всех доменов параллельно
        tasks = [extract_with_semaphore(domain) for domain in domains]
        results = await asyncio.gather(*tasks)
        
        # Подсчитываем статистику
        successful = sum(1 for r in results if r["status"] == "success")
        failed = sum(1 for r in results if r["status"] == "error")
        not_found = sum(1 for r in results if r["status"] == "not_found")
        
        logger.info(
            f"=== Batch INN extraction completed ==="
        )
        logger.info(
            f"Statistics: total={len(domains)}, successful={successful}, failed={failed}, not_found={not_found}"
        )
        # Логируем результаты для каждого домена
        for r in results:
            if r["status"] == "success":
                logger.info(f"✓ {r['domain']}: INN={r['inn']}, method={r['proof'].get('method') if r['proof'] else 'unknown'}, confidence={r['proof'].get('confidence') if r['proof'] else 'unknown'}")
            elif r["status"] == "not_found":
                logger.info(f"○ {r['domain']}: INN not found")
            else:
                logger.warning(f"✗ {r['domain']}: Error - {r.get('error', 'Unknown error')}")
        
        return {
            "results": results,
            "total": len(domains),
            "processed": len(results),
            "successful": successful,
            "failed": failed,
            "notFound": not_found
        }
        
    finally:
        await ollama_client.close()

