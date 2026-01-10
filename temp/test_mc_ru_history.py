import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.browser_agent import BrowserAgent
from playwright.async_api import async_playwright

async def test_history_page():
    print("=" * 80)
    print("Testing INN search on mc.ru/company/history page")
    print("=" * 80)
    
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
        
        print("\nNavigating to https://mc.ru/company/history...")
        await page.goto('https://mc.ru/company/history', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
        
        agent = BrowserAgent()
        agent.page = page
        
        print("\nSearching for INN via CDP...")
        result = await agent.search_inn_comprehensive()
        
        if result:
            print(f"\n[SUCCESS] Found INN: {result.get('inn')}")
            print(f"Source: {result.get('source')}")
            print(f"Has org form: {result.get('has_org_form')}")
            print(f"Context: {result.get('context', '')[:300]}")
        else:
            print("\n[FAILED] INN not found on history page")
            
            # Check links on this page
            links = await agent.get_links()
            print(f"\nFound {len(links)} links on history page:")
            for i, link in enumerate(links[:20], 1):
                text = link.get('text', '')
                href = link.get('href', '')
                if 'контакты' in text.lower() or 'contact' in text.lower() or 'contacts' in href.lower():
                    print(f"{i}. [CONTACTS] Text: '{text}', href: {href}")
                else:
                    print(f"{i}. Text: '{text}', href: {href[:80]}")
        
        await playwright.stop()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_history_page())


