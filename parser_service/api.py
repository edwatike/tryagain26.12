"""FastAPI application for Parser Service."""
import asyncio
import sys
import logging
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# CRITICAL: Set event loop policy BEFORE any other imports
# This must be the very first thing to avoid NotImplementedError on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from src.parser import Parser
from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    depth: int = 10  # Number of search result pages to parse
    source: str = "google"  # "google", "yandex", or "both"


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
    import traceback
    import logging
    import asyncio
    import sys
    from concurrent.futures import ThreadPoolExecutor
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting parse for keyword: {request.keyword}, depth: {request.depth}, source: {request.source}")
        logger.info(f"Platform: {sys.platform}, is Windows: {sys.platform == 'win32'}")
        
        # On Windows, run parsing in a separate thread with asyncio.run() to avoid NotImplementedError
        # This is EXACTLY the same approach as test_browser_connection.py
        if sys.platform == 'win32':
            logger.info("Using Windows-specific parsing in separate thread with asyncio.run()")
            def run_parsing_in_thread(keyword_param, depth_param, source_param, chrome_cdp_url_param):
                """Run parsing in a separate thread with its own event loop using asyncio.run().
                
                This function runs ALL parsing operations in ONE asyncio.run() call,
                just like test_browser_connection.py does. This ensures all Playwright
                operations happen in the same event loop with the correct policy.
                """
                import asyncio
                import sys
                
                # Set event loop policy for this thread (same as test_browser_connection.py)
                # MUST be done BEFORE importing/using Playwright
                if sys.platform == 'win32':
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                
                # Import here AFTER setting policy to ensure Playwright uses correct policy
                import httpx
                from playwright.async_api import async_playwright
                from src.engines import YandexEngine, GoogleEngine
                from src.parser import Parser
                from typing import Set
                
                async def parse_async():
                    """Async function to run ALL parsing operations in one event loop."""
                    import logging
                    thread_logger = logging.getLogger(__name__)
                    thread_logger.info("Starting parse_async() in thread with asyncio.run()")
                    
                    # Get WebSocket URL from Chrome CDP (same as test_browser_connection.py)
                    thread_logger.info("Getting Chrome CDP WebSocket URL...")
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(f"{chrome_cdp_url_param}/json/version")
                        if response.status_code != 200:
                            raise Exception(f"Chrome CDP returned status {response.status_code}")
                        cdp_info = response.json()
                        ws_url = cdp_info.get("webSocketDebuggerUrl")
                        if not ws_url:
                            raise Exception("No webSocketDebuggerUrl in CDP response")
                        thread_logger.info(f"Got WebSocket URL: {ws_url}")
                    
                    # Start Playwright and connect to Chrome (same as test_browser_connection.py)
                    # This should work now because we're in a thread with asyncio.run() and correct policy
                    thread_logger.info("Starting Playwright...")
                    playwright = await async_playwright().start()
                    thread_logger.info("Playwright started, connecting to Chrome CDP...")
                    browser = await playwright.chromium.connect_over_cdp(ws_url)
                    thread_logger.info("Connected to Chrome CDP successfully!")
                    
                    try:
                        # Get browser contexts
                        contexts = browser.contexts
                        thread_logger.info(f"Found {len(contexts)} browser context(s)")
                        
                        # Select context based on profile index
                        # Profile index: 0 = first profile, 1 = second profile, etc.
                        from src.config import settings
                        profile_index = settings.CHROME_PROFILE_INDEX
                        
                        if len(contexts) == 0:
                            thread_logger.warning("No existing contexts found, creating new context")
                            context = await browser.new_context(
                                viewport={"width": 800, "height": 600}
                            )
                        else:
                            # Use specific profile context if index is valid
                            if 0 <= profile_index < len(contexts):
                                context = contexts[profile_index]
                                thread_logger.info(f"Using profile context at index {profile_index} (profile #{profile_index + 1})")
                            else:
                                # Fallback to first context if index is out of range
                                thread_logger.warning(
                                    f"Profile index {profile_index} is out of range (0-{len(contexts)-1}), "
                                    f"using first context (profile #1)"
                                )
                                context = contexts[0]
                        
                        # Set HTTP headers
                        await context.set_extra_http_headers({
                            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        })
                        
                        # Now run the actual parsing logic
                        parser = Parser(chrome_cdp_url_param)
                        # Set browser, playwright, and context directly to avoid re-connecting
                        parser.browser = browser
                        parser.playwright = playwright
                        parser.context = context
                        parser._playwright_started = True
                        
                        # Engines already imported above
                        
                        # Use depth directly from request parameter
                        depth = depth_param
                        thread_logger.info(f"Using depth={depth} for parsing (requested: {depth_param})")
                        
                        # Prepare query
                        query = f"{keyword_param} купить"
                        thread_logger.info(f"Query: {query}, source: {source_param}, depth: {depth}")
                        
                        # Collect links from search engines
                        collected_links: Set[str] = set()
                        
                        # Run search engines in parallel (same approach as parser.py)
                        tasks = []
                        
                        if source_param in ["yandex", "both"]:
                            yandex_page = await context.new_page()
                            yandex_engine = YandexEngine()
                            tasks.append(yandex_engine.parse(yandex_page, query, depth, collected_links))
                        
                        if source_param in ["google", "both"]:
                            google_page = await context.new_page()
                            google_engine = GoogleEngine()
                            tasks.append(google_engine.parse(google_page, query, depth, collected_links))
                        
                        # Wait for all search engines to complete
                        if tasks:
                            await asyncio.gather(*tasks)
                        
                        # Return only collected URLs without parsing pages
                        # Convert collected links to supplier-like format (only URLs, no page parsing)
                        suppliers = []
                        for url in list(collected_links):  # No limit - return all collected URLs
                            # Extract domain from URL
                            from urllib.parse import urlparse
                            parsed_url = urlparse(url)
                            domain = parsed_url.netloc.replace("www.", "")
                            
                            suppliers.append({
                                "name": domain,  # Use domain as name since we don't parse pages
                                "domain": domain,
                                "email": None,
                                "phone": None,
                                "inn": None,
                                "source_url": url
                            })
                        
                        return suppliers
                    finally:
                        # Clean up
                        if browser:
                            await browser.close()
                        if playwright:
                            await playwright.stop()
                
                # Use asyncio.run() to create a new event loop with the correct policy
                # This is EXACTLY the same approach as test_browser_connection.py
                return asyncio.run(parse_async())
            
            # Run parsing in a separate thread
            current_loop = asyncio.get_running_loop()
            executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="parsing")
            try:
                logger.info("Running parsing in separate thread with asyncio.run() (Windows)...")
                suppliers = await current_loop.run_in_executor(
                    executor,
                    run_parsing_in_thread,
                    request.keyword,
                    request.depth,
                    request.source,
                    settings.CHROME_CDP_URL
                )
            finally:
                executor.shutdown(wait=False)
        else:
            # Non-Windows: run normally
            parser = Parser(settings.CHROME_CDP_URL)
            suppliers = await parser.parse_keyword(
                keyword=request.keyword,
                depth=request.depth,
                source=request.source
            )
        
        logger.info(f"Parse completed: found {len(suppliers)} suppliers")
        return ParseResponse(
            keyword=request.keyword,
            suppliers=suppliers,
            total_found=len(suppliers)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except httpx.ConnectError as e:
        # Connection error to Chrome CDP or other services
        error_message = f"Cannot connect to Chrome CDP at {settings.CHROME_CDP_URL}. Please ensure Chrome is running with --remote-debugging-port=9222. Error: {str(e)}"
        logger.error(f"Connection error in parse_keyword: {error_message}")
        raise HTTPException(
            status_code=503,
            detail=error_message
        )
    except httpx.TimeoutException as e:
        # Timeout error
        error_message = f"Timeout while parsing. The operation took too long. Error: {str(e)}"
        logger.error(f"Timeout error in parse_keyword: {error_message}")
        raise HTTPException(
            status_code=504,
            detail=error_message
        )
    except Exception as e:
        error_traceback = traceback.format_exc()
        error_message = str(e) if e else "Unknown error"
        error_type = type(e).__name__
        
        logger.error(f"Error in parse_keyword ({error_type}): {error_message}\n{error_traceback}")
        
        # Provide more helpful error messages for common issues
        if "Chrome CDP" in error_message or "connect" in error_message.lower():
            detail_message = (
                f"Chrome CDP connection error: {error_message}\n\n"
                f"Please ensure:\n"
                f"1. Chrome is running with --remote-debugging-port=9222\n"
                f"2. Chrome CDP is accessible at {settings.CHROME_CDP_URL}\n"
                f"3. No firewall is blocking the connection"
            )
        elif "NotImplementedError" in error_type:
            detail_message = (
                f"Windows event loop error: {error_message}\n\n"
                f"This is a known Windows issue. The parser should handle this automatically, "
                f"but if it persists, please check the Windows event loop policy configuration."
            )
        else:
            # Return detailed error information for other errors
            detail_message = f"{error_type}: {error_message}"
            if error_traceback:
                detail_message += f"\n\nTraceback:\n{error_traceback}"
        
        raise HTTPException(
            status_code=500,
            detail=detail_message
        )

