"""Search engines integration."""
import asyncio
import logging
import time
from typing import Set, List
from playwright.async_api import Page
from .human_behavior import (
    human_pause,
    very_human_behavior,
    light_human_behavior,
    wait_for_captcha,
)

logger = logging.getLogger(__name__)


class SearchEngine:
    """Base class for search engines."""
    
    def __init__(self, name: str):
        self.name = name
    
    async def parse(self, page: Page, query: str, depth: int, collected_links: Set[str]):
        """Parse search results and collect links."""
        raise NotImplementedError


class YandexEngine(SearchEngine):
    """Yandex search engine parser."""
    
    def __init__(self):
        super().__init__("YANDEX")
    
    async def parse(self, page: Page, query: str, depth: int, collected_links: Set[str]):
        """Parse Yandex search results."""
        start_time = time.time()
        logger.info(f"{self.name}: Начало парсинга '{query}'")
        print(f"\n[*] {self.name}: Старт парсинга...")
        
        initial_count = len(collected_links)
        
        # Set additional headers for Yandex
        await page.set_extra_http_headers({
            'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
        })
        
        await human_pause(2, 4)
        
        await page.goto(
            f"https://yandex.ru/search/?text={query.replace(' ', '+')}",
            wait_until="domcontentloaded",
            timeout=60000
        )
        await wait_for_captcha(page, self.name)
        
        logger.info(f"{self.name}: Starting to parse {depth} page(s)")
        for n in range(1, depth + 1):
            print(f"[PAGE] {self.name}: страница {n}/{depth}")
            logger.info(f"{self.name}: Processing page {n} of {depth}")
            
            await very_human_behavior(page)
            await human_pause(2, 4)
            await wait_for_captcha(page, self.name)
            
            # Try multiple selectors for Yandex links
            elems = page.locator("a.Link")
            count = await elems.count()
            
            # If no links found with "a.Link", try alternative selectors
            if count == 0:
                elems = page.locator("a[href^='http']")
                count = await elems.count()
            
            logger.info(f"{self.name}: Found {count} link elements on page {n}")
            
            for i in range(count):
                try:
                    href = await elems.nth(i).get_attribute("href")
                    if href and href.startswith("http") and ".ru" in href:
                        # Exclude Yandex internal links
                        if "yandex.ru/search" in href or "yandex.ru/_crpd" in href:
                            continue
                        # Exclude other search engines
                        if any(domain in href.lower() for domain in ["google", "youtube", "yandex"]):
                            continue
                        clean_url = href.split("?")[0].split("#")[0]
                        collected_links.add(clean_url)
                        logger.debug(f"{self.name}: Added link: {clean_url}")
                except Exception as e:
                    logger.debug(f"{self.name}: Error extracting link {i}: {e}")
                    pass
            
            logger.info(f"{self.name}: Total collected so far: {len(collected_links)}")
            
            if n < depth:
                next_btn = page.locator("a[aria-label='Следующая страница']")
                if await next_btn.count() == 0:
                    logger.warning(f"{self.name}: No next page button found, stopping at page {n}")
                    break
                
                await human_pause(7, 15)
                await next_btn.click()
                await human_pause(3, 5)
                await wait_for_captcha(page, self.name)
        
        elapsed = time.time() - start_time
        new_links = len(collected_links) - initial_count
        print(f"[OK] {self.name}: Собрано {new_links} ссылок за {elapsed:.1f} сек ({elapsed/60:.1f} мин)\n")
        logger.info(f"{self.name}: Завершено за {elapsed:.1f}с, собрано {new_links} ссылок")


