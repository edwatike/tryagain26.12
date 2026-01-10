import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.browser_agent import BrowserAgent
from playwright.async_api import async_playwright

async def test_contacts_page():
    print("=" * 80)
    print("Testing CDP search on mc.ru contacts page")
    print("=" * 80)
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp('http://127.0.0.1:9222')
        
        # Get existing context or create new
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
        
        # Get existing page or create new
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()
        
        # Navigate to mc.ru contacts page
        print("\nNavigating to https://mc.ru/company/contacts...")
        await page.goto('https://mc.ru/company/contacts', wait_until='domcontentloaded', timeout=10000)
        await asyncio.sleep(2)
        
        # Create browser agent and set page
        agent = BrowserAgent()
        agent.page = page
        
        # Test comprehensive search
        print("\nSearching for INN via CDP...")
        result = await agent.search_inn_comprehensive()
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        if result:
            print(f"INN: {result.get('inn')}")
            print(f"Source: {result.get('source')}")
            print(f"Visible: {result.get('visible')}")
            print(f"Has INN context: {result.get('has_inn_context')}")
            print(f"Has org form: {result.get('has_org_form')}")
            context_text = result.get('context', '')[:500]
            print(f"Context: {context_text}...")
            
            # Check if it's a tracking ID
            inn = result.get('inn', '')
            context_str = str(result.get('context', '')).lower()
            is_tracking = any(indicator in context_str for indicator in [
                '_ym', 'yandex', 'metrika', 'tracking', 'analytics',
                'google', 'gtag', 'ga_', 'session', 'cookie'
            ])
            
            if is_tracking:
                print(f"\n[WARNING] Found INN might be from tracking/metrics: {inn}")
            else:
                print(f"\n[SUCCESS] Found INN: {inn}!")
        else:
            print("INN not found")
        
        await playwright.stop()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_contacts_page())


