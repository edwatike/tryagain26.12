import asyncio
import sys
from pathlib import Path
import re

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.browser_agent import BrowserAgent
from playwright.async_api import async_playwright

async def find_inn_fast():
    """Quickly find INN on mc.ru by checking common pages"""
    print("=" * 80)
    print("Quick INN search on mc.ru - checking multiple pages")
    print("=" * 80)
    
    pages_to_check = [
        "https://mc.ru",
        "https://mc.ru/about",
        "https://mc.ru/company",
        "https://mc.ru/company/about",
        "https://mc.ru/company/contacts",
        "https://mc.ru/company/rekvizity",
        "https://mc.ru/company/requisites",
        "https://mc.ru/contacts",
        "https://mc.ru/rekvizity",
        "https://mc.ru/requisites",
    ]
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp('http://127.0.0.1:9222')
        
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
        
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()
        
        agent = BrowserAgent()
        agent.page = page
        
        for url in pages_to_check:
            print(f"\n{'='*80}")
            print(f"Checking: {url}")
            print(f"{'='*80}")
            
            try:
                await agent.navigate(url)
                await asyncio.sleep(2)
                
                # Scroll to load content
                await agent.scroll_to_bottom()
                await asyncio.sleep(2)
                
                # Comprehensive search
                result = await agent.search_inn_comprehensive()
                if result:
                    print(f"\n[SUCCESS] Found INN: {result.get('inn')}")
                    print(f"Source: {result.get('source')}")
                    print(f"URL: {url}")
                    print(f"Context: {result.get('context', '')[:300]}")
                    await playwright.stop()
                    return result
                else:
                    print("[NOT FOUND] No INN on this page")
                    
            except Exception as e:
                print(f"[ERROR] {e}")
                continue
        
        print("\n[FAILED] INN not found on any checked page")
        await playwright.stop()
        return None
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(find_inn_fast())


