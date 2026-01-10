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

async def test_full_page():
    print("=" * 80)
    print("Testing full page load on mc.ru contacts page")
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
        
        # Navigate to mc.ru contacts page and wait for full load
        print("\nNavigating to https://mc.ru/company/contacts...")
        await page.goto('https://mc.ru/company/contacts', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(5)  # Wait for dynamic content
        
        # Scroll to bottom to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        
        # Test comprehensive search
        agent = BrowserAgent()
        agent.page = page
        
        print("\nTesting comprehensive search...")
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
            context_text = result.get('context', '')
            print(f"Context length: {len(context_text)}")
            print(f"Context (first 500): {context_text[:500]}")
            
            # Check if it's a tracking ID
            inn = result.get('inn', '')
            context_str = str(context_text).lower()
            is_tracking = any(indicator in context_str for indicator in [
                '_ym', 'yandex', 'metrika', 'tracking', 'analytics',
                'google', 'gtag', 'ga_', 'session', 'cookie'
            ])
            
            if is_tracking:
                print(f"\n[WARNING] Found INN might be from tracking/metrics: {inn}")
            else:
                print(f"\n[SUCCESS] Found INN: {inn}!")
                print(f"Has org form context: {result.get('has_org_form')}")
        else:
            print("INN not found")
            
            # Try to get page text and search manually
            print("\nTrying manual search...")
            page_text = await page.inner_text('body')
            inn_pattern = r'\b\d{10}\b|\b\d{12}\b'
            matches = re.findall(inn_pattern, page_text)
            print(f"Found {len(matches)} potential INN in page text: {matches[:10]}")
            
            # Check HTML
            html = await page.content()
            html_matches = re.findall(inn_pattern, html)
            print(f"Found {len(html_matches)} potential INN in HTML: {html_matches[:10]}")
        
        await playwright.stop()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_page())