class GoogleEngine(SearchEngine):
    """Google search engine parser."""
    
    def __init__(self):
        super().__init__("GOOGLE")
    
    async def parse(self, page: Page, query: str, depth: int, collected_links: Set[str]):
        """Parse Google search results."""
        start_time = time.time()
        logger.info(f"{self.name}: Начало парсинга '{query}'")
        print(f"\n[*] {self.name}: Старт парсинга...")
        
        initial_count = len(collected_links)
        
        print(f"[GOOGLE] Opening search page for: {query}")
        logger.info(f"{self.name}: Opening Google search for '{query}'")
        
        await page.goto(
            f"https://www.google.com/search?q={query.replace(' ', '+')}&hl=ru",
            timeout=60000,
            wait_until="domcontentloaded"
        )
        
        print(f"[GOOGLE] Page loaded: {page.url}")
        logger.info(f"{self.name}: Page loaded: {page.url}")
        
        # Wait for CAPTCHA to be solved if present
        await wait_for_captcha(page, self.name)
        
        # If we're on CAPTCHA page, wait for user to solve it
        max_captcha_wait = 300  # 5 minutes
        captcha_wait_start = time.time()
        while "/sorry" in page.url.lower() or "captcha" in page.url.lower():
            elapsed = time.time() - captcha_wait_start
            if elapsed > max_captcha_wait:
                print(f"[ERROR] {self.name}: CAPTCHA wait timeout after {max_captcha_wait}s")
                logger.error(f"{self.name}: CAPTCHA wait timeout")
                break
            
            print(f"[WAIT] {self.name}: Waiting for CAPTCHA to be solved... ({int(elapsed)}s / {max_captcha_wait}s)")
            await asyncio.sleep(3)
            try:
                await page.reload(wait_until="domcontentloaded", timeout=30000)
            except:
                pass
        
        if "/sorry" not in page.url.lower():
            print(f"[OK] {self.name}: CAPTCHA solved or not present, continuing...")
            logger.info(f"{self.name}: Ready to parse search results")
        
        logger.info(f"{self.name}: Starting to parse {depth} page(s)")
        for n in range(1, depth + 1):
            print(f"[PAGE] {self.name}: страница {n}/{depth}")
            logger.info(f"{self.name}: Processing page {n} of {depth}, current URL: {page.url}")
            
            await light_human_behavior(page)
            await wait_for_captcha(page, self.name)
            
            # Use simple approach like old parser - get all links
            elems = page.locator("a")
            count = await elems.count()
            print(f"[DEBUG] {self.name}: Found {count} total links on page")
            logger.info(f"{self.name}: Found {count} total links on page")
            
            for i in range(count):
                try:
                    href = await elems.nth(i).get_attribute("href")
                    if href:
                        # Clean href - remove Google redirect parameters
                        if href.startswith("/url?q="):
                            import urllib.parse
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                            if "q" in parsed:
                                href = parsed["q"][0]
                        
                        # Filter: must be http/https, contain .ru, not be Google/Youtube
                        if (href and href.startswith("http") and 
                            ".ru" in href and 
                            "google" not in href.lower() and
                            "youtube" not in href.lower()):
                            clean_href = href.split("&")[0].split("?")[0]
                            collected_links.add(clean_href)
                            print(f"[FOUND] {self.name}: {clean_href}")
                            logger.info(f"{self.name}: Found link: {clean_href}")
                except Exception as e:
                    logger.debug(f"Error extracting link {i}: {e}")
                    pass
            
            print(f"[INFO] {self.name}: Total links collected so far: {len(collected_links)}")
            logger.info(f"{self.name}: Total links collected so far: {len(collected_links)}")
            
            if n < depth:
                next_btn = page.locator("a#pnnext")
                if await next_btn.count() == 0:
                    break
                
                await human_pause(2, 5)
                await next_btn.click()
                await wait_for_captcha(page, self.name)
        
        elapsed = time.time() - start_time
        new_links = len(collected_links) - initial_count
        print(f"[OK] {self.name}: Собрано {new_links} ссылок за {elapsed:.1f} сек ({elapsed/60:.1f} мин)\n")
        logger.info(f"{self.name}: Завершено за {elapsed:.1f}с, собрано {new_links} ссылок")


# Legacy functions for backward compatibility
async def search_google(keyword: str, max_results: int = 10) -> List[str]:
    """Legacy function - returns empty list. Use GoogleEngine.parse() instead."""
    logger.warning("search_google() is deprecated. Use GoogleEngine.parse() instead.")
    return []


async def search_yandex(keyword: str, max_results: int = 10) -> List[str]:
    """Legacy function - returns empty list. Use YandexEngine.parse() instead."""
    logger.warning("search_yandex() is deprecated. Use YandexEngine.parse() instead.")
    return []


async def search_combined(keyword: str, max_results: int = 10) -> List[str]:
    """Legacy function - returns empty list. Use both engines separately instead."""
    logger.warning("search_combined() is deprecated. Use both engines separately instead.")
    return []

