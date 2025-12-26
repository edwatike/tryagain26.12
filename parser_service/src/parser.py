"""Main parser logic."""
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup

from src.config import settings
from src.engines import search_combined
from src.utils import (
    extract_domain,
    extract_emails,
    extract_phones,
    extract_inn,
    clean_text,
)
from src.human_behavior import random_delay, human_like_scroll


class Parser:
    """Main parser class."""
    
    def __init__(self, chrome_cdp_url: str):
        self.chrome_cdp_url = chrome_cdp_url
        self.browser: Optional[Browser] = None
    
    async def connect_browser(self):
        """Connect to Chrome via CDP."""
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        # Connect to existing Chrome instance via CDP
        self.browser = await playwright.chromium.connect_over_cdp(self.chrome_cdp_url)
    
    async def close(self):
        """Close browser connection."""
        if self.browser:
            await self.browser.close()
    
    async def parse_page(self, url: str) -> dict:
        """Parse a single page and extract supplier data."""
        if not self.browser:
            await self.connect_browser()
        
        page = await self.browser.new_page()
        
        try:
            # Navigate to page
            await page.goto(url, wait_until="networkidle", timeout=settings.page_load_timeout)
            
            # Simulate human behavior
            await random_delay(1000, 2000)
            await human_like_scroll(page)
            
            # Get page content
            html = await page.content()
            title = await page.title()
            
            # Parse HTML
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text()
            
            # Extract data
            emails = extract_emails(text)
            phones = extract_phones(text)
            inn = extract_inn(text)
            
            # Extract company name (from title or h1)
            company_name = title
            h1 = soup.find("h1")
            if h1:
                company_name = clean_text(h1.get_text())
            
            # If no company name found, use domain
            if not company_name or len(company_name) < 3:
                company_name = extract_domain(url)
            
            return {
                "name": company_name,
                "domain": extract_domain(url),
                "email": emails[0] if emails else None,
                "phone": phones[0] if phones else None,
                "inn": inn,
                "source_url": url,
            }
        except Exception as e:
            print(f"Error parsing {url}: {e}")
            return {
                "name": extract_domain(url),
                "domain": extract_domain(url),
                "email": None,
                "phone": None,
                "inn": None,
                "source_url": url,
            }
        finally:
            await page.close()
    
    async def parse_keyword(self, keyword: str, max_urls: int = 10) -> List[dict]:
        """Parse suppliers for a keyword."""
        # Search for URLs
        urls = await search_combined(keyword, max_urls)
        
        if not urls:
            # If no URLs from search, return empty list
            # In production, this would use actual search results
            return []
        
        # Connect to browser
        await self.connect_browser()
        
        suppliers = []
        for url in urls[:max_urls]:
            try:
                supplier_data = await self.parse_page(url)
                suppliers.append(supplier_data)
                await random_delay(1000, 3000)  # Delay between pages
            except Exception as e:
                print(f"Error processing {url}: {e}")
                continue
        
        await self.close()
        return suppliers

